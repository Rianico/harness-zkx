#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""herdr-reply — send a completion reply callback to a caller agent without shell mangling.

Delivers `<STATUS> <artifacts> <issues>` or a result payload to the caller's agent
name, wrapped in the same timestamped `Routing:`/`Hierarchy:`/`Protocol:` envelope
`herdr-prompt` uses, so the party reading a reply always knows who reported and to
whom. When the sender holds an active lease, its `Ticket-ID`/`Task-ID` ride along as
`Ticket-ID:` and `In-Reply-To:` correlation lines. The envelope is script-rendered,
never model-authored, so it cannot be forgotten.

    herdr-reply orchestrator "COMPLETED artifacts=[...] issues=[]"
    herdr-reply orchestrator --file result.md
    echo "COMPLETED" | herdr-reply orchestrator
    herdr-reply orchestrator "COMPLETED" --wait --timeout 15000

Exit status: 0 accepted, 1 herdr failure, 2 usage or missing precondition,
3 target needs human input (blocked), 4 prompt delivered but wait timed out.

Local addition to the absorbed upstream Herdr skill; not part of `herdrdev/herdr`.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    EXIT_BLOCKED,
    EXIT_OK,
    KNOWN_AGENT_KINDS,
    METHOD_CONSTRAINT_EPILOG,
    HerdrError,
    UsageError,
    decode_response,
    diagnose_agent_not_found,
    entries,
    entry_optional_text,
    error_code,
    fetch_inventory,
    find_herdr,
    format_shell_pane_diagnostic,
    guard,
    inspect_target_shell_pane,
    require_herdr_env,
    run_herdr,
    run_herdr_checked,
    verify_target_not_bare_shell,
)
from herdr_lease import get_lease, release_lease
from herdr_prompt import (
    render_envelope,
    resolve_caller,
    resolve_receiver,
    utc_stamp,
)

STDIN = "-"
BLOCKED = "blocked"
BLOCKED_CODE = "agent_blocked"
TIMEOUT_CODE = "timeout"
EXIT_WAIT_TIMEOUT = 4


class WaitTimeout(Exception):
    """Reply delivered but `--wait` timed out; the caller is still processing (exit 4)."""


@dataclass
class Options:
    """CLI options; `argparse` writes into this typed namespace."""

    target: str = ""
    message: str | None = None
    file: str | None = None
    wait: bool = False
    timeout: int | None = None
    json: bool = False
    dry_run: bool = False
    auto_start: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-reply",
        description="Deliver a completion reply to a caller agent without shell mangling.",
        epilog=(
            "exit status: 0 accepted, 1 herdr failure, 2 usage or precondition, "
            "3 target needs human input, 4 reply delivered but wait timed out\n\n"
            + METHOD_CONSTRAINT_EPILOG
        ),
    )
    _ = parser.add_argument("target", metavar="TARGET", help="caller agent name or pane id")
    _ = parser.add_argument(
        "message",
        nargs="?",
        metavar="MESSAGE",
        help="reply text (e.g. '<STATUS> <artifacts> <issues>'); omitted reads --file or stdin",
    )
    _ = parser.add_argument(
        "--file",
        metavar="PATH",
        help="payload file; '-' reads stdin verbatim",
    )
    _ = parser.add_argument(
        "--wait",
        action="store_true",
        help="wait for caller to settle after receiving reply",
    )
    _ = parser.add_argument(
        "--timeout",
        type=int,
        metavar="MS",
        help="fail after this many milliseconds",
    )
    _ = parser.add_argument("--json", action="store_true", help="print herdr's raw JSON response")
    _ = parser.add_argument("--dry-run", action="store_true", help="print the argv, submit nothing")
    _ = parser.add_argument(
        "--auto-start",
        metavar="KIND",
        help="automatically start the agent on an open shell pane before delivering the reply",
    )
    return parser


def read_payload(source: str | None, message: str | None) -> str:
    if message is not None:
        if source is not None:
            raise UsageError("pass either a MESSAGE argument or --file, not both")
        payload = message
    elif source is None or source == STDIN:
        if sys.stdin.isatty():
            raise UsageError(
                "no MESSAGE or --file given and stdin is a terminal; pass MESSAGE, --file PATH, or pipe the payload"
            )
        try:
            raw = sys.stdin.buffer.read()
        except OSError as exc:
            raise UsageError(f"cannot read payload from stdin: {exc}") from exc
        try:
            payload = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UsageError(f"payload is not valid UTF-8: {exc}") from exc
    else:
        try:
            raw = Path(source).read_bytes()
        except OSError as exc:
            raise UsageError(f"cannot read payload from {source!r}: {exc}") from exc
        try:
            payload = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UsageError(f"payload is not valid UTF-8: {exc}") from exc

    if "\x00" in payload:
        raise UsageError("payload contains a NUL byte, which cannot appear in an argv element")
    if not payload.strip():
        raise UsageError("payload is empty; refusing to submit an empty reply")
    return payload


