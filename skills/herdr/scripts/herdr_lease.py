#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""herdr-lease — task lease helper for Herdr multi-agent lanes.

Maintains ticket leases in `.lane/lease.json` (or `.herdr-lease.json` in cwd / lane worktree)
to prevent overlapping dispatches to callees with active in-flight tickets.

Local addition to the absorbed upstream Herdr skill; not part of `herdrdev/herdr`.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LEASE_FILE_LANE = ".lane/lease.json"
LEASE_FILE_CWD = ".herdr-lease.json"


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


def resolve_lease_file(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    base = resolve_base_dir(base_dir, env=env)
    lane_file = base / ".lane" / "lease.json"
    cwd_file = base / ".herdr-lease.json"
    if cwd_file.is_file():
        return cwd_file
    if lane_file.is_file():
        return lane_file
    if (base / ".lane").is_dir():
        return lane_file
    return lane_file


def _read_leases(lease_file: Path) -> dict[str, dict[str, Any]]:
    if not lease_file.is_file():
        return {}
    try:
        data = json.loads(lease_file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items() if isinstance(v, dict)}
    except Exception:
        pass
    return {}


def _write_leases(lease_file: Path, leases: dict[str, dict[str, Any]]) -> None:
    lease_file.parent.mkdir(parents=True, exist_ok=True)
    content = (json.dumps(leases, indent=2) + "\n").encode("utf-8")
    fd, tmp_path = tempfile.mkstemp(
        dir=lease_file.parent,
        prefix=f".{lease_file.name}.tmp-",
    )
    try:
        with open(fd, "wb") as f:
            _ = f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, lease_file)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def get_lease(
    target: str,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any] | None:
    """Return active lease dict for target if present, else None.

    Matches target against lease key, stored 'target' name, or 'pane_id'.
    """
    lease_file = resolve_lease_file(base_dir, env=env)
    leases = _read_leases(lease_file)
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
) -> dict[str, Any]:
    """Record an active ticket lease for target with timestamp, storing target and pane_id."""
    lease_file = resolve_lease_file(base_dir, env=env)
    leases = _read_leases(lease_file)

    # Clean up any previous lease for the same target or pane_id under a different key
    keys_to_remove = [
        k
        for k, v in leases.items()
        if k != target
        and (v.get("target") == target or (pane_id is not None and v.get("pane_id") == pane_id))
    ]
    for k in keys_to_remove:
        del leases[k]

    lease: dict[str, Any] = {
        "target": target,
        "ticket": ticket_path,
        "caller": caller,
        "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
    }
    if pane_id:
        lease["pane_id"] = pane_id
    leases[target] = lease
    _write_leases(lease_file, leases)
    return lease


def release_lease(
    target: str,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> bool:
    """Clear active lease for target (matching key, target name, or pane_id).

    Returns True if released, False if not found.
    """
    lease_file = resolve_lease_file(base_dir, env=env)
    leases = _read_leases(lease_file)
    keys_to_delete: list[str] = []
    if target in leases:
        keys_to_delete.append(target)
    for key, lease in leases.items():
        if key not in keys_to_delete:
            if lease.get("target") == target or lease.get("pane_id") == target:
                keys_to_delete.append(key)
    if keys_to_delete:
        for k in keys_to_delete:
            del leases[k]
        _write_leases(lease_file, leases)
        return True
    return False
