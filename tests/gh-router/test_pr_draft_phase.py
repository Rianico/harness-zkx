"""Draft phase of `pr.py --check`: draft.json + pr_body.md, small stdout.

The range authority is the fact source: the draft carries one capped row per
landed commit (15 lines plus a full SHA pointer), the pre-PR fields stay null,
and the full text lives on disk only. Every --check run emits both files, even a
refused one, and stdout stays down to counts, the two paths, and one hint.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from tests.git_env import git_env

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_PY = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts/pr.py"

LONG_BODY_LINES = 20

GH_STUB = """#!/usr/bin/env bash
for arg in "$@"; do
  if [[ "$arg" =~ pulls\\?head= ]]; then echo "null"; exit 0; fi
  if [[ "$arg" == "user" ]]; then echo "merger-user"; exit 0; fi
done
exit 0
"""


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=git_env(), check=True)


def _git(repo: Path, *args: str) -> None:
    _ = _run(["git", "-C", str(repo), *args])


def _make_repo(repo: Path) -> None:
    """Synthetic repo: main + origin/main + a two-commit feat-draft branch."""
    repo.mkdir(parents=True)
    _ = _run(["git", "init", "-b", "main", str(repo)])
    for key, value in (
        ("user.name", "Draft Synthetic"),
        ("user.email", "draft@x.io"),
        ("commit.gpgsign", "false"),
    ):
        _ = _run(["git", "-C", str(repo), "config", key, value])
    _ = (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(repo, "commit", "-m", "chore: base")
    _git(repo, "remote", "add", "origin", "https://github.com/test/draft.git")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    _git(repo, "checkout", "-b", "feat-draft")
    _ = (repo / "one.txt").write_text("one\n", encoding="utf-8")
    _git(repo, "add", "one.txt")
    _git(repo, "commit", "-m", "feat: one")
    _ = (repo / "two.txt").write_text("two\n", encoding="utf-8")
    _git(repo, "add", "two.txt")
    long_body = "\n".join(f"body-line-{i}" for i in range(1, LONG_BODY_LINES + 1))
    _git(repo, "commit", "-m", "feat: two", "-m", long_body)


def _gh_env(tmp_path: Path) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    _ = gh.write_text(GH_STUB, encoding="utf-8")
    gh.chmod(0o755)
    return git_env(PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}")


def _run_check(repo: Path, env: dict[str, str], *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PR_PY), "--check", "--head", "feat-draft", *extra],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )


def test_default_out_dir_emits_capped_commits_and_null_pr_fields(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    draft_path = repo / ".lsz" / "tmp" / "draft.json"
    body_path = repo / ".lsz" / "tmp" / "pr_body.md"
    assert draft_path.is_file(), "the default out-dir is <repo-root>/.lsz/tmp"
    assert body_path.is_file()

    draft: dict[str, Any] = json.loads(draft_path.read_text(encoding="utf-8"))
    assert draft["pr_number"] is None
    assert draft["pr_url"] is None
    assert draft["base"] == "main"
    assert draft["counts"]["commits"] == 2

    commits = draft["commits"]
    assert [commit["subject"] for commit in commits] == ["feat: one", "feat: two"]
    for commit in commits:
        assert re.fullmatch(r"[0-9a-f]{40}", commit["sha"]), commit["sha"]
        assert commit["sha"].startswith(commit["short_sha"])
        assert commit["body_lines"] <= 15

    long_commit = commits[1]
    assert long_commit["body_lines"] == 15
    assert long_commit["body_omitted_lines"] == LONG_BODY_LINES - 15
    assert "body-line-15" in long_commit["body"]
    assert "body-line-16" not in long_commit["body"]

    body_text = body_path.read_text(encoding="utf-8")
    assert "curated landing body" in body_text
    assert "Co-authored-by: Draft Synthetic <draft@x.io>" in body_text

    # stdout stays small: counts, the two paths, one hint — never the full text.
    assert "commits: 2" in r.stdout
    assert "trailers: 1" in r.stdout
    assert str(draft_path) in r.stdout
    assert str(body_path) in r.stdout
    assert r.stdout.count("hint:") == 1
    assert "body-line-" not in r.stdout
    assert "curated landing body" not in r.stdout
    assert "Co-authored-by" not in r.stdout


def test_pr_body_keeps_the_authored_rendering_while_squash_body_is_cleaned(
    tmp_path: Path,
) -> None:
    """`pr_body.md` is the authored description; `draft.json` carries the cleaned squash text."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "authored.md"
    _ = body_file.write_text(
        "## Summary\nreal change\n\n"
        "```mermaid\nflowchart LR\n  A --> B\n```\n\n"
        "<details><summary>trace</summary>\nlog\n</details>\n",
        encoding="utf-8",
    )

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    draft: dict[str, Any] = json.loads(
        (repo / ".lsz" / "tmp" / "draft.json").read_text(encoding="utf-8")
    )
    squash_body = str(draft["squash_body"])
    assert "mermaid" not in squash_body
    assert "flowchart" not in squash_body
    assert "<details>" not in squash_body

    body_text = (repo / ".lsz" / "tmp" / "pr_body.md").read_text(encoding="utf-8")
    assert "```mermaid" in body_text
    assert "flowchart LR" in body_text
    assert "<details>" in body_text
    assert "real change" in body_text


