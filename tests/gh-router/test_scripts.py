"""Smoke tests for the gh-router scripts: syntax, executability, help contract, lib wiring.

The model-facing contract of these scripts is their `--help` header and their exit codes,
so that is what is pinned here — no network, no gh auth required.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GH_ROUTER = REPO_ROOT / "skills/gh-router"
LIBS = GH_ROUTER / "lib"
# Scripts with a `--help` contract that must answer without touching gh or the repo.
SCRIPTS = [
    GH_ROUTER / "scripts/state.sh",
    GH_ROUTER / "scripts/ci.sh",
    GH_ROUTER / "subskills/gh-release/scripts/confirm.sh",
    GH_ROUTER / "scripts/changelog.sh",
    GH_ROUTER / "subskills/pr-land/scripts/pr.sh",
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


def _shell_scripts() -> list[Path]:
    return sorted(GH_ROUTER.rglob("*.sh"))


def test_every_script_sources_only_libs_that_exist() -> None:
    """Shared code moved to lib/ when it was split by concern.

    A stale source path fails loudly here instead of at run time inside a release, and the
    count assertion keeps this guard from passing vacuously if the wiring is ever removed.
    """
    wired = 0
    for script in _shell_scripts():
        text = script.read_text()
        for match in re.finditer(r'^source "\$LIB_DIR/([^"]+)"', text, re.MULTILINE):
            lib = LIBS / match.group(1)
            assert lib.is_file(), f"{script.relative_to(REPO_ROOT)} sources missing lib/{match.group(1)}"
            wired += 1
        if "LIB_DIR" in text:
            assert 'LIB_DIR="$(cd' in text, f"{script.relative_to(REPO_ROOT)} uses LIB_DIR without defining it"
    assert wired >= 8, f"expected the scripts to source lib/, found {wired} wiring sites"


def test_no_script_sources_the_retired_common_helper() -> None:
    """`_common.sh` was retired into lib/{log,repo}.sh; nothing may reference it again."""
    for script in _shell_scripts():
        assert "_common.sh" not in script.read_text(), f"{script.relative_to(REPO_ROOT)} references the retired helper"


def test_pure_libs_install_no_trap_and_log_nothing() -> None:
    """A script that only needs a fact must be able to source it without side effects.

    repo.sh/checks.sh are consumed through command substitution, so an ERR trap or a logging
    call in them would put diagnostics on a channel callers parse as a value.
    """
    for name in ("repo.sh", "checks.sh"):
        text = (LIBS / name).read_text()
        # Match statements, not prose: these modules document that they install no trap.
        assert not re.search(r"^\s*trap\s", text, re.MULTILINE), f"lib/{name} installs a trap"
        assert not re.search(r"^\s*_log\s", text, re.MULTILINE), f"lib/{name} logs"
        assert not re.search(r"^\s*set\s+-", text, re.MULTILINE), f"lib/{name} changes shell options"

