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
from pathlib import Path

import _github
from _errors import PrError
from _github import repo_remote_for_ref

__all__ = [
    "_UNRELEASED_ATTR_RES",
    "_UNRELEASED_BULLET_RE",
    "_UNRELEASED_SECTION_RE",
    "_UNRELEASED_VERSION_END_RE",
    "_read_unreleased_block",
    "_unreleased_attribution_re",
    "stamp_changelog",
    "unreleased_attributes_pr",
]


_UNRELEASED_BULLET_RE = re.compile(r"^[*+-]\s+")


_UNRELEASED_SECTION_RE = re.compile(r"^###\s+")


_UNRELEASED_VERSION_END_RE = re.compile(r"^## \[[^\]]+\]", re.MULTILINE)


_UNRELEASED_ATTR_RES: dict[str, re.Pattern[str]] = {}


def _unreleased_attribution_re(pr_num: str) -> re.Pattern[str]:
    """Cached end-of-entry attribution matcher for one PR number (keeps re.escape)."""
    cached = _UNRELEASED_ATTR_RES.get(pr_num)
    if cached is None:
        cached = re.compile(r"\(#" + re.escape(pr_num) + r"\)(?:\s*\(BREAKING CHANGE\))?\s*$")
        _UNRELEASED_ATTR_RES[pr_num] = cached
    return cached


def _read_unreleased_block(cwd: Path | None = None) -> str | None:
    """Return the ## [Unreleased] block body, or None when absent or unreadable.

    A missing file, undecodable bytes, and a missing Unreleased heading all
    read as absent (None); the caller picks the advisory.
    """
    root = cwd or Path.cwd()
    try:
        content = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    except OSError, UnicodeDecodeError:
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
    in_section = False
    for line in block.splitlines():
        if _UNRELEASED_SECTION_RE.match(line):
            in_section = True
            continue
        if not _UNRELEASED_BULLET_RE.match(line):
            continue
        if not in_section:
            continue
        if attribution_re.search(line.rstrip()):
            return True
    return False


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
        return False

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
    bullet_re = re.compile(r"^([*+-]\s+)(.+)$")

    def entry_identity(text: str) -> str:
        s = text.strip()
        if s[:1] in "*+-":
            s = s[1:].strip()
        while True:
            trimmed = re.sub(r"\s*\(#\d+\)\s*$|\s*\(BREAKING CHANGE\)\s*$", "", s).rstrip()
            if trimmed == s:
                return s
            s = trimmed

    new_lines: list[str] = []
    modified = False

    for line in unreleased_block.splitlines(keepends=True):
        raw_line = line.rstrip("\r\n")
        m = bullet_re.match(raw_line)
        if not m:
            new_lines.append(line)
            continue

        prefix, body = m.group(1), m.group(2)
        if attribution_re.search(body):
            new_lines.append(line)
            continue

        identity = entry_identity(raw_line)
        if identity in baseline:
            new_lines.append(line)
            continue

        ending = ""
        if line.endswith("\r\n"):
            ending = "\r\n"
        elif line.endswith("\n"):
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
        _ = _github.run_command(["git", "add", "CHANGELOG.md"], cwd=cwd, check=True)
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
