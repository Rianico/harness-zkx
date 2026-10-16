"""The user-level fallback lane store (#182 a2a h3): determinism, visibility, laziness.

`herdr_lease.resolve_base_dir` gained a third layer: with no `HERDR_LANE_DIR` and no git
anchor it lands on `fallback_lane_base()` — one home-derived path — instead of raising
`LaneAnchorError`. These cases pin the three properties that make the layer safe:

* #229 determinism: one identical path from every working directory, so a dispatcher and a
  callee in an ad-hoc lane still share one store; `PWD` and the cwd name nothing here.
* Visibility: taking the branch prints exactly one stderr advisory per process, never one
  per call, and anchored resolutions print nothing.
* Laziness: neither resolution nor a read creates the directory; only the first write does.

Every case pins `HOME` to `tmp_path` in the `env` it passes: the fallback is home-derived,
and that is what keeps these in-process resolutions inside the test's own sandbox (the
autouse guard in `tests/herdr/conftest.py` refuses a fallback resolution that names the
operator's real home).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import herdr_lease
import pytest

LANE_DIR_ENV = "HERDR_LANE_DIR"
ADVISORY = "user-level lane store"


def _outside(tmp_path: Path) -> Path:
    """A directory that is not inside any git working tree; the caller chdirs into it."""
    outside = tmp_path / "outside-repo"
    outside.mkdir(exist_ok=True)
    return outside


def test_fallback_lane_base_is_the_same_path_from_two_working_directories_229(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Name #229: a cwd- or PWD-derived fallback re-opens the split-store incident exactly.

    A dispatcher and its callee in ad-hoc panes ran in different working directories; the
    fallback must therefore name ONE path from both, derived from the pinned `HOME` alone.
    Mutant killed: derive the fallback from `os.getcwd()` or `PWD` and the two resolutions
    below differ and the test fails.
    """
    dir_a = tmp_path / "dir-a"
    dir_b = tmp_path / "dir-b"
    dir_a.mkdir()
    dir_b.mkdir()
    env_a = {"HOME": str(tmp_path), "PATH": os.environ.get("PATH", ""), "PWD": str(dir_a)}
    env_b = {"HOME": str(tmp_path), "PATH": os.environ.get("PATH", ""), "PWD": str(dir_b)}

    monkeypatch.chdir(dir_a)
    first = herdr_lease.resolve_base_dir(env=env_a)
    monkeypatch.chdir(dir_b)
    second = herdr_lease.resolve_base_dir(env=env_b)

    assert first == second, f"#229: {first} != {second}; a cwd/PWD-derived fallback"
    assert first == (tmp_path / ".herdr" / "lane").resolve()
    assert tmp_path in first.parents, "the fallback lives under the pinned HOME, not the cwd"


def test_fallback_advisory_shows_once_per_process_and_never_for_an_anchored_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """One line when the split happens, silence when it does not, spam never.

    The flag is module-level so one process prints at most one advisory; the autouse guard
    resets it per test, and this test drives all four branch/order combinations after that
    single reset. Mutant killed: remove the advisory, and the third step below sees no line.
    """
    env = {"HOME": str(tmp_path), "PATH": os.environ.get("PATH", "")}

    anchored_repo = tmp_path / "repo"
    anchored_repo.mkdir()
    _ = subprocess.run(
        ["git", "init", "-q", str(anchored_repo)],
        env={**os.environ, "HOME": str(tmp_path)},
        capture_output=True,
        text=True,
        check=True,
    )

    monkeypatch.chdir(anchored_repo)
    _ = herdr_lease.resolve_base_dir(env=env)
    assert ADVISORY not in capsys.readouterr().err, "a git anchor never reaches the fallback"

    _ = herdr_lease.resolve_base_dir(env={**env, LANE_DIR_ENV: str(tmp_path / "lane")})
    assert ADVISORY not in capsys.readouterr().err, "an explicit HERDR_LANE_DIR names the store"

    monkeypatch.chdir(_outside(tmp_path))
    first = herdr_lease.resolve_base_dir(env=env)
    err = capsys.readouterr().err
    assert err.count(ADVISORY) == 1, err
    assert str(first) in err, "the advisory names the resolved fallback path"
    assert len([line for line in err.splitlines() if ADVISORY in line]) == 1, err

    _ = herdr_lease.resolve_base_dir(env=env)
    assert ADVISORY not in capsys.readouterr().err, "at most once per process, not per call"


def test_fallback_store_is_created_by_the_first_write_never_by_a_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Lazy creation: resolving and reading leave the path non-existent; a lease write creates it."""
    monkeypatch.chdir(_outside(tmp_path))
    env = {"HOME": str(tmp_path), "PATH": os.environ.get("PATH", "")}
    fallback = tmp_path / ".herdr" / "lane"

    _ = herdr_lease.resolve_base_dir(env=env)
    _ = herdr_lease.resolve_state_read_path(env=env)
    _ = herdr_lease.get_lease("reviewer", env=env)
    assert not fallback.exists(), "resolution and reads must not create the fallback store"

    _ = herdr_lease.acquire_lease("reviewer", "h3.md", "orchestrator", env=env)
    assert (fallback / ".lane" / "tasks.yaml").is_file(), (
        "the first write creates the store, as it already creates its parents"
    )
    assert herdr_lease.release_lease("reviewer", env=env) is True
