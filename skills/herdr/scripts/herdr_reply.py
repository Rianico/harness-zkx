#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml"]
# ///
"""herdr-reply — send a completion reply callback to a caller agent without shell mangling.

Delivers `<STATUS> <artifacts> <issues>` or a result payload to the caller's agent
name, wrapped in the same A2A Markdown frontmatter envelope `herdr-prompt` uses — its
`status.state` carries the lifecycle state the reply's first token names — so the party
reading a reply always knows who reported and to
whom. When the sender holds an active lease, its task and ticket ride along as the
envelope's `id`, `metadata.ticket_id`, and `metadata.in_reply_to` fields. The envelope is script-rendered,
never model-authored, so it cannot be forgotten.

The record's task linkage is resolved from the whole store, not just the lease (#246 D1.2):
an explicit `--ticket <id>` (or `--in-reply-to <record-id>`) wins, else the sender's active
lease. The ticket signal comes from the rendered dispatch contract, which binds `--ticket`
(#246 E1.1), so a reply that names no ticket is never guessed at: with no lease and no flag it
is recorded unlinked, mutating no task. Zero, one, or several open tasks — or an explicit name
the sender does not hold open — records the reply unlinked with one warning line, never a
guess, so a second reply for the same ticket still advances the task through `--ticket`
instead of losing the linkage when the first reply consumes the lease. Every unlinked line
leads with a stable severity
marker (#246 D1.5): "open work refused" when the step refused to bind what it was told (open
work it would not guess at, or a flag that names no open task of the sender), "nothing to
link" when there was nothing to link, and "sender or store unreadable" when there was no
answer at all (no sender resolved, or the anchor/store could not be read). An unlinked warning
claims a record only when one was written — that clause is appended after the store answers,
so it can never contradict the `NOT RECORDED` pointer delivered in the same run. Every warning
now accompanies an unlinked reply; the explicit `--ticket`/`--in-reply-to` bindings stay
silent, because they are the caller's instruction.

Prompt text is never provenance (#231). Before the prompt is sent the payload is persisted
as a store record — a body file plus one metadata-only index sidecar carrying its digest,
shape, and cited-artifact count — and a short pointer rides between the envelope and the body:

  * `COMPLETE` cites an evidence-shaped section; the caller trusts the stored record and
    re-derives evidence from the artifacts.
  * `INCOMPLETE` is a COMPLETED payload with no evidence section; it is recorded as
    incomplete and the task state is not advanced.
  * `NOT RECORDED` means the store could not resolve, its index could not be read, the write
    failed, or the record did not resolve back through the reader: delivery continues, but
    the prompt is the only copy.

Persist first, poke second: every store touch degrades to the NOT RECORDED pointer rather
than blocking delivery, so a reply is still delivered (exit 0, one `agent prompt`, body last)
when the store cannot resolve. The pointer only ever names a record the reader can produce:
the store is read before it is written (an unreadable index is preserved, never clobbered),
and the row that was written is re-resolved through the same `get_reply` the reader uses.

Before any of that, the outbound payload itself is checked (#247 D2): every *backticked* 7-40
lowercase-hex token in the *body* must name a commit (`git rev-parse --verify <token>^{commit}`
against the lane's repository anchor, never the ambient working directory, so one payload gets one
verdict from any directory), because a backticked hex token is an instruction — "do not
rewrite `8d9fa742`" — and an instruction that names no commit points at nothing. Only the body is
checked: the envelope is composed later and is never inspected. Hex left bare
in prose stays prose — UUID fragments inside cited paths are never read as
citations — but a backticked review-record id or mutant label IS refused: the
broad trigger reads it exactly like a drifted commit abbreviation, and the
sanctioned route is to waive that token by name with `--allow-unresolvable-sha`.
An unresolvable token is refused loudly (exit 2, naming the token and
the payload path) before any record exists, so a refused payload consumes no lease; `--dry-run`
reports it the same way instead of accepting the payload silently. A git override that moves the
object store the probe reads (`GIT_DIR`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY`,
`GIT_ALTERNATE_OBJECT_DIRECTORIES`) skips the check loudly, naming every unchecked token, rather
than let one resolve in another repository; the two verdict-neutral location overrides
(`GIT_WORK_TREE`, `GIT_INDEX_FILE`) never skip for that reason alone. A genuinely intentional
non-resolving token is waived by name with `--allow-unresolvable-sha <TOKEN>`, and every waiver
is reported on stderr — never a silent bypass.

    herdr-reply orchestrator "COMPLETED artifacts=[...] issues=[]"
    herdr-reply orchestrator --file result.md
    echo "COMPLETED" | herdr-reply orchestrator
    herdr-reply orchestrator "COMPLETED" --wait --timeout 15000
    herdr-reply orchestrator --file reply.md --allow-unresolvable-sha 8d9a742

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
from typing import Any

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_bootstrap import (
    DEFAULT_SETTLE_SECONDS,
    append_invariant,
    lane_invariant_path,
    load_kind_entry,
    pane_cwd,
    planned_invariant_content,
    read_if_exists,
    render_invariant,
    settle_fresh_pane,
    target_is_tracked,
    target_path,
    write_role_invariant,
)
from herdr_cli import (
    EXIT_BLOCKED,
    EXIT_OK,
    EXIT_USAGE,
    KNOWN_AGENT_KINDS,
    METHOD_CONSTRAINT_EPILOG,
    STDIN,
    HerdrError,
    UsageError,
    add_shared_argument,
    decode_payload,
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
    read_payload_stream,
    reply_helper,
    require_herdr_env,
    run_herdr,
    run_herdr_checked,
    verify_target_not_bare_shell,
)
from herdr_envelope import (
    caller_anchor,
    format_delivery_summary,
    render_envelope,
    render_prelude,
    reply_state,
)

# Re-exported: the evidence extraction must not move an attribute a test or caller pins.
from herdr_evidence import (
    ARTIFACT_LIMIT as ARTIFACT_LIMIT,
)
from herdr_evidence import (
    CANONICAL_EVIDENCE_HEADS as CANONICAL_EVIDENCE_HEADS,
)
from herdr_evidence import (
    EVIDENCE_KEYWORDS as EVIDENCE_KEYWORDS,
)
from herdr_evidence import (
    EVIDENCE_LABEL_LIMIT as EVIDENCE_LABEL_LIMIT,
)
from herdr_evidence import (
    EVIDENCE_LABEL_WORDS as EVIDENCE_LABEL_WORDS,
)
from herdr_evidence import (
    EVIDENCE_STEMS as EVIDENCE_STEMS,
)
from herdr_evidence import (
    FENCE_MARKER as FENCE_MARKER,
)
from herdr_evidence import (
    NOT_EVIDENCE_HEADS as NOT_EVIDENCE_HEADS,
)
from herdr_evidence import (
    STATUS_MAP as STATUS_MAP,
)
from herdr_evidence import (
    evidence_label,
    extract_artifacts,
    parse_status_line,
    payload_shape,
)
from herdr_evidence import (
    evidence_section as evidence_section,
)

# Re-exported: the SHA-guard extraction must not move an attribute a test pins.
from herdr_git_guard import (
    ALLOW_UNRESOLVABLE_SHA,
    lane_git_dir,
    require_resolvable_shas,
)
from herdr_git_guard import (
    GIT_LOCATION_REDIRECT_VARS as GIT_LOCATION_REDIRECT_VARS,
)
from herdr_git_guard import (
    GIT_VERDICT_NEUTRAL_LOCATION_VARS as GIT_VERDICT_NEUTRAL_LOCATION_VARS,
)
from herdr_git_guard import (
    SHA_SHAPED_BACKTICKED_RE as SHA_SHAPED_BACKTICKED_RE,
)
from herdr_git_guard import (
    backticked_sha_tokens as backticked_sha_tokens,
)
from herdr_git_guard import (
    git_can_resolve_commits as git_can_resolve_commits,
)
from herdr_git_guard import (
    git_location_redirect as git_location_redirect,
)
from herdr_git_guard import (
    names_a_commit as names_a_commit,
)
from herdr_git_guard import (
    unresolvable_sha_tokens as unresolvable_sha_tokens,
)
from herdr_label import reconcile_lane
from herdr_lease import (
    REPLIES_DIR_LANE,
    STATE_COMPLETED,
    STATE_FAILED,
    STATE_INPUT_REQUIRED,
    STATE_SUBMITTED,
    STATE_WORKING,
    get_lease,
    get_reply,
    get_task,
    list_tasks,
    record_event,
    release_lease,
    resolve_base_dir,
    save_verified_reply,
    state_is_readable,
    status_of,
)
from herdr_prompt import (
    resolve_caller,
    resolve_receiver,
)

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
    settle: float = DEFAULT_SETTLE_SECONDS
    verbose: bool = False
    ticket: str | None = None
    in_reply_to_record: str | None = None
    allow_unresolvable_sha: list[str] | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-reply",
        description="Deliver a completion reply to a caller agent without shell mangling.",
        epilog=(
            "exit status: 0 accepted, 1 herdr failure, 2 usage or precondition, "
            "3 target needs human input, 4 reply delivered but wait timed out\n\n"
            "lease bookkeeping is best-effort and never blocks delivery: an unresolvable lease\n"
            "store is reported on stderr, skipping the correlation lookup, trajectory note, or\n"
            "release. A skipped correlation drops metadata.ticket_id/in_reply_to from the\n"
            "envelope; the reply still correlates by pane/target\n\n" + METHOD_CONSTRAINT_EPILOG
        ),
    )
    _ = parser.add_argument("target", metavar="TARGET", help="caller agent name or pane id")
    _ = parser.add_argument(
        "message",
        nargs="?",
        metavar="MESSAGE",
        help="reply text (e.g. '<STATUS> <artifacts> <issues>'); omitted reads --file or stdin",
    )
    add_shared_argument(
        parser,
        "file",
        help="payload file; '-' reads stdin verbatim",
    )
    add_shared_argument(
        parser,
        "wait",
        help="wait for caller to settle after receiving reply",
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
        "auto_start",
        help="automatically start the agent on an open shell pane before delivering the reply",
    )
    add_shared_argument(
        parser,
        "settle",
        default=DEFAULT_SETTLE_SECONDS,
        help=(
            "seconds to wait after `--auto-start` spawns the caller, before the reply is "
            "delivered, so a still-initialising pane is not treated as acceptant; "
            f"0 waits not at all (default: {DEFAULT_SETTLE_SECONDS:g})"
        ),
    )
    add_shared_argument(
        parser,
        "verbose",
        help="include cwd/resume recovery metadata in the envelope metadata (default trimmed)",
    )
    _ = parser.add_argument(
        "--ticket",
        metavar="ID",
        default=None,
        help=(
            "bind this reply's task linkage to the named task (its task id, or a ticket id "
            "whose open task this sender owns is unique); without it the linkage comes from "
            "the sender's active lease, else the reply is recorded unlinked"
        ),
    )
    _ = parser.add_argument(
        "--in-reply-to",
        dest="in_reply_to_record",
        metavar="RECORD",
        default=None,
        help="bind this reply to the task of the named stored reply record",
    )
    _ = parser.add_argument(
        ALLOW_UNRESOLVABLE_SHA,
        dest="allow_unresolvable_sha",
        action="append",
        metavar="TOKEN",
        default=None,
        help=(
            "waive the outbound-SHA guard for one backticked 7-40 hex token that deliberately "
            "names no commit in this lane (repeatable); every waiver is reported on stderr, so "
            "it is never a silent bypass"
        ),
    )
    return parser


_SHA_RE = re.compile(r"[0-9a-f]{7,40}")


def payload_origin(options: Options) -> str:
    """The origin named in a guard message: the payload file, or the stream it arrived on."""
    if options.file and options.file != STDIN:
        return options.file
    return "<message>" if options.message is not None else "<stdin>"


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


# `herdr_evidence._NON_ALNUM_RE` moved with the evidence subsystem; `_slug` keeps its own
# copy of the identical pattern instead of importing a private name across modules.
_SLUG_STRIP_RE = re.compile(r"[^a-z0-9]+")


def _slug(value: str | None) -> str:
    """A filesystem-safe fragment for a record id; `unknown` when there is nothing to slug."""
    if not value:
        return "unknown"
    cleaned = _SLUG_STRIP_RE.sub("-", value.casefold()).strip("-")
    return cleaned or "unknown"


def build_reply_entry(
    payload: str,
    *,
    sender: str | None,
    caller: str | None,
    ticket_id: str | None,
    task_id: str | None,
    in_reply_to: str | None,
    mapped: str | None,
    sha: str | None,
    shape: str,
    evidence: str | None,
) -> dict[str, Any]:
    """The index row for one reply: metadata only, never the body text (#231 F3).

    Every body-derived value is reduced to a bounded token: `status` is the mapped status
    only (never the payload's first line), `sha` is kept only when it is hex, `evidence` is
    `evidence_label(heading)` — a closed-vocabulary label — and `artifacts` is a *count* of
    the cited path-like tokens, so no path is stored. `task_id` binds the row to the lease it
    came from, which is what the advance gate compares before it moves a task (F-C2).
    """
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return {
        "id": f"{stamp}-{_slug(sender)}-{digest[:8]}",
        "recorded_at": _now_iso(),
        "sender": sender,
        "caller": caller,
        "ticket_id": ticket_id,
        "task_id": task_id,
        "in_reply_to": in_reply_to,
        "status": mapped,
        "shape": shape,
        "evidence": evidence_label(evidence),
        "sha": sha if isinstance(sha, str) and _SHA_RE.fullmatch(sha) else None,
        "digest": digest,
        "bytes": len(payload.encode("utf-8")),
        "artifacts": len(extract_artifacts(payload)),
    }


def persist_reply(
    entry: Mapping[str, Any],
    body: str,
    *,
    env: Mapping[str, str],
) -> tuple[dict[str, Any] | None, str | None]:
    """Persist the record, best-effort; `(stored row, None)` or `(None, one-line reason)`.

    Never fatal by contract (#229): a store this process cannot resolve degrades to the
    NOT RECORDED pointer silently, because the lease steps already report that same
    unresolvable anchor; a resolvable store that fails is reported once via
    `report_lease_trouble` and degrades the same way. The reply is delivered either way.

    The transaction itself — record, re-resolve through the reader, discard what does not
    resolve (#231 F2) — is owned by the store: `herdr_lease.save_verified_reply`. This
    caller only supplies the trouble report the pointer contract demands.
    """
    return save_verified_reply(entry, body, env=env, on_trouble=report_lease_trouble)


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
    its delivered payload is unchanged (#231). `evidence` is the ledger label, not the
    heading text, so the pointer stays metadata-only too.
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
            f"Record: {REPLIES_DIR_LANE}/{stored['id']}.yaml sha256={stored['digest']} — "
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


# The recovery command is executable, so it names this lane's own `herdr_reply.py` as an absolute
# path resolved from this tree: an operator can run it from any cwd, and a placeholder would
# render a command that cannot run. The derivation is single-sourced in `herdr_cli.reply_helper()`
# — the `~/.agents/skills/herdr` symlink is deliberately not used, since it can resolve into
# another worktree whose `herdr_*` code may be older.
REPLY_HELPER = reply_helper()


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
        f'  1. Auto-revive & deliver: uv run "{REPLY_HELPER}" '
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
        payload = decode_payload(message)
    else:
        payload = decode_payload(
            read_payload_stream(
                source,
                tty_refusal=(
                    "no MESSAGE or --file given and stdin is a terminal; "
                    "pass MESSAGE, --file PATH, or pipe the payload"
                ),
            )
        )
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
    going after this line, and the line names what was skipped and why. The message is
    collapsed onto one line: a parse error's own text spans several, and one line is the
    promise the contract makes (#231).
    """
    print(f"herdr-reply: {action} skipped: {_one_line(str(exc))}", file=sys.stderr)


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


# ── lane task group for the ADR-0020 reconciliation pass (#182 t2) ──────────────────


def resolve_lane_task_group(
    lease: Mapping[str, Any] | None,
    task_id: str | None,
    env: Mapping[str, str],
) -> str | None:
    """The Task Group slug this lane was opened under, read back from the lane's own records.

    `herdr-reply` has no `--task-group` flag, so the slug the reconciliation pass would write as
    the tab title and as `<task_group>-orch` can only come from stored evidence: the sender's
    lease, then the task record this reply advances. A record that carries none answers unknown,
    and this returns None: the pass then leaves the tab title and the orchestrator name alone
    with one stderr line instead of renaming to a bare tab id or to a slug guessed from a
    visible label. Reading the store never decides delivery, so an unreadable record is swallowed
    here — the lease steps around it already reported the store on stderr, and the contract is
    one line per skipped step. `herdr-dispatch` writes the slug it was given with `--task-group`
    into both records it creates (#182 t3 C), so a lane opened with a task group heals its own
    tab title on the reply side; a lane opened without one still answers None and stays skipped.
    """
    records: list[Mapping[str, Any] | None] = [lease]
    if task_id:
        try:
            records.append(get_task(task_id, env=env))
        except Exception:
            records.append(None)
    for record in records:
        if isinstance(record, Mapping):
            value = record.get("task_group")
            if isinstance(value, str) and value:
                return value
    return None


# ── reply task linkage (#246 D1.2) ──────────────────────────────────────────────────

# The open/terminal partition that decides which of the sender's tasks count as open work for
# the linkage (#246 D1.4/F2). Both sets are enumerated and a test pins that they partition the
# store's `CANONICAL_STATUSES`, so a status added there cannot silently default to open.
# `TASK_STATE_COMPLETED` is the only state this store writes that ends the round;
# `TASK_STATE_SUBMITTED`/`TASK_STATE_WORKING`/`TASK_STATE_INPUT_REQUIRED`/`TASK_STATE_FAILED`
# all still await their assignee. `_is_open_task` normalizes through `herdr_lease.STATUS_ALIASES`
# before comparing, so a record written by a pre-cutover worktree (`status: dispatched`) lands on
# the same side of the partition as one written here (`status: TASK_STATE_SUBMITTED`) — the shared
# live store cannot be upgraded in lockstep. A status that names no state reads as neither.
OPEN_TASK_STATUSES = frozenset({STATE_SUBMITTED, STATE_WORKING, STATE_INPUT_REQUIRED, STATE_FAILED})
TERMINAL_TASK_STATUSES = frozenset({STATE_COMPLETED})


def _is_open_task(task: Mapping[str, Any]) -> bool:
    """Whether a task still awaits its assignee: its state is one of the open ones.

    Both vocabularies read alike, and an unknown or absent state is NOT open: a record nobody can
    read must not be reported as the sender's open work.
    """
    return status_of(task) in OPEN_TASK_STATUSES


# ── unlinked-warning severity markers (#246 D1.5 R2) ─────────────────────────────────

# One STABLE leading marker per severity, so a caller or a pin keys on the class instead of on
# the incident prose. The first two are the D1.3 severities — the step refused to bind what it
# was told (open work it would not guess at, or a flag naming no open task of the sender), or
# there was genuinely nothing to link. The third is the wording for an answer the resolver could
# not obtain at all (no sender resolved, or the anchor/store could not be read), which is
# neither a refusal nor an empty answer. Each of the two store-dependent branches below may or
# may not record, so the record claim is NOT part of a marker.
UNLINKED_REFUSED_MARKER = "unlinked reply (open work refused)"
UNLINKED_NOTHING_MARKER = "unlinked reply (nothing to link)"
UNLINKED_UNREADABLE_MARKER = "unlinked reply (sender or store unreadable)"

# The caller-side tail of an UNLINKED warning (#246 D1.5 F1): the resolver cannot know whether
# the store will take the record, so the claim is emitted only after `persist_reply` answers,
# and the opposite outcome is stated just as plainly when no record was written. A warning must
# never contradict the `NOT RECORDED` pointer the caller is about to read. Every warning line is
# an unlinked outcome (#246 E1.2): the explicit bindings stay silent, so no linked warning exists.
RECORDED_CLAUSE = "; recording the reply unlinked"
NOT_RECORDED_CLAUSE = "; no store record was written"


def _unlinked(marker: str, reason: str, exc: BaseException | None = None) -> str:
    """The one warning line for a reply that could not be bound to a task: marker, then why.

    The line leads with a stable severity marker (#246 D1.5), so a caller — or a pin — keys on
    the severity class instead of on the incident prose, and never claims a record: whether one
    was written is appended by the caller once the store has answered, because the
    store-dependent branches record or not depending on whether the store resolves at all.
    """
    detail = f" ({_one_line(str(exc))})" if exc is not None else ""
    return f"{marker}: task linkage unresolved — {reason}{detail}"


def _sender_open_tasks(sender: str, env: Mapping[str, str]) -> list[dict[str, Any]] | None:
    """Every non-terminal task assigned to `sender`; None when the store cannot be read.

    `None` and `[]` are different answers: an unreadable store has already been reported by
    the lease steps, so it must not also warn about a missing linkage, while an empty list is
    a real "this sender holds no open task". `_load_state` turns corruption into empty state,
    so the readability probe runs first — without it a damaged store read as `[]` and the
    warning claimed the sender held no open task (#246 D1.4/F3).
    """
    try:
        if not state_is_readable(env=env):
            return None
        tasks = list_tasks(env=env)
    except Exception:
        return None
    return [task for task in tasks if task.get("assignee") == sender and _is_open_task(task)]


def _linkage_from_ticket(
    value: str, *, sender: str | None, env: Mapping[str, str]
) -> tuple[str | None, str | None]:
    """The sender's open task named by `--ticket`, or an unlinked warning.

    `value` names a task id, or a ticket id whose sender-owned open task is unique. An
    explicit flag that names a task which is another sender's, already finished, or unknown
    yields no linkage rather than falling back to the lease: the flag was the instruction.
    """
    if sender is None:
        return None, _unlinked(
            UNLINKED_UNREADABLE_MARKER, f"--ticket {value!r} given but no sender resolved"
        )
    try:
        tasks = list_tasks(env=env)
    except Exception as exc:
        return None, _unlinked(
            UNLINKED_UNREADABLE_MARKER, f"--ticket {value!r} could not be resolved", exc
        )
    named = [task for task in tasks if task.get("task_id") == value]
    if named:
        if named[0].get("assignee") == sender and _is_open_task(named[0]):
            return value, None
        return None, _unlinked(
            UNLINKED_REFUSED_MARKER,
            f"--ticket {value!r} is not an open task of sender {sender!r}",
        )
    matching = [
        task
        for task in tasks
        if task.get("ticket_id") == value and task.get("assignee") == sender and _is_open_task(task)
    ]
    if len(matching) == 1 and isinstance(matching[0].get("task_id"), str):
        return str(matching[0]["task_id"]), None
    return None, _unlinked(
        UNLINKED_REFUSED_MARKER,
        f"--ticket {value!r} does not name exactly one open task of sender {sender!r}",
    )


def _linkage_from_record(
    record_id: str, *, sender: str | None, env: Mapping[str, str]
) -> tuple[str | None, str | None]:
    """The open task a named stored reply points at, or an unlinked warning.

    `--in-reply-to <record-id>` re-binds a follow-up to whichever task the named record was
    linked to, so a corrected or additive reply resolves without restating the ticket.
    """
    if sender is None:
        return None, _unlinked(
            UNLINKED_UNREADABLE_MARKER, f"--in-reply-to {record_id!r} given but no sender resolved"
        )
    try:
        record = get_reply(record_id, env=env)
        linked = record.get("task_id") if isinstance(record, Mapping) else None
        task = get_task(linked, env=env) if isinstance(linked, str) else None
    except Exception as exc:
        return None, _unlinked(
            UNLINKED_UNREADABLE_MARKER, f"--in-reply-to {record_id!r} could not be resolved", exc
        )
    if not isinstance(record, Mapping) or record.get("sender") != sender:
        return None, _unlinked(
            UNLINKED_REFUSED_MARKER,
            f"--in-reply-to {record_id!r} names no reply record of sender {sender!r}",
        )
    if not isinstance(linked, str):
        return None, _unlinked(
            UNLINKED_REFUSED_MARKER, f"--in-reply-to {record_id!r} carries no task linkage"
        )
    if not isinstance(task, dict) or task.get("assignee") != sender or not _is_open_task(task):
        return None, _unlinked(
            UNLINKED_REFUSED_MARKER,
            f"--in-reply-to {record_id!r} names task {linked!r}, not an open task of "
            f"sender {sender!r}",
        )
    return linked, None


def resolve_task_linkage(
    *,
    sender: str | None,
    lease: Mapping[str, Any] | None,
    explicit_ticket: str | None,
    in_reply_to_record: str | None,
    env: Mapping[str, str],
) -> tuple[str | None, str | None]:
    """(task_id, warning) for the task this reply advances, or (None, reason) when unlinked.

    The linkage used to come only from the sender's lease, which the first reply releases, so
    a legitimate second reply for the same ticket was recorded with `task_id: null` and could
    never advance anything (#246 D1.2). Precedence, most explicit first: the `--in-reply-to`
    record, then the `--ticket` name, then the sender's active lease (the legacy path for the
    first reply). No step infers: the rendered dispatch contract carries `--ticket` (#246
    E1.1), so a reply that names nothing is never guessed at. Zero or several open tasks, or
    an explicit name that does not resolve to one of the sender's open tasks, records the
    reply unlinked with one warning line — a wrong linkage is worse than none. The
    sole-open-task branch deleted in E1.2 bound the wrong row exactly once; a guard that is
    told does not guess.

    Every unlinked answer carries a reason (#246 D1.3), so a recorded reply with
    `task_id: null` is never silent. The reason states the severity, and the line leads with a
    stable marker for that severity (#246 D1.5): "open work refused" when the step refused to
    bind what it was told — open work it would not guess at (one or several open tasks), or a
    flag that names no open task of the sender — "nothing to link" when there was nothing to
    link, and "sender or store unreadable" when there was no answer at all (no sender
    resolved, or the anchor/store could not be read). The last of those is the third wording,
    distinct from both a refusal and an empty answer. The warning never claims a record here:
    whether one was written depends on the store, so the caller appends that clause after the
    store answers. Every warning now accompanies an unlinked reply; the explicit `--ticket`
    and `--in-reply-to` bindings stay silent, because they are the caller's instruction.
    """
    if in_reply_to_record is not None:
        return _linkage_from_record(in_reply_to_record, sender=sender, env=env)
    if explicit_ticket is not None:
        return _linkage_from_ticket(explicit_ticket, sender=sender, env=env)
    if isinstance(lease, Mapping):
        lease_task = lease.get("task_id")
        if isinstance(lease_task, str):
            return lease_task, None
    if sender is None:
        # Unreachable end to end, and named here only: `resolve_current_agent` finds no sender
        # when `pane current` yields no pane id, and the CHECKED `pane current --current` that
        # `herdr_prompt.resolve_caller` runs later aborts at RC 1 before this warning can print.
        # The shared stub CAN fail `pane current` (omit `state["current"]`, or set it to `""`),
        # so that is not the reason this branch is unreachable — the checked read above it is.
        return None, _unlinked(
            UNLINKED_UNREADABLE_MARKER, "no sender resolved, so no task could be attributed"
        )
    open_tasks = _sender_open_tasks(sender, env=env)
    if open_tasks is None:
        return None, _unlinked(
            UNLINKED_UNREADABLE_MARKER, "the sender's open tasks could not be read"
        )
    if not open_tasks:
        return None, _unlinked(UNLINKED_NOTHING_MARKER, f"sender {sender!r} holds no open task")
    if len(open_tasks) == 1:
        return None, _unlinked(
            UNLINKED_REFUSED_MARKER,
            f"sender {sender!r} holds 1 open task, "
            "so no ticket was inferred \u2014 pass --ticket <id>",
        )
    count = len(open_tasks)
    return None, _unlinked(
        UNLINKED_REFUSED_MARKER,
        f"sender {sender!r} holds {count} open tasks, so the ticket is ambiguous",
    )


def _recorded_and_advanceable(
    record_id: str | None,
    shape: str | None,
    *,
    sender: str,
    task_id: str | None,
    env: Mapping[str, str],
) -> bool:
    """Whether a persisted record permits advancing this sender's task (#231 F-C2).

    Prompt text is never provenance: without a record id, or with an id the store does not
    hold, nothing advances. A record whose shape is `incomplete` carries the verdict itself —
    no `completed` event, no state advance, and no invented canonical status. And a record
    must be *bound* to the lease being advanced: a row another agent wrote, or a row for
    another task, never advances this one, so a caller-supplied id cannot move a foreign
    lease. A shape-less caller (legacy) and an `n/a` or `complete` record advance as before.
    """
    if not record_id:
        return False
    if shape == "incomplete":
        return False
    try:
        record = get_reply(record_id, env=env)
    except Exception as exc:
        report_lease_trouble("reply record lookup", exc)
        return False
    if record is None:
        return False
    if record.get("sender") != sender:
        return False
    return task_id is None or record.get("task_id") == task_id


def record_sender_status(
    herdr: str,
    env: Mapping[str, str],
    mapped: str | None,
    sha: str | None,
    *,
    record_id: str | None = None,
    shape: str | None = None,
    task_id: str | None = None,
) -> None:
    """Append the sender's completion event to its task trajectory, when one is linked.

    Resolves the sender's own lease first, then gates the advance on the persisted record
    (#231): a missing `record_id`, an id the store does not hold, an `incomplete` shape, or a
    record bound to another sender/task appends no event and changes no state. The lease
    lookup still runs ahead of the gate, so an unresolvable store reports the same
    `trajectory note` skip it always did. Non-fatal by contract: a missing lease or a store
    this process cannot resolve is still a reply.

    `task_id` is the linkage the caller already resolved (#246 D1.2): the sender's lease for a
    first reply, or the task a later reply re-bound to. When it is None the sender's lease is
    read here, which keeps a direct caller's behaviour unchanged.

    The trajectory `note` is metadata only -- the mapped status token plus the hex `sha` when
    the payload carries one (`completed 8c715091`, or just the status). A non-hex second token
    is dropped, so no payload text reaches `.lane/tasks.yaml` (#231).
    """
    if not mapped:
        return
    try:
        sender = resolve_current_agent(herdr, env)
        if not sender:
            return
    except Exception as exc:
        report_lease_trouble("trajectory note", exc)
        return

    linked = task_id
    if linked is None:
        try:
            lease = get_lease(sender, env=env)
        except Exception as exc:
            report_lease_trouble("trajectory note", exc)
            return
        if not isinstance(lease, dict):
            return
        lease_task = lease.get("task_id")
        linked = lease_task if isinstance(lease_task, str) else None

    if not _recorded_and_advanceable(record_id, shape, sender=sender, task_id=linked, env=env):
        return

    validated_sha = sha if isinstance(sha, str) and _SHA_RE.fullmatch(sha) else None
    note = f"{mapped} {validated_sha}" if validated_sha else mapped
    try:
        if linked is not None:
            _ = record_event(
                linked,
                mapped,
                note=note,
                sha=validated_sha,
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

    if options.settle < 0:
        raise UsageError(f"--settle {options.settle} must not be negative")

    if options.auto_start:
        auto_kind = options.auto_start.strip().lower()
        if not auto_kind or auto_kind not in KNOWN_AGENT_KINDS:
            raise UsageError(
                f"--auto-start kind {options.auto_start!r} is not a recognized agent kind (known: {', '.join(sorted(KNOWN_AGENT_KINDS))})"
            )

    shell_info = inspect_target_shell_pane(herdr, target, env)
    revive_argv: list[str] | None = None
    revive_invariant: str | None = None
    if shell_info is not None:
        if options.auto_start:
            kind = options.auto_start.strip().lower()
            start_name = (
                shell_info.suggested_name
                if shell_info.suggested_name != "<name>"
                else f"agent-{shell_info.pane_id.replace(':', '-')}"
            )
            revive_argv = [
                herdr,
                "agent",
                "start",
                start_name,
                "--kind",
                kind,
                "--pane",
                shell_info.pane_id,
            ]
            # #237: a revived caller is a fresh agent, so it receives the same invariant
            # injection as a bootstrapped one — otherwise the reply lands on a contract-less
            # agent. The role is unknowable here, so the agent name stands in, exactly as
            # `herdr-bootstrap` falls back to the name when no role is given. The snippet file
            # for an inline kind lives under the resolved store base: any absolute path the
            # spawned binary can read will do, and the pane cwd is not needed for it. A file
            # kind is appended to the pane's live cwd, the surface that kind reads; with no
            # determinable cwd, or a tracked target the append would change, the revive is
            # refused loudly rather than delivering to an agent that holds no contract.
            # Deliberately stricter than bootstrap's tracked rule (which offers an override
            # flag): the reply path carries no such flag, so ambiguity refuses.
            entry = load_kind_entry(kind)
            snippet = render_invariant(start_name)
            agent_args: list[str] = []
            invariant_surface: str | None = None
            if entry.inline_invariant:
                if not entry.invariant_flag:
                    raise UsageError(
                        f"--auto-start kind {kind!r} names no invariant flag in kinds.yaml; "
                        "refusing to revive a caller that would hold no lane contract"
                    )
                invariant_file = lane_invariant_path(str(resolve_base_dir(env=env)), start_name)
                if not options.dry_run:
                    try:
                        write_role_invariant(invariant_file, snippet)
                    except OSError as exc:
                        raise UsageError(f"cannot write {invariant_file}: {exc}") from exc
                agent_args += [entry.invariant_flag, str(invariant_file)]
                invariant_surface = str(invariant_file)
            else:
                pane_dir = pane_cwd(herdr, shell_info.pane_id, env)
                if not pane_dir:
                    raise UsageError(
                        f"cannot determine the cwd of pane {shell_info.pane_id}; a {kind!r} "
                        "caller reads its invariant from a file there, so reviving it would "
                        "deliver this reply to an agent with no lane contract — bootstrap the "
                        "caller explicitly instead"
                    )
                agents_file = target_path(pane_dir, kind)
                try:
                    current = read_if_exists(agents_file)
                except OSError as exc:
                    raise UsageError(f"cannot read {agents_file}: {exc}") from exc
                if planned_invariant_content(current, snippet) != current:
                    if target_is_tracked(agents_file, env) is not False:
                        raise UsageError(
                            f"refusing to append the lane invariant to {agents_file}: its "
                            "version-control state is not certainly untracked — bootstrap the "
                            "caller explicitly with --allow-tracked-invariant instead of "
                            "reviving it into a contract-less agent"
                        )
                    if not options.dry_run:
                        try:
                            _ = append_invariant(agents_file, snippet)
                        except OSError as exc:
                            raise UsageError(f"cannot write {agents_file}: {exc}") from exc
                invariant_surface = str(agents_file)
            agent_args += entry.trust_flags
            for arg in agent_args:
                if "\n" in arg or "\r" in arg:
                    raise UsageError(f"revive agent args must be single-line: {arg!r}")
            if agent_args:
                revive_argv += ["--", *agent_args]
            revive_invariant = invariant_surface
            if not options.dry_run:
                _ = run_herdr_checked(revive_argv, env)
                # A revived caller is a fresh spawn too: settle before the reply is delivered
                # (#237), so its first prompt is not swallowed by a pane still initialising.
                settle_fresh_pane(options.settle)
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
    body = payload
    if options.file and options.file != STDIN:
        source = f"File: {options.file}"
    elif options.message is not None:
        source = f"Payload: inline ({len(payload.encode('utf-8'))} bytes)"
    else:
        source = f"Payload: stdin ({len(payload.encode('utf-8'))} bytes)"
    mapped, sha, _line = parse_status_line(payload)
    if mapped is None:
        # #246 D1.1: the Final Reply Template requires the body to start at its status line.
        # A status-less payload used to be recorded as a `status: null`, `shape: n/a` row and
        # consumed the sender's lease, so its corrected reply could never advance the task;
        # refuse before any record exists rather than record something that only looks like a
        # reply.
        raise UsageError(
            "payload does not start at its status line; the first non-empty line must be "
            "COMPLETED, BLOCKED, or REJECTED (see the Final Reply Template in "
            "skills/herdr/references/lane-coordination.md); refusing to record or submit the reply"
        )
    # #247 D2: a backticked SHA-shaped token is an instruction, and an instruction that names no
    # commit points at nothing. This runs before any record exists — and before `--dry-run`
    # returns — so a refused payload consumes no lease and submits nothing.
    require_resolvable_shas(
        payload,
        payload_path=payload_origin(options),
        waived=options.allow_unresolvable_sha or (),
        cwd=lane_git_dir(env),
        env=env,
    )
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
    # #246 D1.2: the lease is consumed by the first reply, so the task this reply advances is
    # resolved from the whole store — the explicit flag, else the lease — and an unresolvable
    # answer is recorded unlinked with one warning line. No step infers (#246 E1.2): the
    # rendered contract carries `--ticket`, so a reply that names nothing mutates nothing. The
    # resolution only ever reads the store, so `--dry-run` runs it too: the preview carries the
    # correlation the real send carries, while recording nothing.
    linked_task_id, linkage_warning = resolve_task_linkage(
        sender=sender,
        lease=lease,
        explicit_ticket=options.ticket,
        in_reply_to_record=options.in_reply_to_record,
        env=env,
    )
    # The envelope describes the task this reply advances, and the precedence is the resolver's:
    # the resolved, store-backed linkage names `id`/`in_reply_to` first; the lease's task id is
    # the fallback, reached only when the resolver returned nothing while a lease still names
    # one; when neither resolves, `id` renders `''` and both correlation keys stay absent.
    # `ticket_id` prefers the lease's ticket, else the resolved task record's ticket, read back
    # through `get_task`. `status.state` is the status the payload's first token stated, mapped
    # above (a payload with no status is refused before this line renders anything).
    envelope_task_id = linked_task_id or in_reply_to
    envelope_ticket_id = ticket_id
    if envelope_ticket_id is None and envelope_task_id is not None:
        try:
            task_record = get_task(envelope_task_id, env=env)
        except Exception:
            task_record = None
        if isinstance(task_record, dict):
            record_ticket = task_record.get("ticket_id")
            if isinstance(record_ticket, str) and record_ticket:
                envelope_ticket_id = record_ticket
    panes, agents = fetch_inventory(herdr, env)
    caller_ctx = resolve_caller(herdr, env, inventory=(panes, agents))
    receiver = resolve_receiver(panes, agents, target)
    # ADR-0020 active reconciliation (#182 t2), anchored on the physical ids this snapshot
    # already resolved: `caller_ctx.pane_id` names the orchestrator pane, `caller_ctx.tab_id`
    # names the lane's tab, and each worker is keyed by its own `pane_id`. Task-group source:
    # no `--task-group` flag exists here, so the slug is read back from the lane's records (see
    # `resolve_lane_task_group`); with none recorded the tab title and the orchestrator name are
    # skipped with one stderr line, and the worker-name half still runs. Best-effort by contract:
    # no rename below can change this exit status or delay the delivery after it.
    _ = reconcile_lane(
        herdr,
        env,
        task_group=resolve_lane_task_group(lease, envelope_task_id, env),
        marker="herdr-reply",
        dry_run=options.dry_run,
        missing_note=(
            "no task group recorded for this lane, so the tab title and the orchestrator "
            "name were left alone"
        ),
        pane_id=caller_ctx.pane_id,
        tab_id=caller_ctx.tab_id,
        inventory=(panes, agents),
    )
    anchor = f"[You: {caller_anchor(caller_ctx)}]"
    reply_envelope = render_envelope(
        caller_ctx,
        receiver=receiver or target,
        include_recovery=options.verbose,
        ticket_id=envelope_ticket_id,
        task_id=envelope_task_id,
        in_reply_to=envelope_task_id,
        tab_id=caller_ctx.tab_id,
        state=reply_state(mapped),
    )
    shape, heading = payload_shape(payload)
    # The pointer and the index row carry the same bounded label, never the heading text.
    evidence = evidence_label(heading)
    prelude = render_prelude(reply_envelope)
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
                task_id=linked_task_id,
                in_reply_to=linked_task_id,
                mapped=mapped,
                sha=sha,
                shape=shape,
                evidence=heading,
            )
            stored, reason = persist_reply(entry, payload, env=env)
        except Exception as exc:
            report_lease_trouble("reply record", exc)
            stored, reason = None, _one_line(str(exc))
        if stored is not None:
            record_id = str(stored["id"])
        if linkage_warning:
            # (#246 D1.5 F1) The record claim is caller-side, and emitted only after the store
            # has answered: the resolver cannot know whether the record will be written, and the
            # same branch records or not depending on whether the store resolves at all. Claim a
            # record only when one was written, and say plainly when none was, so the warning
            # never contradicts the NOT RECORDED pointer in the prompt delivered in this run.
            # Every warning is unlinked (#246 E1.2): the explicit bindings stay silent, so the
            # clause always states a recording outcome.
            clause = RECORDED_CLAUSE if stored is not None else NOT_RECORDED_CLAUSE
            print(f"herdr-reply: {linkage_warning}{clause}", file=sys.stderr)
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
        if options.json:
            # A revive plan shows the spawn, the invariant surface, its settle, and the
            # delivery argv; a plain plan stays the delivery argv alone.
            if revive_argv is None:
                print(json.dumps(argv))
            else:
                plan: dict[str, object] = {
                    "agent_start": revive_argv,
                    "role_invariant": revive_invariant,
                    "settle": options.settle,
                    "agent_prompt": argv,
                }
                print(json.dumps(plan))
        else:
            dry_pane = receiver.pane_id if receiver is not None else None
            dry_pane_str = f" ({dry_pane})" if dry_pane and dry_pane != target else ""
            status = f"{anchor} dry-run: would reply to {target}{dry_pane_str}"
            print(format_delivery_summary(status, delivered, body, source))
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
                herdr, env, mapped, sha, record_id=record_id, shape=shape, task_id=linked_task_id
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

    record_sender_status(
        herdr, env, mapped, sha, record_id=record_id, shape=shape, task_id=linked_task_id
    )
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
        status = f"{anchor} replied to {target}{pane_str}  bytes={size}{rev_str}{suffix}"
        print(format_delivery_summary(status, delivered, body, source))
    return EXIT_OK


def refuse_space_form_dash_ticket(parser: argparse.ArgumentParser, argv: Sequence[str]) -> None:
    """Refuse a hand-typed `--ticket -value` with the equals-form remedy (herdr228-closeout#C2).

    Argparse already binds the equals form (`--ticket=-rf`) with no code, so the only
    gap is the space form with a dash-led value, which argparse reports as a bare
    "expected one argument" (exit 2, nothing accepted, nothing explained). This names
    the remedy instead, still exiting 2 with nothing accepted. It never rebinds: a
    pre-parse that reattached the value would silently accept things argparse rejects.
    A missing value errors the same bare way, so it gets the same remedy.
    """
    raw = list(argv)
    for index, token in enumerate(raw):
        if token != "--ticket":
            continue
        following = raw[index + 1] if index + 1 < len(raw) else None
        if following is None or following.startswith("-"):
            parser.error(
                "--ticket needs a value; a value starting with '-' cannot be passed "
                f"as a separate word (got {following!r}); attach it with '=' instead: "
                "--ticket=<value> (for example: --ticket=-rf)"
            )


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    parser = build_parser()
    raw = list(sys.argv[1:] if argv is None else argv)
    refuse_space_form_dash_ticket(parser, raw)
    options = parser.parse_args(raw, namespace=Options())
    try:
        return guard("herdr-reply", lambda: reply_caller(options, env_map))
    except WaitTimeout as exc:
        print(f"herdr-reply: {exc}", file=sys.stderr)
        return EXIT_WAIT_TIMEOUT


if __name__ == "__main__":
    raise SystemExit(main())
