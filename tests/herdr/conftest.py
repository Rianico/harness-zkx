"""Pytest fixtures for the herdr skill tests (herdr-pane and herdr-prompt helpers)."""

import json
import stat
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, STUB_SOURCE, StubHarness

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


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
