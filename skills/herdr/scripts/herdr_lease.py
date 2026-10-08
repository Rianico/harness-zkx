#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = ["pyyaml"]
# ///
"""herdr-lease — task lease and trajectory helper for Herdr multi-agent lanes.

State lives in `.lane/tasks.yaml`: an `active_leases` map of mutual-exclusion locks
(keyed by worker target) and a `tasks` map of durable, append-only task trajectories.
Reads fall back to legacy `.lane/lease.yaml`, `.lane/lease.json`, and `.herdr-lease.json`
so older lanes never break during rollout.

    herdr-lease show [--yaml|--json] [--limit N]
    herdr-lease transition <target|task-id> <status> [--note TEXT] [--actor NAME]

Local addition to the absorbed upstream Herdr skill; not part of `herdrdev/herdr`.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from herdr_cli import UsageError, guard

CANONICAL_STATUSES = ("dispatched", "in_progress", "blocked", "completed", "rework")
STATE_FILE_LANE = ".lane/tasks.yaml"
STATE_FILE_LEGACY_YAML = ".lane/lease.yaml"
STATE_FILE_LEGACY_JSON = ".lane/lease.json"
STATE_FILE_CWD = ".herdr-lease.json"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def resolve_base_dir(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    if base_dir is not None:
        return Path(base_dir)
    env_map = os.environ if env is None else env
    env_dir = env_map.get("HERDR_LANE_DIR") or env_map.get("PWD")
    if env_dir:
        return Path(env_dir)
    return Path.cwd()


def resolve_tasks_file(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """The write target: always `<base>/.lane/tasks.yaml`."""
    return resolve_base_dir(base_dir, env=env) / STATE_FILE_LANE


def resolve_state_read_path(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """The first existing state file, newest schema first, else the write target."""
    base = resolve_base_dir(base_dir, env=env)
    for relative in (
        STATE_FILE_LANE,
        STATE_FILE_LEGACY_YAML,
        STATE_FILE_LEGACY_JSON,
        STATE_FILE_CWD,
    ):
        candidate = base / relative
        if candidate.is_file():
            return candidate
    return resolve_tasks_file(base, env=env)


def resolve_lease_file(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Back-compat alias: the path a lease add/remove should read from."""
    return resolve_state_read_path(base_dir, env=env)


def _empty_state() -> dict[str, Any]:
    return {"active_leases": {}, "tasks": {}}


