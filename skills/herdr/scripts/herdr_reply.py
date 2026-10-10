#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml"]
# ///
"""herdr-reply — send a completion reply callback to a caller agent without shell mangling.

Delivers `<STATUS> <artifacts> <issues>` or a result payload to the caller's agent
name, wrapped in the same timestamped `Routing:`/`Hierarchy:`/`Protocol:` envelope
`herdr-prompt` uses, so the party reading a reply always knows who reported and to
whom. When the sender holds an active lease, its `Ticket-ID`/`Task-ID` ride along as
`Ticket-ID:` and `In-Reply-To:` correlation lines. The envelope is script-rendered,
never model-authored, so it cannot be forgotten.

Prompt text is never provenance (#231). Before the prompt is sent the payload is persisted
as a store record — a body file plus a metadata ledger row carrying its digest, shape, and
cited artifacts — and a short pointer rides between the envelope and the body:

  * `COMPLETE` cites an evidence-shaped section; the caller trusts the stored record and
    re-derives evidence from the artifacts.
  * `INCOMPLETE` is a COMPLETED payload with no evidence section; it is recorded as
    incomplete and the task state is not advanced.
  * `NOT RECORDED` means the store could not resolve or the write failed: delivery continues
    body-only, but the prompt is the only copy.

Persist first, poke second: every store touch degrades to the NOT RECORDED pointer rather
than blocking delivery, so a reply is still delivered (exit 0, one `agent prompt`, body last)
when the store cannot resolve.

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
import hashlib
import json
import os
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    EXIT_BLOCKED,
    EXIT_OK,
    EXIT_USAGE,
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
from herdr_lease import (
    REPLIES_FILE_LANE,
    get_lease,
    get_reply,
    get_task,
    record_event,
    record_reply,
    release_lease,
    resolve_base_dir,
)
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
    verbose: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-reply",
        description="Deliver a completion reply to a caller agent without shell mangling.",
        epilog=(
            "exit status: 0 accepted, 1 herdr failure, 2 usage or precondition, "
            "3 target needs human input, 4 reply delivered but wait timed out\n\n"
            "lease bookkeeping is best-effort and never blocks delivery: an unresolvable lease\n"
            "store is reported on stderr, skipping the correlation lookup, trajectory note, or\n"
            "release. A skipped correlation drops Ticket-ID/In-Reply-To from the envelope; the\n"
            "reply still correlates by pane/target\n\n" + METHOD_CONSTRAINT_EPILOG
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
    _ = parser.add_argument(
        "--verbose",
        action="store_true",
        help="restore the Runtime: Cwd/Resume block in the rendered envelope (default trimmed)",
    )
    return parser


STATUS_MAP: dict[str, str] = {
    "COMPLETED": "completed",
    "BLOCKED": "blocked",
    "REJECTED": "rework",
}


def parse_status_line(payload: str) -> tuple[str | None, str | None, str | None]:
    """Map the payload's first non-empty line onto (status, sha, status_line).

    The first token is upper-cased with a trailing `:` stripped: COMPLETED/BLOCKED/
    REJECTED map to completed/blocked/rework; anything else maps to None. For COMPLETED,
    the second token is treated as the commit SHA when present.
    """
    for raw_line in payload.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        tokens = line.split()
        token = tokens[0].rstrip(":").upper()
        mapped = STATUS_MAP.get(token)
        sha = tokens[1] if mapped == "completed" and len(tokens) > 1 else None
        return mapped, sha, line
    return None, None, None


# ── payload shape (#231): a COMPLETED reply must cite evidence ───────────────────────

EVIDENCE_KEYWORDS = frozenset(
    {
        "evidence",
        "verification",
        "verified",
        "verify",
        "gate",
        "gates",
        "proof",
        "witness",
        "reproduction",
        "repro",
        "artifact",
        "artifacts",
        "test",
        "tests",
        "pytest",
        "check",
        "checks",
        "log",
        "logs",
    }
)

FENCE_MARKER = "```"
ARTIFACT_LIMIT = 24
_LABEL_MAX_LENGTH = 60
_TRAILING_PUNCTUATION = ".,;:!?)]}'\">`"
_MARKDOWN_DECORATION = "*_`~#>[]()"
_FENCE_RE = re.compile(r"^```")
_ATX_RE = re.compile(r"^(#{1,6})[ \t]+(\S.*)$")
_BOLD_RE = re.compile(r"^\*\*[ \t]*(.*?)[ \t]*\*\*:?[ \t]*(.*)$")
_LABEL_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*(?:[ \t]+[A-Za-z0-9_-]+)*)[ \t]*:[ \t]*(.*)$")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_WORD_RE = re.compile(r"\w")
# The shape table tests pin exactly these outcomes:
#
#   payload                                shape        evidence heading
#   COMPLETED + "## Evidence" + body       complete     Evidence
#   COMPLETED + "**Evidence:** 660 passed" complete     Evidence
#   COMPLETED + "Gates:" + a command line  complete     Gates
#   COMPLETED + "### Test output" + body   complete     Test output
#   COMPLETED + a fence with a non-blank   complete     ```
#   COMPLETED + "## Verification" + body   complete     Verification
#   COMPLETED                              incomplete   None
#   COMPLETED abc1234                      incomplete   None
#   COMPLETED + "## Notes" + body          incomplete   None
#   COMPLETED + "## Evidence" then heading incomplete   None   (empty body)
#   COMPLETED + "## Next steps" + body     incomplete   None
#   BLOCKED / REJECTED / no status line    n/a          None
#
# This is a *shape* check, not a quality gate: it asks whether a COMPLETED payload cites
# evidence, never whether that evidence is good. It runs only when the first line maps to
# `completed`; a BLOCKED/REJECTED reply (or one with no status line) is `n/a` and its
# behaviour is unchanged. A heading ATX form carries no inline text of its own, so `## Notes`
# never counts by itself — only a following non-blank body line, a bold/label inline tail, or
# a fence does.


def _strip_title(text: str) -> str:
    """The heading's identifying text: markdown decoration and a trailing colon removed."""
    return text.strip().strip(_MARKDOWN_DECORATION).rstrip(":").strip()


