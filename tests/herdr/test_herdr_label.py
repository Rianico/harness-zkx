"""Tests for skills/herdr/scripts/herdr_label.py (herdr-label helper)."""

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import herdr_cli
import herdr_label
import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness

SCRIPT = SCRIPTS_DIR / "herdr_label.py"

PANE_ENV = {
    "HERDR_PANE_ID": "w9:p1",
    "HERDR_TAB_ID": "w9:t1",
    "HERDR_WORKSPACE_ID": "w9",
}

# w9:p1 hosts the agent `reviewer`; w9:p2 is a plain shell pane.
SECOND_AGENT = {"pane_id": "w9:p9", "name": "buildbot", "agent": "pi", "agent_status": "idle"}


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPT)


def renames(stub: StubHarness) -> list[list[str]]:
    return [call[1:] for call in stub.calls() if call[2] == "rename"]


def shell_pane_state(**overrides: object) -> dict[str, object]:
    return {**DEFAULT_STATE, "current": "w9:p2", "agents": [], **overrides}


# ── unit ────────────────────────────────────────────────────────────────────────────


def test_conflict_with_finds_the_other_pane() -> None:
    agents = [
        {"pane_id": "w9:p1", "name": "reviewer"},
        {"pane_id": "w9:p9", "name": "buildbot"},
    ]
    assert herdr_label.conflict_with(agents, "buildbot", "w9:p1") == "w9:p9"


@pytest.mark.parametrize("name", ["reviewer", "unused"])
def test_conflict_with_ignores_self_and_free_names(name: str) -> None:
    agents = [{"pane_id": "w9:p1", "name": "reviewer"}]
    assert herdr_label.conflict_with(agents, name, "w9:p1") is None


# ── integration: the happy path ─────────────────────────────────────────────────────


def test_names_the_label_and_the_agent(stub: StubHarness) -> None:
    done = stub.run("buildbot", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "named w9:p1  label=buildbot  agent=buildbot"
    assert renames(stub) == [
        ["pane", "rename", "w9:p1", "buildbot"],
        ["agent", "rename", "w9:p1", "buildbot"],
    ]


def test_json_reports_both_names(stub: StubHarness) -> None:
    done = stub.run("buildbot", "--json", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert json.loads(done.stdout) == {
        "pane_id": "w9:p1",
        "label": "buildbot",
        "agent": "buildbot",
    }


def test_label_only_leaves_the_agent_name_alone(stub: StubHarness) -> None:
    done = stub.run("review pane", "--label-only", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "named w9:p1  label=review pane  agent=-"
    assert renames(stub) == [["pane", "rename", "w9:p1", "review pane"]]


def test_a_pane_without_an_agent_is_only_labelled(stub: StubHarness) -> None:
    done = stub.run("scratch-pad", env=PANE_ENV, state=shell_pane_state())
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "named w9:p2  label=scratch-pad  agent=-"
    assert renames(stub) == [["pane", "rename", "w9:p2", "scratch-pad"]]


def test_a_multi_word_label_is_allowed_without_an_agent(stub: StubHarness) -> None:
    done = stub.run("review pane", env=PANE_ENV, state=shell_pane_state())
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "label=review pane" in done.stdout


def test_clear_drops_both_names(stub: StubHarness) -> None:
    done = stub.run("--clear", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "cleared w9:p1  label=-  agent=-"
    assert renames(stub) == [
        ["pane", "rename", "w9:p1", "--clear"],
        ["agent", "rename", "w9:p1", "--clear"],
    ]


def test_pane_flag_targets_another_pane(stub: StubHarness) -> None:
    state = {**DEFAULT_STATE, "agents": [SECOND_AGENT]}
    done = stub.run("buildbot", "--pane", "w9:p9", env=PANE_ENV, state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.strip() == "named w9:p9  label=buildbot  agent=buildbot"
    assert [call[1:3] for call in stub.calls()] == [
        ["agent", "list"],
        ["pane", "rename"],
        ["agent", "rename"],
    ]


def test_dry_run_prints_the_calls_and_renames_nothing(stub: StubHarness) -> None:
    done = stub.run("buildbot", "--dry-run", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert renames(stub) == []
    calls = json.loads(done.stdout)
    assert calls[0][1:5] == ["pane", "rename", "w9:p1", "buildbot"]
    assert calls[1][1:5] == ["agent", "rename", "w9:p1", "buildbot"]


def test_dry_run_still_rejects_a_bad_name(stub: StubHarness) -> None:
    done = stub.run("Reviewer", "--dry-run", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert renames(stub) == []


# ── integration: guards, validated before any mutation ──────────────────────────────


def test_an_invalid_agent_name_is_rejected_without_mutating(stub: StubHarness) -> None:
    done = stub.run("Reviewer", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not a valid agent name" in done.stderr
    assert renames(stub) == []


def test_a_multi_word_name_needs_label_only_when_an_agent_is_present(stub: StubHarness) -> None:
    done = stub.run("review pane", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "--label-only" in done.stderr
    assert renames(stub) == []


def test_a_name_already_in_use_is_rejected_without_mutating(stub: StubHarness) -> None:
    state = {**DEFAULT_STATE, "agents": [*DEFAULT_STATE["agents"], SECOND_AGENT]}
    done = stub.run("buildbot", env=PANE_ENV, state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "already used by pane w9:p9" in done.stderr
    assert renames(stub) == []


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (("--clear", "buildbot"), "either NAME or --clear"),
        ((), "pass NAME"),
    ],
)
def test_name_and_clear_are_mutually_required(
    stub: StubHarness, argv: tuple[str, ...], expected: str
) -> None:
    done = stub.run(*argv, env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert expected in done.stderr


def test_refuses_without_herdr_env(stub: StubHarness) -> None:
    done = stub.run("buildbot", env={"HERDR_ENV": None})
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "HERDR_ENV" in done.stderr
    assert stub.calls() == []


def test_a_pane_rename_failure_is_reported(stub: StubHarness) -> None:
    error = {"code": "pane_not_found", "message": "pane w9:p1 not found"}
    done = stub.run("buildbot", env=PANE_ENV, state={**DEFAULT_STATE, "pane_rename_error": error})
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "pane_not_found" in done.stderr
    assert "Traceback" not in done.stderr


def test_an_agent_rename_failure_is_reported(stub: StubHarness) -> None:
    error = {"code": "agent_not_found", "message": "no agent in w9:p1"}
    done = stub.run("buildbot", env=PANE_ENV, state={**DEFAULT_STATE, "agent_rename_error": error})
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "agent_not_found" in done.stderr
    assert "Traceback" not in done.stderr


# ── metadata: PEP 723 conformance ───────────────────────────────────────────────────


def test_pep723_metadata_precedes_docstring() -> None:
    header = SCRIPT.read_text().split('"""', 1)[0]
    assert header.startswith("#!/usr/bin/env python3\n")
    assert "# /// script" in header
    assert 'requires-python = ">=3.12"' in header
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
    assert "usage: herdr-label" in done.stdout
