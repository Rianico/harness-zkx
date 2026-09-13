"""Smoke tests for the gh-router scripts: syntax, executability, help contract.

The model-facing contract of these scripts is their `--help` header and their exit codes,
so that is what is pinned here — no network, no gh auth required.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = [
    REPO_ROOT / "skills/gh-router/scripts/state.sh",
    REPO_ROOT / "skills/gh-router/scripts/ci.sh",
    REPO_ROOT / "skills/gh-router/subskills/gh-release/scripts/confirm.sh",
    REPO_ROOT / "skills/gh-router/scripts/changelog.sh",
]


def test_scripts_exist_and_are_executable() -> None:
    for script in SCRIPTS:
        assert script.is_file(), f"missing {script}"
        assert script.stat().st_mode & 0o111, f"{script} is not executable"


def test_scripts_parse_with_bash() -> None:
    for script in SCRIPTS:
        result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert result.returncode == 0, f"{script} does not parse:\n{result.stderr}"


def test_help_is_brief_and_does_not_need_the_network() -> None:
    """`--help` must answer from the file header alone, before any gh/repo access."""
    for script in SCRIPTS:
        result = subprocess.run(["bash", str(script), "--help"], capture_output=True, text=True)
        assert result.returncode == 0, f"{script} --help failed: {result.stderr}"
        assert "Usage:" in result.stdout, f"{script} --help does not print a Usage line"
        assert len(result.stdout.splitlines()) <= 14, f"{script} --help is not brief"


def test_changelog_sync_dry_run_decides_without_mutating() -> None:
    """`changelog.sh sync` reports a verdict and touches nothing unless --apply is passed."""
    script = REPO_ROOT / "skills/gh-router/scripts/changelog.sh"

    def changelog_status() -> str:
        return subprocess.run(
            ["git", "status", "--porcelain", "--", "CHANGELOG.md"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        ).stdout

    before = changelog_status()
    result = subprocess.run(
        ["bash", str(script), "sync"], capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode in (0, 1), f"dry run failed unexpectedly: {result.stderr}"
    combined = (result.stdout + result.stderr).lower()
    assert "changelog.md" in combined, "verdict does not name the file it inspected"
    assert changelog_status() == before, "dry run mutated the working tree"
