"""
Tests for observation grouping functionality.

These tests verify that the observer daemon correctly groups
observations by session for pattern detection.

Eval 2.2: Observation Grouping
- Observations grouped by session_id
- Events ordered by timestamp within session
- Truncated fields preserved correctly
"""

import json
from datetime import datetime, timedelta
from pathlib import Path


class TestGroupBySession:
    """Tests for grouping observations by session."""

    def test_group_by_session_id(self, project_observations_dir: Path) -> None:
        """
        Should group observations by session_id.

        Eval 2.2: Observations grouped by session_id.
        """
        # Create observations from multiple sessions
        observations_file = project_observations_dir / "observations.jsonl"
        sessions = ["session-1", "session-2", "session-3"]
        base_time = datetime(2026, 4, 30, 10, 0, 0)

        for i, session in enumerate(sessions):
            for j in range(5):
                obs = {
                    "timestamp": (base_time + timedelta(minutes=i * 10 + j)).isoformat() + "Z",
                    "event": "tool_start",
                    "tool": "Read",
                    "session": session,
                    "project_id": "test123",
                    "tool_use_id": f"toolu_{i}_{j}",
                }
                with open(observations_file, "a") as f:
                    f.write(json.dumps(obs) + "\n")

        from hooks.observe import observer_daemon

        groups = observer_daemon.group_observations_by_session(observations_file)

        assert len(groups) == 3, f"Expected 3 session groups, got {len(groups)}"
        for session_id in sessions:
            assert session_id in groups, f"Session {session_id} should be in groups"
            assert len(groups[session_id]) == 5, f"Session {session_id} should have 5 observations"

    def test_empty_session_handling(self, project_observations_dir: Path) -> None:
        """
        Should handle observations with missing session_id.
        """
        observations_file = project_observations_dir / "observations.jsonl"
        obs_no_session = {
            "timestamp": "2026-04-30T10:00:00Z",
            "event": "tool_start",
            "tool": "Read",
            # No session field
            "project_id": "test123",
        }
        with open(observations_file, "a") as f:
            f.write(json.dumps(obs_no_session) + "\n")

        from hooks.observe import observer_daemon

        groups = observer_daemon.group_observations_by_session(observations_file)

        # Should either skip or use a default session
        # Implementation decision: use "unknown" as default
        assert "unknown" in groups or len(groups) == 0, "Should handle missing session_id"

    def test_session_payload_schema(self, project_observations_dir: Path) -> None:
        """
        Output payload should match expected schema.

        Eval 2.2: Output payload should match expected schema.
        """
        observations_file = project_observations_dir / "observations.jsonl"
        obs = {
            "timestamp": "2026-04-30T10:00:00Z",
            "event": "tool_start",
            "tool": "Read",
            "session": "session-1",
            "project_id": "test123",
            "tool_use_id": "toolu_001",
        }
        with open(observations_file, "a") as f:
            f.write(json.dumps(obs) + "\n")

        from hooks.observe import observer_daemon

        payload = observer_daemon.build_session_payload(observations_file)

        # Expected schema
        assert "sessions" in payload, "Payload should have 'sessions' key"
        assert isinstance(payload["sessions"], list), "sessions should be a list"
        if len(payload["sessions"]) > 0:
            session = payload["sessions"][0]
            assert "session_id" in session, "Session should have session_id"
            assert "events" in session, "Session should have events"
            assert isinstance(session["events"], list), "events should be a list"


