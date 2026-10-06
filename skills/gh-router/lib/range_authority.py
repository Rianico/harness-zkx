#!/usr/bin/env python3
"""Shared git primitives plus the range authority for gh-router.

Spec grammar for ``resolve_range(spec, mode)``::

    spec       ::= two_dot | three_dot | sha_pair | single_ref
    two_dot    ::= <ref> ".." <ref>        # base used exactly as given
    three_dot  ::= <ref> "..." <ref>       # base replaced by merge-base
    sha_pair   ::= <sha> <sha>             # whitespace-separated pair,
                                          # explicit base, operator = mode
    single_ref ::= <ref>                   # base resolved via origin/HEAD,
                                          # then origin/main, then
                                          # origin/master; operator = mode

``mode`` is one of ``".."`` or ``"..."``. When ``spec`` already carries an
operator, that operator wins and ``mode`` is only recorded. ``<ref>`` is
anything ``git rev-parse --verify`` accepts locally (branch, tag, full or
abbreviated SHA). Only local plumbing runs here: ``rev-parse --verify``,
``merge-base`` and ``rev-list`` (plus ``rev-parse --show-toplevel`` for root
discovery, mirroring ``lib/repo.sh`` practice of never touching the network).
``fetch``, ``ls-remote`` and ``remote`` never run.
"""

from __future__ import annotations

import difflib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

__all__ = (
    "MalformedSpec",
    "RangeRefusal",
    "RangeResolution",
    "RangeDict",
    "RangeCounts",
    "RangeCountsDict",
    "ResolvedFrom",
    "build_diff",
    "exit_code_for",
    "find_repo_root",
    "get_commit_summary",
    "resolve_range",
    "run_git",
    "truncate_lines",
)

ResolvedFrom = Literal["explicit", "origin/HEAD", "origin/main", "origin/master"]

_EXPLICIT: ResolvedFrom = "explicit"

_BASE_CANDIDATES: tuple[ResolvedFrom, ...] = (
    "origin/HEAD",
    "origin/main",
    "origin/master",
)

_MODES: tuple[str, str] = ("..", "...")

_SHA_TOKEN = r"[0-9a-fA-F]{4,40}"
_SHA_PAIR_RE = re.compile(rf"({_SHA_TOKEN})\s+({_SHA_TOKEN})")


class MalformedSpec(ValueError):
    """The range spec (or mode) is syntactically unusable. Exit 2."""


class RangeRefusal(RuntimeError):
    """The spec parses but the range cannot be resolved locally. Exit 3."""


def exit_code_for(exc: BaseException) -> int:
    """Map a range failure to its process exit code."""
    if isinstance(exc, MalformedSpec):
        return 2
    if isinstance(exc, RangeRefusal):
        return 3
    return 1


def run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return result.stdout


def find_repo_root(start: Path) -> Path:
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "not a git repository"
        raise RuntimeError(message)
    return Path(result.stdout.strip()).resolve()


def get_commit_summary(repo_root: Path, ref: str, path: str | None = None) -> dict[str, str] | None:
    """Extract commit details (sha, author, relative_time/date, subject, body)."""
    fmt = "%h%x00%an%x00%ar%x00%s%x00%b"
    cmd = ["git", "-C", str(repo_root), "log", "-1", f"--format={fmt}", ref]
    if path is not None:
        cmd_with_path = [*cmd, "--", path]
        res = subprocess.run(cmd_with_path, capture_output=True, text=True, check=False)
        if res.returncode == 0 and res.stdout.strip():
            parts = res.stdout.rstrip("\n").split("\x00", 4)
            if len(parts) == 5:
                return {
                    "sha": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "relative_time": parts[2],
                    "subject": parts[3],
                    "body": parts[4].strip(),
                }
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0 or not res.stdout.strip():
        return None
    parts = res.stdout.rstrip("\n").split("\x00", 4)
    if len(parts) != 5:
        return None
    return {
        "sha": parts[0],
        "author": parts[1],
        "date": parts[2],
        "relative_time": parts[2],
        "subject": parts[3],
        "body": parts[4].strip(),
    }


def truncate_lines(lines: list[str], max_lines: int) -> list[str]:
    if len(lines) <= max_lines:
        return lines
    omitted = len(lines) - max_lines
    return [*lines[:max_lines], f"... ({omitted} more lines omitted)"]


def build_diff(
    left_lines: list[str],
    right_lines: list[str],
    left_label: str,
    right_label: str,
    max_lines: int,
) -> list[str]:
    diff = list(
        difflib.unified_diff(
            left_lines,
            right_lines,
            fromfile=left_label,
            tofile=right_label,
            lineterm="",
        )
    )
    if not diff:
        diff = ["(no textual diff)"]
    return truncate_lines(diff, max_lines)


@dataclass(frozen=True, slots=True)
class RangeCounts:
    """Cardinality of each side of a resolved range."""

    commits: int
    only_in_base: int


