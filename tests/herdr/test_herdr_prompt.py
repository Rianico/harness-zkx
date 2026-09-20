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


def test_error_code_reads_envelope() -> None:
    stderr = '{"error":{"code":"agent_blocked","message":"blocked"},"id":"cli:agent:prompt"}'
    assert herdr_prompt.error_code(stderr) == "agent_blocked"


@pytest.mark.parametrize("stderr", ["", "not json", "[]", '{"error":null}', '{"ok":1}'])
def test_error_code_tolerates_other_shapes(stderr: str) -> None:
    assert herdr_prompt.error_code(stderr) is None


def test_error_code_accepts_plain_string_error() -> None:
    assert herdr_prompt.error_code('{"error":"split failed"}') == "split failed"


def test_settled_state_reads_agent_status() -> None:
    raw = '{"result":{"agent":{"agent_status":"blocked"},"type":"agent_prompted"}}'
    assert herdr_prompt.settled_state(raw) == "blocked"


def test_settled_state_is_none_without_agent() -> None:
    assert herdr_prompt.settled_state('{"result":{}}') is None


def test_decode_response_reports_non_json() -> None:
    with pytest.raises(herdr_prompt.HerdrError, match="non-JSON"):
        _ = herdr_prompt.decode_response("not json")


def test_decode_response_reports_non_object() -> None:
    with pytest.raises(herdr_prompt.HerdrError, match="non-object"):
        _ = herdr_prompt.decode_response("[1, 2]")


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
    assert done.returncode == herdr_prompt.EXIT_USAGE
    assert "HERDR_ENV" in done.stderr
    assert stub.calls() == []


def test_refuses_when_herdr_missing_from_path(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        env={"PATH": "/nonexistent", "HERDR_BIN_PATH": None},
    )
    assert done.returncode == herdr_prompt.EXIT_USAGE
    assert "not found on PATH" in done.stderr


def test_missing_file_is_usage_error(stub: StubHarness) -> None:
    done = stub.run("reviewer", "--file", "/nonexistent/payload.md")
    assert done.returncode == herdr_prompt.EXIT_USAGE
    assert "cannot read payload" in done.stderr
    assert stub.prompts() == []


def test_blank_payload_is_rejected_without_prompting(stub: StubHarness) -> None:
    done = stub.run("reviewer", stdin="   \n")
    assert done.returncode == herdr_prompt.EXIT_USAGE
    assert "empty" in done.stderr
    assert stub.prompts() == []


def test_non_positive_timeout_is_rejected(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), "--timeout", "0")
    assert done.returncode == herdr_prompt.EXIT_USAGE
    assert "not positive" in done.stderr
    assert stub.prompts() == []


# ── integration: byte-exact delivery ────────────────────────────────────────────────


def test_file_payload_is_delivered_byte_for_byte(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)))
    assert done.returncode == herdr_prompt.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[3] == "reviewer"
    assert call[4] == METACHARS
    assert "--wait" not in call


def test_stdin_dash_payload_is_delivered_verbatim(stub: StubHarness) -> None:
    done = stub.run("reviewer", "--file", "-", stdin=METACHARS)
    assert done.returncode == herdr_prompt.EXIT_OK, done.stderr
    assert stub.prompts()[0][4] == METACHARS


def test_bare_stdin_payload_is_delivered_verbatim(stub: StubHarness) -> None:
    done = stub.run("reviewer", stdin=METACHARS)
    assert done.returncode == herdr_prompt.EXIT_OK, done.stderr
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
    )
    assert done.returncode == herdr_prompt.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[1:5] == ["agent", "prompt", "reviewer", "short"]
    assert call[5:] == ["--wait", "--until", "idle", "--until", "done", "--timeout", "120000"]


def test_summary_reports_byte_count_and_state(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hello")), "--wait")
    assert done.returncode == herdr_prompt.EXIT_OK, done.stderr
    assert "prompted reviewer" in done.stdout
    assert "bytes=5" in done.stdout
    assert "state=idle" in done.stdout


def test_json_prints_raw_response(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "hi")), "--json")
    assert done.returncode == herdr_prompt.EXIT_OK, done.stderr
    assert json.loads(done.stdout)["result"]["agent"]["agent_status"] == "idle"


def test_dry_run_prints_exact_argv_without_prompting(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), "--dry-run", "--wait")
    assert done.returncode == herdr_prompt.EXIT_OK, done.stderr
    assert stub.prompts() == []
    argv = json.loads(done.stdout)
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
    assert done.returncode == herdr_prompt.EXIT_BLOCKED
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
    assert done.returncode == herdr_prompt.EXIT_BLOCKED
    assert "state=blocked" in done.stdout


def test_other_herdr_error_exits_herdr(stub: StubHarness, tmp_path: Path) -> None:
    error = {"code": "agent_not_found", "message": "agent target reviewer not found"}
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        state={**DEFAULT_STATE, "prompt_error": error},
    )
    assert done.returncode == herdr_prompt.EXIT_HERDR
    assert "not found" in done.stderr
    assert "Traceback" not in done.stderr


# ── metadata: PEP 723 conformance ────────────────────────────────────────────────────


def test_pep723_metadata_precedes_docstring() -> None:
    header = SCRIPT.read_text().split('"""', 1)[0]
    assert header.startswith("#!/usr/bin/env python3\n")
    assert "# /// script" in header
    assert 'requires-python = ">=3.12"' in header
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
    assert done.returncode == herdr_prompt.EXIT_OK, done.stderr
    assert "usage: herdr-prompt" in done.stdout
