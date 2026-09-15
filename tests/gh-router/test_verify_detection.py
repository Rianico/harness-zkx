"""Repo-type detection in the release preflight (gh-release/scripts/verify.sh).

The phase used to treat the mere presence of `package.json` as "this is a Node repo". This
harness carries a `package.json` that is only a release-tooling manifest (semantic-release
deps, `private: true`, no `scripts`), so `verify.sh` classified itself as Node, ran
`npm run lint`, and aborted the phase before ruff or pytest ever ran — a release preflight
that could never pass on the repository that ships it.

These tests drive the real script with stubbed toolchains on PATH, so they assert which
project type was detected without running a package manager, a network call, or a linter.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY = REPO_ROOT / "skills/gh-router/subskills/gh-release/scripts/verify.sh"


def _stub_toolchain(tmp_path: Path) -> tuple[str, Path]:
    """Every toolchain entry is a stub that records its argv instead of running."""
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    calls = tmp_path / "calls.log"
    for exe in ("uv", "npm", "pnpm", "cargo"):
        stub = stub_bin / exe
        _ = stub.write_text(
            f'#!/usr/bin/env bash\nprintf "%s %s\\n" "{exe}" "$*" >> "{calls}"\nexit 0\n'
        )
        stub.chmod(0o755)
    return f"{stub_bin}:{os.environ['PATH']}", calls


def _run_verify(repo: Path, path: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(VERIFY)],
        cwd=repo,
        capture_output=True,
        text=True,
        env={**os.environ, "PATH": path},
    )


def test_release_manifest_only_repo_is_verified_as_python(tmp_path: Path) -> None:
    """A package.json without `scripts` is release tooling, not a Node project."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / "pyproject.toml").write_text("[project]\nname = 'x'\nversion = '0.0.0'\n")
    _ = (repo / "package.json").write_text(
        '{\n  "name": "x",\n  "private": true,\n  "devDependencies": {"semantic-release": ">=25"}\n}\n'
    )
    path, calls = _stub_toolchain(tmp_path)

    result = _run_verify(repo, path)

    assert result.returncode == 0, result.stdout + result.stderr
    invoked = calls.read_text()
    assert "uv run ruff check ." in invoked, invoked
    assert "uv run basedpyright" in invoked, invoked
    assert "uv run pytest" in invoked, invoked
    assert "npm " not in invoked and "pnpm " not in invoked, invoked


def test_node_repo_with_scripts_still_verifies_as_node(tmp_path: Path) -> None:
    """The python fallback must not steal repos that really do declare npm scripts."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / "package.json").write_text(
        '{\n  "name": "x",\n  "scripts": {"lint": "eslint .", "typecheck": "tsc", "test": "vitest run"}\n}\n'
    )
    path, calls = _stub_toolchain(tmp_path)

    result = _run_verify(repo, path)

    assert result.returncode == 0, result.stdout + result.stderr
    invoked = calls.read_text()
    assert "npm run --silent lint" in invoked, invoked
    assert "npm test" in invoked, invoked
    assert "uv run" not in invoked, invoked


def test_rust_repo_is_unaffected(tmp_path: Path) -> None:
    """Cargo detection keeps its place behind the Node signal."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = (repo / "Cargo.toml").write_text("[package]\nname = 'x'\nversion = '0.0.0'\n")
    path, calls = _stub_toolchain(tmp_path)

    result = _run_verify(repo, path)

    assert result.returncode == 0, result.stdout + result.stderr
    invoked = calls.read_text()
    assert "cargo clippy" in invoked, invoked
    assert "cargo test" in invoked, invoked
    assert "uv run" not in invoked, invoked
