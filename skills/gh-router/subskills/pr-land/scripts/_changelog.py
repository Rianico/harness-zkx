"""The CHANGELOG unreleased-ledger seam: attribution reads and the auto-stamp.

`stamp_changelog` commits and pushes the attribution, so every git call this module makes
goes through the qualified `_github.run_command(...)` lookup — the tests patch that one seam
and require that no real subprocess runs. The seam's scope is pr-land's own modules: the
range/repo-root authority helper in `lib/range_authority.py` spawns its own `subprocess.run`
coverage, outside it.
"""

import os
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import _github
from _errors import PrError
from _github import _ahead_behind, _remote_branch_exists, repo_remote_for_ref

__all__ = [
    "_UNRELEASED_ATTR_RES",
    "_UNRELEASED_BULLET_RE",
    "_UNRELEASED_SECTION_RE",
    "_UNRELEASED_VERSION_END_RE",
    "_read_unreleased_block",
    "_unreleased_attribution_re",
    "stamp_changelog",
    "stamp_needed",
    "unreleased_attributes_pr",
    "warn_ledger_gap",
]


_HIDDEN_TYPES = frozenset({"docs", "chore", "style", "test", "ci", "build"})
_HIDDEN_TITLE_RE = re.compile(r"^(?P<type>[a-z]+)(?P<bang>!)?(\([^)]*\))?:")

_UNRELEASED_BULLET_RE = re.compile(r"^[*+-]\s+")


_UNRELEASED_SECTION_RE = re.compile(r"^###\s+\S")


_UNRELEASED_VERSION_END_RE = re.compile(r"^## \[[^\]]+\]", re.MULTILINE)


_UNRELEASED_ATTR_RES: dict[str, re.Pattern[str]] = {}


def _unreleased_attribution_re(pr_num: str) -> re.Pattern[str]:
    """Cached end-of-entry attribution matcher for one PR number (keeps re.escape)."""
    cached = _UNRELEASED_ATTR_RES.get(pr_num)
    if cached is None:
        cached = re.compile(r"\(#" + re.escape(pr_num) + r"\)(?:\s*\(BREAKING CHANGE\))?\s*$")
        _UNRELEASED_ATTR_RES[pr_num] = cached
    return cached


@dataclass(frozen=True)
class LedgerEntry:
    """One Unreleased-block line: the original line plus its bullet parse."""

    line: str
    raw: str
    prefix: str
    body: str
    in_section: bool


def _iter_ledger_entries(block: str) -> Iterator[LedgerEntry]:
    """Yield every line of an Unreleased block with bullet parsing attached.

    The single home for the ledger walk: section tracking, bullet detection,
    and marker splitting live here so the three readers cannot drift.
    Non-bullet lines yield with an empty prefix and body.
    """
    in_section = False
    for line in block.splitlines(keepends=True):
        raw = line.rstrip("\r\n")
        if _UNRELEASED_SECTION_RE.match(raw):
            in_section = True
        matched = _UNRELEASED_BULLET_RE.match(raw)
        if not matched:
            yield LedgerEntry(line=line, raw=raw, prefix="", body="", in_section=in_section)
            continue
        marker = matched.group(0)
        yield LedgerEntry(
            line=line, raw=raw, prefix=marker, body=raw[len(marker) :], in_section=in_section
        )


def _entry_identity(raw_line: str) -> str:
    """Ledger identity of a raw line: stripped of marker and attribution suffixes."""
    identity = raw_line.strip()
    if identity[:1] in "*+-":
        identity = identity[1:].strip()
    while True:
        trimmed = re.sub(r"\s*\(#\d+\)\s*$|\s*\(BREAKING CHANGE\)\s*$", "", identity).rstrip()
        if trimmed == identity:
            return identity
        identity = trimmed


def _read_unreleased_block(cwd: Path | None = None) -> str | None:
    """Return the ## [Unreleased] block body, or None when absent or unreadable.

    A missing file, undecodable bytes, and a missing Unreleased heading all
    read as absent (None); the caller picks the advisory.
    """
    root = cwd or Path.cwd()
    try:
        content = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    except OSError:
        return None
    except UnicodeDecodeError:
        return None
    if "## [Unreleased]" not in content:
        return None
    _, rest = content.split("## [Unreleased]", 1)
    end = _UNRELEASED_VERSION_END_RE.search(rest)
    return rest[: end.start()] if end else rest


def unreleased_attributes_pr(pr_num: str, cwd: Path | None = None) -> bool:
    """Return True when the ## [Unreleased] block carries a bullet entry for this PR.

    Scans bullet lines only, and only after a ### section heading inside the
    block (mirroring parse_unreleased_sections in scripts/changelog-gate.py);
    an entry attributes N when it ends with (#N), optionally followed by
    (BREAKING CHANGE). Mirrors ATTRIBUTION_RE in scripts/changelog-gate.py.
    A missing or unreadable CHANGELOG.md, or no Unreleased block, reads as
    unattributed (False).
    """
    block = _read_unreleased_block(cwd)
    if block is None:
        return False
    attribution_re = _unreleased_attribution_re(pr_num)
    for entry in _iter_ledger_entries(block):
        if not entry.prefix or not entry.in_section:
            continue
        if attribution_re.search(entry.raw.rstrip()):
            return True
    return False


