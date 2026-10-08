"""The squash-message domain: the PR Body Contract, its gates, and the message assembly.

The squash commit message is the durable artifact of a landing, so its lifecycle lives here: the
trailer helpers that keep commit attribution, the sanitiser that refuses unresolved template
tokens, the section/bullet/rollback gates, and the assembly that derives a message from the PR
body. `pr.py` (the CLI entry point) re-exports this surface, so the historical
`from pr import <name>` imports keep working; the two entry adapters that consume the CLI's
`PrOptions` and its process runner stay in `pr.py` to keep this module free of import cycles.

On the explicit `--squash-message` / `--squash-message-file` path the strict shape gate REFUSES
the constructs listed in requirement 3 — a non-contract heading, a markdown checkbox (bare or
ordered), a Mermaid fence, the raw `CODE_AUTHORS` block token, and a message over the line or
bullet budget. It does not refuse everything: an explicit message is STILL sanitized for the
ephemera requirement 3 never names — HTML comments, `<details>` blocks, `Landing:` /
`Ledger-Waiver:` directives, and empty headings — exactly as `clean_squash_body` strips them on
the `--check` preview path. So the precise reading of requirement 3 is: refuse the shape-gate
constructs, still sanitize the rest.
"""

import re
import sys
from pathlib import Path
from typing import NoReturn

from _errors import RefusalError, UsageError

__all__ = [
    "_count_squash_bullets",
    "_copy_tokens",
    "_fenced_line_mask",
    "_evidence_marker_text",
    "_is_label_line",
    "_is_stop_line",
    "_refuse_squash",
    "_section_content",
    "_section_key",
    "_section_open",
    "_states_rollback",
    "_strip_unclosed",
    "AFTER_MARKERS",
    "BEFORE_AFTER_ARROW",
    "BEFORE_MARKERS",
    "build_squash_message",
    "check_closes_lines",
    "check_explicit_squash_message",
    "check_raw_token",
    "check_squash_body",
    "check_squash_title",
    "check_title_length",
    "CHECKBOX_RE",
    "clean_squash_body",
    "copy_body_coverage",
    "copy_overlap",
    "CLOSES_LINE_RE",
    "CLOSES_REF_RE",
    "CLOSING_RE",
    "CODE_AUTHORS_TOKEN",
    "CONVENTIONAL_TYPES",
    "COPY_OVERLAP_THRESHOLD",
    "COPY_TOKEN_FLOOR",
    "DEFAULT_TEMPLATE_PATH",
    "DETAILS_BLOCK_RE",
    "DETAILS_UNCLOSED_OPENER_RE",
    "DIRECTIVE_RE",
    "DOOR_RE",
    "EMAIL_KEY_RE",
    "EMPTY_BULLET_RE",
    "FENCE_RE",
    "FIX_TYPE",
    "HEADING_RE",
    "insert_trailers",
    "is_closing_line",
    "is_fallback_body",
    "is_trailer_line",
    "is_unfilled_body",
    "LABEL_ONLY_RE",
    "MERMAID_FENCE_RE",
    "MERMAID_UNCLOSED_OPENER_RE",
    "pr_co_author_trailers",
    "print_squash_message_required",
    "PROCEDURAL_SECTION_RE",
    "refuse_mechanic_copy",
    "refuse_raw_token",
    "refuse_unfilled_body",
    "resolve_squash_message",
    "REVIEW_ONLY_SECTION_RE",
    "ROLLBACK_RE",
    "split_squash_sections",
    "SQUASH_BODY_MAX_BULLETS",
    "SQUASH_BULLET_RE",
    "SQUASH_HEADING_RE",
    "SQUASH_LABEL_RE",
    "squash_message",
    "SQUASH_MESSAGE_MAX_LINES",
    "SQUASH_MESSAGE_SPEC",
    "SQUASH_SECTIONS",
    "SQUASH_TITLE_MAX",
    "SQUASH_TITLE_RE",
    "trailer_email_key",
    "TRAILER_RE",
]


