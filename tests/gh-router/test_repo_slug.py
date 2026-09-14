"""Regression tests for push-remote repo resolution (issue #33).

`gh repo view` resolves to the upstream project in a multi-remote checkout, so a
`repository_dispatch` — or a run lookup — targets the wrong repo. These tests pin the
push-remote-first derivation in `_common.sh::repo_slug`, hermetically: no network, no gh
auth, no dependence on the ambient checkout.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMMON = REPO_ROOT / "skills/gh-router/subskills/gh-release/scripts/_common.sh"
CI_SH = REPO_ROOT / "skills/gh-router/scripts/ci.sh"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_checkout(tmp_path: Path) -> Path:
    repo = tmp_path / "checkout"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "f").write_text("x\n")
    _git(repo, "add", "f")
    _git(repo, "commit", "-qm", "init")
    return repo


def _repo_slug(repo: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", f'source "{COMMON}"; repo_slug'],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def test_repo_slug_ignores_a_differently_named_upstream_remote(tmp_path: Path) -> None:
    """The reported failure: origin pushes to one project, upstream is another."""
    repo = _init_checkout(tmp_path)
    _git(repo, "remote", "add", "origin", "git@github.com:Rianico/dsh-better-edit.git")
    _git(repo, "remote", "add", "upstream", "git@github.com:Rianico/pi-better-edit.git")
    _git(repo, "config", "branch.main.remote", "origin")

    result = _repo_slug(repo)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "Rianico/dsh-better-edit"


def test_repo_slug_honours_branch_push_remote(tmp_path: Path) -> None:
    """branch.<ref>.pushRemote outranks branch.<ref>.remote when they disagree."""
    repo = _init_checkout(tmp_path)
    _git(repo, "remote", "add", "origin", "git@github.com:Rianico/upstream-project.git")
    _git(repo, "remote", "add", "fork", "git@github.com:Rianico/my-fork.git")
    _git(repo, "config", "branch.main.remote", "origin")
    _git(repo, "config", "branch.main.pushRemote", "fork")

    result = _repo_slug(repo)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "Rianico/my-fork"


def test_repo_slug_parses_url_style_remotes(tmp_path: Path) -> None:
    """https:// remotes parse to the same slug as scp-style ones."""
    repo = _init_checkout(tmp_path)
    _git(repo, "remote", "add", "origin", "https://github.com/Rianico/harness-zkx.git")
    _git(repo, "config", "branch.main.remote", "origin")

    result = _repo_slug(repo)

    assert result.returncode == 0, result.stderr
    assert result.stdout == "Rianico/harness-zkx"


def test_repo_slug_fails_rather_than_returning_a_non_slug(tmp_path: Path) -> None:
    """An unparseable remote must not leak through as a "slug"."""
    repo = _init_checkout(tmp_path)
    # No remotes at all: every git lookup fails, so only the gh fallback could answer.
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    stub_gh = stub_bin / "gh"
    stub_gh.write_text("#!/usr/bin/env bash\nexit 1\n")
    stub_gh.chmod(0o755)
    # Invoke it the way _common.sh documents — assignment in a condition context. A bare
    # `repo_slug` call trips the ERR trap, which is not how any caller uses it.
    script = f'source "{COMMON}"\nif slug=$(repo_slug); then printf "%s" "$slug"; else exit 1; fi\n'

    result = subprocess.run(
        ["bash", "-c", script],
        cwd=repo,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": f"{stub_bin}:{os.environ['PATH']}"},
    )

    assert result.returncode != 0
    assert result.stdout.strip() == ""


def test_ci_sh_resolves_its_repo_through_repo_slug() -> None:
    """ci.sh must not answer repo identity from `gh repo view` (the #33 regression)."""
    text = CI_SH.read_text()

    assert "repo_slug" in text, "ci.sh does not resolve the repo via repo_slug"
    assert 'REPO="$(gh repo view' not in text, "ci.sh resolves its repo from gh repo view"
