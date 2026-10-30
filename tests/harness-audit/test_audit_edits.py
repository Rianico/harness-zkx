"""Tests for harness-audit edit workload (audit_edits.py)."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import audit_edits  # type: ignore[import-not-found]

_SCRIPT = (
    Path(__file__).resolve().parent.parent.parent
    / "skills"
    / "harness-audit"
    / "scripts"
    / "audit_edits.py"
)


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            _ = f.write(json.dumps(r, ensure_ascii=False) + "\n")


def session_header(sid: str = "test-uuid") -> dict[str, Any]:
    return {
        "type": "session",
        "version": 3,
        "id": sid,
        "timestamp": "2026-09-21T00:00:00Z",
        "cwd": "/tmp",
    }


def edit_call(
    mid: str,
    parent: str | None,
    call_id: str,
    file: str,
    edits: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "type": "message",
        "id": mid,
        "parentId": parent,
        "timestamp": "2026-09-21T00:00:01Z",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "toolCall",
                    "id": call_id,
                    "name": "edit",
                    "arguments": {"file": file, "edits": edits},
                }
            ],
        },
    }


def edit_result(
    mid: str,
    parent: str | None,
    call_id: str,
    text: str,
    is_error: bool = False,
) -> dict[str, Any]:
    return {
        "type": "message",
        "id": mid,
        "parentId": parent,
        "timestamp": "2026-09-21T00:00:02Z",
        "message": {
            "role": "toolResult",
            "toolCallId": call_id,
            "toolName": "edit",
            "content": [{"type": "text", "text": text}],
            "isError": is_error,
        },
    }


def ok_result(mid: str, parent: str | None, call_id: str) -> dict[str, Any]:
    return edit_result(mid, parent, call_id, "Edited /tmp/a.ts", is_error=False)


def assistant_text(mid: str, parent: str | None, text: str) -> dict[str, Any]:
    return {
        "type": "message",
        "id": mid,
        "parentId": parent,
        "timestamp": "2026-09-21T00:00:03Z",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": text}],
        },
    }


def test_classify_codes() -> None:
    assert (
        audit_edits.classify('[MODEL] [E_UNKNOWN_ANCHOR] nothing served "abc"')
        == "E_UNKNOWN_ANCHOR"
    )
    assert (
        audit_edits.classify('[MODEL] edit[0] failed: [E_FOREIGN_ANCHOR] anchor "x"')
        == "E_FOREIGN_ANCHOR"
    )
    assert audit_edits.classify("[MODEL] [E_BATCH_ABORT] overlapping spans") == "E_BATCH_ABORT"
    assert audit_edits.classify("[MODEL] [E_TARGET_LOST] line gone") == "E_TARGET_LOST"
    assert (
        audit_edits.classify('[MODEL] [E_MALFORMED_ANCHOR] Invalid anchor "10"')
        == "E_MALFORMED_ANCHOR"
    )


def test_categorize() -> None:
    assert audit_edits.categorize("E_UNKNOWN_ANCHOR", ["833"], False) == "N"
    assert audit_edits.categorize("E_FOREIGN_ANCHOR", [], True) == "F"
    assert audit_edits.categorize("E_UNKNOWN_ANCHOR", [], True) == "F"
    assert audit_edits.categorize("E_BATCH_ABORT", [], False) == "B"
    assert audit_edits.categorize("E_TARGET_LOST", [], False) == "T"
    assert audit_edits.categorize("E_MALFORMED_ANCHOR", [], False) == "M"
    assert audit_edits.categorize("E_UNKNOWN_ANCHOR", [], False) == "H"
    assert audit_edits.categorize("E_STALE_ANCHOR", [], False) == "H"
    assert audit_edits.categorize("E_UNSERVED_RANGE", [], False) == "H"
    assert audit_edits.categorize("E_FUTURE_CODE", [], False) == "?"


def test_scan_counts_and_rate(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            edit_call(
                "a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]
            ),
            ok_result("r1", "a1", "call_1"),
            edit_call(
                "a2", "r1", "call_2", "/tmp/a.ts", [{"anchor_from": "833", "anchor_to": "833"}]
            ),
            edit_result(
                "r2",
                "a2",
                "call_2",
                '[MODEL] [E_UNKNOWN_ANCHOR] has not served the anchor "833"',
                True,
            ),
        ],
    )
    res = audit_edits.scan(p)
    assert res["edit_count"] == 2
    assert res["success_count"] == 1
    assert res["failure_count"] == 1
    assert res["failure_rate"] == 0.5
    assert res["by_code"] == {"E_UNKNOWN_ANCHOR": 1}
    assert res["failures"][0]["category"] == "N"


def test_scan_numeric_anchor_flag(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            edit_call(
                "a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "125", "anchor_to": "125"}]
            ),
            edit_result(
                "r1",
                "a1",
                "call_1",
                '[MODEL] [E_UNKNOWN_ANCHOR] has not served the anchor "125"',
                True,
            ),
        ],
    )
    res = audit_edits.scan(p)
    assert res["numeric_anchor_failures"] == 1
    assert res["failures"][0]["numeric_anchors"] == ["125"]
    assert res["failures"][0]["file"] == "/tmp/a.ts"
    assert res["failures"][0]["category"] == "N"


def test_scan_foreign_leak(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    text = (
        '[MODEL] edit[2] (/b/types.ts) failed: [E_FOREIGN_ANCHOR] the anchor "AUj" '
        "is inconsistent with /b/types.ts; served for /b/session.ts; nothing was written."
    )
    write_jsonl(
        p,
        [
            session_header(),
            edit_call(
                "a1", None, "call_1", "/b/types.ts", [{"anchor_from": "AUj", "anchor_to": "AUj"}]
            ),
            edit_result("r1", "a1", "call_1", text, True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["foreign_leak_failures"] == 1
    assert res["failures"][0]["code"] == "E_FOREIGN_ANCHOR"
    assert res["failures"][0]["foreign_served_for"] == "/b/session.ts"
    assert res["failures"][0]["category"] == "F"


def test_scan_served_for_at_end_of_line(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    text = '[MODEL] [E_UNKNOWN_ANCHOR] anchor "AUj" not served for /b/types.ts; served for /b/session.ts'
    write_jsonl(
        p,
        [
            session_header(),
            edit_call(
                "a1", None, "call_1", "/b/types.ts", [{"anchor_from": "AUj", "anchor_to": "AUj"}]
            ),
            edit_result("r1", "a1", "call_1", text, True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["foreign_leak_failures"] == 1
    assert res["failures"][0]["foreign_served_for"] == "/b/session.ts"
    assert res["failures"][0]["category"] == "F"


def test_scan_relative_path_fallback(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    text = '[MODEL] [E_UNKNOWN_ANCHOR] edit[0] (src/index.ts) failed: anchor "zz" not served'
    write_jsonl(
        p,
        [
            session_header(),
            edit_result("r1", None, "call_orphan", text, True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["failure_count"] == 1
    assert res["failures"][0]["file"] == "src/index.ts"


def test_scan_pairs_pipe_id_and_batch_abort(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    text = "[MODEL] [E_BATCH_ABORT] edit[3] overlapping spans — edit[1] and edit[3] overlap."
    write_jsonl(
        p,
        [
            session_header(),
            edit_call(
                "a1", None, "call_abc", "/tmp/s.ts", [{"anchor_from": "UIb", "anchor_to": "WZQ"}]
            ),
            edit_result("r1", "a1", "call_abc|fc_abc", text, True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["failure_count"] == 1
    assert res["failures"][0]["code"] == "E_BATCH_ABORT"
    assert res["failures"][0]["file"] == "/tmp/s.ts"
    assert res["failures"][0]["category"] == "B"


def test_scan_unknown_code_category(tmp_path: Path, capsys: Any) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            edit_call(
                "a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]
            ),
            edit_result("r1", "a1", "call_1", "[MODEL] [E_FUTURE_CODE] something new", True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["failures"][0]["code"] == "E_FUTURE_CODE"
    assert res["failures"][0]["category"] == "?"
    assert "E_FUTURE_CODE" in capsys.readouterr().err


def test_scan_ignores_non_edit(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            {
                "type": "message",
                "id": "r1",
                "parentId": None,
                "timestamp": "2026-09-21T00:00:02Z",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "call_x",
                    "toolName": "bash",
                    "content": [{"type": "text", "text": "x\n" * 100}],
                    "isError": False,
                },
            },
        ],
    )
    res = audit_edits.scan(p)
    assert res["edit_count"] == 0
    assert res["failure_count"] == 0


def test_scan_counts_parse_errors(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    with p.open("w", encoding="utf-8") as f:
        _ = f.write(json.dumps(session_header()) + "\n")
        _ = f.write("{not valid json\n")
        _ = f.write("[1, 2, 3]\n")
        _ = f.write(
            json.dumps(
                edit_call(
                    "a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "zzz", "anchor_to": "zzz"}]
                )
            )
            + "\n"
        )
        _ = f.write(
            json.dumps(
                edit_result("r1", "a1", "call_1", '[MODEL] [E_UNKNOWN_ANCHOR] anchor "zzz"', True)
            )
            + "\n"
        )
    res = audit_edits.scan(p)
    assert res["parse_errors"] == 1  # only the invalid-JSON line; "[1,2,3]" parses but is skipped
    assert res["record_count"] == 5
    assert res["failure_count"] == 1


def test_scan_with_context(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            edit_call(
                "a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "zzz", "anchor_to": "zzz"}]
            ),
            edit_result("r1", "a1", "call_1", '[MODEL] [E_UNKNOWN_ANCHOR] anchor "zzz"', True),
            assistant_text("a2", "r1", "retry after read"),
        ],
    )
    res = audit_edits.scan(p, with_context=1)
    assert len(res["failures"][0]["next_turns"]) == 1
    assert res["failures"][0]["next_turns"][0]["role"] == "assistant"
    assert res["full_context_by_line"][res["failures"][0]["jsonl_line"]][0]["role"] == "assistant"


def test_cli_not_found() -> None:
    res = subprocess.run(
        [sys.executable, str(_SCRIPT), "not-a-session-xxxx"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    assert "no session found" in res.stderr.lower()


def test_cli_rejects_negative_context(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(p, [session_header()])
    res = subprocess.run(
        [sys.executable, str(_SCRIPT), str(p), "--with-context", "-1"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 1
    assert "--with-context" in res.stderr


def test_cli_dump_context(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            edit_call(
                "a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "zzz", "anchor_to": "zzz"}]
            ),
            edit_result("r1", "a1", "call_1", '[MODEL] [E_UNKNOWN_ANCHOR] anchor "zzz"', True),
            assistant_text("a2", "r1", "retry after read"),
        ],
    )
    dump_dir = tmp_path / "dump"
    res = subprocess.run(
        [sys.executable, str(_SCRIPT), str(p), "--dump-context", str(dump_dir)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    files = list(dump_dir.glob("edit-failure-*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["failure"]["code"] == "E_UNKNOWN_ANCHOR"
    assert payload["failure"]["category"] == "H"
    assert len(payload["next_turns_full"]) == 1
    assert payload["next_turns_full"][0]["role"] == "assistant"


def test_cli_json_output(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            edit_call(
                "a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]
            ),
            ok_result("r1", "a1", "call_1"),
        ],
    )
    res = subprocess.run(
        [sys.executable, str(_SCRIPT), str(p), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["edit_count"] == 1
    assert data["failure_count"] == 0
    assert "full_context_by_line" not in data


# --- full code registry + applied-tier warnings ---
def test_code_registry_is_complete() -> None:
    assert len(audit_edits.ERROR_CODES) == 19
    assert len(audit_edits.WARNING_CODES) == 6
    assert "E_BAD_PAYLOAD" in audit_edits.KNOWN_CODES
    assert "E_NOT_FOUND" in audit_edits.KNOWN_CODES
    assert "E_UNSERVED_RANGE" in audit_edits.KNOWN_CODES  # legacy, still recognized


def test_categorize_extended_letters() -> None:
    assert audit_edits.categorize("E_BAD_PAYLOAD", [], False) == "P"
    assert audit_edits.categorize("E_NOT_FOUND", [], False) == "R"
    assert audit_edits.categorize("E_ACCESS", [], False) == "R"
    assert audit_edits.categorize("E_UNSUPPORTED_FILE", [], False) == "R"
    assert audit_edits.categorize("E_LARGE_FILE", [], False) == "R"
    assert audit_edits.categorize("E_SUSPICIOUS_TEXT", [], False) == "G"
    assert audit_edits.categorize("E_EMPTY_RANGE", [], False) == "G"
    assert audit_edits.categorize("E_NOOP_LOOP", [], False) == "G"
    assert audit_edits.categorize("E_UNDO_STALE", [], False) == "U"
    assert audit_edits.categorize("E_UNDO_UNAVAILABLE", [], False) == "U"
    assert audit_edits.categorize("E_STALE_RANGE", [], False) == "H"
    assert audit_edits.categorize("E_UNVERIFIED_RANGE", [], False) == "H"
    assert audit_edits.categorize("E_UNKNOWN", [], False) == "?"


def test_scan_bad_payload_and_warning(tmp_path: Path, capsys: Any) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            edit_call(
                "a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]
            ),
            edit_result(
                "r1",
                "a1",
                "call_1",
                "[MODEL] [E_BAD_PAYLOAD] payload failed contract validation",
                True,
            ),
            edit_call(
                "a2", "r1", "call_2", "/tmp/b.ts", [{"anchor_from": "DdE", "anchor_to": "FfG"}]
            ),
            edit_result(
                "r2",
                "a2",
                "call_2",
                "[MODEL] [W_REVERSED_ANCHORS] applied with reversed anchors",
                False,
            ),
        ],
    )
    res = audit_edits.scan(p)
    assert res["by_code"] == {"E_BAD_PAYLOAD": 1}
    assert res["failures"][0]["category"] == "P"
    assert "?" not in {f["category"] for f in res["failures"]}
    assert res["warning_count"] == 1
    assert res["by_warning_code"] == {"W_REVERSED_ANCHORS": 1}
    assert res["warnings"][0]["code"] == "W_REVERSED_ANCHORS"
    assert res["warnings"][0]["is_error"] is False
    out = audit_edits.format_text(res)
    assert "Applied-tier warnings" in out
    assert "W_REVERSED_ANCHORS" in out
    # a recognized code must not trigger the unknown-code stderr warning
    assert "E_BAD_PAYLOAD" not in capsys.readouterr().err


def test_scan_accepts_event_stream(tmp_path: Path) -> None:
    p = tmp_path / "stream.jsonl"
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
                            "id": "call_1",
                            "name": "edit",
                            "arguments": {
                                "file": "/tmp/a.ts",
                                "edits": [{"anchor_from": "aBc", "anchor_to": "aBc"}],
                            },
                        }
                    ],
                },
            },
            {
                "type": "message_end",
                "message": {
                    "role": "toolResult",
                    "toolCallId": "call_1",
                    "toolName": "edit",
                    "content": [
                        {
                            "type": "text",
                            "text": '[MODEL] [E_UNKNOWN_ANCHOR] anchor "aBc" not served',
                        }
                    ],
                    "isError": True,
                },
            },
        ],
    )
    res = audit_edits.scan(p)
    assert res["edit_count"] == 1
    assert res["failure_count"] == 1
    assert res["failures"][0]["code"] == "E_UNKNOWN_ANCHOR"


# --- pi-subagents transcripts (recordType schema) ---
def transcript_tool_start(
    call_id: str,
    file: str,
    edits: list[dict[str, Any]],
    run_id: str = "run-1",
    tool_name: str = "edit",
) -> dict[str, Any]:
    return {
        "version": 1,
        "recordType": "tool_start",
        "source": "async",
        "runId": run_id,
        "agent": "worker",
        "childIndex": 0,
        "cwd": "/tmp",
        "sourceEventType": "tool_execution_start",
        "toolCallId": call_id,
        "toolName": tool_name,
        "argsPayload": json.dumps({"file": file, "edits": edits}),
        "argsPreview": f"file={file}",
    }


def transcript_tool_end(
    call_id: str, is_error: bool, run_id: str = "run-1", tool_name: str = "edit"
) -> dict[str, Any]:
    return {
        "version": 1,
        "recordType": "tool_end",
        "source": "async",
        "runId": run_id,
        "agent": "worker",
        "childIndex": 0,
        "cwd": "/tmp",
        "sourceEventType": "tool_execution_end",
        "toolCallId": call_id,
        "toolName": tool_name,
        "isError": is_error,
    }


def transcript_result(
    call_id: str,
    text: str,
    is_error: bool,
    run_id: str = "run-1",
    tool_name: str = "edit",
) -> dict[str, Any]:
    return {
        "version": 1,
        "recordType": "message",
        "source": "async",
        "runId": run_id,
        "agent": "worker",
        "childIndex": 0,
        "cwd": "/tmp",
        "sourceEventType": "message_end",
        "role": "toolResult",
        "toolCallId": call_id,
        "toolName": tool_name,
        "isError": is_error,
        "text": text,
        "message": {
            "role": "toolResult",
            "toolCallId": call_id,
            "toolName": tool_name,
            "isError": is_error,
            "content": [{"type": "text", "text": text}],
        },
    }


def test_scan_transcript_counts_and_failures(tmp_path: Path) -> None:
    p = tmp_path / "worker_transcript.jsonl"
    write_jsonl(
        p,
        [
            transcript_tool_start(
                "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]
            ),
            transcript_tool_end("call_1", False),
            transcript_result("call_1", "Edited /tmp/a.ts", False),
            transcript_tool_start(
                "call_2", "/tmp/a.ts", [{"anchor_from": "833", "anchor_to": "833"}]
            ),
            transcript_tool_end("call_2", True),
            transcript_result(
                "call_2",
                '[MODEL] [E_UNKNOWN_ANCHOR] has not served the anchor "833"',
                True,
            ),
        ],
    )
    res = audit_edits.scan(p)
    assert res["edit_count"] == 2
    assert res["success_count"] == 1
    assert res["failure_count"] == 1
    assert res["failure_rate"] == 0.5
    assert res["by_code"] == {"E_UNKNOWN_ANCHOR": 1}
    assert res["failures"][0]["file"] == "/tmp/a.ts"
    assert res["failures"][0]["category"] == "N"


def test_scan_transcript_dedupes_tool_end_and_message(tmp_path: Path) -> None:
    p = tmp_path / "dedup_transcript.jsonl"
    write_jsonl(
        p,
        [
            transcript_tool_start(
                "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]
            ),
            transcript_tool_end("call_1", True),
            transcript_result("call_1", "[MODEL] [E_UNKNOWN_ANCHOR] nope", True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["edit_count"] == 1  # not 2: tool_end + message share a toolCallId
    assert res["failure_count"] == 1


def test_scan_transcript_tool_end_fallback(tmp_path: Path) -> None:
    p = tmp_path / "fallback_transcript.jsonl"
    write_jsonl(
        p,
        [
            transcript_tool_start(
                "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]
            ),
            transcript_tool_end("call_1", True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["edit_count"] == 1
    assert res["failure_count"] == 1
    assert res["failures"][0]["file"] == "/tmp/a.ts"


def test_scan_transcript_ignores_markers_in_read_and_bash(tmp_path: Path) -> None:
    p = tmp_path / "read_bash_transcript.jsonl"
    write_jsonl(
        p,
        [
            transcript_tool_start("call_r", "/tmp/a.ts", [], tool_name="read"),
            transcript_result(
                "call_r", "bundled JS contains [E_FOO] and [W_BAR]", False, tool_name="read"
            ),
            transcript_tool_start("call_b", "", [], tool_name="bash"),
            transcript_result("call_b", "[E_BAZ] [W_QUX]", False, tool_name="bash"),
        ],
    )
    res = audit_edits.scan(p)
    assert res["edit_count"] == 0
    assert res["failure_count"] == 0
    assert res["warning_count"] == 0
    assert res["by_code"] == {}


def test_scan_transcript_numeric_anchor_malformed(tmp_path: Path) -> None:
    p = tmp_path / "malformed_transcript.jsonl"
    text = (
        '[MODEL] edit[1] (/tmp/a.ts) failed: [E_MALFORMED_ANCHOR] The anchor "155" '
        'is not valid: Use the hash alone (e.g. "aB3x") — no line numbers.'
    )
    write_jsonl(
        p,
        [
            transcript_tool_start(
                "call_1",
                "/tmp/a.ts",
                [{"anchor_from": "155", "anchor_to": "156"}],
            ),
            transcript_tool_end("call_1", True),
            transcript_result("call_1", text, True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["numeric_anchor_failures"] >= 1
    assert res["failures"][0]["code"] == "E_MALFORMED_ANCHOR"
    assert res["failures"][0]["category"] == "N"
    assert "155" in res["failures"][0]["numeric_anchors"]


def test_scan_transcript_evidence_failure_codes(tmp_path: Path) -> None:
    p = tmp_path / "evidence_transcript.jsonl"
    cases = [
        (
            "call_f",
            "/b/types.ts",
            [{"anchor_from": "AUj", "anchor_to": "AUj"}],
            '[MODEL] edit[0] (/b/types.ts) failed: [E_FOREIGN_ANCHOR] the anchor "AUj" '
            "is inconsistent with /b/types.ts; served for /b/session.ts; nothing was written.",
        ),
        (
            "call_r",
            "/tmp/missing.ts",
            [{"anchor_from": "VowA", "anchor_to": "KTMv"}],
            "[MODEL] [E_NOT_FOUND] File not found: /tmp/missing.ts.",
        ),
        (
            "call_p",
            "/tmp/a.ts",
            [{"anchor_from": "nTEL", "anchor_to": "I52c"}],
            "[MODEL] [E_BAD_PAYLOAD] The edit payload is not valid: edit[0] has "
            'unsupported field(s) "text_unchanged_check".',
        ),
        (
            "call_m",
            "/tmp/a.ts",
            [{"anchor_from": "155", "anchor_to": "156"}],
            '[MODEL] edit[1] (/tmp/a.ts) failed: [E_MALFORMED_ANCHOR] The anchor "155" '
            "is not valid.",
        ),
    ]
    records: list[dict[str, Any]] = []
    for call_id, file, edits, text in cases:
        records += [
            transcript_tool_start(call_id, file, edits),
            transcript_tool_end(call_id, True),
            transcript_result(call_id, text, True),
        ]
    write_jsonl(p, records)
    res = audit_edits.scan(p)
    assert set(res["by_code"]) == {
        "E_FOREIGN_ANCHOR",
        "E_NOT_FOUND",
        "E_BAD_PAYLOAD",
        "E_MALFORMED_ANCHOR",
    }
    cats = {f["code"]: f["category"] for f in res["failures"]}
    assert cats["E_FOREIGN_ANCHOR"] == "F"
    assert cats["E_NOT_FOUND"] == "R"
    assert cats["E_BAD_PAYLOAD"] == "P"
    # Intrinsic category for the code is M; a numeric anchor overrides to N.
    assert audit_edits.categorize("E_MALFORMED_ANCHOR", [], False) == "M"
    assert cats["E_MALFORMED_ANCHOR"] == "N"


def test_scan_auto_discovers_transcripts(tmp_path: Path) -> None:
    session = tmp_path / "sess.jsonl"
    write_jsonl(session, [session_header()])
    artifacts = tmp_path / "subagent-artifacts"
    artifacts.mkdir()
    transcript = artifacts / "abc_worker_transcript.jsonl"
    write_jsonl(
        transcript,
        [
            transcript_tool_start(
                "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]
            ),
            transcript_tool_end("call_1", False),
            transcript_result("call_1", "Edited /tmp/a.ts", False),
        ],
    )
    res = audit_edits.scan(session)
    assert res["edit_count"] == 1
    assert res["transcript_count"] == 1
    assert res["transcripts"] == [str(transcript)]
    assert res["schema_recognized"] is True


def test_scan_transcripts_can_be_disabled(tmp_path: Path) -> None:
    session = tmp_path / "sess.jsonl"
    write_jsonl(session, [session_header()])
    artifacts = tmp_path / "subagent-artifacts"
    artifacts.mkdir()
    write_jsonl(
        artifacts / "abc_worker_transcript.jsonl",
        [
            transcript_tool_start(
                "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]
            ),
            transcript_tool_end("call_1", False),
            transcript_result("call_1", "Edited /tmp/a.ts", False),
        ],
    )
    res = audit_edits.scan(session, transcripts=False)
    assert res["edit_count"] == 0
    assert res["transcript_count"] == 0


def test_scan_transcript_assistant_toolcall_fallback(tmp_path: Path) -> None:
    p = tmp_path / "assistant_transcript.jsonl"
    write_jsonl(
        p,
        [
            {
                "version": 1,
                "recordType": "message",
                "sourceEventType": "message_end",
                "runId": "run-1",
                "role": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "toolCall",
                            "id": "call_1",
                            "name": "edit",
                            "arguments": {
                                "file": "/tmp/from-assistant.ts",
                                "edits": [{"anchor_from": "zzz", "anchor_to": "zzz"}],
                            },
                        }
                    ],
                },
            },
            transcript_result("call_1", '[MODEL] [E_UNKNOWN_ANCHOR] anchor "zzz" not served', True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["edit_count"] == 1
    assert res["failures"][0]["file"] == "/tmp/from-assistant.ts"


def test_cli_transcript_json(tmp_path: Path) -> None:
    p = tmp_path / "worker_transcript.jsonl"
    write_jsonl(
        p,
        [
            transcript_tool_start(
                "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]
            ),
            transcript_tool_end("call_1", False),
            transcript_result("call_1", "Edited /tmp/a.ts", False),
        ],
    )
    res = subprocess.run(
        [sys.executable, str(_SCRIPT), str(p), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["edit_count"] == 1
    assert data["failure_count"] == 0


def test_cli_unrecognized_schema_exits_3(tmp_path: Path) -> None:
    p = tmp_path / "mystery.jsonl"
    write_jsonl(p, [{"foo": "bar"}, {"baz": 1}])
    res = subprocess.run(
        [sys.executable, str(_SCRIPT), str(p)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 3
    assert "schema" in res.stderr.lower()


def test_cli_help_mentions_transcripts() -> None:
    res = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "transcript" in res.stdout.lower()


# --- T3: merge semantics, provenance uniformity, call attribution ---
def test_scan_merged_skips_unrecognized_file(tmp_path: Path, capsys: Any) -> None:
    session = tmp_path / "sess.jsonl"
    write_jsonl(
        session,
        [
            session_header(),
            edit_call(
                "a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]
            ),
            ok_result("r1", "a1", "call_1"),
        ],
    )
    artifacts = tmp_path / "subagent-artifacts"
    artifacts.mkdir()
    bad = artifacts / "bad_worker_transcript.jsonl"
    write_jsonl(bad, [{"foo": "bar"}, {"baz": 1}])
    res = audit_edits.scan(session)
    assert res["edit_count"] == 1  # counts come from the recognized main file only
    assert res["failure_count"] == 0
    assert res["schema_recognized"] is True
    assert res["skipped_files"] == [bad.name]
    err = capsys.readouterr().err
    assert "bad_worker_transcript.jsonl" in err
    assert "unrecognized schema" in err


def test_scan_merged_all_unrecognized_schema(tmp_path: Path, capsys: Any) -> None:
    session = tmp_path / "mystery.jsonl"
    write_jsonl(session, [{"foo": "bar"}])
    artifacts = tmp_path / "subagent-artifacts"
    artifacts.mkdir()
    bad = artifacts / "bad_worker_transcript.jsonl"
    write_jsonl(bad, [{"baz": 1}])
    res = audit_edits.scan(session)
    assert res["schema_recognized"] is False
    assert res["record_count"] == 0  # skipped files are excluded from counts
    assert res["skipped_files"] == [session.name, bad.name]
    err = capsys.readouterr().err
    assert "mystery.jsonl" in err
    assert "bad_worker_transcript.jsonl" in err


def test_cli_merged_good_and_bad_transcript_exits_0(tmp_path: Path) -> None:
    session = tmp_path / "sess.jsonl"
    write_jsonl(
        session,
        [
            session_header(),
            edit_call(
                "a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]
            ),
            ok_result("r1", "a1", "call_1"),
        ],
    )
    artifacts = tmp_path / "subagent-artifacts"
    artifacts.mkdir()
    write_jsonl(artifacts / "bad_worker_transcript.jsonl", [{"foo": "bar"}])
    res = subprocess.run(
        [sys.executable, str(_SCRIPT), str(session), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["edit_count"] == 1
    assert "bad_worker_transcript.jsonl" in res.stderr


def test_cli_merged_all_unrecognized_exits_3(tmp_path: Path) -> None:
    session = tmp_path / "mystery.jsonl"
    write_jsonl(session, [{"foo": "bar"}])
    artifacts = tmp_path / "subagent-artifacts"
    artifacts.mkdir()
    write_jsonl(artifacts / "bad_worker_transcript.jsonl", [{"baz": 1}])
    res = subprocess.run(
        [sys.executable, str(_SCRIPT), str(session)],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 3
    assert "schema" in res.stderr.lower()


def test_scan_provenance_uniform_single_vs_merged(tmp_path: Path) -> None:
    session = tmp_path / "sess.jsonl"
    write_jsonl(session, [session_header()])
    artifacts = tmp_path / "subagent-artifacts"
    artifacts.mkdir()
    transcript = artifacts / "abc_worker_transcript.jsonl"
    write_jsonl(
        transcript,
        [
            transcript_tool_start(
                "call_1", "/tmp/a.ts", [{"anchor_from": "zzz", "anchor_to": "zzz"}]
            ),
            transcript_tool_end("call_1", True),
            transcript_result("call_1", '[MODEL] [E_UNKNOWN_ANCHOR] anchor "zzz" not served', True),
            {
                "recordType": "message",
                "runId": "run-1",
                "sourceEventType": "message_end",
                "role": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "retry after read"}],
                },
            },
        ],
    )
    single = audit_edits.scan(transcript, with_context=1)
    merged = audit_edits.scan(session, with_context=1)
    assert single["failures"][0]["source_file"] == transcript.name
    assert merged["failures"][0]["source_file"] == transcript.name
    assert isinstance(single["failures"][0]["context_key"], str)
    assert single["failures"][0]["context_key"] == merged["failures"][0]["context_key"]
    single_types = {type(k) for k in single["full_context_by_line"]}
    merged_types = {type(k) for k in merged["full_context_by_line"]}
    assert single_types == merged_types
    assert len(single["failures"][0]["next_turns"]) == 1


def test_scan_runid_collision_attributes_own_call(tmp_path: Path) -> None:
    p = tmp_path / "collision_transcript.jsonl"
    write_jsonl(
        p,
        [
            transcript_tool_start(
                "call_dup",
                "/tmp/run1.ts",
                [{"anchor_from": "aaaa", "anchor_to": "aaaa"}],
                run_id="run-1",
            ),
            transcript_tool_start(
                "call_dup",
                "/tmp/run2.ts",
                [{"anchor_from": "bbbb", "anchor_to": "bbbb"}],
                run_id="run-2",
            ),
            transcript_tool_end("call_dup", True, run_id="run-1"),
            transcript_result(
                "call_dup", '[MODEL] [E_UNKNOWN_ANCHOR] anchor "aaaa"', True, run_id="run-1"
            ),
            transcript_tool_end("call_dup", True, run_id="run-2"),
            transcript_result(
                "call_dup", '[MODEL] [E_UNKNOWN_ANCHOR] anchor "bbbb"', True, run_id="run-2"
            ),
        ],
    )
    res = audit_edits.scan(p)
    assert res["edit_count"] == 2
    assert res["failure_count"] == 2
    assert res["failures"][0]["file"] == "/tmp/run1.ts"
    assert res["failures"][1]["file"] == "/tmp/run2.ts"
    assert "aaaa" in res["failures"][0]["anchors"]
    assert "bbbb" in res["failures"][1]["anchors"]