TRAILER_RE = re.compile(r"^[ \t]*co-authored-by:[ \t]*", re.IGNORECASE)
EMAIL_KEY_RE = re.compile(r"^[ \t]*co-authored-by:[^<]*<([^<>]+)>", re.IGNORECASE)
CLOSING_RE = re.compile(
    r"^[ \t]*(closes?|closed|fixes?|fixed|resolves?|resolved|refs?)[ \t]*:?[ \t]+(#[0-9]|GH-[0-9]|[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+#[0-9])",
    re.IGNORECASE,
)
PROCEDURAL_SECTION_RE = re.compile(r"^#{1,6}\s+(Checklist|Landing)\b", re.IGNORECASE)
REVIEW_ONLY_SECTION_RE = re.compile(
    r"^#{1,6}\s+(Architecture|Verification Evidence)\b", re.IGNORECASE
)
# A Mermaid fence opens with 3+ backticks OR 3+ tildes followed by `mermaid`, and closes
# with the SAME fence character (`_count_squash_bullets` uses the same rule), so `~~~mermaid`
# and a 4-backtick fence are refused on the explicit path and stripped on the preview path.
MERMAID_FENCE_RE = re.compile(
    r"^[ \t]*(?P<fence>[`~])(?P=fence){2,}[ \t]*mermaid\b.*?^[ \t]*(?P=fence){3,}[ \t]*$",
    re.DOTALL | re.MULTILINE | re.IGNORECASE,
)
MERMAID_UNCLOSED_OPENER_RE = re.compile(r"^[ \t]*(?:`{3,}|~{3,})[ \t]*mermaid\b", re.IGNORECASE)
DETAILS_BLOCK_RE = re.compile(
    r"^[ \t]*(?:[-*+][ \t]+)?<details\b.*?</details>", re.DOTALL | re.MULTILINE | re.IGNORECASE
)
DETAILS_UNCLOSED_OPENER_RE = re.compile(
    r"^[ \t]*(?:[-*+][ \t]+)?<details\b", re.MULTILINE | re.IGNORECASE
)
# `##Heading` (no space) is still a heading: administrative headings cannot ride in as prose.
HEADING_RE = re.compile(r"^#{1,6}\s*\S")
DIRECTIVE_RE = re.compile(r"^[ \t]*(Landing|Ledger-Waiver):", re.IGNORECASE)
EMPTY_BULLET_RE = re.compile(r"^[ \t]*[*+-][ \t]*$")
# A checkbox is a review artifact bare or ordered: `- [ ] x`, `1. [ ] x`, `1) [ ] x`.
CHECKBOX_RE = re.compile(r"^[ \t]*(?:(?:[-*+]|\d+[.)])[ \t]+)?\[[ xX]\](?:[ \t]|$)")
SQUASH_BULLET_RE = re.compile(r"^[ \t]*(?:[*+-]|\d+[.)])[ \t]+\S")
SQUASH_TITLE_RE = re.compile(
    r"^(?P<type>[A-Za-z]+)(?:\((?P<scope>[^()\s]+)\))?(?P<breaking>!)?:[ \t]+(?P<subject>\S.*)$"
)
SQUASH_HEADING_RE = re.compile(r"^#{1,6}\s+(?P<name>.+?)[ \t]*#*[ \t]*$")
SQUASH_LABEL_RE = re.compile(
    r"^[ \t]*(?:[-*+][ \t]+)?(?:\*\*)?(?P<name>[A-Za-z][A-Za-z &/-]*?)(?:\*\*)?[ \t]*:[ \t]*(?:\*\*)?[ \t]*(?P<rest>.*)$"
)
# The shipped PR template names containment with `**Rollback / containment:**`, so that
# label opens Blast Radius just as a `Door:` line does; `Door:` stays canonical.
DOOR_RE = re.compile(
    r"^[ \t]*(?:[-*+][ \t]+)?(?:\*\*)?(?:door|rollback[ \t]*/[ \t]*containment)(?:\*\*)?[ \t]*:",
    re.IGNORECASE,
)
ROLLBACK_RE = re.compile(r"rollback", re.IGNORECASE)
CLOSES_REF_RE = re.compile(
    r"^(?:closes?|closed|fix(?:es|ed)?|resolve[sd]?)[ \t]+#\d", re.IGNORECASE
)
CLOSES_LINE_RE = re.compile(
    r"^(?:closes?|closed|fix(?:es|ed)?|resolve[sd]?)[ \t]+#\d+$", re.IGNORECASE
)
SQUASH_TITLE_MAX = 100
# The squash body stays one screen: a short Core line, then the optional parts.
SQUASH_BODY_MAX_BULLETS = 5
# The explicit message is hand-supplied, so it is refused, never silently
# sanitized: the copy detector flags the description pasted back, and the shape
# gate keeps the message one screen (max 5 bullets / 15 lines).
COPY_OVERLAP_THRESHOLD = 0.80
COPY_TOKEN_FLOOR = 25
COPY_SHINGLE_SIZE = 5
SQUASH_MESSAGE_MAX_LINES = 15
CONVENTIONAL_TYPES = frozenset(
    {
        "feat",
        "fix",
        "docs",
        "style",
        "refactor",
        "perf",
        "test",
        "build",
        "ci",
        "chore",
        "revert",
    }
)
FIX_TYPE = "fix"
# Canonical body parts (the PR Body Contract) and the label aliases that open them.
SQUASH_SECTIONS: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "what changed", "core"),
    "root_cause": ("root cause", "root"),
    "blast_radius": ("blast radius & safety", "blast radius and safety", "blast radius"),
    "evidence": ("evidence", "proof"),
    "links": ("links", "related issues"),
}
BEFORE_AFTER_ARROW = ("\u2192", "->")
BEFORE_MARKERS = ("before", "was", "old", "prior")
AFTER_MARKERS = ("after", "now", "new")
# A bare label line (`**Before (command + output):**`) ends at its colon: it names a slot
# and states no output, so the Evidence gate counts it only when output follows it.
LABEL_ONLY_RE = re.compile(r":[ \t]*(?:[*_`]+[ \t]*)*$")
CODE_AUTHORS_TOKEN = "CODE_AUTHORS"
DEFAULT_TEMPLATE_PATH = Path(".github/pull_request_template.md")


