"""Tests for skills/herdr/scripts/herdr_prompt.py (herdr-prompt helper).

Integration cases route through the shared stub `herdr`; payload assertions read back the
recorded argv, which is what proves byte-for-byte delivery.
"""

import json
import os
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
    done = stub.run(
        "--label", "scratch pad", "--file", str(payload_file(tmp_path, "hi")), "--no-caller-context"
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
        "worker1",
        "worker2",
        "--file",
        str(payload_file(tmp_path, "hi")),
        "--no-wait",
        "--no-caller-context",
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (first, second) = stub.prompts()
    assert (first[3], second[3]) == ("worker1", "worker2")
    assert first[4] == second[4] == "hi"
    assert "prompted worker1" in done.stdout
    assert "prompted worker2" in done.stdout


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


def test_wait_timeout_is_exit_4_not_herdr_error(stub: StubHarness, tmp_path: Path) -> None:
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
    done = stub.run("worker1", "worker2", "--file", str(payload_file(tmp_path, "hi")), "--dry-run")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    argv_lines: list[list[str]] = [json.loads(line) for line in done.stdout.splitlines()]
    assert [argv[3] for argv in argv_lines] == ["worker1", "worker2"]


# ── integration: caller context (#106, #119) ─────────────────────────────────────────


def test_caller_block_renders_all_fields() -> None:
    caller = herdr_prompt.CallerContext(pane_id="w1:p1", label="orchestrator", agent="orchestrator")
    assert (
        herdr_prompt.render_caller_block(caller)
        == "Caller: pane=w1:p1 label=orchestrator agent=orchestrator"
    )


def test_caller_block_omits_absent_fields_never_invents() -> None:
    caller = herdr_prompt.CallerContext(pane_id="w9:p1", agent="reviewer")
    assert herdr_prompt.render_caller_block(caller) == "Caller: pane=w9:p1 agent=reviewer"


def test_caller_block_sanitizes_label_to_single_line() -> None:
    caller = herdr_prompt.CallerContext(pane_id="w1:p1", label="review\npane\tX", agent="reviewer")
    assert (
        herdr_prompt.render_caller_block(caller)
        == "Caller: pane=w1:p1 label=review pane X agent=reviewer"
    )


def test_caller_block_omits_blank_label() -> None:
    caller = herdr_prompt.CallerContext(pane_id="w1:p1", label="   ", agent="reviewer")
    assert herdr_prompt.render_caller_block(caller) == "Caller: pane=w1:p1 agent=reviewer"


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
    assert text.startswith("Caller: pane=w9:p1 agent=reviewer")
    assert "\n\nhi\n\n" in text
    assert 'herdr agent prompt reviewer "<STATUS> <artifacts> <issues>"' in text


def test_herdr_pane_id_selects_the_caller(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer", "--file", str(payload_file(tmp_path, "hi")), env={"HERDR_PANE_ID": "w9:p2"}
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (prompt_call,) = stub.prompts()
    assert prompt_call[4].startswith("Caller: pane=w9:p2 label=scratch pad")
    assert "agent=" not in prompt_call[4].splitlines()[0]
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


def test_broadcast_prepends_identically_per_target(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("worker1", "worker2", "--file", str(payload_file(tmp_path, "hi")), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (first, second) = stub.prompts()
    assert (first[3], second[3]) == ("worker1", "worker2")
    assert first[4] == second[4]
    assert first[4].startswith("Caller: pane=w9:p1 agent=reviewer")


def test_dry_run_renders_caller_payload_without_prompting(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")), "--dry-run")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    argv: list[str] = json.loads(done.stdout)
    assert argv[3] == "reviewer"
    assert argv[4].startswith("Caller: pane=w9:p1 agent=reviewer")
    assert "herdr agent prompt reviewer" in argv[4]


def test_dry_run_opt_out_renders_verbatim(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer", "--file", str(payload_file(tmp_path, "hi")), "--dry-run", "--no-caller-context"
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    assert json.loads(done.stdout)[4] == "hi"