def test_out_dir_creates_parents_and_leaves_the_default_untouched(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    out_dir = tmp_path / "nested" / "deep" / "drafts"
    assert not out_dir.exists()

    r = _run_check(repo, env, "--body", "## Summary\nbody\n", "--out-dir", str(out_dir))

    assert r.returncode == 0, r.stderr
    assert (out_dir / "draft.json").is_file()
    assert (out_dir / "pr_body.md").is_file()
    assert not (repo / ".lsz").exists()
    assert str(out_dir / "draft.json") in r.stdout


def test_pre_pr_without_body_still_emits_files_and_refuses(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)

    r = _run_check(repo, env)

    assert r.returncode == 2
    assert "no open PR for head feat-draft" in r.stderr
    draft_path = repo / ".lsz" / "tmp" / "draft.json"
    assert draft_path.is_file()
    assert (repo / ".lsz" / "tmp" / "pr_body.md").is_file()
    draft: dict[str, Any] = json.loads(draft_path.read_text(encoding="utf-8"))
    assert draft["pr_number"] is None
    assert draft["pr_url"] is None
    assert draft["status"] == "refused"
    assert draft["exit_code"] == 2
    assert draft["commits"], "range facts are emitted even without an authored body"


def test_missing_out_dir_argument_is_a_usage_error(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)

    r = subprocess.run(
        [sys.executable, str(PR_PY), "--check", "--out-dir"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )

    assert r.returncode == 2
    assert "missing argument for --out-dir" in r.stderr


def test_title_follows_head_not_cwd(tmp_path: Path) -> None:
    """The default title derives from --head, never from the caller's checkout."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    _git(repo, "checkout", "main")
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    draft: dict[str, Any] = json.loads(
        (repo / ".lsz" / "tmp" / "draft.json").read_text(encoding="utf-8")
    )
    assert draft["title"] == "feat: two"


def test_empty_range_warns_the_title_is_a_guess(tmp_path: Path) -> None:
    """No unique commits means the title cannot describe the change; say so."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    _git(repo, "branch", "empty", "main")
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file), "--head", "empty")
    assert "no unique commits" in r.stderr
    assert "--title" in r.stderr


def test_dirty_block_reports_uncommitted_work(tmp_path: Path) -> None:
    """draft.json names working-tree dirt; the fingerprint stays commit-only."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file))
    assert r.returncode == 0, r.stderr
    clean: dict[str, Any] = json.loads(
        (repo / ".lsz" / "tmp" / "draft.json").read_text(encoding="utf-8")
    )
    assert clean["dirty"] == {"porcelain": [], "diff_stat": []}
    assert clean["counts"]["dirty_files"] == 0

    _ = (repo / "one.txt").write_text("one edited\n", encoding="utf-8")
    _ = (repo / "untracked.txt").write_text("new\n", encoding="utf-8")
    r = _run_check(repo, env, "--body-file", str(body_file))
    assert r.returncode == 0, r.stderr
    draft: dict[str, Any] = json.loads(
        (repo / ".lsz" / "tmp" / "draft.json").read_text(encoding="utf-8")
    )
    porcelain = draft["dirty"]["porcelain"]
    assert any("one.txt" in row for row in porcelain)
    assert any("untracked.txt" in row for row in porcelain)
    assert draft["counts"]["dirty_files"] == len(porcelain)


def test_hint_carries_the_curation_spec(tmp_path: Path) -> None:
    """The single stdout hint names the bullet order and the strip rules."""
    repo = tmp_path / "repo"
    _make_repo(repo)
    env = _gh_env(tmp_path)
    body_file = tmp_path / "pr_body.md"
    _ = body_file.write_text("## Summary\ncurated landing body\n\nCloses #7\n", encoding="utf-8")

    r = _run_check(repo, env, "--body-file", str(body_file))

    assert r.returncode == 0, r.stderr
    assert r.stdout.count("hint:") == 1
    assert "Core" in r.stdout
    assert "Mermaid" in r.stdout
