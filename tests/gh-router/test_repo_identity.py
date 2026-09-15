"""Regression tests for push-remote repo identity (lib/repo.sh).

`gh repo view` resolves to the upstream project in a multi-remote checkout, so a run lookup
404s and a `repository_dispatch` fires a release workflow at the wrong repo (#33). These tests
pin the push-remote-first derivation, hermetically: no network, no gh auth, no dependence on
the ambient checkout.

They also pin the module's *contract*, which is what makes it composable: stdout carries the
value and nothing else, and failure is a non-zero exit rather than a printed diagnostic.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REPO_LIB = REPO_ROOT / "skills/gh-router/lib/repo.sh"
CI_SH = REPO_ROOT / "skills/gh-router/scripts/ci.sh"


def _git(repo: Path, *args: str) -> None:
    _ = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_checkout(tmp_path: Path) -> Path:
    repo = tmp_path / "checkout"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    _ = (repo / "f").write_text("x\n")
    _git(repo, "add", "f")
    _git(repo, "commit", "-qm", "init")
    return repo


def _run(
    repo: Path, body: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", f'source "{REPO_LIB}"\n{body}'],
        cwd=repo,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
    )


def test_repo_slug_ignores_a_differently_named_upstream_remote(tmp_path: Path) -> None:
    """The reported failure: origin pushes to one project, upstream is another."""
    repo = _init_checkout(tmp_path)
    _git(repo, "remote", "add", "origin", "git@github.com:Rianico/dsh-better-edit.git")
    _git(repo, "remote", "add", "upstream", "git@github.com:Rianico/pi-better-edit.git")
    _git(repo, "config", "branch.main.remote", "origin")

    result = _run(repo, "repo_slug")

    assert result.returncode == 0, result.stderr
    assert result.stdout == "Rianico/dsh-better-edit"


def test_repo_slug_honours_branch_push_remote(tmp_path: Path) -> None:
    """branch.<ref>.pushRemote outranks branch.<ref>.remote when they disagree."""
    repo = _init_checkout(tmp_path)
    _git(repo, "remote", "add", "origin", "git@github.com:Rianico/upstream-project.git")
    _git(repo, "remote", "add", "fork", "git@github.com:Rianico/my-fork.git")
    _git(repo, "config", "branch.main.remote", "origin")
    _git(repo, "config", "branch.main.pushRemote", "fork")

    result = _run(repo, "repo_slug")

    assert result.returncode == 0, result.stderr
    assert result.stdout == "Rianico/my-fork"


def test_repo_slug_parses_url_style_remotes(tmp_path: Path) -> None:
    """https:// remotes parse to the same slug as scp-style ones."""
    repo = _init_checkout(tmp_path)
    _git(repo, "remote", "add", "origin", "https://github.com/Rianico/harness-zkx.git")
    _git(repo, "config", "branch.main.remote", "origin")

    result = _run(repo, "repo_slug")

    assert result.returncode == 0, result.stderr
    assert result.stdout == "Rianico/harness-zkx"


def test_failure_is_a_nonzero_exit_not_stdout_noise(tmp_path: Path) -> None:
    """A resolvable-slug miss must not leak a diagnostic onto stdout.

    Callers consume this module through command substitution (`REPO=$(repo_slug) || fail`), so
    error text on stdout would silently become the "slug". This is why repo.sh installs no ERR
    trap and prints nothing but the value.
    """
    repo = _init_checkout(tmp_path)
    # No remotes, and a gh that always fails, so no derivation can succeed.
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    stub_gh = stub_bin / "gh"
    _ = stub_gh.write_text("#!/usr/bin/env bash\nexit 1\n")
    stub_gh.chmod(0o755)
    path = f"{stub_bin}:{os.environ['PATH']}"

    slug = _run(
        repo, "if slug=$(repo_slug); then printf '%s' \"$slug\"; else exit 1; fi", {"PATH": path}
    )
    assert slug.returncode != 0
    assert slug.stdout.strip() == ""

    # A bare call is equally safe: the module itself never writes to stdout on failure.
    bare = _run(repo, "repo_slug", {"PATH": path})
    assert bare.returncode != 0
    assert bare.stdout.strip() == ""


def test_default_branch_fails_cleanly_when_the_slug_cannot_be_resolved(tmp_path: Path) -> None:
    """default_branch must propagate failure so callers keep their own fallback."""
    repo = _init_checkout(tmp_path)
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    stub_gh = stub_bin / "gh"
    _ = stub_gh.write_text("#!/usr/bin/env bash\nexit 1\n")
    stub_gh.chmod(0o755)

    result = _run(
        repo,
        "if base=$(default_branch); then printf '%s' \"$base\"; else exit 1; fi",
        {"PATH": f"{stub_bin}:{os.environ['PATH']}"},
    )

    assert result.returncode != 0
    assert result.stdout.strip() == ""


def test_ci_sh_resolves_its_repo_through_repo_slug() -> None:
    """ci.sh must not answer repo identity from `gh repo view` (the #33 regression)."""
    text = CI_SH.read_text()

    assert "repo_slug" in text, "ci.sh does not resolve the repo via repo_slug"
    assert 'REPO="$(gh repo view' not in text, "ci.sh resolves its repo from gh repo view"
