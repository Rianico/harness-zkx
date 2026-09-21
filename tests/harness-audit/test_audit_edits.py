"""Tests for harness-audit edit workload (audit_edits.py)."""

import json
import subprocess
import sys
from pathlib import Path

import audit_edits  # type: ignore[import-not-found]


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def session_header(sid: str = "test-uuid") -> dict:
    return {
        "type": "session",
        "version": 3,
        "id": sid,
        "timestamp": "2026-09-21T00:00:00Z",
        "cwd": "/tmp",
    }


def edit_call(mid: str, parent: str | None, call_id: str, file: str, edits: list[dict]) -> dict:
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
    mid: str, parent: str | None, call_id: str, text: str, is_error: bool = False
) -> dict:
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


def ok_result(mid: str, parent: str | None, call_id: str) -> dict:
    return edit_result(mid, parent, call_id, "Edited /tmp/a.ts", is_error=False)


def test_classify_codes() -> None:
    assert audit_edits.classify('[MODEL] [E_UNKNOWN_ANCHOR] nothing served "abc"') == "E_UNKNOWN_ANCHOR"
    assert (
        audit_edits.classify('[MODEL] edit[0] failed: [E_FOREIGN_ANCHOR] anchor "x"')
        == "E_FOREIGN_ANCHOR"
    )
    assert audit_edits.classify('[MODEL] [E_BATCH_ABORT] overlapping spans') == "E_BATCH_ABORT"
    assert audit_edits.classify('[MODEL] [E_TARGET_LOST] line gone') == "E_TARGET_LOST"
    assert audit_edits.classify('[MODEL] [E_MALFORMED_ANCHOR] Invalid anchor "10"') == "E_MALFORMED_ANCHOR"


def test_scan_counts_and_rate(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            edit_call("a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]),
            ok_result("r1", "a1", "call_1"),
            edit_call("a2", "r1", "call_2", "/tmp/a.ts", [{"anchor_from": "833", "anchor_to": "833"}]),
            edit_result("r2", "a2", "call_2", '[MODEL] [E_UNKNOWN_ANCHOR] has not served the anchor "833"', True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["edit_count"] == 2
    assert res["success_count"] == 1
    assert res["failure_count"] == 1
    assert res["failure_rate"] == 0.5
    assert res["by_code"] == {"E_UNKNOWN_ANCHOR": 1}


def test_scan_numeric_anchor_flag(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            edit_call("a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "125", "anchor_to": "125"}]),
            edit_result("r1", "a1", "call_1", '[MODEL] [E_UNKNOWN_ANCHOR] has not served the anchor "125"', True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["numeric_anchor_failures"] == 1
    assert res["failures"][0]["numeric_anchors"] == ["125"]
    assert res["failures"][0]["file"] == "/tmp/a.ts"


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
            edit_call("a1", None, "call_1", "/b/types.ts", [{"anchor_from": "AUj", "anchor_to": "AUj"}]),
            edit_result("r1", "a1", "call_1", text, True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["foreign_leak_failures"] == 1
    assert res["failures"][0]["code"] == "E_FOREIGN_ANCHOR"
    assert res["failures"][0]["foreign_served_for"] == "/b/session.ts"


def test_scan_pairs_pipe_id_and_batch_abort(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    text = "[MODEL] [E_BATCH_ABORT] edit[3] overlapping spans — edit[1] and edit[3] overlap."
    write_jsonl(
        p,
        [
            session_header(),
            edit_call("a1", None, "call_abc", "/tmp/s.ts", [{"anchor_from": "UIb", "anchor_to": "WZQ"}]),
            edit_result("r1", "a1", "call_abc|fc_abc", text, True),
        ],
    )
    res = audit_edits.scan(p)
    assert res["failure_count"] == 1
    assert res["failures"][0]["code"] == "E_BATCH_ABORT"
    assert res["failures"][0]["file"] == "/tmp/s.ts"


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


def test_scan_with_context(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            edit_call("a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "zzz", "anchor_to": "zzz"}]),
            edit_result("r1", "a1", "call_1", '[MODEL] [E_UNKNOWN_ANCHOR] anchor "zzz"', True),
            {
                "type": "message",
                "id": "a2",
                "parentId": "r1",
                "timestamp": "2026-09-21T00:00:03Z",
                "message": {"role": "assistant", "content": [{"type": "text", "text": "retry after read"}]},
            },
        ],
    )
    res = audit_edits.scan(p, with_context=1)
    assert len(res["failures"][0]["next_turns"]) == 1
    assert res["failures"][0]["next_turns"][0]["role"] == "assistant"


def test_cli_not_found() -> None:
    res = subprocess.run(
        [sys.executable, str(Path("skills/harness-audit/scripts/audit_edits.py")), "not-a-session-xxxx"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 2
    assert "no session found" in res.stderr.lower()


def test_cli_json_output(tmp_path: Path) -> None:
    p = tmp_path / "sess.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            edit_call("a1", None, "call_1", "/tmp/a.ts", [{"anchor_from": "aBc", "anchor_to": "aBc"}]),
            ok_result("r1", "a1", "call_1"),
        ],
    )
    res = subprocess.run(
        [sys.executable, str(Path("skills/harness-audit/scripts/audit_edits.py")), str(p), "--json"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["edit_count"] == 1
    assert data["failure_count"] == 0
