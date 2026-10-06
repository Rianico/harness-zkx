#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml"]
# ///
"""Brief payload for a commit interval (gh-router range surface).

Resolves SPEC through the shared range authority using local git plumbing only
(no network) and emits a versioned brief payload: range totals, per-commit rows
with full bodies, per-area rollups, file rows, and change signals.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import NotRequired, TypedDict

_BRIEF_LIB_DIR = str(Path(__file__).resolve().parents[3] / "lib")
if _BRIEF_LIB_DIR not in sys.path:
    sys.path.insert(0, _BRIEF_LIB_DIR)
from range_authority import (
    MalformedSpec,
    RangeRefusal,
    exit_code_for,
    find_repo_root,
    resolve_range,
    run_git,
)

_BRIEF_EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
_BRIEF_HELP_LINES = (
    "Usage: brief.py SPEC [PATH_FILTER] [options]",
    "Brief a commit interval through the shared range authority (local git only).",
    "  SPEC                 range spec, e.g. 'base...HEAD' or 'a1b2c3 d4e5f6' (--pr [SPEC] landing view, default HEAD)",
    "  PATH_FILTER          optional path prefix narrowing file and area rows",
    "  --mode ..|...        operator when SPEC carries none (default: ...)",
    "  --commit SHA          narrow commit rows to one member (--verify FINGERPRINT checks range fingerprint)",
    "  --file PATH           repeatable path narrowing file and area rows",
    "  --hunks              include unified hunks in text output (--context N)",
    "  --max-lines N        cap per capped block; remainder printed (default: 40)",
    "  --group-by KEY       area|category|status rollup for area rows (default: area)",
    "  --yaml | --json      structured payload instead of the text brief",
    "  --repo DIR           path inside the repository (default: .)",
    "  Exits 0 ok | 1 failure | 2 malformed spec | 3 unknown ref",
    "  -h | --help          show this brief help (works outside a repo)",
)

_CONVENTIONAL_RE = re.compile(r"^([A-Za-z]+)(?:\(([^()]*)\))?(!)?\s*:\s*\S")
_BRIEF_NUMBER_RE = re.compile(r"#(\d+)")
_BRIEF_SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
_BRIEF_BREAKING_RE = re.compile(r"^BREAKING[ -]CHANGE\s*:", re.IGNORECASE | re.MULTILINE)

_BRIEF_STATUS_WORDS = {
    "A": "added",
    "M": "modified",
    "D": "deleted",
    "R": "renamed",
    "C": "copied",
    "T": "type-changed",
    "U": "unmerged",
}

_BRIEF_SOURCE_EXTS = frozenset(
    {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".go",
        ".rs",
        ".java",
        ".rb",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".cs",
        ".swift",
        ".kt",
        ".mjs",
        ".cjs",
        ".sh",
    }
)
_BRIEF_CONFIG_NAMES = frozenset(
    {
        "makefile",
        "dockerfile",
        "package.json",
        "pyproject.toml",
        ".oxlintrc.json",
        "eslint.config.js",
    }
)
_BRIEF_CONFIG_EXTS = frozenset({".json", ".yml", ".yaml", ".toml", ".ini", ".cfg"})
_BRIEF_DEPS_NAMES = frozenset(
    {
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "cargo.toml",
        "cargo.lock",
        "go.mod",
        "go.sum",
        "pyproject.toml",
        "uv.lock",
        "gemfile",
        "gemfile.lock",
        "pom.xml",
        "build.gradle",
    }
)


class _BriefRefs(TypedDict):
    numbers: list[int]
    shas: list[str]


class _BriefAuthor(TypedDict):
    name: str
    email: str


class _BriefCommitCounts(TypedDict):
    files: int
    insertions: int
    deletions: int


class _BriefCommitFile(TypedDict):
    path: str
    status: str
    insertions: int
    deletions: int


class _BriefCommit(TypedDict):
    sha: str
    short: str
    subject: str
    type: str | None
    scope: str | None
    breaking: bool
    refs: _BriefRefs
    author: _BriefAuthor
    date: str
    body: str
    counts: _BriefCommitCounts
    files: list[_BriefCommitFile]


class _BriefArea(TypedDict):
    path: str
    files: int
    insertions: int
    deletions: int


class _BriefFile(TypedDict):
    path: str
    status: str
    insertions: int
    deletions: int
    commits: int
    category: str
    binary: bool
    renamed_from: str | None


class _BriefRangeCounts(TypedDict):
    commits: int
    files: int
    insertions: int
    deletions: int
    added: int
    modified: int
    renamed: int
    deleted: int


class _BriefRange(TypedDict):
    spec_in: str
    mode: str
    merge_base: str
    only_in_base: int
    resolved_from: str
    counts: _BriefRangeCounts
    fingerprint: str


class _BriefSignals(TypedDict):
    breaking: list[str]
    deps: list[str]
    changelog: bool
    renames: list[str]
    evidence_candidates: list[str]


class _BriefTruncated(TypedDict):
    files: int
    commits: int


class _BriefLanding(TypedDict):
    commits: int
    conventional: int
    multi_entry: bool


class _BriefVerification(TypedDict):
    expected: str
    actual: str
    ok: bool


class _BriefPayload(TypedDict):
    schema: int
    range: _BriefRange
    commits: list[_BriefCommit]
    areas: list[_BriefArea]
    files: list[_BriefFile]
    signals: _BriefSignals
    truncated: _BriefTruncated
    landing: NotRequired[_BriefLanding]
    verification: NotRequired[_BriefVerification]


class _BriefNumstatRow(TypedDict):
    insertions: int
    deletions: int
    binary: bool


class _BriefStatusRow(TypedDict):
    status: str
    old: str
    new: str


@dataclass(frozen=True)
class _BriefArgs:
    spec: str | None
    path_filter: str | None
    mode: str
    repo: str
    commit: str | None
    file: list[str]
    hunks: bool
    context: int
    max_lines: int
    group_by: str
    brief_yaml: bool
    brief_json: bool
    brief_help: bool
    pr: str | None
    verify: str | None


def _parse_brief_conventional(subject: str) -> tuple[str | None, str | None, bool]:
    """Split a subject into (type, scope, explicit-bang) per the team convention."""
    match = _CONVENTIONAL_RE.match(subject.strip())
    if match is None:
        return (None, None, False)
    kind, scope, bang = match.group(1).lower(), match.group(2), match.group(3)
    return (kind, scope if scope else None, bang == "!")


def _find_brief_refs(*texts: str) -> _BriefRefs:
    """Collect #N numbers and hex shas in first-seen order, deduplicated."""
    numbers = sorted({int(found) for text in texts for found in _BRIEF_NUMBER_RE.findall(text)})
    shas: list[str] = []
    for text in texts:
        for found in _BRIEF_SHA_RE.findall(text):
            if found not in shas:
                shas.append(found)
    return {"numbers": numbers, "shas": shas}


