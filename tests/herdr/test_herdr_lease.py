"""Tests for skills/herdr/scripts/herdr_lease.py (task lease and trajectory helper)."""

from __future__ import annotations

import fcntl
import json
import multiprocessing
import os
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Protocol

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
    # Writes emit the canonical A2A spelling; dispatch is SUBMITTED ("handed over,
    # not yet worked"). The trajectory `event` label is an action, so it stays the
    # caller's own token.
    assert task["status"] == herdr_lease.STATE_SUBMITTED
    assert task["assignee"] == "callee"
    assert task["caller"] == "orchestrator"
    assert len(task["trajectory"]) == 1
    assert task["trajectory"][0]["event"] == "dispatched"
    assert task["trajectory"][0]["to_status"] == herdr_lease.STATE_SUBMITTED

    assert herdr_lease.get_lease("callee", base_dir=tmp_path) == lease


def test_transition_appends_trajectory(tmp_path: Path) -> None:
    task_id = "#183#a"
    _ = herdr_lease.acquire_lease(
        "callee", "ticket.md", "orch", base_dir=tmp_path, ticket_id="#183", task_id=task_id
    )

    # The callers below pass historical tokens; `transition` accepts them and the
    # store persists the canonical state name.
    second = herdr_lease.transition(task_id, "in_progress", base_dir=tmp_path)
    assert second["status"] == herdr_lease.STATE_WORKING

    third = herdr_lease.transition(task_id, "completed", note="all green", base_dir=tmp_path)
    trajectory = third["trajectory"]
    assert [event["seq"] for event in trajectory] == [1, 2, 3]
    assert [event["to_status"] for event in trajectory] == [
        herdr_lease.STATE_SUBMITTED,
        herdr_lease.STATE_WORKING,
        herdr_lease.STATE_COMPLETED,
    ]
    assert trajectory[1]["from_status"] == herdr_lease.STATE_SUBMITTED
    assert trajectory[2]["from_status"] == herdr_lease.STATE_WORKING
    assert trajectory[2]["note"] == "all green"
    assert third["status"] == herdr_lease.STATE_COMPLETED
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
    assert task["status"] == herdr_lease.STATE_WORKING
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
    assert rendered["tasks"]["#183#a"]["status"] == herdr_lease.STATE_SUBMITTED


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
    # The line reports the persisted states, which are canonical spellings even
    # though the caller passed the historical token `in_progress`.
    assert (
        f"task #183#a: {herdr_lease.STATE_SUBMITTED} -> {herdr_lease.STATE_WORKING} (started)"
    ) in captured.out

    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["status"] == herdr_lease.STATE_WORKING
    assert task["trajectory"][-1]["note"] == "started"


# ── #182 t3: the A2A state vocabulary, persisted identity, resolver-only stores ──────


TASK_ID = "#182#a2a"


def test_a_write_emits_the_canonical_state_and_reads_as_completed(tmp_path: Path) -> None:
    """A record this module writes spells its state with the A2A enum and reads back as it.

    Pin -> mutant: a write path that re-renders the enum into a historical token, or a reader
    that knows only the historical spelling and so answers None for a record written here.
    """
    _ = herdr_lease.acquire_lease(
        "callee", "182.md", "orch", base_dir=tmp_path, ticket_id="#182", task_id=TASK_ID
    )

    done = herdr_lease.transition(TASK_ID, herdr_lease.STATE_COMPLETED, base_dir=tmp_path)

    # The literal spelling is pinned, not only the constant: the enum name must reach the file.
    raw = yaml.safe_load((tmp_path / ".lane" / "tasks.yaml").read_text(encoding="utf-8"))
    assert raw["tasks"][TASK_ID]["status"] == "TASK_STATE_COMPLETED"
    assert done["status"] == herdr_lease.STATE_COMPLETED
    reread = herdr_lease.get_task(TASK_ID, base_dir=tmp_path)
    assert herdr_lease.status_of(reread) == herdr_lease.STATE_COMPLETED


