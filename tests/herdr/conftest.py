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
from herdr_worktree import LANE_DIR_ENV

# The live store's base, computed through `herdr_lease`'s own resolver rather than a
# hardcoded path: with no `HERDR_LANE_DIR` anywhere in the environment, a process whose cwd
# sits inside this repository resolves the git common dir and lands on the shared LIVE lane
# store. This is the one root no test may ever resolve to.
_LIVE_STORE_BASE = herdr_lease.resolve_base_dir(
    env={key: value for key, value in os.environ.items() if key != LANE_DIR_ENV}
)


@pytest.fixture(autouse=True)
def _never_resolve_the_live_store(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail a test when an in-process store call resolves to this repository's live lane store.

    Store isolation was a convention; here it becomes a checked invariant (#182 t3b): any
    in-process `acquire_lease`/`transition`/`record_event` with neither `base_dir` nor an
    anchored `env` silently reaches the shared store. A test this catches must be given an
    isolated `base_dir`/`HERDR_LANE_DIR`, never weakened. Guards in-process calls only:
    subprocess tests are isolated by `tests/herdr/stub.py`'s `base_env()`, which pins
    `HERDR_LANE_DIR` to `tmp_path`.
    """
    original = herdr_lease.resolve_base_dir

    def guarded(base_dir: Path | str | None = None, env: Mapping[str, str] | None = None) -> Path:
        resolved = original(base_dir, env=env)
        try:
            clashes = os.path.samefile(resolved, _LIVE_STORE_BASE)
        except OSError:
            clashes = resolved == _LIVE_STORE_BASE
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
