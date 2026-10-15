"""Tests for skills/herdr/scripts/herdr_prompt.py (herdr-prompt helper).

Integration cases route through the shared stub `herdr`; payload assertions read back the
recorded argv, which is what proves byte-for-byte delivery.
"""

import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import herdr_agent
import herdr_bootstrap
import herdr_cli
import herdr_envelope
import herdr_prompt
import herdr_wait
import pytest
import yaml

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness

SCRIPT = SCRIPTS_DIR / "herdr_prompt.py"

# The delivered envelope's `status.timestamp` grammar: bare ISO-8601 UTC, no brackets.
TIMESTAMP_RE = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"

METACHARS = """Do NOT expand: $HOME `whoami` "$(date)" 'single' \\backslash
line2 → unicode ✓
```bash
echo "code fence survived"
```"""


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPT)


def payload_file(tmp_path: Path, text: str = METACHARS) -> Path:
    path = tmp_path / "payload.md"
    _ = path.write_text(text, encoding="utf-8")
    return path


# ── unit: pure helpers ──────────────────────────────────────────────────────────────


def test_settled_state_reads_agent_status() -> None:
    raw = '{"result":{"agent":{"agent_status":"blocked"},"type":"agent_prompted"}}'
    assert herdr_prompt.settled_state(raw) == "blocked"


def test_settled_state_is_none_without_agent() -> None:
    assert herdr_prompt.settled_state('{"result":{}}') is None


def test_build_prompt_argv_orders_text_before_flags() -> None:
    argv = herdr_prompt.build_prompt_argv(
        "herdr", "reviewer", "hi", wait=True, until=["idle", "done"], timeout=120000
    )
    assert argv == [
        "herdr",
        "agent",
        "prompt",
        "reviewer",
        "hi",
        "--wait",
        "--until",
        "idle",
        "--until",
        "done",
        "--timeout",
        "120000",
    ]


def test_build_prompt_argv_omits_flags_by_default() -> None:
    argv = herdr_prompt.build_prompt_argv(
        "herdr", "reviewer", "hi", wait=False, until=[], timeout=None
    )
    assert argv == ["herdr", "agent", "prompt", "reviewer", "hi"]


def test_build_prompt_argv_rejects_non_positive_timeout() -> None:
    with pytest.raises(herdr_prompt.UsageError, match="not positive"):
        _ = herdr_prompt.build_prompt_argv("herdr", "r", "hi", wait=True, until=[], timeout=0)


def test_read_payload_reads_file_verbatim(tmp_path: Path) -> None:
    assert herdr_prompt.read_payload(str(payload_file(tmp_path))) == METACHARS


def test_read_payload_rejects_blank(tmp_path: Path) -> None:
    path = tmp_path / "blank.md"
    _ = path.write_text("   \n")
    with pytest.raises(herdr_prompt.UsageError, match="empty"):
        _ = herdr_prompt.read_payload(str(path))


def test_read_payload_rejects_nul(tmp_path: Path) -> None:
    path = tmp_path / "nul.md"
    _ = path.write_bytes(b"a\x00b")
    with pytest.raises(herdr_prompt.UsageError, match="NUL"):
        _ = herdr_prompt.read_payload(str(path))


def test_read_payload_rejects_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "binary.md"
    _ = path.write_bytes(b"\xff\xfebad")
    with pytest.raises(herdr_prompt.UsageError, match="UTF-8"):
        _ = herdr_prompt.read_payload(str(path))


def test_read_payload_reports_missing_file(tmp_path: Path) -> None:
    with pytest.raises(herdr_prompt.UsageError, match="cannot read payload"):
        _ = herdr_prompt.read_payload(str(tmp_path / "nope.md"))


def test_message_positional_is_refused_as_a_target_not_a_payload(stub: StubHarness) -> None:
    """Issue #212: a message passed as a positional must be reported as a bad TARGET."""
    done = stub.run("reviewer", "What single word did I ask you to remember?", stdin="")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert stub.prompts() == []
    assert "cannot be an agent name or pane id" in done.stderr
    assert "--file PATH or stdin" in done.stderr
    assert "payload is empty" not in done.stderr


def test_read_payload_refuses_interactive_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    class Tty:
        def isatty(self) -> bool:
            return True

    monkeypatch.setattr(herdr_prompt.sys, "stdin", Tty())
    with pytest.raises(herdr_prompt.UsageError, match="terminal"):
        _ = herdr_prompt.read_payload(None)


# ── integration: guards and preconditions ───────────────────────────────────────────


def test_refuses_without_herdr_env(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), env={"HERDR_ENV": None})
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "HERDR_ENV" in done.stderr
    assert stub.calls() == []


def test_refuses_when_herdr_missing_from_path(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        env={"PATH": "/nonexistent", "HERDR_BIN_PATH": None},
    )
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not found on PATH" in done.stderr


def test_missing_file_is_usage_error(stub: StubHarness) -> None:
    done = stub.run("reviewer", "--file", "/nonexistent/payload.md")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "cannot read payload" in done.stderr
    assert stub.prompts() == []


def test_blank_payload_is_rejected_without_prompting(stub: StubHarness) -> None:
    done = stub.run("reviewer", stdin="   \n")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "empty" in done.stderr
    assert stub.prompts() == []


def test_non_positive_timeout_is_rejected(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), "--timeout", "0")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not positive" in done.stderr
    assert stub.prompts() == []


# ── integration: byte-exact delivery ────────────────────────────────────────────────


def test_file_payload_is_delivered_byte_for_byte(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), "--no-caller-context")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[3] == "reviewer"
    assert call[4] == METACHARS
    assert "--wait" not in call


def test_stdin_dash_payload_is_delivered_verbatim(stub: StubHarness) -> None:
    done = stub.run("reviewer", "--file", "-", "--no-caller-context", stdin=METACHARS)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts()[0][4] == METACHARS


def test_bare_stdin_payload_is_delivered_verbatim(stub: StubHarness) -> None:
    done = stub.run("reviewer", "--no-caller-context", stdin=METACHARS)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts()[0][4] == METACHARS


def test_wait_until_and_timeout_follow_the_text(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path, "short")),
        "--wait",
        "--until",
        "idle",
        "--until",
        "done",
        "--timeout",
        "120000",
        "--no-caller-context",
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[1:5] == ["agent", "prompt", "reviewer", "short"]
    assert call[5:] == ["--wait", "--until", "idle", "--until", "done", "--timeout", "120000"]