def _categorize_brief_path(path: str) -> str:
    """Bucket a repo path for the category rollup and the test-line share."""
    lowered = path.lower()
    parts = lowered.split("/")
    name = parts[-1]
    _, dot, ext = name.rpartition(".")
    if (
        "tests" in parts
        or "test" in parts
        or "__tests__" in parts
        or name.startswith("test_")
        or ".test." in name
        or ".spec." in name
        or name.endswith("_test" + (dot + ext if dot else ""))
    ):
        return "test"
    if ext in (".md", ".rst", ".txt") or name in ("changelog.md", "changes.md", "license"):
        return "docs"
    if "github" in parts and "workflows" in parts:
        return "config"
    if name in _BRIEF_CONFIG_NAMES or (dot and (dot + ext) in _BRIEF_CONFIG_EXTS):
        return "config"
    if dot and (dot + ext) in _BRIEF_SOURCE_EXTS:
        return "source"
    if name in ("makefile", "dockerfile") or ext in (".css", ".scss", ".less"):
        return "build"
    return "other"


def _is_brief_deps_path(path: str) -> bool:
    name = path.lower().rsplit("/", 1)[-1]
    return name in _BRIEF_DEPS_NAMES or name.startswith("requirements")


def _is_brief_changelog_path(path: str) -> bool:
    return path.lower().rsplit("/", 1)[-1] == "changelog.md"


