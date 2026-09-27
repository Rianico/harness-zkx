#!/usr/bin/env python3
"""Summarize and extract compact merge-conflict context from a Git repository."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NotRequired, Protocol, TypedDict, cast

START_RE = re.compile(r"^<<<<<<<(?: (.*))?$")
BASE_RE = re.compile(r"^\|\|\|\|\|\|\|(?: (.*))?$")
END_RE = re.compile(r"^>>>>>>>(?: (.*))?$")


class _Hunk(TypedDict):
    start_line: int
    end_line: int
    before_context: list[str]
    ours: list[str]
    ours_label: str
    base: list[str] | None
    base_label: str | None
    theirs: list[str]
    theirs_label: str
    after_context: list[str]


class _CommitIntent(TypedDict):
    ref: str
    sha: str
    author: str
    date: str
    subject: str
    body: str


class _AuthorIntent(TypedDict):
    ours: _CommitIntent | None
    theirs: _CommitIntent | None


class _Report(TypedDict):
    path: str
    stages: list[int]
    conflict_type: str
    marker_hunks: int
    parse_error: str | None
    worktree_present: bool
    operation: str | None
    author_intent: _AuthorIntent | None
    hunks: list[_Hunk]


class _IndexPreview(TypedDict):
    ours: list[str] | None
    theirs: list[str] | None
    base: list[str] | None
    ours_vs_theirs_diff: NotRequired[list[str]]


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


def detect_git_operation(repo_root: Path) -> tuple[str, str | None, str | None]:
    """Detect git operation in progress and return (operation, ours_ref, theirs_ref)."""
    for op, theirs in [
        ("rebase", "REBASE_HEAD"),
        ("merge", "MERGE_HEAD"),
        ("cherry-pick", "CHERRY_PICK_HEAD"),
        ("revert", "REVERT_HEAD"),
    ]:
        res = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--verify", "-q", theirs],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return (op, "HEAD", theirs)

    # Check git directories for rebase in progress if REBASE_HEAD was not verified as a ref
    for dir_name in ("rebase-merge", "rebase-apply"):
        git_path_res = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--git-path", dir_name],
            capture_output=True,
            text=True,
            check=False,
        )
        if git_path_res.returncode == 0:
            raw_path = git_path_res.stdout.strip()
            if raw_path:
                p = Path(raw_path)
                target = p if p.is_absolute() else (repo_root / p)
                if target.is_dir():
                    return ("rebase", "HEAD", "REBASE_HEAD")

    return ("unknown", None, None)


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


def format_operation_description(
    op: str,
    _ours_ref: str | None,
    _theirs_ref: str | None,
    ours_sha: str | None,
    theirs_sha: str | None,
) -> str | None:
    if op == "unknown" or not op:
        return None
    if op == "rebase":
        if theirs_sha and ours_sha:
            return f"rebase (replaying {theirs_sha} onto {ours_sha})"
        return "rebase"
    if op == "merge":
        if theirs_sha and ours_sha:
            return f"merge (merging {theirs_sha} into {ours_sha})"
        return "merge"
    if op == "cherry-pick":
        if theirs_sha and ours_sha:
            return f"cherry-pick (applying {theirs_sha} onto {ours_sha})"
        return "cherry-pick"
    if op == "revert":
        if theirs_sha and ours_sha:
            return f"revert (reverting {theirs_sha} onto {ours_sha})"
        return "revert"
    return op


def get_unmerged_entries(repo_root: Path) -> dict[str, dict[int, dict[str, str]]]:
    entries: dict[str, dict[int, dict[str, str]]] = {}
    output = run_git(repo_root, "ls-files", "-u", "-z")
    for record in output.split("\0"):
        if not record:
            continue
        metadata, path = record.split("\t", 1)
        mode, object_id, stage_text = metadata.split()
        file_entry = entries.setdefault(path, {})
        file_entry[int(stage_text)] = {"mode": mode, "object_id": object_id}
    return entries


def read_text_file(path: Path) -> list[str] | None:
    if not path.exists() or path.is_dir():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if "\x00" in text:
        return None
    return text.splitlines()


def read_stage_text(repo_root: Path, path: str, stage: int) -> list[str] | None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f":{stage}:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    if "\x00" in result.stdout:
        return None
    return result.stdout.splitlines()


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


def classify_conflict(stages: list[int], marker_hunks: int) -> str:
    if marker_hunks:
        return "text"
    stage_set = set(stages)
    if stage_set == {2, 3}:
        return "add/add"
    if stage_set == {1, 2}:
        return "deleted-by-them"
    if stage_set == {1, 3}:
        return "deleted-by-us"
    if stage_set == {1, 2, 3}:
        return "index-only"
    return "unmerged"


def normalize_requested_path(repo_root: Path, raw_path: str) -> str:
    path = Path(raw_path)
    candidate = path.resolve() if path.is_absolute() else (repo_root / path).resolve()
    try:
        return str(candidate.relative_to(repo_root))
    except ValueError as error:
        raise RuntimeError(f"path is outside repository: {raw_path}") from error


def parse_conflict_hunks(lines: list[str], context: int) -> tuple[list[_Hunk], str | None]:
    hunks: list[_Hunk] = []
    index = 0
    while index < len(lines):
        start_match = START_RE.match(lines[index])
        if not start_match:
            index += 1
            continue

        start_index = index
        ours_label = start_match.group(1) or "ours"
        index += 1
        ours: list[str] = []
        base: list[str] = []
        theirs: list[str] = []
        base_label: str | None = None
        theirs_label = "theirs"

        while index < len(lines):
            base_match = BASE_RE.match(lines[index])
            if base_match:
                base_label = base_match.group(1) or "base"
                index += 1
                while index < len(lines) and lines[index] != "=======":
                    base.append(lines[index])
                    index += 1
                break
            if lines[index] == "=======":
                break
            ours.append(lines[index])
            index += 1

        if index >= len(lines) or lines[index] != "=======":
            return hunks, f"unterminated conflict starting at line {start_index + 1}"

        index += 1
        end_index = index
        while index < len(lines):
            end_match = END_RE.match(lines[index])
            if end_match:
                theirs_label = end_match.group(1) or "theirs"
                end_index = index
                index += 1
                break
            theirs.append(lines[index])
            index += 1
        else:
            return hunks, f"unterminated conflict starting at line {start_index + 1}"

        hunks.append(
            {
                "start_line": start_index + 1,
                "end_line": end_index + 1,
                "before_context": lines[max(0, start_index - context) : start_index],
                "ours": ours,
                "ours_label": ours_label,
                "base": base or None,
                "base_label": base_label,
                "theirs": theirs,
                "theirs_label": theirs_label,
                "after_context": lines[index : index + context],
            }
        )

    return hunks, None


def build_summary_report(
    repo_root: Path,
    path: str,
    stage_entries: dict[int, dict[str, str]],
    context: int,
    operation_info: tuple[str, str | None, str | None] | None = None,
) -> _Report:
    worktree_lines = read_text_file(repo_root / path)
    hunks: list[_Hunk] = []
    parse_error = None
    if worktree_lines is not None:
        hunks, parse_error = parse_conflict_hunks(worktree_lines, context)
    stages = sorted(stage_entries)

    op, ours_ref, theirs_ref = operation_info or detect_git_operation(repo_root)
    ours_commit = get_commit_summary(repo_root, ours_ref, path) if ours_ref else None
    theirs_commit = get_commit_summary(repo_root, theirs_ref, path) if theirs_ref else None

    ours_intent: _CommitIntent | None = None
    if ours_commit and ours_ref:
        ours_intent = {
            "ref": ours_ref,
            "sha": ours_commit["sha"],
            "author": ours_commit["author"],
            "date": ours_commit["date"],
            "subject": ours_commit["subject"],
            "body": ours_commit["body"],
        }

    theirs_intent: _CommitIntent | None = None
    if theirs_commit and theirs_ref:
        theirs_intent = {
            "ref": theirs_ref,
            "sha": theirs_commit["sha"],
            "author": theirs_commit["author"],
            "date": theirs_commit["date"],
            "subject": theirs_commit["subject"],
            "body": theirs_commit["body"],
        }

    author_intent: _AuthorIntent | None = None
    if ours_intent is not None or theirs_intent is not None:
        author_intent = {"ours": ours_intent, "theirs": theirs_intent}

    ours_sha = ours_intent["sha"] if ours_intent else None
    theirs_sha = theirs_intent["sha"] if theirs_intent else None
    operation_desc = format_operation_description(op, ours_ref, theirs_ref, ours_sha, theirs_sha)

    return {
        "path": path,
        "stages": stages,
        "conflict_type": classify_conflict(stages, len(hunks)),
        "marker_hunks": len(hunks),
        "parse_error": parse_error,
        "worktree_present": worktree_lines is not None,
        "operation": operation_desc,
        "author_intent": author_intent,
        "hunks": hunks,
    }


def build_index_preview(repo_root: Path, report: _Report, max_lines: int) -> _IndexPreview:
    path = str(report["path"])
    ours = read_stage_text(repo_root, path, 2)
    theirs = read_stage_text(repo_root, path, 3)
    base = read_stage_text(repo_root, path, 1)
    preview: _IndexPreview = {
        "ours": truncate_lines(ours, max_lines) if ours else None,
        "theirs": truncate_lines(theirs, max_lines) if theirs else None,
        "base": truncate_lines(base, max_lines) if base else None,
    }
    if ours and theirs:
        preview["ours_vs_theirs_diff"] = build_diff(ours, theirs, "ours", "theirs", max_lines)
    return preview


def section_lines(title: str, lines: list[str] | None) -> list[str]:
    if lines is None:
        return [f"{title}:", "  (not present)"]
    if not lines:
        return [f"{title}:", "  (empty)"]
    return [f"{title}:", *[f"  {line}" for line in lines]]


def render_summary_text(repo_root: Path, reports: list[_Report]) -> str:
    lines = [f"repo: {repo_root}", f"conflicted files: {len(reports)}"]
    for report in reports:
        stages = ",".join(str(stage) for stage in report["stages"])
        lines.append(
            f"- {report['path']} | type={report['conflict_type']} | stages={stages} | hunks={report['marker_hunks']}"
        )
        if report["parse_error"]:
            lines.append(f"  parse-error: {report['parse_error']}")
    lines.append("use --file <path> for compact hunk details or --all for every file")
    return "\n".join(lines)


def render_detail_text(
    repo_root: Path,
    report: _Report,
    max_lines: int,
) -> str:
    lines = [
        f"== {report['path']} ==",
        f"type: {report['conflict_type']}",
    ]
    if report["operation"]:
        lines.append(f"operation: {report['operation']}")
    if report["author_intent"]:
        intent = report["author_intent"]
        if intent["ours"] or intent["theirs"]:
            lines.append("author intent:")
            for side in ("ours", "theirs"):
                commit = intent[side]
                if commit:
                    ref_label = commit["ref"]
                    lines.append(
                        f"  {side} ({ref_label}): [{commit['sha']}] by {commit['author']}, {commit['date']}"
                    )
                    lines.append(f"    subject: {commit['subject']}")
                    if commit["body"]:
                        lines.append(f"    body: {commit['body']}")
    lines.append(f"stages: {', '.join(str(stage) for stage in report['stages'])}")
    parse_error = report["parse_error"]
    if parse_error:
        lines.append(f"parse-error: {parse_error}")

    hunks = report["hunks"]
    if hunks:
        lines.append(f"hunks: {len(hunks)}")
        for index, hunk in enumerate(hunks, start=1):
            ours = list(hunk["ours"])
            theirs = list(hunk["theirs"])
            diff = build_diff(
                ours,
                theirs,
                str(hunk["ours_label"]),
                str(hunk["theirs_label"]),
                max_lines,
            )
            lines.extend(
                [
                    "",
                    f"[hunk {index}] current lines {hunk['start_line']}-{hunk['end_line']}",
                    *section_lines(
                        "before", truncate_lines(list(hunk["before_context"]), max_lines)
                    ),
                    *section_lines(
                        f"ours ({hunk['ours_label']})",
                        truncate_lines(ours, max_lines),
                    ),
                ]
            )
            if hunk["base"] is not None:
                lines.extend(
                    section_lines(
                        f"base ({hunk['base_label'] or 'base'})",
                        truncate_lines(list(hunk["base"]), max_lines),
                    )
                )
            lines.extend(
                [
                    *section_lines(
                        f"theirs ({hunk['theirs_label']})",
                        truncate_lines(theirs, max_lines),
                    ),
                    *section_lines("ours vs theirs diff", diff),
                    *section_lines("after", truncate_lines(list(hunk["after_context"]), max_lines)),
                ]
            )
        return "\n".join(lines)

    preview = build_index_preview(repo_root, report, max_lines)
    lines.append("hunks: 0")
    lines.append("index preview:")
    lines.extend(section_lines("ours", preview["ours"]))
    lines.extend(section_lines("base", preview["base"]))
    lines.extend(section_lines("theirs", preview["theirs"]))
    if "ours_vs_theirs_diff" in preview:
        lines.extend(section_lines("ours vs theirs diff", preview["ours_vs_theirs_diff"]))
    return "\n".join(lines)


def render_json(
    repo_root: Path,
    reports: list[_Report],
    include_details: bool,
    max_lines: int,
) -> str:
    files: list[dict[str, object]] = []
    for report in reports:
        file_entry: dict[str, object] = {
            "path": report["path"],
            "conflict_type": report["conflict_type"],
            "stages": report["stages"],
            "marker_hunks": report["marker_hunks"],
            "parse_error": report["parse_error"],
        }
        if report["operation"] is not None:
            file_entry["operation"] = report["operation"]
        if report["author_intent"] is not None:
            file_entry["author_intent"] = cast(object, report["author_intent"])
        if include_details:
            if report["hunks"]:
                file_entry["hunks"] = [
                    {
                        "start_line": hunk["start_line"],
                        "end_line": hunk["end_line"],
                        "before_context": truncate_lines(list(hunk["before_context"]), max_lines),
                        "ours_label": hunk["ours_label"],
                        "ours": truncate_lines(list(hunk["ours"]), max_lines),
                        "base_label": hunk["base_label"],
                        "base": truncate_lines(list(hunk["base"]), max_lines)
                        if hunk["base"]
                        else None,
                        "theirs_label": hunk["theirs_label"],
                        "theirs": truncate_lines(list(hunk["theirs"]), max_lines),
                        "after_context": truncate_lines(list(hunk["after_context"]), max_lines),
                        "ours_vs_theirs_diff": build_diff(
                            list(hunk["ours"]),
                            list(hunk["theirs"]),
                            str(hunk["ours_label"]),
                            str(hunk["theirs_label"]),
                            max_lines,
                        ),
                    }
                    for hunk in report["hunks"]
                ]
            else:
                file_entry["index_preview"] = build_index_preview(repo_root, report, max_lines)
        files.append(file_entry)

    return json.dumps(
        {
            "repo_root": str(repo_root),
            "conflicted_files": files,
        },
        indent=2,
    )


class _Args(Protocol):
    """The CLI surface, declared so `argparse`'s `Namespace` stops leaking `Any`."""

    repo: str
    file: list[str]
    all: bool
    json: bool
    context: int
    max_lines: int


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Summarize and extract compact merge-conflict context."
    )
    _ = parser.add_argument("--repo", default=".", help="Path inside the target repository.")
    _ = parser.add_argument(
        "--file",
        action="append",
        default=[],
        help="Conflicted file to inspect in detail. Repeat to inspect multiple files.",
    )
    _ = parser.add_argument(
        "--all",
        action="store_true",
        help="Print detailed output for every conflicted file.",
    )
    _ = parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of text.",
    )
    _ = parser.add_argument(
        "--context",
        type=int,
        default=2,
        help="Lines of surrounding context to include around each conflict hunk.",
    )
    _ = parser.add_argument(
        "--max-lines",
        type=int,
        default=40,
        help="Maximum lines to print for each section before truncating.",
    )
    args = cast(_Args, cast(object, parser.parse_args()))

    if args.all and args.file:
        parser.error("--all cannot be combined with --file")
    if args.context < 0:
        parser.error("--context must be non-negative")
    if args.max_lines <= 0:
        parser.error("--max-lines must be positive")

    try:
        repo_root = find_repo_root(Path(args.repo).resolve())
        entries = get_unmerged_entries(repo_root)
        operation_info = detect_git_operation(repo_root)
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    reports = [
        build_summary_report(repo_root, path, entries[path], args.context, operation_info)
        for path in sorted(entries)
    ]

    if not reports:
        message = (
            json.dumps({"repo_root": str(repo_root), "conflicted_files": []}, indent=2)
            if args.json
            else f"repo: {repo_root}\nconflicted files: 0"
        )
        print(message)
        return 0

    if args.all:
        selected_reports = reports
    elif args.file:
        try:
            requested_paths = {normalize_requested_path(repo_root, path) for path in args.file}
        except RuntimeError as error:
            print(f"error: {error}", file=sys.stderr)
            return 2
        known_paths = {str(report["path"]) for report in reports}
        missing = sorted(requested_paths - known_paths)
        if missing:
            for path in missing:
                print(f"error: conflicted file not found: {path}", file=sys.stderr)
            return 2
        selected_reports = [report for report in reports if report["path"] in requested_paths]
    else:
        selected_reports = []

    if args.json:
        print(
            render_json(
                repo_root, selected_reports or reports, bool(selected_reports), args.max_lines
            )
        )
        return 0

    if not selected_reports:
        print(render_summary_text(repo_root, reports))
        return 0

    print(
        "\n\n".join(
            render_detail_text(repo_root, report, args.max_lines) for report in selected_reports
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
