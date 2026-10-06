"""Tests for scripts/check.sh and .githooks/pre-commit — the local CI gate mirror.

Covers file presence, mode bits, the gate command ordering contract, and the
end-to-end flag behavior. The e2e tests run the gate with --skip-tests so no
nested pytest is ever launched; the skipif decorator guards the rare case where
this suite itself runs inside `bash scripts/check.sh` gate 4.
"""

from __future__ import annotations

import functools
import os
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_SCRIPT = REPO_ROOT / "scripts" / "check.sh"
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

GATE_COMMANDS = [
    "uv run ruff check .",
    "uv run ruff format --check .",
    "uv run basedpyright --warnings",
    "uv run pytest",
]

SKIP_NESTED = pytest.mark.skipif(
    os.environ.get("HARNESS_CHECK_GATE") == "1",
    reason="nested check-gate pytest run",
)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([*args], cwd=REPO_ROOT, capture_output=True, text=True, check=False)


@functools.cache
def _skip_tests_run() -> subprocess.CompletedProcess[str]:
    """One shared `check.sh --skip-tests` run for the gate-banner assertions."""
    return _run("bash", "scripts/check.sh", "--skip-tests")


def test_files_exist_and_are_executable() -> None:
    for path in (CHECK_SCRIPT, HOOK):
        assert path.is_file(), f"{path} missing"
        assert stat.S_IMODE(path.stat().st_mode) == 0o755, f"{path} is not mode 0755"


def test_check_script_content_contract() -> None:
    text = CHECK_SCRIPT.read_text(encoding="utf-8")
    assert "set -euo pipefail" in text
    previous = -1
    for command in GATE_COMMANDS:
        index = text.index(command)
        assert index > previous, f"gate command out of order: {command!r}"
        previous = index


@SKIP_NESTED
def test_skip_tests_exit_zero_and_gate_banners() -> None:
    result = _skip_tests_run()
    assert result.returncode == 0, result.stderr[-2000:]
    for banner in GATE_COMMANDS[:3]:
        assert banner in result.stdout, f"gate banner missing from stdout: {banner!r}"


@SKIP_NESTED
def test_skip_tests_banner_reports_skipped_gate() -> None:
    result = _skip_tests_run()
    assert result.returncode == 0, result.stderr[-2000:]
    assert "SKIPPED" in result.stdout
    assert "uv run pytest was skipped" in result.stdout


@SKIP_NESTED
def test_pre_commit_hook_forwards_to_check_script() -> None:
    result = _run("bash", ".githooks/pre-commit", "--skip-tests")
    assert result.returncode == 0, result.stderr[-2000:]
    assert "uv run ruff check ." in result.stdout, "hook did not reach the gate"


@SKIP_NESTED
def test_unknown_flag_exits_two_with_usage() -> None:
    result = _run("bash", "scripts/check.sh", "--bogus")
    assert result.returncode == 2
    assert "usage" in result.stderr
