"""Tests for harness-audit audit script."""

import json
import subprocess
import sys
from pathlib import Path

# conftest adds scripts dir to sys.path
import audit  # type: ignore[import-not-found]


# helpers
def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            _ = f.write(json.dumps(r, ensure_ascii=False) + "\n")


def session_header(sid: str = "test-uuid") -> dict[str, object]:
    return {
        "type": "session",
        "version": 3,
        "id": sid,
        "timestamp": "2026-09-06T00:00:00Z",
        "cwd": "/tmp",
    }


def toolcall_msg(mid: str, parent: str | None, call_id: str, command: str) -> dict[str, object]:
    return {
        "type": "message",
        "id": mid,
        "parentId": parent,
        "timestamp": "2026-09-06T00:00:01Z",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "toolCall",
                    "id": call_id,
                    "name": "bash",
                    "arguments": {"command": command},
                }
            ],
        },
    }


def toolresult_msg(
    mid: str, parent: str | None, call_id: str, text: str, is_error: bool = False
) -> dict[str, object]:
    return {
        "type": "message",
        "id": mid,
        "parentId": parent,
        "timestamp": "2026-09-06T00:00:02Z",
        "message": {
            "role": "toolResult",
            "toolCallId": call_id,
            "toolName": "bash",
            "content": [{"type": "text", "text": text}],
            "isError": is_error,
        },
    }


# --- count_lines ---
def test_count_lines_empty() -> None:
    assert audit.count_lines("") == 0


def test_count_lines_single() -> None:
    assert audit.count_lines("hi") == 1


def test_count_lines_with_newline() -> None:
    assert audit.count_lines("hi\n") == 1


def test_count_lines_multi() -> None:
    assert audit.count_lines("a\nb\nc\n") == 3
    assert audit.count_lines("a\nb\nc") == 3


# --- truncate_body ---
def test_truncate_small_keeps_all() -> None:
    text = "a\nb\nc\n"
    out, removed = audit.truncate_body(text, keep=10)
    assert removed == 0
    assert out == text


def test_truncate_large() -> None:
    text = "\n".join(f"line {i}" for i in range(30)) + "\n"
    out, removed = audit.truncate_body(text, keep=5)
    assert removed == 20  # 30 - 5 - 5
    assert "omitted" in out
    assert out.count("\n") == 11  # 5 + 1 + 5
    assert out.startswith("line 0")
    assert "line 29" in out


def test_truncate_keep_zero() -> None:
    text = "a\nb\nc\n"
    out, removed = audit.truncate_body(text, keep=0)
    assert removed == 3
    assert "omitted" in out
    assert "a" not in out


# --- scan ---
def test_scan_threshold(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    big = "\n".join(f"x {i}" for i in range(25)) + "\n"
    small = "hi\n"
    write_jsonl(
        p,
        [
            session_header(),
            toolcall_msg("a1", None, "call_big", "seq 1 25"),
            toolresult_msg("r1", "a1", "call_big", big),
            toolcall_msg("a2", "r1", "call_small", "echo hi"),
            toolresult_msg("r2", "a2", "call_small", small),
        ],
    )
    res = audit.scan(p, threshold=20)
    assert res["bash_count"] == 2
    assert res["oversized_count"] == 1
    assert res["oversized"][0]["lines"] == 25
    assert res["oversized"][0]["command"] == "seq 1 25"


def test_scan_ignores_non_bash(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            {
                "type": "message",
                "id": "r1",
                "parentId": None,
                "timestamp": "2026-09-06T00:00:02Z",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "call_x",
                    "toolName": "read",
                    "content": [{"type": "text", "text": "x\n" * 100}],
                    "isError": False,
                },
            },
        ],
    )
    res = audit.scan(p, threshold=20)
    assert res["bash_count"] == 0
    assert res["oversized_count"] == 0