@dataclass(frozen=True, slots=True)
class RangeResolution:
    """Resolved commit range: head side ``commits`` oldest first.

    ``only_in_base`` holds base-side commits and is always computed, even
    when ``commits`` is empty (head behind base or identical tips).
    """

    mode: str
    base_ref: str
    head_ref: str
    resolved_from: ResolvedFrom
    merge_base: str
    commits: tuple[str, ...]
    only_in_base: tuple[str, ...]
    counts: RangeCounts

    def to_dict(self) -> RangeDict:
        """Serialize to plain JSON-ready types at the seam."""
        return {
            "mode": self.mode,
            "base_ref": self.base_ref,
            "head_ref": self.head_ref,
            "resolved_from": self.resolved_from,
            "merge_base": self.merge_base,
            "commits": list(self.commits),
            "only_in_base": list(self.only_in_base),
            "counts": {"commits": self.counts.commits, "only_in_base": self.counts.only_in_base},
        }


class RangeCountsDict(TypedDict):
    commits: int
    only_in_base: int


class RangeDict(TypedDict):
    mode: str
    base_ref: str
    head_ref: str
    resolved_from: str
    merge_base: str
    commits: list[str]
    only_in_base: list[str]
    counts: RangeCountsDict


def _verify(repo_root: Path, ref: str) -> bool:
    probe = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "--verify", "-q", ref],
        capture_output=True,
        text=True,
        check=False,
    )
    return probe.returncode == 0


def _parse_spec(spec: str, mode: str) -> tuple[str | None, str, str]:
    """Split ``spec`` into (base or None, head, effective operator)."""
    if mode not in _MODES:
        raise MalformedSpec(f"unknown mode: {mode!r}")
    text = spec.strip()
    if not text:
        raise MalformedSpec("empty range spec")
    if "..." in text:
        parts = text.split("...")
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            raise MalformedSpec(f"malformed three-dot spec: {spec!r}")
        return (parts[0].strip(), parts[1].strip(), "...")
    if ".." in text:
        parts = text.split("..")
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            raise MalformedSpec(f"malformed two-dot spec: {spec!r}")
        return (parts[0].strip(), parts[1].strip(), "..")
    pair = _SHA_PAIR_RE.fullmatch(text)
    if pair is not None:
        return (pair.group(1), pair.group(2), mode)
    if re.search(r"\s", text) is not None:
        raise MalformedSpec(f"malformed range spec: {spec!r}")
    return (None, text, mode)


def _resolve_base(repo_root: Path, base_given: str | None, head: str) -> tuple[str, ResolvedFrom]:
    if base_given is not None:
        if not _verify(repo_root, base_given):
            raise RangeRefusal(f"unresolvable ref: {base_given}")
        return (base_given, _EXPLICIT)
    for candidate in _BASE_CANDIDATES:
        if _verify(repo_root, candidate):
            return (candidate, candidate)
    raise RangeRefusal(f"unknown base: no origin/HEAD, origin/main or origin/master for {head}")


def _rev_list(repo_root: Path, revision_range: str) -> tuple[str, ...]:
    try:
        output = run_git(repo_root, "rev-list", "--reverse", revision_range)
    except RuntimeError as error:
        raise RangeRefusal(f"cannot list range {revision_range}: {error}") from error
    return tuple(line for line in output.splitlines() if line.strip())


def resolve_range(spec: str, mode: str) -> RangeResolution:
    """Resolve ``spec`` to commit SHAs using local git plumbing only."""
    base_given, head, effective = _parse_spec(spec, mode)
    try:
        repo_root = find_repo_root(Path.cwd())
    except RuntimeError as error:
        raise RangeRefusal(f"not a git repository: {error}") from error
    if not _verify(repo_root, head):
        raise RangeRefusal(f"unresolvable ref: {head}")
    base_ref, resolved_from = _resolve_base(repo_root, base_given, head)
    try:
        merge_base = run_git(repo_root, "merge-base", base_ref, head).strip().splitlines()[0]
    except (RuntimeError, IndexError) as error:
        raise RangeRefusal(f"no merge base for {base_ref} and {head}: {error}") from error
    if effective == "...":
        commits = _rev_list(repo_root, f"{merge_base}..{head}")
        only_in_base = _rev_list(repo_root, f"{merge_base}..{base_ref}")
    else:
        commits = _rev_list(repo_root, f"{base_ref}..{head}")
        only_in_base = _rev_list(repo_root, f"{head}..{base_ref}")
    return RangeResolution(
        mode=effective,
        base_ref=base_ref,
        head_ref=head,
        resolved_from=resolved_from,
        merge_base=merge_base,
        commits=commits,
        only_in_base=only_in_base,
        counts=RangeCounts(commits=len(commits), only_in_base=len(only_in_base)),
    )
