"""Shared synthetic-repo and stub helpers for gh-router tests.

Deduped from per-file copies (T3d item 9): `_git` (six files), `_make_repo`
(four files), `_init_git_repo` (conflict), and the bindir/gh-stub triplet
behind `make_gh_mock` / `_make_gh_mock`. Fixture bytes are preserved —
callers pass their old identity/origin/branch values through, so the only
behavioral delta is hermeticity: `run_git` always builds `git_env()`
(the golden copy inherited ambient env before).

Kept out on purpose: `test_pr_status._make_repo` (local bare origin for
push tests — different contract) and `_make_trunk_repo` (trunk fixture,
no main refs — different contract).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from tests.git_env import git_env


def run_git(repo: Path, *args: str) -> str:
    """Run `git -C repo ...` hermetically; return stdout."""
    res = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env=git_env(),
        check=True,
    )
    return res.stdout


def make_repo(
    repo: Path,
    *,
    slug: str,
    branch: str,
    user_name: str,
    user_email: str,
    extra_commits: tuple[tuple[str, str, str, str | None], ...] = (),
) -> None:
    """Synthetic origin-backed repo: main + base commit + origin/main refs + feat branch.

    `extra_commits` is `(filename, content, message, body?)` per extra commit
    on the feat branch, appended after the shared `feat: one` commit.
    """
    _ = subprocess.run(
        ["git", "init", "-b", "main", str(repo)],
        capture_output=True,
        env=git_env(),
        check=True,
    )
    for key, value in (
        ("user.name", user_name),
        ("user.email", user_email),
        ("commit.gpgsign", "false"),
    ):
        _ = subprocess.run(
            ["git", "-C", str(repo), "config", key, value],
            capture_output=True,
            env=git_env(),
            check=True,
        )
    _ = (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _ = run_git(repo, "add", "base.txt")
    _ = run_git(repo, "commit", "-m", "chore: base")
    _ = run_git(repo, "remote", "add", "origin", f"https://github.com/test/{slug}.git")
    _ = run_git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _ = run_git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    _ = run_git(repo, "checkout", "-b", branch)
    _ = (repo / "one.txt").write_text("one\n", encoding="utf-8")
    _ = run_git(repo, "add", "one.txt")
    _ = run_git(repo, "commit", "-m", "feat: one")
    for filename, content, message, body in extra_commits:
        _ = (repo / filename).write_text(content, encoding="utf-8")
        _ = run_git(repo, "add", filename)
        if body is None:
            _ = run_git(repo, "commit", "-m", message)
        else:
            _ = run_git(repo, "commit", "-m", message, "-m", body)


def init_git_repo(repo: Path) -> str:
    """Init in place with the Tester identity; return the default branch name."""
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


def write_gh_stub(bindir: Path, script: str) -> Path:
    """Write an executable `gh` stub `script` into `bindir`; return `bindir`."""
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    _ = gh.write_text(script, encoding="utf-8")
    gh.chmod(0o755)
    return bindir