def validate_target_not_kind(target: str, herdr: str, env: Mapping[str, str]) -> None:
    """Refuse target if it is an agent kind rather than an addressable agent name."""
    try:
        agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
    except HerdrError:
        return
    live_names = {entry_optional_text(a, "name") for a in agents if entry_optional_text(a, "name")}
    live_panes = {
        entry_optional_text(a, "pane_id") for a in agents if entry_optional_text(a, "pane_id")
    }
    live_kinds = {
        entry_optional_text(a, "agent") for a in agents if entry_optional_text(a, "agent")
    }
    all_kinds = KNOWN_AGENT_KINDS | live_kinds

    if target in all_kinds and target not in live_names and target not in live_panes:
        matching = sorted(
            entry_optional_text(a, "name") or ""
            for a in agents
            if entry_optional_text(a, "agent") == target and entry_optional_text(a, "name")
        )
        matching = [name for name in matching if name]
        hint = f" (live agents of this kind: {', '.join(matching)})" if matching else ""
        raise UsageError(
            f"target {target!r} is an agent kind, not an addressable agent name{hint}. "
            + "Pass the agent name (or pane id) instead"
        )


def fetch_agent_revision(
    herdr: str, target: str, env: Mapping[str, str]
) -> tuple[str | None, str | None]:
    """Fetch (revision, pane_id) from `herdr agent get <target>`, if available."""
    done = run_herdr([herdr, "agent", "get", target], env)
    if done.returncode != 0:
        return None, None
    try:
        data = decode_response(done.stdout).get("result")
        if isinstance(data, dict):
            agent = data.get("agent")
            if isinstance(agent, dict):
                rev = agent.get("revision")
                pane = agent.get("pane_id")
                return (
                    str(rev) if rev is not None else None,
                    str(pane) if pane is not None else None,
                )
    except Exception:
        pass
    return None, None


def settled_state(raw: str) -> str | None:
    result = decode_response(raw).get("result")
    if not isinstance(result, dict):
        return None
    agent = result.get("agent")
    if not isinstance(agent, dict):
        return None
    state = agent.get("agent_status")
    return state if isinstance(state, str) and state else None


def resolve_current_agent(herdr: str, env: Mapping[str, str]) -> str | None:
    """Resolve the calling agent's name (or pane id) from environment and herdr state."""
    pane_id = env.get("HERDR_PANE_ID")
    if not pane_id:
        try:
            done = run_herdr([herdr, "pane", "current"], env)
            if done.returncode == 0:
                result = decode_response(done.stdout).get("result", {})
                if isinstance(result, dict):
                    pane = result.get("pane", {})
                    if isinstance(pane, dict):
                        pane_id = pane.get("pane_id")
        except Exception:
            pass
    if not pane_id:
        return None
    try:
        agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
        for a in agents:
            if entry_optional_text(a, "pane_id") == pane_id:
                name = entry_optional_text(a, "name")
                if name:
                    return name
    except Exception:
        pass
    return pane_id


def release_active_lease(herdr: str, env: Mapping[str, str]) -> None:
    """Release active task lease for the replying sender (current agent or current pane).

    NEVER release target's lease: target is the caller (e.g. task-manager).
    Only the sender's lease is released upon sending a reply.
    """
    try:
        sender = resolve_current_agent(herdr, env)
        if not sender:
            sender = env.get("HERDR_PANE_ID")
        if sender:
            _ = release_lease(sender, env=env)
    except Exception:
        pass


