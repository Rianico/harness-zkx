"""Closed-issue advisory: a `Closes #N` naming an already-CLOSED issue warns, never refuses.

The shape gate (`check_closes_lines`) only checks the line's form, so a follow-up PR keeps
declaring `Closes #87` long after #87 closed. This adds an ADVISORY: at `--check` preflight and
on the merge path the tooling queries `gh issue view` for each referenced issue and prints a
two-line hint when the state is CLOSED. It is warn-only — it never changes an exit code and never
refuses. Unit tests patch the `_github.run_command` seam; the end-to-end tests drive `pr.py
--check` against a stub `gh` that answers the `issue view ... --json state,closedAt,title` query.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.git_env import git_env

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
PR_PY = PR_SCRIPTS / "pr.py"

if str(PR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PR_SCRIPTS))

import _github as github_mod  # noqa: E402
from _github import issue_state, warn_closed_issues  # noqa: E402
from _squash import extract_closes_numbers  # noqa: E402

ADVISORY = 'advisory: issue #{num} is already CLOSED (title: "{title}")'
HINT = (
    "hint: if this PR is a follow-up, consider using 'Part of #N' "
    "and opening a dedicated issue for this scope."
)


def _completed(
    cmd: list[str], rc: int, out: str, err: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(cmd, rc, out, err)


# --- extract_closes_numbers: pure text scan over CLOSES_REF_RE lines ---


def test_extract_closes_numbers_reads_every_closes_line_in_first_seen_order() -> None:
    """Every closing-keyword line yields its number; prose and list items never do."""
    text = "Summary cites #88 in passing.\nCloses #87\nFixes #12\nclosed #90\nRefs #5\n"
    assert extract_closes_numbers(text) == ["87", "12", "90"]


def test_extract_closes_numbers_dedupes_closes_across_repeat_lines() -> None:
    """A repeated number appears once, keeping its first position."""
    assert extract_closes_numbers("Closes #5\nCloses #5\nCloses #6\n") == ["5", "6"]


def test_extract_closes_numbers_ignores_prose_and_list_items() -> None:
    """`- Closes #9`, a bare `see #42`, and empty text yield nothing."""
    assert extract_closes_numbers("- Closes #9\n") == []
    assert extract_closes_numbers("## Links\nsee #42\n") == []
    assert extract_closes_numbers("") == []


# --- issue_state: the gh issue view read, fail-open ---


def test_issue_state_returns_state_and_title_for_a_closes_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, list[str]] = {}

    def fake(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen["cmd"] = list(cmd)
        payload = {"state": "CLOSED", "closedAt": "2026-01-01T00:00:00Z", "title": "Fix the bug"}
        return _completed(cmd, 0, json.dumps(payload), "")

    monkeypatch.setattr(github_mod, "run_command", fake)
    assert issue_state("owner/repo", "87") == ("CLOSED", "Fix the bug")
    assert seen["cmd"][:4] == ["gh", "issue", "view", "87"]
    assert "state,closedAt,title" in seen["cmd"]
    assert seen["cmd"][-2:] == ["-R", "owner/repo"]


def test_issue_state_returns_none_for_a_closes_target_on_nonzero_rc(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return _completed(cmd, 1, "", "gh: rate limited")

    monkeypatch.setattr(github_mod, "run_command", fake)
    assert issue_state("t/r", "87") is None


def test_issue_state_returns_none_for_a_closes_target_on_garbage_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return _completed(cmd, 0, "not json")

    monkeypatch.setattr(github_mod, "run_command", fake)
    assert issue_state("t/r", "87") is None


# --- warn_closed_issues: prints exactly for CLOSED, silent otherwise ---


def test_warn_closed_issues_warns_only_on_closed_closes_targets(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        num = cmd[3]
        state = "CLOSED" if num == "87" else "OPEN"
        return _completed(cmd, 0, json.dumps({"state": state, "title": "T"}), "")

    monkeypatch.setattr(github_mod, "run_command", fake)
    warned = warn_closed_issues("t/r", "Closes #87\nCloses #5\n")
    err = capsys.readouterr().err
    assert warned == 1
    assert ADVISORY.format(num="87", title="T") in err
    assert "advisory: issue #5" not in err
    assert err.count(HINT) == 1


def test_warn_closed_issues_is_silent_when_a_closes_query_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return _completed(cmd, 1, "", "boom")

    monkeypatch.setattr(github_mod, "run_command", fake)
    assert warn_closed_issues("t/r", "Closes #87\n") == 0
    assert capsys.readouterr().err == ""


# --- end to end: pr.py --check against a stub gh that answers the issue view query ---

# The stub answers `pulls?head=` (no open PR -> local body path), `user` (the merger), and
# precisely the `issue view ... --json state,closedAt,title` query, keyed off ISSUE_STATE.
GH_STUB = """#!/usr/bin/env bash
echo "$@" >> "$GH_LOG"
for arg in "$@"; do
  if [[ "$arg" =~ pulls\\?head= ]]; then echo "null"; exit 0; fi
  if [[ "$arg" == "user" ]]; then echo "merger-user"; exit 0; fi
  if [[ "$arg" == "state,closedAt,title" ]]; then
    printf '{"state":"%s","closedAt":"2026-01-01T00:00:00Z","title":"%s"}\\n' \\
      "${ISSUE_STATE:-OPEN}" "${ISSUE_TITLE:-the issue}"
    exit 0
  fi