def stamp_needed(pr_num: str, cwd: Path | None = None) -> bool:
    """True when the ledger holds an entry the stamp would attribute to this PR.

    The stamp's fail/hard-fail contract needs want-vs-outcome: a stamp that had
    nothing to attribute is a no-op (soft), while a stamp that tried and failed
    hard-fails after PR creation. Mirrors `stamp_changelog`'s bullet walk — an
    already-attributed block and baseline entries never count — without writing.
    """
    block = _read_unreleased_block(cwd)
    if block is None or f"(#{pr_num})" in block:
        return False
    root = cwd or Path.cwd()
    baseline_path = root / ".config" / "changelog-unattributed-baseline.txt"
    baseline: set[str] = set()
    if baseline_path.is_file():
        try:
            baseline = {
                line.strip()
                for line in baseline_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")
            }
        except OSError:
            baseline = set()
    any_attribution_re = re.compile(r"\(#\d+\)(?:\s*\(BREAKING CHANGE\))?\s*$")
    for entry in _iter_ledger_entries(block):
        if not entry.prefix:
            continue
        if any_attribution_re.search(entry.body):
            continue
        if _entry_identity(entry.raw) in baseline:
            continue
        return True
    return False


def _push_stranded_stamp(head_ref: str, pr_num: str, cwd: Path | None = None) -> bool:
    """Push the stranded stamp commit for an already-attributed entry.
    Returns True when a push repaired the remote, False when the branch is already
    in sync or the push failed (warning on stderr, the same soft failure as the
    stamp's own push). Never commits, never rewrites CHANGELOG.md, never force-pushes.
    """
    try:
        remote = repo_remote_for_ref(head_ref, cwd=cwd)
        if not _remote_branch_exists(head_ref, cwd=cwd, remote=remote):
            needs_push = True
        else:
            ahead, _ = _ahead_behind(head_ref, remote, cwd=cwd)
            needs_push = ahead > 0
        if not needs_push:
            return False
        push_res = _github.run_command(["git", "push", remote, head_ref], cwd=cwd)
        if push_res.returncode != 0:
            print(
                f"warning: git push to {remote} {head_ref} failed: {push_res.stderr.strip()}",
                file=sys.stderr,
            )
            return False
        print(
            f"recovered stranded stamp for #{pr_num}: pushed to {remote}/{head_ref}",
            file=sys.stderr,
        )
    except PrError as e:
        print(f"warning: changelog stamp recovery skipped: {e}", file=sys.stderr)
        return False
    return True


def stamp_changelog(
    head_ref: str,
    pr_num: str,
    cwd: Path | None = None,
) -> bool:
    root = cwd or Path.cwd()
    changelog_path = root / "CHANGELOG.md"
    if not changelog_path.is_file():
        return False

    try:
        content = changelog_path.read_text(encoding="utf-8")
    except OSError:
        return False

    if "## [Unreleased]" not in content:
        return False

    before_unreleased, rest = content.split("## [Unreleased]", 1)
    version_match = re.search(r"^## \[[^\]]+\].*", rest, re.MULTILINE)
    if version_match:
        unreleased_block = rest[: version_match.start()]
        after_unreleased = rest[version_match.start() :]
    else:
        unreleased_block = rest
        after_unreleased = ""

    if f"(#{pr_num})" in unreleased_block:
        # Recovery: a previous run stamped and committed but its push failed, leaving
        # the commit stranded. Repair the remote instead of returning early; when the
        # branch is already in sync this stays a no-op.
        return _push_stranded_stamp(head_ref, pr_num, cwd=cwd)
    baseline_path = root / ".config" / "changelog-unattributed-baseline.txt"
    baseline: set[str] = set()
    if baseline_path.is_file():
        try:
            baseline = {
                line.strip()
                for line in baseline_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")
            }
        except OSError:
            baseline = set()

    attribution_re = re.compile(r"\(#\d+\)(?:\s*\(BREAKING CHANGE\))?\s*$")
    breaking_re = re.compile(r"\s*\(BREAKING CHANGE\)\s*$")
    new_lines: list[str] = []
    modified = False

    for entry in _iter_ledger_entries(unreleased_block):
        if not entry.prefix:
            new_lines.append(entry.line)
            continue
        prefix, body, raw_line = entry.prefix, entry.body, entry.raw
        if attribution_re.search(body):
            new_lines.append(entry.line)
            continue

        identity = _entry_identity(raw_line)
        if identity in baseline:
            new_lines.append(entry.line)
            continue

        ending = ""
        if entry.line.endswith("\r\n"):
            ending = "\r\n"
        elif entry.line.endswith("\n"):
            ending = "\n"
        if breaking_re.search(body):
            body_without_breaking = breaking_re.sub("", body).rstrip()
            stamped_body = f"{body_without_breaking} (#{pr_num}) (BREAKING CHANGE)"
        else:
            stamped_body = f"{body.rstrip()} (#{pr_num})"

        new_lines.append(f"{prefix}{stamped_body}{ending}")
        modified = True

    if not modified:
        return False

    new_unreleased = "".join(new_lines)
    new_content = before_unreleased + "## [Unreleased]" + new_unreleased + after_unreleased

    try:
        _ = changelog_path.write_text(new_content, encoding="utf-8")
    except OSError as e:
        print(f"warning: could not write stamped CHANGELOG.md: {e}", file=sys.stderr)
        return False

    try:
        add_res = _github.run_command(["git", "add", "CHANGELOG.md"], cwd=cwd)
        if add_res.returncode != 0:
            print(
                f"warning: git add failed during changelog stamp: {add_res.stderr.strip()}",
                file=sys.stderr,
            )
            return False
        commit_res = _github.run_command(
            ["git", "commit", "-m", f"chore(changelog): attribute #{pr_num} in unreleased ledger"],
            cwd=cwd,
            timeout=60.0,
            env={**os.environ, "HARNESS_CHECK_SKIP_TESTS": "1"},
        )
        if commit_res.returncode != 0:
            print(
                f"warning: git commit failed during changelog stamp: {commit_res.stderr.strip()}",
                file=sys.stderr,
            )
            return False

        remote = repo_remote_for_ref(head_ref, cwd=cwd)
        push_res = _github.run_command(["git", "push", remote, head_ref], cwd=cwd)
        if push_res.returncode != 0:
            print(
                f"warning: git push to {remote} {head_ref} failed: {push_res.stderr.strip()}",
                file=sys.stderr,
            )
            return False

        print(
            f"attributed #{pr_num} in CHANGELOG.md and pushed to {remote}/{head_ref}",
            file=sys.stderr,
        )
        return True
    except PrError as e:
        print(f"warning: changelog auto-stamp failed: {e}", file=sys.stderr)
        return False


