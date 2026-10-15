#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml"]
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
with the A2A Markdown frontmatter envelope (ADR 0020) — fenced by `---` and carrying
`id`, `context_id`, `status` (state plus timestamp) and `metadata` (`ticket_id`,
`sender`, `receiver`, `task_group`, `in_reply_to`) — then the Herdr skill notice on
its own line, and closes with the completion-reply contract via `herdr-reply`, so a callee can
answer the sender by name using the helper script without shell mangling. The
default envelope carries no recovery metadata (`cwd`, session, resume command); it is
retrieved just-in-time from `.lane/tasks.yaml`. Pass `--verbose` to add the
`cwd`/`resume` fields under `metadata` for debugging. The envelope is script-rendered,
never model-authored, so it cannot be forgotten. The callee always receives the full envelope
and reply contract; only the caller's own stdout shrinks. `--dry-run` prints a trimmed delivery
summary (envelope metadata, the `---` delimiter, and a body preview) without submitting, and
`--json` prints the exact rendered argv instead.

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

# The `herdr agent get` unwrap and the state vocabulary moved to `herdr_agent`; the
# fail-soft policies below stay here and catch what the seam raises. These names stay
# reachable as `herdr_prompt.<name>` for every existing consumer.
from herdr_agent import (
    AgentObservation as AgentObservation,  # noqa: F401
)
from herdr_agent import (
    has_active_subagents as has_active_subagents,  # noqa: F401
)
from herdr_agent import (
    is_agent_settled as is_agent_settled,  # noqa: F401
)
from herdr_agent import (
    is_recognized as is_recognized,  # noqa: F401
)
from herdr_agent import (
    observe_agent as observe_agent,
)
from herdr_agent import (
    read_interactive_ready as read_interactive_ready,
)
from herdr_bootstrap import load_kind_entry

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    EXIT_BLOCKED,
    EXIT_OK,
    METHOD_CONSTRAINT_EPILOG,
    STDIN,
    HerdrError,
    UsageError,
    add_shared_argument,
    current_pane_id,
    decode_payload,
    decode_response,
    diagnose_agent_not_found,
    diagnose_target_pane,
    entries,
    entry_optional_text,
    error_code,
    fetch_inventory,
    find_herdr,
    guard,
    read_payload_stream,
    require_herdr_env,
    run_herdr,
    run_herdr_checked,
    verify_target_not_bare_shell,
)

# The envelope domain moved to `herdr_envelope`; these names stay reachable as
# `herdr_prompt.<name>` for every existing consumer. Identity producers above import
# `CallerContext`, and `prompt_agents` calls `wrap_with_envelope`; the rest are explicit
# re-exports (the `name as name` form marks them as public API for the type checker).
from herdr_envelope import (  # noqa: F401
    PAGING_DELIMITER as PAGING_DELIMITER,
)
from herdr_envelope import (
    REPLY_HELPER as REPLY_HELPER,
)
from herdr_envelope import (
    SKILL_NOTICE as SKILL_NOTICE,
)
from herdr_envelope import (
    STATE_COMPLETED as STATE_COMPLETED,
)
from herdr_envelope import (
    STATE_FAILED as STATE_FAILED,
)
from herdr_envelope import (
    STATE_INPUT_REQUIRED as STATE_INPUT_REQUIRED,
)
from herdr_envelope import (
    STATE_WORKING as STATE_WORKING,
)
from herdr_envelope import (
    CallerContext as CallerContext,
)
from herdr_envelope import (
    Envelope as Envelope,
)
from herdr_envelope import (
    _scalar as _scalar,  # pyright: ignore[reportPrivateUsage]
)
from herdr_envelope import (
    _single_line as _single_line,  # pyright: ignore[reportPrivateUsage]
)
from herdr_envelope import (
    caller_anchor as caller_anchor,
)
from herdr_envelope import (
    format_delivery_summary as format_delivery_summary,
)
from herdr_envelope import (
    parse_envelope as parse_envelope,
)
from herdr_envelope import (
    render_envelope as render_envelope,
)
from herdr_envelope import (
    render_prelude as render_prelude,
)
from herdr_envelope import (
    render_reply_contract as render_reply_contract,
)
from herdr_envelope import (
    reply_state as reply_state,
)
from herdr_envelope import (
    sender_ref as sender_ref,
)
from herdr_envelope import (
    split_envelope_and_body as split_envelope_and_body,
)
from herdr_envelope import (
    utc_stamp as utc_stamp,
)
from herdr_envelope import (
    wrap_with_envelope as wrap_with_envelope,
)

