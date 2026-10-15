"""The live-store guard's own three boundaries are pinned here (#182 t5).

`tests/herdr/conftest.py` resolves this repository's live lane store at collection time and wraps
`herdr_lease.resolve_base_dir` so any in-process call that lands on that root fails. None of that
had evidence, and every part of it can fail silently:

* A bare import-time resolution crashes the WHOLE package. With no `HERDR_LANE_DIR` and no git
  anchor — an sdist, a container, a CI artifact, any cwd outside a working tree — the resolver
  raises `herdr_worktree.LaneAnchorError`, and collection of `tests/herdr` dies on it: not one
  test runs, and the report says nothing about the store. So one case below runs the real conftest,
  copied, in a subprocess whose cwd is outside every git working tree, and demands a green
  collection. Copying it is the point: collection cannot be observed from inside the session it
  would have broken.
* A stand-down that quietly became a stand-everything is the opposite failure, and it would be
  invisible: no test would ever again be caught reaching the live store. So the next case runs the
  same copied conftest inside a sandbox that IS a git repository, where an unanchored in-process
  call must still be refused.
* The wrapper only covers a caller that looks the name up on the lease module at call time. Two
  modules name-imported `resolve_base_dir` at collection time and therefore keep running the
  original: the fixture's docstring says so, and the last case measures that sentence instead of
  trusting it — including the half that used to read as a hole, a script body re-executed after
  the patch (`tests/in_process.py` does exactly that with `runpy.run_path`), which binds the
  guarded function and IS covered.

No case here reaches the shared live lane store: the subprocesses run in throwaway directories
that are not this repository and never carry `HERDR_LANE_DIR`, and the in-process case patches the
resolver and restores it through `monkeypatch` without resolving anything.
"""

from __future__ import annotations

import os
import runpy
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

import herdr_git_guard
import herdr_lease
import herdr_reply
import pytest

from tests.herdr.stub import SCRIPTS_DIR

REPO_ROOT = SCRIPTS_DIR.parents[2]
CONFTEST = REPO_ROOT / "tests" / "herdr" / "conftest.py"

LANE_DIR_ENV = "HERDR_LANE_DIR"
# A stray `PYTEST_ADDOPTS` would inject the repo's own `-n auto` into the subprocess, and a stray
# git namespace variable would seat it back inside a working tree, defeating the premise.
_SCRUB = {LANE_DIR_ENV, "PYTEST_ADDOPTS", "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}

# Collected next to the copied conftest by the subprocess run. Asserting from inside that session
# is the only way to see the conftest's own state: the raw resolver must raise, and the module must
# still have imported, standing down rather than naming a root.
_NO_ANCHOR_PROBE = '''"""Throwaway probe: the copied conftest must collect, not crash, with no anchor."""

import os
import sys

import herdr_lease
import pytest
from herdr_worktree import LANE_DIR_ENV, LaneAnchorError


def _collected_conftest():
    collected = [
        module
        for name, module in list(sys.modules.items())
        if name.endswith("conftest") and hasattr(module, "_LIVE_STORE_BASE")
    ]
    assert collected, "the copied conftest was never imported by this collection"
    return collected[0]


def test_the_raw_resolver_refuses_to_guess_without_an_anchor() -> None:
    env = {key: value for key, value in os.environ.items() if key != LANE_DIR_ENV}
    assert LANE_DIR_ENV not in env, "the probe needs the no-anchor environment, not a pinned lane"
    with pytest.raises(LaneAnchorError):
        _ = herdr_lease.resolve_base_dir(env=env)


def test_the_collected_conftest_stood_down_instead_of_erroring() -> None:
    assert _collected_conftest()._LIVE_STORE_BASE is None, (
        "with no anchor the live root must stay unknown, never a guessed directory"
    )
'''

# The other half of the stand-down: where an anchor DOES resolve, the guard must still bite. This
# sandbox is its own git repository, so the copied conftest names a live base and wraps the
# resolver — and an in-process call that resolves onto that base has to fail, exactly as it did
# before the lazy computation made the stand-down possible.
_ANCHORED_PROBE = '''"""Throwaway probe: with a git anchor present the copied conftest must install the guard."""

import os
import sys

import herdr_lease
import pytest


def _collected_conftest():
    collected = [
        module
        for name, module in list(sys.modules.items())
        if name.endswith("conftest") and hasattr(module, "_LIVE_STORE_BASE")
    ]
    assert collected, "the copied conftest was never imported by this collection"
    return collected[0]


def test_the_anchor_resolved_so_a_live_base_was_named() -> None:
    assert _collected_conftest()._LIVE_STORE_BASE is not None, (
        "this sandbox is a git repository, so the resolver must name its root"
    )


def test_an_unanchored_call_that_lands_on_that_base_is_refused() -> None:
    # No `base_dir`, and an `env` carrying no `HERDR_LANE_DIR`: the resolution falls to the git
    # anchor, which is the very root the guard named. `PATH` is all git needs.
    env = {"PATH": os.environ.get("PATH", "")}
    with pytest.raises(pytest.fail.Exception, match="store isolation"):
        _ = herdr_lease.resolve_base_dir(env=env)
'''


def _sandbox(tmp_path: Path, name: str, probe: str, git_init: bool) -> Path:
    """A throwaway project: the conftest under test, one probe file, and optionally its own repo.

    Without `git_init` the directory sits under the OS temp directory, outside every working tree,
    so the subprocess resolves no lane anchor at all. With it, the sandbox is the anchor. Either way
    the caller asserts the premise against git itself instead of assuming it.
    """
    sandbox = tmp_path / name
    sandbox.mkdir()
    _ = shutil.copy(CONFTEST, sandbox / "conftest.py")
    _ = (sandbox / "test_probe.py").write_text(probe, encoding="utf-8")
    if git_init:
        done = subprocess.run(
            ["git", "init", "-q", str(sandbox)],
            env=_sandbox_env(sandbox),
            capture_output=True,
            text=True,
            check=False,
        )
        assert done.returncode == 0, f"cannot seed the sandbox repo: {done.stderr}"
    return sandbox


def _sandbox_env(sandbox: Path) -> dict[str, str]:
    """The ambient environment minus every anchor, plus the repo root for `tests.herdr.stub`."""
    env = {key: value for key, value in os.environ.items() if key not in _SCRUB}
    existing = env.pop("PYTHONPATH", "")
    paths = [str(REPO_ROOT), *([existing] if existing else [])]
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env["PWD"] = str(sandbox)
    return env


def _collect_in_sandbox(sandbox: Path) -> subprocess.CompletedProcess[str]:
    """Run pytest over the sandbox: the copied conftest plus its probe, in that directory."""
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"],
        cwd=sandbox,
        env=_sandbox_env(sandbox),
        capture_output=True,
        text=True,
        check=False,
    )