def _title_is_hidden(title: str) -> bool:
    """Mirror the ledger gate: a hidden type without `!` owes no entry."""
    match = _HIDDEN_TITLE_RE.match(title.strip().casefold())
    if match is None or match.group("bang") is not None:
        return False
    return match.group("type") in _HIDDEN_TYPES


def warn_ledger_gap(num: str, draft: bool, no_stamp: bool, title: str = "") -> None:
    """Advise when no ## [Unreleased] entry carries `(#num)` after a create-or-reuse.

    The single home for the ledger advisory: the no-section, draft, and ready
    wordings live here once instead of once per stamp-mode branch in `pr.py`.
    A hidden-type title with nothing left to attribute owes no entry: the gate
    exempts exactly that case, so it prints nothing.
    Pure commentary on stderr; never refuses, never mutates.
    """
    block = _read_unreleased_block()
    if block is None:
        print(
            "warning: no ## [Unreleased] section in CHANGELOG.md; "
            "the Ledger floor gate requires one before this PR can land. "
            f"Add the section with an entry ending in (#{num}).",
            file=sys.stderr,
        )
        return
    if _title_is_hidden(title) and not stamp_needed(num):
        return
    if draft:
        if no_stamp:
            print(
                f"note: --no-stamp: head was not stamped for PR #{num} — "
                f"no ## [Unreleased] entry carries (#{num}); the Ledger floor gate "
                "(changelog gate) rejects this PR once it goes ready. "
                f"Add an entry ending in (#{num}) before you flip it ready.",
                file=sys.stderr,
            )
        else:
            print(
                f"note: no ## [Unreleased] entry carries (#{num}); "
                "the Ledger floor gate rejects this PR once it goes ready. "
                f"Add an entry ending in (#{num}) before you flip it ready "
                "(the PR-body `Ledger-Waiver:` trailer overrides the gate for this PR).",
                file=sys.stderr,
            )
    elif no_stamp:
        print(
            f"warning: --no-stamp: head was not stamped for PR #{num} — "
            f"no ## [Unreleased] entry carries (#{num}); the Ledger floor gate "
            f'("#{num} carries no entries in ## [Unreleased]") will reject this PR '
            "and the changelog gate stays red "
            "(the PR-body `Ledger-Waiver:` trailer overrides the gate for this PR). "
            f"Add an entry ending in (#{num}) and push it, or re-run without --no-stamp.",
            file=sys.stderr,
        )
    else:
        print(
            f"warning: no ## [Unreleased] entry carries (#{num}); "
            "the Ledger floor gate\n"
            f'("#{num} carries no entries in ## [Unreleased]") will reject this PR on the\n'
            f"ready flip. Add an entry ending in (#{num}), commit it to this branch, or\n"
            "leave the PR draft until the entry lands "
            "(the PR-body `Ledger-Waiver:` trailer overrides the gate for this PR).",
            file=sys.stderr,
        )
