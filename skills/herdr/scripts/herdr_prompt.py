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
    herdr-prompt reviewer callee --file brief.md --no-wait
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

Sender context is prepended by default (see `resolve_caller`): the payload opens
with the Style 2 nested envelope — `Routing:` (Sender, Group, and the
`Receiver(You)` position field), `Hierarchy:` (Task-Group, Ticket-ID, Task-ID,
and In-Reply-To correlation), and `Protocol:` (the Herdr skill notice) — and
closes with the completion-reply contract via `herdr-reply`, so a callee can
answer the sender by name using the helper script without shell mangling. The
default envelope is strictly Routing/Hierarchy/Protocol; recovery metadata
(`cwd`, session, resume command) is never in the default envelope and is
retrieved just-in-time from `.lane/tasks.yaml`. Pass `--verbose` to restore the
`Runtime:` (Cwd/Resume) block for debugging. The envelope is script-rendered,
never model-authored, so it cannot be forgotten.
`--dry-run` shows the exact rendered payload that would be submitted.

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    EXIT_BLOCKED,
    EXIT_OK,
    METHOD_CONSTRAINT_EPILOG,
    HerdrError,
    UsageError,
    current_pane_id,
    decode_response,
    diagnose_agent_not_found,
    diagnose_target_pane,
    entries,
    entry_optional_text,
    error_code,
    fetch_inventory,
    find_herdr,
    guard,
    require_herdr_env,
    run_herdr,
    run_herdr_checked,
    verify_target_not_bare_shell,
)

STDIN = "-"
BLOCKED = "blocked"
BLOCKED_CODE = "agent_blocked"
PROMPT_STATES = "idle, working, blocked, done, or unknown"
TIMEOUT_CODE = "timeout"
EXIT_WAIT_TIMEOUT = 4

READY_TIMEOUT_SECONDS = 10.0
READY_INTERVAL_SECONDS = 0.2
HANDSHAKE_TIMEOUT_SECONDS = 1.5
HANDSHAKE_INTERVAL_SECONDS = 0.1


def _sleep(seconds: float) -> None:
    """Sleep seam: tests monkeypatch this module attribute to skip real delays."""
    time.sleep(seconds)


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
    ticket_id: str | None = None
    task_id: str | None = None
    task_group: str | None = None
    verbose: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-prompt",
        description="Submit a byte-exact prompt payload to a Herdr agent (no shell involved).",
        epilog=(
            "exit status: 0 accepted, 1 herdr failure, 2 usage or precondition, "
            "3 a target needs human input, 4 prompt delivered but the wait timed out\n\n"
            + METHOD_CONSTRAINT_EPILOG
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
        help="send the payload verbatim without the Sender/Receiver envelope and reply contract",
    )
    _ = parser.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "include Runtime: Cwd/Resume recovery metadata; "
            "default envelope is Routing/Hierarchy/Protocol only"
        ),
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
    """The envelope sender: pane id, visible label, addressable agent name, kind, session, tab, cwd."""

    pane_id: str
    label: str | None = None
    agent: str | None = None
    kind: str | None = None
    session_id: str | None = None
    resume_cmd: str | None = None
    tab_id: str | None = None
    cwd: str | None = None


def build_resume_cmd(kind: str | None, session_id: str | None) -> str | None:
    """Build the agent-native resume command string for the caller, if known."""
    if kind == "agy":
        return f"agy --conversation={session_id}" if session_id else None
    if kind == "pi":
        if not session_id:
            return None
        return (
            f"pi --resume {session_id}"
            if session_id.endswith(".jsonl")
            else f"pi --session {session_id}"
        )
    if kind == "claude":
        return f"claude --resume {session_id}" if session_id else None
    if kind in ("qodercli", "qoderclicn"):
        return f"{kind} resume"
    return None


def _session_value(entry: Mapping[str, object]) -> str | None:
    """Read the agent-native session handle out of an agent list entry."""
    sess = entry.get("agent_session")
    if isinstance(sess, dict):
        val = sess.get("value")
        if isinstance(val, str) and val:
            return val
    return None


