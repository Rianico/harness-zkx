"""Tests for skills/herdr/scripts/herdr_lease.py (task lease and trajectory helper)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import herdr_lease
import pytest
import yaml


def test_get_lease_returns_none_when_empty(tmp_path: Path) -> None:
    assert herdr_lease.get_lease("callee", base_dir=tmp_path) is None


def test_acquire_and_get_lease(tmp_path: Path) -> None:
    lease = herdr_lease.acquire_lease("callee", "ticket.md", "orchestrator", base_dir=tmp_path)
    assert lease["target"] == "callee"
    assert lease["ticket"] == "ticket.md"
    assert lease["caller"] == "orchestrator"
    assert "timestamp" in lease

    fetched = herdr_lease.get_lease("callee", base_dir=tmp_path)
    assert fetched == lease


def test_acquire_and_match_by_name_or_pane_id(tmp_path: Path) -> None:
    lease = herdr_lease.acquire_lease(
        "callee", "ticket.md", "orchestrator", pane_id="w9:p2", base_dir=tmp_path
    )
    assert lease["target"] == "callee"
    assert lease["pane_id"] == "w9:p2"

    # Both name and pane_id can be queried
    assert herdr_lease.get_lease("callee", base_dir=tmp_path) == lease
    assert herdr_lease.get_lease("w9:p2", base_dir=tmp_path) == lease
    assert herdr_lease.is_leased("callee", base_dir=tmp_path) is True
    assert herdr_lease.is_leased("w9:p2", base_dir=tmp_path) is True

    # Can release by pane_id
    assert herdr_lease.release_lease("w9:p2", base_dir=tmp_path) is True
    assert herdr_lease.get_lease("callee", base_dir=tmp_path) is None
    assert herdr_lease.get_lease("w9:p2", base_dir=tmp_path) is None


def test_acquire_multiple_targets(tmp_path: Path) -> None:
    _ = herdr_lease.acquire_lease("callee1", "t1.md", "tm", base_dir=tmp_path)
    _ = herdr_lease.acquire_lease("callee2", "t2.md", "tm", base_dir=tmp_path)

    l1 = herdr_lease.get_lease("callee1", base_dir=tmp_path)
    l2 = herdr_lease.get_lease("callee2", base_dir=tmp_path)
    assert l1 is not None and l1["ticket"] == "t1.md"
    assert l2 is not None and l2["ticket"] == "t2.md"


def test_release_lease(tmp_path: Path) -> None:
    _ = herdr_lease.acquire_lease("callee", "t.md", "tm", base_dir=tmp_path)
    assert herdr_lease.get_lease("callee", base_dir=tmp_path) is not None

    assert herdr_lease.release_lease("callee", base_dir=tmp_path) is True
    assert herdr_lease.get_lease("callee", base_dir=tmp_path) is None
    assert herdr_lease.release_lease("callee", base_dir=tmp_path) is False


def test_herdr_lease_cwd_fallback(tmp_path: Path) -> None:
    cwd_file = tmp_path / ".herdr-lease.json"
    _ = cwd_file.write_text('{"callee": {"ticket": "t.md", "caller": "tm"}}', encoding="utf-8")

    lease = herdr_lease.get_lease("callee", base_dir=tmp_path)
    assert lease is not None
    assert lease["ticket"] == "t.md"

    assert herdr_lease.release_lease("callee", base_dir=tmp_path) is True
    assert herdr_lease.get_lease("callee", base_dir=tmp_path) is None


def test_env_threading_for_lease_functions(tmp_path: Path) -> None:
    lane_dir = tmp_path / "custom_lane"
    env = {"HERDR_LANE_DIR": str(lane_dir)}

    assert herdr_lease.get_lease("callee", env=env) is None
    lease = herdr_lease.acquire_lease("callee", "ticket.md", "lead", pane_id="w1:p1", env=env)
    assert lease["ticket"] == "ticket.md"
    assert (lane_dir / ".lane" / "tasks.yaml").is_file()

    fetched = herdr_lease.get_lease("w1:p1", env=env)
    assert fetched == lease

    assert herdr_lease.release_lease("callee", env=env) is True
    assert herdr_lease.get_lease("callee", env=env) is None


def test_acquire_persists_ticket_and_task_ids(tmp_path: Path) -> None:
    ticket_id = "#182-herdr-msg-enhance"
    task_id = "#182-herdr-msg-enhance#lease-ids"
    lease = herdr_lease.acquire_lease(
        "callee",
        "ticket.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id=ticket_id,
        task_id=task_id,
    )
    assert lease["ticket_id"] == ticket_id
    assert lease["task_id"] == task_id

    fetched = herdr_lease.get_lease("callee", base_dir=tmp_path)
    assert fetched is not None
    assert fetched["ticket_id"] == ticket_id
    assert fetched["task_id"] == task_id


def test_acquire_stores_and_replaces_caller_recovery(tmp_path: Path) -> None:
    task_id = "#183#recovery"
    _ = herdr_lease.acquire_lease(
        "callee",
        "ticket.md",
        "orch",
        base_dir=tmp_path,
        ticket_id="#183",
        task_id=task_id,
        caller_recovery={"pane_id": "w1:p1", "kind": "pi", "cwd": "/repo"},
    )
    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["caller_recovery"] == {"pane_id": "w1:p1", "kind": "pi", "cwd": "/repo"}
    assert set(task["caller_recovery"]) == {"pane_id", "kind", "cwd"}

    # A re-acquire replaces the mapping (latest dispatcher wins) without inventing keys.
    _ = herdr_lease.acquire_lease(
        "callee",
        "ticket.md",
        "orch",
        base_dir=tmp_path,
        ticket_id="#183",
        task_id=task_id,
        caller_recovery={"pane_id": "w1:p1"},
    )
    replaced = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert replaced is not None
    assert replaced["caller_recovery"] == {"pane_id": "w1:p1"}


def test_acquire_omits_empty_caller_recovery_fields(tmp_path: Path) -> None:
    task_id = "#183#omit"
    _ = herdr_lease.acquire_lease(
        "callee",
        "ticket.md",
        "orch",
        base_dir=tmp_path,
        ticket_id="#183",
        task_id=task_id,
        caller_recovery={"pane_id": "w1:p1", "kind": "", "cwd": None, "resume_cmd": ""},
    )
    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["caller_recovery"] == {"pane_id": "w1:p1"}


def test_acquire_without_ids_omits_new_keys(tmp_path: Path) -> None:
    lease = herdr_lease.acquire_lease(
        "callee", "ticket.md", "orchestrator", pane_id="w9:p2", base_dir=tmp_path
    )
    assert "ticket_id" not in lease
    assert "task_id" not in lease

    fetched = herdr_lease.get_lease("callee", base_dir=tmp_path)
    assert fetched is not None
    assert "ticket_id" not in fetched
    assert "task_id" not in fetched
    # Existing fields remain intact
    assert fetched["target"] == "callee"
    assert fetched["ticket"] == "ticket.md"
    assert fetched["caller"] == "orchestrator"
    assert fetched["pane_id"] == "w9:p2"
    assert "timestamp" in fetched


def test_legacy_lease_without_new_keys_loads_and_releases(tmp_path: Path) -> None:
    cwd_file = tmp_path / ".herdr-lease.json"
    _ = cwd_file.write_text(
        '{"callee": {"target": "callee", "ticket": "t.md", '
        '"caller": "tm", "pane_id": "w7:p3", "timestamp": "2020-01-01T00:00:00Z"}}',
        encoding="utf-8",
    )

    # Loads and matches by pane_id
    fetched = herdr_lease.get_lease("w7:p3", base_dir=tmp_path)
    assert fetched is not None
    assert fetched["ticket"] == "t.md"
    assert "ticket_id" not in fetched
    assert "task_id" not in fetched

    # Releases by pane_id
    assert herdr_lease.release_lease("w7:p3", base_dir=tmp_path) is True
    assert herdr_lease.get_lease("callee", base_dir=tmp_path) is None


def _read_state(tmp_path: Path) -> dict[str, Any]:
    text = (tmp_path / ".lane" / "tasks.yaml").read_text(encoding="utf-8")
    parsed = yaml.safe_load(text)
    assert isinstance(parsed, dict)
    return parsed


def test_acquire_writes_yaml_task_roundtrip(tmp_path: Path) -> None:
    lease = herdr_lease.acquire_lease(
        "callee",
        "ticket.md",
        "orchestrator",
        pane_id="w9:p2",
        base_dir=tmp_path,
        ticket_id="#183",
        task_id="#183#a",
        task_group="tg",
    )

    assert (tmp_path / ".lane" / "tasks.yaml").is_file()
    state = _read_state(tmp_path)
    assert set(state) == {"active_leases", "tasks"}

    active = state["active_leases"]["callee"]
    assert active["target"] == "callee"
    assert active["task_id"] == "#183#a"
    assert active["pane_id"] == "w9:p2"
    assert active["acquired_at"] == active["timestamp"]

    task = state["tasks"]["#183#a"]
    assert task["ticket_id"] == "#183"
    assert task["task_id"] == "#183#a"
    assert task["ticket_path"] == "ticket.md"
    assert task["task_group"] == "tg"
    assert task["status"] == "dispatched"
    assert task["assignee"] == "callee"
    assert task["caller"] == "orchestrator"
    assert len(task["trajectory"]) == 1
    assert task["trajectory"][0]["event"] == "dispatched"
    assert task["trajectory"][0]["to_status"] == "dispatched"

    assert herdr_lease.get_lease("callee", base_dir=tmp_path) == lease


def test_transition_appends_trajectory(tmp_path: Path) -> None:
    task_id = "#183#a"
    _ = herdr_lease.acquire_lease(
        "callee", "ticket.md", "orch", base_dir=tmp_path, ticket_id="#183", task_id=task_id
    )

    second = herdr_lease.transition(task_id, "in_progress", base_dir=tmp_path)
    assert second["status"] == "in_progress"

    third = herdr_lease.transition(task_id, "completed", note="all green", base_dir=tmp_path)
    trajectory = third["trajectory"]
    assert [event["seq"] for event in trajectory] == [1, 2, 3]
    assert [event["to_status"] for event in trajectory] == [
        "dispatched",
        "in_progress",
        "completed",
    ]
    assert trajectory[1]["from_status"] == "dispatched"
    assert trajectory[2]["from_status"] == "in_progress"
    assert trajectory[2]["note"] == "all green"
    assert third["status"] == "completed"
    assert herdr_lease.get_task(task_id, base_dir=tmp_path) == third


def test_release_lease_is_soft_completion(tmp_path: Path) -> None:
    task_id = "#183#a"
    _ = herdr_lease.acquire_lease(
        "callee", "ticket.md", "orch", base_dir=tmp_path, ticket_id="#183", task_id=task_id
    )
    _ = herdr_lease.transition(task_id, "in_progress", base_dir=tmp_path)

    assert herdr_lease.release_lease("callee", base_dir=tmp_path) is True
    assert herdr_lease.get_lease("callee", base_dir=tmp_path) is None

    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["status"] == "in_progress"
    assert len(task["trajectory"]) == 2


def test_reacquire_same_target_keeps_single_lease(tmp_path: Path) -> None:
    _ = herdr_lease.acquire_lease("callee", "a.md", "orch", pane_id="w9:p1", base_dir=tmp_path)
    _ = herdr_lease.acquire_lease("callee", "b.md", "orch", pane_id="w9:p1", base_dir=tmp_path)

    state = _read_state(tmp_path)
    assert list(state["active_leases"]) == ["callee"]
    assert state["active_leases"]["callee"]["ticket"] == "b.md"


def test_reacquire_same_pane_under_new_key_keeps_single_lease(tmp_path: Path) -> None:
    _ = herdr_lease.acquire_lease("callee-a", "a.md", "orch", pane_id="w9:p1", base_dir=tmp_path)
    _ = herdr_lease.acquire_lease("callee-b", "b.md", "orch", pane_id="w9:p1", base_dir=tmp_path)

    state = _read_state(tmp_path)
    assert list(state["active_leases"]) == ["callee-b"]


def test_legacy_json_fallback_loads_without_tasks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lane = tmp_path / ".lane"
    lane.mkdir()
    _ = (lane / "lease.json").write_text(
        json.dumps({"callee": {"ticket": "t.md", "caller": "tm"}}), encoding="utf-8"
    )

    lease = herdr_lease.get_lease("callee", base_dir=tmp_path)
    assert lease is not None
    assert lease["ticket"] == "t.md"
    assert lease["target"] == "callee"
    assert lease["acquired_at"] == lease["timestamp"]
    assert herdr_lease.list_tasks(base_dir=tmp_path) == []

    assert herdr_lease.main(["show", "--yaml"], env={"HERDR_LANE_DIR": str(tmp_path)}) == 0


def test_legacy_yaml_fallback_loads(tmp_path: Path) -> None:
    lane = tmp_path / ".lane"
    lane.mkdir()
    _ = (lane / "lease.yaml").write_text(
        "callee:\n  ticket: t.md\n  caller: tm\n", encoding="utf-8"
    )

    lease = herdr_lease.get_lease("callee", base_dir=tmp_path)
    assert lease is not None
    assert lease["ticket"] == "t.md"


def test_cli_show_yaml_prints_canonical_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _ = herdr_lease.acquire_lease(
        "callee", "ticket.md", "orch", base_dir=tmp_path, ticket_id="#183", task_id="#183#a"
    )

    assert herdr_lease.main(["show", "--yaml"], env={"HERDR_LANE_DIR": str(tmp_path)}) == 0

    captured = capsys.readouterr()
    rendered = yaml.safe_load(captured.out)
    assert isinstance(rendered, dict)
    assert set(rendered) == {"active_leases", "tasks"}
    assert rendered["active_leases"]["callee"]["task_id"] == "#183#a"
    assert rendered["tasks"]["#183#a"]["status"] == "dispatched"


def test_cli_show_empty_state_prints_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert herdr_lease.main(["show"], env={"HERDR_LANE_DIR": str(tmp_path)}) == 0

    captured = capsys.readouterr()
    assert "no active leases" in captured.out


def test_cli_transition_invalid_status_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _ = herdr_lease.acquire_lease(
        "callee", "ticket.md", "orch", base_dir=tmp_path, ticket_id="#183", task_id="#183#a"
    )

    code = herdr_lease.main(
        ["transition", "#183#a", "bogus"], env={"HERDR_LANE_DIR": str(tmp_path)}
    )
    assert code == 2
    _ = capsys.readouterr()


def test_cli_transition_appends_event(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "#183#a"
    _ = herdr_lease.acquire_lease(
        "callee", "ticket.md", "orch", base_dir=tmp_path, ticket_id="#183", task_id=task_id
    )

    code = herdr_lease.main(
        ["transition", task_id, "in_progress", "--note", "started"],
        env={"HERDR_LANE_DIR": str(tmp_path)},
    )
    assert code == 0

    captured = capsys.readouterr()
    assert "task #183#a: dispatched -> in_progress (started)" in captured.out

    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["status"] == "in_progress"
    assert task["trajectory"][-1]["note"] == "started"