def _normalize(text: str) -> list[str]:
    """Lowercase, drop markdown decoration, split on non-alphanumerics."""
    cleaned = text.casefold()
    for character in _MARKDOWN_DECORATION:
        cleaned = cleaned.replace(character, " ")
    return [word for word in _NON_ALNUM_RE.split(cleaned) if word]


def _has_keyword(words: Sequence[str]) -> bool:
    return any(word in EVIDENCE_KEYWORDS for word in words)


def _parse_heading(line: str) -> tuple[str, str, list[str]] | None:
    """Return (title, inline text after the marker, normalized words) for a heading line.

    A line is a heading when it is ATX (`## Title`), bold (`**Title**`, optional `:`), or a
    `Word[Word …]:` label no longer than 60 characters. ATX headings carry no inline text:
    the remainder of the line *is* the title, which is why `## Evidence` alone is not complete.
    """
    match = _ATX_RE.match(line)
    if match:
        title = _strip_title(match.group(2))
        return title, "", _normalize(title)
    match = _BOLD_RE.match(line)
    if match:
        title = _strip_title(match.group(1))
        return title, match.group(2).strip(), _normalize(title)
    match = _LABEL_RE.match(line)
    if match:
        label = match.group(1)
        if len(label) <= _LABEL_MAX_LENGTH:
            title = label.strip()
            return title, match.group(2).strip(), _normalize(title)
    return None


def evidence_section(payload: str) -> str | None:
    """The first evidence-shaped section's heading text, else None.

    Scans the payload in document order and returns the first section that makes it
    evidence-shaped: a heading whose normalized words contain an `EVIDENCE_KEYWORDS` entry
    with an inline tail (`**Evidence:** 660 passed`) or a body line before the next heading,
    or a fenced code block with at least one non-blank line. A fenced block returns the fence
    marker (`"```"`) — it has no heading text of its own. A fence closes the current heading
    scope, and an empty keyword heading (immediately followed by another heading) is skipped.
    """
    current_title: str | None = None
    current_is_evidence = False
    in_fence = False
    fence_has_content = False
    for raw_line in payload.splitlines():
        line = raw_line.strip()
        if _FENCE_RE.match(line):
            if in_fence:
                if fence_has_content:
                    return FENCE_MARKER
                in_fence = False
                fence_has_content = False
            else:
                in_fence = True
                fence_has_content = False
                current_title = None
                current_is_evidence = False
            continue
        if in_fence:
            if line:
                fence_has_content = True
            continue
        heading = _parse_heading(line)
        if heading is not None:
            title, inline, words = heading
            if _has_keyword(words):
                if inline:
                    return title
                current_title = title
                current_is_evidence = True
            else:
                current_title = None
                current_is_evidence = False
            continue
        if not line:
            continue
        if current_is_evidence and current_title is not None:
            return current_title
    if in_fence and fence_has_content:
        return FENCE_MARKER
    return None