def trailer_email_key(line: str) -> str:
    m = EMAIL_KEY_RE.search(line)
    if m:
        return m.group(1).strip().lower()
    return ""


def is_trailer_line(line: str) -> bool:
    return bool(TRAILER_RE.search(line))


def is_closing_line(line: str) -> bool:
    return bool(CLOSING_RE.search(line))


def pr_co_author_trailers(tsv: str, merger: str = "", body: str = "") -> str:
    merger_key = merger.strip().lower()
    existing_emails: set[str] = set()
    for line in body.splitlines():
        k = trailer_email_key(line)
        if k:
            existing_emails.add(k)

    seen: set[str] = set()
    trailers: list[str] = []

    for row in tsv.splitlines():
        if not row:
            continue
        parts = row.split("\t")
        login = parts[0].strip().lower() if len(parts) > 0 else ""
        name = parts[1].strip() if len(parts) > 1 else ""
        email = parts[2].strip() if len(parts) > 2 else ""

        if not name or not email:
            continue
        if merger_key and (login == merger_key or email.lower() == merger_key):
            continue
        key = email.lower()
        if key in seen or key in existing_emails:
            continue
        seen.add(key)
        trailers.append(f"Co-authored-by: {name} <{email}>")

    if not trailers:
        return ""
    return "\n".join(trailers) + "\n"


def insert_trailers(body: str, new_text: str) -> str:
    new_text_stripped = new_text.strip("\n")
    new_trailers = (
        [line for line in new_text_stripped.split("\n") if line.strip()]
        if new_text_stripped
        else []
    )

    seen: set[str] = set()
    existing_trailers: list[str] = []
    stripped_lines: list[str] = []
    dupes = False
    below = False
    closing_seen = False

    for line in body.splitlines():
        if is_trailer_line(line):
            key = trailer_email_key(line)
            if key:
                if key in seen:
                    dupes = True
                else:
                    seen.add(key)
                    existing_trailers.append(line)
                if closing_seen:
                    below = True
                continue
        if not closing_seen and is_closing_line(line):
            closing_seen = True
        stripped_lines.append(line)

    if not new_trailers and not dupes and not below:
        return body

    before_lines: list[str] = []
    after_lines: list[str] = []
    found_closing = False
    for line in stripped_lines:
        if not found_closing and is_closing_line(line):
            found_closing = True
            after_lines.append(line)
        elif not found_closing:
            before_lines.append(line)
        else:
            after_lines.append(line)

    all_trailers = existing_trailers + new_trailers
    all_str = "\n".join(all_trailers) if all_trailers else ""

    before = "\n".join(before_lines).rstrip("\n")
    after = "\n".join(after_lines).strip("\n")

    out = before
    if all_str:
        if out:
            out = out + "\n\n" + all_str
        else:
            out = all_str
        if after:
            out = out + "\n\n" + after
    else:
        if after:
            if out:
                out = out + "\n" + after
            else:
                out = after

    if body.endswith("\n"):
        out += "\n"
    return out


def check_raw_token(text: str, token: str = CODE_AUTHORS_TOKEN) -> bool:
    """True when *token* sits inside an HTML comment `<!-- ... -->`.

    Only the `<!-- CODE_AUTHORS -->` block is refused: a bare prose mention of
    `CODE_AUTHORS` outside a comment stays allowed, the pre-existing intent pinned by
    `test_raw_token_gate_ignores_prose_mentions`.
    """
    in_comment = False
    for line in text.splitlines(keepends=True):
        idx = 0
        while idx < len(line):
            if not in_comment:
                start = line.find("<!--", idx)
                if start == -1:
                    break
                in_comment = True
                idx = start + 4
            else:
                end = line.find("-->", idx)
                if end == -1:
                    if token in line[idx:]:
                        return True
                    break
                if token in line[idx:end]:
                    return True
                in_comment = False
                idx = end + 3
    return False


def refuse_raw_token(text: str, token: str = CODE_AUTHORS_TOKEN) -> None:
    if check_raw_token(text, token):
        print(f"refusing squash message: raw {token} token still present", file=sys.stderr)
        print(
            "remediation: replace the token with Co-authored-by lines for outside contributors (or delete the block), then re-run",
            file=sys.stderr,
        )
        raise RefusalError(f"raw {token} token still present")


def check_title_length(title: str, num: str | int) -> None:
    header = f"{title} (#{num})"
    if len(header) > SQUASH_TITLE_MAX:
        print(
            f"refusing squash merge: commit title exceeds {SQUASH_TITLE_MAX} chars ({len(header)}): {header}",
            file=sys.stderr,
        )
        print("remediation: shorten the PR title, then re-run", file=sys.stderr)
        raise RefusalError(f"commit title exceeds {SQUASH_TITLE_MAX} chars: {header}")


