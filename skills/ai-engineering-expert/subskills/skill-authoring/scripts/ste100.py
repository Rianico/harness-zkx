"""ASD-STE100 deterministic linting helper for procedural and instructional prose."""

from __future__ import annotations

import re

# STE-100 Rule 1.3: use only approved words. These fluff terms have no
# deterministic meaning and are banned in procedural/instructional prose.
STE100_BANNED_WORDS: dict[str, str] = {
    "comprehensive": "use a specific scope instead",
    "robust": "use a concrete guarantee instead",
    "properly": "use the exact condition instead",
    "various": "list items explicitly instead",
    "should work": "state the deterministic behavior instead",
}

# STE-100 Rule 6.5: keep procedural sentences to 20 words or fewer.
STE100_MAX_SENTENCE_WORDS: int = 20

_STRIP_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
_STRIP_TABLE_RE = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)
_STRIP_HEADING_RE = re.compile(r"^\s*#{1,6}\s+.*$", re.MULTILINE)
_STRIP_INLINE_CODE_RE = re.compile(r"`+[^`]+?`+")

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n{2,}|\n(?=\s*[-*+]\s+|\s*\d+\.\s+)")


def _strip_code_blocks(text: str) -> str:
    """Blank out fenced code blocks (```...```) so code lines are not linted as prose."""
    return _STRIP_CODE_RE.sub(" ", text)


def _strip_tables(text: str) -> str:
    """Blank out markdown table lines (lines matching `^\\s*\\|.*\\|\\s*$`)."""
    return _STRIP_TABLE_RE.sub("", text)


def _strip_inline_code(text: str) -> str:
    """Replace inline code spans (`...`) with a single token `code` so code syntax does not inflate prose word count."""
    return _STRIP_INLINE_CODE_RE.sub("code", text)


def _strip_headings(text: str) -> str:
    """Blank out markdown headings (`^\\s*#{1,6}\\s+.*$`)."""
    return _STRIP_HEADING_RE.sub("", text)


def split_sentences(text: str) -> list[str]:
    r"""Clean text by stripping code blocks, markdown tables, headings, and replacing inline code spans with `code`.

    Splits on sentence-ending punctuation (`[.!?]`), paragraph breaks (`\n{2,}`),
    or list items (`\n(?=\s*[-*+]\s+|\s*\d+\.\s+)`).
    Returns clean trimmed non-empty sentences.
    """
    clean = _strip_code_blocks(text)
    clean = _strip_tables(clean)
    clean = _strip_headings(clean)
    clean = _strip_inline_code(clean)
    parts = _SENTENCE_SPLIT_RE.split(clean)
    return [part.strip() for part in parts if part.strip()]


def lint_sentence_lengths(text: str, max_words: int = STE100_MAX_SENTENCE_WORDS) -> list[str]:
    """Return issues for sentences exceeding ``max_words`` words."""
    issues: list[str] = []
    for sentence in split_sentences(text):
        words = len(sentence.split())
        if words > max_words:
            preview = sentence[:80] + ("..." if len(sentence) > 80 else "")
            issues.append(f"Sentence has {words} words (max {max_words}): {preview}")
    return issues


def lint_banned_words(text: str) -> list[str]:
    """Return issues for STE-100 banned fluff terms outside fenced code blocks."""
    clean = _strip_code_blocks(text)
    issues: list[str] = []
    for term, reason in STE100_BANNED_WORDS.items():
        escaped = re.escape(term).replace(r"\ ", r"\s+")
        pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
        for match in pattern.finditer(clean):
            issues.append(f"Banned STE-100 term '{match.group(0)}': {reason}")
    return issues


__all__ = [
    "STE100_BANNED_WORDS",
    "STE100_MAX_SENTENCE_WORDS",
    "_strip_code_blocks",
    "_strip_headings",
    "_strip_inline_code",
    "_strip_tables",
    "lint_banned_words",
    "lint_sentence_lengths",
    "split_sentences",
]