done
exit 0
"""


def _make_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    _ = subprocess.run(["git", "init", "-b", "main", str(repo)], env=git_env(), check=True)
    for key, value in (
        ("user.name", "Advisory Synthetic"),
        ("user.email", "advisory@x.io"),
        ("commit.gpgsign", "false"),
    ):
        _ = subprocess.run(
            ["git", "-C", str(repo), "config", key, value], env=git_env(), check=True
        )
    _ = (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(repo), "add", "base.txt"], env=git_env(), check=True)
    _ = subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "chore: base"], env=git_env(), check=True
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "remote", "add", "origin", "https://github.com/test/advisory.git"],
        env=git_env(),
        check=True,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "update-ref", "refs/remotes/origin/main", "HEAD"],
        env=git_env(),
        check=True,
    )
    _ = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "symbolic-ref",
            "refs/remotes/origin/HEAD",
            "refs/remotes/origin/main",
        ],
        env=git_env(),
        check=True,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "checkout", "-b", "feat-advisory"], env=git_env(), check=True
    )
    _ = (repo / "one.txt").write_text("one\n", encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(repo), "add", "one.txt"], env=git_env(), check=True)
    _ = subprocess.run(
        ["git", "-C", str(repo), "commit", "-m", "feat: one"], env=git_env(), check=True
    )


def _gh_env(tmp_path: Path, **issue: str) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    _ = gh.write_text(GH_STUB, encoding="utf-8")
    gh.chmod(0o755)
    return git_env(
        PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}",
        GH_LOG=str(tmp_path / "gh.log"),
        **issue,
    )


def _run_check(repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    body_file = env.pop("_BODY_FILE")
    return subprocess.run(
        [
            sys.executable,
            str(PR_PY),
            "--check",
            "--head",
            "feat-advisory",
            "--title",
            "feat(gh-router): closes advisory probe",
            "--body-file",
            str(body_file),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )


def _closes_body(tmp_path: Path) -> Path:
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\nreal change lands\n\nCloses #87\n", encoding="utf-8")
    return body_file


def test_check_closes_advisory_warns_and_keeps_exit_zero(tmp_path: Path) -> None:
    """A CLOSED referenced issue prints both advisory lines; --check still exits 0."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path, ISSUE_STATE="CLOSED", ISSUE_TITLE="Fix the login race")
    env["_BODY_FILE"] = str(_closes_body(tmp_path))

    r = _run_check(repo, env)

    assert r.returncode == 0, r.stderr
    assert ADVISORY.format(num="87", title="Fix the login race") in r.stderr
    assert HINT in r.stderr
    log = (tmp_path / "gh.log").read_text(encoding="utf-8")
    assert "issue view 87" in log


def test_check_closes_advisory_stays_silent_when_issue_is_open(tmp_path: Path) -> None:
    """An OPEN referenced issue prints no advisory line; the run otherwise succeeds."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path, ISSUE_STATE="OPEN", ISSUE_TITLE="Still open")
    env["_BODY_FILE"] = str(_closes_body(tmp_path))

    r = _run_check(repo, env)

    assert r.returncode == 0, r.stderr
    assert "advisory: issue" not in r.stderr
    assert "hint: if this PR is a follow-up" not in r.stderr
