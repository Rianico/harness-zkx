"""ASD-STE100 Issue 9 (published January 15, 2025) deterministic linting helper for procedural and instructional prose."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# STE-100 Rule 1.1: use only approved words. Rule 1.3 requires that an
# approved word carries only its approved meaning. These fluff terms have no
# deterministic meaning and are banned in procedural/instructional prose.
STE100_BANNED_WORDS: dict[str, str] = {
    "comprehensive": "use a specific scope instead",
    "robust": "use a concrete guarantee instead",
    "properly": "use the exact condition instead",
    "various": "list items explicitly instead",
    "should work": "state the deterministic behavior instead",
    "seamless": "state the concrete interface or protocol guarantee instead",
    "cutting-edge": "state the exact version, benchmark, or technique instead",
    "effortless": "state the automated step or command instead",
    "blazing-fast": "state the latency or throughput metric instead",
    "state-of-the-art": "state the baseline model or benchmark result instead",
    "game-changing": "state the measurable improvement instead",
}

# Banned soft phrasal verbs in technical prose.
STE100_BANNED_PHRASAL_VERBS: dict[str, str] = {
    "spin up": "use a specific lifecycle verb (e.g. start, initialize, provision) instead",
    "kick off": "use a specific verb (e.g. start, begin, trigger) instead",
    "dive into": "use an analytical verb (e.g. inspect, examine, detail) instead",
    "reach out": "use a direct communication verb (e.g. contact, query, message) instead",
    "circle back": "use a specific follow-up verb (e.g. revisit, follow up, return) instead",
    "touch base": "use a direct verb (e.g. confer, contact, sync) instead",
}

# Target verbal nouns for smothered verbs / nominalizations detection.
_SMOTHERED_VERB_NOUNS: dict[str, str] = {
    "analysis": "analyze",
    "analyses": "analyze",
    "determination": "determine",
    "determinations": "determine",
    "assessment": "assess",
    "assessments": "assess",
    "investigation": "investigate",
    "investigations": "investigate",
    "verification": "verify",
    "verifications": "verify",
    "validation": "validate",
    "validations": "validate",
    "execution": "execute",
    "executions": "execute",
    "measurement": "measure",
    "measurements": "measure",
    "modification": "modify",
    "modifications": "modify",
    "allocation": "allocate",
    "allocations": "allocate",
    "conversion": "convert",
    "conversions": "convert",
    "deployment": "deploy",
    "deployments": "deploy",
    "migration": "migrate",
    "migrations": "migrate",
    "installation": "install",
    "installations": "install",
    "inspection": "inspect",
    "inspections": "inspect",
}

# STE-100 Rule 5.1 (keep procedural sentences to 20 words or fewer).
STE100_MAX_SENTENCE_WORDS: int = 20

_STRIP_CODE_RE = re.compile(r"(?:`{3,}[\s\S]*?`{3,}|~{3,}[\s\S]*?~{3,})")
_STRIP_TABLE_RE = re.compile(r"^.*\|.*$", re.MULTILINE)
_STRIP_HEADING_RE = re.compile(r"^\s*#{1,6}\s+.*$", re.MULTILINE)
_STRIP_INLINE_CODE_RE = re.compile(r"`+[^`]+?`+")
_HTML_ENTITY_RE = re.compile(r"&(?:[a-zA-Z0-9]+|#\d+|#[xX][0-9a-fA-F]+);")
_HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]+\)")
_URL_RE = re.compile(r"\b(?:https?://|mailto:|tel:)[^\s)\]>\"']+", re.IGNORECASE)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n{2,}|\n(?=\s*[-*+]\s+|\s*\d+\.\s+)")

_PHRASAL_VERB_PATTERNS: dict[str, re.Pattern[str]] = {
    "spin up": re.compile(r"\b(spin[s]?|spinning|spun)[-\s]+up\b", re.IGNORECASE),
    "kick off": re.compile(r"\bkick(?:s|ed|ing)?[-\s]+off\b", re.IGNORECASE),
    "dive into": re.compile(r"\b(dive[sd]?|diving|dove)[-\s]+into\b", re.IGNORECASE),
    "reach out": re.compile(r"\breach(?:es|ed|ing)?[-\s]+out\b", re.IGNORECASE),
    "circle back": re.compile(r"\b(circle[sd]?|circling)[-\s]+back\b", re.IGNORECASE),
    "touch base": re.compile(r"\btouch(?:es|ed|ing)?[-\s]+base\b", re.IGNORECASE),
}

_NOMINALIZATION_NOUNS_PATTERN = "|".join(_SMOTHERED_VERB_NOUNS.keys())
_NOMINALIZATION_RE = re.compile(
    r"\b(perform(?:s|ed|ing)?|conduct(?:s|ed|ing)?|carr(?:y|ies|ied|ying)\s+out|make[s]?|made|making)\s+"
    r"(a|an|the)\s+"
    r"(?:[a-zA-Z-]+\s+)?"
    rf"({_NOMINALIZATION_NOUNS_PATTERN})\b",
    re.IGNORECASE,
)


def _strip_code_blocks(text: str) -> str:
    """Blank out fenced code blocks (``` or ~~~) so code lines are not linted as prose."""
    return _STRIP_CODE_RE.sub(" ", text)


def _strip_tables(text: str) -> str:
    """Blank out markdown table lines (any line containing a pipe `|` separator)."""
    return _STRIP_TABLE_RE.sub("", text)


def _strip_inline_code(text: str) -> str:
    """Replace inline code spans (`...`) with token `code` so code syntax does not inflate prose word count."""
    return _STRIP_INLINE_CODE_RE.sub("code", text)


def _strip_headings(text: str) -> str:
    """Blank out markdown headings (`^\\s*#{1,6}\\s+.*$`)."""
    return _STRIP_HEADING_RE.sub("", text)


def _strip_html_entities(text: str) -> str:
    """Blank out HTML entities like &amp;, &nbsp;, &#123;, etc."""
    return _HTML_ENTITY_RE.sub(" ", text)


def _strip_html_comments(text: str) -> str:
    """Blank out HTML comments (`<!-- ... -->`)."""
    return _HTML_COMMENT_RE.sub(" ", text)


def _strip_html_tags(text: str) -> str:
    """Blank out HTML tags like `<a href="...">` and `</span>`."""
    return _HTML_TAG_RE.sub(" ", text)


def _strip_urls_and_links(text: str) -> str:
    """Strip markdown links (preserving link text), URIs (http, mailto, tel), and link titles."""
    clean = _MARKDOWN_LINK_RE.sub(r"\1", text)
    return _URL_RE.sub(" ", clean)


def _prepare(
    text: str,
    *,
    code_blocks: bool = True,
    tables: bool = True,
    headings: bool = True,
    inline_code: bool = True,
    urls_and_links: bool = False,
    html_tags_comments: bool = False,
) -> str:
    """Prepare text for linting by stripping non-prose structures according to policy."""
    clean = text
    if html_tags_comments:
        clean = _strip_html_comments(clean)
        clean = _strip_html_tags(clean)
        clean = _strip_html_entities(clean)
    if code_blocks:
        clean = _strip_code_blocks(clean)
    if inline_code:
        clean = _strip_inline_code(clean)
    if urls_and_links:
        clean = _strip_urls_and_links(clean)
    if tables:
        clean = _strip_tables(clean)
    if headings:
        clean = _strip_headings(clean)
    return clean


def split_sentences(text: str) -> list[str]:
    r"""Clean text by stripping code blocks, markdown tables, headings, and replacing inline code spans with `code`.

    Splits on sentence-ending punctuation (`[.!?]`), paragraph breaks (`\n{2,}`),
    or list items (`\n(?=\s*[-*+]\s+|\s*\d+\.\s+)`).
    Returns clean trimmed non-empty sentences.
    """
    clean = _prepare(
        text,
        code_blocks=True,
        tables=True,
        headings=True,
        inline_code=True,
        urls_and_links=False,
        html_tags_comments=False,
    )
    parts = _SENTENCE_SPLIT_RE.split(clean)
    return [part.strip() for part in parts if part.strip()]


_PARENTHETICAL_RE = re.compile(r"\([^()]*\)")


def _count_ste_words(sentence: str) -> int:
    r"""Count words by the STE-100 Rule 8.5-8.7 conventions.

    Rule 8.5: text in parentheses counts as one word.
    Rule 8.6: each element (number, abbreviation, identifier, symbol, unit) counts as one word.
    Rule 8.7: a hyphenated word counts as one word.
    Rules 8.6 and 8.7 hold already, because a whitespace split keeps each token intact.
    """
    collapsed = sentence
    for _ in range(4):
        reduced = _PARENTHETICAL_RE.sub("word", collapsed)
        if reduced == collapsed:
            break
        collapsed = reduced
    return len(collapsed.split())


def lint_sentence_lengths(text: str, max_words: int = STE100_MAX_SENTENCE_WORDS) -> list[str]:
    """Return issues for sentences exceeding ``max_words`` words by the Rule 8.5-8.7 count."""
    issues: list[str] = []
    for sentence in split_sentences(text):
        words = _count_ste_words(sentence)
        if words > max_words:
            preview = sentence[:80] + ("..." if len(sentence) > 80 else "")
            issues.append(f"Sentence has {words} words (max {max_words}): {preview}")
    return issues


def lint_banned_words(text: str) -> list[str]:
    """Return issues for STE-100 banned fluff terms outside code blocks, tables, and inline code."""
    clean = _prepare(
        text,
        code_blocks=True,
        tables=True,
        headings=False,
        inline_code=True,
        urls_and_links=False,
        html_tags_comments=False,
    )
    issues: list[str] = []
    for term, reason in STE100_BANNED_WORDS.items():
        escaped = re.escape(term).replace(r"\ ", r"\s+").replace(r"\-", r"[- ]")
        pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
        for match in pattern.finditer(clean):
            issues.append(f"Banned STE-100 term '{match.group(0)}': {reason}")
    return issues


def lint_phrasal_verbs(text: str) -> list[str]:
    """Return issues for banned soft phrasal verbs outside code blocks, tables, and inline code."""
    clean = _prepare(
        text,
        code_blocks=True,
        tables=True,
        headings=False,
        inline_code=True,
        urls_and_links=False,
        html_tags_comments=False,
    )
    issues: list[str] = []
    for verb, reason in STE100_BANNED_PHRASAL_VERBS.items():
        pattern = _PHRASAL_VERB_PATTERNS.get(verb)
        if pattern is None:
            escaped = re.escape(verb).replace(r"\ ", r"[-\s]+")
            pattern = re.compile(rf"\b{escaped}\b", re.IGNORECASE)
        for match in pattern.finditer(clean):
            issues.append(f"Banned phrasal verb '{match.group(0)}': {reason}")
    return issues


def lint_semicolons(text: str) -> list[str]:
    """Flag semicolons in prose outside code blocks, inline code, URLs, HTML comments/tags, and entities."""
    clean = _prepare(
        text,
        code_blocks=True,
        tables=True,
        headings=False,
        inline_code=True,
        urls_and_links=True,
        html_tags_comments=True,
    )
    issues: list[str] = []
    for line in clean.splitlines():
        if ";" in line:
            preview = line.strip()[:80] + ("..." if len(line.strip()) > 80 else "")
            issues.append(f"Semicolon in prose (STE-100 Rule 8.1): {preview}")
    return issues


def lint_nominalizations(text: str) -> list[str]:
    """Detect smothered verbs (STE-100 Rule 3.7: use an approved verb to describe an action, not a noun)."""
    clean = _prepare(
        text,
        code_blocks=True,
        tables=True,
        headings=False,
        inline_code=True,
        urls_and_links=False,
        html_tags_comments=False,
    )
    issues: list[str] = []
    for match in _NOMINALIZATION_RE.finditer(clean):
        noun = match.group(3).lower()
        direct_verb = _SMOTHERED_VERB_NOUNS.get(noun, "direct verb")
        issues.append(
            f"Smothered verb nominalization '{match.group(0)}': use '{direct_verb}' instead"
        )
    return issues


def _lint_markdown_content(content: str, max_words: int = STE100_MAX_SENTENCE_WORDS) -> list[str]:
    """Run all STE-100 deterministic linters on markdown text, stripping frontmatter if present."""
    frontmatter_match = re.search(r"^---\n.*?\n---", content, re.DOTALL)
    body = content[frontmatter_match.end() :] if frontmatter_match else content

    issues: list[str] = []
    issues.extend(lint_sentence_lengths(body, max_words=max_words))
    issues.extend(lint_banned_words(body))
    issues.extend(lint_phrasal_verbs(body))
    issues.extend(lint_semicolons(body))
    issues.extend(lint_nominalizations(body))
    return issues


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for standalone ASD-STE100 linting."""
    parser = argparse.ArgumentParser(
        prog="ste100",
        description="ASD-STE100 Issue 9 (published January 15, 2025) deterministic linter for procedural and instructional prose.",
    )
    _ = parser.add_argument("path", type=Path, help="Path to markdown file or directory to lint")
    _ = parser.add_argument(
        "--max-words",
        type=int,
        default=STE100_MAX_SENTENCE_WORDS,
        help=f"Maximum allowed words per sentence (default: {STE100_MAX_SENTENCE_WORDS})",
    )
    args = parser.parse_args(argv)

    target_path: Path = args.path
    if not target_path.exists():
        print(f"Error: path does not exist: {target_path}", file=sys.stderr)
        return 2

    files_to_lint: list[Path] = []
    if target_path.is_file():
        files_to_lint.append(target_path)
    elif target_path.is_dir():
        files_to_lint.extend(sorted(target_path.rglob("*.md")))

    if not files_to_lint:
        print(f"No markdown files found under: {target_path}")
        return 0

    total_issues = 0
    for file_path in files_to_lint:
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as exc:
            print(f"Error reading {file_path}: {exc}", file=sys.stderr)
            total_issues += 1
            continue

        issues = _lint_markdown_content(content, max_words=args.max_words)
        if issues:
            total_issues += len(issues)
            print(f"FAIL  {file_path} ({len(issues)} issue{'s' if len(issues) != 1 else ''}):")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"PASS  {file_path}")

    if total_issues > 0:
        print(f"\nTotal STE-100 issues: {total_issues}")
        return 1

    print("\nAll files passed STE-100 deterministic linting.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

__all__ = [
    "STE100_BANNED_PHRASAL_VERBS",
    "STE100_BANNED_WORDS",
    "STE100_MAX_SENTENCE_WORDS",
    "_prepare",
    "_strip_code_blocks",
    "_strip_headings",
    "_strip_html_comments",
    "_strip_html_entities",
    "_strip_html_tags",
    "_strip_inline_code",
    "_strip_tables",
    "_strip_urls_and_links",
    "lint_banned_words",
    "lint_nominalizations",
    "lint_phrasal_verbs",
    "lint_semicolons",
    "lint_sentence_lengths",
    "main",
    "split_sentences",
]