def _load_state(path: Path) -> dict[str, Any]:
    """Read state from `path`; a missing or corrupt file yields empty state, never a raise."""
    if not path.is_file():
        return _empty_state()
    try:
        raw = path.read_text(encoding="utf-8")
        data: Any = json.loads(raw) if path.suffix == ".json" else yaml.safe_load(raw)
    except Exception:
        return _empty_state()
    if not isinstance(data, dict):
        return _empty_state()

    if "active_leases" in data:
        active = data.get("active_leases")
        tasks = data.get("tasks")
        active_leases = (
            {str(k): v for k, v in active.items() if isinstance(v, dict)}
            if isinstance(active, dict)
            else {}
        )
        tasks_map = (
            {str(k): v for k, v in tasks.items() if isinstance(v, dict)}
            if isinstance(tasks, dict)
            else {}
        )
        return {"active_leases": active_leases, "tasks": tasks_map}

    # Legacy flat mapping {target: lease}; there are no task records yet.
    active_leases = {}
    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        lease = dict(value)
        _ = lease.setdefault("target", str(key))
        timestamp = lease.get("timestamp") or _now_iso()
        lease["timestamp"] = timestamp
        lease["acquired_at"] = timestamp
        active_leases[str(key)] = lease
    return {"active_leases": active_leases, "tasks": {}}


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.tmp-")
    try:
        with open(fd, "wb") as f:
            _ = f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _write_state(
    state: dict[str, Any],
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> None:
    """Persist `state` to the canonical tasks file, atomically."""
    payload = yaml.safe_dump(
        state, sort_keys=False, allow_unicode=True, default_flow_style=False
    ).encode("utf-8")
    _atomic_write(resolve_tasks_file(base_dir, env=env), payload)


def get_lease(
    target: str,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any] | None:
    """Return the active lease dict for target if present, else None.

    Matches target against the lease key, the stored 'target' name, or 'pane_id'.
    """
    leases = _load_state(resolve_state_read_path(base_dir, env=env))["active_leases"]
    if target in leases:
        return leases[target]
    for lease in leases.values():
        if lease.get("target") == target or lease.get("pane_id") == target:
            return lease
    return None


def is_leased(
    target: str,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> bool:
    """Check if target has an active lease."""
    return get_lease(target, base_dir=base_dir, env=env) is not None


def acquire_lease(
    target: str,
    ticket_path: str,
    caller: str,
    pane_id: str | None = None,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    ticket_id: str | None = None,
    task_id: str | None = None,
    task_group: str | None = None,
    role: str | None = None,
    caller_recovery: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Record an active ticket lease for target, storing target and pane_id.

    Any other active lease for the same target or pane_id is dropped first. When
    ticket_id/task_id are omitted, the stored lease shape is unchanged; when task_id
    is given, a task record is created or updated and a `dispatched` event appended.
    A truthy `caller_recovery` mapping is stored on the task (empty fields omitted,
    never fabricated) and replaces any prior mapping for the same task.
    """
    state = _load_state(resolve_state_read_path(base_dir, env=env))
    leases = state["active_leases"]

    keys_to_remove = [
        key
        for key, value in leases.items()
        if key != target
        and (
            value.get("target") == target
            or (pane_id is not None and value.get("pane_id") == pane_id)
        )
    ]
    for key in keys_to_remove:
        del leases[key]

    now = _now_iso()
    lease: dict[str, Any] = {
        "target": target,
        "ticket": ticket_path,
        "caller": caller,
        "timestamp": now,
        "acquired_at": now,
    }
    if pane_id:
        lease["pane_id"] = pane_id
    if ticket_id is not None:
        lease["ticket_id"] = ticket_id
    if task_id is not None:
        lease["task_id"] = task_id
    leases[target] = lease

    if task_id is not None:
        tasks = state["tasks"]
        task = tasks.get(task_id)
        previous_status = task.get("status") if isinstance(task, dict) else None
        if not isinstance(task, dict):
            task = {}
            tasks[task_id] = task
        task["ticket_id"] = ticket_id
        task["task_id"] = task_id
        task["ticket_path"] = ticket_path
        task["task_group"] = task_group
        task["status"] = "dispatched"
        task["assignee"] = target
        task["caller"] = caller
        if caller_recovery is not None:
            filtered = {key: value for key, value in dict(caller_recovery).items() if value}
            if filtered:
                task["caller_recovery"] = filtered
        trajectory = task.get("trajectory")
        if not isinstance(trajectory, list):
            trajectory = []
            task["trajectory"] = trajectory
        trajectory.append(
            {
                "seq": len(trajectory) + 1,
                "timestamp": now,
                "event": "dispatched",
                "actor": caller,
                "role": role or caller,
                "from_status": previous_status or "unassigned",
                "to_status": "dispatched",
                "note": "Dispatched ticket via herdr-dispatch",
            }
        )

    _write_state(state, base_dir=base_dir, env=env)
    return lease


def release_lease(
    target: str,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> bool:
    """Clear active lease for target (matching key, target name, or pane_id).

    Soft completion: task records and trajectories are never touched. Returns True
    if a lease was released, False if none matched.
    """
    state = _load_state(resolve_state_read_path(base_dir, env=env))
    leases = state["active_leases"]
    keys_to_delete = [
        key
        for key, lease in leases.items()
        if key == target or lease.get("target") == target or lease.get("pane_id") == target
    ]
    if not keys_to_delete:
        return False
    for key in keys_to_delete:
        del leases[key]
    _write_state(state, base_dir=base_dir, env=env)
    return True


def get_task(
    task_id: str,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any] | None:
    """Return the task record for task_id if present, else None."""
    task = _load_state(resolve_state_read_path(base_dir, env=env))["tasks"].get(task_id)
    return task if isinstance(task, dict) else None


def list_active_leases(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Every active lease, in stored order."""
    return list(_load_state(resolve_state_read_path(base_dir, env=env))["active_leases"].values())


def list_tasks(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Every task record, in stored order."""
    return list(_load_state(resolve_state_read_path(base_dir, env=env))["tasks"].values())


def record_event(
    task_id: str,
    to_status: str,
    *,
    note: str | None = None,
    sha: str | None = None,
    actor: str | None = None,
    role: str | None = None,
    event: str | None = None,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any] | None:
    """Append a trajectory event and advance the task status; None if no such task."""
    state = _load_state(resolve_state_read_path(base_dir, env=env))
    task = state["tasks"].get(task_id)
    if not isinstance(task, dict):
        return None

    trajectory = task.get("trajectory")
    if not isinstance(trajectory, list):
        trajectory = []
        task["trajectory"] = trajectory

    from_status = task.get("status")
    entry: dict[str, Any] = {
        "seq": len(trajectory) + 1,
        "timestamp": _now_iso(),
        "event": event or to_status,
        "actor": actor,
        "role": role or actor,
        "from_status": from_status,
        "to_status": to_status,
    }
    if note is not None:
        entry["note"] = note
    if sha is not None:
        entry["sha"] = sha
    trajectory.append(entry)
    task["status"] = to_status

    _write_state(state, base_dir=base_dir, env=env)
    return task


def transition(
    target_or_task_id: str,
    status: str,
    *,
    note: str | None = None,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
    actor: str | None = None,
    role: str | None = None,
) -> dict[str, Any]:
    """Move a task to `status`, resolving a task id or an active-lease target first."""
    if status not in CANONICAL_STATUSES:
        raise UsageError(
            f"unknown status {status!r}; expected one of {', '.join(CANONICAL_STATUSES)}"
        )

    state = _load_state(resolve_state_read_path(base_dir, env=env))
    tasks = state["tasks"]

    task_id: str | None = None
    if target_or_task_id in tasks:
        task_id = target_or_task_id
    else:
        leases = state["active_leases"]
        lease = leases.get(target_or_task_id)
        if not isinstance(lease, dict):
            lease = next(
                (
                    candidate
                    for candidate in leases.values()
                    if candidate.get("target") == target_or_task_id
                    or candidate.get("task_id") == target_or_task_id
                ),
                None,
            )
        if isinstance(lease, dict):
            resolved = lease.get("task_id")
            if isinstance(resolved, str):
                task_id = resolved

    if task_id is None:
        raise UsageError(f"no task found for {target_or_task_id!r}")

    task = record_event(
        task_id,
        status,
        note=note,
        actor=actor,
        role=role,
        base_dir=base_dir,
        env=env,
    )
    if task is None:
        raise UsageError(f"no task found for {target_or_task_id!r}")
    return task


@dataclass
class Options:
    """CLI options; `argparse` writes into this typed namespace."""

    command: str = ""
    yaml: bool = False
    json: bool = False
    limit: int = 20
    target: str = ""
    status: str = ""
    note: str | None = None
    actor: str | None = None
    role: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-lease",
        description="Inspect active worker leases and durable task trajectories.",
        epilog="exit status: 0 ok, 2 usage or unknown status/task",
    )
    subparsers = parser.add_subparsers(dest="command")
    show = subparsers.add_parser("show", help="print active leases and recent tasks")
    output = show.add_mutually_exclusive_group()
    _ = output.add_argument("--yaml", action="store_true", help="print the canonical state as YAML")
    _ = output.add_argument("--json", action="store_true", help="print the canonical state as JSON")
    _ = show.add_argument(
        "--limit", type=int, default=20, metavar="N", help="cap the tasks listed (default 20)"
    )
    change = subparsers.add_parser("transition", help="append a task status transition")
    _ = change.add_argument("target", metavar="TARGET", help="a task id or an active-lease target")
    _ = change.add_argument(
        "status", metavar="STATUS", help="one of: " + ", ".join(CANONICAL_STATUSES)
    )
    _ = change.add_argument("--note", default=None, metavar="TEXT", help="a note on the event")
    _ = change.add_argument("--actor", default=None, metavar="NAME", help="who moved the task")
    _ = change.add_argument("--role", default=None, metavar="NAME", help="the actor's role")
    return parser


def _last_event(task: Mapping[str, Any]) -> dict[str, Any] | None:
    trajectory = task.get("trajectory")
    if isinstance(trajectory, list) and trajectory and isinstance(trajectory[-1], dict):
        return trajectory[-1]
    return None


def _last_event_timestamp(task: Mapping[str, Any]) -> str:
    event = _last_event(task)
    if event is not None:
        timestamp = event.get("timestamp")
        if isinstance(timestamp, str):
            return timestamp
    return ""


def _canonical_state(state: Mapping[str, Any]) -> dict[str, Any]:
    return {"active_leases": state["active_leases"], "tasks": state["tasks"]}


def _print_summary(canonical: Mapping[str, Any], limit: int) -> None:
    leases = canonical["active_leases"]
    if not leases:
        print("no active leases")
    else:
        print(f"active leases: {len(leases)}")
        for key, lease in leases.items():
            target = lease.get("target") or key
            task_id = lease.get("task_id") or "-"
            ticket = lease.get("ticket") or "-"
            caller = lease.get("caller") or "-"
            since = lease.get("acquired_at") or lease.get("timestamp") or "-"
            print(f"  {target}  task={task_id}  ticket={ticket}  caller={caller}  since={since}")

    tasks = list(canonical["tasks"].values())
    if not tasks or limit <= 0:
        return
    ordered = sorted(tasks, key=_last_event_timestamp, reverse=True)[:limit]
    print(f"tasks: {len(ordered)}")
    for task in ordered:
        event = _last_event(task)
        task_id = task.get("task_id") or "-"
        status = task.get("status") or "-"
        assignee = task.get("assignee") or "-"
        label = (event.get("event") if event else None) or "-"
        print(f"  {task_id}  {status}  {assignee}  {label}")


def _show(options: Options, env: Mapping[str, str]) -> int:
    canonical = _canonical_state(_load_state(resolve_state_read_path(env=env)))
    if options.yaml:
        print(yaml.safe_dump(canonical, sort_keys=False), end="")
        return 0
    if options.json:
        print(json.dumps(canonical, indent=2, sort_keys=False))
        return 0
    _print_summary(canonical, options.limit)
    return 0


def _transition(options: Options, env: Mapping[str, str]) -> int:
    task = transition(
        options.target,
        options.status,
        note=options.note,
        actor=options.actor,
        role=options.role,
        env=env,
    )
    last = _last_event(task)
    from_status = last.get("from_status") if last else None
    note = last.get("note") if last else None
    suffix = f" ({note})" if note else ""
    print(f"task {task.get('task_id')}: {from_status} -> {task.get('status')}{suffix}")
    return 0


def run(options: Options, env: Mapping[str, str]) -> int:
    if options.command == "show":
        return _show(options, env)
    if options.command == "transition":
        return _transition(options, env)
    raise UsageError("missing subcommand: expected 'show' or 'transition'")


def main(
    argv: Sequence[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    return guard("herdr-lease", lambda: run(options, env_map))


if __name__ == "__main__":
    raise SystemExit(main())
