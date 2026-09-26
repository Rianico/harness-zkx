#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""herdr-prompt — deliver one prompt payload to a Herdr agent without shell mangling.

Reads the payload verbatim from a file or stdin, hands it to
``herdr agent prompt <TARGET> <TEXT>`` as a single argv element, and forwards the wait
flags. No shell is involved, so quotes, backticks, ``$``, newlines, and code fences
survive byte-for-byte.

    herdr-prompt reviewer --file brief.md --wait --timeout 120000
    herdr-prompt reviewer worker --file brief.md --no-wait
    herdr-prompt reviewer --file - < brief.md
    git diff | herdr-prompt reviewer --wait
    herdr-prompt --label "review pane" --file brief.md --wait

TARGET is one or more agent names or pane ids; every target receives the same
payload verbatim. `--label` takes an exact pane label instead, which is
what a person reads off the pane border; labels are not unique, so an ambiguous one fails
with the candidates listed. `--no-wait` dispatches without waiting and fails
when combined with `--wait`.

Exit status: 0 accepted (``--wait`` settled without needing input), 1 herdr failure,
2 usage or missing precondition, 3 a target needs human input (``agent_blocked``, or
``--wait`` settled on ``blocked``), 4 the prompt was delivered but ``--wait``
timed out first — the agent is working asynchronously: yield turn and await reply
callback, or resume with ``herdr-wait`` instead of resubmitting.

Caller context is prepended by default (see `resolve_caller`): the payload opens
with a `Caller:` block (including Herdr skill notice and sibling workers if present)
and closes with the completion-reply contract via `herdr-reply`, so a worker
can answer the caller by name using the helper script without shell mangling.
`--no-caller-context` sends the payload verbatim (with a loud warning for named targets);
`--dry-run` shows the exact rendered payload that would be submitted.

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    EXIT_BLOCKED,
    EXIT_OK,
    HerdrError,
    UsageError,
    current_pane_id,
    decode_response,
    entries,
    entry_optional_text,
    error_code,
    find_herdr,
    guard,
    require_herdr_env,
    run_herdr,
    run_herdr_checked,
)

STDIN = "-"
BLOCKED = "blocked"
BLOCKED_CODE = "agent_blocked"
PROMPT_STATES = "idle, working, blocked, done, or unknown"
TIMEOUT_CODE = "timeout"
EXIT_WAIT_TIMEOUT = 4


class WaitTimeout(Exception):
    """Prompt delivered but `--wait` timed out; the agent is still working (exit 4)."""


@dataclass
class Options:
    """CLI options; `argparse` writes into this typed namespace."""

    targets: list[str] = field(default_factory=list)
    label: str | None = None
    file: str | None = None
    wait: bool = False
    no_wait: bool = False
    until: list[str] = field(default_factory=list)
    timeout: int | None = None
    json: bool = False
    dry_run: bool = False
    no_caller_context: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-prompt",
        description="Submit a byte-exact prompt payload to a Herdr agent (no shell involved).",
        epilog=(
            "exit status: 0 accepted, 1 herdr failure, 2 usage or precondition, "
            "3 a target needs human input, 4 prompt delivered but the wait timed out"
        ),
    )
    _ = parser.add_argument(
        "targets", nargs="*", metavar="TARGET", help="agent names or pane ids (one or more)"
    )
    _ = parser.add_argument(
        "--label",
        metavar="LABEL",
        help="exact pane label to resolve to a pane id, instead of TARGET",
    )
    _ = parser.add_argument(
        "--file",
        metavar="PATH",
        help="payload file; '-' or omitted reads stdin verbatim",
    )
    _ = parser.add_argument(
        "--wait",
        action="store_true",
        help="wait for the first settled state after submission",
    )
    _ = parser.add_argument(
        "--no-wait",
        action="store_true",
        help="dispatch without waiting; fails when combined with --wait",
    )
    _ = parser.add_argument(
        "--until",
        action="append",
        metavar="STATUS",
        help=f"exact state to match after --wait, repeatable ({PROMPT_STATES})",
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
        "--no-caller-context",
        action="store_true",
        help="send the payload verbatim without the caller block and reply contract",
    )
    return parser


