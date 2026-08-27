#!/usr/bin/env python3
"""
Generate test fixtures for continuous learning tests.

Creates:
- observations.jsonl (1000+ lines)
- cursor.json
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent


def generate_observations(count: int = 1500) -> list[dict]:
    """Generate sample observations."""
    sessions = [f"session-{i}" for i in range(10)]
    tools = ["Read", "Edit", "Bash", "Write", "Grep", "Glob"]
    events = ["tool_start", "tool_complete"]
    base_time = datetime(2026, 4, 30, 8, 0, 0)

    observations = []

    for i in range(count):
        session = random.choice(sessions)
        tool = random.choice(tools)
        event = random.choice(events)
        timestamp = base_time + timedelta(seconds=i * 2)

        obs = {
            "timestamp": timestamp.isoformat() + "Z",
            "event": event,
            "tool": tool,
            "input": {
                "file_path": f"/path/to/file_{i % 20}.py",
                "content": f"sample content {i}"[:100],
            }
            if tool in ["Read", "Edit", "Write"]
            else {"command": f"echo 'test {i}'"}
            if tool == "Bash"
            else {"pattern": "test"},
            "output": f"Result of {tool} operation {i}"[:200] if event == "tool_complete" else None,
            "session": session,
            "project_id": "test123abc456",
            "project_name": "test-project",
            "tool_use_id": f"toolu_{i:06d}",
        }
        observations.append(obs)

    return observations


def generate_sessions() -> dict[str, list[dict]]:
    """Generate sample session data for pattern testing."""
    sessions = {}

    # Session with user correction pattern
    sessions["user_correction"] = [
        {
            "timestamp": "2026-04-30T10:00:00Z",
            "event": "tool_start",
            "tool": "Edit",
            "session": "correction-1",
        },
        {
            "timestamp": "2026-04-30T10:00:05Z",
            "event": "tool_complete",
            "tool": "Edit",
            "session": "correction-1",
            "output": "user_rejected: true",
        },
        {
            "timestamp": "2026-04-30T10:00:10Z",
            "event": "tool_start",
            "tool": "Read",
            "session": "correction-1",
        },
        {
            "timestamp": "2026-04-30T10:00:15Z",
            "event": "tool_complete",
            "tool": "Read",
            "session": "correction-1",
        },
        {
            "timestamp": "2026-04-30T10:00:20Z",
            "event": "tool_start",
            "tool": "Edit",
            "session": "correction-1",
        },
        {
            "timestamp": "2026-04-30T10:00:25Z",
            "event": "tool_complete",
            "tool": "Edit",
            "session": "correction-1",
            "output": "success",
        },
    ]

    # Session with repeated workflow pattern
    sessions["repeated_workflow"] = []
    base = datetime(2026, 4, 30, 11, 0, 0)
    for i in range(4):  # 4 repetitions (exceeds minimum of 3)
        t = base + timedelta(minutes=i * 5)
        sessions["repeated_workflow"].extend(
            [
                {
                    "timestamp": t.isoformat() + "Z",
                    "event": "tool_start",
                    "tool": "Read",
                    "session": "workflow-1",
                },
                {
                    "timestamp": (t + timedelta(seconds=5)).isoformat() + "Z",
                    "event": "tool_complete",
                    "tool": "Read",
                    "session": "workflow-1",
                },
                {
                    "timestamp": (t + timedelta(seconds=10)).isoformat() + "Z",
                    "event": "tool_start",
                    "tool": "Edit",
                    "session": "workflow-1",
                },
                {
                    "timestamp": (t + timedelta(seconds=15)).isoformat() + "Z",
                    "event": "tool_complete",
                    "tool": "Edit",
                    "session": "workflow-1",
                },
                {
                    "timestamp": (t + timedelta(seconds=20)).isoformat() + "Z",
                    "event": "tool_start",
                    "tool": "Bash",
                    "session": "workflow-1",
                },
                {
                    "timestamp": (t + timedelta(seconds=25)).isoformat() + "Z",
                    "event": "tool_complete",
                    "tool": "Bash",
                    "session": "workflow-1",
                },
            ]
        )

    # Session with error resolution pattern
    sessions["error_resolution"] = [
        {
            "timestamp": "2026-04-30T12:00:00Z",
            "event": "tool_start",
            "tool": "Bash",
            "session": "resolution-1",
        },
        {
            "timestamp": "2026-04-30T12:00:05Z",
            "event": "tool_complete",
            "tool": "Bash",
            "session": "resolution-1",
            "output": "error: command not found",
        },
        {
            "timestamp": "2026-04-30T12:00:10Z",
            "event": "tool_start",
            "tool": "Bash",
            "session": "resolution-1",
            "input": {"command": "modified command"},
        },
        {
            "timestamp": "2026-04-30T12:00:15Z",
            "event": "tool_complete",
            "tool": "Bash",
            "session": "resolution-1",
            "output": "success",
        },
    ]

    return sessions


def main():
    # Create fixtures directory if needed
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    # Generate observations.jsonl
    observations = generate_observations(1500)
    obs_file = FIXTURES_DIR / "observations.jsonl"
    with open(obs_file, "w") as f:
        for obs in observations:
            f.write(json.dumps(obs) + "\n")
    print(f"Created {obs_file} with {len(observations)} lines")

    # Generate cursor.json
    cursor = {"line": 500, "updated_at": "2026-04-30T10:30:00Z"}
    cursor_file = FIXTURES_DIR / "cursor.json"
    with open(cursor_file, "w") as f:
        json.dump(cursor, f, indent=2)
    print(f"Created {cursor_file}")

    # Generate session fixtures
    sessions = generate_sessions()
    sessions_dir = FIXTURES_DIR / "sessions"
    sessions_dir.mkdir(exist_ok=True)

    for name, events in sessions.items():
        session_file = sessions_dir / f"{name}.json"
        with open(session_file, "w") as f:
            json.dump(events, f, indent=2)
        print(f"Created {session_file} with {len(events)} events")

    print("\nFixtures created successfully!")


if __name__ == "__main__":
    main()
