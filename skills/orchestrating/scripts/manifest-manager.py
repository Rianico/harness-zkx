#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def get_file_hash(path: str) -> str:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "missing"


def get_utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _build_artifacts(artifact_paths: list[str]) -> list[dict]:
    return [{"path": p, "hash": get_file_hash(p)} for p in artifact_paths]


def _require_args(args: list[str], count: int, label: str) -> None:
    if len(args) < count:
        print(f"Error: '{label}' requires at least {count} arguments, got {len(args)}")
        sys.exit(1)


def main():
    if len(sys.argv) < 3:
        print("Usage: manifest-manager.py <manifest_path> <command> [args...]")
        sys.exit(1)

    manifest_path = Path(sys.argv[1])
    command = sys.argv[2]
    args = sys.argv[3:]

    manifest = {
        "mission_id": "",
        "status": "in_progress",
        "intent_hash": "",
        "artifacts": [],
        "phases": [],
    }
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())

    if command == "init":
        _require_args(args, 2, "init")
        manifest["mission_id"] = args[0]
        manifest["intent_hash"] = get_file_hash(args[1])
        manifest["artifacts"] = _build_artifacts([args[1]])

    elif command == "get-next-run":
        _require_args(args, 1, "get-next-run")
        phase_id = args[0]
        runs = [
            int(p["run_id"].split("-")[1]) for p in manifest["phases"] if p["phase_id"] == phase_id
        ]
        next_run = max(runs, default=0) + 1
        print(f"run-{next_run}")
        return

    elif command == "add-phase":
        _require_args(args, 3, "add-phase")
        phase_id, run_id, status = args[0], args[1], args[2]
        agent_id = args[3] if len(args) > 3 else "orchestrator"
        artifact_paths = args[4:]

        artifacts = _build_artifacts(artifact_paths)
        provenance = {"agent_id": agent_id}

        for p in manifest["phases"]:
            if p["phase_id"] == phase_id and p["run_id"] == run_id:
                p["status"] = status
                if status == "completed" and not p.get("finished_at"):
                    p["finished_at"] = get_utc_now()
                p["artifacts"] = artifacts
                p["provenance"] = provenance
                break
        else:
            now = get_utc_now()
            manifest["phases"].append(
                {
                    "phase_id": phase_id,
                    "run_id": run_id,
                    "status": status,
                    "created_at": now,
                    "finished_at": now if status == "completed" else None,
                    "artifacts": artifacts,
                    "provenance": provenance,
                    "units": [],
                }
            )

    elif command == "add-unit":
        _require_args(args, 4, "add-unit")
        phase_id, run_id, unit_id, status = args[0], args[1], args[2], args[3]
        agent_id = args[4] if len(args) > 4 else "orchestrator"
        artifact_paths = args[5:]

        artifacts = _build_artifacts(artifact_paths)
        provenance = {"agent_id": agent_id}

        phase = next(
            (p for p in manifest["phases"] if p["phase_id"] == phase_id and p["run_id"] == run_id),
            None,
        )
        if not phase:
            now = get_utc_now()
            phase = {
                "phase_id": phase_id,
                "run_id": run_id,
                "status": "in_progress",
                "created_at": now,
                "finished_at": None,
                "artifacts": [],
                "units": [],
                "provenance": None,
            }
            manifest["phases"].append(phase)

        for u in phase["units"]:
            if u["unit_id"] == unit_id:
                u["status"] = status
                if status == "completed" and not u.get("finished_at"):
                    u["finished_at"] = get_utc_now()
                u["artifacts"] = artifacts
                u["provenance"] = provenance
                break
        else:
            now = get_utc_now()
            phase["units"].append(
                {
                    "unit_id": unit_id,
                    "status": status,
                    "created_at": now,
                    "finished_at": now if status == "completed" else None,
                    "artifacts": artifacts,
                    "provenance": provenance,
                }
            )

    elif command == "set-status":
        _require_args(args, 1, "set-status")
        manifest["status"] = args[0]

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Manifest updated: {manifest_path}")


if __name__ == "__main__":
    main()
