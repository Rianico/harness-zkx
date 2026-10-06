"""Tests for skills/herdr/scripts/herdr_wait.py (multi-agent wait barrier).

Barrier, --any, blocked, and timeout paths run through the shared stub `herdr`;
`agent get` answers come from scripted per-target state (`agent_get` for static
status, `agent_get_seq` for a status per poll, indexed by prior poll count).
"""

import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import herdr_cli
import herdr_wait
import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness

SCRIPT = SCRIPTS_DIR / "herdr_wait.py"


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPT)


def settled_state(**overrides: object) -> dict[str, object]:
    """Static `agent get` answers for the named targets."""
    return {**DEFAULT_STATE, "agent_get": dict(overrides)}


# ── unit: match-set resolution ────────────────────────────────────────────────


def test_resolve_until_defaults_to_settled() -> None:
    assert herdr_wait.resolve_until([]) == ["idle", "done", "blocked"]


def test_resolve_until_idle_auto_expands_with_warning(capsys: pytest.CaptureFixture[str]) -> None:
    assert herdr_wait.resolve_until(["idle"]) == ["idle", "done"]
    assert "they settle to done" in capsys.readouterr().err


def test_resolve_until_idle_plus_done_is_stable(capsys: pytest.CaptureFixture[str]) -> None:
    assert herdr_wait.resolve_until(["idle", "done"]) == ["idle", "done"]
    assert capsys.readouterr().err == ""


def test_resolve_until_rejects_unknown_state() -> None:
    with pytest.raises(herdr_wait.UsageError, match="not a known agent state"):
        _ = herdr_wait.resolve_until(["frobnicate"])


def test_format_table_aligns_columns() -> None:
    table = herdr_wait.format_table(
        [
            herdr_wait.Snapshot("a", "done", revision="r12", session="/s/a.jsonl", elapsed_ms=7),
            herdr_wait.Snapshot("b", "working", elapsed_ms=70),
        ]
    )
    header, *rows = table.splitlines()
    assert header.startswith("TARGET")
    assert "SESSION_PATH" in header
    assert rows[0].split() == ["a", "done", "r12", "7ms", "/s/a.jsonl"]
    assert rows[1].split() == ["b", "working", "-", "70ms", "-"]


# ── integration: guards and preconditions ─────────────────────────────────────


def test_refuses_without_herdr_env(stub: StubHarness) -> None:
    done = stub.run("a", env={"HERDR_ENV": None})
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "HERDR_ENV" in done.stderr


def test_missing_targets_are_rejected(stub: StubHarness) -> None:
    done = stub.run()
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "at least one TARGET" in done.stderr


def test_duplicate_targets_are_rejected(stub: StubHarness) -> None:
    done = stub.run("a", "a", "--interval", "0.01")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "duplicate" in done.stderr


def test_hold_interval_must_be_positive(stub: StubHarness) -> None:
    done = stub.run("a", "--hold-interval", "0")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "--hold-interval 0.0 is not positive" in done.stderr


def test_agent_get_failure_is_herdr_error(stub: StubHarness) -> None:
    error = {"code": "agent_not_found", "message": "agent target nope not found"}
    done = stub.run("nope", "--interval", "0.01", state={**DEFAULT_STATE, "agent_get_error": error})
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "not found" in done.stderr


# ── integration: barrier and reactive modes ───────────────────────────────────


