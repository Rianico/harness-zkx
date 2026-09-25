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
