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
from herdr_worktree import LANE_DIR_ENV, LaneAnchorError


# The live store's base, computed through `herdr_lease`'s own resolver rather than a hardcoded
# path: with no `HERDR_LANE_DIR` anywhere in the environment, a process whose cwd sits inside this
# repository resolves the git common dir and lands on the shared LIVE lane store. This is the one
# root no test may ever resolve to.
#
# Computed behind a guard: the resolver raises `herdr_worktree.LaneAnchorError` when neither
# `HERDR_LANE_DIR` nor a git anchor resolves — an sdist, a container, a CI artifact, any cwd
# outside a working tree — and called bare at import, as it used to be, that error is a collection
# failure for the whole `tests/herdr` package. Where no live root resolves, no in-process call can
# land on one either, so the fixture below stands down instead.
def _resolve_live_store_base() -> Path | None:
    """This repository's live lane store base, or `None` where no anchor resolves at all."""
    try:
        return herdr_lease.resolve_base_dir(
            env={key: value for key, value in os.environ.items() if key != LANE_DIR_ENV}
        )
    except LaneAnchorError:
        return None


_LIVE_STORE_BASE: Path | None = _resolve_live_store_base()


@pytest.fixture(autouse=True)
def _never_resolve_the_live_store(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail a test when an in-process store call resolves to this repository's live lane store.

    Store isolation was a convention; here it becomes a checked invariant (#182 t3b): any
    in-process `acquire_lease`/`transition`/`record_event` with neither `base_dir` nor an
    anchored `env` silently reaches the shared store. A test this catches must be given an
    isolated `base_dir`/`HERDR_LANE_DIR`, never weakened. Guards in-process calls only:
    subprocess tests are isolated by `tests/herdr/stub.py`'s `base_env()`, which pins
    `HERDR_LANE_DIR` to `tmp_path`.

    Coverage is the lease module's own name lookup, so it spans every read and write of the
    task store reached through `herdr_lease`. The two modules that name-imported
    `resolve_base_dir` keep the original binding, because the test modules import them at
    collection time and a later attribute patch cannot reach a binding they already took:
    `herdr_git_guard` (lane git dir, read-only) and `herdr_reply`'s `--auto-start` path, which
    writes a role invariant under `<lane>/.lane/invariants/` — a lane file, not `tasks.yaml`,
    and no test reaches it without an anchored `env`. The split is not universal: a module body
    RE-EXECUTED after the patch binds the guarded function, and that is exactly what
    `tests/in_process.py` does with `runpy.run_path` for the script-as-`__main__` copy, so an
    in-process `herdr_reply --auto-start` runs guarded. `tests/herdr/test_herdr_store_guard.py`
    pins both halves and the no-anchor stand-down.
    """
    live_base = _LIVE_STORE_BASE
    if live_base is None:
        return
    original = herdr_lease.resolve_base_dir

    def guarded(base_dir: Path | str | None = None, env: Mapping[str, str] | None = None) -> Path:
        resolved = original(base_dir, env=env)
        try:
            clashes = os.path.samefile(resolved, live_base)
        except OSError:
            clashes = resolved == live_base
        if clashes:
            pytest.fail(
                "store isolation: an in-process lease call resolved this repository's live "
                "lane store; pass an isolated `base_dir` or set `HERDR_LANE_DIR` in `env`"
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
