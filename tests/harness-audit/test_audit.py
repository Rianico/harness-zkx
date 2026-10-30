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
    # DELIBERATE regression-lock update (ha-fix-A): the "(N.NKB limit)" suffix is no
    # longer the discriminator — a recognized output tail is. The bare pattern (no
    # suffix, no path) must still miss; every real footer shape must match.
    too_strict = "[Showing lines 1-10 of 100]"
    real = "[Showing lines 1-30 of 500 (50.0KB limit). Use offset=31 to continue]"
    assert audit.TRUNCATION_FOOTER_RE.search(too_strict) is None
    assert audit.truncation_of(too_strict) is None
    # Footer-derived delivered = B - A + 1 = 30; the blank separator + footer are chrome.
    assert audit.truncation_of(real) == (500, 470)


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
    # DELIBERATE regression-lock update (ha-fix-A): delivered is footer-derived
    # (B - A + 1 = 30), not count_lines(text) (which counts the footer as content).
    entry = res["oversized"][0]
    assert entry["lines"] == 30
    assert entry["produced_lines"] == 500
    assert entry["omitted_lines"] == 470
    assert res["total_omitted_lines"] == 470
    assert res["truncated_count"] == 1
    out = audit.format_text(res, keep=10)
    assert "Produced but not delivered (delivery cap)" in out


# --- delivery-cap footer shapes (P3/P4) ---
def _cap_session(tmp_path: Path, name: str, text: str) -> Path:
    """One bash toolCall/result pair whose result text carries a delivery-cap footer."""
    p = tmp_path / name
    write_jsonl(
        p,
        [
            session_header(),
            toolcall_msg("a1", None, "c1", "seq 1 500"),
            toolresult_msg("r1", "a1", "c1", text),
        ],
    )
    return p


def test_capped_delivered_count_excludes_footer_chrome(tmp_path: Path) -> None:
    """P3: the blank separator + footer line must not count as delivered content.

    Evidence session jsonl line 56: A=6, B=84, Z=84, count_lines(text)=81. The old
    rule reported 3 omitted; the footer implies 84 - (84 - 6 + 1) = 5.
    """
    body = "\n".join(f"line {i}" for i in range(79))
    footer = "[Showing lines 6-84 of 84 (50.0KB limit). Full output: /tmp/pi-bash-x.log]"
    text = body + "\n\n" + footer
    p = _cap_session(tmp_path, "chrome.jsonl", text)
    res = audit.scan(p, threshold=20)
    assert audit.count_lines(text) == 81  # 79 delivered + blank separator + footer
    entry = res["oversized"][0]
    assert entry["lines"] == 79
    assert entry["produced_lines"] == 84
    assert entry["omitted_lines"] == 5
    assert res["total_omitted_lines"] == 5
    assert res["truncated_count"] == 1


def test_lines_cap_footer_without_kb_suffix_is_counted(tmp_path: Path) -> None:
    """P4 shape 2: "[Showing lines A-B of Z. Full output: <path>]" (no KB suffix)."""
    body = "\n".join(f"line {i}" for i in range(30))
    footer = "[Showing lines 1-30 of 5000. Full output: /tmp/pi-bash-lines.log]"
    text = body + "\n\n" + footer
    assert audit.truncation_of(text) == (5000, 4970)
    p = _cap_session(tmp_path, "lines-cap.jsonl", text)
    res = audit.scan(p, threshold=20)
    entry = res["oversized"][0]
    assert entry["lines"] == 30
    assert entry["produced_lines"] == 5000
    assert entry["omitted_lines"] == 4970
    assert res["total_produced_lines"] == 5000
    assert res["total_omitted_lines"] == 4970
    assert res["truncated_count"] == 1


def test_partial_last_line_footer_is_counted(tmp_path: Path) -> None:
    """P4 shape 3: "[Showing last <size> of line N (line is <size>). Full output: <path>]".

    The footer guarantees N total lines; the last one is delivered only in part.
    Line accounting: produced = N, the incomplete last line counts as omitted.
    """
    body = "\n".join(f"line {i}" for i in range(41))
    footer = (
        "[Showing last 50.0KB of line 42 (line is 120.0KB). Full output: /tmp/pi-bash-partial.log]"
    )
    text = body + "\n" + ("z" * 100) + "\n\n" + footer
    assert audit.truncation_of(text) == (42, 1)
    p = _cap_session(tmp_path, "partial.jsonl", text)
    res = audit.scan(p, threshold=20)
    entry = res["oversized"][0]
    assert entry["lines"] == 41
    assert entry["produced_lines"] == 42
    assert entry["omitted_lines"] == 1
    assert res["total_produced_lines"] == 42
    assert res["total_omitted_lines"] == 1
    assert res["truncated_count"] == 1


def test_read_lines_cap_footer_without_kb_suffix_is_counted() -> None:
    """P4: the read tool's lines-cap tail ("Use offset=") counts too."""
    text = "x\n[Showing lines 1-10 of 100. Use offset=11 to continue]"
    assert audit.truncation_of(text) == (100, 90)