def _is_brief_evidence_path(path: str) -> bool:
    lowered = f"/{path.lower()}/"
    return _categorize_brief_path(path) == "test" or "/.github/" in lowered


def _parse_brief_numstat(output: str) -> list[_BriefNumstatRow]:
    rows: list[_BriefNumstatRow] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        cells = line.split("\t")
        if len(cells) < 3:
            continue
        if cells[0] == "-" and cells[1] == "-":
            rows.append({"insertions": 0, "deletions": 0, "binary": True})
            continue
        try:
            rows.append({"insertions": int(cells[0]), "deletions": int(cells[1]), "binary": False})
        except ValueError:
            continue
    return rows


def _parse_brief_name_status(output: str) -> list[_BriefStatusRow]:
    rows: list[_BriefStatusRow] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        cells = line.split("\t")
        letter = cells[0][:1]
        if letter == "R" and len(cells) >= 3:
            rows.append({"status": letter, "old": cells[1], "new": cells[2]})
        elif len(cells) >= 2:
            rows.append({"status": letter, "old": cells[1], "new": cells[1]})
    return rows


def _read_brief_diff(
    repo_root: Path, old: str, new: str
) -> tuple[list[_BriefNumstatRow], list[_BriefStatusRow]]:
    """Read one local diff in paired numstat + name-status form (index-aligned)."""
    numstat = _parse_brief_numstat(run_git(repo_root, "diff", "--numstat", "-M", old, new, "--"))
    statuses = _parse_brief_name_status(
        run_git(repo_root, "diff", "--name-status", "-M", old, new, "--")
    )
    if len(numstat) != len(statuses):
        raise RuntimeError(f"unpaired diff rows for {old}..{new}")
    return (numstat, statuses)


def _read_brief_commit(repo_root: Path, sha: str) -> _BriefCommit:
    """Read one commit: full meta, conventional kind, refs, and its own file rows."""
    raw = run_git(
        repo_root,
        "log",
        "-1",
        "--date=iso-strict",
        "--format=%H%x00%h%x00%an%x00%ae%x00%ad%x00%s%x00%b%x00%P",
        sha,
    ).rstrip("\n")
    cells = raw.split("\x00")
    if len(cells) != 8:
        raise RuntimeError(f"unparseable commit meta for {sha}")
    full, short, name, email, date, subject, body, parents_raw = cells
    kind, scope, bang = _parse_brief_conventional(subject)
    breaking = bang or _BRIEF_BREAKING_RE.search(body) is not None
    parents = parents_raw.split()
    old = parents[0] if parents else _BRIEF_EMPTY_TREE
    numstat, statuses = _read_brief_diff(repo_root, old, full)
    files: list[_BriefCommitFile] = []
    insertions = 0
    deletions = 0
    for numbers, status_row in zip(numstat, statuses, strict=True):
        word = _BRIEF_STATUS_WORDS.get(status_row["status"], "unknown")
        files.append(
            {
                "path": status_row["new"],
                "status": word,
                "insertions": numbers["insertions"],
                "deletions": numbers["deletions"],
            }
        )
        insertions += numbers["insertions"]
        deletions += numbers["deletions"]
    return {
        "sha": full,
        "short": short,
        "subject": subject,
        "type": kind,
        "scope": scope,
        "breaking": breaking,
        "refs": _find_brief_refs(subject, body),
        "author": {"name": name, "email": email},
        "date": date,
        "body": body.strip(),
        "counts": {"files": len(files), "insertions": insertions, "deletions": deletions},
        "files": files,
    }