def test_barrier_waits_for_all_targets(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "agent_get_seq": {"a": ["working", "done"], "b": ["working", "working", "idle"]},
    }
    done = stub.run("a", "b", "--interval", "0.01", "--timeout", "5000", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "TARGET" in done.stdout and "SESSION_PATH" in done.stdout
    gets = [call for call in stub.calls() if call[1:4] == ["agent", "get", "a"]]
    assert len(gets) >= 2  # polled, not a single event-driven wait


def test_barrier_accepts_background_done_without_until(stub: StubHarness) -> None:
    state = settled_state(a={"agent_status": "done"})
    done = stub.run("a", "--interval", "0.01", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "done" in done.stdout


def test_revision_zero_settled_state_fails_fast(stub: StubHarness) -> None:
    """False-positive done with revision 0 (agy, unrecognized) fails fast, never hangs."""
    state = settled_state(a={"agent_status": "done", "revision": "0"})
    done = stub.run("a", "--interval", "0.01", "--timeout", "200000", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "a reports done with revision 0 (unrecognized; typical of agy)" in done.stderr
    assert "REQUIRED" in done.stderr
    assert "unsatisfiable wait" in done.stderr
    assert "timed out" not in done.stderr


def test_int_revision_zero_fails_fast(stub: StubHarness) -> None:
    """Numeric revision 0 normalizes to "0" and fails fast as well."""
    state = settled_state(a={"agent_status": "idle", "revision": 0})
    done = stub.run("a", "--interval", "0.01", "--timeout", "200000", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "a reports idle with revision 0 (unrecognized; typical of agy)" in done.stderr
    assert "REQUIRED" in done.stderr
    assert "unsatisfiable wait" in done.stderr


def test_revision_zero_fast_failure_steers_to_dispatch_and_yield(stub: StubHarness) -> None:
    """Fail-fast stderr names the event-driven herdr-reply pattern, not just the hold."""
    state = settled_state(a={"agent_status": "idle", "revision": "0"})
    done = stub.run("a", "--interval", "0.01", "--timeout", "200000", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "a reports idle with revision 0 (unrecognized; typical of agy)" in done.stderr
    assert "REQUIRED" in done.stderr
    assert (
        "agents with background subagents (e.g. agy) report idle while subagents work"
        in done.stderr
    )
    assert "weakly-recognized agents do not advance revision" in done.stderr
    assert "dispatch and yield turn for herdr-reply callback instead" in done.stderr
    assert "Dispatch & Yield" in done.stderr
    assert "herdr-reply" in done.stderr


def test_barrier_fails_fast_when_any_target_is_revision_zero(stub: StubHarness) -> None:
    """A held target can never settle the ALL barrier, so the barrier exits 2 at once."""
    state = settled_state(a={"agent_status": "idle", "revision": "0"}, b={"agent_status": "done"})
    done = stub.run("a", "b", "--interval", "0.01", "--timeout", "200000", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "unsatisfiable wait: a " in done.stderr
    assert "timed out" not in done.stderr


def test_any_mode_settles_despite_held_revision_zero_target(stub: StubHarness) -> None:
    """--any still succeeds on a recognized match while another target is revision 0."""
    state = settled_state(
        a={"agent_status": "done", "revision": "0"}, b={"agent_status": "done", "revision": "r3"}
    )
    done = stub.run("a", "b", "--any", "--interval", "0.01", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr


def test_any_mode_fails_fast_when_all_targets_revision_zero(stub: StubHarness) -> None:
    """--any with every target revision 0 is equally unsatisfiable: exit 2, never hang."""
    state = settled_state(
        a={"agent_status": "idle", "revision": "0"}, b={"agent_status": "done", "revision": "0"}
    )
    done = stub.run("a", "b", "--any", "--interval", "0.01", "--timeout", "200000", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "unsatisfiable wait" in done.stderr
    assert "herdr-reply" in done.stderr
    assert "timed out" not in done.stderr


class _FakeTime:
    """Monotonic clock and sleeper advanced only by explicit sleeps."""

    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def test_periodic_hold_heartbeat_emitted(
    stub: StubHarness, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """--any mode with one live target keeps pulsing heartbeats for the held target.

    The heartbeat is wall-clock-driven: in a subprocess run, slow `herdr` stub
    spawns can burn the whole watchdog budget before the second held poll, so
    the pulse never emits (flaky). Drive the loop with an injected fake
    monotonic clock instead: time advances only when the loop sleeps, on exact
    quarter-second steps, so the hold branch pulses deterministically.
    """
    stub.write_state(
        settled_state(a={"agent_status": "done", "revision": "0"}, b={"agent_status": "working"})
    )
    _ = monkeypatch.setattr(herdr_wait, "time", _FakeTime())
    options = herdr_wait.Options(
        targets=["a", "b"], any=True, timeout=1000, interval=0.25, hold_interval=0.5
    )
    rc = herdr_wait.wait_agents(options, stub.base_env())
    err = capsys.readouterr().err
    assert rc == herdr_cli.EXIT_HERDR, err
    assert "holding a (done, revision 0)" in err
    assert "(still waiting)" in err


def test_timeout_annotates_targets_held_on_revision_zero(stub: StubHarness) -> None:
    """Timeout in --any mode annotates targets held on revision 0; ordinary targets stay bare."""
    state = settled_state(
        a={"agent_status": "idle", "revision": "0"}, b={"agent_status": "working"}
    )
    done = stub.run("a", "b", "--any", "--interval", "0.01", "--timeout", "200", state=state)
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "timed out after 200ms" in done.stderr
    assert (
        "a (idle) [revision 0 held; weakly-recognized agent does not settle barrier; use dispatch & yield]"
        in done.stderr
    )
    assert "b (working)" in done.stderr
    assert "b (working) [" not in done.stderr


def test_is_recognized_gate() -> None:
    assert herdr_wait.is_recognized(herdr_wait.Snapshot("a", "done", revision="r1"))
    assert herdr_wait.is_recognized(herdr_wait.Snapshot("a", "done", revision=None))
    assert not herdr_wait.is_recognized(herdr_wait.Snapshot("a", "done", revision="0"))
    assert not herdr_wait.is_recognized(herdr_wait.Snapshot("a", "idle", revision="0"))


def test_has_active_subagents() -> None:
    assert herdr_wait.has_active_subagents(
        herdr_wait.Snapshot("a", "idle", tokens={"summary": "⏳ 1 subagent (developer)"})
    )
    assert herdr_wait.has_active_subagents(
        herdr_wait.Snapshot("a", "idle", tokens={"title-suffix": "⏳developer"})
    )
    assert herdr_wait.has_active_subagents(
        herdr_wait.Snapshot("a", "idle", tokens={"summary": "2 subagents running"})
    )
    assert not herdr_wait.has_active_subagents(herdr_wait.Snapshot("a", "idle", tokens=None))
    assert not herdr_wait.has_active_subagents(herdr_wait.Snapshot("a", "idle", tokens={}))
    assert not herdr_wait.has_active_subagents(
        herdr_wait.Snapshot("a", "idle", tokens={"summary": "ready"})
    )


def test_is_settled_rejects_active_subagents() -> None:
    snap_busy = herdr_wait.Snapshot("a", "idle", revision="r1", tokens={"summary": "⏳ 1 subagent"})
    snap_free = herdr_wait.Snapshot("a", "idle", revision="r1", tokens=None)
    wanted = ["idle", "done"]

    assert not herdr_wait.is_settled(snap_busy, wanted)
    assert herdr_wait.is_settled(snap_free, wanted)


def test_wait_treats_subagents_as_unsettled_until_cleared(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "agent_get": {"a": {"agent_status": "idle", "revision": "r1"}},
        "agent_get_tokens_seq": {"a": [{"summary": "⏳ 1 subagent"}, None]},
    }
    done = stub.run("a", "--interval", "0.01", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "idle" in done.stdout


def test_wait_times_out_if_subagents_never_clear(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "agent_get": {
            "a": {
                "agent_status": "idle",
                "revision": "r1",
                "tokens": {"summary": "⏳ 1 subagent (developer)"},
            }
        },
    }
    done = stub.run("a", "--interval", "0.01", "--timeout", "100", state=state)
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "timed out after 100ms" in done.stderr
    assert "a (idle)" in done.stderr


def test_any_exits_on_first_settled_target(stub: StubHarness) -> None:
    state = settled_state(a={"agent_status": "working"}, b={"agent_status": "done"})
    done = stub.run("a", "b", "--any", "--interval", "0.01", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "done" in done.stdout


def test_until_idle_alone_still_matches_done(stub: StubHarness) -> None:
    state = settled_state(a={"agent_status": "done"})
    done = stub.run("a", "--until", "idle", "--interval", "0.01", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "matching idle or done" in done.stderr


def test_blocked_exits_blocked_immediately(stub: StubHarness) -> None:
    state = settled_state(a={"agent_status": "working"}, b={"agent_status": "blocked"})
    done = stub.run("a", "b", "--interval", "0.01", "--timeout", "5000", state=state)
    assert done.returncode == herdr_cli.EXIT_BLOCKED
    assert "b need human input" in done.stderr


def test_timeout_names_the_unsettled_targets(stub: StubHarness) -> None:
    state = settled_state(a={"agent_status": "working"}, b={"agent_status": "working"})
    done = stub.run("a", "b", "--interval", "0.01", "--timeout", "200", state=state)
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "timed out after 200ms" in done.stderr
    assert "a (working)" in done.stderr
    assert "b (working)" in done.stderr


def test_json_prints_machine_summary(stub: StubHarness) -> None:
    state = settled_state(
        a={"agent_status": "done", "revision": "r7", "session": "/tmp/s.jsonl"},
    )
    done = stub.run("a", "--interval", "0.01", "--json", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    summary = json.loads(done.stdout)["targets"]["a"]
    assert summary["status"] == "done"
    assert summary["revision"] == "r7"
    assert summary["session"] == "/tmp/s.jsonl"


# ── metadata: PEP 723 conformance ─────────────────────────────────────────────


def test_pep723_metadata_precedes_docstring() -> None:
    header = SCRIPT.read_text().split('"""', 1)[0]
    assert header.startswith("#!/usr/bin/env python3\n")
    assert "# /// script" in header
    assert 'requires-python = ">=3.14"' in header
    assert "dependencies = []" in header
    assert header.rstrip().endswith("# ///")


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv is required for the PEP 723 runner")
def test_uv_run_help_executes_without_path_configuration(tmp_path: Path) -> None:
    import os

    done = subprocess.run(
        ["uv", "run", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        env={"HOME": os.environ.get("HOME", ""), "PATH": os.environ.get("PATH", "")},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "usage: herdr-wait" in done.stdout
