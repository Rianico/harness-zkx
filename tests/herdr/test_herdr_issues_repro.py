"""Reproduction unit tests for Herdr issues A-E.

Follows EDD: Verifies defects in issues A-E before and after remediation.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import herdr_cli
import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness

ALL_SCRIPTS = [
    "herdr_dispatch.py",
    "herdr_reply.py",
    "herdr_prompt.py",
    "herdr_wait.py",
    "herdr_overview.py",
    "herdr_pane.py",
    "herdr_label.py",
    "herdr_transcript.py",
    "herdr_agy_bridge.py",
]


@pytest.fixture
def reply_stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPTS_DIR / "herdr_reply.py")


@pytest.fixture
def prompt_stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPTS_DIR / "herdr_prompt.py")


@pytest.fixture
def dispatch_stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPTS_DIR / "herdr_dispatch.py")


@pytest.fixture
def wait_stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPTS_DIR / "herdr_wait.py")


@pytest.fixture
def overview_stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPTS_DIR / "herdr_overview.py")


def payload_file(tmp_path: Path, text: str = "test payload") -> Path:
    path = tmp_path / "payload.md"
    _ = path.write_text(text, encoding="utf-8")
    return path


# ── Issue A: Target resolution dead-ends ─────────────────────────────────────


def test_issue_a_reply_diagnoses_label_with_no_agent(reply_stub: StubHarness) -> None:
    """When target matches a pane label but has no live agent, diagnose and provide alternatives."""
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": "/tmp",
                "label": "lens-orchestrator",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    done = reply_stub.run("lens-orchestrator", "COMPLETED", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "wM:p1N" in done.stderr
    assert "lens-orchestrator" in done.stderr
    assert "zsh" in done.stderr
    assert "herdr agent start" in done.stderr
    assert "pane send-text" in done.stderr
    assert "Queue/watch" in done.stderr or "queue" in done.stderr.lower()
    assert "Graceful abort" in done.stderr or "abort" in done.stderr.lower()
    assert (
        "Suggested recovery: herdr agent start lens-orchestrator --kind <kind> --pane wM:p1N"
        in done.stderr
    )


def test_issue_a_detects_previous_agent_kind_clue(reply_stub: StubHarness) -> None:
    """When a pane carries an agent attribute clue, the suggested recovery includes the kind."""
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": "pi",
                "agent_status": "unknown",
                "cwd": "/tmp",
                "label": "lens-orchestrator",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    done = reply_stub.run("lens-orchestrator", "COMPLETED", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert (
        "Suggested recovery: herdr agent start lens-orchestrator --kind pi --pane wM:p1N"
        in done.stderr
    )


def test_issue_a_detects_agent_kind_clue_from_title(reply_stub: StubHarness) -> None:
    """When a pane carries a title mentioning an agent kind, suggested recovery detects it."""
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "title": "claude-code session",
                "agent_status": "unknown",
                "cwd": "/tmp",
                "label": "lens-orchestrator",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    done = reply_stub.run("lens-orchestrator", "COMPLETED", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert (
        "Suggested recovery: herdr agent start lens-orchestrator --kind claude --pane wM:p1N"
        in done.stderr
    )


def test_issue_a_detects_agent_kind_clue_from_label(reply_stub: StubHarness) -> None:
    """When a pane carries a label mentioning an agent kind, suggested recovery detects it."""
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": "/tmp",
                "label": "callee-pi",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    done = reply_stub.run("callee-pi", "COMPLETED", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "Suggested recovery: herdr agent start callee-pi --kind pi --pane wM:p1N" in done.stderr


def test_issue_a_prompt_label_diagnoses_no_agent(prompt_stub: StubHarness, tmp_path: Path) -> None:
    """When --label matches a pane without a live agent, diagnose and provide alternatives."""
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": "/tmp",
                "label": "lens-orchestrator",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    done = prompt_stub.run(
        "--label", "lens-orchestrator", "--file", str(payload_file(tmp_path)), state=state
    )
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "wM:p1N" in done.stderr
    assert "zsh" in done.stderr
    assert "herdr agent start" in done.stderr
    assert "pane send-text" in done.stderr
    assert (
        "Suggested recovery: herdr agent start lens-orchestrator --kind <kind> --pane wM:p1N"
        in done.stderr
    )


# ── Issue B: Unsafe fallback path ────────────────────────────────────────────


def test_issue_b_prompt_refuses_bare_shell_pane(prompt_stub: StubHarness, tmp_path: Path) -> None:
    """Prompt helper refuses injection into a bare shell pane."""
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "w9:p2",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": None,
                "agent_status": "unknown",
                "cwd": "/tmp",
                "label": "scratch",
            }
        ],
        "process_info": {
            "w9:p2": {
                "shell_pid": 5678,
                "foreground_processes": [{"name": "zsh", "pid": 5678}],
            }
        },
    }
    done = prompt_stub.run("w9:p2", "--file", str(payload_file(tmp_path)), state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "executes prose as commands" in done.stderr
    assert prompt_stub.prompts() == []


def test_issue_b_reply_refuses_bare_shell_pane(reply_stub: StubHarness) -> None:
    """Reply helper refuses injection into a bare shell pane."""
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "w9:p2",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": None,
                "agent_status": "unknown",
                "cwd": "/tmp",
            }
        ],
        "process_info": {
            "w9:p2": {
                "shell_pid": 5678,
                "foreground_processes": [{"name": "bash", "pid": 5678}],
            }
        },
    }
    done = reply_stub.run("w9:p2", "COMPLETED", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "executes prose as commands" in done.stderr
    assert reply_stub.prompts() == []


def test_issue_b_dispatch_refuses_bare_shell_pane(
    dispatch_stub: StubHarness, tmp_path: Path
) -> None:
    """Dispatch helper refuses injection into a bare shell pane."""
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "w9:p2",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": None,
                "agent_status": "unknown",
                "cwd": "/tmp",
            }
        ],
        "process_info": {
            "w9:p2": {
                "shell_pid": 5678,
                "foreground_processes": [{"name": "fish", "pid": 5678}],
            }
        },
    }
    done = dispatch_stub.run("w9:p2", "--file", str(payload_file(tmp_path)), state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "executes prose as commands" in done.stderr
    assert dispatch_stub.prompts() == []


# ── Issue C: Weak agent observability ────────────────────────────────────────


def test_issue_c_wait_revision_zero_dispatch_and_yield_required(
    wait_stub: StubHarness,
) -> None:
    """Wait on revision-0 agent states Dispatch-&-Yield is REQUIRED, not advisory."""
    state = {
        **DEFAULT_STATE,
        "agent_get": {"a": {"agent_status": "done", "revision": "0"}},
    }
    done = wait_stub.run("a", "--interval", "0.01", "--timeout", "1000", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "REQUIRED" in done.stderr
    assert "cannot be observed to completion" in done.stderr
    assert "Dispatch-&-Yield" in done.stderr or "Dispatch & Yield" in done.stderr


def test_issue_c_prompt_wait_on_agy_agent_warns_required(
    prompt_stub: StubHarness, tmp_path: Path
) -> None:
    """Prompt with --wait targeting an agy agent warns that Dispatch-&-Yield is required."""
    state = {
        **DEFAULT_STATE,
        "agents": [{"pane_id": "w9:p1", "name": "agy-agent", "agent": "agy"}],
        "panes": [
            {
                "pane_id": "w9:p1",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": "agy",
                "agent_status": "working",
                "cwd": "/tmp",
            }
        ],
        "agent_get": {"agy-agent": {"revision": "0", "pane_id": "w9:p1"}},
    }
    done = prompt_stub.run(
        "agy-agent", "--file", str(payload_file(tmp_path)), "--wait", state=state
    )
    assert "waiting on agy agents is unreliable" in done.stderr
    assert "Dispatch-&-Yield" in done.stderr or "dispatch-and-yield" in done.stderr.lower()


def test_issue_c_dispatch_wait_on_agy_agent_warns_required(
    dispatch_stub: StubHarness, tmp_path: Path
) -> None:
    """Dispatch with --wait targeting an agy agent warns that Dispatch-&-Yield is required."""
    state = {
        **DEFAULT_STATE,
        "agents": [{"pane_id": "w9:p1", "name": "agy-agent", "agent": "agy"}],
        "panes": [
            {
                "pane_id": "w9:p1",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": "agy",
                "agent_status": "working",
                "cwd": "/tmp",
            }
        ],
        "agent_get": {"agy-agent": {"revision": "0", "pane_id": "w9:p1"}},
    }
    done = dispatch_stub.run(
        "agy-agent", "--file", str(payload_file(tmp_path)), "--wait", state=state
    )
    assert "waiting on agy agents is unreliable" in done.stderr
    assert "Dispatch-&-Yield" in done.stderr or "dispatch-and-yield" in done.stderr.lower()


# ── Issue D: Overview format surprise ────────────────────────────────────────


def test_issue_d_overview_json_flag(overview_stub: StubHarness) -> None:
    """Overview supports --json and emits valid JSON."""
    done = overview_stub.run("--json")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    parsed = json.loads(done.stdout)
    assert "scope" in parsed
    assert "workspaces" in parsed
    assert "pane_total" in parsed


def test_issue_d_overview_format_json(overview_stub: StubHarness) -> None:
    """Overview supports --format json and emits valid JSON."""
    done = overview_stub.run("--format", "json")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    parsed = json.loads(done.stdout)
    assert "scope" in parsed
    assert "workspaces" in parsed


def test_issue_d_overview_yaml_header_comment(overview_stub: StubHarness) -> None:
    """Overview YAML output includes top guidance header comment."""
    done = overview_stub.run()
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    first_line = done.stdout.splitlines()[0]
    assert first_line.startswith(
        "# herdr-overview (format: YAML; pass --json for JSON, --format table for table)"
    )


# ── Issue E: Method-constraint discoverability ────────────────────────────────


@pytest.mark.parametrize("script_name", ALL_SCRIPTS)
def test_issue_e_scripts_help_epilogues(
    stub_factory: Callable[[Path], StubHarness], script_name: str
) -> None:
    """All 9 helper scripts include the method-constraint reminder in their --help epilogue."""
    stub = stub_factory(SCRIPTS_DIR / script_name)
    done = stub.run("--help")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    normalized = " ".join(done.stdout.split())
    assert (
        "Always use harness helper scripts in skills/herdr/scripts/, never bare herdr CLI for agent communication or pane control."
        in normalized
    )
