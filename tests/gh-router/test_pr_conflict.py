"""Unit tests for pr-conflict subskill and extract_conflict_context.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = (
    REPO_ROOT
    / "skills"
    / "gh-router"
    / "subskills"
    / "pr-conflict"
    / "scripts"
    / "extract_conflict_context.py"
)
SCRIPTS_DIR = SCRIPT_PATH.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from extract_conflict_context import (
    classify_conflict,
    detect_git_operation,
    format_operation_description,
    get_commit_summary,
    parse_conflict_hunks,
)


def _init_git_repo(repo: Path) -> str:
    _ = subprocess.run(["git", "-C", str(repo), "init"], check=True, capture_output=True)
    _ = subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Tester Author"],
        check=True,
        capture_output=True,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "tester@example.com"],
        check=True,
        capture_output=True,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "config", "commit.gpgsign", "false"],
        check=True,
        capture_output=True,
    )
    initial_file = repo / "common.txt"
    _ = initial_file.write_text("base line\n", encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True)
    _ = subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "chore: base commit\n\nInitial repo setup."],
        check=True,
        capture_output=True,
    )
    # Detect branch name (master or main)
    res = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return res.stdout.strip()


def test_detect_git_operation_clean(tmp_path: Path) -> None:
    _ = _init_git_repo(tmp_path)
    op, ours_ref, theirs_ref = detect_git_operation(tmp_path)
    assert op == "unknown"
    assert ours_ref is None
    assert theirs_ref is None


def test_detect_git_operation_merge(tmp_path: Path) -> None:
    base_branch = _init_git_repo(tmp_path)
    f = tmp_path / "conflicted.txt"

    # Commit on feature branch
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", "-b", "feature-merge"],
        check=True,
        capture_output=True,
    )
    _ = f.write_text("feature content\n", encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True, capture_output=True)
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "feat: feature merge work"],
        check=True,
        capture_output=True,
    )

    # Commit conflicting change on base branch
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", base_branch],
        check=True,
        capture_output=True,
    )
    _ = f.write_text("base conflicting content\n", encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True, capture_output=True)
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "fix: base branch hotfix"],
        check=True,
        capture_output=True,
    )

    # Trigger merge conflict
    merge_res = subprocess.run(
        ["git", "-C", str(tmp_path), "merge", "feature-merge"],
        capture_output=True,
        text=True,
    )
    assert merge_res.returncode != 0

    op, ours_ref, theirs_ref = detect_git_operation(tmp_path)
    assert op == "merge"
    assert ours_ref == "HEAD"
    assert theirs_ref == "MERGE_HEAD"


def test_detect_git_operation_rebase(tmp_path: Path) -> None:
    base_branch = _init_git_repo(tmp_path)
    f = tmp_path / "rebase_file.txt"

    # Commit on feature branch
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", "-b", "feature-rebase"],
        check=True,
        capture_output=True,
    )
    _ = f.write_text("feature rebase content\n", encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True, capture_output=True)
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "feat(rebase): feature intent"],
        check=True,
        capture_output=True,
    )

    # Commit on base branch
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", base_branch],
        check=True,
        capture_output=True,
    )
    _ = f.write_text("base rebase content\n", encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True, capture_output=True)
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "feat(base): upstream changes"],
        check=True,
        capture_output=True,
    )

    # Checkout feature and rebase onto base
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", "feature-rebase"],
        check=True,
        capture_output=True,
    )
    rebase_res = subprocess.run(
        ["git", "-C", str(tmp_path), "rebase", base_branch],
        capture_output=True,
        text=True,
    )
    assert rebase_res.returncode != 0

    op, ours_ref, theirs_ref = detect_git_operation(tmp_path)
    assert op == "rebase"
    assert ours_ref == "HEAD"
    assert theirs_ref == "REBASE_HEAD"


def test_detect_git_operation_cherry_pick(tmp_path: Path) -> None:
    base_branch = _init_git_repo(tmp_path)
    f = tmp_path / "cp_file.txt"

    # Commit on feature branch
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", "-b", "feature-cp"],
        check=True,
        capture_output=True,
    )
    _ = f.write_text("feature cp line\n", encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True, capture_output=True)
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "feat: candidate to cherry-pick"],
        check=True,
        capture_output=True,
    )

    # Commit conflicting change on base branch
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", base_branch],
        check=True,
        capture_output=True,
    )
    _ = f.write_text("base cp line\n", encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True, capture_output=True)
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "fix: conflict on base"],
        check=True,
        capture_output=True,
    )

    # Cherry pick feature commit onto base
    cp_res = subprocess.run(
        ["git", "-C", str(tmp_path), "cherry-pick", "feature-cp"],
        capture_output=True,
        text=True,
    )
    assert cp_res.returncode != 0

    op, ours_ref, theirs_ref = detect_git_operation(tmp_path)
    assert op == "cherry-pick"
    assert ours_ref == "HEAD"
    assert theirs_ref == "CHERRY_PICK_HEAD"


def test_get_commit_summary(tmp_path: Path) -> None:
    _ = _init_git_repo(tmp_path)
    summary = get_commit_summary(tmp_path, "HEAD", "common.txt")
    assert summary is not None
    assert summary["author"] == "Tester Author"
    assert summary["subject"] == "chore: base commit"
    assert "Initial repo setup." in summary["body"]
    assert len(summary["sha"]) >= 4
    assert summary["date"]
    assert summary["relative_time"] == summary["date"]

    # Nonexistent ref returns None
    assert get_commit_summary(tmp_path, "NONEXISTENT_REF") is None


def test_format_operation_description() -> None:
    assert (
        format_operation_description("rebase", "HEAD", "REBASE_HEAD", "1111111", "2222222")
        == "rebase (replaying 2222222 onto 1111111)"
    )
    assert (
        format_operation_description("merge", "HEAD", "MERGE_HEAD", "1111111", "2222222")
        == "merge (merging 2222222 into 1111111)"
    )
    assert (
        format_operation_description(
            "cherry-pick", "HEAD", "CHERRY_PICK_HEAD", "1111111", "2222222"
        )
        == "cherry-pick (applying 2222222 onto 1111111)"
    )
    assert (
        format_operation_description("revert", "HEAD", "REVERT_HEAD", "1111111", "2222222")
        == "revert (reverting 2222222 onto 1111111)"
    )
    assert format_operation_description("unknown", None, None, None, None) is None
    assert format_operation_description("rebase", "HEAD", "REBASE_HEAD", None, None) == "rebase"


def test_extract_conflict_context_cli_execution(tmp_path: Path) -> None:
    base_branch = _init_git_repo(tmp_path)
    f = tmp_path / "app.py"

    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", "-b", "feat/calc"],
        check=True,
        capture_output=True,
    )
    _ = f.write_text("def calc(): return 'feature'\n", encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True, capture_output=True)
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "feat(calc): implement feature calc"],
        check=True,
        capture_output=True,
    )

    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "checkout", base_branch],
        check=True,
        capture_output=True,
    )
    _ = f.write_text("def calc(): return 'main'\n", encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True, capture_output=True)
    _ = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "fix(calc): hotfix main calc"],
        check=True,
        capture_output=True,
    )

    merge_res = subprocess.run(
        ["git", "-C", str(tmp_path), "merge", "feat/calc"],
        capture_output=True,
        text=True,
    )
    assert merge_res.returncode != 0

    # 1. Summary mode text
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "conflicted files: 1" in res.stdout
    assert "- app.py | type=text" in res.stdout

    # 2. Detail mode text for single file
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo", str(tmp_path), "--file", "app.py"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "== app.py ==" in res.stdout
    assert "type: text" in res.stdout
    assert "operation: merge (merging" in res.stdout
    assert "author intent:" in res.stdout
    assert "ours (HEAD):" in res.stdout
    assert "subject: fix(calc): hotfix main calc" in res.stdout
    assert "theirs (MERGE_HEAD):" in res.stdout
    assert "subject: feat(calc): implement feature calc" in res.stdout
    assert "stages: 2, 3" in res.stdout
    assert "hunks: 1" in res.stdout
    assert "ours vs theirs diff:" in res.stdout

    # 3. JSON mode for single file
    res = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--repo",
            str(tmp_path),
            "--file",
            "app.py",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert "conflicted_files" in payload
    assert len(payload["conflicted_files"]) == 1
    item = payload["conflicted_files"][0]
    assert item["path"] == "app.py"
    assert item["conflict_type"] == "text"
    assert "merge (merging" in item["operation"]
    assert item["author_intent"]["ours"]["ref"] == "HEAD"
    assert item["author_intent"]["ours"]["subject"] == "fix(calc): hotfix main calc"
    assert item["author_intent"]["theirs"]["ref"] == "MERGE_HEAD"
    assert item["author_intent"]["theirs"]["subject"] == "feat(calc): implement feature calc"
    assert len(item["hunks"]) == 1


def test_extract_conflict_context_clean_cli(tmp_path: Path) -> None:
    _ = _init_git_repo(tmp_path)

    # Clean text mode
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "conflicted files: 0" in res.stdout

    # Clean JSON mode
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--repo", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    payload = json.loads(res.stdout)
    assert payload["conflicted_files"] == []


def test_classify_conflict() -> None:
    assert classify_conflict([1, 2, 3], marker_hunks=1) == "text"
    assert classify_conflict([2, 3], marker_hunks=0) == "add/add"
    assert classify_conflict([1, 2], marker_hunks=0) == "deleted-by-them"
    assert classify_conflict([1, 3], marker_hunks=0) == "deleted-by-us"
    assert classify_conflict([1, 2, 3], marker_hunks=0) == "index-only"
    assert classify_conflict([2], marker_hunks=0) == "unmerged"


def test_parse_conflict_hunks() -> None:
    lines = [
        "preceding line",
        "<<<<<<< ours",
        "ours content",
        "||||||| base",
        "base content",
        "=======",
        "theirs content",
        ">>>>>>> theirs",
        "following line",
    ]
    hunks, err = parse_conflict_hunks(lines, context=1)
    assert err is None
    assert len(hunks) == 1
    hunk = hunks[0]
    assert hunk["ours"] == ["ours content"]
    assert hunk["ours_label"] == "ours"
    assert hunk["base"] == ["base content"]
    assert hunk["base_label"] == "base"
    assert hunk["theirs"] == ["theirs content"]
    assert hunk["theirs_label"] == "theirs"
    assert hunk["before_context"] == ["preceding line"]
    assert hunk["after_context"] == ["following line"]
