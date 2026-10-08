"""Tests for skills/herdr/scripts/herdr_lease.py (task lease helper)."""

from __future__ import annotations

from pathlib import Path

import herdr_lease


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
    assert (lane_dir / ".lane" / "lease.json").is_file()

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