def build_identity(
    panes: Sequence[Mapping[str, object]],
    agents: Sequence[Mapping[str, object]],
    pane_id: str,
) -> CallerContext:
    """Build the envelope identity for one pane from the pane and agent inventories."""
    label: str | None = None
    tab_id: str | None = None
    cwd: str | None = None
    for entry in panes:
        if entry_optional_text(entry, "pane_id") == pane_id:
            label = entry_optional_text(entry, "label")
            tab_id = entry_optional_text(entry, "tab_id")
            cwd = entry_optional_text(entry, "cwd")
            break
    agent: str | None = None
    kind: str | None = None
    session_id: str | None = None
    for entry in agents:
        if entry_optional_text(entry, "pane_id") == pane_id:
            agent = entry_optional_text(entry, "name")
            kind = entry_optional_text(entry, "agent")
            session_id = _session_value(entry)
            break
    return CallerContext(
        pane_id=pane_id,
        label=label,
        agent=agent,
        kind=kind,
        session_id=session_id,
        resume_cmd=build_resume_cmd(kind, session_id),
        tab_id=tab_id,
        cwd=cwd,
    )


def resolve_caller(
    herdr: str,
    env: Mapping[str, str],
    *,
    inventory: tuple[Sequence[Mapping[str, object]], Sequence[Mapping[str, object]]] | None = None,
) -> CallerContext:
    """Read the caller from HERDR_PANE_ID (or `pane current`), the pane list, and the agent list."""
    pane_id = env.get("HERDR_PANE_ID") or current_pane_id(herdr, env)
    panes, agents = inventory if inventory else fetch_inventory(herdr, env)
    return build_identity(panes, agents, pane_id)


def resolve_receiver(
    panes: Sequence[Mapping[str, object]],
    agents: Sequence[Mapping[str, object]],
    target: str,
) -> CallerContext | None:
    """Resolve a target to its pane identity: a pane id, or the unique live agent name herdr accepts."""
    pane_ids = {entry_optional_text(entry, "pane_id") for entry in panes}
    pane_id = target if target in pane_ids else None
    if pane_id is None:
        for entry in agents:
            if entry_optional_text(entry, "name") == target:
                pane_id = entry_optional_text(entry, "pane_id")
                break
    if not pane_id:
        return None
    return build_identity(panes, agents, pane_id)


def _single_line(value: str, limit: int = 64) -> str:
    """Collapse a free-form pane label onto one header line; labels are operator input."""
    return " ".join(value.split())[:limit]


def _scalar(value: str) -> str:
    """Render a header value; quote only when a YAML reader would mangle it."""
    if not value:
        return ""
    if (
        '"' in value
        or "'" in value
        or "#" in value
        or '": "' in value
        or any(ch.isspace() for ch in value)
    ):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def sender_ref(sender: CallerContext) -> str:
    """Render the targetable `<agent>@<pane>` ref plus position fields; a pane label is never a name."""
    label = _single_line(sender.label) if sender.label else ""
    parts = [f"{sender.agent}@{sender.pane_id}" if sender.agent else sender.pane_id]
    if label and label != sender.agent:
        parts.append(f"label {_scalar(label)}")
    if sender.tab_id:
        parts.append(f"tab {_scalar(sender.tab_id)}")
    if sender.kind:
        parts.append(f"kind {_scalar(sender.kind)}")
    return " - ".join(parts)


def receiver_ref(receiver: str | CallerContext) -> str:
    """Render the addressee as a position ref when it resolved, else as the bare target token."""
    if isinstance(receiver, CallerContext):
        return sender_ref(receiver)
    return _scalar(receiver)


