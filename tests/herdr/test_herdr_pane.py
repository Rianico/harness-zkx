"""Tests for skills/herdr/scripts/herdr_pane.py (herdr-pane helper).

All integration cases route through a stub `herdr` on PATH, so no live Herdr session is
touched: the stub records the argv it received and replays canned JSON.
"""

import json
import os
import stat
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest

SCRIPTS_DIR = (Path(__file__).parent.parent.parent / "skills" / "herdr" / "scripts").resolve()
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import herdr_pane  # noqa: E402

SCRIPT = SCRIPTS_DIR / "herdr_pane.py"

STUB_SOURCE = '''#!/usr/bin/env python3
"""Fake herdr for tests: append argv to STUB_HERDR_LOG, replay STUB_HERDR_STATE."""

import json
import os
import sys
from pathlib import Path

argv = sys.argv
with Path(os.environ["STUB_HERDR_LOG"]).open("a") as log:
    log.write(json.dumps(argv) + "\\n")
args = argv[1:]

state = json.loads(Path(os.environ["STUB_HERDR_STATE"]).read_text())

if args[:2] == ["pane", "current"]:
    print(json.dumps({"result": {"pane": {"pane_id": state["current"]}}}))
    raise SystemExit(0)

if args[:2] == ["pane", "layout"]:
    pane_id = args[args.index("--pane") + 1]
    print(json.dumps({"result": {"layout": {"panes": [{"pane_id": pane_id, "rect": state["rect"]}]}}}))
    raise SystemExit(0)

if args[:2] == ["pane", "split"]:
    if state.get("split_error"):
        print(json.dumps({"error": state["split_error"]}), file=sys.stderr)
        raise SystemExit(1)
    pane = state.get("split_pane", {"pane_id": "w9:pNEW", "tab_id": "w9:t1", "cwd": "/tmp"})
    print(json.dumps({"result": {"pane": pane}}))
    raise SystemExit(0)

print(json.dumps({"error": "unexpected argv: " + " ".join(args)}), file=sys.stderr)
raise SystemExit(1)
'''

DEFAULT_STATE = {"current": "w9:p1", "rect": {"width": 100, "height": 40}}


@dataclass(frozen=True)
class StubHarness:
    """A temp PATH containing a fake `herdr`, plus the run/log helpers around it."""

    tmp_path: Path
    bin_dir: Path
    log_path: Path
    state_path: Path

    @property
    def herdr(self) -> Path:
        return self.bin_dir / "herdr"

    def calls(self) -> list[list[str]]:
        if not self.log_path.exists():
            return []
        return [json.loads(line) for line in self.log_path.read_text().splitlines() if line]

    def splits(self) -> list[list[str]]:
        return [call for call in self.calls() if call[1:3] == ["pane", "split"]]

    def run(
        self,
        *args: str,
        state: Mapping[str, object] | None = None,
        env: Mapping[str, str | None] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        _ = self.state_path.write_text(
            json.dumps(dict(state if state is not None else DEFAULT_STATE))
        )
        full_env: dict[str, str] = {
            "PATH": f"{self.bin_dir}:{os.environ.get('PATH', '')}",
            "HERDR_ENV": "1",
            "PWD": str(self.tmp_path),
            "STUB_HERDR_LOG": str(self.log_path),
            "STUB_HERDR_STATE": str(self.state_path),
        }
        for key, value in (env or {}).items():
            if value is None:
                _ = full_env.pop(key, None)
            else:
                full_env[key] = value
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            env=full_env,
            check=False,
        )