def read_payload(source: str | None) -> str:
    """Read the payload verbatim; only the choice of stream is validated, not its content."""
    if source is None or source == STDIN:
        if sys.stdin.isatty():
            raise UsageError(
                "no --file given and stdin is a terminal; pass --file PATH or pipe the payload"
            )
        try:
            raw = sys.stdin.buffer.read()
        except OSError as exc:
            raise UsageError(f"cannot read payload from stdin: {exc}") from exc
    else:
        try:
            raw = Path(source).read_bytes()
        except OSError as exc:
            raise UsageError(f"cannot read payload from {source!r}: {exc}") from exc

    if b"\x00" in raw:
        raise UsageError("payload contains a NUL byte, which cannot appear in an argv element")
    try:
        payload = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UsageError(f"payload is not valid UTF-8: {exc}") from exc
    if not payload.strip():
        raise UsageError("payload is empty; refusing to submit an empty prompt")
    return payload


@dataclass(frozen=True)
class CallerContext:
    """Who is handing off: pane id, visible label, and addressable agent name."""

    pane_id: str
    label: str | None = None
    agent: str | None = None


def resolve_caller(herdr: str, env: Mapping[str, str]) -> CallerContext:
    """Read the caller from HERDR_PANE_ID (or `pane current`), the pane list, and the agent list."""
    pane_id = env.get("HERDR_PANE_ID") or current_pane_id(herdr, env)
    label: str | None = None
    listed = entries(run_herdr_checked([herdr, "pane", "list"], env), "result", "panes")
    for entry in listed:
        if entry_optional_text(entry, "pane_id") == pane_id:
            label = entry_optional_text(entry, "label")
            break
    agent: str | None = None
    agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
    for entry in agents:
        if entry_optional_text(entry, "pane_id") == pane_id:
            agent = entry_optional_text(entry, "name")
            break
    return CallerContext(pane_id=pane_id, label=label, agent=agent)


def _single_line(value: str, limit: int = 64) -> str:
    """Collapse a free-form pane label onto one header line; labels are operator input."""
    return " ".join(value.split())[:limit]


def render_caller_block(caller: CallerContext) -> str:
    """Render the `Caller:` header; absent fields are omitted, never invented."""
    fields = f"pane={caller.pane_id}"
    label = _single_line(caller.label) if caller.label else ""
    if label:
        fields += f" label={label}"
    if caller.agent:
        fields += f" agent={caller.agent}"
    return f"Caller: {fields}"


SKILL_NOTICE = "Herdr: see skill ~/.agents/skills/herdr/SKILL.md — use scripts in ~/.agents/skills/herdr/scripts/ for communication, not bare herdr CLI"


def render_reply_contract(caller: CallerContext) -> str:
    """Render the completion-reply contract; without an agent name no target is addressable."""
    if caller.agent:
        contract = f'  uv run ~/.agents/skills/herdr/scripts/herdr_reply.py {caller.agent} "<STATUS> <artifacts> <issues>"'
        return (
            "On completion, reply to the caller in one message using the herdr helper script:\n"
            f"{contract}"
        )
    note = (
        "(the calling pane has no agent name; reply cannot be addressed — "
        "report completion to the user instead)"
    )
    return f"On completion, reply to the caller in one message:\n  {note}"


def resolve_workspace_workers(
    herdr: str,
    caller_pane_id: str,
    target_panes: Sequence[str],
    env: Mapping[str, str],
) -> list[str]:
    """Find other live agents in the caller's workspace (or target's workspace)."""
    try:
        listed_panes = entries(run_herdr_checked([herdr, "pane", "list"], env), "result", "panes")
        agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
    except HerdrError:
        return []

    pane_ws: dict[str, str] = {}
    for p in listed_panes:
        pid = entry_optional_text(p, "pane_id")
        ws = entry_optional_text(p, "workspace_id")
        if pid and ws:
            pane_ws[pid] = ws

    agent_panes: dict[str, str] = {}
    for a in agents:
        name = entry_optional_text(a, "name")
        pid = entry_optional_text(a, "pane_id")
        if name and pid:
            agent_panes[name] = pid

    resolved_targets: set[str] = set()
    for t in target_panes:
        if t in pane_ws:
            resolved_targets.add(t)
        elif t in agent_panes:
            resolved_targets.add(agent_panes[t])

    caller_ws = pane_ws.get(caller_pane_id)
    target_workspaces = {pane_ws.get(p) for p in resolved_targets if pane_ws.get(p)}

    workspaces_to_check: list[str] = []
    if caller_ws:
        workspaces_to_check.append(caller_ws)
    for tw in target_workspaces:
        if tw and tw not in workspaces_to_check:
            workspaces_to_check.append(tw)

    excluded_panes = {caller_pane_id} | resolved_targets
    workers: list[str] = []
    for a in agents:
        name = entry_optional_text(a, "name")
        pid = entry_optional_text(a, "pane_id")
        if not name or not pid or pid in excluded_panes:
            continue
        if pane_ws.get(pid) in workspaces_to_check:
            workers.append(f"{name}@{pid}")

    return sorted(dict.fromkeys(workers))


