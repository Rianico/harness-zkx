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

import herdr_cli
import herdr_prompt
import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness

SCRIPT = SCRIPTS_DIR / "herdr_prompt.py"

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
        "--label", "scratch pad", "--file", str(payload_file(tmp_path, "hi")), "--dry-run"
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
    done = stub.run("callee1", "callee2", "--file", str(payload_file(tmp_path, "hi")), "--dry-run")
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
        == "pi --resume /path/to/session.jsonl"
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
        herdr_prompt._scalar("pi --resume /path/to/session.jsonl")
        == '"pi --resume /path/to/session.jsonl"'
    )
    assert herdr_prompt._scalar("review pane X") == '"review pane X"'
    assert herdr_prompt._scalar("a#b") == '"a#b"'
    assert herdr_prompt._scalar("it's") == '"it\'s"'
    assert herdr_prompt._scalar('say "hi"') == '"say \\"hi\\""'
    assert herdr_prompt._scalar("back\\slash x") == '"back\\\\slash x"'
    assert herdr_prompt._scalar("") == ""


def test_envelope_renders_sender_alone_when_nothing_else_is_known() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", label="orchestrator", agent="orchestrator")
    assert herdr_prompt.render_envelope(sender) == "\n".join(
        [
            "Sender: orchestrator@w1:p1",
            herdr_prompt.SKILL_NOTICE,
        ]
    )


def test_envelope_renders_position_receiver_group_and_resume() -> None:
    sender = herdr_prompt.CallerContext(
        pane_id="w1:p1",
        label="orchestrator",
        agent="orchestrator",
        kind="pi",
        session_id="/tmp/session.jsonl",
        resume_cmd="pi --resume /tmp/session.jsonl",
    )
    assert herdr_prompt.render_envelope(
        sender,
        receiver="impl-1",
        group_members=["orchestrator@w1:p1", "impl-1@w1:p3"],
    ) == "\n".join(
        [
            "Sender: orchestrator@w1:p1 - kind pi",
            "Group: orchestrator@w1:p1, impl-1@w1:p3",
            'Resume: "pi --resume /tmp/session.jsonl"',
            herdr_prompt.SKILL_NOTICE,
            "",
            "Receiver(You): impl-1",
        ]
    )


def test_envelope_renders_a_resolved_receiver_as_a_position_ref() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", label="orchestrator", agent="orchestrator")
    receiver = herdr_prompt.CallerContext(
        pane_id="w1:p3", label="impl-1", agent="impl-1", kind="agy", tab_id="w1:t1"
    )
    assert herdr_prompt.render_envelope(sender, receiver=receiver) == "\n".join(
        [
            "Sender: orchestrator@w1:p1",
            herdr_prompt.SKILL_NOTICE,
            "",
            "Receiver(You): impl-1@w1:p3 - tab w1:t1 - kind agy",
        ]
    )


def test_envelope_renders_tab_cwd_and_resume() -> None:
    sender = herdr_prompt.CallerContext(
        pane_id="w1:p1",
        label="orchestrator",
        agent="orchestrator",
        tab_id="w1:t1",
        cwd="/path/to/my project",
        kind="pi",
        session_id="/tmp/session.jsonl",
        resume_cmd="pi --resume /tmp/session.jsonl",
    )
    assert herdr_prompt.render_envelope(sender) == "\n".join(
        [
            "Sender: orchestrator@w1:p1 - tab w1:t1 - kind pi",
            'Resume: "pi --resume /tmp/session.jsonl"',
            'Cwd: "/path/to/my project"',
            herdr_prompt.SKILL_NOTICE,
        ]
    )


def test_envelope_keeps_a_label_that_differs_from_the_agent_name() -> None:
    sender = herdr_prompt.CallerContext(
        pane_id="w1:p2",
        label="callee",
        agent="t7-impl",
        kind="qodercli",
        resume_cmd="qodercli resume",
    )
    assert herdr_prompt.render_envelope(sender) == "\n".join(
        [
            "Sender: t7-impl@w1:p2 - label callee - kind qodercli",
            'Resume: "qodercli resume"',
            herdr_prompt.SKILL_NOTICE,
        ]
    )


def test_sender_ref_only_ever_uses_the_agent_name_as_the_target_token() -> None:
    labelled_only = herdr_prompt.CallerContext(pane_id="w9:p2", label="scratch pad")
    spare_label = herdr_prompt.CallerContext(pane_id="w1:p1", label="callee", agent="impl-1")
    assert herdr_prompt.sender_ref(labelled_only) == 'w9:p2 - label "scratch pad"'
    assert herdr_prompt.sender_ref(spare_label) == "impl-1@w1:p1 - label callee"


def test_envelope_omits_unknown_fields_never_invents() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w9:p1", agent="reviewer")
    assert herdr_prompt.render_envelope(sender) == "\n".join(
        ["Sender: reviewer@w9:p1", herdr_prompt.SKILL_NOTICE]
    )


def test_envelope_sanitizes_label_to_single_line() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", label="review\npane\tX", agent="reviewer")
    assert (
        herdr_prompt.render_envelope(sender).splitlines()[0]
        == 'Sender: reviewer@w1:p1 - label "review pane X"'
    )


def test_envelope_drops_a_blank_label() -> None:
    sender = herdr_prompt.CallerContext(pane_id="w1:p1", label="   ", agent="reviewer")
    assert herdr_prompt.render_envelope(sender).splitlines()[0] == "Sender: reviewer@w1:p1"


def test_reply_contract_without_agent_is_unaddressable() -> None:
    caller = herdr_prompt.CallerContext(pane_id="w9:p2", label="scratch pad")
    contract = herdr_prompt.render_reply_contract(caller)
    assert "cannot be addressed" in contract
    assert "herdr agent prompt w9:p2" not in contract