def payload_shape(payload: str) -> tuple[str, str | None]:
    """(shape, evidence_heading) where shape is "complete", "incomplete" or "n/a".

    The evidence requirement applies only when `parse_status_line` maps the first line to
    `completed`; every other payload is `"n/a"` with no behaviour change. A shape check, not
    a quality gate: it never inspects whether the cited evidence is any good.
    """
    mapped, _sha, _line = parse_status_line(payload)
    if mapped != "completed":
        return "n/a", None
    heading = evidence_section(payload)
    if heading is None:
        return "incomplete", None
    return "complete", heading


# ── persist first, then poke (#231) ─────────────────────────────────────────────────

COMPLETE_POINTER_TAIL = (
    "Provenance: the stored record, not this prompt; re-derive evidence from the cited artifacts."
)
INCOMPLETE_POINTER = (
    "Payload: INCOMPLETE — COMPLETED carries no evidence section, so it is recorded as "
    "incomplete (shape=incomplete) and the task state is NOT advanced to completed."
)
NOT_RECORDED_POINTER = (
    "Payload: NOT RECORDED — delivery continues body-only ({reason}); no store record, "
    "task state unchanged, and this prompt is the only copy."
)


def _one_line(text: str, limit: int = 160) -> str:
    """Collapse an exception message onto one line so it can ride inside a pointer."""
    return " ".join(text.split())[:limit]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _slug(value: str | None) -> str:
    """A filesystem-safe fragment for a record id; `unknown` when there is nothing to slug."""
    if not value:
        return "unknown"
    cleaned = _NON_ALNUM_RE.sub("-", value.casefold()).strip("-")
    return cleaned or "unknown"


def extract_artifacts(payload: str) -> list[str]:
    """Path-like tokens cited in the payload: deduped, sorted, capped at 24, no URLs."""
    found: set[str] = set()
    for token in payload.split():
        if "://" in token:
            continue
        cleaned = token.rstrip(_TRAILING_PUNCTUATION)
        if "/" not in cleaned or not _WORD_RE.search(cleaned):
            continue
        found.add(cleaned)
    return sorted(found)[:ARTIFACT_LIMIT]


def build_reply_entry(
    payload: str,
    *,
    sender: str | None,
    caller: str | None,
    ticket_id: str | None,
    in_reply_to: str | None,
    mapped: str | None,
    sha: str | None,
    status_line: str | None,
    shape: str,
    evidence: str | None,
) -> dict[str, Any]:
    """The ledger row for one reply: metadata only, never the body text."""
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return {
        "id": f"{stamp}-{_slug(sender)}-{digest[:8]}",
        "recorded_at": _now_iso(),
        "sender": sender,
        "caller": caller,
        "ticket_id": ticket_id,
        "in_reply_to": in_reply_to,
        "status_line": status_line,
        "status": mapped,
        "shape": shape,
        "evidence": evidence,
        "sha": sha,
        "digest": digest,
        "bytes": len(payload.encode("utf-8")),
        "artifacts": extract_artifacts(payload),
    }


def persist_reply(
    entry: Mapping[str, Any],
    body: str,
    *,
    env: Mapping[str, str],
) -> tuple[dict[str, Any] | None, str | None]:
    """Persist the record, best-effort; `(stored entry, None)` or `(None, one-line reason)`.

    Never fatal by contract (#229): a store this process cannot resolve degrades to the
    NOT RECORDED pointer silently, because the lease steps already report that same
    unresolvable anchor; a resolvable store whose write fails is reported once via
    `report_lease_trouble` and degrades the same way. The reply is delivered either way.
    """
    try:
        _ = resolve_base_dir(env=env)
    except Exception as exc:
        return None, _one_line(str(exc))
    try:
        return record_reply(entry, body, env=env), None
    except Exception as exc:
        report_lease_trouble("reply record", exc)
        return None, _one_line(str(exc))


