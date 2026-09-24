"""Tests for skills/herdr/scripts/herdr_pane.py (herdr-pane helper).

All integration cases route through a stub `herdr` on PATH, so no live Herdr session is
touched: the stub records the argv it received and replays canned JSON.
"""

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import herdr_cli
import herdr_pane
import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness, flag_value

SCRIPT = SCRIPTS_DIR / "herdr_pane.py"


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPT)


# ── unit: pure helpers ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("vertical", "down"),
        ("Vertical", "down"),
        ("vert", "down"),
        ("v", "down"),
        ("down", "down"),
        ("below", "down"),
        ("under", "down"),
        ("stacked", "down"),
        ("horizontal", "right"),
        ("horiz", "right"),
        ("h", "right"),
        ("right", "right"),
        ("beside", "right"),
        ("  alongside  ", "right"),
    ],
)
def test_normalize_direction_maps_aliases(token: str, expected: str) -> None:
    assert herdr_pane.normalize_direction(token) == expected


def test_normalize_direction_rejects_unknown() -> None:
    with pytest.raises(herdr_pane.UsageError, match="unknown direction"):
        herdr_pane.normalize_direction("diagonal")


def test_payload_field_reports_non_json() -> None:
    with pytest.raises(herdr_pane.HerdrError, match="non-JSON"):
        herdr_pane.payload_field("not json", "result")


def test_payload_field_reports_missing_key() -> None:
    with pytest.raises(herdr_pane.HerdrError, match="missing result.pane"):
        herdr_pane.payload_field('{"result": {}}', "result", "pane")


def test_build_split_argv_rejects_bad_ratio() -> None:
    with pytest.raises(herdr_pane.UsageError, match="out of range"):
        herdr_pane.build_split_argv(
            "herdr", "w9:p1", "down", cwd="/tmp", ratio=1.5, extra_env=(), focus=False
        )


# ── integration: guard and preconditions ────────────────────────────────────────────


def test_refuses_without_herdr_env(stub: StubHarness) -> None:
    done = stub.run("vertical", env={"HERDR_ENV": None})
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "HERDR_ENV" in done.stderr
    assert stub.calls() == []


def test_refuses_when_herdr_missing_from_path(stub: StubHarness) -> None:
    done = stub.run("vertical", env={"PATH": "/nonexistent", "HERDR_BIN_PATH": None})
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not found on PATH" in done.stderr


def test_unknown_direction_is_usage_error(stub: StubHarness) -> None:
    done = stub.run("diagonal")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "unknown direction" in done.stderr
    assert stub.splits() == []


# ── integration: direction mapping ──────────────────────────────────────────────────


def test_vertical_stacks_down(stub: StubHarness) -> None:
    done = stub.run("vertical")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.splits()
    assert call[0] == str(stub.herdr)
    assert flag_value(call, "--direction") == "down"
    assert flag_value(call, "--pane") == "w9:p1"
    assert "--no-focus" in call
    assert "focus=caller" in done.stdout


def test_horizontal_places_right(stub: StubHarness) -> None:
    done = stub.run("horizontal")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.splits()
    assert flag_value(call, "--direction") == "right"


@pytest.mark.parametrize(("word", "expected"), [("v", "down"), ("under", "down"), ("h", "right")])
def test_short_aliases_reach_herdr(stub: StubHarness, word: str, expected: str) -> None:
    done = stub.run(word)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert flag_value(stub.splits()[0], "--direction") == expected


# ── integration: auto direction ─────────────────────────────────────────────────────


def test_auto_prefers_right_for_wide_pane(stub: StubHarness) -> None:
    done = stub.run(state={"current": "w9:p1", "rect": {"width": 170, "height": 45}})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert flag_value(stub.splits()[0], "--direction") == "right"


def test_auto_prefers_down_for_tall_pane(stub: StubHarness) -> None:
    done = stub.run(state={"current": "w9:p1", "rect": {"width": 40, "height": 45}})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert flag_value(stub.splits()[0], "--direction") == "down"


def test_auto_requires_caller_resolution(stub: StubHarness) -> None:
    _ = stub.run()
    assert [call[1:3] for call in stub.calls()][:2] == [["pane", "current"], ["pane", "layout"]]


# ── integration: options ────────────────────────────────────────────────────────────


def test_focus_flag_targets_new_pane(stub: StubHarness) -> None:
    done = stub.run("vertical", "--focus")
    (call,) = stub.splits()
    assert "--focus" in call
    assert "--no-focus" not in call
    assert "focus=new pane" in done.stdout


def test_explicit_pane_skips_caller_lookup(stub: StubHarness) -> None:
    done = stub.run("vertical", "--pane", "w9:p7")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert flag_value(stub.splits()[0], "--pane") == "w9:p7"
    assert all(call[1:3] != ["pane", "current"] for call in stub.calls())
    assert "caller=w9:p7" in done.stdout


def test_cwd_ratio_and_env_are_forwarded(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "horizontal",
        "--cwd",
        str(tmp_path),
        "--ratio",
        "0.3",
        "--env",
        "FOO=bar",
        "--env",
        "BAZ=1",
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    call = stub.splits()[0]
    assert flag_value(call, "--cwd") == str(tmp_path)
    assert flag_value(call, "--ratio") == "0.3"
    assert call.count("--env") == 2
    assert "FOO=bar" in call and "BAZ=1" in call


def test_default_cwd_comes_from_pwd_env(stub: StubHarness) -> None:
    _ = stub.run("vertical")
    assert flag_value(stub.splits()[0], "--cwd") == str(stub.tmp_path)


def test_missing_cwd_is_rejected(stub: StubHarness) -> None:
    done = stub.run("vertical", "--cwd", str(stub.tmp_path / "nope"))
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not an existing directory" in done.stderr
    assert stub.splits() == []


def test_malformed_env_pair_is_rejected(stub: StubHarness) -> None:
    done = stub.run("vertical", "--env", "FOO")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "malformed" in done.stderr
    assert stub.splits() == []


def test_json_prints_raw_response(stub: StubHarness) -> None:
    done = stub.run("vertical", "--json")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert json.loads(done.stdout)["result"]["pane"]["pane_id"] == "w9:pNEW"


def test_dry_run_prints_command_without_splitting(stub: StubHarness) -> None:
    done = stub.run("horizontal", "--dry-run")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.splits() == []
    assert str(stub.herdr) in done.stdout
    assert "pane split" in done.stdout
    assert "--direction right" in done.stdout


# ── integration: failure paths ──────────────────────────────────────────────────────


def test_herdr_split_failure_is_reported(stub: StubHarness) -> None:
    done = stub.run("vertical", state={**DEFAULT_STATE, "split_error": "no space"})
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "no space" in done.stderr
    assert "Traceback" not in done.stderr


def test_unusable_split_response_is_reported(stub: StubHarness) -> None:
    done = stub.run("vertical", state={**DEFAULT_STATE, "split_pane": {"tab_id": "w9:t1"}})
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "result.pane.pane_id" in done.stderr


# ── metadata: PEP 723 conformance ────────────────────────────────────────────────────


def test_pep723_metadata_precedes_docstring() -> None:
    header = SCRIPT.read_text().split('"""', 1)[0]
    assert header.startswith("#!/usr/bin/env python3\n")
    assert "# /// script" in header
    assert 'requires-python = ">=3.14"' in header
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
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "usage: herdr-pane" in done.stdout
