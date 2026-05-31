#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
import json
import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

def get_file_hash(path: str) -> str:
    if not os.path.exists(path):
        return "missing"
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    if len(sys.argv) < 3:
        print("Usage: manifest-manager.py <manifest_path> <command> [args...]")
        sys.exit(1)

    manifest_path = Path(sys.argv[1])
    command = sys.argv[2]

    manifest = {"mission_id": "", "status": "in_progress", "intent_hash": "", "phases": []}
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

    if command == "init":
        # init <mission_id> <design_doc_path>
        manifest["mission_id"] = sys.argv[3]
        manifest["intent_hash"] = get_file_hash(sys.argv[4])
    
    elif command == "get-next-run":
        # get-next-run <phase_id>
        phase_id = sys.argv[3]
        runs = [int(p["run_id"].split("-")[1]) for p in manifest["phases"] if p["phase_id"] == phase_id]
        next_run = max(runs, default=0) + 1
        print(f"run-{next_run}")
        return

    elif command == "add-phase":
        # add-phase <phase_id> <run_id> <status> [agent_id] [artifact_paths...]
        phase_id = sys.argv[3]
        run_id = sys.argv[4]
        status = sys.argv[5]
        agent_id = sys.argv[6] if len(sys.argv) > 6 else "orchestrator"
        artifact_paths = sys.argv[7:]

        artifacts = [{"path": p, "hash": get_file_hash(p)} for p in artifact_paths]
        provenance = {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "artifacts": artifacts
        }
        
        # In Versioned Run pattern, every add-phase is effectively a new record or updating specific run
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
                "units": []
            })

    elif command == "add-unit":
        # add-unit <phase_id> <run_id> <unit_id> <status> [agent_id] [artifact_paths...]
        phase_id = sys.argv[3]
        run_id = sys.argv[4]
        unit_id = sys.argv[5]
        status = sys.argv[6]
        agent_id = sys.argv[7] if len(sys.argv) > 7 else "orchestrator"
        artifact_paths = sys.argv[8:]

        artifacts = [{"path": p, "hash": get_file_hash(p)} for p in artifact_paths]
        provenance = {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "artifacts": artifacts
        }

        phase = next((p for p in manifest["phases"] if p["phase_id"] == phase_id and p["run_id"] == run_id), None)
        if not phase:
            phase = {
                "phase_id": phase_id,
                "run_id": run_id,
                "status": "in_progress",
                "units": [],
                "provenance": None
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
                "provenance": provenance
            })

    elif command == "set-status":
        # set-status <status>
        manifest["status"] = sys.argv[3]

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

    # Save manifest
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Manifest updated: {manifest_path}")

if __name__ == "__main__":
    main()
