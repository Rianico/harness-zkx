"""The live-store guard's own boundaries are pinned here (#182 t5, #182 h3).

`tests/herdr/conftest.py` resolves this repository's live lane store at collection time and wraps
`herdr_lease.resolve_base_dir` so any in-process call that lands on that root — or, since #182 h3,
on the user-level fallback store as named by the call-time environment — fails. None of that had
evidence, and every part of it can fail silently:

* A bare import-time resolution crashes the WHOLE package. With no `HERDR_LANE_DIR` and no git
  anchor — an sdist, a container, a CI artifact, any cwd outside a working tree — the primitive
  `herdr_worktree.resolve_lane_base_dir` raises `herdr_worktree.LaneAnchorError`, and collecting a
  conftest that called it bare would die on it: not one test runs, and the report says nothing
  about the store. So one case below runs the real conftest, copied, in a subprocess whose cwd is
  outside every git working tree, and demands a green collection. Copying it is the point:
  collection cannot be observed from inside the session it would have broken.
* A stand-down that quietly became a stand-everything is the opposite failure, and it would be
  invisible: no test would ever again be caught reaching the live store. So the next case runs the
  same copied conftest inside a sandbox that IS a git repository, where an unanchored in-process
  call must still be refused.
* The wrapper only covers a caller that looks the name up on the lease module at call time.
  `herdr_reply` and `herdr_git_guard` used to name-import `resolve_base_dir` at collection time and
  therefore kept running the original — a hole for the `--auto-start` invariant write and the lane
  git dir. #182 h3 closed it: both call sites now read the attribute off the module, and the last
  two cases measure that — an unanchored `--auto-start`-style call through `herdr_git_guard` is
  refused by the guard, and neither module still holds a stale binding. The half that used to read
  as a hole, a script body re-executed after the patch (`tests/in_process.py` does exactly that
  with `runpy.run_path`), binds the guarded function and IS covered.

No case here reaches the shared live lane store or the operator's real user-level store: the
subprocesses run in throwaway directories that are not this repository and never carry
`HERDR_LANE_DIR`, and every in-process case pins `HOME` or `base_dir` into its own `tmp_path`.

The last section is the pre-call complement of that guard (#182 h5): `tests/herdr/stub.py`'s
`_require_sandboxed_home` refuses a harness run whose resulting `HOME` is absent, equal to the
operator's real home, or not under the harness's `tmp_path` — so an override that drops or
relocates the `base_env()` pin fails before the state file is written and before any code runs,
rather than after a mutant's `mkdir` has already landed in `$HOME/.herdr/lane`.
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

from tests.herdr.stub import SCRIPTS_DIR, StubHarness

REPO_ROOT = SCRIPTS_DIR.parents[2]
CONFTEST = REPO_ROOT / "tests" / "herdr" / "conftest.py"

LANE_DIR_ENV = "HERDR_LANE_DIR"
# A stray `PYTEST_ADDOPTS` would inject the repo's own `-n auto` into the subprocess, and a stray
# git namespace variable would seat it back inside a working tree, defeating the premise.
_SCRUB = {LANE_DIR_ENV, "PYTEST_ADDOPTS", "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR"}

# Collected next to the copied conftest by the subprocess run. Asserting from inside that session
# is the only way to see the conftest's own state: the primitive must still raise, the composed
# resolver must land on the fallback the pinned `HOME` names (never created by a read), and the
# module must still have imported, standing down on the live-store clause rather than naming a root.
_NO_ANCHOR_PROBE = '''"""Throwaway probe: the copied conftest must collect, not crash, with no anchor."""

import os
import sys

import herdr_lease
import pytest
from herdr_worktree import LANE_DIR_ENV, LaneAnchorError, resolve_lane_base_dir


def _collected_conftest():
    collected = [
        module
        for name, module in list(sys.modules.items())
        if name.endswith("conftest") and hasattr(module, "_LIVE_STORE_BASE")
    ]
    assert collected, "the copied conftest was never imported by this collection"
    return collected[0]


def test_the_primitive_still_refuses_to_guess_without_an_anchor() -> None:
    env = {key: value for key, value in os.environ.items() if key != LANE_DIR_ENV}
    assert LANE_DIR_ENV not in env, "the probe needs the no-anchor environment, not a pinned lane"
    with pytest.raises(LaneAnchorError):
        _ = resolve_lane_base_dir(env)


def test_the_composed_resolver_falls_back_under_the_pinned_home_and_creates_nothing(
    tmp_path,
) -> None:
    # `HOME` pinned into this test's sandbox: the guard's fallback clause stands down on a
    # path it can see is the test's own, so this also pins that a deliberate fallback test passes.
    env = {"HOME": str(tmp_path), "PATH": os.environ.get("PATH", "")}
    resolved = herdr_lease.resolve_base_dir(env=env)
    assert resolved == (tmp_path / ".herdr" / "lane").resolve(), resolved
    assert tmp_path in resolved.parents
    assert not resolved.exists(), "resolution is side-effect-free: only a write creates the store"


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
    assert "3 passed" in result.stdout, (
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


def test_the_guard_covers_a_module_lookup_a_re_executed_body_and_an_unanchored_auto_start_call(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The fixture's coverage boundary, measured: call-time lookup is guarded, old bindings are gone.

    `monkeypatch.setattr(herdr_lease, "resolve_base_dir", …)` is exactly how the autouse fixture
    installs its guard. #182 h3 closed the name-import hole: `herdr_reply`'s `--auto-start`
    invariant write and `herdr_git_guard.lane_git_dir` now read the attribute off the lease
    module at call time, so the guard sees them — no stale binding survives in either module,
    and a real unanchored call through `herdr_git_guard` is refused. The other covered half:
    `tests/in_process.py:74` re-executes every herdr script body through `runpy.run_path` for
    its script-as-`__main__` copy, and a body executed after the patch re-reads the attribute.
    """
    assert not hasattr(herdr_reply, "resolve_base_dir"), (
        "the name-import hole must stay closed: a module-level binding taken at import "
        "outruns any later attribute patch"
    )
    assert not hasattr(herdr_git_guard, "resolve_base_dir"), "and neither may it survive here"

    def sentinel(base_dir: Path | str | None = None, env: Mapping[str, str] | None = None) -> Path:
        return Path("/sentinel-not-a-store")

    monkeypatch.setattr(herdr_lease, "resolve_base_dir", sentinel)

    assert herdr_lease.resolve_base_dir is sentinel, "the lease module's own lookup is wrapped"
    assert getattr(herdr_reply, "herdr_lease", None) is herdr_lease, (
        "the reply module resolves through the lease MODULE, so its call site hits the wrapper"
    )
    assert getattr(herdr_git_guard, "herdr_lease", None) is herdr_lease, "and so does the guard's"

    body = tmp_path / "re_executed_script_body.py"
    _ = body.write_text(
        "from herdr_lease import resolve_base_dir\n\nBINDING = resolve_base_dir\n",
        encoding="utf-8",
    )
    namespace = runpy.run_path(str(body))
    assert namespace["BINDING"] is sentinel, (
        "a module body re-executed after the patch must bind the guarded function"
    )