LEGACY_STORE = """\
active_leases: {}
tasks:
  "#182#old":
    ticket_id: "#182"
    task_id: "#182#old"
    ticket_path: 182.md
    task_group: harness
    status: completed
    assignee: callee
    caller: orchestrator
    trajectory:
    - seq: 1
      event: dispatched
      from_status: dispatched
      to_status: dispatched
    - seq: 2
      event: completed
      from_status: dispatched
      to_status: completed
  "#182#open":
    ticket_id: "#182"
    task_id: "#182#open"
    ticket_path: 182.md
    status: in_progress
    assignee: worker
    caller: orchestrator
    trajectory:
    - seq: 1
      event: dispatched
      from_status: unassigned
      to_status: dispatched
"""


def test_a_record_from_a_pre_cutover_worktree_still_reads(tmp_path: Path) -> None:
    """The alias table is the shared-store regression guard, and reads migrate nothing.

    The store below is written BY HAND in exactly the shape another worktree's older code
    writes it: `status: completed`, `status: in_progress`, trajectory endpoints spelled the old
    way. Deleting `STATUS_ALIASES` makes every one of those read as NO state, so this fails on
    that mutant — which is the regression the live `.lane/tasks.yaml` would otherwise suffer in
    silence, since worktrees cannot be upgraded in lockstep.
    """
    lane = tmp_path / ".lane"
    lane.mkdir()
    store = lane / "tasks.yaml"
    _ = store.write_text(LEGACY_STORE, encoding="utf-8")
    before = store.read_bytes()

    done = herdr_lease.get_task("#182#old", base_dir=tmp_path)
    working = herdr_lease.get_task("#182#open", base_dir=tmp_path)
    assert herdr_lease.status_of(done) == herdr_lease.STATE_COMPLETED
    assert herdr_lease.status_of(working) == herdr_lease.STATE_WORKING
    assert store.read_bytes() == before, "a read must not rewrite a historical record"

    # A write advances the one record it was asked to, canonically, and leaves the other row's
    # historical spelling exactly as it found it: no background migration, ever.
    moved = herdr_lease.transition("#182#open", herdr_lease.STATE_INPUT_REQUIRED, base_dir=tmp_path)
    assert moved["status"] == "TASK_STATE_INPUT_REQUIRED"
    after = yaml.safe_load(store.read_text(encoding="utf-8"))
    assert after["tasks"]["#182#open"]["status"] == "TASK_STATE_INPUT_REQUIRED"
    assert after["tasks"]["#182#old"]["status"] == "completed"


@pytest.mark.parametrize("token", herdr_lease.HISTORICAL_STATUSES)
def test_every_historical_token_names_a_defined_state(token: str) -> None:
    """The alias table is total: each token the live store holds maps onto exactly one state.

    Pin -> mutant: a table that drops a spelling (the token then reads as unknown) or maps one
    onto a name that is not a state.
    """
    canonical = herdr_lease.STATUS_ALIASES[token]
    assert canonical in herdr_lease.CANONICAL_STATUSES, token
    assert herdr_lease.normalize_status(token) == canonical, token
    assert herdr_lease.status_of({"status": token}) == canonical, token
    # An alias is stable: reading the name it points at answers the same name.
    assert herdr_lease.normalize_status(canonical) == canonical, token


def test_the_alias_table_covers_exactly_the_vocabularies_it_documents() -> None:
    """Domain and range are the two documented spellings, and every state is reachable."""
    assert set(herdr_lease.STATUS_ALIASES) == set(herdr_lease.CANONICAL_STATUSES) | set(
        herdr_lease.HISTORICAL_STATUSES
    )
    assert set(herdr_lease.STATUS_ALIASES.values()) == set(herdr_lease.CANONICAL_STATUSES)
    # The table is a read aid, not a write vocabulary: it never hands out a historical name.
    for canonical in herdr_lease.CANONICAL_STATUSES:
        assert canonical not in herdr_lease.HISTORICAL_STATUSES, canonical


