"""Tests for the session-wide git scrub — `tests/conftest.py` and `git_env.py`.

Pins all three halves of the defence: the two hazards (an ambient `GIT_DIR`
outranks `git -C`, so cwd-only isolation is a lie; an ambient `GIT_AUTHOR_NAME`
outranks the repo-local `user.name`, so a nested fixture repo commits as the
caller) and the scrubs that remove either before a test can be affected.
"""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

from tests.git_env import (
    GIT_IDENTITY_VARS,
    GIT_LOCATION_VARS,
    git_env,
    scrub_git_identity_vars,
    scrub_git_location_vars,
    scrub_git_vars,
)

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


def test_ambient_git_author_outranks_repo_config(tmp_path: Path) -> None:
    """Pins the hazard: `GIT_AUTHOR_NAME` beats the repo-local `user.name`.

    Git exports the resolved identity into every hook, so a nested repo a test
    creates inherits the outer commit's identity and the fixture's `user.name`
    loses. The ambient name is generated, so no reproduction identity lands in
    the repo.
    """
    repo = _init_repo(tmp_path / "probe")
    _ = subprocess.run(
        ["git", "-C", str(repo), "config", "user.name", "Fixture Committer"],
        capture_output=True,
        text=True,
        check=True,
        timeout=REAL_TIMEOUT,
    )
    _ = subprocess.run(
        ["git", "-C", str(repo), "config", "user.email", "fixture@example.com"],
        capture_output=True,
        text=True,
        check=True,
        timeout=REAL_TIMEOUT,
    )
    _ = (repo / "tracked.txt").write_text("hazard\n", encoding="utf-8")
    _ = subprocess.run(
        ["git", "-C", str(repo), "add", "tracked.txt"],
        capture_output=True,
        text=True,
        check=True,
        timeout=REAL_TIMEOUT,
    )
    ambient = f"ambient-{uuid.uuid4().hex[:12]}"
    polluted = {
        **scrub_git_vars(dict(os.environ)),
        "GIT_AUTHOR_NAME": ambient,
        "GIT_AUTHOR_EMAIL": f"{ambient}@example.com",
        "GIT_COMMITTER_NAME": ambient,
        "GIT_COMMITTER_EMAIL": f"{ambient}@example.com",
    }
    _ = subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "hazard"],
        env=polluted,
        capture_output=True,
        text=True,
        check=True,
        timeout=REAL_TIMEOUT,
    )
    author = subprocess.run(
        ["git", "-C", str(repo), "log", "-1", "--format=%an"],
        capture_output=True,
        text=True,
        check=True,
        timeout=REAL_TIMEOUT,
    ).stdout.strip()
    assert author == ambient, "hazard gone: repo config beat GIT_AUTHOR_NAME"


def test_scrub_git_location_vars_removes_every_override() -> None:
    dirty = {name: "polluted" for name in GIT_LOCATION_VARS}
    dirty["PATH"] = "/usr/bin"
    assert scrub_git_location_vars(dirty) == {"PATH": "/usr/bin"}


def test_scrub_git_identity_vars_removes_every_override() -> None:
    dirty = {name: "polluted" for name in GIT_IDENTITY_VARS}
    dirty["PATH"] = "/usr/bin"
    assert scrub_git_identity_vars(dirty) == {"PATH": "/usr/bin"}


def test_scrub_git_vars_removes_both_classes() -> None:
    dirty = {
        **{name: "polluted" for name in GIT_LOCATION_VARS},
        **{name: "polluted" for name in GIT_IDENTITY_VARS},
        "PATH": "/usr/bin",
    }
    assert scrub_git_vars(dirty) == {"PATH": "/usr/bin"}


def test_git_env_drops_both_classes_and_keeps_the_process_env() -> None:
    env = git_env()
    assert [name for name in (*GIT_LOCATION_VARS, *GIT_IDENTITY_VARS) if name in env] == []
    assert env.get("PATH") == os.environ.get("PATH")


def test_git_env_cannot_readmit_a_location_override(tmp_path: Path) -> None:
    """An explicit location override is scrubbed too: pinning one must not be possible."""
    env = git_env(GIT_DIR=str(tmp_path / "bogus.git"))
    assert "GIT_DIR" not in env


def test_git_env_keeps_a_deliberate_identity_override() -> None:
    """An explicit identity pin survives: authoring a fixture commit is deliberate."""
    env = git_env(GIT_AUTHOR_NAME="Fixture Author", GIT_COMMITTER_EMAIL="fixture@example.com")
    assert env["GIT_AUTHOR_NAME"] == "Fixture Author"
    assert env["GIT_COMMITTER_EMAIL"] == "fixture@example.com"


def test_no_git_override_survives_into_this_session() -> None:
    """The autouse conftest fixture must have scrubbed the live session env."""
    assert [name for name in (*GIT_LOCATION_VARS, *GIT_IDENTITY_VARS) if name in os.environ] == []


def _shell_scrubbed_git_vars() -> set[str]:
    scrubbed: set[str] = set()
    for line in CHECK_SCRIPT.read_text(encoding="utf-8").splitlines():
        if line.startswith("unset GIT_"):
            scrubbed.update(line.removeprefix("unset ").split())
    return scrubbed


def test_check_script_scrubs_every_git_override() -> None:
    """`check.sh` must scrub exactly the vars this module declares, both classes.

    One contract in two languages: a var scrubbed in tests but left set in the
    shell would still leak into every gate child the script spawns. Each list is
    asserted separately, so a drift names the class that drifted.
    """
    scrubbed = _shell_scrubbed_git_vars()
    assert set(GIT_LOCATION_VARS) <= scrubbed, "shell scrub is missing a location override"
    assert set(GIT_IDENTITY_VARS) <= scrubbed, "shell scrub is missing an identity override"
    assert scrubbed == set(GIT_LOCATION_VARS) | set(GIT_IDENTITY_VARS), (
        "shell scrub unsets a var no canonical list declares"
    )


def test_git_override_classes_stay_disjoint() -> None:
    """A var in both lists would mask a gap in the other class's scrub."""
    assert set(GIT_LOCATION_VARS) & set(GIT_IDENTITY_VARS) == set()
