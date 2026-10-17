"""Pytest fixtures for the herdr skill tests (herdr-pane and herdr-prompt helpers)."""

import json
import os
import stat
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, STUB_SOURCE, StubHarness

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import herdr_lease
from herdr_worktree import LANE_DIR_ENV, LaneAnchorError, resolve_lane_base_dir


# The live store's base, computed through `herdr_worktree.resolve_lane_base_dir` — the primitive
# that still refuses to guess — rather than the composed `herdr_lease.resolve_base_dir`: since
# #182 h3 the composed resolver falls back to a user-level store instead of raising, so only
# the primitive can answer "does a repo lane anchor resolve at all here?". With no
# `HERDR_LANE_DIR` anywhere in the environment, a process whose cwd sits inside this repository
# resolves the git common dir and lands on the shared LIVE lane store. This is one root no test
# may ever resolve to; the other is the fallback store named below.
#
# Computed behind a guard: the primitive raises `herdr_worktree.LaneAnchorError` when neither
# `HERDR_LANE_DIR` nor a git anchor resolves — an sdist, a container, a CI artifact, any cwd
# outside a working tree — and called bare at import, as it used to be, that error is a collection
# failure for the whole `tests/herdr` package. Where no live root resolves, no in-process call can
# land on one either, so the fixture below stands down on clause (a) — clause (b), the fallback
# store, is checked against the call-time environment either way.
def _resolve_live_store_base() -> Path | None:
    """This repository's live lane store base, or `None` where no anchor resolves at all."""
    try:
        return resolve_lane_base_dir(
            env={key: value for key, value in os.environ.items() if key != LANE_DIR_ENV}
        )
    except LaneAnchorError:
        return None


_LIVE_STORE_BASE: Path | None = _resolve_live_store_base()


def _under(path: Path, root: Path) -> bool:
    """Whether `path` is `root` or sits under it, by resolved equality."""
    return path == root or root in path.parents


@pytest.fixture(autouse=True)
def _never_resolve_the_live_store(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Fail a test when an in-process store call resolves a store outside its own sandbox.

    Store isolation was a convention; here it becomes a checked invariant (#182 t3b): any
    in-process `acquire_lease`/`transition`/`record_event` with neither `base_dir` nor an
    anchored `env` silently reaches the shared store — and since #182 h3, if it is not the
    repository's live lane store (clause a), it may be the operator's real user-level fallback
    store (clause b). A test this catches must be given an isolated
    `base_dir`/`HERDR_LANE_DIR`/`HOME`, never weakened. Guards in-process calls only:
    subprocess tests are isolated by `tests/herdr/stub.py`'s `base_env()`, which pins
    `HERDR_LANE_DIR` and `HOME` to `tmp_path` — the latter because the fallback store is
    home-derived, so a run that loses `HERDR_LANE_DIR` must not reach the operator's real one.

    Clause (b) compares the resolved path against `herdr_lease.fallback_lane_base` computed
    from the call-time environment (the `env` the caller passed, else `os.environ`), and
    refuses unless that path sits inside this test's own `tmp_path`. A test that deliberately
    exercises the fallback pins `HOME` to `tmp_path` and asserts the path lands under it —
    the computed danger path is then also under `tmp_path`, so the pin passes and the guard
    stands down; an unpinning call computes the operator's real home store and is refused.

    Coverage is the lease module's own name lookup, so it spans every read and write of the
    task store reached through `herdr_lease`, including `herdr_reply`'s `--auto-start` path
    (which writes a role invariant under `<lane>/.lane/invariants/`) and `herdr_git_guard`'s
    `lane_git_dir`: both now look `resolve_base_dir` up on the module at call time, so the
    guard sees their calls (#182 h3 closed the name-import hole). The split that remains:
    a module body RE-EXECUTED after the patch binds the guarded function, and that is exactly
    what `tests/in_process.py` does with `runpy.run_path` for the script-as-`__main__` copy,
    so an in-process `herdr_reply --auto-start` runs guarded.
    `tests/herdr/test_herdr_store_guard.py` pins all of this and the no-anchor stand-down.

    The fixture also resets `herdr_lease._fallback_advisory_shown` per test: the fallback
    advisory is once-per-process by design, and the suite shares one process, so without the
    reset only the first fallback test would ever see the line.
    """
    monkeypatch.setattr(herdr_lease, "_fallback_advisory_shown", False)
    live_base = _LIVE_STORE_BASE
    original = herdr_lease.resolve_base_dir

    def guarded(base_dir: Path | str | None = None, env: Mapping[str, str] | None = None) -> Path:
        resolved = original(base_dir, env=env)
        if live_base is not None:
            try:
                clashes = os.path.samefile(resolved, live_base)
            except OSError:
                clashes = resolved == live_base
            if clashes:
                pytest.fail(
                    "store isolation: an in-process lease call resolved this repository's live "
                    "lane store; pass an isolated `base_dir` or set `HERDR_LANE_DIR` in `env`"
                )
        danger = herdr_lease.fallback_lane_base(os.environ if env is None else env)
        if resolved == danger and not _under(danger, tmp_path):
            pytest.fail(
                f"store isolation: an in-process lease call resolved the user-level fallback "
                f"lane store {danger}; pass an isolated `base_dir` or pin `HERDR_LANE_DIR`/"
                f"`HOME` in `env`"
            )
        return resolved

    monkeypatch.setattr(herdr_lease, "resolve_base_dir", guarded)


@pytest.fixture
def stub_factory(tmp_path: Path) -> Callable[[Path], StubHarness]:
    """Build a `StubHarness` bound to one helper script; each test module wraps it."""

    def make(script: Path) -> StubHarness:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(exist_ok=True)
        herdr = bin_dir / "herdr"
        _ = herdr.write_text(STUB_SOURCE)
        herdr.chmod(herdr.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        harness = StubHarness(
            script, tmp_path, bin_dir, tmp_path / "calls.jsonl", tmp_path / "state.json"
        )
        _ = harness.state_path.write_text(json.dumps(DEFAULT_STATE))
        return harness

    return make