@pytest.mark.parametrize(
    "unknown",
    ["", " unknown", "Completed", "task_state_completed", "TASK_STATE_DONE", None, 7, True],
)
def test_a_status_that_names_no_state_reads_as_no_state(unknown: object) -> None:
    """Totality has a second half: an unreadable spelling is never quietly a valid one."""
    assert herdr_lease.normalize_status(unknown) is None
    assert herdr_lease.status_of({"status": unknown}) is None
    assert herdr_lease.status_of(None) is None


def test_transition_refuses_a_status_that_names_no_state(tmp_path: Path) -> None:
    """The refusal is a usage error, not a silent write of the caller's own word."""
    _ = herdr_lease.acquire_lease(
        "callee", "182.md", "orch", base_dir=tmp_path, ticket_id="#182", task_id=TASK_ID
    )

    with pytest.raises(herdr_lease.UsageError):
        _ = herdr_lease.transition(TASK_ID, "prancing", base_dir=tmp_path)

    task = herdr_lease.get_task(TASK_ID, base_dir=tmp_path)
    assert task is not None and task["status"] == herdr_lease.STATE_SUBMITTED


def test_record_event_refuses_a_status_that_names_no_state(tmp_path: Path) -> None:
    """Both write entry points refuse an unknown token alike (#182 t3b P3): `record_event`
    persists no caller word `transition` would reject. The raise is the same `UsageError` the
    reply call site already wraps, so lease bookkeeping stays one stderr skip line — never an
    exit status (pinned at the reply seam by the best-effort suite in test_herdr_reply.py).

    Pin -> mutant: let `record_event` write `"prancing"` verbatim, and this row carries a
    status no reader can name while the refusal never fires.
    """
    _ = herdr_lease.acquire_lease(
        "callee", "182.md", "orch", base_dir=tmp_path, ticket_id="#182", task_id=TASK_ID
    )

    with pytest.raises(herdr_lease.UsageError):
        _ = herdr_lease.record_event(TASK_ID, "prancing", base_dir=tmp_path)

    task = herdr_lease.get_task(TASK_ID, base_dir=tmp_path)
    assert task is not None and task["status"] == herdr_lease.STATE_SUBMITTED
    assert [entry["event"] for entry in task["trajectory"]] == ["dispatched"]


def test_runtime_identity_survives_a_write_read_round_trip(tmp_path: Path) -> None:
    """Section A: the anchors ride on BOTH records and come back byte-identical.

    Pin -> mutant: identity written on the lease only, or a read that re-derives it from the
    live fleet instead of the durable row.
    """
    lease = herdr_lease.acquire_lease(
        "callee",
        "182.md",
        "orchestrator",
        pane_id="w9:p3",
        base_dir=tmp_path,
        ticket_id="#182",
        task_id=TASK_ID,
        task_group="harness",
        tab_id="w9:t1",
        context_id="01J4X9K7-session",
    )

    reread = herdr_lease.get_lease("callee", base_dir=tmp_path)
    task = herdr_lease.get_task(TASK_ID, base_dir=tmp_path)
    assert reread == lease
    assert task is not None

    for record in (lease, reread, task):
        assert record["pane_id"] == "w9:p3"
        assert record["tab_id"] == "w9:t1"
        assert record["context_id"] == "01J4X9K7-session"
        assert record["task_group"] == "harness"

    raw = yaml.safe_load((tmp_path / ".lane" / "tasks.yaml").read_text(encoding="utf-8"))
    assert raw["tasks"][TASK_ID]["context_id"] == "01J4X9K7-session"
    assert raw["active_leases"]["callee"]["tab_id"] == "w9:t1"


