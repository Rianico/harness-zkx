"""Tests for `skills/branch-worktree-pr/scripts/merge_copy.py` (issue #39).

`wt merge` concatenates every task-branch commit body into one squashed message, so a single
over-long body line fails commitlint's `body-max-line-length` at merge time. The pre-check
must name the offending commit/line before the merge, and must stay silent for repos that do
not wire commitlint at all.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import merge_copy


def _git(repo: Path, *args: str) -> None:
    _ = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _repo_with_a_long_body(tmp_path: Path, body_line: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "t")
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "chore: base")
    _git(repo, "tag", "base")
    (repo / "b.txt").write_text("b\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", f"feat(thing): add a thing\n\n{body_line}")
    return repo


def test_commit_body_offenders_reports_the_offending_line(tmp_path: Path) -> None:
    repo = _repo_with_a_long_body(tmp_path, "x" * 130)

    offenders = merge_copy.commit_body_offenders(repo, "base", 100)

    assert len(offenders) == 1, offenders
    assert "130 chars" in offenders[0], offenders
    assert ":3:" in offenders[0], f"expected the body line number, got {offenders[0]}"


def test_commit_body_offenders_accepts_a_wrapped_body(tmp_path: Path) -> None:
    """A body wrapped under the limit must not be flagged (no false pre-check failures)."""
    repo = _repo_with_a_long_body(tmp_path, "wrapped body line")

    assert merge_copy.commit_body_offenders(repo, "base", 100) == []


def test_commitlint_configured_detects_the_config_file(tmp_path: Path) -> None:
    (tmp_path / "commitlint.config.js").write_text("export default {}\n", encoding="utf-8")
    assert merge_copy.commitlint_configured(tmp_path)


def test_commitlint_configured_detects_the_package_json_key(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"commitlint": {"extends": []}}\n', encoding="utf-8")
    assert merge_copy.commitlint_configured(tmp_path)


def test_commitlint_configured_is_false_without_commitlint(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name": "x"}\n', encoding="utf-8")
    assert not merge_copy.commitlint_configured(tmp_path)
