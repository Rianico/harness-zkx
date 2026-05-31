#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_file_hash(path: str) -> str:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "missing"


def _build_provenance(agent_id: str, artifact_paths: list[str]) -> dict:
    return {
        "agent_id": agent_id,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "artifacts": [{"path": p, "hash": get_file_hash(p)} for p in artifact_paths],
    }


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

    manifest = {"mission_id": "", "status": "in_progress", "intent_hash": "", "phases": []}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())

    if command == "init":
        _require_args(args, 2, "init")
        manifest["mission_id"] = args[0]
        manifest["intent_hash"] = get_file_hash(args[1])

    elif command == "get-next-run":
        _require_args(args, 1, "get-next-run")
        phase_id = args[0]
        runs = [int(p["run_id"].split("-")[1]) for p in manifest["phases"] if p["phase_id"] == phase_id]
        next_run = max(runs, default=0) + 1
        print(f"run-{next_run}")
        return

    elif command == "add-phase":
        _require_args(args, 3, "add-phase")
        phase_id, run_id, status = args[0], args[1], args[2]
        agent_id = args[3] if len(args) > 3 else "orchestrator"
        artifact_paths = args[4:]

        provenance = _build_provenance(agent_id, artifact_paths)

        for p in manifest["phases"]:
            if p["phase_id"] == phase_id and p["run_id"] == run_id:
                p["status"] = status
                p["provenance"] = provenance
                break
        else:
            manifest["phases"].append({
                "phase_id": phase_id,
                "run_id": run_id,
                "status": status,
                "provenance": provenance,
                "units": [],
            })

    elif command == "add-unit":
        _require_args(args, 4, "add-unit")
        phase_id, run_id, unit_id, status = args[0], args[1], args[2], args[3]
        agent_id = args[4] if len(args) > 4 else "orchestrator"
        artifact_paths = args[5:]

        provenance = _build_provenance(agent_id, artifact_paths)

        phase = next((p for p in manifest["phases"] if p["phase_id"] == phase_id and p["run_id"] == run_id), None)
        if not phase:
            phase = {
                "phase_id": phase_id,
                "run_id": run_id,
                "status": "in_progress",
                "units": [],
                "provenance": None,
            }
            manifest["phases"].append(phase)

        for u in phase["units"]:
            if u["unit_id"] == unit_id:
                u["status"] = status
                u["provenance"] = provenance
                break
        else:
            phase["units"].append({
                "unit_id": unit_id,
                "status": status,
                "provenance": provenance,
            })

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