BLOCKED = "blocked"
BLOCKED_CODE = "agent_blocked"
PROMPT_STATES = "idle, working, blocked, done, or unknown"
TIMEOUT_CODE = "timeout"
EXIT_WAIT_TIMEOUT = 4

READY_TIMEOUT_SECONDS = 10.0
READY_INTERVAL_SECONDS = 0.2
# Matches the window `herdr agent prompt` documents for a submission accepted from a
# non-working state ("an observed state change within 5000ms"). A shorter window reports a
# delivered prompt as unaccepted whenever the agent's state moves late (#193).
HANDSHAKE_TIMEOUT_SECONDS = 5.0
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
    add_shared_argument(
        parser,
        "label",
        help="exact pane label to resolve to a pane id, instead of TARGET",
    )
    add_shared_argument(
        parser,
        "file",
        help="payload file; '-' or omitted reads stdin verbatim",
    )
    add_shared_argument(
        parser,
        "wait",
        help="wait for the first settled state after submission",
    )
    add_shared_argument(
        parser,
        "no_wait",
        help="dispatch without waiting; fails when combined with --wait",
    )
    add_shared_argument(
        parser,
        "until",
        help=f"exact state to match after --wait, repeatable ({PROMPT_STATES})",
    )
    add_shared_argument(
        parser,
        "timeout",
        help="fail after this many milliseconds",
    )
    add_shared_argument(
        parser, "json", help="print herdr's raw JSON (and the raw argv under --dry-run)"
    )
    add_shared_argument(
        parser,
        "dry_run",
        help="print a trimmed delivery summary, submit nothing (argv with --json)",
    )
    add_shared_argument(
        parser,
        "no_caller_context",
        help="send the payload verbatim without the A2A envelope and reply contract",
    )
    add_shared_argument(
        parser,
        "verbose",
        help=(
            "include cwd/resume recovery metadata under the envelope metadata; "
            "the default envelope carries recovery metadata nowhere"
        ),
    )
    return parser


def read_payload(source: str | None) -> str:
    """Read the payload verbatim; only the choice of stream is validated, not its content."""
    payload = decode_payload(
        read_payload_stream(
            source,
            tty_refusal="no --file given and stdin is a terminal; pass --file PATH or pipe the payload",
        )
    )
    if not payload.strip():
        raise UsageError(
            "payload is empty; refusing to submit an empty prompt. The payload comes from "
            "--file PATH or stdin — positional arguments are TARGETs"
        )
    return payload


def build_resume_cmd(kind: str | None, session_id: str | None) -> str | None:
    """Build the agent-native resume command string for the caller, if known."""
    if kind == "agy":
        return f"agy --conversation={session_id}" if session_id else None
    if kind == "pi":
        # `--resume` is a value-less picker: `pi --resume <path>` opens the picker instead of
        # re-attaching (verified 2026-10-09 in a non-TTY `--print` run). `--session` takes the
        # session file or the id, so one form covers both (#211).
        return f"pi --session {session_id}" if session_id else None
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


def reject_message_like_targets(targets: Sequence[str]) -> None:
    """Refuse a TARGET containing whitespace, before the payload is read (#212).

    No agent name or pane id carries a space, so such a target is provably a misread message.
    Reporting it here keeps the first mistake (a positional payload) from being blamed on the
    second (an empty payload), and it costs no `herdr` call on the happy path.
    """
    for target in targets:
        if any(character.isspace() for character in target):
            raise UsageError(
                f"target {target!r} contains whitespace, so it cannot be an agent name or pane "
                "id; it reads like a message, and the payload comes only from --file PATH or "
                "stdin"
            )