def render_envelope(
    sender: CallerContext,
    *,
    receiver: str | CallerContext | None = None,
    group_members: Sequence[str] = (),
    include_recovery: bool = False,
    ticket_id: str | None = None,
    task_id: str | None = None,
    task_group: str | None = None,
    tab_id: str | None = None,
    in_reply_to: str | None = None,
) -> str:
    """Render the Style 2 envelope; the receiver closes the Routing block, and an absent field renders no line."""
    routing = ["Routing:", f"  Sender: {sender_ref(sender)}"]
    if group_members:
        routing.append(f"  Group: [{', '.join(group_members)}]")
    if receiver:
        routing.append(f"  Receiver(You): {receiver_ref(receiver)}")

    hierarchy: list[str] = []
    if task_group and tab_id:
        hierarchy.append(f"  Task-Group: {task_group} ({tab_id})")
    elif task_group:
        hierarchy.append(f"  Task-Group: {task_group}")
    elif tab_id:
        hierarchy.append(f"  Task-Group: {tab_id}")
    if ticket_id:
        hierarchy.append(f"  Ticket-ID: {ticket_id}")
    if task_id:
        hierarchy.append(f"  Task-ID: {task_id}")
    if in_reply_to:
        hierarchy.append(f"  In-Reply-To: {in_reply_to}")

    runtime: list[str] = []
    if include_recovery:
        if sender.cwd:
            runtime.append(f"  Cwd: {_scalar(sender.cwd)}")
        if sender.resume_cmd:
            runtime.append(f"  Resume: {_scalar(sender.resume_cmd)}")

    lines = [*routing]
    if hierarchy:
        lines.append("Hierarchy:")
        lines.extend(hierarchy)
    if runtime:
        lines.append("Runtime:")
        lines.extend(runtime)
    lines.append("Protocol:")
    lines.append(f"  {SKILL_NOTICE}")
    return "\n".join(lines)


def utc_stamp() -> str:
    """Timestamp an envelope; both directions stamp, so a transcript reads in order."""
    return f"[{datetime.now(UTC).isoformat(timespec='milliseconds').replace('+00:00', 'Z')}]"


SKILL_NOTICE = "Herdr: see skill ~/.agents/skills/herdr/SKILL.md — use scripts in ~/.agents/skills/herdr/scripts/ for communication, not bare herdr CLI"


def render_reply_contract(sender: CallerContext) -> str:
    """Render the completion-reply contract; without an agent name no target is addressable."""
    if sender.agent:
        contract = f'  uv run ~/.agents/skills/herdr/scripts/herdr_reply.py {sender.agent} "<STATUS> <artifacts> <issues>"'
        return (
            "On completion, reply to the sender in one message using the herdr helper script:\n"
            f"{contract}"
        )
    note = (
        "(the sending pane has no agent name; reply cannot be addressed — "
        "report completion to the user instead)"
    )
    return f"On completion, reply to the sender in one message:\n  {note}"


def resolve_group_members(
    panes: Sequence[Mapping[str, object]],
    agents: Sequence[Mapping[str, object]],
    caller_pane_id: str,
    target_panes: Sequence[str],
) -> list[str]:
    """Find every live agent in the caller's workspace (or target's workspace), caller first."""
    pane_ws: dict[str, str] = {}
    for p in panes:
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

    caller_name: str | None = None
    for a in agents:
        if entry_optional_text(a, "pane_id") == caller_pane_id:
            caller_name = entry_optional_text(a, "name")
            break
    members: list[str] = []
    if caller_name:
        members.append(f"{caller_name}@{caller_pane_id}")
    others: list[str] = []
    for a in agents:
        name = entry_optional_text(a, "name")
        pid = entry_optional_text(a, "pane_id")
        if not name or not pid or pid == caller_pane_id:
            continue
        if pane_ws.get(pid) in workspaces_to_check:
            others.append(f"{name}@{pid}")
    members.extend(sorted(dict.fromkeys(others)))
    return members