def _refuse_squash(message: str, remediation: str) -> NoReturn:
    print(f"refusing squash merge: {message}", file=sys.stderr)
    print(f"remediation: {remediation}", file=sys.stderr)
    raise RefusalError(message)


def check_squash_title(title: str, num: str | int) -> None:
    """Title gate: `type(scope): subject (#N)` — a Conventional Commit line, <= 100 chars.

    The length budget reports first, so an over-long title keeps its one message.
    The scope and the breaking `!` stay optional, as in the Convention.
    The type is matched case-insensitively: casing joins the refusals only as prose.
    """
    check_title_length(title, num)
    match = SQUASH_TITLE_RE.match(title.strip())
    if match is None or match.group("type").casefold() not in CONVENTIONAL_TYPES:
        _refuse_squash(
            f'commit title is not a Conventional Commit "type(scope): subject": {title} (#{num})',
            "rename the PR title to `type(scope): subject` "
            "(feat, fix, docs, refactor, test, ...), then re-run",
        )


def _section_key(name: str) -> str | None:
    """Canonical key for a section heading or label; None when the name is prose."""
    normalized = re.sub(r"\s+", " ", name.strip().strip("*_` ").strip().lower())
    # `## Root Cause:` and `## Root Cause` open the same section: a trailing colon is shape.
    normalized = normalized.removesuffix(":").strip()
    for key, aliases in SQUASH_SECTIONS.items():
        if normalized in aliases:
            return key
    return None


def _section_open(line: str) -> tuple[str | None, str]:
    """The heading or label name opening a line, with any inline label content.

    A heading whose name is not a section is retried before its first colon, so
    `## Root Cause: <why>` opens Root with `<why>` as its content.
    """
    heading = SQUASH_HEADING_RE.match(line)
    if heading:
        name = heading.group("name")
        if _section_key(name) is not None:
            return name, ""
        prefix, sep, rest = name.partition(":")
        if sep and _section_key(prefix) is not None:
            return prefix, rest.strip()
        return name, ""
    label = SQUASH_LABEL_RE.match(line)
    if label:
        return label.group("name"), label.group("rest")
    return None, ""


def split_squash_sections(text: str) -> tuple[dict[str, list[str]], list[str]]:
    """Bucket a cleaned squash body into declared sections plus the prose outside them.

    A heading (`## Evidence`) or a label line (`- Blast Radius: …`) opens a section;
    an unrecognized name stays prose. Prose before the first section is the Core
    narrative, so a heading-free body still carries a Core.
    """
    sections: dict[str, list[str]] = {}
    prose: list[str] = []
    current: str | None = None
    for line in text.split("\n"):
        name, rest = _section_open(line)
        key = _section_key(name) if name is not None else None
        if key is not None:
            current = key
            section = sections.setdefault(key, [])
            if rest.strip():
                section.append(rest)
            continue
        if current is None:
            prose.append(line)
        else:
            sections[current].append(line)
    return sections, prose


def _section_content(sections: dict[str, list[str]], key: str) -> str:
    return "\n".join(sections.get(key, [])).strip()


def check_closes_lines(msg: str) -> None:
    """Every closing-keyword line names exactly one issue (`Closes #12`, GitHub syntax)."""
    for line in msg.splitlines():
        stripped = line.strip()
        if CLOSES_REF_RE.match(stripped) and not CLOSES_LINE_RE.match(stripped):
            _refuse_squash(
                f'closing-keyword line is not one issue: "{stripped}"',
                "write each issue as its own `Closes #NN` line (never comma-separated), then re-run",
            )


FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")


def _fenced_line_mask(text: str) -> list[bool]:
    """Per-line mask: True where the line sits inside a balanced fenced code block.

    A fence opens a quoted span only when a matching closer appears later (backtick and
    tilde fences, any info string, Mermaid included): every line from the opener to the
    closer (both ends inclusive) is quoted material. An UNCLOSED opener quotes nothing,
    so the lines after it stay unquoted and every scan still bites (fail closed). The
    shared shape scans and `_count_squash_bullets` read this one mask.
    """
    lines = text.splitlines()
    quoted = [False] * len(lines)
    i = 0
    while i < len(lines):
        opener = FENCE_RE.match(lines[i])
        if opener is not None:
            char = opener.group(1)[0]
            closer = i + 1
            while closer < len(lines):
                end = FENCE_RE.match(lines[closer])
                if end is not None and end.group(1)[0] == char:
                    break
                closer += 1
            if closer < len(lines):
                for k in range(i, closer + 1):
                    quoted[k] = True
                i = closer + 1
                continue
        i += 1
    return quoted


def _count_squash_bullets(text: str) -> int:
    """Bullet lines outside fenced code blocks; a quoted diff or log is not the list.

    The mask comes from `_fenced_line_mask`: a balanced span (backtick and tilde
    fences, any info string) is quoted, an unclosed opener quotes nothing and the
    bullets after it still count (fail closed). Markers are `*`, `+`, `-`, and
    numbered `1.` / `1)`.
    """
    lines = text.splitlines()
    quoted = _fenced_line_mask(text)
    return sum(1 for k, line in enumerate(lines) if not quoted[k] and SQUASH_BULLET_RE.match(line))


