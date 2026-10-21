"""Tests for `herdr-lane up`: plan honesty, read-back discipline, and failure state."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import herdr_lane
import pytest
from herdr_cli import EXIT_HERDR, EXIT_OK, EXIT_USAGE, HerdrError

Daemon = Callable[[Sequence[str], Mapping[str, str]], str]
Sibling = Callable[[Sequence[str], Mapping[str, str]], None]


def lane_env(tmp_path: Path) -> dict[str, str]:
    (tmp_path / "orch").mkdir()
    (tmp_path / "tm").mkdir()
    (tmp_path / "impl").mkdir()
    return {
        "HERDR_ENV": "1",
        "HERDR_BIN_PATH": "/fake/herdr",
        "HERDR_LANE_DIR": str(tmp_path / "store"),
        "PWD": str(tmp_path / "orch"),
    }


def up_args(tmp_path: Path, *extra: str) -> list[str]:
    return [
        "up",
        "--prefix",
        "demo",
        "--cwd-tm",
        str(tmp_path / "tm"),
        "--cwd-impl",
        str(tmp_path / "impl"),
        *extra,
    ]


def silent_daemon(_argv: Sequence[str], _env: Mapping[str, str]) -> str:
    return ""


def noop_sibling(_argv: Sequence[str], _env: Mapping[str, str]) -> None:
    return None


def recorder(sink: list[list[str]]) -> Sibling:
    def record(argv: Sequence[str], _env: Mapping[str, str]) -> None:
        sink.append(list(argv))

    return record


def test_up_dry_run_prints_the_plan_and_executes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def explode(_argv: Sequence[str], _env: Mapping[str, str]) -> str:
        raise AssertionError("dry run must not execute anything")

    def explode_sibling(_argv: Sequence[str], _env: Mapping[str, str]) -> None:
        raise AssertionError("dry run must not execute anything")

    monkeypatch.setattr(herdr_lane, "run_herdr_checked", explode)
    monkeypatch.setattr(herdr_lane, "run_sibling", explode_sibling)

    code = herdr_lane.main(up_args(tmp_path, "--dry-run"), lane_env(tmp_path))
    lines = capsys.readouterr().out.strip().splitlines()

    assert code == EXIT_OK
    assert len(lines) == herdr_lane.PLANNED_STEPS
    assert "tab create --label demo " in lines[0]
    assert "tab create --label demo-r1 " in lines[2]
    assert "--direction right" in lines[3]
    assert f"--env HERDR_LANE_DIR={tmp_path / 'store'}" in lines[3]
    assert "--role orch" in lines[1] and "--role tm" in lines[4] and "--role impl" in lines[5]


def test_up_creates_two_tabs_one_split_and_three_agents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    daemon: list[list[str]] = []
    siblings: list[list[str]] = []
    created = {"tabs": 0}

    def dispatch(argv: Sequence[str], _env: Mapping[str, str]) -> str:
        daemon.append(list(argv))
        if argv[1] == "tab" and argv[2] == "create":
            created["tabs"] += 1
            return json.dumps({"result": {"tab": {"tab_id": f"w9:t{created['tabs']}"}}})
        if argv[1] == "pane" and argv[2] == "list":
            return json.dumps(
                {
                    "result": {
                        "panes": [
                            {"tab_id": "w9:t1", "pane_id": "w9:p1"},
                            {"tab_id": "w9:t2", "pane_id": "w9:p2"},
                        ]
                    }
                }
            )
        if argv[1] == "pane" and argv[2] == "split":
            return json.dumps({"result": {"pane": {"pane_id": "w9:p3"}}})
        raise AssertionError(f"unexpected call: {argv}")

    monkeypatch.setattr(herdr_lane, "run_herdr_checked", dispatch)
    monkeypatch.setattr(herdr_lane, "run_sibling", recorder(siblings))

    code = herdr_lane.main(up_args(tmp_path, "--revision", "2"), lane_env(tmp_path))
    out = capsys.readouterr().out

    assert code == EXIT_OK
    labels = [argv[argv.index("--label") + 1] for argv in daemon if argv[1] == "tab"]
    assert labels == ["demo", "demo-r2"]
    assert [argv[argv.index("--role") + 1] for argv in siblings] == ["orch", "tm", "impl"]
    assert [argv[argv.index("--pane") + 1] for argv in siblings] == ["w9:p1", "w9:p2", "w9:p3"]
    assert all(argv[argv.index("--task-group") + 1] == "demo" for argv in siblings)
    split = [argv for argv in daemon if argv[2] == "split"][0]
    assert split[split.index("--pane") + 1] == "w9:p2"
    assert "lane demo r2" in out


def test_up_reads_the_tab_id_from_tab_list_when_the_response_is_silent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def dispatch(argv: Sequence[str], _env: Mapping[str, str]) -> str:
        calls.append(list(argv))
        if argv[1] == "tab" and argv[2] == "create":
            return json.dumps({"result": {"tab": {"label": argv[argv.index("--label") + 1]}}})
        if argv[1] == "tab" and argv[2] == "list":
            return json.dumps(
                {
                    "result": {
                        "tabs": [
                            {"tab_id": "w9:t7", "label": "demo"},
                            {"tab_id": "w9:t8", "label": "demo-r1"},
                        ]
                    }
                }
            )
        if argv[1] == "pane" and argv[2] == "list":
            return json.dumps(
                {
                    "result": {
                        "panes": [
                            {"tab_id": "w9:t7", "pane_id": "w9:p7"},
                            {"tab_id": "w9:t8", "pane_id": "w9:p8"},
                        ]
                    }
                }
            )
        if argv[1] == "pane" and argv[2] == "split":
            return json.dumps({"result": {"pane": {"pane_id": "w9:p9"}}})
        raise AssertionError(f"unexpected call: {argv}")

    siblings: list[list[str]] = []
    monkeypatch.setattr(herdr_lane, "run_herdr_checked", dispatch)
    monkeypatch.setattr(herdr_lane, "run_sibling", recorder(siblings))

    code = herdr_lane.main(up_args(tmp_path), lane_env(tmp_path))

    assert code == EXIT_OK
    assert ("tab", "list") in [(argv[1], argv[2]) for argv in calls]
    assert [argv[argv.index("--pane") + 1] for argv in siblings][0] == "w9:p7"


def test_up_stops_at_the_first_failure_and_names_what_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def dispatch(argv: Sequence[str], _env: Mapping[str, str]) -> str:
        if argv[1] == "tab":
            return json.dumps({"result": {"tab": {"tab_id": "w9:t1"}}})
        if argv[1] == "pane" and argv[2] == "list":
            return json.dumps({"result": {"panes": [{"tab_id": "w9:t1", "pane_id": "w9:p1"}]}})
        raise HerdrError("split refused")

    monkeypatch.setattr(herdr_lane, "run_herdr_checked", dispatch)
    monkeypatch.setattr(herdr_lane, "run_sibling", noop_sibling)

    code = herdr_lane.main(up_args(tmp_path), lane_env(tmp_path))
    err = capsys.readouterr().err

    assert code == EXIT_HERDR
    assert "bring-up stopped" in err
    assert "split refused" in err
    assert "w9:t1" in err
    assert "Close those panes before retrying" in err


def test_up_requires_the_crew_worktrees(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        herdr_lane.main(
            ["up", "--prefix", "demo", "--cwd-impl", str(tmp_path / "impl")], lane_env(tmp_path)
        )

    assert excinfo.value.code == EXIT_USAGE


def test_up_rejects_a_revision_below_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(herdr_lane, "run_herdr_checked", silent_daemon)
    monkeypatch.setattr(herdr_lane, "run_sibling", noop_sibling)

    code = herdr_lane.main(up_args(tmp_path, "--revision", "0"), lane_env(tmp_path))
    err = capsys.readouterr().err

    assert code == EXIT_USAGE
    assert "--revision 0 is out of range" in err


def test_up_refuses_outside_a_herdr_pane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(herdr_lane, "run_herdr_checked", silent_daemon)
    monkeypatch.setattr(herdr_lane, "run_sibling", noop_sibling)
    env = {key: value for key, value in lane_env(tmp_path).items() if key != "HERDR_ENV"}

    code = herdr_lane.main(up_args(tmp_path), env)
    err = capsys.readouterr().err

    assert code == EXIT_USAGE
    assert "not inside a Herdr-managed pane" in err