class TestOrderWithinSession:
    """Tests for ordering events within a session."""

    def test_order_by_timestamp(self, project_observations_dir: Path) -> None:
        """
        Events should be ordered by timestamp within session.

        Eval 2.2: Events ordered by timestamp within session.
        """
        observations_file = project_observations_dir / "observations.jsonl"
        base_time = datetime(2026, 4, 30, 10, 0, 0)

        # Add events in reverse order
        for i in range(5, 0, -1):
            obs = {
                "timestamp": (base_time + timedelta(minutes=i)).isoformat() + "Z",
                "event": "tool_start",
                "tool": "Read",
                "session": "session-1",
                "project_id": "test123",
                "tool_use_id": f"toolu_{i}",
            }
            with open(observations_file, "a") as f:
                f.write(json.dumps(obs) + "\n")

        from hooks.observe import observer_daemon

        groups = observer_daemon.group_observations_by_session(observations_file)

        timestamps = [e["timestamp"] for e in groups["session-1"]]

        assert timestamps == sorted(timestamps), "Events should be sorted by timestamp"

    def test_preserve_tool_start_before_complete(self, project_observations_dir: Path) -> None:
        """
        Tool start should come before complete when timestamps are equal.
        """
        observations_file = project_observations_dir / "observations.jsonl"

        # Same timestamp for start and complete
        ts = "2026-04-30T10:00:00Z"

        # Add complete before start (wrong order in file)
        obs_complete = {
            "timestamp": ts,
            "event": "tool_complete",
            "tool": "Read",
            "session": "session-1",
            "project_id": "test123",
            "tool_use_id": "toolu_001",
        }
        obs_start = {
            "timestamp": ts,
            "event": "tool_start",
            "tool": "Read",
            "session": "session-1",
            "project_id": "test123",
            "tool_use_id": "toolu_001",
        }

        with open(observations_file, "a") as f:
            f.write(json.dumps(obs_complete) + "\n")
            f.write(json.dumps(obs_start) + "\n")

        from hooks.observe import observer_daemon

        groups = observer_daemon.group_observations_by_session(observations_file)

        events = groups["session-1"]
        # Start should come before complete
        assert events[0]["event"] == "tool_start", "tool_start should come before tool_complete"


class TestTruncatedFields:
    """Tests for preserving truncated fields."""

    def test_truncated_input_preserved(self, project_observations_dir: Path) -> None:
        """
        Truncated input should be preserved in grouping.

        Eval 2.2: Truncated fields preserved correctly.
        """
        observations_file = project_observations_dir / "observations.jsonl"

        # Input that was truncated (indicated by truncation marker)
        obs = {
            "timestamp": "2026-04-30T10:00:00Z",
            "event": "tool_start",
            "tool": "Edit",
            "input": "x" * 5000 + "...[TRUNCATED]",
            "session": "session-1",
            "project_id": "test123",
        }
        with open(observations_file, "a") as f:
            f.write(json.dumps(obs) + "\n")

        from hooks.observe import observer_daemon

        groups = observer_daemon.group_observations_by_session(observations_file)

        assert "session-1" in groups
        event = groups["session-1"][0]
        assert "[TRUNCATED]" in event["input"], "Truncated input should be preserved"

    def test_truncated_output_preserved(self, project_observations_dir: Path) -> None:
        """
        Truncated output should be preserved in grouping.
        """
        observations_file = project_observations_dir / "observations.jsonl"

        obs = {
            "timestamp": "2026-04-30T10:00:00Z",
            "event": "tool_complete",
            "tool": "Bash",
            "output": "y" * 5000 + "...[TRUNCATED]",
            "session": "session-1",
            "project_id": "test123",
        }
        with open(observations_file, "a") as f:
            f.write(json.dumps(obs) + "\n")

        from hooks.observe import observer_daemon

        groups = observer_daemon.group_observations_by_session(observations_file)

        event = groups["session-1"][0]
        assert "[TRUNCATED]" in event["output"], "Truncated output should be preserved"


class TestPayloadStructure:
    """Tests for payload structure validation."""

    def test_payload_includes_metadata(self, project_observations_dir: Path) -> None:
        """
        Payload should include processing metadata.
        """
        observations_file = project_observations_dir / "observations.jsonl"
        for i in range(10):
            obs = {
                "timestamp": f"2026-04-30T10:0{i}:00Z",
                "event": "tool_start",
                "tool": "Read",
                "session": f"session-{i % 3}",
                "project_id": "test123",
            }
            with open(observations_file, "a") as f:
                f.write(json.dumps(obs) + "\n")

        from hooks.observe import observer_daemon

        payload = observer_daemon.build_session_payload(observations_file)

        # Should include metadata
        assert "processed_count" in payload, "Payload should include processed_count"
        assert payload["processed_count"] == 10, (
            "processed_count should match number of observations"
        )

    def test_payload_includes_project_id(self, project_observations_dir: Path) -> None:
        """
        Payload should include project_id.
        """
        observations_file = project_observations_dir / "observations.jsonl"
        obs = {
            "timestamp": "2026-04-30T10:00:00Z",
            "event": "tool_start",
            "tool": "Read",
            "session": "session-1",
            "project_id": "abc123def456",
        }
        with open(observations_file, "a") as f:
            f.write(json.dumps(obs) + "\n")

        from hooks.observe import observer_daemon

        payload = observer_daemon.build_session_payload(observations_file)

        assert "project_id" in payload, "Payload should include project_id"
        assert payload["project_id"] == "abc123def456"
