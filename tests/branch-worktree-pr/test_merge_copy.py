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


# --- automatic body wrapping -----------------------------------------------------------------


def test_wrap_commit_message_wraps_body_and_keeps_the_subject() -> None:
    """The subject is bounded by a different rule, so wrapping must not touch it."""
    subject = "feat(thing): a subject that is deliberately quite long but still under the limit"
    message = f"{subject}\n\n{'word ' * 40}end\n"

    wrapped = merge_copy.wrap_commit_message(message, 40)

    lines = wrapped.split("\n")
    assert lines[0] == subject
    assert all(len(line) <= 40 for line in lines[1:]), wrapped
    assert len([line for line in lines if line.strip()]) > 2, wrapped


def test_wrap_commit_message_leaves_footers_verbatim() -> None:
    """`BREAKING CHANGE:` and `Token: value` footers must survive byte-for-byte.

    A rewrap that splits `BREAKING CHANGE:` from its value — or wraps a `Closes #12` line —
    silently breaks commitlint's footer parser, so footers are never touched.
    """
    breaking = "BREAKING CHANGE: " + "x" * 120
    trailer = "Closes #" + "4" * 60
    message = f"feat(api)!: drop a field\n\nshort body\n\n{breaking}\n{trailer}\n"

    wrapped = merge_copy.wrap_commit_message(message, 40)

    assert f"\n{breaking}\n" in wrapped, wrapped
    assert f"\n{trailer}\n" in wrapped, wrapped


def test_commit_body_offenders_ignores_footers(tmp_path: Path) -> None:
    """A long footer is `footer-max-line-length`'s business, not this rule's."""
    repo = _repo_with_a_long_body(tmp_path, "BREAKING CHANGE: " + "x" * 130)

    assert merge_copy.commit_body_offenders(repo, "base", 100) == []


def test_wrap_commit_message_cannot_break_an_unbreakable_token() -> None:
    """A single word over the limit is left for the caller's re-check to report, not truncated."""
    token = "x" * 130
    wrapped = merge_copy.wrap_commit_message(f"feat(thing): t\n\n{token}\n", 100)

    assert token in wrapped, "the token must not be split or dropped"
    assert any(len(line) > 100 for line in wrapped.split("\n"))


def test_rewrite_commit_bodies_wraps_history_and_preserves_content(tmp_path: Path) -> None:
    """The rewrap is message-only: trees, files and authorship survive, bodies get wrapped."""
    repo = _repo_with_a_long_body(tmp_path, " ".join(["word"] * 40))
    before_author = subprocess.run(
        ["git", "log", "-1", "--pretty=%an <%ae>"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    ok, detail = merge_copy.rewrite_commit_bodies(repo, "base", 100)

    assert ok, detail
    assert "wrapped 1 commit" in detail, detail
    assert merge_copy.commit_body_offenders(repo, "base", 100) == [], "still offending"
    # content and authorship unchanged
    assert (repo / "b.txt").read_text(encoding="utf-8") == "b\n"
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout
    assert status == "", f"rewrap dirtied the tree: {status}"
    after_author = subprocess.run(
        ["git", "log", "-1", "--pretty=%an <%ae>"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert after_author == before_author
    # the branches/target are intact
    log = subprocess.run(
        ["git", "log", "--oneline", "base..HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert len(log.splitlines()) == 1, log


def test_rewrite_commit_bodies_is_a_noop_when_already_wrapped(tmp_path: Path) -> None:
    repo = _repo_with_a_long_body(tmp_path, "short body line")
    before = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()

    ok, detail = merge_copy.rewrite_commit_bodies(repo, "base", 100)

    assert ok, detail
    assert "no commit body needed wrapping" in detail, detail
    after = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert after == before, "an already-wrapped history must not be rewritten"
