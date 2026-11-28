"""Tests for `herdr-lane up`: plan honesty, read-back discipline, and failure state."""

from __future__ import annotations

import json
import shlex
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path

import herdr_cli
import herdr_lane
import pytest
from herdr_cli import EXIT_HERDR, EXIT_OK, EXIT_USAGE, HerdrError

Daemon = Callable[[Sequence[str], Mapping[str, str]], str]
Sibling = Callable[[Sequence[str], Mapping[str, str]], None]


def lane_env(tmp_path: Path) -> dict[str, str]:
    (tmp_path / "orch").mkdir(exist_ok=True)
    (tmp_path / "tm").mkdir(exist_ok=True)
    (tmp_path / "impl").mkdir(exist_ok=True)
    return {
        "HERDR_ENV": "1",
        "HERDR_BIN_PATH": "/fake/herdr",
        "HERDR_LANE_DIR": str(tmp_path / "store"),
        "HERDR_WORKSPACE_ID": "w9",
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


def pane_json(pane_id: str, tab_id: str) -> dict[str, object]:
    return {
        "pane_id": pane_id,
        "terminal_id": f"term-{pane_id}",
        "workspace_id": "w9",
        "tab_id": tab_id,
        "focused": False,
        "agent_status": "idle",
        "revision": 1,
    }


def tab_json(tab_id: str, label: str) -> dict[str, object]:
    return {
        "tab_id": tab_id,
        "workspace_id": "w9",
        "number": 1,
        "label": label,
        "focused": False,
        "pane_count": 1,
        "agent_status": "idle",
    }


def created_tab_response(tab_id: str, pane_id: str, label: str) -> str:
    return json.dumps(
        {"result": {"tab": tab_json(tab_id, label), "root_pane": pane_json(pane_id, tab_id)}}
    )


def split_response(pane_id: str, tab_id: str) -> str:
    return json.dumps({"result": {"pane": pane_json(pane_id, tab_id)}})


class DaemonRecorder:
    """Answers like herdr 0.9.5's `tab create` and `pane split`, recording every argv."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self._tabs: Iterator[tuple[str, str]] = iter([("w9:t1", "w9:p1"), ("w9:t2", "w9:p2")])

    def __call__(self, argv: Sequence[str], _env: Mapping[str, str]) -> str:
        self.calls.append(list(argv))
        if list(argv[1:3]) == ["tab", "create"]:
            tab_id, pane_id = next(self._tabs)
            return created_tab_response(tab_id, pane_id, argv[argv.index("--label") + 1])
        if list(argv[1:3]) == ["pane", "split"]:
            return split_response("w9:p3", "w9:t2")
        raise AssertionError(f"unexpected call: {argv}")


def silent_daemon(_argv: Sequence[str], _env: Mapping[str, str]) -> str:
    return ""


def noop_sibling(_argv: Sequence[str], _env: Mapping[str, str]) -> None:
    return None


def recorder(sink: list[list[str]]) -> Sibling:
    def record(argv: Sequence[str], _env: Mapping[str, str]) -> None:
        sink.append(list(argv))

    return record


def explode(_argv: Sequence[str], _env: Mapping[str, str]) -> str:
    raise AssertionError("dry run must not execute anything")


def explode_sibling(_argv: Sequence[str], _env: Mapping[str, str]) -> None:
    raise AssertionError("dry run must not execute anything")


def planned_daemon_argvs(lines: Sequence[str]) -> list[list[str]]:
    """The plan lines whose argv drives `herdr` itself, split back into tokens."""
    found: list[list[str]] = []
    for line in lines:
        argv = shlex.split(line)
        if argv[1:3] in (["tab", "create"], ["pane", "split"]):
            found.append(argv)
    return found


def test_up_dry_run_prints_the_plan_and_executes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(herdr_cli, "run_herdr_checked", explode)
    monkeypatch.setattr(herdr_lane, "run_sibling", explode_sibling)

    code = herdr_lane.main(up_args(tmp_path, "--dry-run"), lane_env(tmp_path))
    lines = capsys.readouterr().out.strip().splitlines()

    assert code == EXIT_OK
    assert len(lines) == herdr_lane.PLANNED_STEPS
    orch_tab = shlex.split(lines[0])
    assert orch_tab[1:3] == ["tab", "create"]
    assert orch_tab[orch_tab.index("--workspace") + 1] == "w9"
    assert orch_tab[orch_tab.index("--cwd") + 1] == str(tmp_path / "orch")
    assert orch_tab[orch_tab.index("--label") + 1] == "demo"
    crew_tab = shlex.split(lines[2])
    assert crew_tab[crew_tab.index("--label") + 1] == "demo-r1"
    assert crew_tab[crew_tab.index("--cwd") + 1] == str(tmp_path / "tm")
    assert "--direction right" in lines[3]
    assert f"--env HERDR_LANE_DIR={tmp_path / 'store'}" in lines[3]
    assert "--role orch" in lines[1] and "--role tm" in lines[4] and "--role impl" in lines[5]


def test_dry_run_plan_matches_the_executed_argv_token_for_token(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    daemon = DaemonRecorder()
    monkeypatch.setattr(herdr_cli, "run_herdr_checked", daemon)
    monkeypatch.setattr(herdr_lane, "run_sibling", noop_sibling)

    assert herdr_lane.main(up_args(tmp_path, "--dry-run"), lane_env(tmp_path)) == EXIT_OK
    planned = planned_daemon_argvs(capsys.readouterr().out.strip().splitlines())
    assert herdr_lane.main(up_args(tmp_path), lane_env(tmp_path)) == EXIT_OK

    expected = [[token.replace("<tm-pane>", "w9:p2") for token in argv] for argv in planned]
    assert daemon.calls == expected


def test_up_creates_two_tabs_one_split_and_three_agents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    daemon = DaemonRecorder()
    siblings: list[list[str]] = []
    monkeypatch.setattr(herdr_cli, "run_herdr_checked", daemon)
    monkeypatch.setattr(herdr_lane, "run_sibling", recorder(siblings))

    code = herdr_lane.main(up_args(tmp_path, "--revision", "2"), lane_env(tmp_path))
    out = capsys.readouterr().out

    assert code == EXIT_OK
    assert [call[1:3] for call in daemon.calls] == [
        ["tab", "create"],
        ["tab", "create"],
        ["pane", "split"],
    ]
    labels = [argv[argv.index("--label") + 1] for argv in daemon.calls if argv[1] == "tab"]
    assert labels == ["demo", "demo-r2"]
    workspaces = [argv[argv.index("--workspace") + 1] for argv in daemon.calls if argv[1] == "tab"]
    assert workspaces == ["w9", "w9"]
    assert [argv[argv.index("--role") + 1] for argv in siblings] == ["orch", "tm", "impl"]
    assert [argv[argv.index("--pane") + 1] for argv in siblings] == ["w9:p1", "w9:p2", "w9:p3"]
    assert all(argv[argv.index("--task-group") + 1] == "demo" for argv in siblings)
    split = [argv for argv in daemon.calls if argv[2] == "split"][0]
    assert split[split.index("--pane") + 1] == "w9:p2"
    assert "lane demo r2" in out


def test_up_fails_loudly_when_tab_create_names_no_root_pane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[list[str]] = []

    def dispatch(argv: Sequence[str], _env: Mapping[str, str]) -> str:
        calls.append(list(argv))
        label = argv[argv.index("--label") + 1]
        return json.dumps({"result": {"tab": tab_json("w9:t7", label)}})

    monkeypatch.setattr(herdr_cli, "run_herdr_checked", dispatch)
    monkeypatch.setattr(herdr_lane, "run_sibling", noop_sibling)

    code = herdr_lane.main(up_args(tmp_path), lane_env(tmp_path))
    err = capsys.readouterr().err

    assert code == EXIT_HERDR
    assert "bring-up stopped" in err
    assert "result.root_pane" in err
    assert "Created so far — nothing" in err
    assert [argv[1:3] for argv in calls] == [["tab", "create"]]


def test_up_stops_at_the_first_failure_and_names_what_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    calls: list[list[str]] = []

    def dispatch(argv: Sequence[str], _env: Mapping[str, str]) -> str:
        calls.append(list(argv))
        if argv[1:3] == ["tab", "create"]:
            return created_tab_response("w9:t1", "w9:p1", argv[argv.index("--label") + 1])
        raise HerdrError("split refused")

    monkeypatch.setattr(herdr_cli, "run_herdr_checked", dispatch)
    monkeypatch.setattr(herdr_lane, "run_sibling", noop_sibling)

    code = herdr_lane.main(up_args(tmp_path), lane_env(tmp_path))
    err = capsys.readouterr().err

    assert code == EXIT_HERDR
    assert [argv[1:3] for argv in calls] == [
        ["tab", "create"],
        ["tab", "create"],
        ["pane", "split"],
    ]
    assert "bring-up stopped" in err
    assert "split refused" in err
    assert "w9:t1" in err
    assert "w9:p1" in err
    assert "Close those panes before retrying" in err


def test_up_forwards_each_model_to_its_own_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    daemon = DaemonRecorder()
    siblings: list[list[str]] = []
    monkeypatch.setattr(herdr_cli, "run_herdr_checked", daemon)
    monkeypatch.setattr(herdr_lane, "run_sibling", recorder(siblings))
    models = ("--tm-model", "tm-x", "--impl-model", "impl-y")

    assert herdr_lane.main(up_args(tmp_path, "--dry-run", *models), lane_env(tmp_path)) == EXIT_OK
    lines = capsys.readouterr().out.strip().splitlines()
    orch_line, tm_line, impl_line = lines[1], lines[4], lines[5]
    assert "--model tm-x" in tm_line
    assert "--model impl-y" in impl_line
    assert "impl-y" not in tm_line
    assert "tm-x" not in impl_line
    assert "--model" not in orch_line

    assert herdr_lane.main(up_args(tmp_path, *models), lane_env(tmp_path)) == EXIT_OK
    orch_argv, tm_argv, impl_argv = siblings
    assert tm_argv[-2:] == ["--model", "tm-x"]
    assert impl_argv[-2:] == ["--model", "impl-y"]
    assert "--model" not in orch_argv


def test_up_omits_the_model_flag_when_no_model_is_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(herdr_cli, "run_herdr_checked", explode)
    monkeypatch.setattr(herdr_lane, "run_sibling", explode_sibling)

    assert herdr_lane.main(up_args(tmp_path, "--dry-run"), lane_env(tmp_path)) == EXIT_OK
    lines = capsys.readouterr().out.strip().splitlines()

    assert all("--model" not in line for line in lines)


def test_up_requires_the_crew_worktrees(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        herdr_lane.main(
            ["up", "--prefix", "demo", "--cwd-impl", str(tmp_path / "impl")], lane_env(tmp_path)
        )

    assert excinfo.value.code == EXIT_USAGE


def test_up_rejects_a_revision_below_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(herdr_cli, "run_herdr_checked", silent_daemon)
    monkeypatch.setattr(herdr_lane, "run_sibling", noop_sibling)

    code = herdr_lane.main(up_args(tmp_path, "--revision", "0"), lane_env(tmp_path))
    err = capsys.readouterr().err

    assert code == EXIT_USAGE
    assert "--revision 0 is out of range" in err


def test_up_refuses_outside_a_herdr_pane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(herdr_cli, "run_herdr_checked", silent_daemon)
    monkeypatch.setattr(herdr_lane, "run_sibling", noop_sibling)
    env = {key: value for key, value in lane_env(tmp_path).items() if key != "HERDR_ENV"}

    code = herdr_lane.main(up_args(tmp_path), env)
    err = capsys.readouterr().err

    assert code == EXIT_USAGE
    assert "not inside a Herdr-managed pane" in err


def test_up_honors_explicit_workspace_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(herdr_cli, "run_herdr_checked", explode)
    monkeypatch.setattr(herdr_lane, "run_sibling", noop_sibling)

    code = herdr_lane.main(up_args(tmp_path, "--dry-run", "--workspace", "w42"), lane_env(tmp_path))
    lines = capsys.readouterr().out.strip().splitlines()

    assert code == EXIT_OK
    tabs = [shlex.split(line) for line in (lines[0], lines[2])]
    assert [argv[argv.index("--workspace") + 1] for argv in tabs] == ["w42", "w42"]
    assert [argv[argv.index("--label") + 1] for argv in tabs] == ["demo", "demo-r1"]