def reply_caller(options: Options, env: Mapping[str, str]) -> int:
    require_herdr_env(env)
    herdr = find_herdr(env)
    target = options.target.strip()
    if not target:
        raise UsageError("pass TARGET (caller agent name or pane id)")
    validate_target_not_kind(target, herdr, env)

    if options.auto_start:
        auto_kind = options.auto_start.strip().lower()
        if not auto_kind or auto_kind not in KNOWN_AGENT_KINDS:
            raise UsageError(
                f"--auto-start kind {options.auto_start!r} is not a recognized agent kind (known: {', '.join(sorted(KNOWN_AGENT_KINDS))})"
            )

    shell_info = inspect_target_shell_pane(herdr, target, env)
    if shell_info is not None:
        if options.auto_start:
            kind = options.auto_start.strip().lower()
            start_name = (
                shell_info.suggested_name
                if shell_info.suggested_name != "<name>"
                else f"agent-{shell_info.pane_id.replace(':', '-')}"
            )
            start_argv = [
                herdr,
                "agent",
                "start",
                start_name,
                "--kind",
                kind,
                "--pane",
                shell_info.pane_id,
            ]
            if not options.dry_run:
                _ = run_herdr_checked(start_argv, env)
            target = start_name
        else:
            diag = format_shell_pane_diagnostic(
                target=target,
                pane_id=shell_info.pane_id,
                label=shell_info.label,
                foreground_proc=shell_info.foreground_proc,
                is_label_match=shell_info.is_label_match,
                suggested_name=shell_info.suggested_name,
                suggested_kind=shell_info.suggested_kind,
            )
            raise UsageError(diag)
    else:
        verify_target_not_bare_shell(herdr, target, env)

    payload = read_payload(options.file, options.message)
    sender = resolve_current_agent(herdr, env)
    lease = get_lease(sender, env=env) if sender else None
    ticket_id: str | None = None
    in_reply_to: str | None = None
    if isinstance(lease, dict):
        lease_ticket = lease.get("ticket_id")
        if isinstance(lease_ticket, str):
            ticket_id = lease_ticket
        lease_task = lease.get("task_id")
        if isinstance(lease_task, str):
            in_reply_to = lease_task
    panes, agents = fetch_inventory(herdr, env)
    caller_ctx = resolve_caller(herdr, env, inventory=(panes, agents))
    reply_envelope = render_envelope(
        caller_ctx,
        receiver=resolve_receiver(panes, agents, target) or target,
        include_recovery=False,
        ticket_id=ticket_id,
        in_reply_to=in_reply_to,
        tab_id=caller_ctx.tab_id,
    )
    payload = f"{utc_stamp()}\n{reply_envelope}\n\n{payload}"

    argv = [herdr, "agent", "prompt", target, payload]
    if options.wait:
        argv.append("--wait")
    if options.timeout is not None:
        if options.timeout <= 0:
            raise UsageError(f"--timeout {options.timeout} is not positive")
        argv += ["--timeout", str(options.timeout)]

    if options.dry_run:
        print(json.dumps(argv))
        return EXIT_OK

    done = run_herdr(argv, env)
    if done.returncode != 0:
        detail = (done.stderr or done.stdout).strip() or f"exit status {done.returncode}"
        code = error_code(done.stderr)
        if code == BLOCKED_CODE:
            print(f"herdr-reply: {target}: {detail}", file=sys.stderr)
            return EXIT_BLOCKED
        if code == TIMEOUT_CODE:
            release_active_lease(herdr, env)
            raise WaitTimeout(
                f"reply delivered to {target} but wait timed out; caller is processing asynchronously"
            )
        if code == "agent_not_found":
            diag = diagnose_agent_not_found(herdr, target, env)
            if diag:
                raise UsageError(diag)
        raise HerdrError(f"herdr agent prompt {target} failed: {detail}")

    release_active_lease(herdr, env)
    _ = decode_response(done.stdout)
    state = settled_state(done.stdout)
    if options.json:
        print(done.stdout, end="" if done.stdout.endswith("\n") else "\n")
    else:
        size = len(payload.encode("utf-8"))
        suffix = f"  state={state}" if state else ""
        rev, pane = fetch_agent_revision(herdr, target, env)
        resolved_pane = pane or (shell_info.pane_id if shell_info else None)
        pane_str = f" ({resolved_pane})" if resolved_pane and resolved_pane != target else ""
        rev_str = f"  revision={rev}" if rev else ""
        print(f"replied to {target}{pane_str}  bytes={size}{rev_str}{suffix}")
    return EXIT_OK


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    try:
        return guard("herdr-reply", lambda: reply_caller(options, env_map))
    except WaitTimeout as exc:
        print(f"herdr-reply: {exc}", file=sys.stderr)
        return EXIT_WAIT_TIMEOUT


if __name__ == "__main__":
    raise SystemExit(main())