def wrap_with_caller(payload: str, caller: CallerContext, *, workers: Sequence[str] = ()) -> str:
    """Prepend the caller block, skill notice, and append the reply contract around the payload."""
    header_lines = [render_caller_block(caller), SKILL_NOTICE]
    if workers:
        header_lines.append(f"Workers: {', '.join(workers)}")
    header = "\n".join(header_lines)
    return f"{header}\n\n{payload}\n\n{render_reply_contract(caller)}"


def build_prompt_argv(
    herdr: str,
    target: str,
    payload: str,
    *,
    wait: bool,
    until: Sequence[str],
    timeout: int | None,
) -> list[str]:
    argv = [herdr, "agent", "prompt", target, payload]
    if wait:
        argv.append("--wait")
    for state in until:
        argv += ["--until", state]
    if timeout is not None:
        if timeout <= 0:
            raise UsageError(f"--timeout {timeout} is not positive")
        argv += ["--timeout", str(timeout)]
    return argv


def settled_state(raw: str) -> str | None:
    """Read `result.agent.agent_status` when herdr returned it; absence is not an error."""
    result = decode_response(raw).get("result")
    if not isinstance(result, dict):
        return None
    agent = result.get("agent")
    if not isinstance(agent, dict):
        return None
    state = agent.get("agent_status")
    return state if isinstance(state, str) and state else None


def resolve_label(herdr: str, label: str, env: Mapping[str, str]) -> str:
    """Resolve an exact pane label to its pane id; labels are not unique, so ambiguity fails."""
    raw = run_herdr_checked([herdr, "pane", "list"], env)
    matches = [entry for entry in entries(raw, "result", "panes") if entry.get("label") == label]
    if not matches:
        raise UsageError(f"no pane carries the label {label!r}; run herdr-overview to list labels")
    if len(matches) > 1:
        candidates = ", ".join(
            f"{entry_optional_text(entry, 'pane_id') or '?'} "
            f"({entry_optional_text(entry, 'agent') or 'no agent'})"
            for entry in matches
        )
        raise UsageError(f"label {label!r} is ambiguous: {candidates}; pass the pane id instead")
    pane_id = entry_optional_text(matches[0], "pane_id")
    if not pane_id:
        raise HerdrError("the labelled pane has no pane_id")
    return pane_id


KNOWN_AGENT_KINDS: frozenset[str] = frozenset(
    {
        "pi",
        "qodercli",
        "agy",
        "claude",
        "cursor",
        "codestral",
        "cline",
        "gemini",
        "openai",
        "copilot",
        "aider",
    }
)


def validate_targets_not_kinds(targets: Sequence[str], herdr: str, env: Mapping[str, str]) -> None:
    """Refuse targets that are agent kinds (e.g. 'qodercli') instead of addressable agent names."""
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

    for target in targets:
        if target in all_kinds and target not in live_names and target not in live_panes:
            matching = sorted(
                entry_optional_text(a, "name") or ""
                for a in agents
                if entry_optional_text(a, "agent") == target and entry_optional_text(a, "name")
            )
            matching = [name for name in matching if name]
            hint = f" (live agent names: {', '.join(matching)})" if matching else ""
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


def resolve_targets(options: Options, herdr: str, env: Mapping[str, str]) -> list[str]:
    """Pick the prompt targets: explicit TARGETs, or the pane carrying --label."""
    if options.label:
        if options.targets:
            raise UsageError("pass either TARGETs or --label, not both")
        return [resolve_label(herdr, options.label, env)]
    if not options.targets:
        raise UsageError("pass TARGET (agent name or pane id) or --label")
    if len(set(options.targets)) != len(options.targets):
        raise UsageError("duplicate TARGETs; list each agent once")
    if not options.no_caller_context:
        validate_targets_not_kinds(options.targets, herdr, env)
    return list(options.targets)