def _fingerprint_brief_payload(spec_in: str, mode: str, merge_base: str, shas: list[str]) -> str:
    """Stable range identity over (spec, mode, merge base, ordered commit shas)."""
    material = "\n".join([spec_in, mode, merge_base, *shas])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _match_brief_path(path: str, wanted: str) -> bool:
    """Exact file match or subtree-prefix match for file narrowing."""
    cleaned = wanted.strip().lstrip("./")
    return path == cleaned or path.startswith(cleaned.rstrip("/") + "/")


def _group_brief_key(path: str, status: str, group_by: str) -> str:
    if group_by == "category":
        return _categorize_brief_path(path)
    if group_by == "status":
        return status
    return path.split("/", 1)[0] if "/" in path else "(root)"


def _build_brief(
    spec_in: str,
    mode: str,
    repo_root: Path,
    path_filter: str | None,
    commit_filter: str | None,
    file_filter: list[str],
    group_by: str,
    max_lines: int,
    want_landing: bool = False,
) -> tuple[_BriefPayload, str, str]:
    """Assemble the payload; also returns the (old, new) diff endpoints."""
    resolution = resolve_range(spec_in, mode)
    wanted = [path_filter] if path_filter else []
    wanted.extend(file_filter)
    commits = [_read_brief_commit(repo_root, sha) for sha in resolution.commits]
    full_commits = list(commits)
    if commit_filter is not None:
        wanted_commit = commit_filter.lower()
        if not re.fullmatch(r"[0-9a-f]{4,40}", wanted_commit):
            raise RangeRefusal(
                "commit must be a full or short sha "
                f"(4-40 hex chars), not a revspec: {commit_filter}"
            )
        commits = [
            entry
            for entry in commits
            if entry["sha"].lower() == wanted_commit
            or entry["sha"].lower().startswith(wanted_commit)
        ]
        if len(commits) > 1:
            shorts = ", ".join(entry["short"] for entry in commits)
            raise RangeRefusal(
                f"ambiguous commit prefix: {commit_filter} matches {shorts}; use a longer prefix"
            )
        if not commits:
            raise RangeRefusal(f"commit not in range: {commit_filter}")
    if resolution.mode == "...":
        old_endpoint, new_endpoint = resolution.merge_base, resolution.head_ref
    else:
        old_endpoint, new_endpoint = resolution.base_ref, resolution.head_ref
    numstat, statuses = _read_brief_diff(repo_root, old_endpoint, new_endpoint)
    per_commit = Counter[str]()
    for entry in (_read_brief_commit(repo_root, sha) for sha in resolution.commits):
        for row in entry["files"]:
            per_commit[row["path"]] += 1
    full_files: list[_BriefFile] = []
    for numbers, status_row in zip(numstat, statuses, strict=True):
        word = _BRIEF_STATUS_WORDS.get(status_row["status"], "unknown")
        full_files.append(
            {
                "path": status_row["new"],
                "status": word,
                "insertions": numbers["insertions"],
                "deletions": numbers["deletions"],
                "commits": per_commit.get(status_row["new"], 0),
                "category": _categorize_brief_path(status_row["new"]),
                "binary": numbers["binary"],
                "renamed_from": status_row["old"] if word == "renamed" else None,
            }
        )
    view_files = [
        row
        for row in full_files
        if not wanted or any(_match_brief_path(row["path"], w) for w in wanted)
    ]
    area_totals: dict[str, _BriefArea] = {}
    for row in view_files:
        key = _group_brief_key(row["path"], row["status"], group_by)
        bucket = area_totals.setdefault(
            key, {"path": key, "files": 0, "insertions": 0, "deletions": 0}
        )
        bucket["files"] += 1
        bucket["insertions"] += row["insertions"]
        bucket["deletions"] += row["deletions"]
    areas = sorted(
        area_totals.values(),
        key=lambda b: (b["insertions"] + b["deletions"], b["path"]),
        reverse=True,
    )
    counts: _BriefRangeCounts = {
        "commits": len(resolution.commits),
        "files": len(view_files),
        "insertions": sum(r["insertions"] for r in view_files),
        "deletions": sum(r["deletions"] for r in view_files),
        "added": sum(1 for r in view_files if r["status"] == "added"),
        "modified": sum(1 for r in view_files if r["status"] == "modified"),
        "renamed": sum(1 for r in view_files if r["status"] == "renamed"),
        "deleted": sum(1 for r in view_files if r["status"] == "deleted"),
    }
    shown_commits = commits[:max_lines]
    shown_files = view_files[:max_lines]
    payload: _BriefPayload = {
        "schema": 1,
        "range": {
            "spec_in": spec_in,
            "mode": resolution.mode,
            "merge_base": resolution.merge_base,
            "only_in_base": len(resolution.only_in_base),
            "resolved_from": resolution.resolved_from,
            "counts": counts,
            "fingerprint": _fingerprint_brief_payload(
                spec_in, resolution.mode, resolution.merge_base, list(resolution.commits)
            ),
        },
        "commits": shown_commits,
        "areas": areas,
        "files": shown_files,
        "signals": {
            "breaking": [e["short"] for e in commits if e["breaking"]],
            "deps": sorted({r["path"] for r in full_files if _is_brief_deps_path(r["path"])}),
            "changelog": any(_is_brief_changelog_path(r["path"]) for r in full_files),
            "renames": sorted(r["path"] for r in full_files if r["status"] == "renamed"),
            "evidence_candidates": sorted(
                {r["path"] for r in full_files if _is_brief_evidence_path(r["path"])}
            ),
        },
        "truncated": {
            "files": len(view_files) - len(shown_files),
            "commits": len(commits) - len(shown_commits),
        },
    }
    if want_landing:
        conventional = sum(1 for entry in full_commits if entry["type"] is not None)
        total = len(full_commits)
        payload["landing"] = {
            "commits": total,
            "conventional": conventional,
            "multi_entry": conventional > 1,
        }
    return (payload, old_endpoint, new_endpoint)


