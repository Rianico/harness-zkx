"""Tests for skills/herdr/scripts/herdr_cli.py — the adapter the three helpers share."""

import io
import json
import sys
from collections.abc import Callable
from pathlib import Path

import herdr_cli
import herdr_prompt
import herdr_reply
import pytest


def test_error_code_reads_envelope() -> None:
    stderr = '{"error":{"code":"agent_blocked","message":"blocked"},"id":"cli:agent:prompt"}'
    assert herdr_cli.error_code(stderr) == "agent_blocked"


@pytest.mark.parametrize("stderr", ["", "not json", "[]", '{"error":null}', '{"ok":1}'])
def test_error_code_tolerates_other_shapes(stderr: str) -> None:
    assert herdr_cli.error_code(stderr) is None


def test_error_code_accepts_plain_string_error() -> None:
    assert herdr_cli.error_code('{"error":"split failed"}') == "split failed"


def test_decode_response_reports_non_json() -> None:
    with pytest.raises(herdr_cli.HerdrError, match="non-JSON"):
        _ = herdr_cli.decode_response("not json")


def test_decode_response_reports_non_object() -> None:
    with pytest.raises(herdr_cli.HerdrError, match="non-object"):
        _ = herdr_cli.decode_response("[1, 2]")


def test_payload_field_reads_nested_values() -> None:
    raw = json.dumps({"result": {"pane": {"pane_id": "w9:p1"}}})
    assert herdr_cli.payload_field(raw, "result", "pane", "pane_id") == "w9:p1"


def test_payload_field_reports_the_missing_path() -> None:
    with pytest.raises(herdr_cli.HerdrError, match=r"result\.pane\.pane_id"):
        _ = herdr_cli.payload_field(json.dumps({"result": {}}), "result", "pane", "pane_id")


def test_text_field_rejects_an_empty_string() -> None:
    raw = json.dumps({"result": {"pane": {"pane_id": ""}}})
    with pytest.raises(herdr_cli.HerdrError, match="non-empty string"):
        _ = herdr_cli.text_field(raw, "result", "pane", "pane_id")


@pytest.mark.parametrize(
    ("value", "expected"),
    [("x", "x"), ("", None), (None, None), (7, None)],
)
def test_entry_optional_text_tolerates_absence(value: object, expected: str | None) -> None:
    assert herdr_cli.entry_optional_text({"label": value}, "label") == expected


def test_entry_optional_text_missing_key_is_none() -> None:
    assert herdr_cli.entry_optional_text({}, "label") is None


def test_entry_text_requires_a_non_empty_string() -> None:
    assert herdr_cli.entry_text({"pane_id": "w9:p1"}, "pane_id", where="pane") == "w9:p1"
    with pytest.raises(herdr_cli.HerdrError, match="has no usable 'pane_id'"):
        _ = herdr_cli.entry_text({"pane_id": ""}, "pane_id", where="pane")


def test_entries_reads_a_list_of_objects() -> None:
    raw = json.dumps({"result": {"panes": [{"pane_id": "w9:p1"}, {"pane_id": "w9:p2"}]}})
    found = herdr_cli.entries(raw, "result", "panes")
    assert [entry["pane_id"] for entry in found] == ["w9:p1", "w9:p2"]


def test_entries_rejects_a_non_list() -> None:
    with pytest.raises(herdr_cli.HerdrError, match="is not a list"):
        _ = herdr_cli.entries(json.dumps({"result": {"panes": {}}}), "result", "panes")


def test_entries_rejects_a_non_object_entry() -> None:
    with pytest.raises(herdr_cli.HerdrError, match="non-object entry"):
        _ = herdr_cli.entries(json.dumps({"result": {"panes": [1]}}), "result", "panes")


def test_guard_maps_usage_errors_to_exit_usage(capsys: pytest.CaptureFixture[str]) -> None:
    def boom() -> int:
        raise herdr_cli.UsageError("bad flag")

    assert herdr_cli.guard("herdr-x", boom) == herdr_cli.EXIT_USAGE
    assert "herdr-x: bad flag" in capsys.readouterr().err


def test_guard_maps_herdr_errors_to_exit_herdr(capsys: pytest.CaptureFixture[str]) -> None:
    def boom() -> int:
        raise herdr_cli.HerdrError("herdr said no")

    assert herdr_cli.guard("herdr-x", boom) == herdr_cli.EXIT_HERDR
    assert "herdr-x: herdr said no" in capsys.readouterr().err


def test_guard_passes_through_a_successful_action() -> None:
    assert herdr_cli.guard("herdr-x", lambda: int(herdr_cli.EXIT_OK)) == herdr_cli.EXIT_OK


# ── unit: scoped agent naming ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("role", "task_group", "expected"),
    [
        ("tm", "msg", "msg-tm"),
        ("msg-tm", "msg", "msg-tm"),
        ("tm", None, "tm"),
        ("tm", "", "tm"),
        ("msg", "msg", "msg"),
    ],
)
def test_scoped_agent_name_prefixes_and_passes_through(
    role: str, task_group: str | None, expected: str
) -> None:
    assert herdr_cli.scoped_agent_name(role, task_group) == expected


def test_scoped_agent_name_is_idempotent() -> None:
    once = herdr_cli.scoped_agent_name("tm", "msg")
    assert herdr_cli.scoped_agent_name(once, "msg") == once == "msg-tm"


def test_validate_agent_name_accepts_a_scoped_name() -> None:
    herdr_cli.validate_agent_name("msg-impl-1")


@pytest.mark.parametrize("name", ["Message", "msg impl", "a" * 33])
def test_validate_agent_name_rejects_violations(name: str) -> None:
    with pytest.raises(herdr_cli.UsageError, match="not a valid agent name"):
        herdr_cli.validate_agent_name(name)