def test_an_unobserved_anchor_is_omitted_never_guessed(tmp_path: Path) -> None:
    """Section C's posture at the store seam: identity nobody observed is written as absent.

    The slug joins the anchored ids: the row omits `task_group` entirely rather than holding a
    null that a later guarded re-dispatch could not tell apart from never-recorded evidence
    (#182 t3b P2 — absence, not null, is what "not observed" writes).
    """
    lease = herdr_lease.acquire_lease(
        "callee", "182.md", "orch", base_dir=tmp_path, ticket_id="#182", task_id=TASK_ID
    )

    task = herdr_lease.get_task(TASK_ID, base_dir=tmp_path)
    assert task is not None
    for record in (lease, task):
        for key in ("pane_id", "tab_id", "context_id", "task_group"):
            assert key not in record, f"{key} in {record}"


def test_the_store_and_the_envelope_spell_shared_states_identically() -> None:
    """One A2A vocabulary, written by two modules that must not drift apart.

    The store deliberately does not import `herdr_envelope` (a lane must stay readable without
    the wire layer), so the four names the two share are spelled twice. This pin is what keeps
    the duplication honest: a rename on one side fails here instead of emitting two dialects.
    """
    import herdr_envelope

    for name in (
        "STATE_WORKING",
        "STATE_COMPLETED",
        "STATE_INPUT_REQUIRED",
        "STATE_FAILED",
    ):
        assert getattr(herdr_lease, name) == getattr(herdr_envelope, name), name