def build_brief_payload(
    spec_in: str,
    mode: str,
    repo_root: Path,
    path_filter: str | None = None,
    commit_filter: str | None = None,
    file_filter: list[str] | None = None,
    group_by: str = "area",
    max_lines: int = 40,
) -> _BriefPayload:
    """Public seam: the versioned brief payload for SPEC resolved with MODE."""
    payload, _, _ = _build_brief(
        spec_in, mode, repo_root, path_filter, commit_filter, file_filter or [], group_by, max_lines
    )
    return payload


def _rerun_brief_command(spec_in: str, mode: str, extra: str) -> str:
    script = Path(__file__).resolve()
    return f"uv run {script} '{spec_in}' --mode {mode}{extra}"


def render_brief_text(
    payload: _BriefPayload,
    hunks: dict[str, list[str]] | None = None,
    max_lines: int = 40,
) -> str:
    """Render the default text brief: precomputed overview plus capped rows."""
    block = payload["range"]
    counts = block["counts"]
    lines = [
        (
            f"brief '{block['spec_in']}' ({block['mode']}): "
            f"{counts['commits']} commits, {counts['files']} files "
            f"(+{counts['insertions']}/-{counts['deletions']})"
        ),
        (
            f"base via {block['resolved_from']} merge-base {block['merge_base'][:12]} "
            f"only-in-base {block['only_in_base']} fingerprint {block['fingerprint'][:12]}"
        ),
    ]
    full_commits = payload["commits"]
    kinds = Counter(e["type"] or "other" for e in full_commits)
    authors = sorted({e["author"]["name"] for e in full_commits})
    dates = sorted(e["date"] for e in full_commits)
    span = f"{dates[0]}..{dates[-1]}" if dates else "no commits"
    lines.append(
        "overview: "
        + ", ".join(f"{k} x{v}" for k, v in sorted(kinds.items()))
        + f" | authors {len(authors)} | span {span}"
    )
    lines.append(
        f"files: added {counts['added']} modified {counts['modified']} "
        f"renamed {counts['renamed']} deleted {counts['deleted']}"
    )
    test_ins = sum(f["insertions"] for f in payload["files"] if f["category"] == "test")
    total_ins = counts["insertions"]
    share = f"{(100 * test_ins // total_ins)}%" if total_ins else "n/a"
    churn = sorted(
        payload["files"], key=lambda r: (r["insertions"] + r["deletions"], r["path"]), reverse=True
    )[:5]
    lines.append(
        f"test-line share {share} | churn: "
        + (
            ", ".join(f"{r['path']} (+{r['insertions']}/-{r['deletions']})" for r in churn)
            or "none"
        )
    )
    lines.append("areas:")
    for area in payload["areas"]:
        lines.append(
            f"  {area['path']}: {area['files']} files (+{area['insertions']}/-{area['deletions']})"
        )
    lines.append("commits:")
    for entry in full_commits:
        label = entry["type"] or "other"
        if entry["scope"]:
            label += f"({entry['scope']})"
        if entry["breaking"]:
            label += "!"
        lines.append(
            f"  {entry['short']} [{label}] {entry['subject']} "
            f"— {entry['author']['name']} {entry['date']} "
            f"({entry['counts']['files']} files "
            f"+{entry['counts']['insertions']}/-{entry['counts']['deletions']})"
        )
        if entry["body"]:
            lines.extend(f"    {body_line}" for body_line in entry["body"].splitlines())
        refs = entry["refs"]
        if refs["numbers"] or refs["shas"]:
            lines.append("    refs: " + " ".join([f"#{n}" for n in refs["numbers"]] + refs["shas"]))
    omitted_commits = payload["truncated"]["commits"]
    if omitted_commits:
        lines.append(
            f"  ... ({omitted_commits} more commits omitted; rerun: "
            + _rerun_brief_command(
                block["spec_in"], block["mode"], f" --max-lines {max_lines + omitted_commits}"
            )
            + ")"
        )
    lines.append("files:")
    for row in payload["files"]:
        lines.append(
            f"  {row['status']} {row['path']} "
            f"(+{row['insertions']}/-{row['deletions']}, in {row['commits']} commits)"
        )
        for hunk_line in (hunks or {}).get(row["path"], []):
            lines.append(f"    {hunk_line}")
    omitted_files = payload["truncated"]["files"]
    if omitted_files:
        lines.append(
            f"  ... ({omitted_files} more files omitted; rerun: "
            + _rerun_brief_command(
                block["spec_in"], block["mode"], f" --max-lines {max_lines + omitted_files}"
            )
            + ")"
        )
    signals = payload["signals"]
    lines.append(
        "signals: breaking ["
        + ", ".join(signals["breaking"])
        + "] deps ["
        + ", ".join(signals["deps"])
        + "] changelog "
        + ("yes" if signals["changelog"] else "no")
        + " renames ["
        + ", ".join(signals["renames"])
        + "] evidence ["
        + ", ".join(signals["evidence_candidates"])
        + "]"
    )
    landing = payload.get("landing")
    if landing is not None:
        multi = "yes" if landing["multi_entry"] else "no"
        lines.append(
            f"landing: commits {landing['commits']} "
            f"conventional {landing['conventional']} multi-entry {multi}"
        )
    return "\n".join(lines)