def test_caller_context_prepended_by_default(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (prompt_call,) = stub.prompts()
    text = prompt_call[4]
    lines = text.splitlines()
    assert re.match(r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\]$", lines[0])
    assert lines[1:7] == [
        "Sender: reviewer@w9:p1 - tab w9:t1 - kind pi",
        "Group: reviewer@w9:p1",
        "Cwd: /tmp/harness",
        herdr_prompt.SKILL_NOTICE,
        "",
        "Receiver(You): reviewer@w9:p1 - tab w9:t1 - kind pi",
    ]
    assert "Herdr: see skill ~/.agents/skills/herdr/SKILL.md" in text
    assert "Group: reviewer@w9:p1" in text
    assert "Receiver(You): reviewer@w9:p1 - tab w9:t1 - kind pi" in text
    assert "\n\nhi\n\n" in text
    assert (
        'uv run ~/.agents/skills/herdr/scripts/herdr_reply.py reviewer "<STATUS> <artifacts> <issues>"'
        in text
    )


def test_resolve_caller_extracts_kind_session_and_resume(stub: StubHarness, tmp_path: Path) -> None:
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
    lines = text.splitlines()
    assert re.match(r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\]$", lines[0])
    assert lines[1:8] == [
        "Sender: reviewer@w9:p1 - tab w9:t1 - kind pi",
        "Group: reviewer@w9:p1",
        'Resume: "pi --resume /tmp/session.jsonl"',
        "Cwd: /tmp/harness",
        herdr_prompt.SKILL_NOTICE,
        "",
        "Receiver(You): reviewer@w9:p1 - tab w9:t1 - kind pi",
    ]
    assert "Group: reviewer@w9:p1" in text
    assert "Receiver(You): reviewer@w9:p1 - tab w9:t1 - kind pi" in text


def test_herdr_pane_id_selects_the_caller(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer", "--file", str(payload_file(tmp_path, "hi")), env={"HERDR_PANE_ID": "w9:p2"}
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (prompt_call,) = stub.prompts()
    lines = prompt_call[4].splitlines()
    assert re.match(r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\]$", lines[0])
    assert lines[1:7] == [
        'Sender: w9:p2 - label "scratch pad" - tab w9:t1',
        "Group: reviewer@w9:p1",
        "Cwd: /tmp/scratch",
        herdr_prompt.SKILL_NOTICE,
        "",
        "Receiver(You): reviewer@w9:p1 - tab w9:t1 - kind pi",
    ]
    assert "cannot be addressed" in prompt_call[4]


def test_no_caller_context_sends_verbatim_without_lookups(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")), "--no-caller-context")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (prompt_call,) = stub.prompts()
    assert prompt_call[4] == "hi"
    kinds = [call[1:3] for call in stub.calls()]
    assert kinds == [["agent", "prompt"]]
    assert "--no-caller-context drops the Sender/Receiver envelope" in done.stderr


def test_broadcast_renders_per_target_callee(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("callee1", "callee2", "--file", str(payload_file(tmp_path, "hi")), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (first, second) = stub.prompts()
    assert (first[3], second[3]) == ("callee1", "callee2")
    first_lines = first[4].splitlines()
    assert re.match(r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\]$", first_lines[0])
    assert first_lines[1:7] == [
        "Sender: reviewer@w9:p1 - tab w9:t1 - kind pi",
        "Group: reviewer@w9:p1",
        "Cwd: /tmp/harness",
        herdr_prompt.SKILL_NOTICE,
        "",
        "Receiver(You): callee1",
    ]
    assert "Group: reviewer@w9:p1" in first[4]
    assert "Group: reviewer@w9:p1" in second[4]
    assert first[4] != second[4]
    assert "Receiver(You): callee1" in first[4]
    assert "Receiver(You): callee2" in second[4]
    assert first[4].splitlines()[1:] != second[4].splitlines()[1:]
    body_first = "\n".join(first[4].splitlines()[1:]).replace(
        "Receiver(You): callee1", "Receiver(You): X"
    )
    body_second = "\n".join(second[4].splitlines()[1:]).replace(
        "Receiver(You): callee2", "Receiver(You): X"
    )
    assert body_first == body_second


def test_dry_run_renders_caller_payload_without_prompting(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")), "--dry-run")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    argv: list[str] = json.loads(done.stdout)
    assert argv[3] == "reviewer"
    lines = argv[4].splitlines()
    assert re.match(r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\]$", lines[0])
    assert lines[1:7] == [
        "Sender: reviewer@w9:p1 - tab w9:t1 - kind pi",
        "Group: reviewer@w9:p1",
        "Cwd: /tmp/harness",
        herdr_prompt.SKILL_NOTICE,
        "",
        "Receiver(You): reviewer@w9:p1 - tab w9:t1 - kind pi",
    ]
    assert "Receiver(You): reviewer@w9:p1 - tab w9:t1 - kind pi" in argv[4]
    assert "Herdr: see skill ~/.agents/skills/herdr/SKILL.md" in argv[4]
    assert "~/.agents/skills/herdr/scripts/herdr_reply.py reviewer" in argv[4]


def test_dry_run_opt_out_renders_verbatim(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer", "--file", str(payload_file(tmp_path, "hi")), "--dry-run", "--no-caller-context"
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    assert json.loads(done.stdout)[4] == "hi"


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
    assert "Group: reviewer@w9:p1, t7-impl@w9:p2" in text
    assert "Receiver(You): t7-impl@w9:p2 - label callee - tab w9:t1 - kind qodercli" in text


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