def test_new_writes_reach_the_store_only_through_the_resolver(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The ticket's own invariant: never address a store by path, always resolve it.

    A fake per-worktree root is the cwd here, standing in for the stale `.lane/tasks.yaml` a
    worktree leaves behind. Every resolution must land on the anchored lane, the lease must
    record that same anchor, and nothing may be created under the cwd.

    Pin -> mutant: `Path.cwd()`/`PWD`/`__file__`-relative store path in any of the new code.
    """
    lane = tmp_path / "lane"
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    monkeypatch.chdir(worktree)

    resolved: list[Path] = []
    real = herdr_lease.resolve_base_dir

    def spy(base_dir: Path | str | None = None, env: Mapping[str, str] | None = None) -> Path:
        root = real(base_dir, env=env)
        _ = resolved.append(root)
        return root

    _ = monkeypatch.setattr(herdr_lease, "resolve_base_dir", spy)
    env = {"HERDR_LANE_DIR": str(lane), "PWD": str(worktree)}

    lease = herdr_lease.acquire_lease(
        "callee",
        "182.md",
        "orchestrator",
        pane_id="w9:p3",
        env=env,
        ticket_id="#182",
        task_id=TASK_ID,
        task_group="harness",
        tab_id="w9:t1",
        context_id="01J4X9K7-session",
    )
    _ = herdr_lease.transition(TASK_ID, "in_progress", env=env)
    _ = herdr_lease.record_event(TASK_ID, "completed", env=env)
    _ = herdr_lease.get_task(TASK_ID, env=env)
    _ = herdr_lease.get_lease("callee", env=env)
    assert herdr_lease.release_lease("callee", env=env) is True

    assert resolved, "not one store access went through the resolver"
    assert set(resolved) == {lane.resolve()}, resolved
    assert lease["store"] == str(lane.resolve())
    assert (lane / ".lane" / "tasks.yaml").is_file()
    assert not (worktree / ".lane").exists(), "a per-worktree store was created"
    assert not (worktree / ".herdr-lease.json").exists()


def test_write_state_uses_the_shared_atomic_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import herdr_cli

    calls: list[tuple[Path, dict[str, Any]]] = []

    def fake(path: Path, data: Mapping[str, Any], **_kwargs: object) -> None:
        calls.append((path, dict(data)))

    monkeypatch.setattr(herdr_cli, "atomic_write_yaml", fake)

    herdr_lease._write_state({"active_leases": {"callee": {}}}, base_dir=tmp_path)

    assert calls
    assert calls[0][1] == {"active_leases": {"callee": {}}}


# ── #369: one writer at a time — the tasks store is a shared live database ────────────
#
# `.lane/tasks.yaml` is a whole-file read-modify-write: load the mapping, mutate one row,
# `os.replace` the whole document back. Two writers that overlap lose one of the two
# mutations silently, and a lost lease reads as a free worker. Every case below fails on
# the pre-#369 writer, which took no lock: `threading` alone cannot prove it (an `flock`
# belongs to the open file description, so threads in one process share the failure
# mode differently), hence real child processes. Those children are SPAWNED, never forked:
# a fork of this already multi-threaded pytest process would copy `herdr_lease`'s own
# `_path_guards` mutexes and per-thread lock depths into a child that can never release
# them — the hazard Python 3.14 warns about — so every child gets a fresh interpreter and
# the store file is the only thing shared.

PROCESSES = 8
LEASES_PER_WORKER = 5
EVENTS_PER_WORKER = 8
START_TIMEOUT = 30.0


class _Signal(Protocol):
    """The `multiprocessing.Event` surface the worker processes synchronize on."""

    def set(self) -> None: ...

    def wait(self, timeout: float | None = None) -> bool: ...


def _lock_file(base: Path) -> Path:
    """The advisory lock this store takes: the resolved tasks file plus a `.lock` suffix."""
    return herdr_lease.resolve_tasks_file(base_dir=base).with_name("tasks.yaml.lock")


def _lock_is_free(lock_path: Path) -> bool:
    """Whether the exclusive lock can be taken right now, without blocking on it."""
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        return True
    finally:
        os.close(descriptor)


def _start_all(target: Callable[..., None], args_list: Sequence[tuple[object, ...]]) -> None:
    """Start one spawned process per argument tuple, release them together, demand clean exits.

    `spawn` pickles `target` by module and qualified name, so every target here is a
    module-level function taking plain `str`/`int` arguments plus `Event`s the parent drew
    from this same context.
    """
    context = multiprocessing.get_context("spawn")
    start = context.Event()
    processes = [context.Process(target=target, args=(*args, start)) for args in args_list]
    for process in processes:
        process.start()
    start.set()
    for process in processes:
        process.join(timeout=START_TIMEOUT)
    for process in processes:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
    assert [process.exitcode for process in processes] == [0] * len(processes)


def _acquire_many(base: str, worker: int, start: _Signal) -> None:
    """Take `LEASES_PER_WORKER` distinct leases, one read-modify-write of the whole file each."""
    store = Path(base)
    _ = start.wait(timeout=START_TIMEOUT)
    for shard in range(LEASES_PER_WORKER):
        _ = herdr_lease.acquire_lease(
            f"worker-{worker}-{shard}", f"{worker}-{shard}.md", "orchestrator", base_dir=store
        )


def _record_many(base: str, task_id: str, worker: int, start: _Signal) -> None:
    """Append `EVENTS_PER_WORKER` events to one shared task from this process."""
    store = Path(base)
    _ = start.wait(timeout=START_TIMEOUT)
    for shard in range(EVENTS_PER_WORKER):
        _ = herdr_lease.record_event(
            task_id,
            herdr_lease.STATE_WORKING,
            note=f"w{worker}-{shard}",
            actor=f"worker-{worker}",
            base_dir=store,
        )


def test_eight_processes_keep_every_lease_they_acquire(tmp_path: Path) -> None:
    """`PROCESSES x LEASES_PER_WORKER` concurrent acquires leave every distinct key behind.

    Pin -> mutant: drop the lock from `acquire_lease` and the last writer wins the whole
    mapping, so most of the `PROCESSES * LEASES_PER_WORKER` leases vanish — a lost lease
    reads to the dispatcher as a free worker, which is the #369 collision.
    """
    _start_all(_acquire_many, [(str(tmp_path), worker) for worker in range(PROCESSES)])

    leases = herdr_lease.list_active_leases(base_dir=tmp_path)
    expected = {
        f"worker-{worker}-{shard}"
        for worker in range(PROCESSES)
        for shard in range(LEASES_PER_WORKER)
    }
    assert {lease["target"] for lease in leases} == expected
    assert len(leases) == PROCESSES * LEASES_PER_WORKER
    stored = yaml.safe_load((tmp_path / ".lane" / "tasks.yaml").read_text(encoding="utf-8"))
    assert set(stored["active_leases"]) == expected


def test_eight_processes_append_every_event_to_one_task(tmp_path: Path) -> None:
    """`PROCESSES x EVENTS_PER_WORKER` concurrent appends keep every event and every `seq`.

    The trajectory is the append that loses updates most visibly: two writers that loaded
    the same list both write `seq: 2`, so a lost update duplicates a sequence number as
    well as dropping a note.
    """
    task_id = "#369#lost-update"
    _ = herdr_lease.acquire_lease(
        "worker", "369.md", "orchestrator", base_dir=tmp_path, ticket_id="#369", task_id=task_id
    )

    _start_all(
        _record_many,
        [(str(tmp_path), task_id, worker) for worker in range(PROCESSES)],
    )

    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    trajectory = task["trajectory"]
    assert [event["seq"] for event in trajectory] == list(
        range(1, PROCESSES * EVENTS_PER_WORKER + 2)
    )
    assert {event["note"] for event in trajectory[1:]} == {
        f"w{worker}-{shard}" for worker in range(PROCESSES) for shard in range(EVENTS_PER_WORKER)
    }
    assert herdr_lease.status_of(task) == herdr_lease.STATE_WORKING


def _raise_inside_the_lock(
    base: str,
    held: _Signal,
    raise_now: _Signal,
    reacquired: _Signal,
    done: _Signal,
    finish: _Signal,
) -> None:
    """Take the lock, raise inside the block, then take it again in this same process."""
    store = Path(base)
    try:
        with herdr_lease.locked_tasks_state(base_dir=store):
            held.set()
            _ = raise_now.wait(timeout=START_TIMEOUT)
            raise RuntimeError("the block raised while holding the lock")
    except RuntimeError:
        # Swallowed on purpose: the raise IS the event under test, and the lock must survive it.
        pass
    with herdr_lease.locked_tasks_state(base_dir=store):
        reacquired.set()
    done.set()
    _ = finish.wait(timeout=START_TIMEOUT)


def test_the_lock_is_released_when_the_block_raises(tmp_path: Path) -> None:
    """An exception inside the `with` block releases the lock, so the next writer proceeds.

    Pin -> mutant: a lock taken without a `finally` (or a depth counter that is not
    decremented on the error path) leaves the file locked after the raise, and every
    later writer of this store blocks forever.
    """
    context = multiprocessing.get_context("spawn")
    held, raise_now, reacquired, done, finish = (context.Event() for _ in range(5))
    child = context.Process(
        target=_raise_inside_the_lock,
        args=(str(tmp_path), held, raise_now, reacquired, done, finish),
    )
    child.start()
    lock_path = _lock_file(tmp_path)
    try:
        assert held.wait(timeout=START_TIMEOUT), "the child never took the lock"
        assert not _lock_is_free(lock_path), "the lock was free while another process held it"
        raise_now.set()
        assert reacquired.wait(timeout=START_TIMEOUT), (
            "the lock stayed taken after the exception unwound the with block"
        )
        assert done.wait(timeout=START_TIMEOUT)
        assert _lock_is_free(lock_path), "the lock stayed taken after the with block exited"
    finally:
        finish.set()
        child.join(timeout=START_TIMEOUT)
        if child.is_alive():
            child.terminate()
            child.join(timeout=5)
    assert child.exitcode == 0


def _hold_the_lock(base: str, held: _Signal, finish: _Signal) -> None:
    """Hold the writer lock until the parent says the reads are done."""
    with herdr_lease.locked_tasks_state(base_dir=Path(base)):
        held.set()
        _ = finish.wait(timeout=START_TIMEOUT)


def test_readers_do_not_block_behind_a_writer_lock(tmp_path: Path) -> None:
    """`get_lease` and `list_active_leases` complete while another process holds the lock.

    Reads are lock-free by design: they are pure snapshots of an atomically replaced file,
    so a held writer must never make the dispatcher wait. Pin -> mutant: take the lock on a
    read path and this reader never returns.
    """
    lease = herdr_lease.acquire_lease("callee", "369.md", "orchestrator", base_dir=tmp_path)

    context = multiprocessing.get_context("spawn")
    held, finish = context.Event(), context.Event()
    holder = context.Process(target=_hold_the_lock, args=(str(tmp_path), held, finish))
    holder.start()
    results: list[tuple[dict[str, Any] | None, int]] = []

    def read_while_written() -> None:
        found = herdr_lease.get_lease("callee", base_dir=tmp_path)
        results.append((found, len(herdr_lease.list_active_leases(base_dir=tmp_path))))

    reader = threading.Thread(target=read_while_written, daemon=True)
    started = time.monotonic()
    try:
        assert held.wait(timeout=START_TIMEOUT), "the holder never took the lock"
        # The bound measures the read, not the child's boot: spawn imports this module before
        # the holder can take the lock, and counting that would time interpreter startup.
        started = time.monotonic()
        reader.start()
        reader.join(timeout=2.0)
    finally:
        elapsed = time.monotonic() - started
        finish.set()
        holder.join(timeout=START_TIMEOUT)
        if holder.is_alive():
            holder.terminate()
            holder.join(timeout=5)

    assert not reader.is_alive(), "a reader blocked behind the writer's lock"
    assert elapsed < 1.0, f"the read took {elapsed:.3f}s behind a held lock"
    assert results == [(lease, 1)]
    assert holder.exitcode == 0


def test_the_lock_is_reentrant_for_nested_writes(tmp_path: Path) -> None:
    """A nested `locked_tasks_state` and a nested write in one thread do not self-deadlock.

    `transition` holds the lock to resolve its target and then calls `record_event`, which
    locks the same store again. An `flock` is held per open file description, so a second
    descriptor would block on itself: the depth guard is what makes the nesting work.
    """
    task_id = "#369#nested"
    _ = herdr_lease.acquire_lease(
        "worker", "369.md", "orchestrator", base_dir=tmp_path, ticket_id="#369", task_id=task_id
    )
    tasks_file = herdr_lease.resolve_tasks_file(base_dir=tmp_path)
    seen: list[Path] = []
    moved: list[dict[str, Any]] = []

    def nested_work() -> None:
        with herdr_lease.locked_tasks_state(base_dir=tmp_path) as held:
            seen.append(held)
            with herdr_lease.locked_tasks_state(base_dir=tmp_path) as held_again:
                seen.append(held_again)
            moved.append(
                herdr_lease.transition(task_id, herdr_lease.STATE_WORKING, base_dir=tmp_path)
            )

    worker = threading.Thread(target=nested_work, daemon=True)
    worker.start()
    worker.join(timeout=5.0)

    assert not worker.is_alive(), "nested locked_tasks_state self-deadlocked"
    assert seen == [tasks_file, tasks_file]
    assert [task["status"] for task in moved] == [herdr_lease.STATE_WORKING]
    assert herdr_lease.get_task(task_id, base_dir=tmp_path) == moved[0]


def test_the_lock_file_sits_beside_the_tasks_file(tmp_path: Path) -> None:
    """The lock is `<base>/.lane/tasks.yaml.lock`, the write target plus a `.lock` suffix."""
    with herdr_lease.locked_tasks_state(base_dir=tmp_path) as tasks_file:
        assert tasks_file == tmp_path / ".lane" / "tasks.yaml"
        assert (tmp_path / ".lane" / "tasks.yaml.lock").is_file()
        assert not tasks_file.exists(), "taking the lock must not create the store itself"