def _read_brief_hunks(
    repo_root: Path, old: str, new: str, paths: list[str], context: int, max_lines: int
) -> dict[str, list[str]]:
    """Read unified hunks per path, capped with an in-text remainder marker."""
    hunks: dict[str, list[str]] = {}
    for path in paths:
        try:
            output = run_git(repo_root, "diff", f"-U{context}", old, new, "--", path)
        except RuntimeError:
            continue
        kept = output.splitlines()[:max_lines]
        if len(output.splitlines()) > max_lines:
            kept.append(f"... (hunk output capped at {max_lines} lines)")
        hunks[path] = kept
    return hunks


def _resolve_pr_spec(spec: str | None, pr: str) -> str:
    """Resolve the pr range spec from positional SPEC and the --pr value."""
    if pr != "HEAD":
        if spec is not None:
            raise MalformedSpec("--pr SPEC and positional SPEC are exclusive")
        return pr
    if spec is not None:
        return spec
    return "HEAD"


def _is_brief_fingerprint(value: str) -> bool:
    """Check the expected fingerprint shape (64 hex chars)."""
    return re.fullmatch(r"[0-9a-fA-F]{64}", value.strip()) is not None


def render_verify_hit_text(payload: _BriefPayload) -> str:
    """Render the verify hit readout with fingerprint and base provenance."""
    block = payload["range"]
    return (
        f"brief '{block['spec_in']}' ({block['mode']}): verified fingerprint "
        f"{block['fingerprint']} via {block['resolved_from']} "
        f"merge-base {block['merge_base'][:12]} only-in-base {block['only_in_base']}"
    )