@dataclass
class Dispatch:
    """Per-target outcome of a broadcast prompt."""

    target: str
    state: str | None = None
    wait_timed_out: bool = False
    blocked: bool = False


def prompt_one(
    herdr: str, target: str, payload: str, options: Options, env: Mapping[str, str]
) -> Dispatch:
    """Deliver the payload to one target, mapping herdr's answer onto a Dispatch."""
    argv = build_prompt_argv(
        herdr,
        target,
        payload,
        wait=options.wait,
        until=options.until,
        timeout=options.timeout,
    )
    if options.dry_run:
        print(json.dumps(argv))
        return Dispatch(target)

    done = run_herdr(argv, env)
    if done.returncode != 0:
        detail = (done.stderr or done.stdout).strip() or f"exit status {done.returncode}"
        code = error_code(done.stderr)
        if code == BLOCKED_CODE:
            print(f"herdr-prompt: {target}: {detail}", file=sys.stderr)
            return Dispatch(target, blocked=True)
        if code == TIMEOUT_CODE:
            # Not a dispatch failure: the prompt was accepted and the agent is
            # working; only the wait ran out. Reported as exit 4, never exit 1.
            return Dispatch(target, wait_timed_out=True)
        raise HerdrError(f"herdr agent prompt {target} failed: {detail}")

    _ = decode_response(done.stdout)
    state = settled_state(done.stdout)
    if options.json:
        print(done.stdout, end="" if done.stdout.endswith("\n") else "\n")
    else:
        size = len(payload.encode("utf-8"))
        suffix = f"  state={state}" if state else ""
        rev, pane = (
            fetch_agent_revision(herdr, target, env)
            if not options.no_caller_context
            else (None, None)
        )
        pane_str = f" ({pane})" if pane and pane != target else ""
        rev_str = f"  revision={rev}" if rev else ""
        print(f"prompted {target}{pane_str}  bytes={size}{rev_str}{suffix}")
    return Dispatch(target, state=state, blocked=state == BLOCKED)


def prompt_agents(options: Options, env: Mapping[str, str]) -> int:
    if options.wait and options.no_wait:
        raise UsageError("pass either --wait or --no-wait, not both")
    require_herdr_env(env)
    herdr = find_herdr(env)
    targets = resolve_targets(options, herdr, env)
    payload = read_payload(options.file)
    if options.no_caller_context:
        for target in targets:
            print(
                f"herdr-prompt: warning: --no-caller-context drops caller block and reply contract for target {target!r}; target cannot call back",
                file=sys.stderr,
            )
    else:
        caller = resolve_caller(herdr, env)
        workers = resolve_workspace_workers(herdr, caller.pane_id, targets, env)
        payload = wrap_with_caller(payload, caller, workers=workers)
    dispatches = [prompt_one(herdr, target, payload, options, env) for target in targets]
    blocked = sorted(dispatch.target for dispatch in dispatches if dispatch.blocked)
    if blocked:
        names = ", ".join(blocked)
        print(f"herdr-prompt: {names} need human input (blocked)", file=sys.stderr)
        return EXIT_BLOCKED
    timed_out = sorted(dispatch.target for dispatch in dispatches if dispatch.wait_timed_out)
    if timed_out:
        names = ", ".join(timed_out)
        if options.timeout is not None:
            hint = f"still working after {options.timeout}ms (wait timed out)"
        else:
            hint = "still working when the wait timed out"
        raise WaitTimeout(
            f"prompt delivered to {names} but {hint}; "
            f"working asynchronously. Yield turn and await reply callback, or resume with herdr-wait {names} --timeout <ms> instead of resubmitting"
        )
    return EXIT_OK


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    try:
        return guard("herdr-prompt", lambda: prompt_agents(options, env_map))
    except WaitTimeout as exc:
        print(f"herdr-prompt: {exc}", file=sys.stderr)
        return EXIT_WAIT_TIMEOUT


if __name__ == "__main__":
    raise SystemExit(main())