def fetch_agent_revision(
    herdr: str, target: str, env: Mapping[str, str]
) -> tuple[str | None, str | None]:
    """Fetch (revision, pane_id) from `herdr agent get <target>`, if available."""
    try:
        obs = observe_agent(herdr, target, env)
    except Exception:
        return None, None
    return obs.revision, obs.pane_id


def _format_seconds(seconds: float) -> str:
    """Render a timeout without a trailing `.0` so diagnostics read `10s`, not `10.0s`."""
    return f"{seconds:g}"


def resolve_agent_kinds(
    herdr: str, targets: Sequence[str], env: Mapping[str, str]
) -> dict[str, str | None]:
    """Map each target to its agent kind from one `herdr agent list`; None when unresolved.

    Read only on a failure path — the unconfirmed handshake and the wait timeout — to decide
    whether a revision-based re-check can ever succeed. A read that fails, or a target the
    list does not hold, leaves that target unresolved; the caller then keeps the previous
    advice rather than guessing about the kind.
    """
    kinds: dict[str, str | None] = dict.fromkeys(targets)
    try:
        agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
    except HerdrError:
        return kinds
    for target in targets:
        for agent in agents:
            if target in (
                entry_optional_text(agent, "name"),
                entry_optional_text(agent, "pane_id"),
            ):
                kinds[target] = entry_optional_text(agent, "agent")
                break
    return kinds


def revision_can_move(kind: str | None) -> bool:
    """Whether a revision increment is a usable acceptance signal for this kind.

    `false` for a kind `references/kinds.yaml` declares `revision_moves: false` (agy, #238): its
    revision never moves, so the handshake's revision half can never fire and a revision-based
    re-check (`herdr-wait`) is unsatisfiable there (exit 2) — only the status half remains. An
    unresolved kind, or a config this process cannot read, defaults to true, keeping the
    previous advice whenever the kind is unknown.
    """
    if not kind:
        return True
    try:
        return load_kind_entry(kind).revision_moves
    except UsageError:
        return True


def kind_lifecycle_bridge(kind: str | None) -> str | None:
    """The bridge script `references/kinds.yaml` declares for this kind, if any (#238).

    The bridge is a per-kind fact, not a constant here, so a second revision-static kind is
    pointed at its own bridge and a kind that declares none is not sent to another kind's. An
    unresolved kind, or a config this process cannot read, reads as no bridge, keeping the
    advice bridge-neutral rather than guessing.
    """
    if not kind:
        return None
    try:
        return load_kind_entry(kind).lifecycle_bridge
    except UsageError:
        return None


def revision_static_surface(kind: str | None) -> str:
    """The status surface advice may trust for a kind whose revision cannot move (#238).

    Derived from the kind's own contract: a kind that declares a `lifecycle_bridge` is named
    with that bridge, and a kind that declares none gets phrasing that names no bridge at all.
    """
    bridge = kind_lifecycle_bridge(kind)
    if bridge:
        return f"the {kind} bridge's status title ({bridge})"
    return "the kind's own status surface"


def agent_readiness(
    herdr: str, target: str, env: Mapping[str, str]
) -> tuple[bool, str | None, str | None]:
    """Probe `herdr agent get <target>`; return (ready, status, revision).

    ready is true only when the agent is settled (`idle`/`done`) and its
    `interactive_ready` field is not explicitly false (a missing field counts as
    ready, for back-compat). A failed read — non-zero exit, unreadable response,
    or missing record — is not ready.
    """
    try:
        obs = observe_agent(herdr, target, env)
    except HerdrError:
        return (False, None, None)
    ready = obs.status in ("idle", "done") and obs.interactive_ready is not False
    return (ready, obs.status, obs.revision)