# ── pin: the shared payload reader, exercised through BOTH entry points ────────────
#
# `herdr_cli.read_payload_stream` and `herdr_cli.decode_payload` are the shared
# acquisition-and-validation seam. `herdr_prompt.read_payload` and
# `herdr_reply.read_payload` keep their own fallback (MESSAGE, the both-given refusal) and
# their own wording. This pin calls both entry points with the same input and asserts they
# agree, so a future edit that re-forks one caller's path (drops the NUL check, drops the
# UTF-8 decode, or swaps in the other caller's wording) fails here.

PayloadReader = Callable[[str | None, str | None], str]


def _read_prompt(source: str | None, message: str | None) -> str:
    """Adapt herdr-prompt's one-argument reader to the two-argument shape the pin uses."""
    assert message is None, "herdr-prompt has no MESSAGE positional"
    return herdr_prompt.read_payload(source)


def _read_reply(source: str | None, message: str | None) -> str:
    return herdr_reply.read_payload(source, message)


PAYLOAD_READERS: list[object] = [
    pytest.param(_read_prompt, id="prompt"),
    pytest.param(_read_reply, id="reply"),
]


class _Tty:
    """A stand-in for an interactive stdin: `isatty()` is all `read_payload` asks of it."""

    def isatty(self) -> bool:
        return True


@pytest.mark.parametrize("read", PAYLOAD_READERS)
def test_payload_reader_rejects_a_nul_byte(read: PayloadReader, tmp_path: Path) -> None:
    path = tmp_path / "nul.bin"
    _ = path.write_bytes(b"a\x00b")
    with pytest.raises(herdr_cli.UsageError, match="NUL byte"):
        _ = read(str(path), None)


@pytest.mark.parametrize("read", PAYLOAD_READERS)
def test_payload_reader_rejects_invalid_utf8(read: PayloadReader, tmp_path: Path) -> None:
    path = tmp_path / "binary.bin"
    _ = path.write_bytes(b"\xff\xfebad")
    with pytest.raises(herdr_cli.UsageError, match="not valid UTF-8"):
        _ = read(str(path), None)


@pytest.mark.parametrize("read", PAYLOAD_READERS)
def test_payload_reader_names_the_nul_refusal_first(read: PayloadReader, tmp_path: Path) -> None:
    """Both entry points report the SAME blocker for a NUL-bearing, invalid-UTF-8 payload.

    Pins the NUL-before-decode order: the argv-safety refusal wins over the codec complaint.
    """
    path = tmp_path / "both.bin"
    _ = path.write_bytes(b"\x00\xff")
    with pytest.raises(herdr_cli.UsageError, match="NUL byte"):
        _ = read(str(path), None)


@pytest.mark.parametrize("read", PAYLOAD_READERS)
def test_payload_reader_reports_a_missing_file(read: PayloadReader, tmp_path: Path) -> None:
    with pytest.raises(herdr_cli.UsageError, match="cannot read payload"):
        _ = read(str(tmp_path / "nope.md"), None)


@pytest.mark.parametrize("read", PAYLOAD_READERS)
def test_payload_reader_returns_the_same_valid_payload(read: PayloadReader, tmp_path: Path) -> None:
    path = tmp_path / "ok.md"
    _ = path.write_text("shared payload \u00e9\n", encoding="utf-8")
    assert read(str(path), None) == "shared payload \u00e9\n"


@pytest.mark.parametrize("read", PAYLOAD_READERS)
def test_payload_reader_reads_stdin_and_dash(
    read: PayloadReader, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO("piped \u00e9\n".encode())))
    assert read(None, None) == "piped \u00e9\n"
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b"dashed\n")))
    assert read("-", None) == "dashed\n"


def test_payload_readers_agree_on_one_valid_payload(tmp_path: Path) -> None:
    path = tmp_path / "ok.md"
    _ = path.write_text("agreed \u00e9\n", encoding="utf-8")
    assert _read_prompt(str(path), None) == _read_reply(str(path), None)


# ── pin: the reply-only fallbacks stay local to herdr-reply ────────────────────────


def test_reply_message_and_file_together_are_refused(tmp_path: Path) -> None:
    with pytest.raises(herdr_cli.UsageError, match="not both"):
        _ = herdr_reply.read_payload(str(tmp_path / "x"), "msg")


def test_reply_message_alone_is_the_payload() -> None:
    assert herdr_reply.read_payload(None, "msg") == "msg"


def test_reply_stdin_refusal_names_message_not_only_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The reply's wording must keep naming MESSAGE, never the prompt's `--file` sentence."""
    monkeypatch.setattr(sys, "stdin", _Tty())
    with pytest.raises(herdr_cli.UsageError, match="MESSAGE"):
        _ = herdr_reply.read_payload(None, None)


def test_prompt_stdin_refusal_names_only_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdin", _Tty())
    with pytest.raises(herdr_cli.UsageError, match="no --file given"):
        _ = herdr_prompt.read_payload(None)


def test_prompt_empty_refusal_names_the_prompt(tmp_path: Path) -> None:
    path = tmp_path / "blank.md"
    _ = path.write_text("   \n", encoding="utf-8")
    with pytest.raises(herdr_cli.UsageError, match="empty prompt"):
        _ = herdr_prompt.read_payload(str(path))


def test_reply_empty_refusal_names_the_reply(tmp_path: Path) -> None:
    path = tmp_path / "blank.md"
    _ = path.write_text("   \n", encoding="utf-8")
    with pytest.raises(herdr_cli.UsageError, match="empty reply"):
        _ = herdr_reply.read_payload(str(path), None)