# --- footer must be the harness tail (ha-fix-A2 / P1-2) ---
def test_truncation_of_ignores_footer_shaped_prose_mid_body() -> None:
    """P1-2: a quoted footer followed by real content is prose, not a delivery cap."""
    body = "\n".join(f"line {i}" for i in range(30))
    quoted = "[Showing lines 1-30 of 500 (50.0KB limit). Full output: /tmp/quoted.log]"
    assert audit.truncation_of(body + "\n\n" + quoted + "\n\n" + body) is None
    assert audit.truncation_of(body + "\n" + quoted + "\ntrailing") is None
    partial = "[Showing last 50.0KB of line 42 (line is 120.0KB). Full output: /tmp/p.log]"
    assert audit.truncation_of(body + "\n\n" + partial + "\n\n" + body) is None


def test_truncation_of_parses_tail_footer_and_status_tail() -> None:
    """P1-2: a genuine tail footer still parses, with or without a status line."""
    body = "\n".join(f"line {i}" for i in range(30))
    footer = "[Showing lines 1-30 of 500 (50.0KB limit). Full output: /tmp/real.log]"
    assert audit.truncation_of(body + "\n\n" + footer) == (500, 470)
    assert audit.truncation_of(body + "\n\n" + footer + "\n") == (500, 470)
    # An aborted / timed-out bash command appends one status line after the footer.
    assert audit.truncation_of(body + "\n\n" + footer + "\n\nCommand aborted") == (500, 470)
    assert audit.truncation_of(body + "\n\n" + footer + "\n\nCommand timed out after 5s") == (
        500,
        470,
    )


# --- scan / emit_filtered threshold agreement (ha-fix-A2 / P1-1) ---
def test_emit_filtered_agrees_with_scan_on_capped_threshold(tmp_path: Path) -> None:
    """P1-1: the filter must use the same footer-derived delivered count as scan."""
    p = tmp_path / "capped.jsonl"
    body = "\n".join(f"line {i}" for i in range(30))
    footer = "[Showing lines 1-30 of 500 (50.0KB limit). Use offset=31 to continue]"
    text = body + "\n\n" + footer
    write_jsonl(
        p,
        [
            session_header(),
            toolcall_msg("a1", None, "c1", "seq 1 500"),
            toolresult_msg("r1", "a1", "c1", text),
        ],
    )
    assert audit.count_lines(text) == 32  # 30 delivered + blank separator + footer
    res = audit.scan(p, threshold=30)
    assert res["oversized_count"] == 0  # delivered == 30, so not oversized
    out = audit.emit_filtered(p, threshold=30, keep=5)
    for line in out.read_text().splitlines():
        d = json.loads(line)
        if d.get("message", {}).get("toolCallId") == "c1":
            assert d["message"]["content"][0]["text"] == text  # left intact


def test_emit_filtered_still_truncates_capped_entry_over_threshold(tmp_path: Path) -> None:
    """P1-1: a capped entry whose delivered count exceeds the threshold is truncated."""
    p = tmp_path / "capped-over.jsonl"
    body = "\n".join(f"line {i}" for i in range(30))
    footer = "[Showing lines 1-30 of 500 (50.0KB limit). Use offset=31 to continue]"
    text = body + "\n\n" + footer
    write_jsonl(
        p,
        [
            session_header(),
            toolcall_msg("a1", None, "c1", "seq 1 500"),
            toolresult_msg("r1", "a1", "c1", text),
        ],
    )
    assert audit.scan(p, threshold=20)["oversized_count"] == 1
    out = audit.emit_filtered(p, threshold=20, keep=5)
    for line in out.read_text().splitlines():
        d = json.loads(line)
        if d.get("message", {}).get("toolCallId") == "c1":
            assert "omitted" in d["message"]["content"][0]["text"]


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
    # exact line + arithmetic: delivered 30 (B-A+1), produced 500, omitted 470
    assert (
        "Produced but not delivered (delivery cap): 470 lines omitted across 1 tool results, all tools"
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


# --- text report is byte-identical for a truncation-free session (ha-fix-A guard) ---
def test_text_report_byte_identical_without_truncation(tmp_path: Path) -> None:
    """A session with no delivery-cap footer renders the same bytes as before the fix."""
    p = tmp_path / "plain.jsonl"
    write_jsonl(
        p,
        [
            session_header(),
            toolcall_msg("a1", None, "c1", "seq 1 25"),
            toolresult_msg("r1", "a1", "c1", "\n".join(f"x {i}" for i in range(25)) + "\n"),
            toolcall_msg("a2", None, "c2", "echo hi"),
            toolresult_msg("r2", "a2", "c2", "hi\n"),
        ],
    )
    out = audit.format_text(audit.scan(p, threshold=20), keep=10)
    expected = (
        f"session: {p}\n"
        "records: 5  bash toolResults: 2  threshold: >20 lines\n"
        "\n"
        "Oversized bash outputs: 1 / 2\n"
        "\n"
        "  #  jsonl  lines    chars  command\n"
        "────────────────────────────────────────────────────────────────────────\n"
        "  1      3     25      115  seq 1 25\n"
        "\n"
        "Truncation preview (keep 10 head + 10 tail + marker):\n"
        "  line 3: 25 → 21 lines (−4)\n"
        "\n"
        "Next turns after each oversized (with --with-context):\n"
        "\n"
        "Total bash output: 26 lines / 118 chars\n"
        "Estimated savings if truncated (keep 10 each side): −4 lines / −18 chars  (~4 tokens @ 4 chars/token)\n"
        "\n"
        "Refine: oversized outputs above are trimtable — use --emit-filtered to write a filtered copy,\n"
        "or adjust --threshold / --keep-head-tail to taste.\n"
    )
    assert out == expected