def _states_rollback(blast_radius: list[str]) -> bool:
    """A rollback *statement*, never the label that merely names containment.

    The shipped template's `**Rollback / containment:**` label counts only when
    content follows its colon; a `Door:` line never counts on its own name. Any
    other line (or the content after a label) that names a rollback counts too.
    """
    for line in blast_radius:
        label = SQUASH_LABEL_RE.match(line)
        if label is None:
            if ROLLBACK_RE.search(line):
                return True
            continue
        name = label.group("name")
        rest = label.group("rest")
        if ROLLBACK_RE.search(name) and rest.strip():
            return True
        if ROLLBACK_RE.search(rest):
            return True
    return False


def _is_label_line(line: str) -> bool:
    """True for a bare label: nothing after its colon but emphasis markers and space.

    The shipped template's `**Before (command + output):**` is one; it names a slot, not output.
    """
    return bool(LABEL_ONLY_RE.search(line.strip()))


def _evidence_marker_text(evidence: list[str]) -> str:
    """The Evidence text the before -> after markers match against.

    A bare label line states no output, so it counts only when the block under it — the
    lines up to the next label — carries content. The shipped template's bare
    `**Before (command + output):**` / `**After (command + output):**` pair therefore reads
    as empty text and is refused; the same labels over pasted output still pair, and output
    pasted on the label's own line counts directly.
    """
    kept: list[str] = []
    for index, line in enumerate(evidence):
        if not _is_label_line(line):
            kept.append(line)
            continue
        block: list[str] = []
        for candidate in evidence[index + 1 :]:
            if _is_label_line(candidate):
                break
            block.append(candidate)
        if any(candidate.strip() for candidate in block):
            kept.append(line)
    return "\n".join(kept).lower()


def check_squash_body(msg: str, *, title: str = "", pr_link: str = "") -> None:
    """Body gate over the cleaned squash message.

    Core is required on every path. Root is required for every `fix` title, prose
    bodies included, and never for any other type. Blast Radius, Evidence, and Links
    are validated when declared: a `Door:` line (or the shipped template's
    `Rollback / containment:` label) plus a rollback statement, a before -> after over
    pasted output (a bare label is not proof), and the PR link. At most
    SQUASH_BODY_MAX_BULLETS bullets outside any fenced block
    keep the message one screen.
    """
    sections, prose = split_squash_sections(msg)
    if not _section_content(sections, "summary") and not "\n".join(prose).strip():
        _refuse_squash(
            "squash body carries no Core section",
            "write one `## Summary` line (or `- Core: <one line>`) saying what changed and why, then re-run",
        )
    match = SQUASH_TITLE_RE.match(title.strip())
    is_fix = match is not None and match.group("type").casefold() == FIX_TYPE
    if is_fix and not _section_content(sections, "root_cause"):
        _refuse_squash(
            "a fix squash body carries no Root section",
            "add a `## Root Cause` line naming why the bug happened, then re-run",
        )
    blast_radius = sections.get("blast_radius")
    if blast_radius is not None:
        if not any(DOOR_RE.match(line) for line in blast_radius):
            _refuse_squash(
                "the Blast Radius section carries neither a `Door:` line nor the "
                "template's `Rollback / containment:` line",
                "open Blast Radius with `Door: one-way` (or the template's "
                "`**Rollback / containment:** revert the squash commit`), then re-run",
            )
        if not _states_rollback(blast_radius):
            _refuse_squash(
                "the Blast Radius section states no rollback",
                "state the rollback (`**Rollback / containment:** revert the squash commit`), then re-run",
            )
    evidence = sections.get("evidence")
    if evidence is not None:
        text = _evidence_marker_text(evidence)
        arrowed = any(arrow in text for arrow in BEFORE_AFTER_ARROW)
        both = any(marker in text for marker in BEFORE_MARKERS) and any(
            marker in text for marker in AFTER_MARKERS
        )
        if not (arrowed or both):
            _refuse_squash(
                "the Evidence section states no before -> after",
                "show the before output and the after output "
                "(`before: 3 failed -> after: 0 failed`), then re-run",
            )
    links = sections.get("links")
    if links is not None and pr_link and pr_link not in "\n".join(links):
        _refuse_squash(
            "the Links section carries no PR link",
            f"add `{pr_link}` to Links, then re-run",
        )
    check_closes_lines(msg)
    bullets = _count_squash_bullets(msg)
    if bullets > SQUASH_BODY_MAX_BULLETS:
        _refuse_squash(
            f"squash body carries {bullets} bullets (max {SQUASH_BODY_MAX_BULLETS})",
            "condense the change into at most 5 bullets, then re-run",
        )


def _is_stop_line(line: str) -> bool:
    return bool(HEADING_RE.match(line) or is_closing_line(line) or is_trailer_line(line))


