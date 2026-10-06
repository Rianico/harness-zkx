"""Tests for the session-wide git-location scrub — `tests/conftest.py` and `git_env.py`.

Pins both halves of the defence: the hazard (an ambient `GIT_DIR` outranks
`git -C`, so cwd-only isolation is a lie) and the scrub that removes it before a
test can be affected.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from tests.git_env import GIT_LOCATION_VARS, git_env, scrub_git_location_vars

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECK_SCRIPT = REPO_ROOT / "scripts" / "check.sh"
REAL_TIMEOUT = 60


def _init_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _ = subprocess.run(
        ["git", "init", "-q", "-b", "main", str(path)],
        capture_output=True,
        text=True,
        check=True,
        timeout=REAL_TIMEOUT,
    )
    return path


def _config_get(repo: Path, key: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "config", "--get", key],
        capture_output=True,
        text=True,
        check=False,
        timeout=REAL_TIMEOUT,
    )
    return result.stdout.strip()


def test_ambient_git_dir_outranks_dash_c(tmp_path: Path) -> None:
    """Pins the hazard: `GIT_DIR` beats `git -C`, so cwd-only isolation is a lie.

    This is the mechanism that lets a leaked override redirect a test's git write
    into a foreign repository's shared config.
    """
    foreign = _init_repo(tmp_path / "foreign")
    probe = _init_repo(tmp_path / "probe")
    polluted = {**scrub_git_location_vars(dict(os.environ)), "GIT_DIR": str(foreign / ".git")}
    _ = subprocess.run(
        ["git", "-C", str(probe), "config", "hazard.canary", "1"],
        env=polluted,
        capture_output=True,
        text=True,
        check=True,
        timeout=REAL_TIMEOUT,
    )
    assert _config_get(foreign, "hazard.canary") == "1", "hazard gone: -C beat GIT_DIR"
    assert _config_get(probe, "hazard.canary") == "", "probe repo took the write"


def test_scrub_git_location_vars_removes_every_override() -> None:
    dirty = {name: "polluted" for name in GIT_LOCATION_VARS}
    dirty["PATH"] = "/usr/bin"
    assert scrub_git_location_vars(dirty) == {"PATH": "/usr/bin"}


def test_git_env_drops_overrides_and_keeps_the_process_env() -> None:
    env = git_env()
    assert [name for name in GIT_LOCATION_VARS if name in env] == []
    assert env.get("PATH") == os.environ.get("PATH")


def test_git_env_cannot_readmit_an_override(tmp_path: Path) -> None:
    """An explicit override is scrubbed too: pinning one must not be possible."""
    env = git_env(GIT_DIR=str(tmp_path / "bogus.git"))
    assert "GIT_DIR" not in env


def test_no_git_location_override_survives_into_this_session() -> None:
    """The autouse conftest fixture must have scrubbed the live session env."""
    assert [name for name in GIT_LOCATION_VARS if name in os.environ] == []


def test_check_script_scrubs_every_git_location_override() -> None:
    """`check.sh` must scrub exactly the vars this module scrubs.

    One contract in two languages: a var scrubbed in tests but left set in the
    shell would still leak into every gate child the script spawns.
    """
    unset_lines = [
        line
        for line in CHECK_SCRIPT.read_text(encoding="utf-8").splitlines()
        if line.startswith("unset GIT_")
    ]
    assert len(unset_lines) == 1, f"expected one git env scrub line, got {unset_lines}"
    scrubbed = set(unset_lines[0].removeprefix("unset ").split())
    assert scrubbed == set(GIT_LOCATION_VARS)
