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

The record's task linkage is resolved from the whole store, not just the lease (#246 D1.2):
an explicit `--ticket <id>` (or `--in-reply-to <record-id>`) wins, else the sender's active
lease, else the sender's sole open task. Zero or several open tasks — or an explicit name the
sender does not hold open — records the reply unlinked with one warning line, never a guess,
so a second reply for the same ticket still advances the task instead of losing the linkage
when the first reply consumes the lease. The sole-open-task step is the one INFERRED binding,
so it warns even when it succeeds (#246 D1.4): it counts candidates and cannot read which
ticket the payload is about, so the line names the task it chose and the `--ticket` flag that
overrides it. The explicit steps stay silent — they are the caller's instruction.

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
from typing import Any

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_bootstrap import DEFAULT_SETTLE_SECONDS, settle_fresh_pane
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
from herdr_lease import (
    REPLIES_DIR_LANE,
    check_reply_store,
    discard_reply,
    get_lease,
    get_reply,
    get_task,
    list_tasks,
    record_event,
    record_reply,
    release_lease,
    resolve_base_dir,
    state_is_readable,
)
from herdr_prompt import (
    render_envelope,
    resolve_caller,
    resolve_receiver,
    utc_stamp,
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
    add_shared_argument(parser, "json", help="print herdr's raw JSON response")
    add_shared_argument(parser, "dry_run", help="print the argv, submit nothing")
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
        help="restore the Runtime: Cwd/Resume block in the rendered envelope (default trimmed)",
    )
    _ = parser.add_argument(
        "--ticket",
        metavar="ID",
        default=None,
        help=(
            "bind this reply's task linkage to the named task (its task id, or a ticket id "
            "whose open task this sender owns is unique); without it the linkage comes from "
            "the sender's lease, else its sole open task, else the reply is unlinked"
        ),
    )
    _ = parser.add_argument(
        "--in-reply-to",
        dest="in_reply_to_record",
        metavar="RECORD",
        default=None,
        help="bind this reply to the task of the named stored reply record",
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

# The exact singular/plural forms that always match, kept from the original floor: every one
# of them also starts with a stem below, so nothing that matched before stops matching.
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

# `#231` F4: a heading word matches evidence vocabulary when it *starts with* one of these
# stems (or is exactly `ci`). The floor was an exact list, so `Validation`, `Validation
# output`, `Results`, `Reproduced`, `Commands run`, `Diff`, `Benchmark results` and friends
# were false negatives that stalled an honest completion; near-misses here are lexical, not
# conceptual. `evidence_section` documents the precedence the classes below rank by.
EVIDENCE_STEMS = (
    "evidenc",
    "verif",
    "validat",
    "gate",
    "proof",
    "witness",
    "reproduc",
    "repro",
    "artifact",
    "test",
    "pytest",
    "check",
    "log",
    "result",
    "benchmark",
    "coverag",
    "report",
    "command",
    "output",
    "diff",
    "run",
    "status",
    "outcome",
    "accept",
)
# Longest stem first, so `reproduced` resolves through `reproduc`, not `repro`.
_STEMS_LONGEST_FIRST = tuple(sorted(EVIDENCE_STEMS, key=len, reverse=True))

# `#231` F3: the ledger's `evidence` label is drawn from this closed vocabulary. A heading's
# words are mapped onto canonical evidence words and everything else is dropped, so no
# arbitrary heading text — and therefore no secret — can reach an index file. The label a
# word maps to is fixed: `Validation output` records `validation output`, not the heading.
_STEM_LABELS: dict[str, str] = {
    "evidenc": "evidence",
    "verif": "verification",
    "validat": "validation",
    "gate": "gate",
    "proof": "proof",
    "witness": "witness",
    "reproduc": "reproduction",
    "repro": "repro",
    "artifact": "artifacts",
    "test": "tests",
    "pytest": "pytest",
    "check": "checks",
    "log": "logs",
    "result": "results",
    "benchmark": "benchmark",
    "coverag": "coverage",
    "report": "report",
    "command": "commands",
    "output": "output",
    "diff": "diff",
    "run": "run",
    "status": "status",
    "outcome": "outcome",
    "accept": "acceptance",
}
_KEYWORD_LABELS: dict[str, str] = {
    "evidence": "evidence",
    "verification": "verification",
    "verified": "verification",
    "verify": "verification",
    "gate": "gate",
    "gates": "gate",
    "proof": "proof",
    "witness": "witness",
    "reproduction": "reproduction",
    "repro": "repro",
    "artifact": "artifacts",
    "artifacts": "artifacts",
    "test": "tests",
    "tests": "tests",
    "pytest": "pytest",
    "check": "checks",
    "checks": "checks",
    "log": "logs",
    "logs": "logs",
}
# Every word `evidence_label` can emit.
EVIDENCE_LABEL_WORDS = frozenset(
    {*_STEM_LABELS.values(), *_KEYWORD_LABELS.values(), "fenced", "block", "section", "ci"}
)
# The canonical section names: a heading carrying one is the strongest match, so `## Evidence`
# outranks `## Artifacts` even when `Artifacts` comes first (#231 F5).
CANONICAL_EVIDENCE_HEADS = frozenset({"evidence", "verification"})
# The floor's deny-list (#231 F4): a heading that matched no vocabulary word is still an
# evidence section when it has a body — `## What I ran` is beyond any stem set — unless it
# names a section that is plainly not evidence.
NOT_EVIDENCE_HEADS = frozenset(
    {"notes", "note", "next steps", "next", "todo", "tbd", "plan", "questions", "changelog"}
)
EVIDENCE_LABEL_LIMIT = 40
_SHA_RE = re.compile(r"[0-9a-f]{7,40}")

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
# The widened floor (#231 F4) and the precedence between a canonical name, a vocabulary
# heading, the deny-list floor and a fence are documented on `evidence_section` and pinned by
# `tests/herdr/test_herdr_reply.py`: 18 realistic headings classify `complete`, while a bare
# status line, a denied heading (`Notes`, `Next steps`, `Todo`, …) and a heading with no body
# stay `incomplete`. There is deliberately no path-citation fallback — a cited path is not
# evidence, so `## Notes` plus a path is still incomplete.
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
    """Whether a heading carries one of the exact evidence keywords (the original floor)."""
    return any(word in EVIDENCE_KEYWORDS for word in words)


def _stem_for(word: str) -> str | None:
    """The evidence stem one heading word starts with (`ci` counts), else None."""
    for stem in _STEMS_LONGEST_FIRST:
        if word.startswith(stem):
            return stem
    return "ci" if word == "ci" else None


def _label_for(word: str) -> str | None:
    """The ledger label for one heading word, or None when it is not evidence vocabulary."""
    keyword = _KEYWORD_LABELS.get(word)
    if keyword is not None:
        return keyword
    stem = _stem_for(word)
    return None if stem is None else _STEM_LABELS.get(stem, stem)


def _evidence_class(words: Sequence[str]) -> int | None:
    """How strongly a heading names evidence: 1 canonical, 2 vocabulary, None otherwise."""
    if any(word in CANONICAL_EVIDENCE_HEADS for word in words):
        return 1
    if _has_keyword(words) or any(_stem_for(word) is not None for word in words):
        return 2
    return None


def evidence_label(heading: str | None) -> str | None:
    """A ledger-safe label for a matched heading: closed vocabulary, capped at 40 (#231 F3).

    `None` for no heading, `"fenced block"` for a matched fence. Otherwise the heading's
    words are mapped onto the evidence vocabulary and the rest are dropped, so the stored
    label is always composed of words `EVIDENCE_LABEL_WORDS` lists — a heading can never
    smuggle text, and therefore never a secret, into an index file. A heading that matched
    only through the deny-list floor carries no vocabulary word and is recorded as the
    literal `"section"`.
    """
    if heading is None:
        return None
    if heading == FENCE_MARKER:
        return "fenced block"
    labels = [label for word in _normalize(heading) if (label := _label_for(word)) is not None]
    if not labels:
        return "section"
    return " ".join(labels)[:EVIDENCE_LABEL_LIMIT]


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
    """The best evidence-shaped section's heading text, else None.

    Precedence, highest first (#231 F4/F5), is a rank, not a document position: the same
    heading form ranks the same whether it is ATX (`## Status`) or bold (`**Status:**`), and a
    bold heading's inline tail counts as its body.

    1. a heading naming the canonical section (`Evidence`, `Verification`);
    2. a heading whose words match evidence vocabulary — an exact keyword or an evidence stem
       (`Artifacts`, `Tests`, `Gates`, `Gate output`, `Validation`, `Validation output`,
       `Results`, `Benchmark results`, `Reproduced`, `Commands run`, `CI`, `Diff`, …);
    3. the deny-list floor: a recognized heading form with a non-blank body (or inline tail)
       whose normalized label is not in `NOT_EVIDENCE_HEADS`, which is what admits
       `## What I ran` beyond any stem set;
    4. a fenced code block with at least one non-blank line (`FENCE_MARKER`).

    Ties go to document order, and only a section that has content counts: a heading with
    neither an inline tail nor a body before the next heading is skipped, which is why a bare
    `## Evidence` is not evidence. A fenced block immediately under a heading is that heading's
    body, not a separate section — `## Evidence` opening onto a fence still ranks class 1, and
    the fence never discards the pending heading — so the canonical reply template in
    `references/lane-coordination.md` records `Evidence` and not `Artifacts`: the canonical name
    is class 1 and `Artifacts` is class 2, however early it appears.
    """
    best: tuple[int, str] | None = None
    pending: tuple[int, str] | None = None
    in_fence = False
    fence_has_content = False
    fence_seen = False

    for raw_line in payload.splitlines():
        line = raw_line.strip()
        if _FENCE_RE.match(line):
            if in_fence:
                if fence_has_content:
                    fence_seen = True
                    # A fence directly under a heading is that heading's body: rank the
                    # pending heading by its own class before the fence closes.
                    if pending is not None:
                        if best is None or pending[0] < best[0]:
                            best = pending
                        pending = None
                in_fence = False
                fence_has_content = False
            else:
                # Opening a fence keeps `pending`: the block below may be that heading's body,
                # so it must survive until the fence proves it empty or carries content.
                in_fence = True
                fence_has_content = False
            continue
        if in_fence:
            if line:
                fence_has_content = True
            continue
        if not line:
            continue
        heading = _parse_heading(line)
        if heading is not None:
            title, inline, words = heading
            pending = None
            rank = _evidence_class(words)
            if rank is None and " ".join(words) not in NOT_EVIDENCE_HEADS:
                rank = 3
            if rank is not None:
                if inline:
                    if best is None or rank < best[0]:
                        best = (rank, title)
                else:
                    pending = (rank, title)
            continue
        if pending is not None:
            if best is None or pending[0] < best[0]:
                best = pending
            pending = None
    if in_fence and fence_has_content:
        fence_seen = True
        if pending is not None and (best is None or pending[0] < best[0]):
            best = pending
    if best is not None:
        return best[1]
    return FENCE_MARKER if fence_seen else None


def payload_shape(payload: str) -> tuple[str, str | None]:
    """(shape, evidence_heading) where shape is "complete", "incomplete" or "n/a".

    The evidence requirement applies only when `parse_status_line` maps the first line to
    `completed`; every other payload is `"n/a"` with no behaviour change. A shape check, not
    a quality gate: it never inspects whether the cited evidence is any good, so the cheapest
    `complete` is a heading named like evidence plus one non-blank line. `evidence_section`
    documents which heading is returned when a payload has several (class 1 wins over class 2,
    both win over the deny-list floor, and all three win over a fence).
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

    Two orderings carry the honesty of the pointer (#231 F2): the index is *read* before
    anything is written, so a store whose index cannot be parsed leaves no half-record behind
    (the damaged file is preserved, not clobbered); and the row that was written is
    re-resolved through the same `get_reply` the reader uses, so a pointer is only ever
    delivered for a record the reader can produce — one that does not resolve is discarded.
    """
    try:
        _ = resolve_base_dir(env=env)
    except Exception as exc:
        return None, _one_line(str(exc))
    try:
        check_reply_store(env=env)
    except Exception as exc:
        report_lease_trouble("reply record", exc)
        return None, _one_line(str(exc))
    try:
        stored = record_reply(entry, body, env=env)
    except Exception as exc:
        report_lease_trouble("reply record", exc)
        return None, _one_line(str(exc))
    try:
        resolved = get_reply(str(stored["id"]), env=env)
    except Exception as exc:
        report_lease_trouble("reply record lookup", exc)
        resolved = None
    if resolved is None:
        discard_reply(str(stored["id"]), env=env)
        return None, "the record did not resolve through the reader"
    return resolved, None


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


# ── reply task linkage (#246 D1.2) ──────────────────────────────────────────────────

# The open/terminal partition that decides which tasks the INFERRED linkage may bind (#246
# D1.4/F2). Both sets are enumerated and a test pins that they partition the store's
# `CANONICAL_STATUSES`, so a status added there cannot silently default to open and become an
# inference target. `completed` is the only status this store writes that ends the round;
# `dispatched`/`in_progress`/`blocked`/`rework` all still await their assignee.
OPEN_TASK_STATUSES = frozenset({"dispatched", "in_progress", "blocked", "rework"})
TERMINAL_TASK_STATUSES = frozenset({"completed"})


def _is_open_task(task: Mapping[str, Any]) -> bool:
    """Whether a task still awaits its assignee: its status is one of the open ones."""
    return task.get("status") in OPEN_TASK_STATUSES


def _unlinked(reason: str, exc: BaseException | None = None) -> str:
    """The one warning line for a reply that could not be bound to a task, and why."""
    detail = f" ({_one_line(str(exc))})" if exc is not None else ""
    return f"task linkage unresolved — {reason}{detail}; recording the reply unlinked"


def _inferred(task_id: str) -> str:
    """The one warning line for a linkage this step INFERRED rather than was told (#246 D1.4).

    The sole-open-task step counts the sender's open tasks; it cannot see which ticket the
    payload is about, so "exactly one candidate" is not evidence of a correct attribution. The
    default stays (it is what advances a corrected or addendum reply with no lease), and its
    silence becomes this line: the caller can tell an inferred binding from the one it asked
    for, and knows the flag that overrides it. PROBE1 measured the cost of that silence.
    """
    return (
        f"task linkage inferred — bound to your sole open task {task_id!r}; "
        "pass --ticket if this reply is about another ticket"
    )


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
        return None, _unlinked(f"--ticket {value!r} given but no sender resolved")
    try:
        tasks = list_tasks(env=env)
    except Exception as exc:
        return None, _unlinked(f"--ticket {value!r} could not be resolved", exc)
    named = [task for task in tasks if task.get("task_id") == value]
    if named:
        if named[0].get("assignee") == sender and _is_open_task(named[0]):
            return value, None
        return None, _unlinked(f"--ticket {value!r} is not an open task of sender {sender!r}")
    matching = [
        task
        for task in tasks
        if task.get("ticket_id") == value and task.get("assignee") == sender and _is_open_task(task)
    ]
    if len(matching) == 1 and isinstance(matching[0].get("task_id"), str):
        return str(matching[0]["task_id"]), None
    return None, _unlinked(
        f"--ticket {value!r} does not name exactly one open task of sender {sender!r}"
    )


def _linkage_from_record(
    record_id: str, *, sender: str | None, env: Mapping[str, str]
) -> tuple[str | None, str | None]:
    """The open task a named stored reply points at, or an unlinked warning.

    `--in-reply-to <record-id>` re-binds a follow-up to whichever task the named record was
    linked to, so a corrected or additive reply resolves without restating the ticket.
    """
    if sender is None:
        return None, _unlinked(f"--in-reply-to {record_id!r} given but no sender resolved")
    try:
        record = get_reply(record_id, env=env)
        linked = record.get("task_id") if isinstance(record, Mapping) else None
        task = get_task(linked, env=env) if isinstance(linked, str) else None
    except Exception as exc:
        return None, _unlinked(f"--in-reply-to {record_id!r} could not be resolved", exc)
    if not isinstance(record, Mapping) or record.get("sender") != sender:
        return None, _unlinked(
            f"--in-reply-to {record_id!r} names no reply record of sender {sender!r}"
        )
    if not isinstance(linked, str):
        return None, _unlinked(f"--in-reply-to {record_id!r} carries no task linkage")
    if not isinstance(task, dict) or task.get("assignee") != sender or not _is_open_task(task):
        return None, _unlinked(
            f"--in-reply-to {record_id!r} names task {linked!r}, not an open task of "
            f"sender {sender!r}"
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
    first reply), then the sender's SOLE open task. Only that last step infers, and only when
    the answer is unique: zero or several open tasks, or an explicit name that does not
    resolve to one of the sender's open tasks, records the reply unlinked with one warning
    line — a wrong linkage is worse than none.

    Every unlinked answer now carries a reason (#246 D1.3), so a recorded reply with
    `task_id: null` is never silent. The reason states the severity: when the sender had open
    work this step refused to guess at — several open tasks, a flag naming another task, or a
    task record whose id cannot be named — the line says the sender holds open work and that no
    linkage was made; when there was nothing to link, the line says the sender holds no open
    task. An unresolved sender and an unreadable store are named too, instead of a reasonless
    `(None, None)` answer.

    The inferred step also warns when it SUCCEEDS (#246 D1.4): it counts candidates, it cannot
    read which ticket the payload is about, so its binding is reported with the task id it
    chose and the flag that overrides it. The explicit steps stay silent — they are the
    caller's instruction, so a warning there would carry no information.
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
        return None, _unlinked("no sender resolved, so no task could be attributed")
    open_tasks = _sender_open_tasks(sender, env=env)
    if open_tasks is None:
        return None, _unlinked("the sender's open tasks could not be read")
    if len(open_tasks) == 1:
        task_id = open_tasks[0].get("task_id")
        if isinstance(task_id, str):
            return task_id, _inferred(task_id)
        return None, _unlinked(
            f"sender {sender!r} holds open work, but the task id is not a string"
        )
    if not open_tasks:
        return None, _unlinked(f"sender {sender!r} holds no open task")
    return None, _unlinked(
        f"sender {sender!r} holds {len(open_tasks)} open tasks, so the ticket is ambiguous"
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
    # resolved from the whole store — the explicit flag, else the lease, else the sender's sole
    # open task — and an unresolvable answer is recorded unlinked with one warning line. The
    # inferred step warns even on success (#246 D1.4): it counts candidates, so the line names
    # the task it bound and the flag that overrides it. A dry run records nothing, so it resolves
    # nothing.
    linked_task_id: str | None = None
    if not options.dry_run:
        linked_task_id, linkage_warning = resolve_task_linkage(
            sender=sender,
            lease=lease,
            explicit_ticket=options.ticket,
            in_reply_to_record=options.in_reply_to_record,
            env=env,
        )
        if linkage_warning:
            print(f"herdr-reply: {linkage_warning}", file=sys.stderr)
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
    shape, heading = payload_shape(payload)
    # The pointer and the index row carry the same bounded label, never the heading text.
    evidence = evidence_label(heading)
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
        # A revive plan shows the spawn, its settle, and the delivery argv; a plain plan stays
        # the delivery argv alone.
        if revive_argv is None:
            print(json.dumps(argv))
        else:
            plan: dict[str, object] = {
                "agent_start": revive_argv,
                "settle": options.settle,
                "agent_prompt": argv,
            }
            print(json.dumps(plan))
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