def build_verify_mismatch_error(
    spec_in: str, expected: str, payload: _BriefPayload
) -> RangeRefusal:
    """Name the moved field set when the recomputed fingerprint differs."""
    block = payload["range"]
    actual = block["fingerprint"]
    return RangeRefusal(
        f"fingerprint mismatch for '{spec_in}': expected {expected} got {actual} "
        f"(spec '{block['spec_in']}' mode {block['mode']} "
        f"merge_base {block['merge_base']} via {block['resolved_from']} "
        f"commits {block['counts']['commits']}); "
        "the range moved since this fingerprint was taken \u2014 compare spec, "
        "mode, merge_base and commit count above against the recorded digest"
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="brief.py", add_help=False)
    _ = parser.add_argument("spec", nargs="?", default=None)
    _ = parser.add_argument("path_filter", nargs="?", default=None)
    _ = parser.add_argument("--mode", default="...")
    _ = parser.add_argument("--repo", default=".")
    _ = parser.add_argument("--commit", default=None)
    _ = parser.add_argument("--file", action="append", default=[])
    _ = parser.add_argument("--hunks", action="store_true")
    _ = parser.add_argument("--context", type=int, default=3)
    _ = parser.add_argument("--max-lines", type=int, default=40)
    _ = parser.add_argument("--group-by", default="area")
    _ = parser.add_argument("--yaml", dest="brief_yaml", action="store_true")
    _ = parser.add_argument("--json", dest="brief_json", action="store_true")
    _ = parser.add_argument("--pr", nargs="?", const="HEAD", default=None)
    _ = parser.add_argument("--verify", default=None)
    _ = parser.add_argument("-h", "--help", dest="brief_help", action="store_true")
    ns = parser.parse_args()
    args = _BriefArgs(
        spec=str(ns.spec) if ns.spec is not None else None,
        path_filter=str(ns.path_filter) if ns.path_filter is not None else None,
        mode=str(ns.mode),
        repo=str(ns.repo),
        commit=str(ns.commit) if ns.commit is not None else None,
        file=[str(item) for item in ns.file],
        hunks=bool(ns.hunks),
        context=int(ns.context),
        max_lines=int(ns.max_lines),
        group_by=str(ns.group_by),
        brief_yaml=bool(ns.brief_yaml),
        brief_json=bool(ns.brief_json),
        brief_help=bool(ns.brief_help),
        pr=str(ns.pr) if ns.pr is not None else None,
        verify=str(ns.verify) if ns.verify is not None else None,
    )
    if args.brief_help:
        print("\n".join(_BRIEF_HELP_LINES))
        return 0
    if args.pr is not None and args.verify is not None:
        parser.error("--pr and --verify are exclusive")
    if args.brief_yaml and args.brief_json:
        parser.error("--yaml and --json are exclusive")
    if args.max_lines <= 0:
        parser.error("--max-lines must be positive")
    if args.context < 0:
        parser.error("--context must be non-negative")
    if args.mode not in ("..", "..."):
        parser.error("--mode must be .. or ...")
    if args.group_by not in ("area", "category", "status"):
        parser.error("--group-by must be area, category, or status")
    pr_spec = ""
    if args.pr is not None:
        if args.path_filter is not None and args.pr != "HEAD":
            parser.error("--pr SPEC takes no positional PATH_FILTER; use --file")
    elif args.verify is not None:
        if not args.spec:
            parser.error("SPEC is required")
        if not _is_brief_fingerprint(args.verify):
            parser.error("--verify needs a 64-char fingerprint")
    else:
        if not args.spec:
            parser.error("SPEC is required")
    try:
        repo_root = find_repo_root(Path(args.repo).resolve())
        os.chdir(repo_root)
        if args.pr is not None:
            assert args.pr is not None
            pr_spec = _resolve_pr_spec(args.spec, args.pr)
            payload, old_endpoint, new_endpoint = _build_brief(
                pr_spec,
                args.mode,
                repo_root,
                args.path_filter,
                args.commit,
                args.file,
                args.group_by,
                args.max_lines,
                True,
            )
            if payload["range"]["counts"]["commits"] == 0:
                only = payload["range"]["only_in_base"]
                if only == 0:
                    raise RangeRefusal(
                        "head is at or behind its base; nothing to land "
                        f"— rebase or check the base (only-in-base {only})"
                    )
                raise RangeRefusal(
                    "head is behind its base; nothing to land "
                    f"— rebase or check the base (only-in-base {only})"
                )
        elif args.verify is not None:
            assert args.spec is not None
            payload, old_endpoint, new_endpoint = _build_brief(
                args.spec,
                args.mode,
                repo_root,
                args.path_filter,
                args.commit,
                args.file,
                args.group_by,
                args.max_lines,
            )
            actual = payload["range"]["fingerprint"]
            expected = args.verify.strip().lower()
            if actual.lower() != expected:
                raise build_verify_mismatch_error(args.spec, expected, payload)
            payload["verification"] = {
                "expected": expected,
                "actual": actual,
                "ok": True,
            }
            if args.brief_json:
                print(json.dumps(payload, indent=2))
                return 0
            if args.brief_yaml:
                try:
                    import yaml
                except ImportError:
                    print(
                        "brief: structured YAML needs the pyyaml dependency",
                        file=sys.stderr,
                    )
                    return 1
                print(yaml.safe_dump(payload, sort_keys=False), end="")
                return 0
            print(render_verify_hit_text(payload))
            return 0
        else:
            assert args.spec is not None
            payload, old_endpoint, new_endpoint = _build_brief(
                args.spec,
                args.mode,
                repo_root,
                args.path_filter,
                args.commit,
                args.file,
                args.group_by,
                args.max_lines,
            )
    except (MalformedSpec, RangeRefusal) as error:
        print(f"brief: {error}", file=sys.stderr)
        return exit_code_for(error)
    except Exception as error:
        print(f"brief: unexpected failure: {error}", file=sys.stderr)
        return 1
    if args.brief_json:
        print(json.dumps(payload, indent=2))
        return 0
    if args.brief_yaml:
        try:
            import yaml
        except ImportError:
            print("brief: structured YAML needs the pyyaml dependency", file=sys.stderr)
            return 1
        print(yaml.safe_dump(payload, sort_keys=False), end="")
        return 0
    hunks: dict[str, list[str]] | None = None
    if args.hunks:
        if args.commit and payload["commits"]:
            hunk_paths = [row["path"] for row in payload["commits"][0]["files"]]
        else:
            hunk_paths = [row["path"] for row in payload["files"]]
        hunks = _read_brief_hunks(
            repo_root, old_endpoint, new_endpoint, hunk_paths, args.context, args.max_lines
        )
    print(render_brief_text(payload, hunks, args.max_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
