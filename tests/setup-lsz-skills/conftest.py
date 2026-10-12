"""Shared fixtures for the setup-lsz-skills tests.

The skill lives under a hyphenated directory (`setup-lsz-skills`), which is not a
valid importable Python module path, so tests load the script by file location via
`importlib` — the same recipe the `scaffold` tests use.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "setup-lsz-skills"
SCRIPT = SKILL_DIR / "scripts" / "setup_detect.py"
TEMPLATES_DIR = SKILL_DIR / "templates"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def sd():
    """The loaded setup_detect module (session-wide; it is pure logic)."""
    return _load("setup_detect_mod", SCRIPT)


@pytest.fixture
def templates_dir() -> Path:
    return TEMPLATES_DIR


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """An initialized git repo with a GitHub origin remote, in its own subdir.

    Kept separate from `tmp_repo` (the bare `tmp_path`) so the two are not the
    same directory when a test needs both a git and a non-git repo.
    """
    repo = tmp_path / "gitrepo"
    repo.mkdir()
    _ = subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    _ = subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/acme/widget.git"],
        cwd=repo,
        check=True,
    )
    return repo


@pytest.fixture
def run_cli():
    """Invoke the skill script as a subprocess against a target `--cwd`."""

    def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--cwd", str(cwd), *args],
            capture_output=True,
            text=True,
        )

    return _run
