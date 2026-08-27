#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "pydantic", "pandas"]
# ///
"""
Analyze command for continuous learning system.

Triggers immediate observation analysis.

Eval 5.2: analyze Command
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports
_project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_project_root))

from hooks.observe.agent_runner import AgentRunner
from hooks.observe.instinct_manager import InstinctManager
from hooks.observe.observer_daemon import (
    read_cursor,
    update_cursor,
)


def get_homunculus_dir() -> Path:
    """Get the homunculus data directory."""
    home = Path(os.environ.get("HOME", "~")).expanduser()
    return home / ".claude" / "lsz" / "homunculus"


def process_project_observations(
    project_dir: Path,
    project_id: str,
    dry_run: bool = False,
    batch_size: int = 50,
) -> dict:
    """Process observations for a single project."""
    observations_file = project_dir / "observations.jsonl"

    if not observations_file.exists():
        return {"processed_count": 0, "message": "No observations file"}

    # Read current cursor
    cursor = read_cursor(project_dir)
    start_line = cursor.get("line", 0)

    # Get new observations
    with open(observations_file) as f:
        lines = f.readlines()

    new_lines = lines[start_line:]

    if not new_lines:
        return {"processed_count": 0, "message": "No new observations"}

    # Limit to batch size
    batch = new_lines[:batch_size]
    processed_count = len(batch)

    if dry_run:
        return {
            "processed_count": processed_count,
            "remaining_count": len(new_lines) - processed_count,
            "message": f"Dry run: would process {processed_count} observations",
        }

    # Build session payload from observations
    observations = []
    for line in batch:
        line = line.strip()
        if line:
            try:
                observations.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Group by session
    sessions: dict[str, list] = {}
    for obs in observations:
        session_id = obs.get("session", "unknown")
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append(obs)

    session_payloads = [{"session_id": sid, "events": events} for sid, events in sessions.items()]

    # Run agent
    payload = {
        "sessions": session_payloads,
        "project_id": project_id,
        "cursor_position": start_line,
    }

    runner = AgentRunner()
    result = runner.run(payload)

    # Update cursor
    update_cursor(project_dir, start_line + processed_count)

    # Process results
    homunculus_dir = project_dir.parent.parent
    manager = InstinctManager(homunculus_dir)

    for instinct in result.instincts_created:
        manager.create_instinct(instinct, project_id)

    for update in result.instincts_updated:
        manager.update_instinct(update, project_id)

    return {
        "processed_count": processed_count,
        "instincts_created": len(result.instincts_created),
        "instincts_updated": len(result.instincts_updated),
    }


def main() -> int:
    """Main entry point for analyze command."""
    parser = argparse.ArgumentParser(description="Analyze observations")
    parser.add_argument("--project", help="Analyze specific project")
    parser.add_argument("--all-projects", action="store_true", help="Analyze all projects")
    parser.add_argument("--batch-size", type=int, default=50, help="Max observations to process")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    homunculus_dir = get_homunculus_dir()

    # Determine which projects to process
    projects_to_process = []

    if args.project:
        project_dir = homunculus_dir / "projects" / args.project
        if project_dir.exists():
            projects_to_process.append((args.project, project_dir))
    elif args.all_projects:
        projects_dir = homunculus_dir / "projects"
        if projects_dir.exists():
            for proj_dir in projects_dir.iterdir():
                if proj_dir.is_dir():
                    projects_to_process.append((proj_dir.name, proj_dir))
    else:
        # Default: process all projects
        projects_dir = homunculus_dir / "projects"
        if projects_dir.exists():
            for proj_dir in projects_dir.iterdir():
                if proj_dir.is_dir():
                    projects_to_process.append((proj_dir.name, proj_dir))

    if not projects_to_process:
        if args.json:
            print(json.dumps({"processed_count": 0, "message": "No projects found"}))
        else:
            print("No projects found to analyze.")
        return 0

    results = []
    total_processed = 0

    for project_id, project_dir in projects_to_process:
        result = process_project_observations(
            project_dir, project_id, dry_run=args.dry_run, batch_size=args.batch_size
        )
        results.append({"project_id": project_id, **result})
        total_processed += result.get("processed_count", 0)

    if args.json:
        output = {
            "processed_count": total_processed,
            "projects": results,
        }
        print(json.dumps(output, indent=2))
    else:
        print(
            f"Processed {total_processed} observation(s) across {len(projects_to_process)} project(s)."
        )
        for r in results:
            msg = r.get("message") or f"{r.get('processed_count', 0)} observations"
            print(f"  Project {r['project_id']}: {msg}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
