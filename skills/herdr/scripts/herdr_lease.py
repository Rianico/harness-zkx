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

The store base is resolved once per lane: an explicit `base_dir`, else `HERDR_LANE_DIR`,
else the repository root that the git common directory sits in — resolved, so reads, writes,
and records agree on one spelling. Store *identity* is still decided physically
(`os.path.samefile`), because resolving collapses symlinks but not case: on a case-insensitive
volume two spellings are one file and two strings (#229). `PWD` and the process cwd are never
anchors: they differ
between a dispatcher and its own callee, which is how a lease came to be released against a
store it was never written to (#229). A lease records the physical store it was written to,
and a release that resolves a different one reports the mismatch on stderr instead of
relocating the write. That diagnostic needs a lease in the resolved store to compare
against; a lease in a store this process never resolves is invisible, and the release is an
honest no-op rather than a write into the store the lease names.

    herdr-lease show [--yaml|--json] [--limit N]
    herdr-lease transition <target|task-id> <status> [--note TEXT] [--actor NAME]
    herdr-lease replies [ID] [--limit N] [--json|--yaml]

Replies are persisted next to the tasks store as metadata only: a body file under
`.lane/replies/<id>.md` plus one index sidecar `.lane/replies/<id>.yaml` that carries the
digest, the payload shape, and the cited artifact *count* — never the body text. The
directory is the index: each record owns one file, written create-only, so concurrent replies
cannot lose each other's row and no lock is needed. A pre-#231 `.lane/replies.yaml` is still
read — merged on read, deduped by id, the sidecar winning — and is never rewritten, so an old
ledger can never be clobbered. `herdr-lease replies` is the reader that re-derives a reply's
evidence, so the orchestrator trusts a store record instead of treating a prompt as
provenance (#231).

Local addition to the absorbed upstream Herdr skill; not part of `herdrdev/herdr`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from herdr_cli import UsageError, add_shared_argument, guard
from herdr_worktree import resolve_lane_base_dir

CANONICAL_STATUSES = ("dispatched", "in_progress", "blocked", "completed", "rework")
STATE_FILE_LANE = ".lane/tasks.yaml"
STATE_FILE_LEGACY_YAML = ".lane/lease.yaml"
STATE_FILE_LEGACY_JSON = ".lane/lease.json"
STATE_FILE_CWD = ".herdr-lease.json"
REPLIES_FILE_LANE = ".lane/replies.yaml"
REPLIES_DIR_LANE = ".lane/replies"
# Bound on regenerating a taken reply id before the record is declared unwritable (#231 F1).
_ID_ATTEMPTS = 16


class ReplyStoreError(UsageError):
    """The reply store cannot serve this call: an unreadable index, or an exhausted id space.

    A `UsageError` so the reader maps it onto the documented exit status 2 instead of
    crashing; the reply path catches it and degrades to `NOT RECORDED` (#231 F2).
    """


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def resolve_base_dir(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """The one lease/task store base for this lane, resolved identically by every caller.

    Layered, and never ambient: an explicit `base_dir` outranks every anchor, then
    `HERDR_LANE_DIR`, then the repository root of this repository's git common directory
    (see `herdr_worktree.resolve_lane_base_dir`). Every worktree and every nested
    subdirectory of one repository therefore resolves to one absolute path. Identity between
    two such paths is decided physically at the comparison site (`os.path.samefile`), since
    resolution alone cannot collapse a case-variant spelling (#229).

    `PWD` and the process cwd are never consulted: a dispatcher in one working directory
    and a callee in another resolved different stores through them, so a lease written by
    one was released — or not — by the other (#229). With neither anchor this raises
    `herdr_worktree.LaneAnchorError` instead of guessing.
    """
    if base_dir is not None:
        return Path(base_dir).resolve()
    env_map = os.environ if env is None else env
    return resolve_lane_base_dir(env_map)


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
    """The first existing state file in the resolved store, newest schema first, else the write target."""
    return _state_read_path_in(resolve_base_dir(base_dir, env=env))


def _state_read_path_in(base: Path) -> Path:
    for relative in (
        STATE_FILE_LANE,
        STATE_FILE_LEGACY_YAML,
        STATE_FILE_LEGACY_JSON,
        STATE_FILE_CWD,
    ):
        candidate = base / relative
        if candidate.is_file():
            return candidate
    return base / STATE_FILE_LANE


def resolve_lease_file(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Back-compat alias: the path a lease add/remove should read from."""
    return resolve_state_read_path(base_dir, env=env)


def resolve_replies_file(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """The reply ledger: `<store base>/.lane/replies.yaml`."""
    return resolve_base_dir(base_dir, env=env) / REPLIES_FILE_LANE


def resolve_replies_dir(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path:
    """The reply body directory: `<store base>/.lane/replies`."""
    return resolve_base_dir(base_dir, env=env) / REPLIES_DIR_LANE


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


def state_is_readable(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> bool:
    """Whether the resolved state file is absent, or present and parseable into a mapping.

    `_load_state` deliberately converts a missing or corrupt file into empty state so every
    reader degrades instead of raising, which leaves a CORRUPT store looking exactly like an
    empty one. A caller that has to say which it is (the reply-linkage warning, #246 D1.4/F3)
    asks here: an absent file is readable-as-empty — there is genuinely nothing to link — while
    a file that exists but does not parse is not readable at all.
    """
    path = resolve_state_read_path(base_dir, env=env)
    if not path.is_file():
        return True
    try:
        raw = path.read_text(encoding="utf-8")
        data: Any = json.loads(raw) if path.suffix == ".json" else yaml.safe_load(raw)
    except Exception:
        return False
    return isinstance(data, dict)


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
    store = resolve_base_dir(base_dir, env=env)
    state = _load_state(_state_read_path_in(store))
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
        "store": str(store),
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

    _write_state(state, base_dir=store)
    return lease


def _same_store(recorded: str, store: Path) -> bool:
    """Whether a recorded spelling names the same physical directory as `store`.

    `os.path.samefile` when both paths exist: on a case-insensitive volume (APFS, the macOS
    default) `MyLaneRepo` and `mylanerepo` are one file and two different strings, so no
    textual comparison — `Path.resolve()` included — can decide this. The resolved-path
    fallback covers a record whose directory has since disappeared, where there is nothing
    left to `stat`.
    """
    try:
        return os.path.samefile(recorded, store)
    except OSError:
        return Path(recorded).resolve() == store.resolve()


def _conflicting_store(recorded: object, store: Path) -> str | None:
    """The recorded spelling when it names another physical store, else `None`.

    An absent, empty, or relative record counts as absent rather than as a mismatch:
    `Path("").resolve()` is the process cwd, so treating a hand-edited or foreign record as
    a spelling would manufacture a refusal out of whichever directory released (#229).
    """
    if not isinstance(recorded, str) or not Path(recorded).is_absolute():
        return None
    return None if _same_store(recorded, store) else recorded


def release_lease(
    target: str,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> bool:
    """Clear active lease for target (matching key, target name, or pane_id).

    Soft completion: task records and trajectories are never touched. Returns True
    if a lease was released, False if none matched.

    A matched lease recording a *different physical store* than this release resolved is
    reported on stderr and left in place — in both stores. Relocating the write would
    fabricate a release the owning store never saw, and a silent one would hide the
    divergence (#229). A spelling difference is not a difference: identity is decided by
    `os.path.samefile` on the two paths, so a symlinked, firmlinked, `/private`-prefixed, or
    case-variant spelling of one directory still releases normally. An absent, empty, or
    relative record is treated as absent, never as a mismatch. A lease with no recorded store
    (legacy schema) is released as before.

    Reach and limits: the diagnostic needs a lease *in the resolved store* to compare
    against. A lease that lives in a store this process never resolves is invisible here,
    and the release is an honest no-op — `False` with empty stderr, never a guessed write
    into the store the lease names.
    """
    store = resolve_base_dir(base_dir, env=env)
    state = _load_state(_state_read_path_in(store))
    leases = state["active_leases"]
    keys_to_delete = [
        key
        for key, lease in leases.items()
        if key == target or lease.get("target") == target or lease.get("pane_id") == target
    ]
    if not keys_to_delete:
        return False
    foreign: set[str] = set()
    for key in keys_to_delete:
        conflicting = _conflicting_store(leases[key].get("store"), store)
        if conflicting is not None:
            foreign.add(conflicting)
    if foreign:
        print(
            f"herdr-lease: lease {target!r} was written to store {', '.join(sorted(foreign))} "
            f"but this release resolved {store}; refusing to relocate the write, nothing released",
            file=sys.stderr,
        )
        return False
    for key in keys_to_delete:
        del leases[key]
    _write_state(state, base_dir=store)
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


def _unlink_quietly(path: Path) -> None:
    """Remove a file this process created; a missing or unremovable file is not an error."""
    try:
        path.unlink()
    except OSError:
        pass


def _preserve_unreadable(path: Path, reason: object) -> str:
    """Move an unreadable index file aside, returning the message for the raised error.

    Byte-for-byte: the file is renamed, never rewritten and never deleted, and a name an
    earlier quarantine already holds is not overwritten (#231 F2). A file that cannot be
    moved is still never rewritten — the message says so instead of guessing.
    """
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    candidate = path.with_name(f"{path.name}.corrupt-{stamp}")
    suffix = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.name}.corrupt-{stamp}-{suffix}")
        suffix += 1
    try:
        _ = path.replace(candidate)
    except OSError as exc:
        return f"reply index {path} is unreadable ({reason}) and could not be moved aside: {exc}"
    return f"reply index {path} is unreadable ({reason}); preserved as {candidate}"


def _parse_index_file(path: Path) -> Any:
    """Parse one index file; a file that cannot be parsed is preserved and raises (#231 F2)."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReplyStoreError(f"reply index {path} could not be read: {exc}") from exc
    try:
        return yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ReplyStoreError(_preserve_unreadable(path, exc)) from exc


def _rows_from_document(document: Any) -> list[dict[str, Any]] | None:
    """The rows a legacy reply ledger holds, or None when its shape is not a ledger."""
    if document is None:
        return []
    if isinstance(document, dict):
        document = document.get("replies")
        if document is None:
            return []
    if not isinstance(document, list) or not all(isinstance(row, dict) for row in document):
        return None
    return [dict(row) for row in document]


def _load_legacy_ledger(path: Path) -> list[dict[str, Any]]:
    """Read-only rows of a pre-#231 ledger; a damaged file is preserved, never written over."""
    if not path.is_file():
        return []
    rows = _rows_from_document(_parse_index_file(path))
    if rows is None:
        raise ReplyStoreError(_preserve_unreadable(path, "the reply list is not a list of records"))
    return rows


def _load_sidecar(path: Path) -> dict[str, Any]:
    """One record's index file; a file that is not one record is damaged, not guessed at."""
    document = _parse_index_file(path)
    if not isinstance(document, dict) or not isinstance(document.get("id"), str):
        raise ReplyStoreError(_preserve_unreadable(path, "not one reply record"))
    return dict(document)


def _reply_sort_key(record: Mapping[str, Any]) -> tuple[str, str]:
    """Newest-last ordering without a lock: `recorded_at`, then `id` as the tiebreaker."""
    return str(record.get("recorded_at") or ""), str(record.get("id") or "")


def _load_replies(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Every stored reply row: the sidecar directory merged with the read-only legacy ledger.

    The directory is the index (#231 F1): each record owns `<replies>/<id>.yaml`, so a read is
    a directory listing with no lock and no read-modify-write to lose. A legacy
    `.lane/replies.yaml` is merged on read — deduped by id, the sidecar winning — and is
    never rewritten, so it can never be clobbered by a reply written here. Rows come back
    sorted by `recorded_at`, then `id`, so `list_replies`'s newest-last tail is stable.

    An index file that cannot be parsed is preserved as `<name>.corrupt-<utc-stamp>` and
    raises `ReplyStoreError`: a reply is either recorded or honestly unrecorded, never a
    silent clobber (#231 F2).
    """
    directory = resolve_replies_dir(base_dir, env=env)
    legacy = _load_legacy_ledger(resolve_replies_file(base_dir, env=env))
    sidecars = (
        [_load_sidecar(path) for path in sorted(directory.glob("*.yaml"))]
        if directory.is_dir()
        else []
    )
    keyed: dict[str, dict[str, Any]] = {}
    unkeyed: list[dict[str, Any]] = []
    for row in (*legacy, *sidecars):
        record_id = row.get("id")
        if isinstance(record_id, str) and record_id:
            keyed[record_id] = row
        else:
            unkeyed.append(row)
    return unkeyed + sorted(keyed.values(), key=_reply_sort_key)


def _write_reply_index(path: Path, record: Mapping[str, Any]) -> None:
    """Create-only index write for one reply record, complete before it is visible (#231 F1).

    The record path funnels every sidecar through here, and the write is create-only: the
    payload is written and `fsync`ed to a temporary file beside the target and then linked
    into place, so `FileExistsError` means another writer already holds that id — the same
    outcome `O_EXCL` gives — and a concurrent reader can only ever see a *complete* index
    file, never the zero-length window an `os.open(O_CREAT|O_EXCL)` plus write exposes (a
    reader that saw it would have to quarantine it as damaged, which is a self-inflicted
    corruption, not a lost update). The payload is `yaml.safe_dump`ed, so the file is one
    record; its mode is `mkstemp`'s `0600`.
    """
    payload = yaml.safe_dump(
        dict(record), sort_keys=False, allow_unicode=True, default_flow_style=False
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.tmp-")
    try:
        with open(descriptor, "wb") as handle:
            _ = handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temp_path, path)
    finally:
        _unlink_quietly(Path(temp_path))


def record_reply(
    entry: Mapping[str, Any],
    body: str,
    *,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Write one reply: the body to `<replies_dir>/<id>.md`, then its index sidecar.

    The directory is the index (#231 F1): one create-only sidecar per record, so two
    concurrent replies cannot lose each other's row — no lock, and no read-modify-write to
    lose. The body is written first; a sidecar write that fails for any reason other than
    losing an id race unlinks the body (F-C3), so a failed record leaves no orphan behind.
    A taken id is regenerated with a numeric suffix (bounded by `_ID_ATTEMPTS`), and the body
    of the record that holds that id is never replaced: an id collision implies the same
    payload digest, so the two bodies are the same bytes.

    The legacy `<store>/.lane/replies.yaml` is only ever read — its rows are merged by
    `list_replies`/`get_reply` — so a reply written here can never clobber it.
    """
    directory = resolve_replies_dir(base_dir, env=env)
    base_id = str(entry["id"])
    for suffix in range(_ID_ATTEMPTS):
        record_id = base_id if suffix == 0 else f"{base_id}-{suffix + 1}"
        sidecar = directory / f"{record_id}.yaml"
        if sidecar.exists():
            continue
        stored = dict(entry)
        stored["id"] = record_id
        stored["payload"] = f"{REPLIES_DIR_LANE}/{record_id}.md"
        body_path = directory / f"{record_id}.md"
        _atomic_write(body_path, body.encode("utf-8"))
        try:
            _write_reply_index(sidecar, stored)
        except FileExistsError:
            # Losing an id race is not a failure: that record's body is byte-identical (the
            # id carries the payload digest), so it is left in place and the next suffix tried.
            continue
        except BaseException:
            _unlink_quietly(body_path)
            raise
        return stored
    raise ReplyStoreError(
        f"reply id {base_id!r} is taken {_ID_ATTEMPTS} times over; no reply record written"
    )


def _payload_path(
    record: Mapping[str, Any],
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> Path | None:
    """Where a row says its body is: relative to the store base, or as written if absolute."""
    payload = record.get("payload")
    if not isinstance(payload, str) or not payload:
        return None
    path = Path(payload)
    return path if path.is_absolute() else resolve_base_dir(base_dir, env=env) / path


def _payload_matches(path: Path, digest: object) -> bool:
    """Whether the body on disk still hashes to the row's recorded digest."""
    if not isinstance(digest, str) or not digest:
        return False
    try:
        raw = path.read_bytes()
    except OSError:
        return False
    return hashlib.sha256(raw).hexdigest() == digest


def get_reply(
    record_id: str,
    *,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any] | None:
    """The reply row for `record_id`, only while its payload still matches its digest (#231).

    The digest is what binds the delivered body to the record, so a row whose payload file is
    missing, unreadable, or no longer hashes to `digest` resolves to `None`: a hand-written
    row and a tampered body are both unreachable. This is the lookup the reader
    (`herdr-lease replies <ID>`) and the advance gate use, so neither can serve a record the
    store does not actually hold.
    """
    for record in _load_replies(base_dir, env=env):
        if record.get("id") != record_id:
            continue
        path = _payload_path(record, base_dir, env)
        if path is None or not _payload_matches(path, record.get("digest")):
            return None
        return record
    return None


def check_reply_store(
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> None:
    """Fail unless every reply index file is readable; raises `ReplyStoreError` (#231 F2).

    The reply path calls this before it writes. An index this process cannot parse must not
    be written over, so the read is the pre-flight: the reply degrades to NOT RECORDED before
    any body or sidecar exists, and the damaged file is preserved (moved aside) by the read
    itself.
    """
    _ = _load_replies(base_dir, env=env)


def discard_reply(
    record_id: str,
    *,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> None:
    """Remove one just-written record's body and sidecar; best-effort, never raises (#231).

    Used when a record cannot be re-resolved through the reader: the delivered pointer then
    says NOT RECORDED, so no index row may name a reply the sender was told is not recorded.
    """
    try:
        directory = resolve_replies_dir(base_dir, env=env)
    except Exception:
        return
    _unlink_quietly(directory / f"{record_id}.md")
    _unlink_quietly(directory / f"{record_id}.yaml")


def list_replies(
    *,
    limit: int = 20,
    base_dir: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> list[dict[str, Any]]:
    """The most recent reply rows in `recorded_at` order; `limit <= 0` lists none."""
    records = _load_replies(base_dir, env=env)
    return records[-limit:] if limit > 0 else []


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
    record_id: str = ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-lease",
        description="Inspect active worker leases and durable task trajectories.",
        epilog="exit status: 0 ok, 2 usage or unknown status/task",
    )
    subparsers = parser.add_subparsers(dest="command")
    show = subparsers.add_parser("show", help="print active leases and recent tasks")
    output = show.add_mutually_exclusive_group()
    add_shared_argument(output, "yaml", help="print the canonical state as YAML")
    add_shared_argument(output, "json", help="print the canonical state as JSON")
    add_shared_argument(show, "limit", help="cap the tasks listed (default 20)")
    change = subparsers.add_parser("transition", help="append a task status transition")
    _ = change.add_argument("target", metavar="TARGET", help="a task id or an active-lease target")
    _ = change.add_argument(
        "status", metavar="STATUS", help="one of: " + ", ".join(CANONICAL_STATUSES)
    )
    _ = change.add_argument("--note", default=None, metavar="TEXT", help="a note on the event")
    _ = change.add_argument("--actor", default=None, metavar="NAME", help="who moved the task")
    add_shared_argument(change, "role", metavar="NAME", help="the actor's role")
    replies = subparsers.add_parser("replies", help="print recorded replies from the store")
    _ = replies.add_argument(
        "record_id",
        nargs="?",
        default="",
        metavar="ID",
        help="one reply record id; omit to list the most recent replies",
    )
    reply_output = replies.add_mutually_exclusive_group()
    add_shared_argument(reply_output, "yaml", help="print the reply records as YAML")
    add_shared_argument(reply_output, "json", help="print the reply records as JSON")
    add_shared_argument(replies, "limit", help="cap the replies listed (default 20)")
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


def _print_replies(records: Sequence[Mapping[str, Any]]) -> None:
    """One compact block per record; `-` stands in for an absent field."""
    if not records:
        print("no reply records")
        return
    for record in records:
        sender = record.get("sender") or "-"
        caller = record.get("caller") or "-"
        print(f"{record.get('id') or '-'}  {record.get('recorded_at') or '-'}")
        print(f"  sender -> caller: {sender} -> {caller}")
        print(
            f"  status: {record.get('status') or '-'}  "
            f"shape: {record.get('shape') or '-'}  "
            f"evidence: {record.get('evidence') or '-'}"
        )
        print(f"  sha: {record.get('sha') or '-'}")
        print(f"  digest: {record.get('digest') or '-'}")
        print(f"  payload: {record.get('payload') or '-'}")


def _replies(options: Options, env: Mapping[str, str]) -> int:
    """Print one recorded reply by id, or the most recent replies."""
    if options.record_id:
        record = get_reply(options.record_id, env=env)
        if record is None:
            raise UsageError(f"no reply record {options.record_id!r} in the store")
        records = [record]
    else:
        records = list_replies(limit=options.limit, env=env)

    if options.yaml:
        print(yaml.safe_dump({"replies": records}, sort_keys=False), end="")
        return 0
    if options.json:
        print(json.dumps(records, indent=2, sort_keys=False))
        return 0
    _print_replies(records)
    return 0


def run(options: Options, env: Mapping[str, str]) -> int:
    if options.command == "show":
        return _show(options, env)
    if options.command == "transition":
        return _transition(options, env)
    if options.command == "replies":
        return _replies(options, env)
    raise UsageError("missing subcommand: expected 'show', 'transition', or 'replies'")


def main(
    argv: Sequence[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    return guard("herdr-lease", lambda: run(options, env_map))


if __name__ == "__main__":
    raise SystemExit(main())