def test_the_suite_still_collects_when_no_lane_anchor_resolves(tmp_path: Path) -> None:
    """No anchor must mean one guard that stands down, not a package that fails to collect.

    Mutant: compute `_LIVE_STORE_BASE` eagerly at import, as this conftest did, and this case
    fails on a non-zero subprocess exit and `ImportError while loading conftest` naming
    `herdr_worktree.LaneAnchorError` in its stderr — every test in `tests/herdr` gone, which is
    exactly the outage the guard now prevents.
    """
    sandbox = _sandbox(tmp_path, "no-anchor", _NO_ANCHOR_PROBE, git_init=False)
    outside = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=sandbox,
        env=_sandbox_env(sandbox),
        capture_output=True,
        text=True,
        check=False,
    )
    assert outside.returncode != 0, (
        f"the sandbox {sandbox} is not outside every git working tree "
        f"({outside.stdout.strip()!r}); a temp directory inside a repo cannot test the no-anchor path"
    )
    result = _collect_in_sandbox(sandbox)
    assert result.returncode == 0, (
        f"collection with no lane anchor exited {result.returncode}\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert "2 passed" in result.stdout, (
        f"the probe did not run to completion:\n{result.stdout}\n{result.stderr}"
    )


def test_the_guard_still_bites_where_an_anchor_does_resolve(tmp_path: Path) -> None:
    """Standing down without an anchor must not have become standing down in general.

    This sandbox is its own git repository, so the copied conftest names a live base and installs
    the wrapper; a call with neither `base_dir` nor an anchored `env` still fails the test that
    makes it. Mutant: return from the fixture before patching whenever the environment carries no
    `HERDR_LANE_DIR`, and the probe's `pytest.fail` never arrives.
    """
    sandbox = _sandbox(tmp_path, "anchored", _ANCHORED_PROBE, git_init=True)
    inside = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=sandbox,
        env=_sandbox_env(sandbox),
        capture_output=True,
        text=True,
        check=False,
    )
    assert inside.returncode == 0, f"the sandbox must be a working tree: {inside.stderr}"
    result = _collect_in_sandbox(sandbox)
    assert result.returncode == 0, (
        f"the guard did not behave where an anchor resolves: exited {result.returncode}\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert "2 passed" in result.stdout, f"{result.stdout}\n{result.stderr}"


def test_the_guard_covers_a_lease_lookup_and_a_re_executed_body_not_a_binding_taken_earlier(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The fixture's coverage boundary, measured: attribute lookup yes, old name binding no.

    `monkeypatch.setattr(herdr_lease, "resolve_base_dir", …)` is exactly how the autouse fixture
    installs its guard, so an immunity proved against this sentinel is immunity proved against
    that guard: under this repository's own run the lease module's attribute is the wrapper while
    `herdr_reply` and `herdr_git_guard` still hold the resolver defined in `herdr_lease`. The half
    that reads like a hole is the last assertion: `tests/in_process.py:74` re-executes every herdr
    script body through `runpy.run_path` for its script-as-`__main__` copy, and a body executed
    after the patch re-reads the attribute, so that path runs guarded.
    """
    binding = herdr_reply.resolve_base_dir
    assert binding is herdr_git_guard.resolve_base_dir, (
        "both modules name-imported one binding at collection time; that shared original is "
        "what a later attribute patch cannot reach"
    )
    assert getattr(binding, "__module__", None) == "herdr_lease", (
        "the shared binding must be the resolver itself, not a wrapper some other fixture left"
    )

    def sentinel(base_dir: Path | str | None = None, env: Mapping[str, str] | None = None) -> Path:
        return Path("/sentinel-not-a-store")

    monkeypatch.setattr(herdr_lease, "resolve_base_dir", sentinel)

    assert herdr_lease.resolve_base_dir is sentinel, "the lease module's own lookup is wrapped"
    assert herdr_reply.resolve_base_dir is binding, "a name-imported module keeps the original"
    assert herdr_git_guard.resolve_base_dir is binding, "and so does the other one"

    body = tmp_path / "re_executed_script_body.py"
    _ = body.write_text(
        "from herdr_lease import resolve_base_dir\n\nBINDING = resolve_base_dir\n",
        encoding="utf-8",
    )
    namespace = runpy.run_path(str(body))
    assert namespace["BINDING"] is sentinel, (
        "a module body re-executed after the patch must bind the guarded function"
    )
