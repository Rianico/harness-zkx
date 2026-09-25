"""Tests for skills/herdr/scripts/herdr_transcript.py (session transcript extractor).

Session files are real JSONL fixtures on disk; the shared stub `herdr` only
resolves `agent get` to the fixture path via scripted `agent_get` state.
"""

import json
from collections.abc import Callable
from pathlib import Path

import herdr_cli
import herdr_transcript
import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness

SCRIPT = SCRIPTS_DIR / "herdr_transcript.py"

PI_LINES: list[dict[str, object]] = [
    {"type": "message", "message": {"role": "user", "content": "review the diff"}},
    {
        "type": "message",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "thinking", "text": "let me look"},
                {"type": "text", "text": "First finding: retry loop."},
                {"type": "tool_use", "name": "read", "input": {}},
            ],
        },
    },
    {
        "type": "message",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": "Verdict: ship it."}],
        },
    },
]

CLAUDE_LINES: list[dict[str, object]] = [
    {"type": "human", "message": {"role": "user", "content": "summarize"}},
    {
        "type": "assistant",
        "message": {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Summary here."},
                {"type": "tool_use", "id": "t1", "name": "bash", "input": {}},
            ],
        },
    },
]


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPT)


def session_file(tmp_path: Path, lines: list[dict[str, object]]) -> Path:
    path = tmp_path / "session.jsonl"
    _ = path.write_text("\n".join(json.dumps(line) for line in lines) + "\n", encoding="utf-8")
    return path


def session_state(path: Path, status: str = "done") -> dict[str, object]:
    return {
        **DEFAULT_STATE,
        "agent_get": {"reviewer": {"agent_status": status, "revision": "r3", "session": str(path)}},
    }


# ── unit: line parsing ────────────────────────────────────────────────────────


def test_line_message_reads_pi_shape() -> None:
    line = json.dumps(PI_LINES[1])
    message = herdr_transcript.line_message(line)
    assert message is not None
    assert message.role == "assistant"
    assert message.text == "First finding: retry loop."


def test_line_message_reads_claude_shape() -> None:
    line = json.dumps(CLAUDE_LINES[1])
    message = herdr_transcript.line_message(line)
    assert message is not None
    assert message.text == "Summary here."


def test_line_message_reads_bare_string_content() -> None:
    line = json.dumps({"message": {"role": "user", "content": "  hi  "}})
    assert herdr_transcript.line_message(line) == herdr_transcript.Message("user", "hi")


def test_line_message_skips_tool_only_and_garbage() -> None:
    tool_only = json.dumps(
        {"message": {"role": "assistant", "content": [{"type": "tool_use", "name": "x"}]}}
    )
    assert herdr_transcript.line_message(tool_only) is None
    assert herdr_transcript.line_message("not json{") is None
    assert herdr_transcript.line_message('{"type": "summary"}') is None


def test_select_filters_role_and_last() -> None:
    messages = herdr_transcript.extract_messages("\n".join(json.dumps(line) for line in PI_LINES))
    assert [item.text for item in herdr_transcript.select(messages, role="user", last=False)] == [
        "review the diff"
    ]
    assert [item.text for item in herdr_transcript.select(messages, role="all", last=True)] == [
        "Verdict: ship it."
    ]
    assert len(herdr_transcript.select(messages, role="assistant", last=False)) == 2


# ── integration: extraction through the stub ──────────────────────────────────


def test_last_prints_latest_assistant_response(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--last", state=session_state(session_file(tmp_path, PI_LINES)))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "Verdict: ship it."


def test_claude_session_extracts_clean_text(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--last", state=session_state(session_file(tmp_path, CLAUDE_LINES)))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "Summary here."


def test_role_filter_selects_user_turns(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer", "--role", "user", state=session_state(session_file(tmp_path, PI_LINES))
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "review the diff"


def test_json_prints_role_text_pairs(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "reviewer",
        "--role",
        "all",
        "--json",
        state=session_state(session_file(tmp_path, PI_LINES)),
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    pairs = json.loads(done.stdout)
    assert [(item["role"], item["text"]) for item in pairs] == [
        ("user", "review the diff"),
        ("assistant", "First finding: retry loop."),
        ("assistant", "Verdict: ship it."),
    ]


def test_missing_session_path_falls_back_to_agent_read(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "agent_get": {},
        "agent_read_text": "pane verdict: still working",
    }
    done = stub.run("reviewer", "--last", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "still working" in done.stdout
    assert "reading pane instead" in done.stderr


def test_agent_read_failure_is_herdr_error(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "agent_get": {},
        "agent_read_error": {"code": "agent_not_found", "message": "nope"},
    }
    done = stub.run("reviewer", "--last", state=state)
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "agent read reviewer failed" in done.stderr


def test_empty_match_is_herdr_error(stub: StubHarness, tmp_path: Path) -> None:
    path = tmp_path / "empty.jsonl"
    _ = path.write_text('{"type": "summary", "text": "noise"}\n', encoding="utf-8")
    done = stub.run("reviewer", "--last", state=session_state(path))
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "no extractable messages" in done.stderr


def test_missing_target_is_usage_error(stub: StubHarness) -> None:
    done = stub.run()
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "pass TARGET" in done.stderr


def test_pep723_metadata_precedes_docstring() -> None:
    header = SCRIPT.read_text().split('"""', 1)[0]
    assert header.startswith("#!/usr/bin/env python3\n")
    assert "# /// script" in header
    assert 'requires-python = ">=3.14"' in header
    assert "dependencies = []" in header
    assert header.rstrip().endswith("# ///")