def test_scan_pairs_with_pipe_id(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    text = "hello\n" * 30
    write_jsonl(
        p,
        [
            session_header(),
            toolcall_msg("a1", None, "call_abc", "echo big"),
            toolresult_msg("r1", "a1", "call_abc|fc_abc", text),
        ],
    )
    res = audit.scan(p, threshold=20)
    assert res["oversized"][0]["command"] == "echo big"


# --- emit_filtered ---
def test_emit_filtered_preserves_line_count_and_truncates(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    big = "\n".join(f"line {i:02d}" for i in range(30)) + "\n"
    write_jsonl(
        p,
        [
            session_header(),
            toolcall_msg("a1", None, "call_big", "seq 1 30"),
            toolresult_msg("r1", "a1", "call_big", big),
            toolcall_msg("a2", "r1", "call_small", "echo hi"),
            toolresult_msg("r2", "a2", "call_small", "hi\n"),
        ],
    )
    out = audit.emit_filtered(p, threshold=20, keep=5)
    assert out.exists()
    # same record count
    assert len(p.read_text().splitlines()) == len(out.read_text().splitlines())
    # big body truncated
    for line in out.read_text().splitlines():
        d = json.loads(line)
        if d.get("type") == "message" and d.get("message", {}).get("toolCallId") == "call_big":
            txt = d["message"]["content"][0]["text"]
            assert "omitted" in txt
            assert audit.count_lines(txt) == 11  # 5 + 1 + 5


# --- resolve + CLI ---
def test_resolve_by_path(tmp_path: Path) -> None:
    p = tmp_path / "my.jsonl"
    _ = p.write_text("{}\n")
    assert audit.resolve_session(str(p)) == p.resolve()


def test_cli_not_found(tmp_path: Path) -> None:
    res = subprocess.run(
        [sys.executable, str(Path("skills/harness-audit/scripts/audit.py")), "not-a-session-xxxx"],
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )
    assert res.returncode == 2
    assert "no session found" in res.stderr.lower()


def test_cli_json_output(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            toolcall_msg("a1", None, "call_big", "echo hi"),
            toolresult_msg("r1", "a1", "call_big", "hi\n"),
        ],
    )
    res = subprocess.run(
        [sys.executable, str(Path("skills/harness-audit/scripts/audit.py")), str(p), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["bash_count"] == 1


# --- event-stream (message_end) acceptance ---
def test_message_of_accepts_message_end() -> None:
    payload = {"role": "toolResult", "content": []}
    assert audit.message_of({"type": "message_end", "message": payload}) == payload
    assert audit.message_of({"type": "message_update", "message": payload}) is None
    assert audit.message_of({"type": "message", "message": "nope"}) is None


def test_scan_accepts_event_stream(tmp_path: Path) -> None:
    p = tmp_path / "stream.jsonl"
    big = "\n".join(f"x {i}" for i in range(25)) + "\n"
    write_jsonl(
        p,
        [
            {"type": "session", "id": "s"},
            {
                "type": "message_end",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "toolCall",
                            "id": "call_big",
                            "name": "bash",
                            "arguments": {"command": "seq 1 25"},
                        }
                    ],
                },
            },
            {
                "type": "message_end",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "call_big",
                    "toolName": "bash",
                    "content": [{"type": "text", "text": big}],
                    "isError": False,
                },
            },
        ],
    )
    res = audit.scan(p, threshold=20)
    assert res["bash_count"] == 1
    assert res["oversized_count"] == 1
    assert res["oversized"][0]["command"] == "seq 1 25"


def test_emit_filtered_accepts_event_stream(tmp_path: Path) -> None:
    p = tmp_path / "stream.jsonl"
    big = "\n".join(f"line {i:02d}" for i in range(30)) + "\n"
    write_jsonl(
        p,
        [
            {"type": "session", "id": "s"},
            {
                "type": "message_end",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "call_big",
                    "toolName": "bash",
                    "content": [{"type": "text", "text": big}],
                    "isError": False,
                },
            },
        ],
    )
    out = audit.emit_filtered(p, threshold=20, keep=5)
    for line in out.read_text().splitlines():
        d = json.loads(line)
        if d.get("type") == "message_end" and d["message"].get("toolCallId") == "call_big":
            txt = d["message"]["content"][0]["text"]
            assert "omitted" in txt
            assert audit.count_lines(txt) == 11