def test_an_unanchored_auto_start_style_call_through_the_git_guard_is_refused(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The hole #182 h3 closed, pinned behaviorally: the guard now sees a real cross-module call.

    `herdr_git_guard.lane_git_dir` is the other module that resolves the lane store; since h3 it
    looks `resolve_base_dir` up on the lease module at call time, so an unanchored call — no
    `base_dir`, no `HERDR_LANE_DIR`, no `HOME` pin, cwd outside every working tree — resolves the
    operator's real user-level fallback store and the autouse guard must refuse it, naming the
    store. Mutant killed: narrow the guard back to the repository's live root only, and this
    call returns quietly on the operator's home path — the safety pin for the whole h3 change.

    The refusal happens before any write; `lane_git_dir`'s `except Exception` cannot swallow it
    because `pytest.fail` raises a `BaseException`, and resolution itself creates nothing. The
    companion assertions pin the sanctioned shape: the same call with `HOME` pinned to the
    test's own sandbox resolves there, stands down from the guard, and still creates nothing.
    """
    outside = tmp_path / "outside"
    outside.mkdir()
    monkeypatch.chdir(outside)
    env = {"PATH": os.environ.get("PATH", "")}
    with pytest.raises(pytest.fail.Exception, match="store isolation"):
        _ = herdr_git_guard.lane_git_dir(env)
    pinned = herdr_git_guard.lane_git_dir({**env, "HOME": str(tmp_path)})
    assert pinned == (tmp_path / ".herdr" / "lane").resolve(), pinned
    assert not pinned.exists(), "the pinned fallback resolution created nothing either"


# ── the stub harness's pre-call home guard (#182 h5) ────────────────────────────────

_HOME_PROBE = '''"""Throwaway helper: report the `HOME` the call delivered, write nothing else."""

import os
import sys

sys.stdout.write(os.environ.get("HOME") or "<unset>")
'''

_SENTINEL = '{"sentinel": true}'


def _home_probe_harness(tmp_path: Path) -> StubHarness:
    """A `StubHarness` over a probe script whose only observable is the `HOME` it sees.

    Deliberately not `stub_factory`: a refusal test needs a `state.json` whose untouched
    sentinel content proves the guard fires before `write_state`, and a log the run never
    got a chance to seed.
    """
    script = tmp_path / "home_probe.py"
    _ = script.write_text(_HOME_PROBE, encoding="utf-8")
    state = tmp_path / "state.json"
    _ = state.write_text(_SENTINEL, encoding="utf-8")
    return StubHarness(script, tmp_path, tmp_path / "bin", tmp_path / "calls.jsonl", state)


def test_a_run_homed_on_the_operators_real_home_is_refused_before_anything_is_written(
    tmp_path: Path,
) -> None:
    """The h3 hazard turned into a check: a `HOME` naming the operator's real home dies at call time.

    Since h3 an unanchored run derives the fallback lane store `<HOME>/.herdr/lane` from
    `HOME` alone, and h3's mutation work watched a mutant's injected `mkdir` materialize
    exactly that in the real home during a sandboxed test whose override relocated `HOME`.
    Mutant killed: delete the guard, and the call returns — with the sentinel rewritten,
    because an unguarded `run` reaches `write_state` before executing. The premise is read
    from the environment, not assumed: the operator's home must sit outside this `tmp_path`
    and must not already carry `.herdr`, or the after-the-fact absence would prove nothing
    and this test would say so loudly instead of passing vacuously. The refusal's diagnosis
    is part of the contract too: the message must name the operator's real home as the
    reason. Mutant killed: collapse the three reason clauses into one string, and the
    hazard phrase still appears while the diagnosis no longer says which hazard fired.
    """
    real_home = Path.home()
    sandbox = tmp_path.resolve()
    home = real_home.resolve()
    assert home != sandbox and sandbox not in home.parents, (
        f"the premise needs the operator's home {home} outside the sandbox {sandbox}"
    )
    herdr_dir = real_home / ".herdr"
    assert not herdr_dir.exists(), (
        f"premise: {herdr_dir} predates this test; its absence after the refused call "
        f"would prove nothing about the run"
    )
    assert os.environ.get("HOME"), "the ambient HOME must name the same home Path.home() honors"
    harness = _home_probe_harness(tmp_path)

    with pytest.raises(RuntimeError) as raised:
        _ = harness.run(env={"HOME": str(real_home), "HERDR_LANE_DIR": None})

    message = str(raised.value)
    assert "fallback lane store" in message, message
    assert "is the operator's real home" in message, (
        f"the refusal must diagnose which hazard fired, not just name the store: {message}"
    )

    assert harness.state_path.read_text(encoding="utf-8") == _SENTINEL, (
        "the refusal happens before `write_state`, not just before execution"
    )
    assert not harness.log_path.exists(), "no stub call was ever made"
    assert not herdr_dir.exists(), "the refused run wrote nothing into the operator's home"


def test_a_run_that_drops_home_is_refused(tmp_path: Path) -> None:
    """`{"HOME": None}` deletes the `base_env()` pin — the exact override shape the mutant rode.

    With no `HOME` in the child environment `Path.home()` takes the passwd entry: the
    operator's real home again. Mutant killed: check the pin in `base_env()` only and
    never re-check after the caller's overrides are applied, and this call runs — the
    sentinel comes back rewritten and stdout says `<unset>`. The message must also name
    absence as the reason, not containment: collapsing the three reason clauses into one
    string keeps the hazard phrase and loses this diagnosis.
    """
    harness = _home_probe_harness(tmp_path)

    with pytest.raises(RuntimeError) as raised:
        _ = harness.run(env={"HOME": None, "HERDR_LANE_DIR": None})

    message = str(raised.value)
    assert "HOME=None" in message, message
    assert "is absent or empty" in message, (
        f"a dropped `HOME` must be refused for being absent, not as a containment failure: {message}"
    )
    assert "fallback lane store" in message, message

    assert harness.state_path.read_text(encoding="utf-8") == _SENTINEL
    assert not harness.log_path.exists()


def test_a_run_homed_on_a_directory_outside_the_sandbox_is_refused(
    tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """Another sandbox is not this sandbox: `HOME` must sit under THIS harness's `tmp_path`.

    The foreign directory is pytest's temp ROOT — an ancestor of `tmp_path`, and the
    resolved spelling `/private/var/...` on macOS. Mutant killed: accept any home that
    is "somewhere in pytest's tmp tree" or compare both containment directions, and this
    ancestor passes a guard that should only ever forgive descendants. The diagnosis must
    be containment — a directory outside the harness's `tmp_path`; collapsing the three
    reason clauses into one string survives the hazard phrase but fails this assertion.
    """
    outside = tmp_path_factory.getbasetemp()
    assert outside in tmp_path.parents, "the premise: an ancestor of the sandbox, never inside it"
    harness = _home_probe_harness(tmp_path)

    with pytest.raises(RuntimeError) as raised:
        _ = harness.run(env={"HOME": str(outside), "HERDR_LANE_DIR": None})

    message = str(raised.value)
    assert "fallback lane store" in message, message
    assert "is outside the harness tmp_path" in message, (
        f"a foreign directory must be refused for containment, never as the operator's home: {message}"
    )

    assert harness.state_path.read_text(encoding="utf-8") == _SENTINEL
    assert not harness.log_path.exists()


def test_home_pinned_into_the_sandbox_still_runs(tmp_path: Path) -> None:
    """The sanctioned shapes pass: `base_env()`'s own pin, a subdirectory, a symlinked spelling.

    Mutants killed: tighten the check to `HOME == tmp_path` and the subdirectory leg
    raises. The symlink leg inside the sandbox is NOT resolve-sensitive — `link` sits
    under `tmp_path`, so its unresolved parents already contain the sandbox and
    containment holds with or without `.resolve()`; it only pins that a symlinked home
    is a home. The spelling that refutes dropping `.resolve()` is the next case.
    """
    harness = _home_probe_harness(tmp_path)

    done = harness.run()
    assert done.returncode == 0, done.stderr
    assert done.stdout == str(tmp_path), "the default pin runs, and the probe reports it"

    nested = tmp_path / "home"
    done = harness.run(env={"HOME": str(nested)})
    assert done.returncode == 0, done.stderr
    assert done.stdout == str(nested), "a subdirectory of the sandbox is inside the sandbox"

    link = tmp_path / "link"
    os.symlink(str(tmp_path.resolve()), link)
    done = harness.run(env={"HOME": str(link)})
    assert done.returncode == 0, done.stderr
    assert done.stdout == str(link), "a symlink spelling that resolves into the sandbox runs"


def test_home_spelled_through_a_symlink_parked_outside_the_sandbox_runs(tmp_path: Path) -> None:
    """Containment is judged after `.resolve()` on BOTH sides, measured, not claimed.

    The link lives in the sandbox's parent and points at `tmp_path.resolve()`: the home
    IS the sandbox, spelled from outside it. Its raw parents never contain `tmp_path`,
    so an unresolved comparison refuses it while the guard's resolve-on-both-sides lets
    it run. Mutant killed: `home = Path(home_value)`, `sandbox = tmp_path` — every other
    case in this file passes unchanged (the inside-symlink leg's raw parents already
    contain the sandbox), and only this leg changes color. This is the real-world shape
    the rule exists for: on macOS `TMPDIR` arrives as `/var/folders/...`, the symlink
    spelling of the `/private/var/folders/...` pytest hands `tmp_path` in, so an ambient
    `HOME` derived from it names the sandbox without ever spelling it the same way.

    The probe reports the spelling verbatim: the guard judges resolved, the child keeps
    unresolved. The link is created in pytest's per-worker temp root and unlinked when
    the run finishes, unique-named and premise-checked so a pre-existing path is never
    clobbered.
    """
    link = tmp_path.parent / f"home-outside-link-{os.urandom(4).hex()}"
    assert not link.exists(), f"premise: {link} predates this test; refusing to clobber it"
    assert tmp_path not in link.parents, (
        "the premise: an unresolved containment test against this spelling must fail, "
        "or the leg proves nothing about .resolve()"
    )
    os.symlink(str(tmp_path.resolve()), link)
    harness = _home_probe_harness(tmp_path)
    try:
        done = harness.run(env={"HOME": str(link)})
    finally:
        _ = link.unlink()
    assert done.returncode == 0, done.stderr
    assert done.stdout == str(link), "the child receives the spelling the caller handed, verbatim"