def test_summary_reports_byte_count_and_state(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer", "--file", str(payload_file(tmp_path, "hello")), "--wait", "--no-caller-context"
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "prompted reviewer" in done.stdout
    assert "bytes=5" in done.stdout
    assert "state=idle" in done.stdout


def test_json_prints_raw_response(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")), "--json")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert json.loads(done.stdout)["result"]["agent"]["agent_status"] == "idle"


def test_dry_run_prints_exact_argv_without_prompting(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        "--dry-run",
        "--json",
        "--wait",
        "--no-caller-context",
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    argv: list[str] = json.loads(done.stdout)
    assert argv[1:5] == ["agent", "prompt", "reviewer", METACHARS]
    assert argv[-1] == "--wait"


# ── integration: outcome taxonomy ───────────────────────────────────────────────────


def test_rejection_while_blocked_exits_blocked(stub: StubHarness, tmp_path: Path) -> None:
    error = {"code": "agent_blocked", "message": "agent reviewer is blocked"}
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        state={**DEFAULT_STATE, "prompt_error": error},
    )
    assert done.returncode == herdr_cli.EXIT_BLOCKED
    assert "blocked" in done.stderr
    assert "Traceback" not in done.stderr


def test_wait_settling_on_blocked_exits_blocked(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        "--wait",
        state={**DEFAULT_STATE, "prompt_status": "blocked"},
    )
    assert done.returncode == herdr_cli.EXIT_BLOCKED
    assert "state=blocked" in done.stdout


def test_other_herdr_error_exits_herdr(stub: StubHarness, tmp_path: Path) -> None:
    error = {"code": "agent_not_found", "message": "agent target reviewer not found"}
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        state={**DEFAULT_STATE, "prompt_error": error},
    )
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "not found" in done.stderr
    assert "Traceback" not in done.stderr


# ── integration: --label resolves what a person reads off the pane ──────────────────


def ambiguous_state() -> dict[str, object]:
    panes = [
        {
            "pane_id": pane_id,
            "tab_id": "w9:t1",
            "workspace_id": "w9",
            "agent": agent,
            "agent_status": "idle",
            "cwd": f"/tmp/{pane_id}",
            "label": "review",
        }
        for pane_id, agent in (("w9:p1", "pi"), ("w9:p2", "agy"))
    ]
    return {**DEFAULT_STATE, "panes": panes}


def test_label_resolves_to_the_pane_id(stub: StubHarness, tmp_path: Path) -> None:
    state = {
        **DEFAULT_STATE,
        "panes": [
            DEFAULT_STATE["panes"][0],
            {**DEFAULT_STATE["panes"][1], "agent": "pi", "agent_status": "idle"},
        ],
    }
    done = stub.run(
        "--label",
        "scratch pad",
        "--file",
        str(payload_file(tmp_path, "hi")),
        "--no-caller-context",
        state=state,
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.startswith("prompted w9:p2  bytes=2")
    (call,) = stub.prompts()
    assert call[3] == "w9:p2"


def test_label_dry_run_shows_the_resolved_pane_id(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "--label",
        "scratch pad",
        "--file",
        str(payload_file(tmp_path, "hi")),
        "--dry-run",
        "--json",
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    assert json.loads(done.stdout)[3] == "w9:p2"


def test_an_ambiguous_label_lists_the_candidates(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "--label",
        "review",
        "--file",
        str(payload_file(tmp_path, "hi")),
        state=ambiguous_state(),
    )
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "ambiguous" in done.stderr
    assert "w9:p1" in done.stderr
    assert "w9:p2" in done.stderr
    assert stub.prompts() == []


def test_an_unknown_label_is_rejected(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("--label", "nope", "--file", str(payload_file(tmp_path, "hi")))
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "no pane carries the label" in done.stderr
    assert stub.prompts() == []


def test_target_and_label_together_are_rejected(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer", "--label", "scratch pad", "--file", str(payload_file(tmp_path, "hi"))
    )
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not both" in done.stderr


def test_an_explicit_target_alone_is_accepted(stub: StubHarness) -> None:
    done = stub.run("reviewer", stdin="hi")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts()[0][3] == "reviewer"


def test_a_missing_target_is_rejected_before_reading_the_payload(stub: StubHarness) -> None:
    done = stub.run()
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "pass TARGET" in done.stderr
    assert stub.prompts() == []


# ── metadata: PEP 723 conformance ────────────────────────────────────────────────────


def test_pep723_metadata_precedes_docstring() -> None:
    header = SCRIPT.read_text().split('"""', 1)[0]
    assert header.startswith("#!/usr/bin/env python3\n")
    assert "# /// script" in header
    assert 'requires-python = ">=3.14"' in header
    assert 'dependencies = ["pyyaml"]' in header
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
    assert "usage: herdr-prompt" in done.stdout


# ── integration: broadcast, --no-wait, and wait-timeout ─────────────────────────


def test_broadcast_delivers_same_payload_to_every_target(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "callee1",
        "callee2",
        "--file",
        str(payload_file(tmp_path, "hi")),
        "--no-wait",
        "--no-caller-context",
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (first, second) = stub.prompts()
    assert (first[3], second[3]) == ("callee1", "callee2")
    assert first[4] == second[4] == "hi"
    assert "prompted callee1" in done.stdout
    assert "prompted callee2" in done.stdout


def test_wait_and_no_wait_together_are_rejected(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")), "--wait", "--no-wait")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not both" in done.stderr
    assert stub.prompts() == []


def test_duplicate_broadcast_targets_are_rejected(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "reviewer", "--file", str(payload_file(tmp_path, "hi")))
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "duplicate" in done.stderr
    assert stub.prompts() == []


def test_prompt_wait_timeout_reports_exit_4_and_advises_herdr_wait(
    stub: StubHarness, tmp_path: Path
) -> None:
    error = {"code": "timeout", "message": "wait timed out after 120000ms"}
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path, "hi")),
        "--wait",
        "--timeout",
        "120000",
        state={**DEFAULT_STATE, "prompt_error": error},
    )
    assert done.returncode == herdr_prompt.EXIT_WAIT_TIMEOUT
    assert done.returncode != herdr_cli.EXIT_HERDR
    assert "prompt delivered to reviewer" in done.stderr
    assert "Yield turn and await reply callback" in done.stderr
    assert "herdr-wait reviewer" in done.stderr
    assert "instead of resubmitting" in done.stderr


def test_broadcast_blocked_reports_exit_blocked(stub: StubHarness, tmp_path: Path) -> None:
    error = {"code": "agent_blocked", "message": "agent reviewer is blocked"}
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path, "hi")),
        state={**DEFAULT_STATE, "prompt_error": error},
    )
    assert done.returncode == herdr_cli.EXIT_BLOCKED
    assert "need human input" in done.stderr


