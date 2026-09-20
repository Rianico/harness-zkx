"""Tests for skills/herdr/scripts/herdr_cli.py — the adapter the three helpers share."""

import json

import herdr_cli
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
def test_optional_text_field_tolerates_absence(value: object, expected: str | None) -> None:
    raw = json.dumps({"result": {"pane": {"label": value}}})
    assert herdr_cli.optional_text_field(raw, "result", "pane", "label") == expected


def test_optional_text_field_missing_path_is_none() -> None:
    assert herdr_cli.optional_text_field(json.dumps({"result": {}}), "result", "pane", "x") is None


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
    assert herdr_cli.guard("herdr-x", lambda: herdr_cli.EXIT_OK) == herdr_cli.EXIT_OK
