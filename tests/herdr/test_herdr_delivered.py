"""Callee-observed `delivered` mark on first working transition (herdr228-delivered).

The callee marks its own observed consumption: the first transition of a
dispatched task to `in_progress` also records one `delivered` binding on the
task, in the same atomic store write. Everything else stays as it is.

Consumption, minimally: the first working (`in_progress`) transition after the
`dispatched` trajectory event counts. What does NOT count, explicitly:
output events after dispatch (no cheap callee seam reads them, so they are
excluded, never silent), revision movement (no store path reads a revision),
pane reads or wait barriers (dispatcher-side, never callee-observed),
`blocked`/`rework`/`completed` transitions (not working), a direct
`dispatched` -> `completed` run with no working transition (no consumption
observed), and tasks whose trajectory holds no `dispatched` event (no dispatch
timestamp to be after). A pane that never transitions writes nothing.
"""

from __future__ import annotations

import inspect
from pathlib import Path
from typing import Any

import herdr_lease
import yaml


def _acquire(tmp_path: Path) -> str:
    task_id = "#228#a"
    _ = herdr_lease.acquire_lease(
        "callee",
        "ticket.md",
        "orch",
        base_dir=tmp_path,
        ticket_id="#228",
        task_id=task_id,
    )
    return task_id


def test_first_working_transition_marks_delivered(tmp_path: Path) -> None:
    task_id = _acquire(tmp_path)

    marked = herdr_lease.transition(task_id, "in_progress", base_dir=tmp_path)

    assert marked["status"] == "in_progress"
    delivered = marked.get("delivered")
    assert isinstance(delivered, dict)
    assert delivered["event"] == "delivered"
    assert delivered["task_id"] == task_id
    assert delivered["ticket_id"] == "#228"
    assert isinstance(delivered.get("timestamp"), str) and delivered["timestamp"]
    # The trajectory pins are untouched: the mark rides beside them, not in them.
    assert [event["event"] for event in marked["trajectory"]] == [
        "dispatched",
        "in_progress",
    ]


def test_never_processed_task_carries_no_mark(tmp_path: Path) -> None:
    task_id = _acquire(tmp_path)

    task = herdr_lease.get_task(task_id, base_dir=tmp_path)

    assert task is not None
    assert "delivered" not in task


def test_working_mark_needs_no_revision_context(tmp_path: Path) -> None:
    """A warm pane at revision 0 still marks: the working transition is the seam."""
    task_id = _acquire(tmp_path)

    marked = herdr_lease.transition(task_id, "in_progress", base_dir=tmp_path)

    assert isinstance(marked.get("delivered"), dict)


def test_non_working_transitions_leave_no_mark(tmp_path: Path) -> None:
    for status in ("blocked", "rework", "completed"):
        lane = tmp_path / status
        lane.mkdir()
        task_id = _acquire(lane)

        moved = herdr_lease.transition(task_id, status, base_dir=lane)

        assert moved["status"] == status
        assert "delivered" not in moved


def test_no_store_path_reads_a_revision(tmp_path: Path) -> None:
    """Revision movement alone cannot mark: no entry point takes a revision."""
    del tmp_path  # the seam is static; no store needed
    for name in ("record_event", "transition", "acquire_lease"):
        params = inspect.signature(getattr(herdr_lease, name)).parameters
        assert not [param for param in params if "revision" in param.lower()], name


def test_working_transition_keeps_a_single_store_write(tmp_path: Path) -> None:
    """Event-driven, not polled: the mark shares the transition's one write."""
    writes = 0
    real_write = herdr_lease._write_state

    def counting(state: dict[str, Any], base_dir: object = None, env: object = None) -> None:
        nonlocal writes
        writes += 1
        real_write(state, base_dir=base_dir, env=env)

    herdr_lease._write_state = counting  # type: ignore[assignment]
    try:
        working_id = _acquire(tmp_path)
        writes = 0
        _ = herdr_lease.transition(working_id, "in_progress", base_dir=tmp_path)
        working_writes = writes

        other = tmp_path / "other"
        other.mkdir()
        other_id = _acquire(other)
        writes = 0
        _ = herdr_lease.transition(other_id, "blocked", base_dir=other)
        plain_writes = writes
    finally:
        herdr_lease._write_state = real_write  # type: ignore[assignment]

    assert working_writes == 1
    assert plain_writes == 1


def test_no_timer_or_polling_machinery(tmp_path: Path) -> None:
    """The mark fires on observation: no daemon, timer, socket, or poll loop."""
    del tmp_path  # the seam is static; no store needed
    module_file = herdr_lease.__file__
    assert module_file is not None
    source = Path(module_file).read_text(encoding="utf-8")
    for probe in ("threading", "socket", "Timer", "time.sleep", ".poll(", "select("):
        assert probe not in source


def test_second_working_transition_adds_no_second_mark(tmp_path: Path) -> None:
    task_id = _acquire(tmp_path)
    first = herdr_lease.transition(task_id, "in_progress", base_dir=tmp_path)
    _ = herdr_lease.transition(task_id, "rework", base_dir=tmp_path)

    second = herdr_lease.transition(task_id, "in_progress", base_dir=tmp_path)

    assert second["delivered"] == first["delivered"]
    assert [event["event"] for event in second["trajectory"]] == [
        "dispatched",
        "in_progress",
        "rework",
        "in_progress",
    ]


def test_task_without_dispatch_event_gets_no_mark(tmp_path: Path) -> None:
    task_id = _acquire(tmp_path)
    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    task["trajectory"] = []
    state_path = tmp_path / ".lane" / "tasks.yaml"
    raw = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    raw["tasks"][task_id]["trajectory"] = []
    _ = state_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    moved = herdr_lease.transition(task_id, "in_progress", base_dir=tmp_path)

    assert moved["status"] == "in_progress"
    assert "delivered" not in moved


def test_unknown_task_stays_none(tmp_path: Path) -> None:
    assert herdr_lease.record_event("#228#missing", "in_progress", base_dir=tmp_path) is None