def test_broadcast_dry_run_prints_one_argv_per_target(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "callee1",
        "callee2",
        "--file",
        str(payload_file(tmp_path, "hi")),
        "--dry-run",
        "--json",
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    argv_lines: list[list[str]] = [json.loads(line) for line in done.stdout.splitlines()]
    assert [argv[3] for argv in argv_lines] == ["callee1", "callee2"]


# ── integration: caller context (#106, #119) ─────────────────────────────────────────


def test_build_resume_cmd_for_all_supported_kinds() -> None:
    # agy
    assert herdr_prompt.build_resume_cmd("agy", "uuid-123") == "agy --conversation=uuid-123"
    assert herdr_prompt.build_resume_cmd("agy", None) is None

    # pi
    assert (
        herdr_prompt.build_resume_cmd("pi", "/path/to/session.jsonl")
        == "pi --session /path/to/session.jsonl"
    )
    assert herdr_prompt.build_resume_cmd("pi", "sess-id-456") == "pi --session sess-id-456"
    assert herdr_prompt.build_resume_cmd("pi", None) is None

    # claude
    assert herdr_prompt.build_resume_cmd("claude", "sess-789") == "claude --resume sess-789"
    assert herdr_prompt.build_resume_cmd("claude", None) is None

    # qodercli / qoderclicn
    assert herdr_prompt.build_resume_cmd("qodercli", None) == "qodercli resume"
    assert herdr_prompt.build_resume_cmd("qoderclicn", None) == "qoderclicn resume"
    assert herdr_prompt.build_resume_cmd("qodercli", "any") == "qodercli resume"

    # unsupported or None
    assert herdr_prompt.build_resume_cmd("gemini", "123") is None
    assert herdr_prompt.build_resume_cmd(None, "123") is None
    assert herdr_prompt.build_resume_cmd(None, None) is None


def test_scalar_quotes_only_when_yaml_would_mangle() -> None:
    assert herdr_prompt._scalar("w1:p1") == "w1:p1"
    assert herdr_prompt._scalar("/path/to/session.jsonl") == "/path/to/session.jsonl"
    assert (
        herdr_prompt._scalar("pi --session /path/to/session.jsonl")
        == '"pi --session /path/to/session.jsonl"'
    )
    assert herdr_prompt._scalar("review pane X") == '"review pane X"'
    assert herdr_prompt._scalar("a#b") == '"a#b"'
    assert herdr_prompt._scalar("it's") == '"it\'s"'
    assert herdr_prompt._scalar('say "hi"') == '"say \\"hi\\""'
    assert herdr_prompt._scalar("back\\slash x") == '"back\\\\slash x"'
    assert herdr_prompt._scalar("") == ""


def test_envelope_renders_sender_alone_when_nothing_else_is_known() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", label="orchestrator", agent="orchestrator")
    block = _frontmatter(herdr_prompt.render_envelope(sender))
    assert block["id"] == ""
    assert block["context_id"] == ""
    assert set(block) == {"id", "context_id", "status", "metadata"}
    assert block["status"]["state"] == "TASK_STATE_WORKING"
    assert block["metadata"] == {"sender": "orchestrator@w1:p1"}


def test_envelope_renders_position_receiver_and_group() -> None:
    sender = herdr_prompt.CallerContext(
        pane_id="w1:p1",
        label="orchestrator",
        agent="orchestrator",
        kind="pi",
        session_id="/tmp/session.jsonl",
        resume_cmd="pi --session /tmp/session.jsonl",
    )
    rendered = herdr_prompt.render_envelope(
        sender,
        receiver="impl-1",
        group_members=["orchestrator@w1:p1", "impl-1@w1:p3"],
    )
    envelope = herdr_prompt.parse_envelope(rendered)
    assert envelope is not None
    assert envelope.sender == "orchestrator@w1:p1"
    assert envelope.receiver == "impl-1"
    assert envelope.group == ("orchestrator@w1:p1", "impl-1@w1:p3")
    assert envelope.context_id == "/tmp/session.jsonl"
    assert not envelope.cwd and not envelope.resume


def test_envelope_renders_recovery_metadata_only_when_included() -> None:
    sender = herdr_prompt.CallerContext(
        pane_id="w1:p1",
        label="orchestrator",
        agent="orchestrator",
        kind="pi",
        cwd="/path/to/my project",
        session_id="/tmp/session.jsonl",
        resume_cmd="pi --session /tmp/session.jsonl",
    )
    envelope = herdr_prompt.parse_envelope(
        herdr_prompt.render_envelope(sender, include_recovery=True)
    )
    assert envelope is not None
    assert envelope.cwd == "/path/to/my project"
    assert envelope.resume == "pi --session /tmp/session.jsonl"
    trimmed = herdr_prompt.parse_envelope(herdr_prompt.render_envelope(sender))
    assert trimmed is not None
    assert not trimmed.cwd and not trimmed.resume


def test_envelope_renders_a_resolved_receiver_as_an_address() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", label="orchestrator", agent="orchestrator")
    receiver = herdr_prompt.CallerContext(
        pane_id="w1:p3", label="impl-1", agent="impl-1", kind="agy", tab_id="w1:t1"
    )
    envelope = herdr_prompt.parse_envelope(herdr_prompt.render_envelope(sender, receiver=receiver))
    assert envelope is not None
    assert envelope.sender == "orchestrator@w1:p1"
    assert envelope.receiver == "impl-1@w1:p3"
    assert "tab w1:t1" not in herdr_prompt.render_envelope(sender, receiver=receiver)


def test_envelope_omits_cwd_and_resume_by_default() -> None:
    sender = herdr_prompt.CallerContext(
        pane_id="w1:p1",
        label="orchestrator",
        agent="orchestrator",
        tab_id="w1:t1",
        cwd="/path/to/my project",
        kind="pi",
        session_id="/tmp/session.jsonl",
        resume_cmd="pi --session /tmp/session.jsonl",
    )
    rendered = herdr_prompt.render_envelope(sender, tab_id=sender.tab_id)
    assert "Cwd:" not in rendered
    assert "Resume:" not in rendered
    envelope = herdr_prompt.parse_envelope(rendered)
    assert envelope is not None
    assert envelope.task_group == "w1:t1"
    assert not envelope.cwd and not envelope.resume


def test_envelope_keeps_a_label_that_differs_from_the_agent_name() -> None:
    sender = herdr_prompt.CallerContext(
        pane_id="w1:p2",
        label="callee",
        agent="t7-impl",
        kind="qodercli",
        resume_cmd="qodercli resume",
    )
    rendered = herdr_prompt.render_envelope(sender)
    envelope = herdr_prompt.parse_envelope(rendered)
    assert envelope is not None
    assert envelope.sender == "t7-impl@w1:p2"
    assert "Runtime:" not in rendered


def test_sender_ref_only_ever_uses_the_agent_name_as_the_target_token() -> None:
    labelled_only = herdr_prompt.CallerContext(pane_id="w9:p2", label="scratch pad")
    spare_label = herdr_prompt.CallerContext(pane_id="w1:p1", label="callee", agent="impl-1")
    assert herdr_prompt.sender_ref(labelled_only) == 'w9:p2 - label "scratch pad"'
    assert herdr_prompt.sender_ref(spare_label) == "impl-1@w1:p1 - label callee"


def test_envelope_omits_unknown_fields_never_invents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(herdr_envelope, "utc_stamp", lambda: "2026-01-02T03:04:05.678Z")
    sender = herdr_prompt.CallerContext(pane_id="w9:p1", agent="reviewer")
    assert herdr_prompt.render_envelope(sender).splitlines() == [
        "---",
        "id: ''",
        "context_id: ''",
        "status:",
        "  state: TASK_STATE_WORKING",
        "  timestamp: '2026-01-02T03:04:05.678Z'",
        "metadata:",
        "  sender: reviewer@w9:p1",
        "---",
    ]


def test_envelope_renders_correlation_metadata_from_the_params() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", agent="orchestrator")
    rendered = herdr_prompt.render_envelope(
        sender,
        ticket_id="#182-herdr-msg-enhance",
        task_id="#182-herdr-msg-enhance#full-stack",
        task_group="full-stack",
        tab_id="w1:t2",
    )
    envelope = herdr_prompt.parse_envelope(rendered)
    assert envelope is not None
    assert envelope.id == "#182-herdr-msg-enhance#full-stack"
    assert envelope.ticket_id == "#182-herdr-msg-enhance"
    assert envelope.task_group == "full-stack@w1:t2"
    assert rendered.splitlines()[0] == "---"


def test_envelope_renders_task_group_alone_or_tab_alone() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", agent="orchestrator")
    only_group = herdr_prompt.parse_envelope(
        herdr_prompt.render_envelope(sender, task_group="full-stack")
    )
    assert only_group is not None
    assert only_group.task_group == "full-stack"
    only_tab = herdr_prompt.parse_envelope(herdr_prompt.render_envelope(sender, tab_id="w1:t2"))
    assert only_tab is not None
    assert only_tab.task_group == "w1:t2"


def test_envelope_renders_in_reply_to() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", agent="orchestrator")
    rendered = herdr_prompt.render_envelope(sender, in_reply_to="#182-herdr-msg-enhance#full-stack")
    assert "Hierarchy:" not in rendered
    envelope = herdr_prompt.parse_envelope(rendered)
    assert envelope is not None
    assert envelope.in_reply_to == "#182-herdr-msg-enhance#full-stack"


def test_envelope_omits_correlation_and_recovery_metadata_when_params_absent() -> None:
    sender = herdr_prompt.CallerContext(
        pane_id="w1:p1", agent="orchestrator", cwd="/tmp/work", resume_cmd="pi --resume"
    )
    block = _frontmatter(herdr_prompt.render_envelope(sender, include_recovery=False))
    assert block["metadata"] == {"sender": "orchestrator@w1:p1"}
    assert "Ticket-ID:" not in str(block)
    assert "In-Reply-To:" not in str(block)


def _frontmatter(block: str) -> dict[str, Any]:
    """Read the fenced frontmatter with a generic YAML reader — the ADR's compatibility promise."""
    lines = block.splitlines()
    assert lines[0] == "---" and lines[-1] == "---", lines
    parsed = yaml.safe_load("\n".join(lines[1:-1]))
    assert isinstance(parsed, dict)
    return cast("dict[str, Any]", parsed)


def test_envelope_group_renders_as_a_yaml_sequence() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", agent="orchestrator")
    rendered = herdr_prompt.render_envelope(
        sender, group_members=["orchestrator@w1:p1", "impl-1@w1:p3"]
    )
    block = _frontmatter(rendered)
    assert block["metadata"]["group"] == ["orchestrator@w1:p1", "impl-1@w1:p3"]


def test_envelope_addresses_the_sender_and_never_leaks_the_label() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", label="review\npane\tX", agent="reviewer")
    assert herdr_prompt.sender_ref(sender) == 'reviewer@w1:p1 - label "review pane X"'
    block = _frontmatter(herdr_prompt.render_envelope(sender))
    assert block["metadata"] == {"sender": "reviewer@w1:p1"}


def test_envelope_drops_a_blank_label() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", label="   ", agent="reviewer")
    assert herdr_prompt.sender_ref(sender) == "reviewer@w1:p1"


def test_reply_contract_without_agent_is_unaddressable() -> None:
    caller = herdr_prompt.CallerContext(pane_id="w9:p2", label="scratch pad")
    contract = herdr_prompt.render_reply_contract(caller)
    assert "cannot be addressed" in contract
    assert "herdr agent prompt w9:p2" not in contract


def test_reply_contract_binds_a_derived_ticket_with_the_ticket_flag() -> None:
    """#246 E1.1: a known ticket id is rendered, shell-quoted, as `--ticket=<id>`.

    Old role: asserted the exact unquoted substring `--ticket #182-…` in the rendered contract.
    E1.1-rework role: asserted the quoted space-form substring `--ticket '#182-…'` and that
    the unquoted form is absent — the unit counterpart of the shell witness pin.
    New role (herdr228-p3#P2): asserts the `=`-form substring `--ticket='#182-…'`, so a
    leading-dash id cannot be parsed as a flag, and that both space forms are absent.
    """
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", agent="reviewer")
    bound = herdr_prompt.render_reply_contract(sender, "#182-herdr-msg-enhance")
    assert "\"<STATUS> <artifacts> <issues>\" --ticket='#182-herdr-msg-enhance'" in bound
    assert "\"<STATUS> <artifacts> <issues>\" --ticket '#182-herdr-msg-enhance'" not in bound
    assert '"<STATUS> <artifacts> <issues>" --ticket #182-herdr-msg-enhance' not in bound


def test_reply_contract_without_a_ticket_omits_the_flag() -> None:
    """#246 E1.1 pin 3 (unit): an absent ticket id renders the pre-change contract, no crash."""
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", agent="reviewer")
    assert "--ticket" not in herdr_prompt.render_reply_contract(sender)
    assert "--ticket" not in herdr_prompt.render_reply_contract(sender, None)


def test_reply_contract_points_at_this_trees_helper_not_a_foreign_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#241 P2-B: the sibling rule tells this tree's helper from an existing foreign one.

    `is_file()` passes for ANY existing path, so the old pin stayed green when the rendered
    helper pointed at the resolved foreign copy — the original defect in its resolved shape.
    A foreign file that exists satisfies the old assertion and fails the sibling rule, which
    is exactly the discrimination the pin was missing.

    Mutant killed: point any rendered REPLY_HELPER at an existing foreign `herdr_reply.py`
    — the sibling assertions at the render sites fail while every `is_file()` assertion
    still passes.
    """
    foreign = tmp_path / "herdr_reply.py"
    _ = foreign.write_text("# a foreign copy that exists\n", encoding="utf-8")
    assert foreign.is_file()
    assert foreign.resolve().parent != SCRIPTS_DIR
    monkeypatch.setattr(herdr_envelope, "REPLY_HELPER", foreign)
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", agent="reviewer")
    contract = herdr_prompt.render_reply_contract(sender, "#182-test")
    match = re.search(r'uv run "([^"]+)"', contract)
    assert match, contract
    assert Path(match.group(1)).is_file()  # the old pin: blind to this mutant
    assert Path(match.group(1)).resolve().parent != SCRIPTS_DIR  # the new rule catches it


def test_reply_contract_documents_the_sha_guard_waiver_with_a_quoted_example() -> None:
    """herdr228-p3#P1: the rendered contract names the sanctioned waiver route in prose.

    A callee quoting a review id (an eight-hex record such as 0c81f04c, which names no
    commit) meets the broad #247 trigger, so the contract itself must tell the callee the
    sanctioned route: waive the token by name with `--allow-unresolvable-sha`. The example
    is itself single-quoted, so it survives copy-paste as one shell word — an unquoted
    placeholder would be a parse error where the callee pastes it (review 399f6102) — and
    the guidance is prose, never a shell template, so nothing pasted from it widens the
    waiver. Mutant: delete the guidance and this pin fails on the missing flag name.
    """
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", agent="reviewer")
    for contract in (
        herdr_prompt.render_reply_contract(sender, "#228-waiver-doc"),
        herdr_prompt.render_reply_contract(sender),
    ):
        assert "--allow-unresolvable-sha" in contract
        assert "'0c81f04c'" in contract
        assert "<TOKEN>" not in contract


def delivered_envelope(text: str) -> tuple[herdr_prompt.Envelope, str]:
    """The A2A envelope of a delivered payload plus its body, read through `herdr_prompt`."""
    envelope, body = herdr_prompt.split_envelope_and_body(text)
    assert envelope is not None, text
    assert body is not None, text
    return envelope, body


def test_caller_context_prepended_by_default(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (prompt_call,) = stub.prompts()
    text = prompt_call[4]
    lines = text.splitlines()
    assert lines[0] == "---"
    assert not any(re.match(r"^\[\d{4}-", line) for line in lines)
    envelope, body = delivered_envelope(text)
    assert envelope.state == "TASK_STATE_WORKING"
    assert re.match(TIMESTAMP_RE, envelope.timestamp)
    assert envelope.sender == "reviewer@w9:p1"
    assert envelope.receiver == "reviewer@w9:p1"
    assert envelope.group == ("reviewer@w9:p1",)
    assert envelope.task_group == "w9:t1"
    assert body.startswith("hi\n\n")
    assert "${herdr_skill}" in herdr_prompt.SKILL_NOTICE
    assert "~/.agents" not in herdr_prompt.SKILL_NOTICE
    assert herdr_prompt.SKILL_NOTICE in lines
    assert f"\n---\n{herdr_prompt.SKILL_NOTICE}\n\nhi\n\n" in text
    reply = re.search(r'  uv run "([^"]+)" reviewer "<STATUS> <artifacts> <issues>"', text)
    assert reply, text
    assert Path(reply.group(1)).is_file(), reply.group(1)
    # #241 P2-B (new pin): the helper must be THIS tree's sibling script, not merely an
    # existing path — `is_file()` passes for a foreign copy too, so it cannot tell the
    # resolved foreign referent (the original defect) from the correct one.
    assert Path(reply.group(1)).resolve().parent == SCRIPTS_DIR, reply.group(1)
    assert "~/.agents" not in text


def test_resolve_caller_extracts_kind_without_a_runtime_block(
    stub: StubHarness, tmp_path: Path
) -> None:
    state = {
        **DEFAULT_STATE,
        "agents": [
            {
                "pane_id": "w9:p1",
                "name": "reviewer",
                "agent": "pi",
                "agent_session": {"kind": "path", "value": "/tmp/session.jsonl"},
            }
        ],
    }
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")), state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (prompt_call,) = stub.prompts()
    text = prompt_call[4]
    assert text.splitlines()[0] == "---"
    envelope, _body = delivered_envelope(text)
    assert envelope.sender == "reviewer@w9:p1"
    assert envelope.context_id == "/tmp/session.jsonl"
    assert not envelope.cwd and not envelope.resume
    assert "Runtime:" not in text
    assert "Resume:" not in text


def test_herdr_pane_id_selects_the_caller(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer", "--file", str(payload_file(tmp_path, "hi")), env={"HERDR_PANE_ID": "w9:p2"}
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (prompt_call,) = stub.prompts()
    text = prompt_call[4]
    assert text.splitlines()[0] == "---"
    envelope, _body = delivered_envelope(text)
    assert envelope.sender == "w9:p2"
    assert envelope.group == ("reviewer@w9:p1",)
    assert envelope.receiver == "reviewer@w9:p1"
    assert envelope.task_group == "w9:t1"
    assert "cannot be addressed" in prompt_call[4]


def test_no_caller_context_sends_verbatim_without_lookups(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")), "--no-caller-context")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (prompt_call,) = stub.prompts()
    assert prompt_call[4] == "hi"
    kinds = [call[1:3] for call in stub.calls()]
    assert kinds == [["agent", "get"], ["agent", "prompt"]]
    assert "--no-caller-context drops the Sender/Receiver envelope" in done.stderr


def test_broadcast_renders_per_target_callee(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("callee1", "callee2", "--file", str(payload_file(tmp_path, "hi")), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (first, second) = stub.prompts()
    assert (first[3], second[3]) == ("callee1", "callee2")
    first_lines = first[4].splitlines()
    assert first_lines[0] == "---"
    assert not any(re.match(r"^\[\d{4}-", line) for line in first_lines)
    first_env, _first_body = delivered_envelope(first[4])
    assert first_env.sender == "reviewer@w9:p1"
    assert first_env.receiver == "callee1"
    assert first_env.group == ("reviewer@w9:p1",)
    assert first_env.task_group == "w9:t1"
    assert first[4] != second[4]
    assert "receiver: callee1" in first[4]
    assert "receiver: callee2" in second[4]
    assert first[4].splitlines()[1:] != second[4].splitlines()[1:]
    body_first = first[4].replace("receiver: callee1", "receiver: X")
    body_second = second[4].replace("receiver: callee2", "receiver: X")
    assert re.sub(r"timestamp: '[^']*'", "", body_first) == re.sub(
        r"timestamp: '[^']*'", "", body_second
    )


def test_dry_run_renders_caller_payload_without_prompting(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")), "--dry-run", "--json")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    argv: list[str] = json.loads(done.stdout)
    assert argv[3] == "reviewer"
    lines = argv[4].splitlines()
    assert lines[0] == "---"
    assert not any(re.match(r"^\[\d{4}-", line) for line in lines)
    envelope, _body = delivered_envelope(argv[4])
    assert envelope.sender == "reviewer@w9:p1"
    assert envelope.receiver == "reviewer@w9:p1"
    assert envelope.group == ("reviewer@w9:p1",)
    assert envelope.task_group == "w9:t1"
    assert "receiver: reviewer@w9:p1" in argv[4]
    assert "${herdr_skill}" in argv[4]
    reply = re.search(r'  uv run "([^"]+)" reviewer "<STATUS> <artifacts> <issues>"', argv[4])
    assert reply, argv[4]
    assert Path(reply.group(1)).is_file(), reply.group(1)
    # #241 P2-B (new pin): same sibling rule as above — an existing foreign path is not
    # this tree's helper.
    assert Path(reply.group(1)).resolve().parent == SCRIPTS_DIR, reply.group(1)
    assert "~/.agents" not in argv[4]


def test_dry_run_opt_out_renders_verbatim(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path, "hi")),
        "--dry-run",
        "--json",
        "--no-caller-context",
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    assert json.loads(done.stdout)[4] == "hi"


def test_dry_run_prints_a_trimmed_summary_not_the_raw_argv(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#259: a caller-side dry run echoes metadata + a body preview, never the serialized argv.

    #259 anchor addendum: the status line carries the `[You: …]` self-anchor in the colon form.
    #260: the delivered envelope carries a plain `receiver:` address — no `(You)` anywhere, in the
    callee payload or the caller copy.

    Pin -> mutant: printing `json.dumps(argv)` (the pre-#259 dry run) — this output is not one
    JSON line and carries no `Herdr:` notice, so a raw-argv render fails it.
    """
    ticket = payload_file(tmp_path, "do the thing")
    done = stub.run("reviewer", "--file", str(ticket), "--dry-run")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    out = done.stdout
    lines = out.splitlines()
    assert lines[0] == "[You: reviewer@w9:p1] dry-run: would prompt reviewer (w9:p1)"
    assert lines[1] == "---"
    assert "metadata:" in out and "status:" in out
    assert "  receiver: reviewer@w9:p1" in out
    assert "(You)" not in out
    assert "Routing:" not in out and "Protocol:" not in out
    assert herdr_prompt.SKILL_NOTICE not in out
    assert lines.count("---") == 2
    assert f"File: {ticket}" in out
    assert "do the thing" in out
    assert not out.startswith("{")


def test_dry_run_json_still_prints_the_full_wrapped_callee_payload(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#259: `--json` keeps the machine render, and the callee payload is untouched by the trim.

    Pin -> mutant: shrinking the DELIVERED payload rather than only the caller echo — the argv
    element [4] must still carry the full frontmatter block, the `Herdr:` notice and the reply
    contract.
    """
    ticket = payload_file(tmp_path, "do the thing")
    done = stub.run("reviewer", "--file", str(ticket), "--dry-run", "--json")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    argv: list[str] = json.loads(done.stdout)
    delivered = argv[4]
    assert herdr_prompt.SKILL_NOTICE in delivered
    assert "receiver: reviewer@w9:p1" in delivered
    assert "On completion, reply to the sender" in delivered


def test_live_prompt_prints_status_then_trimmed_summary(stub: StubHarness, tmp_path: Path) -> None:
    """#259: a live run leads with the anchored status line, then the trimmed metadata + preview."""
    ticket = payload_file(tmp_path, "do the thing")
    done = stub.run("reviewer", "--file", str(ticket), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    out = done.stdout
    lines = out.splitlines()
    assert lines[0].startswith("[You: reviewer@w9:p1] prompted reviewer")
    assert "bytes=" in lines[0]
    assert lines[1] == "---"
    assert "metadata:" in out and "status:" in out
    assert "  receiver: reviewer@w9:p1" in out
    assert "(You)" not in out
    assert "Routing:" not in out and "Protocol:" not in out
    assert f"File: {ticket}" in out
    assert "do the thing" in out


def test_body_preview_prints_short_bodies_and_skips_long_ones(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#259: a <=3-line body prints in full; a longer one prints first, skip marker, last."""
    short = stub.run("reviewer", "--file", str(payload_file(tmp_path, "alpha\nbeta")), "--dry-run")
    assert short.returncode == herdr_cli.EXIT_OK, short.stderr
    assert "alpha" in short.stdout and "beta" in short.stdout
    assert "skipped" not in short.stdout

    long_body = "line1\nline2\nline3\nline4\nline5\nline6"
    long_ = stub.run("reviewer", "--file", str(payload_file(tmp_path, long_body)), "--dry-run")
    assert long_.returncode == herdr_cli.EXIT_OK, long_.stderr
    assert "line1" in long_.stdout and "line6" in long_.stdout
    assert "... [skipped 4 lines]" in long_.stdout
    assert "line3" not in long_.stdout


def test_refuses_target_that_is_an_agent_kind(stub: StubHarness, tmp_path: Path) -> None:
    state = {
        **DEFAULT_STATE,
        "agents": [{"pane_id": "w9:p2", "name": "t7-impl", "agent": "qodercli"}],
        "panes": [
            *DEFAULT_STATE["panes"],
            {"pane_id": "w9:p2", "tab_id": "w9:t1", "workspace_id": "w9", "label": "callee"},
        ],
    }
    done = stub.run("qodercli", "--file", str(payload_file(tmp_path, "hi")), state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "is an agent kind" in done.stderr
    assert "live agent names: t7-impl" in done.stderr
    assert stub.prompts() == []


def test_refuses_qoderclicn_target_that_is_an_agent_kind(stub: StubHarness, tmp_path: Path) -> None:
    state = {
        **DEFAULT_STATE,
        "agents": [{"pane_id": "w9:p2", "name": "t7-impl", "agent": "qoderclicn"}],
        "panes": [
            *DEFAULT_STATE["panes"],
            {"pane_id": "w9:p2", "tab_id": "w9:t1", "workspace_id": "w9", "label": "callee"},
        ],
    }
    done = stub.run("qoderclicn", "--file", str(payload_file(tmp_path, "hi")), state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "is an agent kind" in done.stderr
    assert "live agent names: t7-impl" in done.stderr
    assert stub.prompts() == []


def test_group_members_listed_in_caller_context(stub: StubHarness, tmp_path: Path) -> None:
    state = {
        **DEFAULT_STATE,
        "agents": [
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi"},
            {"pane_id": "w9:p2", "name": "t7-impl", "agent": "qodercli"},
        ],
        "panes": [
            *DEFAULT_STATE["panes"][:1],
            {"pane_id": "w9:p2", "tab_id": "w9:t1", "workspace_id": "w9", "label": "callee"},
        ],
    }
    done = stub.run("w9:p2", "--file", str(payload_file(tmp_path, "hi")), state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (prompt_call,) = stub.prompts()
    text = prompt_call[4]
    envelope, _body = delivered_envelope(text)
    assert envelope.group == ("reviewer@w9:p1", "t7-impl@w9:p2")
    assert envelope.receiver == "t7-impl@w9:p2"
    assert "label callee" not in text


def test_constant_nonzero_revision_accepted_without_retry(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Issue #193: exit code 0 means prompt accepted; constant revision does not retry or drop."""
    state = {
        **DEFAULT_STATE,
        "agent_get_rev_seq": {"reviewer": ["r1", "r1", "r1"]},
    }
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")), state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "prompt dropped" not in done.stderr
    assert "prompted reviewer" in done.stdout
    assert "revision=r1" in done.stdout
    assert len(stub.prompts()) == 1


def test_revision_zero_agent_accepted_without_retry(stub: StubHarness, tmp_path: Path) -> None:
    """agy pins revision at 0: exit 0 is success, and retrying would duplicate the injection."""
    state = {
        **DEFAULT_STATE,
        "agent_get_rev_seq": {"reviewer": ["0", "0"]},
    }
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")), state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "prompt dropped" not in done.stderr
    assert "prompted reviewer" in done.stdout
    assert len(stub.prompts()) == 1


# ── integration: default envelope trim and --verbose opt-in ──────────────────────────


def _session_caller_state() -> dict[str, object]:
    return {
        **DEFAULT_STATE,
        "agents": [
            {
                "pane_id": "w9:p1",
                "name": "reviewer",
                "agent": "pi",
                "agent_session": {"kind": "path", "value": "/tmp/session.jsonl"},
            }
        ],
    }


def test_default_envelope_omits_recovery_metadata(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer", "--file", str(payload_file(tmp_path, "hi")), state=_session_caller_state()
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (prompt_call,) = stub.prompts()
    text = prompt_call[4]
    assert "Runtime:" not in text
    assert "Cwd:" not in text
    envelope, _body = delivered_envelope(text)
    assert envelope.context_id == "/tmp/session.jsonl"
    assert not envelope.cwd and not envelope.resume


def test_verbose_flag_adds_cwd_and_resume_metadata(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path, "hi")),
        "--verbose",
        state=_session_caller_state(),
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (prompt_call,) = stub.prompts()
    lines = prompt_call[4].splitlines()
    assert "  cwd: /tmp/harness" in lines
    assert "  resume: pi --session /tmp/session.jsonl" in lines
    envelope, _body = delivered_envelope(prompt_call[4])
    assert envelope.cwd == "/tmp/harness"
    assert envelope.resume == "pi --session /tmp/session.jsonl"


def test_resolve_caller_captures_session_and_resume() -> None:
    panes = [{"pane_id": "w9:p1", "tab_id": "w9:t1", "cwd": "/tmp/harness"}]
    agents = [
        {
            "pane_id": "w9:p1",
            "name": "reviewer",
            "agent": "pi",
            "agent_session": {"kind": "path", "value": "/tmp/session.jsonl"},
        }
    ]
    caller = herdr_prompt.resolve_caller(
        "herdr", {"HERDR_PANE_ID": "w9:p1"}, inventory=(panes, agents)
    )
    assert caller.session_id == "/tmp/session.jsonl"
    assert caller.resume_cmd == "pi --session /tmp/session.jsonl"


# ── integration: pre-flight readiness gate and --no-wait handshake ──────────────────


def _sleep_recorder() -> tuple[list[float], Callable[[float], None]]:
    slept: list[float] = []

    def fake_sleep(seconds: float) -> None:
        slept.append(seconds)

    return slept, fake_sleep


def test_preflight_waits_until_the_target_settles(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    slept, fake_sleep = _sleep_recorder()
    monkeypatch.setattr(herdr_prompt, "_sleep", fake_sleep)
    stub.write_state(
        {**DEFAULT_STATE, "agent_get_seq": {"reviewer": ["working", "working", "idle"]}}
    )
    code = herdr_prompt.main(
        ["reviewer", "--file", str(payload_file(tmp_path, "hi"))], env=stub.base_env()
    )
    assert code == herdr_cli.EXIT_OK
    assert len(stub.prompts()) == 1
    assert slept == [herdr_prompt.READY_INTERVAL_SECONDS, herdr_prompt.READY_INTERVAL_SECONDS]


def test_preflight_timeout_aborts_before_prompting(
    stub: StubHarness,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    slept, fake_sleep = _sleep_recorder()
    monkeypatch.setattr(herdr_prompt, "_sleep", fake_sleep)
    stub.write_state({**DEFAULT_STATE, "agent_get_seq": {"reviewer": ["working"]}})
    code = herdr_prompt.main(
        ["reviewer", "--file", str(payload_file(tmp_path, "hi"))], env=stub.base_env()
    )
    assert code == herdr_cli.EXIT_USAGE
    assert stub.prompts() == []
    assert len(slept) == 49
    err = capsys.readouterr().err
    assert "did not settle for prompt delivery" in err
    assert "last status=working" in err
    assert "dialog" not in err.lower()
    assert "BUSY" in err


def test_preflight_timeout_reports_observed_busy_without_dialog_guess(
    stub: StubHarness,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pin 1 (#249): a working target's refusal reports the observation, never a hypothesis.

    Mutant killed: restore the dialog-guess wording, so the refusal again claims an
    auth/approval dialog for a merely busy pane — the `dialog` absence assertion fails.
    """
    slept, fake_sleep = _sleep_recorder()
    monkeypatch.setattr(herdr_prompt, "_sleep", fake_sleep)
    stub.write_state({**DEFAULT_STATE, "agent_get_seq": {"reviewer": ["working"]}})
    code = herdr_prompt.main(
        ["reviewer", "--file", str(payload_file(tmp_path, "hi"))], env=stub.base_env()
    )
    assert code == herdr_cli.EXIT_USAGE
    assert stub.prompts() == []
    assert len(slept) == 49
    err = capsys.readouterr().err
    assert "did not settle for prompt delivery" in err
    assert "working" in err
    assert "dialog" not in err.lower()
    assert "BUSY" in err
    assert "longer interval" in err


def test_preflight_timeout_names_blocked_on_input_with_evidence(
    stub: StubHarness,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pin 2 (#249): interactive_ready=false refusal names BLOCKED-ON-INPUT with evidence."""
    slept, fake_sleep = _sleep_recorder()
    monkeypatch.setattr(herdr_prompt, "_sleep", fake_sleep)
    stub.write_state(
        {
            **DEFAULT_STATE,
            "agent_get_seq": {"reviewer": ["working"]},
            "agent_get_ready_seq": {"reviewer": [False]},
        }
    )
    code = herdr_prompt.main(
        ["reviewer", "--file", str(payload_file(tmp_path, "hi"))], env=stub.base_env()
    )
    assert code == herdr_cli.EXIT_USAGE
    assert stub.prompts() == []
    assert len(slept) == 49
    err = capsys.readouterr().err
    assert "did not settle for prompt delivery" in err
    assert "BLOCKED-ON-INPUT" in err
    assert "interactive_ready=false" in err


def test_no_wait_handshake_confirms_acceptance(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    slept, fake_sleep = _sleep_recorder()
    monkeypatch.setattr(herdr_prompt, "_sleep", fake_sleep)
    stub.write_state(DEFAULT_STATE)
    code = herdr_prompt.main(
        ["reviewer", "--file", str(payload_file(tmp_path, "hi")), "--no-wait"],
        env=stub.base_env(),
    )
    assert code == herdr_cli.EXIT_OK
    assert len(stub.prompts()) == 1
    assert slept == []


def test_no_wait_handshake_warns_without_resending(
    stub: StubHarness,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Issue #193: exit 0 means accepted, so an unconfirmed handshake warns and never re-sends."""
    slept, fake_sleep = _sleep_recorder()
    monkeypatch.setattr(herdr_prompt, "_sleep", fake_sleep)
    stub.write_state(
        {
            **DEFAULT_STATE,
            "agent_get_seq": {"reviewer": ["idle"]},
            "agent_get_rev_seq": {"reviewer": ["r1"] * 40},
        }
    )
    code = herdr_prompt.main(
        ["reviewer", "--file", str(payload_file(tmp_path, "hi")), "--no-wait"],
        env=stub.base_env(),
    )
    assert code == herdr_cli.EXIT_OK
    assert len(stub.prompts()) == 1
    assert len(slept) == 49
    err = capsys.readouterr().err
    assert "acceptance was not confirmed" in err
    assert "the CLI accepted the payload" in err


def test_preflight_respects_explicit_interactive_ready_false(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    slept, fake_sleep = _sleep_recorder()
    monkeypatch.setattr(herdr_prompt, "_sleep", fake_sleep)
    stub.write_state(
        {
            **DEFAULT_STATE,
            "agent_get_seq": {"reviewer": ["working", "idle"]},
            "agent_get_ready_seq": {"reviewer": [False, True]},
        }
    )
    code = herdr_prompt.main(
        ["reviewer", "--file", str(payload_file(tmp_path, "hi"))], env=stub.base_env()
    )
    assert code == herdr_cli.EXIT_OK
    assert len(stub.prompts()) == 1
    assert len(slept) == 1


# ── cross-consistency: the wait and prompt paths interpret one feed alike ──────────


def test_readiness_and_fetch_agree_with_the_seam_observation(stub: StubHarness) -> None:
    """One fake-herdr record yields the same interpreted state through both consumers."""
    stub.write_state(
        {
            **DEFAULT_STATE,
            "agent_get": {
                "reviewer": {
                    "agent_status": "idle",
                    "revision": "r4",
                    "tokens": {"summary": "⏳ 1 subagent (developer)"},
                }
            },
        }
    )
    herdr = str(stub.herdr)
    env = stub.base_env()
    obs = herdr_agent.observe_agent(herdr, "reviewer", env)
    ready, status, revision = herdr_prompt.agent_readiness(herdr, "reviewer", env)
    rev, pane = herdr_prompt.fetch_agent_revision(herdr, "reviewer", env)
    snap = herdr_wait.snapshot_agent(herdr, "reviewer", env)

    assert (status, revision) == (obs.status, obs.revision)
    assert (rev, pane) == (obs.revision, obs.pane_id)
    assert (snap.status, snap.revision, snap.tokens) == (obs.status, obs.revision, obs.tokens)
    assert ready  # idle and interactive_ready true, so prompt delivery would proceed
    assert herdr_agent.has_active_subagents(obs)
    assert herdr_wait.has_active_subagents(snap)
    assert not herdr_agent.is_agent_settled(obs, ["idle", "done"])
    assert not herdr_wait.is_settled(snap, ["idle", "done"])


def test_readiness_tracks_the_same_transitions_as_the_seam(stub: StubHarness) -> None:
    """A working→idle feed is read alike by `agent_readiness` and `observe_agent`.

    Each round consumes two polls (one per reader), so the sequence repeats each
    scripted status in pairs and both readers see the same interpreted state.
    """
    stub.write_state(
        {**DEFAULT_STATE, "agent_get_seq": {"reviewer": ["working", "working", "idle", "idle"]}}
    )
    herdr = str(stub.herdr)
    env = stub.base_env()

    busy_ready, busy_status, busy_revision = herdr_prompt.agent_readiness(herdr, "reviewer", env)
    busy_obs = herdr_agent.observe_agent(herdr, "reviewer", env)
    idle_ready, idle_status, idle_revision = herdr_prompt.agent_readiness(herdr, "reviewer", env)
    idle_obs = herdr_agent.observe_agent(herdr, "reviewer", env)

    assert not busy_ready
    assert (busy_status, busy_revision) == (busy_obs.status, busy_obs.revision)
    assert (idle_status, idle_revision) == (idle_obs.status, idle_obs.revision)
    assert idle_ready
    assert herdr_agent.is_agent_settled(idle_obs, ["idle", "done"])


# ── #238: a revision-0 kind is not told to re-check a state that cannot move ────────


def _agy_idle_state(**extra: object) -> dict[str, object]:
    """DEFAULT_STATE with the reviewer running as agy: a revision that never moves."""
    return {
        **DEFAULT_STATE,
        "agents": [
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "agy", "agent_status": "idle"}
        ],
        "agent_get_seq": {"reviewer": ["idle"]},
        "agent_get_rev_seq": {"reviewer": ["r0"] * 40},
        **extra,
    }


def test_unconfirmed_warning_drops_herdr_wait_for_a_revision_static_kind(
    stub: StubHarness,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pin 4 (#238): the unconfirmed-acceptance warning stops naming `herdr-wait` where the
    target's kind can never move its revision, and still names it for an ordinary target.

    Mutant killed: drop the `revision_can_move` branch, so the warning always reads "check with
    herdr-wait before resubmitting" — the agy half then names `herdr-wait` and fails.
    """

    def no_sleep(seconds: float) -> None:
        """Swallow the handshake tick; this test only inspects the warning text."""

    monkeypatch.setattr(herdr_prompt, "_sleep", no_sleep)

    stub.write_state(_agy_idle_state())
    code = herdr_prompt.main(
        ["reviewer", "--file", str(payload_file(tmp_path, "hi")), "--no-wait"],
        env=stub.base_env(),
    )
    assert code == herdr_cli.EXIT_OK
    agy_err = capsys.readouterr().err
    assert "acceptance was not confirmed" in agy_err
    assert "herdr-agy-bridge" in agy_err, "the honest remedy must be named"
    assert "herdr-wait" not in agy_err, (
        "a revision-0 kind must not be sent to an unsatisfiable wait"
    )

    stub.write_state(
        {
            **DEFAULT_STATE,
            "agent_get_seq": {"reviewer": ["idle"]},
            "agent_get_rev_seq": {"reviewer": ["r1"] * 40},
        }
    )
    code = herdr_prompt.main(
        ["reviewer", "--file", str(payload_file(tmp_path, "hi")), "--no-wait"],
        env=stub.base_env(),
    )
    assert code == herdr_cli.EXIT_OK
    assert "herdr-wait" in capsys.readouterr().err


def test_wait_timeout_advice_drops_herdr_wait_for_a_revision_static_kind(
    stub: StubHarness, tmp_path: Path
) -> None:
    """The wait-timeout advice names `herdr-wait` only where the revision can move (#238)."""
    error = {"code": "timeout", "message": "wait timed out after 120000ms"}
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path, "hi")),
        "--wait",
        "--timeout",
        "120000",
        state=_agy_idle_state(prompt_error=error),
    )

    assert done.returncode == herdr_prompt.EXIT_WAIT_TIMEOUT
    assert "Yield turn and await reply callback" in done.stderr
    assert "herdr-agy-bridge" in done.stderr
    assert "herdr-wait" not in done.stderr


# ── #238: the revision-static remedy is derived from the kind, not a constant ──────

# Two revision-static kinds, each with its OWN bridge. The remedy must read the target kind's
# contract, so a second revision-static kind is never sent to the agy bridge.
_TWO_STATIC_KIND_CONFIG = """\
agy:
  trust_flags: []
  invariant: file
  revision_moves: false
  lifecycle_bridge: herdr-agy-bridge
maki:
  trust_flags: []
  invariant: file
  revision_moves: false
  lifecycle_bridge: herdr-maki-bridge
"""

_STATIC_KIND_CASES = (
    ("agy", "herdr-agy-bridge", "herdr-maki-bridge"),
    ("maki", "herdr-maki-bridge", "herdr-agy-bridge"),
)


def _two_static_kind_config(tmp_path: Path) -> Path:
    """Write the fixture kinds.yaml and return its path for `herdr_bootstrap.KINDS_CONFIG`."""
    path = tmp_path / "kinds.yaml"
    _ = path.write_text(_TWO_STATIC_KIND_CONFIG, encoding="utf-8")
    return path


def _static_kind_state(kind: str, **extra: object) -> dict[str, object]:
    """DEFAULT_STATE with the reviewer running as `kind`: a revision that never moves."""
    return {
        **DEFAULT_STATE,
        "agents": [{"pane_id": "w9:p1", "name": "reviewer", "agent": kind, "agent_status": "idle"}],
        "agent_get_seq": {"reviewer": ["idle"]},
        "agent_get_rev_seq": {"reviewer": ["r0"] * 40},
        **extra,
    }


@pytest.mark.parametrize(("kind", "own_bridge", "other_bridge"), _STATIC_KIND_CASES)
def test_unconfirmed_warning_remedy_names_the_kinds_own_bridge(
    stub: StubHarness,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    kind: str,
    own_bridge: str,
    other_bridge: str,
) -> None:
    """Pin 5 (#238): the unconfirmed-acceptance remedy is derived from the target kind, so a
    second revision-static kind is pointed at its own bridge, never at the agy bridge.

    Mutant killed: hardcode `herdr-agy-bridge` in the remedy again — the `maki` case then names
    the agy bridge and fails on `other_bridge not in err`.
    """
    monkeypatch.setattr(herdr_bootstrap, "KINDS_CONFIG", _two_static_kind_config(tmp_path))

    def no_sleep(seconds: float) -> None:
        """Swallow the handshake tick; this test only inspects the warning text."""

    monkeypatch.setattr(herdr_prompt, "_sleep", no_sleep)

    stub.write_state(_static_kind_state(kind))
    code = herdr_prompt.main(
        ["reviewer", "--file", str(payload_file(tmp_path, "hi")), "--no-wait"],
        env=stub.base_env(),
    )
    assert code == herdr_cli.EXIT_OK
    err = capsys.readouterr().err
    assert "acceptance was not confirmed" in err
    assert own_bridge in err, f"the {kind} bridge must be named for its own kind"
    assert other_bridge not in err, "a kind must never be sent to another kind's bridge"
    assert "herdr-wait" not in err


@pytest.mark.parametrize(("kind", "own_bridge", "other_bridge"), _STATIC_KIND_CASES)
def test_wait_timeout_remedy_names_the_kinds_own_bridge(
    stub: StubHarness,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    own_bridge: str,
    other_bridge: str,
) -> None:
    """Pin 6 (#238): the wait-timeout advice derives the bridge from the target kind too, so
    the second call site cannot keep naming one kind's bridge while the first is generalised.

    Mutant killed: hardcode `herdr-agy-bridge` at the timeout site — the `maki` case then names
    the agy bridge and fails on `other_bridge not in done.stderr`.
    """
    monkeypatch.setattr(herdr_bootstrap, "KINDS_CONFIG", _two_static_kind_config(tmp_path))
    error = {"code": "timeout", "message": "wait timed out after 120000ms"}
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path, "hi")),
        "--wait",
        "--timeout",
        "120000",
        state=_static_kind_state(kind, prompt_error=error),
    )

    assert done.returncode == herdr_prompt.EXIT_WAIT_TIMEOUT
    assert own_bridge in done.stderr, f"the {kind} bridge must be named for its own kind"
    assert other_bridge not in done.stderr, "a kind must never be sent to another kind's bridge"
    assert "herdr-wait" not in done.stderr


# ── #241: both branches of the revision-static advice, against the real kind contract ──

AGY_BRIDGE = "herdr-agy-bridge"
NEUTRAL_SURFACE = "the kind's own status surface"

# A second revision-static kind that declares NO bridge. The real config has no such kind
# (every real kind either moves its revision or declares a bridge), so the neutral branch
# is pinned here on a fixture and on the real config's bridge-less kinds below.
_BRIDGELESS_STATIC_KIND_CONFIG = """\
agy:
  trust_flags: []
  invariant: file
  revision_moves: false
  lifecycle_bridge: herdr-agy-bridge
maki:
  trust_flags: []
  invariant: file
  revision_moves: false
"""


def _real_kind_names() -> list[str]:
    """Every kind key declared in the real `skills/herdr/references/kinds.yaml`, in file order."""
    return [
        line[:-1]
        for line in herdr_bootstrap.KINDS_CONFIG.read_text(encoding="utf-8").splitlines()
        if re.fullmatch(r"[A-Za-z0-9_-]+:", line)
    ]


def test_kind_lifecycle_bridge_reads_only_the_real_configs_bridge() -> None:
    """Pin 7 (#241): the bridge is a per-kind fact read from the REAL kinds.yaml.

    Measured at 4df1fd4a: `agy` is the only real kind declaring `lifecycle_bridge`, so it is
    the only kind whose advice may name a bridge, and it names its own.
    """
    bridged = [kind for kind in _real_kind_names() if herdr_prompt.kind_lifecycle_bridge(kind)]
    assert bridged == ["agy"], "the real config declares exactly one bridge kind"
    assert herdr_prompt.kind_lifecycle_bridge("agy") == AGY_BRIDGE
    assert herdr_prompt.revision_static_surface("agy") == (
        f"the agy bridge's status title ({AGY_BRIDGE})"
    )


def test_revision_static_surface_is_bridge_neutral_for_every_bridgeless_real_kind() -> None:
    """Pin 8 (#241): the neutral branch of the real config: phrasing that names no bridge.

    `pi`, `claude`, `cline`, `codex`, `copilot`, and `qodercli` all declare no bridge, and
    none of them may be sent to `agy`'s.

    Mutant killed: drop the `if bridge:` guard in `revision_static_surface` — every kind here
    then renders `the <kind> bridge's status title` and this test fails.
    """
    neutral_kinds = [kind for kind in _real_kind_names() if kind != "agy"]
    assert neutral_kinds, "the real config must still carry bridge-less kinds to pin here"
    for kind in neutral_kinds:
        advice = herdr_prompt.revision_static_surface(kind)
        assert advice == NEUTRAL_SURFACE, kind
        assert "bridge" not in advice, kind
        assert AGY_BRIDGE not in advice, kind


def test_revision_static_surface_stays_neutral_when_the_kind_is_unresolved(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Pin 9 (#241): `None`, a blank name, an unknown kind, an unreadable and a malformed
    config all read as no bridge, so none of them borrows a real kind's bridge.

    Mutant killed: fall back to another kind's bridge when the kind declares none or cannot
    be resolved — the `AGY_BRIDGE not in advice` assertions here fail.
    """
    for probe in (None, "", "no-such-kind"):
        advice = herdr_prompt.revision_static_surface(probe)
        assert advice == NEUTRAL_SURFACE, probe
        assert "bridge" not in advice, probe
        assert AGY_BRIDGE not in advice, probe

    unreadable = tmp_path / "missing-kinds.yaml"
    malformed = tmp_path / "malformed-kinds.yaml"
    _ = malformed.write_text("agy:\n  invariant: nope\n", encoding="utf-8")
    for path in (unreadable, malformed):
        monkeypatch.setattr(herdr_bootstrap, "KINDS_CONFIG", path)
        advice = herdr_prompt.revision_static_surface("agy")
        assert advice == NEUTRAL_SURFACE, path
        assert "bridge" not in advice, path
        assert AGY_BRIDGE not in advice, path


def _bridgeless_static_kind_config(tmp_path: Path) -> Path:
    """Write the one-bridged/one-bridgeless fixture and return its path."""
    path = tmp_path / "kinds.yaml"
    _ = path.write_text(_BRIDGELESS_STATIC_KIND_CONFIG, encoding="utf-8")
    return path


def test_a_bridgeless_static_kind_is_never_sent_to_another_kinds_bridge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pin 10 (#241): the cross-kind promise, on a kind that declares none.

    The existing pair (`_STATIC_KIND_CASES`) covers two kinds that each declare a bridge; this
    covers the kind that declares none, which must read as neutral while its neighbour keeps
    naming its own bridge.

    Mutant killed: return the first declared bridge when the kind declares none — `maki` then
    renders `herdr-agy-bridge` and the `AGY_BRIDGE not in` assertion fails.
    """
    monkeypatch.setattr(herdr_bootstrap, "KINDS_CONFIG", _bridgeless_static_kind_config(tmp_path))
    maki = herdr_prompt.revision_static_surface("maki")
    assert maki == NEUTRAL_SURFACE
    assert AGY_BRIDGE not in maki
    assert herdr_prompt.revision_static_surface("agy") == (
        f"the agy bridge's status title ({AGY_BRIDGE})"
    )


def test_unconfirmed_warning_renders_the_neutral_advice_for_a_bridgeless_static_kind(
    stub: StubHarness,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Pin 11 (#241): the RENDERED warning for a revision-static kind with no bridge.

    Mutant killed: drop the `if bridge:` guard, so this warning claims a `maki bridge's status
    title` that does not exist and `"bridge" not in err` fails.
    """
    monkeypatch.setattr(herdr_bootstrap, "KINDS_CONFIG", _bridgeless_static_kind_config(tmp_path))

    def no_sleep(seconds: float) -> None:
        """Swallow the handshake tick; this test only inspects the warning text."""

    monkeypatch.setattr(herdr_prompt, "_sleep", no_sleep)

    stub.write_state(_static_kind_state("maki"))
    code = herdr_prompt.main(
        ["reviewer", "--file", str(payload_file(tmp_path, "hi")), "--no-wait"],
        env=stub.base_env(),
    )
    assert code == herdr_cli.EXIT_OK
    err = capsys.readouterr().err
    assert "acceptance was not confirmed" in err
    assert NEUTRAL_SURFACE in err
    assert "bridge" not in err, "a bridge-less kind must not be told to read a bridge"