def _strip_unclosed(text: str, opener: re.Pattern[str]) -> str:
    """Drop each unclosed construct from its opener line up to (exclusive) the
    first heading, closing keyword, or trailer line."""
    out: list[str] = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        if opener.search(lines[i]):
            i += 1
            while i < len(lines) and not _is_stop_line(lines[i]):
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def clean_squash_body(body: str) -> str:
    """Strip review-only ephemera from a squash body.

    Removal order is deterministic: HTML comments → mermaid fences → <details>
    blocks → review-only sections → procedural sections → directives → task-list
    checkboxes →
    empty-section pruning. <details> removal runs before pruning so a section
    holding only a details block becomes empty and is dropped. Unclosed
    mermaid/<details> strips stop before the next heading, Closes keyword, or
    Co-authored-by trailer, so the sanitizer never removes those lines. Fenced
    ephemera are anchored at line start (optionally after a list marker): a
    <details> opened mid-line is prose, not markup, and is not stripped; a line
    that begins with the tag is an opener.
    """
    refuse_raw_token(body)
    text = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    # Closing/trailer lines are safe by construction: _strip_unclosed stops
    # before CLOSING_RE/TRAILER_RE lines and section scanning exits on them,
    # so every such line in text survives into pruned.
    text = MERMAID_FENCE_RE.sub("", text)
    text = _strip_unclosed(text, MERMAID_UNCLOSED_OPENER_RE)
    text = DETAILS_BLOCK_RE.sub("", text)
    text = _strip_unclosed(text, DETAILS_UNCLOSED_OPENER_RE)

    lines: list[str] = []
    in_procedural_section = False

    for line in text.splitlines():
        if HEADING_RE.match(line):
            if PROCEDURAL_SECTION_RE.match(line) or REVIEW_ONLY_SECTION_RE.match(line):
                in_procedural_section = True
                continue
            in_procedural_section = False

        if in_procedural_section:
            if is_closing_line(line) or is_trailer_line(line):
                in_procedural_section = False
            else:
                continue

        if DIRECTIVE_RE.match(line):
            continue

        if CHECKBOX_RE.match(line):
            continue

        lines.append(line)

    pruned: list[str] = []
    for i, line in enumerate(lines):
        if HEADING_RE.match(line):
            has_content = False
            for next_line in lines[i + 1 :]:
                if HEADING_RE.match(next_line):
                    break
                s = next_line.strip()
                if (
                    s
                    and not EMPTY_BULLET_RE.match(s)
                    and not is_closing_line(next_line)
                    and not is_trailer_line(next_line)
                ):
                    has_content = True
                    break
            if not has_content:
                continue
        pruned.append(line)

    result = "\n".join(pruned)
    result = re.sub(r"\n{3,}", "\n\n", result).strip()
    if body.endswith("\n") and result:
        result += "\n"
    return result


def squash_message(body: str, template_path: Path | None = None) -> str:
    template = ""
    if template_path and template_path.is_file():
        template = template_path.read_text(encoding="utf-8")
    elif not template_path:
        default_tmpl = DEFAULT_TEMPLATE_PATH
        if default_tmpl.is_file():
            template = default_tmpl.read_text(encoding="utf-8")
    trimmed_body = body.strip()
    trimmed_template = template.strip()
    if not trimmed_body or (trimmed_template and trimmed_body == trimmed_template):
        return ""
    return clean_squash_body(body)


def is_fallback_body(body: str, template_path: Path | None = None) -> bool:
    return squash_message(body, template_path=template_path) == ""


def is_unfilled_body(body: str, template_path: Path | None = None) -> bool:
    """True when *body* carries no authored description: empty, or the repo template verbatim."""
    return is_fallback_body(body, template_path=template_path)


def refuse_unfilled_body(body: str) -> None:
    """Refuse a PR whose description is empty or the unfilled repo template (exit 1)."""
    if body.strip():
        print("refusing PR: the description is the unfilled repo template", file=sys.stderr)
    else:
        print("refusing PR: no description supplied", file=sys.stderr)
    print(
        "remediation: draft the description from the git-diff-digest surface "
        "(skills/gh-router/subskills/git-diff-digest), then pass it with --body-file",
        file=sys.stderr,
    )
    raise RefusalError("PR body is empty or an unfilled template")


SQUASH_MESSAGE_SPEC = (
    'CONTEXT.md "Curated Squash Message" and '
    "skills/gh-router/subskills/pr-land/SKILL.md (Fail-Closed Squash Message)"
)


def print_squash_message_required() -> None:
    """Refusal for a merge path with no explicit squash message (shared wording)."""
    print(
        "refusing squash merge: --merge requires an explicit squash commit message "
        "(--squash-message or --squash-message-file)",
        file=sys.stderr,
    )
    print(
        "remediation: pass --squash-message MSG or --squash-message-file FILE — "
        f"no PR-body fallback (spec: {SQUASH_MESSAGE_SPEC})",
        file=sys.stderr,
    )


