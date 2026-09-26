"""Tests for skills/herdr/scripts/herdr_dispatch.py (herdr-dispatch helper).

Integration cases route through the shared stub `herdr`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import herdr_cli
import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness

SCRIPT = SCRIPTS_DIR / "herdr_dispatch.py"


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPT)


def payload_file(tmp_path: Path, text: str = "TICKET BODY") -> Path:
    path = tmp_path / "ticket.md"
    _ = path.write_text(text, encoding="utf-8")
    return path


def test_dispatch_requires_file(stub: StubHarness) -> None:
    done = stub.run("worker")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "--file" in done.stderr
    assert stub.prompts() == []


def test_dispatch_injects_caller_context_and_reply_contract(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "do this")), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[1:4] == ["agent", "prompt", "reviewer"]
    text = call[4]
    assert text.startswith("Caller: pane=w9:p1 agent=reviewer")
    assert "Herdr: see skill ~/.agents/skills/herdr/SKILL.md" in text
    assert "\n\ndo this\n\n" in text
    assert (
        'uv run ~/.agents/skills/herdr/scripts/herdr_reply.py reviewer "<STATUS> <artifacts> <issues>"'
        in text
    )


def test_dispatch_refuses_agent_kind(stub: StubHarness, tmp_path: Path) -> None:
    state = {
        **DEFAULT_STATE,
        "agents": [{"pane_id": "w9:p2", "name": "t7-impl", "agent": "qodercli"}],
    }
    done = stub.run("qodercli", "--file", str(payload_file(tmp_path)), state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "is an agent kind" in done.stderr
    assert "live agent names: t7-impl" in done.stderr
    assert stub.prompts() == []


def test_dispatch_reports_delivery_revision(stub: StubHarness, tmp_path: Path) -> None:
    state = {
        **DEFAULT_STATE,
        "agent_get": {"reviewer": {"revision": "r99", "pane_id": "w9:p1"}},
    }
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "prompted reviewer" in done.stdout
    assert "revision=r99" in done.stdout


def test_dispatch_dry_run_prints_argv(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "dry")), "--dry-run")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    from typing import cast

    parsed = cast(object, json.loads(done.stdout))
    assert isinstance(parsed, list)
    assert parsed[3] == "reviewer"
    assert "Caller: pane=" in str(parsed[4])


def test_pep723_metadata_precedes_docstring() -> None:
    header = SCRIPT.read_text().split('"""', 1)[0]
    assert header.startswith("#!/usr/bin/env python3\n")
    assert "# /// script" in header
    assert 'requires-python = ">=3.14"' in header
    assert "dependencies = []" in header
    assert header.rstrip().endswith("# ///")


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv is required for the PEP 723 runner")
def test_uv_run_help_executes_without_path_configuration(tmp_path: Path) -> None:
    done = subprocess.run(
        ["uv", "run", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        env={"HOME": os.environ.get("HOME", ""), "PATH": os.environ.get("PATH", "")},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "usage: herdr-dispatch" in done.stdout