def wrap_with_envelope(
    payload: str,
    sender: CallerContext,
    *,
    group_members: Sequence[str] = (),
    receiver: str | CallerContext | None = None,
    include_recovery: bool = False,
    ticket_id: str | None = None,
    task_id: str | None = None,
    task_group: str | None = None,
    tab_id: str | None = None,
) -> str:
    """Prepend the timestamped envelope and append the reply contract around the payload."""
    envelope = render_envelope(
        sender,
        receiver=receiver,
        group_members=group_members,
        include_recovery=include_recovery,
        ticket_id=ticket_id,
        task_id=task_id,
        task_group=task_group,
        tab_id=tab_id,
    )
    header = f"{utc_stamp()}\n{envelope}"
    return f"{header}\n\n{payload}\n\n{render_reply_contract(sender)}"


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
        "aider",
        "agy",
        "amp",
        "claude",
        "cline",
        "codestral",
        "codex",
        "copilot",
        "cursor",
        "devin",
        "droid",
        "gemini",
        "grok",
        "hermes",
        "kilo",
        "kimi",
        "kiro",
        "maki",
        "mastracode",
        "omp",
        "openai",
        "opencode",
        "pi",
        "qodercli",
        "qoderclicn",
        "qwen",
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


def _format_seconds(seconds: float) -> str:
    """Render a timeout without a trailing `.0` so diagnostics read `10s`, not `10.0s`."""
    return f"{seconds:g}"


def agent_readiness(
    herdr: str, target: str, env: Mapping[str, str]
) -> tuple[bool, str | None, str | None]:
    """Probe `herdr agent get <target>`; return (ready, status, revision).

    ready is true only when the agent is settled (`idle`/`done`) and its
    `interactive_ready` field is not explicitly false (a missing field counts as
    ready, for back-compat). A non-zero exit or unreadable response is not ready.
    """
    done = run_herdr([herdr, "agent", "get", target], env)
    if done.returncode != 0:
        return (False, None, None)
    try:
        result = decode_response(done.stdout).get("result")
    except HerdrError:
        return (False, None, None)
    if not isinstance(result, dict):
        return (False, None, None)
    agent = result.get("agent")
    if not isinstance(agent, dict):
        return (False, None, None)
    raw_status = agent.get("agent_status")
    status = raw_status if isinstance(raw_status, str) and raw_status else None
    revision = agent.get("revision")
    revision_str = str(revision) if revision is not None else None
    ready = status in ("idle", "done") and agent.get("interactive_ready") is not False
    return (ready, status, revision_str)


def wait_for_ready(
    herdr: str,
    target: str,
    env: Mapping[str, str],
    *,
    timeout: float = READY_TIMEOUT_SECONDS,
    interval: float = READY_INTERVAL_SECONDS,
) -> str | None:
    """Block until the target settles, else fail naming the pane-unblock path.

    The loop is attempt-counted (never wall-clocked) so a monkeypatched `_sleep`
    runs it instantly; the immediate first probe means a settled agent never sleeps.
    """
    attempts = max(1, math.ceil(timeout / interval))
    last_status: str | None = None
    for attempt in range(attempts):
        ready, status, _ = agent_readiness(herdr, target, env)
        last_status = status
        if ready:
            return status
        if attempt < attempts - 1:
            _sleep(interval)
    raise UsageError(
        f"target {target!r} did not settle for prompt delivery within "
        f"{_format_seconds(timeout)}s (last status={last_status or 'unknown'}): the agent may be "
        "waiting on an auth/approval dialog; open the pane and clear it, then retry"
    )


def verify_prompt_accepted(
    herdr: str,
    target: str,
    env: Mapping[str, str],
    pre_revision: str | None,
    *,
    timeout: float = HANDSHAKE_TIMEOUT_SECONDS,
    interval: float = HANDSHAKE_INTERVAL_SECONDS,
) -> bool:
    """Confirm a `--no-wait` prompt landed: the agent started working or its revision moved."""
    attempts = max(1, math.ceil(timeout / interval))
    for attempt in range(attempts):
        _, status, revision = agent_readiness(herdr, target, env)
        if status == "working":
            return True
        if revision is not None and pre_revision is not None and revision != pre_revision:
            return True
        if attempt < attempts - 1:
            _sleep(interval)
    return False