def _copy_tokens(text: str) -> list[str]:
    """Copy-detector tokens: trailers dropped, `-`/`_` folded to spaces, casefolded.

    `casefold()` folds more than `lower()` (e.g. `ß`), and folding intra-token `-`/`_`
    makes `fail-fast`, `fail_fast` and `fail fast` shingle alike, so punctuation cannot
    hide a pasted description.
    """
    kept = "\n".join(line for line in text.splitlines() if not is_trailer_line(line))
    folded = re.sub(r"[-_]+", " ", kept)
    return re.sub(r"\s+", " ", folded).casefold().split()


def _shingle_set(tokens: list[str], size: int = COPY_SHINGLE_SIZE) -> set[tuple[str, ...]]:
    if len(tokens) < size:
        return set()
    return {tuple(tokens[i : i + size]) for i in range(len(tokens) - size + 1)}


def _copy_shingle_pair(
    message: str, body: str
) -> tuple[set[tuple[str, ...]], set[tuple[str, ...]]] | None:
    """Message and body shingle sets, or None below the token/shingle floor of either side."""
    message_tokens = _copy_tokens(message)
    body_tokens = _copy_tokens(body)
    if len(message_tokens) < COPY_TOKEN_FLOOR or len(body_tokens) < COPY_TOKEN_FLOOR:
        return None
    message_shingles = _shingle_set(message_tokens)
    body_shingles = _shingle_set(body_tokens)
    if not message_shingles or not body_shingles:
        return None
    return message_shingles, body_shingles


def copy_overlap(message: str, body: str) -> float:
    """Jaccard overlap of normalized 5-token shingles between *message* and *body*.

    Below COPY_TOKEN_FLOOR normalized tokens on either side the texts carry too
    little signal to call copy, so 0.0 comes back and a short honest body is never
    flagged.
    """
    pair = _copy_shingle_pair(message, body)
    if pair is None:
        return 0.0
    message_shingles, body_shingles = pair
    return len(message_shingles & body_shingles) / len(message_shingles | body_shingles)


def copy_body_coverage(message: str, body: str) -> float:
    """Fraction of the body's 5-token shingles the message reproduces (`|M ∩ B| / |B|`).

    The complement to `copy_overlap`: appending novel tokens lowers the Jaccard score
    while still reproducing every body shingle, so the body coverage stays near 1.0.
    `refuse_mechanic_copy` refuses when EITHER metric exceeds the threshold. Same
    token/shingle floor as `copy_overlap`: 0.0 below it.
    """
    pair = _copy_shingle_pair(message, body)
    if pair is None:
        return 0.0
    message_shingles, body_shingles = pair
    return len(message_shingles & body_shingles) / len(body_shingles)


def _refuse_explicit(message: str, remediation: str) -> NoReturn:
    print(f"refusing squash message: {message}", file=sys.stderr)
    print(f"remediation: {remediation}", file=sys.stderr)
    raise RefusalError(message)


def refuse_mechanic_copy(message: str, body: str) -> None:
    """Refuse an explicit message that copies the PR body above the overlap threshold.

    The squash message is the curated overview of the description, never the description
    pasted back; the refusal points at the curation spec. Two metrics close the copy
    checks: Jaccard (`copy_overlap`) and body coverage (`copy_body_coverage`), each
    compared against COPY_OVERLAP_THRESHOLD. Coverage catches the append evasion (novel
    tokens bolted on to depress the Jaccard score while every body shingle survives).
    Dropping ~20% of the body, and reordering lines so boundary shingles break, remain
    deliberate evasions of both metrics; the token floor still exempts a short honest
    body.
    """
    overlap = copy_overlap(message, body)
    coverage = copy_body_coverage(message, body)
    if overlap > COPY_OVERLAP_THRESHOLD or coverage > COPY_OVERLAP_THRESHOLD:
        _refuse_explicit(
            f"mechanic copy: the message reproduces {max(overlap, coverage):.0%} of the PR body "
            f"(Jaccard {overlap:.0%}, body coverage {coverage:.0%}, "
            f"threshold {COPY_OVERLAP_THRESHOLD:.0%})",
            f"curate an overview instead of pasting the description (spec: {SQUASH_MESSAGE_SPEC})",
        )


def _non_contract_heading(line: str) -> str | None:
    """The stripped text of a heading line outside the contract vocabulary, else None."""
    if not HEADING_RE.match(line):
        return None
    name, _ = _section_open(line)
    if name is None or _section_key(name) is None:
        return line.strip()
    return None


