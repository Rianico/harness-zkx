"""Tests for harness-audit audit script."""

import json
import subprocess
import sys
from pathlib import Path

# conftest adds scripts dir to sys.path
import audit  # type: ignore[import-not-found]


# helpers
def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def session_header(sid: str = "test-uuid") -> dict:
    return {
        "type": "session",
        "version": 3,
        "id": sid,
        "timestamp": "2026-09-06T00:00:00Z",
        "cwd": "/tmp",
    }


def toolcall_msg(mid: str, parent: str | None, call_id: str, command: str) -> dict:
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
) -> dict:
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
    p.write_text("{}\n")
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