@pytest.fixture
def stub(tmp_path: Path) -> StubHarness:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    herdr = bin_dir / "herdr"
    _ = herdr.write_text(STUB_SOURCE)
    herdr.chmod(herdr.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    harness = StubHarness(tmp_path, bin_dir, tmp_path / "calls.jsonl", tmp_path / "state.json")
    _ = harness.state_path.write_text(json.dumps(DEFAULT_STATE))
    return harness


def flag_value(call: Sequence[str], flag: str) -> str:
    return call[list(call).index(flag) + 1]


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
    assert done.returncode == herdr_pane.EXIT_USAGE
    assert "HERDR_ENV" in done.stderr
    assert stub.calls() == []


def test_refuses_when_herdr_missing_from_path(stub: StubHarness) -> None:
    done = stub.run("vertical", env={"PATH": "/nonexistent", "HERDR_BIN_PATH": None})
    assert done.returncode == herdr_pane.EXIT_USAGE
    assert "not found on PATH" in done.stderr


def test_unknown_direction_is_usage_error(stub: StubHarness) -> None:
    done = stub.run("diagonal")
    assert done.returncode == herdr_pane.EXIT_USAGE
    assert "unknown direction" in done.stderr
    assert stub.splits() == []


# ── integration: direction mapping ──────────────────────────────────────────────────


def test_vertical_stacks_down(stub: StubHarness) -> None:
    done = stub.run("vertical")
    assert done.returncode == herdr_pane.EXIT_OK, done.stderr
    (call,) = stub.splits()
    assert call[0] == str(stub.herdr)
    assert flag_value(call, "--direction") == "down"
    assert flag_value(call, "--pane") == "w9:p1"
    assert "--no-focus" in call
    assert "focus=caller" in done.stdout


def test_horizontal_places_right(stub: StubHarness) -> None:
    done = stub.run("horizontal")
    assert done.returncode == herdr_pane.EXIT_OK, done.stderr
    (call,) = stub.splits()
    assert flag_value(call, "--direction") == "right"


@pytest.mark.parametrize(("word", "expected"), [("v", "down"), ("under", "down"), ("h", "right")])
def test_short_aliases_reach_herdr(stub: StubHarness, word: str, expected: str) -> None:
    done = stub.run(word)
    assert done.returncode == herdr_pane.EXIT_OK, done.stderr
    assert flag_value(stub.splits()[0], "--direction") == expected


# ── integration: auto direction ─────────────────────────────────────────────────────


def test_auto_prefers_right_for_wide_pane(stub: StubHarness) -> None:
    done = stub.run(state={"current": "w9:p1", "rect": {"width": 170, "height": 45}})
    assert done.returncode == herdr_pane.EXIT_OK, done.stderr
    assert flag_value(stub.splits()[0], "--direction") == "right"


def test_auto_prefers_down_for_tall_pane(stub: StubHarness) -> None:
    done = stub.run(state={"current": "w9:p1", "rect": {"width": 40, "height": 45}})
    assert done.returncode == herdr_pane.EXIT_OK, done.stderr
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
    assert done.returncode == herdr_pane.EXIT_OK, done.stderr
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
    assert done.returncode == herdr_pane.EXIT_OK, done.stderr
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
    assert done.returncode == herdr_pane.EXIT_USAGE
    assert "not an existing directory" in done.stderr
    assert stub.splits() == []


def test_malformed_env_pair_is_rejected(stub: StubHarness) -> None:
    done = stub.run("vertical", "--env", "FOO")
    assert done.returncode == herdr_pane.EXIT_USAGE
    assert "malformed" in done.stderr
    assert stub.splits() == []


def test_json_prints_raw_response(stub: StubHarness) -> None:
    done = stub.run("vertical", "--json")
    assert done.returncode == herdr_pane.EXIT_OK, done.stderr
    assert json.loads(done.stdout)["result"]["pane"]["pane_id"] == "w9:pNEW"


def test_dry_run_prints_command_without_splitting(stub: StubHarness) -> None:
    done = stub.run("horizontal", "--dry-run")
    assert done.returncode == herdr_pane.EXIT_OK, done.stderr
    assert stub.splits() == []
    assert str(stub.herdr) in done.stdout
    assert "pane split" in done.stdout
    assert "--direction right" in done.stdout


# ── integration: failure paths ──────────────────────────────────────────────────────


def test_herdr_split_failure_is_reported(stub: StubHarness) -> None:
    done = stub.run("vertical", state={**DEFAULT_STATE, "split_error": "no space"})
    assert done.returncode == herdr_pane.EXIT_HERDR
    assert "no space" in done.stderr
    assert "Traceback" not in done.stderr


def test_unusable_split_response_is_reported(stub: StubHarness) -> None:
    done = stub.run("vertical", state={**DEFAULT_STATE, "split_pane": {"tab_id": "w9:t1"}})
    assert done.returncode == herdr_pane.EXIT_HERDR
    assert "result.pane.pane_id" in done.stderr
