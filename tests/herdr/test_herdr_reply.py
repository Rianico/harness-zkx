"""Tests for skills/herdr/scripts/herdr_reply.py (herdr-reply helper).

Integration cases route through the shared stub `herdr`; payload assertions read back the
recorded argv, proving byte-for-byte delivery without caller context injection.
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

SCRIPT = SCRIPTS_DIR / "herdr_reply.py"

METACHARS = """COMPLETED artifacts=[foo.py] issues=[]
Do NOT expand: $HOME `whoami` "$(date)" 'single' \\backslash
```bash
echo "code fence survived"
```"""


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPT)


def payload_file(tmp_path: Path, text: str = METACHARS) -> Path:
    path = tmp_path / "result.md"
    _ = path.write_text(text, encoding="utf-8")
    return path


def test_positional_message_is_delivered_verbatim(stub: StubHarness) -> None:
    done = stub.run("orchestrator", METACHARS)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[1:4] == ["agent", "prompt", "orchestrator"]
    assert call[4] == METACHARS
    assert "Caller:" not in call[4]
    assert "reply to the caller" not in call[4]
    assert "replied to orchestrator" in done.stdout


def test_file_payload_is_delivered_verbatim(stub: StubHarness, tmp_path: Path) -> None:
    path = payload_file(tmp_path)
    done = stub.run("orchestrator", "--file", str(path))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[4] == METACHARS


def test_stdin_payload_is_delivered_verbatim(stub: StubHarness) -> None:
    done = stub.run("orchestrator", stdin=METACHARS)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[4] == METACHARS


def test_missing_target_is_rejected(stub: StubHarness) -> None:
    done = stub.run()
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "TARGET" in done.stderr
    assert stub.prompts() == []


def test_message_and_file_together_are_rejected(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("orchestrator", "msg", "--file", str(payload_file(tmp_path)))
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not both" in done.stderr
    assert stub.prompts() == []


def test_empty_payload_is_rejected(stub: StubHarness) -> None:
    done = stub.run("orchestrator", "   \n")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "empty" in done.stderr
    assert stub.prompts() == []


def test_refuses_without_herdr_env(stub: StubHarness) -> None:
    done = stub.run("orchestrator", "done", env={"HERDR_ENV": None})
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "HERDR_ENV" in done.stderr
    assert stub.calls() == []


def test_refuses_target_that_is_an_agent_kind(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "agents": [{"pane_id": "w9:p1", "name": "orch-1", "agent": "pi"}],
    }
    done = stub.run("pi", "done", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "is an agent kind" in done.stderr
    assert "live agents of this kind: orch-1" in done.stderr
    assert stub.prompts() == []


def test_delivery_reports_revision_increment(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "agent_get": {"orchestrator": {"revision": "r42", "pane_id": "w9:p1"}},
    }
    done = stub.run("orchestrator", "COMPLETED", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "replied to orchestrator" in done.stdout
    assert "revision=r42" in done.stdout


def test_dry_run_prints_argv_without_submitting(stub: StubHarness) -> None:
    done = stub.run("orchestrator", "COMPLETED", "--dry-run")
    from typing import cast

    parsed = cast(object, json.loads(done.stdout))
    assert isinstance(parsed, list)
    assert parsed[1:5] == ["agent", "prompt", "orchestrator", "COMPLETED"]


def test_wait_and_timeout_forwarded(stub: StubHarness) -> None:
    done = stub.run("orchestrator", "COMPLETED", "--wait", "--timeout", "15000")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[5:] == ["--wait", "--timeout", "15000"]


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
    assert "usage: herdr-reply" in done.stdout