def pointer_block(
    *,
    shape: str,
    evidence: str | None,
    stored: Mapping[str, Any] | None,
    reason: str | None,
) -> str | None:
    """The provenance pointer inserted between the envelope and the body, or None.

    Complete and incomplete replies carry a pointer; a store failure carries the NOT
    RECORDED pointer; a `n/a` reply (BLOCKED/REJECTED) that was recorded carries none, so
    its delivered payload is unchanged (#231).
    """
    if stored is None:
        return NOT_RECORDED_POINTER.format(reason=reason or "store unavailable")
    if shape == "complete":
        return (
            f'Payload: COMPLETE — evidence "{evidence}"; record={stored["id"]} '
            f"store={stored['payload']} sha256={stored['digest']}\n"
            f"{COMPLETE_POINTER_TAIL}"
        )
    if shape == "incomplete":
        return (
            f"{INCOMPLETE_POINTER}\n"
            f"Record: {stored['payload']} sha256={stored['digest']} store={REPLIES_FILE_LANE} — "
            "re-derive from the cited artifacts; this prompt is not provenance."
        )
    return None


def recovery_file_arg(options: Options) -> str:
    """The `--file` value for a recovery hint, or `<reply>` when reading stdin/positional."""
    if options.file and options.file != STDIN:
        return options.file
    return "<reply>"


def caller_recovery_for_reply(herdr: str, env: Mapping[str, str]) -> dict[str, object] | None:
    """Resolve the caller-recovery metadata JIT: sender lease task_id -> task caller_recovery."""
    try:
        sender = resolve_current_agent(herdr, env)
        if not sender:
            return None
        lease = get_lease(sender, env=env)
        if not isinstance(lease, dict):
            return None
        task_id = lease.get("task_id")
        if not isinstance(task_id, str):
            return None
        task = get_task(task_id, env=env)
        if not isinstance(task, dict):
            return None
        recovery = task.get("caller_recovery")
        if isinstance(recovery, dict) and recovery:
            return dict(recovery)
        return None
    except Exception:
        return None


def format_reply_recovery_diagnostic(
    target: str, recovery: Mapping[str, object], file_arg: str
) -> str:
    """Render the exact copy-paste recovery block for an exited reply target."""
    pane_id = recovery.get("pane_id") or "<pane>"
    kind = recovery.get("kind") or "<kind>"
    resume_cmd = recovery.get("resume_cmd")
    lines = [
        f"herdr-reply: target agent {target!r} in pane {pane_id} has exited.",
        "Suggested recovery:",
        "  1. Auto-revive & deliver: uv run ~/.agents/skills/herdr/scripts/herdr_reply.py "
        f"{target} --file {file_arg} --auto-start {kind}",
    ]
    if resume_cmd:
        lines.append(f"  2. Or resume manually in pane {pane_id}: {resume_cmd}")
    return "\n".join(lines)


def emit_recovery_diagnostic(
    herdr: str, env: Mapping[str, str], target: str, file_arg: str
) -> bool:
    """Print the exact recovery block to stderr when the sender's task stored one.

    Returns True when a recovery block was emitted (the caller should stop delivery).
    """
    recovery = caller_recovery_for_reply(herdr, env)
    if recovery is None:
        return False
    print(format_reply_recovery_diagnostic(target, recovery, file_arg), file=sys.stderr)
    return True


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


def report_lease_trouble(action: str, exc: BaseException) -> None:
    """One stderr line for a best-effort lease step that could not run (#229).

    Lease bookkeeping is bookkeeping: an unresolvable store, an unreadable state file, or
    a herdr failure must never decide whether a reply is delivered. Every caller keeps
    going after this line, and the line names what was skipped and why.
    """
    print(f"herdr-reply: {action} skipped: {exc}", file=sys.stderr)


def release_active_lease(herdr: str, env: Mapping[str, str]) -> None:
    """Release active task lease for the replying sender (current agent or current pane).

    NEVER release target's lease: target is the caller (e.g. task-manager).
    Only the sender's lease is released upon sending a reply.

    Best-effort by contract: the reply has already been delivered, so an unresolvable
    store is reported on stderr and never raised (#229) — a lease that cannot be found is
    a lease to be reconciled by hand, not a reason to hide the failure.
    """
    try:
        sender = resolve_current_agent(herdr, env)
        if not sender:
            sender = env.get("HERDR_PANE_ID")
        if sender:
            _ = release_lease(sender, env=env)
    except Exception as exc:
        report_lease_trouble("lease release", exc)