def _read_interactive_ready(herdr: str, target: str, env: Mapping[str, str]) -> bool | None:
    """Read only the `interactive_ready` flag for refusal messaging (never a gate).

    Returns False only when the field is explicitly false, True when explicitly
    true, and None when the probe is unreadable or the field is absent. Called
    once, after the readiness loop has already refused, so it cannot change
    where the gate fires.
    """
    return read_interactive_ready(herdr, target, env)


def wait_for_ready(
    herdr: str,
    target: str,
    env: Mapping[str, str],
    *,
    timeout: float = READY_TIMEOUT_SECONDS,
    interval: float = READY_INTERVAL_SECONDS,
) -> str | None:
    """Block until the target settles, else fail reporting the observed status.

    The loop is attempt-counted (never wall-clocked) so a monkeypatched `_sleep`
    runs it instantly; the immediate first probe means a settled agent never sleeps.
    The refusal names what the readiness read observed — never a hypothesized cause.
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
    status_label = last_status or "unknown"
    held = f"{_format_seconds(timeout)}s over {attempts} readiness probes"
    interactive_ready = _read_interactive_ready(herdr, target, env)
    if interactive_ready is False:
        detail = (
            "observed BLOCKED-ON-INPUT — the readiness read reports "
            f"interactive_ready=false (status={status_label}); open the pane and "
            "clear the pending input, then retry"
        )
    elif last_status == "working":
        detail = (
            "observed BUSY — the readiness read reports status='working', held for "
            f"the full {held}: a turn is in progress; wait and retry after a longer "
            "interval, do not inject mid-turn"
        )
    else:
        detail = (
            f"observed status={status_label!r} with no conclusive busy/blocked signal "
            "(the readiness read cannot distinguish a busy turn from blocked-on-input "
            "here); wait and re-check the pane before retrying"
        )
    raise UsageError(
        f"target {target!r} did not settle for prompt delivery within "
        f"{_format_seconds(timeout)}s (last status={status_label}, held for the full "
        f"{held}): {detail}"
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
    if not options.dry_run:
        reject_message_like_targets(options.targets)
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
    herdr: str,
    target: str,
    payload: str,
    options: Options,
    env: Mapping[str, str],
    *,
    body: str,
    source: str,
    caller_ref: str,
    pane_hint: str | None = None,
) -> Dispatch:
    """Deliver the payload to one target, mapping herdr's answer onto a Dispatch.

    `payload` is the full wrapped text the callee receives; `body` is the original payload,
    `source` names where it came from, and `caller_ref` is the caller's `[You: …]` self-anchor,
    all used only for the caller-facing delivery summary. `pane_hint` resolves the target's pane
    for a `--dry-run` status line, where no live `agent get` runs. The callee delivery is
    byte-exact and untouched — only this caller's stdout changes shape (#259).
    """
    argv = build_prompt_argv(
        herdr,
        target,
        payload,
        wait=options.wait,
        until=options.until,
        timeout=options.timeout,
    )
    dry_pane_str = f" ({pane_hint})" if pane_hint and pane_hint != target else ""
    anchor = f"[You: {caller_ref}] " if caller_ref else ""
    if options.dry_run:
        if options.json:
            print(json.dumps(argv))
        else:
            status = f"{anchor}dry-run: would prompt {target}{dry_pane_str}"
            print(format_delivery_summary(status, payload, body, source))
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
        # Exit 0 from `herdr agent prompt` confirms acceptance; this observation only reports
        # it. Failing here, or re-sending to "confirm", both re-created #193: a delivered
        # prompt reported as dropped, and a duplicate injection.
        _, last_status, _ = agent_readiness(herdr, target, env)
        kind = resolve_agent_kinds(herdr, [target], env)[target]
        if revision_can_move(kind):
            remedy = "check with herdr-wait before resubmitting"
        else:
            # A revision-0 kind (#238): its revision never moves, so a wanted state is
            # unsatisfiable and re-reading the state feed can confirm nothing. Name the
            # signal that is trustworthy there instead of the one that structurally cannot be.
            # Which signal that is comes from the kind's own contract, never from a constant.
            remedy = (
                f"confirm through {revision_static_surface(kind)}, which is trustworthy "
                "where the raw state feed is not, and await the reply callback; a state "
                "re-check cannot confirm delivery for this kind"
            )
        print(
            f"herdr-prompt: warning: acceptance was not confirmed within "
            f"{_format_seconds(HANDSHAKE_TIMEOUT_SECONDS)}s for {target} "
            f"(last status={last_status or 'unknown'}, revision unchanged); the CLI accepted "
            f"the payload — {remedy}",
            file=sys.stderr,
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
        status = f"{anchor}prompted {target}{pane_str}  bytes={size}{rev_str}{suffix}"
        print(format_delivery_summary(status, payload, body, source))
    return Dispatch(target, state=state, blocked=state == BLOCKED)


def prompt_agents(options: Options, env: Mapping[str, str]) -> int:
    if options.wait and options.no_wait:
        raise UsageError("pass either --wait or --no-wait, not both")
    require_herdr_env(env)
    herdr = find_herdr(env)
    targets = resolve_targets(options, herdr, env)
    payload = read_payload(options.file)
    body = payload
    if options.file and options.file != STDIN:
        source = f"File: {options.file}"
    else:
        source = f"Payload: stdin ({len(payload.encode('utf-8'))} bytes)"
    if options.no_caller_context:
        for target in targets:
            print(
                f"herdr-prompt: warning: --no-caller-context drops the Sender/Receiver envelope and reply contract for target {target!r}; target cannot call back",
                file=sys.stderr,
            )
        payloads = {target: payload for target in targets}
        # The anchor names the caller to the caller; without the envelope path there is no
        # inventory lookup, so the env pane id is the only identity available without a call.
        caller_ref = env.get("HERDR_PANE_ID", "")
        pane_hints: dict[str, str | None] = dict.fromkeys(targets)
    else:
        panes, agents = fetch_inventory(herdr, env)
        caller = resolve_caller(herdr, env, inventory=(panes, agents))
        receivers = {target: resolve_receiver(panes, agents, target) for target in targets}
        group_members = resolve_group_members(panes, agents, caller.pane_id, targets)
        payloads = {
            target: wrap_with_envelope(
                payload,
                caller,
                group_members=group_members,
                receiver=receivers[target] or target,
                include_recovery=options.verbose,
                ticket_id=options.ticket_id,
                task_id=options.task_id,
                task_group=options.task_group,
                tab_id=caller.tab_id,
            )
            for target in targets
        }
        caller_ref = caller_anchor(caller)
        pane_hints = {t: r.pane_id if r is not None else None for t, r in receivers.items()}
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
    dispatches = [
        prompt_one(
            herdr,
            target,
            payloads[target],
            options,
            env,
            body=body,
            source=source,
            caller_ref=caller_ref,
            pane_hint=pane_hints[target],
        )
        for target in targets
    ]
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
        # A revision-0 kind (#238) cannot be re-checked by state: its revision never moves, so a
        # wanted state is unsatisfiable and `herdr-wait` exits 2. Advice goes per target, and
        # only the targets whose kind can move are told to resume with `herdr-wait`.
        kinds = resolve_agent_kinds(herdr, timed_out, env)
        movable = [target for target in timed_out if revision_can_move(kinds[target])]
        static = [target for target in timed_out if not revision_can_move(kinds[target])]
        advice = "working asynchronously. Yield turn and await reply callback"
        if movable:
            advice += (
                f", or resume with herdr-wait {', '.join(movable)} --timeout <ms> "
                "instead of resubmitting"
            )
        if static:
            advice += (
                f"; {', '.join(static)} cannot be re-checked that way — the kind's revision "
                "never moves, so "
                + "; ".join(
                    f"confirm through {revision_static_surface(kinds[target])} and await the "
                    "reply callback instead"
                    for target in static
                )
            )
        raise WaitTimeout(f"prompt delivered to {names} but {hint}; {advice}")
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