def test_cli_schema_warning_exits_nonzero(tmp_path: Path) -> None:
    p = tmp_path / "unknown-schema.jsonl"
    write_jsonl(
        p,
        [
            {"type": "session", "id": "s"},
            {"type": "message_start", "message": {"role": "user", "content": []}},
            {"type": "message_update", "delta": "x"},
        ],
    )
    res = subprocess.run(
        [sys.executable, str(Path("skills/harness-audit/scripts/audit.py")), str(p)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 3
    assert "0 bash toolResults" in res.stderr
    assert "schema" in res.stderr.lower()


# --- delivery-cap truncation ---
def test_truncation_footer_requires_kb_limit_suffix() -> None:
    # The too-strict pattern (ending at `of Z]`) must miss; the real footer must match.
    too_strict = "[Showing lines 1-10 of 100]"
    real = "[Showing lines 1-30 of 500 (50.0KB limit). Use offset=31 to continue]"
    assert audit.TRUNCATION_FOOTER_RE.search(too_strict) is None
    assert audit.truncation_of(too_strict) is None
    assert audit.truncation_of(real) == (500, 500 - audit.count_lines(real))


def test_scan_reports_produced_and_omitted(tmp_path: Path) -> None:
    p = tmp_path / "trunc.jsonl"
    body = "\n".join(f"line {i}" for i in range(30))
    text = body + "\n[Showing lines 1-30 of 500 (50.0KB limit). Use offset=31 to continue]\n"
    write_jsonl(
        p,
        [
            session_header(),
            toolcall_msg("a1", None, "call_big", "seq 1 500"),
            toolresult_msg("r1", "a1", "call_big", text),
        ],
    )
    res = audit.scan(p, threshold=20)
    delivered = audit.count_lines(text)
    entry = res["oversized"][0]
    assert entry["lines"] == delivered
    assert entry["produced_lines"] == 500
    assert entry["omitted_lines"] == 500 - delivered
    assert res["total_omitted_lines"] == 500 - delivered
    assert res["truncated_count"] == 1
    out = audit.format_text(res, keep=10)
    assert "Produced but not delivered (delivery cap)" in out


# --- tool census ---
def test_tool_census_counts_all_tools(tmp_path: Path) -> None:
    p = tmp_path / "census.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            toolcall_msg("a1", None, "call_b", "echo hi"),
            toolresult_msg("r1", "a1", "call_b", "hi\n"),
            {
                "type": "message",
                "id": "r2",
                "parentId": "r1",
                "timestamp": "2026-09-06T00:00:03Z",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "call_r",
                    "toolName": "read",
                    "content": [{"type": "text", "text": "a\nb\nc\n"}],
                    "isError": False,
                },
            },
        ],
    )
    res = audit.scan(p, threshold=20)
    assert res["tool_census"]["bash"]["calls"] == 1
    assert res["tool_census"]["read"]["calls"] == 1
    assert res["tool_census"]["read"]["lines"] == 3
    out = audit.format_text(res, keep=10, census=True)
    assert "Tool census" in out
    assert "read" in out
    # all five known tools are always present, zero-filled when unused
    for tool in ("bash", "read", "edit", "write", "undo_last_edit"):
        assert tool in res["tool_census"]
    assert res["tool_census"]["write"]["calls"] == 0


# --- default text shape (locks the conditional delivery-cap summary line) ---
def test_default_text_locks_delivery_cap_line(tmp_path: Path) -> None:
    capped = tmp_path / "capped.jsonl"
    body = "\n".join(f"line {i}" for i in range(30))
    text = body + "\n[Showing lines 1-30 of 500 (50.0KB limit). Use offset=31 to continue]\n"
    write_jsonl(
        capped,
        [
            session_header(),
            toolcall_msg("a1", None, "c1", "seq 1 500"),
            toolresult_msg("r1", "a1", "c1", text),
        ],
    )
    out_capped = audit.format_text(audit.scan(capped, threshold=20), keep=10)
    # exact line + arithmetic: delivered 31, produced 500, omitted 469
    assert (
        "Produced but not delivered (delivery cap): 469 lines omitted across 1 tool results, all tools"
        in out_capped
    )

    plain = tmp_path / "plain.jsonl"
    write_jsonl(
        plain,
        [
            session_header(),
            toolcall_msg("a2", None, "c2", "echo hi"),
            toolresult_msg("r2", "a2", "c2", "hi\n"),
        ],
    )
    out_plain = audit.format_text(audit.scan(plain, threshold=20), keep=10)
    assert "Produced but not delivered" not in out_plain
