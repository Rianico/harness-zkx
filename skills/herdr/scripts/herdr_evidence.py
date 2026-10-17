"""herdr-evidence — status-line classification and evidence-shape analysis.

Owns the two pure reads a reply payload needs: mapping its first non-empty line onto
a status (`parse_status_line`), and deciding whether it cites evidence
(`evidence_section`, `payload_shape`, `evidence_label`, `extract_artifacts`).
Stdlib only: no I/O and no other herdr module.
"""

from __future__ import annotations

import re
from collections.abc import Sequence

__all__ = [
    "STATUS_MAP",
    "parse_status_line",
    "EVIDENCE_KEYWORDS",
    "EVIDENCE_STEMS",
    "EVIDENCE_LABEL_WORDS",
    "CANONICAL_EVIDENCE_HEADS",
    "NOT_EVIDENCE_HEADS",
    "EVIDENCE_LABEL_LIMIT",
    "FENCE_MARKER",
    "ARTIFACT_LIMIT",
    "evidence_label",
    "evidence_section",
    "payload_shape",
    "extract_artifacts",
]


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