def _recorded_and_advanceable(
    record_id: str | None, shape: str | None, env: Mapping[str, str]
) -> bool:
    """Whether a persisted record permits advancing the sender's task (#231).

    Prompt text is never provenance: without a record id, or with an id the store does not
    hold, nothing advances. A record whose shape is `incomplete` carries the verdict itself —
    no `completed` event, no state advance, and no invented canonical status. A shape-less
    caller (legacy) and a `n/a` or `complete` record advance as before.
    """
    if not record_id:
        return False
    if shape == "incomplete":
        return False
    try:
        return get_reply(record_id, env=env) is not None
    except Exception as exc:
        report_lease_trouble("reply record lookup", exc)
        return False


def record_sender_status(
    herdr: str,
    env: Mapping[str, str],
    mapped: str | None,
    sha: str | None,
    status_line: str | None,
    *,
    record_id: str | None = None,
    shape: str | None = None,
) -> None:
    """Append the sender's completion event to its task trajectory, when one is leased.

    Resolves the sender's own lease first, then gates the advance on the persisted record
    (#231): a missing `record_id`, an id the store does not hold, or an `incomplete` shape
    appends no event and changes no state. The lease lookup still runs ahead of the gate, so
    an unresolvable store reports the same `trajectory note` skip it always did. Non-fatal by
    contract: a missing lease or a store this process cannot resolve is still a reply.
    """
    if not mapped:
        return
    try:
        sender = resolve_current_agent(herdr, env)
        if not sender:
            return
        lease = get_lease(sender, env=env)
        if not isinstance(lease, dict):
            return
    except Exception as exc:
        report_lease_trouble("trajectory note", exc)
        return

    if not _recorded_and_advanceable(record_id, shape, env):
        return

    try:
        task_id = lease.get("task_id")
        if isinstance(task_id, str):
            _ = record_event(
                task_id,
                mapped,
                note=status_line,
                sha=sha,
                actor=sender,
                event=mapped,
                env=env,
            )
    except Exception as exc:
        report_lease_trouble("trajectory note", exc)


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
            if emit_recovery_diagnostic(herdr, env, target, recovery_file_arg(options)):
                return EXIT_USAGE
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
    mapped, sha, status_line = parse_status_line(payload)
    sender = resolve_current_agent(herdr, env)
    lease: dict[str, object] | None = None
    if sender:
        try:
            stored = get_lease(sender, env=env)
        except Exception as exc:
            report_lease_trouble("lease correlation", exc)
        else:
            lease = stored if isinstance(stored, dict) else None
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
        include_recovery=options.verbose,
        ticket_id=ticket_id,
        in_reply_to=in_reply_to,
        tab_id=caller_ctx.tab_id,
    )
    shape, evidence = payload_shape(payload)
    prelude = f"{utc_stamp()}\n{reply_envelope}\n\n"
    record_id: str | None = None
    if options.dry_run:
        # A dry run submits nothing, so it records nothing: the payload stays pointer-free.
        delivered = f"{prelude}{payload}"
    else:
        stored: dict[str, Any] | None
        reason: str | None
        try:
            entry = build_reply_entry(
                payload,
                sender=sender,
                caller=target,
                ticket_id=ticket_id,
                in_reply_to=in_reply_to,
                mapped=mapped,
                sha=sha,
                status_line=status_line,
                shape=shape,
                evidence=evidence,
            )
            stored, reason = persist_reply(entry, payload, env=env)
        except Exception as exc:
            report_lease_trouble("reply record", exc)
            stored, reason = None, _one_line(str(exc))
        if stored is not None:
            record_id = str(stored["id"])
        pointer = pointer_block(shape=shape, evidence=evidence, stored=stored, reason=reason)
        # The pointer rides between the envelope and the body; the body stays last.
        delivered = f"{prelude}{pointer}\n\n{payload}" if pointer else f"{prelude}{payload}"
    payload = delivered

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
            record_sender_status(
                herdr, env, mapped, sha, status_line, record_id=record_id, shape=shape
            )
            release_active_lease(herdr, env)
            raise WaitTimeout(
                f"reply delivered to {target} but wait timed out; caller is processing asynchronously"
            )
        if code == "agent_not_found":
            if emit_recovery_diagnostic(herdr, env, target, recovery_file_arg(options)):
                return EXIT_USAGE
            diag = diagnose_agent_not_found(herdr, target, env)
            if diag:
                raise UsageError(diag)
        raise HerdrError(f"herdr agent prompt {target} failed: {detail}")

    record_sender_status(herdr, env, mapped, sha, status_line, record_id=record_id, shape=shape)
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