def resolve_targets(options: Options, herdr: str, env: Mapping[str, str]) -> list[str]:
    """Pick the prompt targets: explicit TARGETs, or the pane carrying --label."""
    if options.label:
        if options.targets:
            raise UsageError("pass either TARGETs or --label, not both")
        pane_id = resolve_label(herdr, options.label, env)
        if not options.dry_run:
            diag = diagnose_target_pane(herdr, pane_id, env)
            if diag is None:
                diag = diagnose_target_pane(herdr, options.label, env)
            if diag is not None:
                raise UsageError(diag)
        return [pane_id]
    if not options.targets:
        raise UsageError("pass TARGET (agent name or pane id) or --label")
    if len(set(options.targets)) != len(options.targets):
        raise UsageError("duplicate TARGETs; list each agent once")
    if not options.no_caller_context:
        validate_targets_not_kinds(options.targets, herdr, env)
        if not options.dry_run:
            for target in options.targets:
                verify_target_not_bare_shell(herdr, target, env)
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

    _ = wait_for_ready(herdr, target, env)

    pre_revision: str | None = None
    if options.no_wait:
        pre_revision, _ = fetch_agent_revision(herdr, target, env)

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
        if code == "agent_not_found":
            diag = diagnose_agent_not_found(herdr, target, env)
            if diag:
                raise UsageError(diag)
        raise HerdrError(f"herdr agent prompt {target} failed: {detail}")

    if options.no_wait and not verify_prompt_accepted(herdr, target, env, pre_revision):
        _, last_status, _ = agent_readiness(herdr, target, env)
        raise HerdrError(
            f"prompt acceptance was not confirmed within "
            f"{_format_seconds(HANDSHAKE_TIMEOUT_SECONDS)}s for {target} "
            f"(last status={last_status or 'unknown'}, revision unchanged); the agent may not "
            "have consumed the payload — verify with herdr-wait or resubmit"
        )

    post_rev, post_pane = (
        fetch_agent_revision(herdr, target, env) if not options.no_caller_context else (None, None)
    )
    pane = post_pane

    _ = decode_response(done.stdout)
    state = settled_state(done.stdout)
    if options.json:
        print(done.stdout, end="" if done.stdout.endswith("\n") else "\n")
    else:
        size = len(payload.encode("utf-8"))
        suffix = f"  state={state}" if state else ""
        pane_str = f" ({pane})" if pane and pane != target else ""
        rev_str = f"  revision={post_rev}" if post_rev else ""
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
                f"herdr-prompt: warning: --no-caller-context drops the Sender/Receiver envelope and reply contract for target {target!r}; target cannot call back",
                file=sys.stderr,
            )
        payloads = {target: payload for target in targets}
    else:
        panes, agents = fetch_inventory(herdr, env)
        caller = resolve_caller(herdr, env, inventory=(panes, agents))
        group_members = resolve_group_members(panes, agents, caller.pane_id, targets)
        payloads = {
            target: wrap_with_envelope(
                payload,
                caller,
                group_members=group_members,
                receiver=resolve_receiver(panes, agents, target) or target,
                include_recovery=options.verbose,
                ticket_id=options.ticket_id,
                task_id=options.task_id,
                task_group=options.task_group,
                tab_id=caller.tab_id,
            )
            for target in targets
        }
    if options.wait:
        try:
            agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
            for a in agents:
                name = entry_optional_text(a, "name")
                pid = entry_optional_text(a, "pane_id")
                kind = entry_optional_text(a, "agent")
                for target in targets:
                    if (target == name or target == pid) and kind == "agy":
                        prog = (
                            "herdr-dispatch"
                            if "herdr_dispatch" in sys.argv[0] or "herdr-dispatch" in sys.argv[0]
                            else "herdr-prompt"
                        )
                        print(
                            f"{prog}: warning: target {target!r} is an 'agy' agent; "
                            "waiting on agy agents is unreliable because they report idle while background subagents work. "
                            "Dispatch-&-Yield (--no-wait + await herdr-reply) is required.",
                            file=sys.stderr,
                        )
        except Exception:
            pass
    dispatches = [prompt_one(herdr, target, payloads[target], options, env) for target in targets]
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