def check_explicit_squash_message(msg: str) -> None:
    """Strict shape gate for the explicit --squash-message / --squash-message-file text.

    Hand-supplied text is refused for exactly the requirement-3 constructs, never silently
    sanitized for them: the raw CODE_AUTHORS block token, a Mermaid fence (3+ backticks OR
    3+ tildes, same closing character), a markdown checkbox (bare or `1.`/`1)` ordered), a
    heading outside the contract's section names (the `##` may sit flush against its text —
    `##Heading` counts), more than SQUASH_MESSAGE_MAX_LINES lines, or more than
    SQUASH_BODY_MAX_BULLETS bullets. It still SANITIZES the ephemera requirement 3 never
    names — HTML comments, `<details>` blocks, directives, empty headings — through
    `clean_squash_body` on the explicit and preview paths alike.

    The balanced-fence mask (`_fenced_line_mask`) skips quoted interior lines, so an honest
    message quoting a diff or log whose interior holds a `#` line or a `- [ ]` line passes;
    a Mermaid opener and an UNCLOSED fence are still refused (the unclosed span quotes
    nothing). The line budget EXCLUDES the `Co-authored-by` trailers `finalize_squash_message`
    appends later, and trailing blank lines do not count (a 15-line file ending in a newline
    stays 15). The commit title stays one line supplied separately (``commit_title``), and
    the contract's own section names are the only headings the overview carries.
    """
    refuse_raw_token(msg)
    lines = msg.splitlines()
    quoted = _fenced_line_mask(msg)
    for index, line in enumerate(lines):
        # A Mermaid opener is refused even when a balanced mask would quote it.
        if MERMAID_UNCLOSED_OPENER_RE.search(line):
            _refuse_explicit(
                "a Mermaid fence stays in the PR body, not the explicit squash message",
                "drop the Mermaid block (it is for humans in the PR body), then re-run",
            )
        if quoted[index]:
            continue
        if CHECKBOX_RE.match(line):
            _refuse_explicit(
                "a markdown checkbox is not part of the explicit squash message",
                "drop the task list; state the change as prose or bullets, then re-run",
            )
        heading = _non_contract_heading(line)
        if heading is not None:
            _refuse_explicit(
                f'the explicit squash message carries a non-contract heading: "{heading}"',
                "use only the contract section names (Summary, What Changed, Root Cause, "
                "Blast Radius & Safety, Evidence, Links), then re-run",
            )
    while lines and not lines[-1].strip():
        _ = lines.pop()
    if len(lines) > SQUASH_MESSAGE_MAX_LINES:
        _refuse_explicit(
            f"the explicit squash message carries {len(lines)} lines "
            f"(max {SQUASH_MESSAGE_MAX_LINES})",
            f"curate the message to an overview of at most {SQUASH_MESSAGE_MAX_LINES} lines, "
            "then re-run",
        )
    bullets = _count_squash_bullets(msg)
    if bullets > SQUASH_BODY_MAX_BULLETS:
        _refuse_explicit(
            f"the explicit squash message carries {bullets} bullets "
            f"(max {SQUASH_BODY_MAX_BULLETS})",
            "condense the change into at most 5 bullets, then re-run",
        )


def resolve_squash_message(
    body: str,
    *,
    explicit: str | None,
    supplied: bool,
    template_path: Path | None = None,
    require_explicit: bool = False,
) -> str:
    """Single decision point for the squash commit message (fail closed).

    The PR body's raw CODE_AUTHORS token is refused on both paths. An explicit
    message is refused when it copies the PR body, then held to the strict shape
    gate (contract headings only, no checkbox/Mermaid/token, <= 15 lines, <= 5
    bullets) and otherwise sanitized through clean_squash_body — the gate refuses the
    requirement-3 constructs but still strips HTML comments, `<details>` blocks,
    directives and empty headings; an empty one is a usage
    error. A merge path (``require_explicit``) refuses without an explicit
    message — there is no PR-body fallback there. ``--check`` keeps the
    fallback: the PR body must yield a non-empty derived squash message, or the
    gate is refused — GitHub's commit-subject synthesis is never an outcome.
    An explicit value always counts as supplied: the flag and the value are
    folded, so a caller cannot pass a message that is silently dropped.
    """
    supplied = supplied or explicit is not None
    if require_explicit and not supplied:
        print_squash_message_required()
        raise RefusalError("squash message required: --merge takes no PR-body fallback")

    if supplied:
        refuse_mechanic_copy(explicit or "", body)
        refuse_raw_token(body)
        check_explicit_squash_message(explicit or "")
        cleaned = clean_squash_body(explicit or "")
        if not cleaned.strip():
            raise UsageError("--squash-message is empty")
        return cleaned
    derived = squash_message(body, template_path=template_path)
    if not derived.strip():
        print(
            "refusing squash merge: PR body is empty or the unfilled repo template",
            file=sys.stderr,
        )
        print(
            "remediation: draft the description from the git-diff-digest surface "
            "(skills/gh-router/subskills/git-diff-digest), then pass an explicit "
            "message with --squash-message (or --squash-message-file)",
            file=sys.stderr,
        )
        raise RefusalError("squash message refused: body is empty or the repo template")
    return derived


def build_squash_message(msg: str, merger: str, tsv: str) -> str:
    cleaned = clean_squash_body(msg)
    new_trailers = pr_co_author_trailers(tsv, merger=merger, body=cleaned)
    final = insert_trailers(cleaned, new_trailers)
    # 100-character line limit on body is dropped per commit #135
    if new_trailers.strip():
        print("appended trailers:", file=sys.stderr)
        print(new_trailers, end="", file=sys.stderr)
    return final
