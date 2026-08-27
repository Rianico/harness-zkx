"""
Comprehensive tests for group_observations_by_session stdlib replacement.

These tests verify that the stdlib-only implementation produces identical
output to the pandas implementation for all specified edge cases.
"""

import json
from pathlib import Path


class TestEmptyAndMissingFiles:
    """Tests for T1-T2: Empty and missing file handling."""

    def test_t1_empty_file_returns_empty_dict(self, tmp_path: Path) -> None:
        """T1: Empty file (zero bytes) should return empty dict."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        observations_file.write_text("")

        result = observer_daemon.group_observations_by_session(observations_file)

        assert result == {}, f"Expected empty dict for empty file, got {result}"

    def test_t1_whitespace_only_returns_empty_dict(self, tmp_path: Path) -> None:
        """T1: File with only whitespace/newlines should return empty dict."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        observations_file.write_text("\n\n   \n\t\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        assert result == {}, f"Expected empty dict for whitespace-only file, got {result}"

    def test_t2_file_not_found_returns_empty_dict(self, tmp_path: Path) -> None:
        """T2: Non-existent file should return empty dict."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "does_not_exist.jsonl"

        result = observer_daemon.group_observations_by_session(observations_file)

        assert result == {}, f"Expected empty dict for missing file, got {result}"


class TestBasicGrouping:
    """Tests for T3-T4: Basic grouping functionality."""

    def test_t3_single_observation_single_session(self, tmp_path: Path) -> None:
        """T3: Single observation should be in its session."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        obs = {"session": "sess-1", "timestamp": "2024-01-15T10:00:00Z", "event": "tool_start"}
        observations_file.write_text(json.dumps(obs) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        assert "sess-1" in result
        assert len(result["sess-1"]) == 1
        assert result["sess-1"][0] == obs

    def test_t4_multiple_observations_same_session(self, tmp_path: Path) -> None:
        """T4: Multiple observations in same session should be grouped together."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        obs1 = {"session": "sess-1", "timestamp": "2024-01-15T10:00:00Z", "event": "tool_start"}
        obs2 = {"session": "sess-1", "timestamp": "2024-01-15T10:00:01Z", "event": "tool_complete"}

        with open(observations_file, "w") as f:
            f.write(json.dumps(obs1) + "\n")
            f.write(json.dumps(obs2) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        assert "sess-1" in result
        assert len(result["sess-1"]) == 2
        # Both should be in the session
        assert result["sess-1"][0]["event"] == "tool_start"
        assert result["sess-1"][1]["event"] == "tool_complete"


class TestSortingBehavior:
    """Tests for T5-T6: Sorting by timestamp and event order."""

    def test_t5_observations_sorted_by_timestamp(self, tmp_path: Path) -> None:
        """T5: Observations should be sorted by timestamp ascending."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        # Write in reverse order
        observations = [
            {"session": "s1", "timestamp": "2024-01-15T10:00:02Z", "event": "x"},
            {"session": "s1", "timestamp": "2024-01-15T10:00:00Z", "event": "x"},
            {"session": "s1", "timestamp": "2024-01-15T10:00:01Z", "event": "x"},
        ]

        with open(observations_file, "w") as f:
            for obs in observations:
                f.write(json.dumps(obs) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        timestamps = [o["timestamp"] for o in result["s1"]]
        assert timestamps == [
            "2024-01-15T10:00:00Z",
            "2024-01-15T10:00:01Z",
            "2024-01-15T10:00:02Z",
        ]

    def test_t6_secondary_sort_by_event_order(self, tmp_path: Path) -> None:
        """T6: When timestamps equal, tool_start < tool_complete < other."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        # Same timestamp, different events in wrong order
        observations = [
            {"session": "s1", "timestamp": "2024-01-15T10:00:00Z", "event": "tool_complete"},
            {"session": "s1", "timestamp": "2024-01-15T10:00:00Z", "event": "tool_start"},
            {"session": "s1", "timestamp": "2024-01-15T10:00:00Z", "event": "other"},
        ]

        with open(observations_file, "w") as f:
            for obs in observations:
                f.write(json.dumps(obs) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        events = [o["event"] for o in result["s1"]]
        assert events == ["tool_start", "tool_complete", "other"]


class TestMissingFields:
    """Tests for T7-T10: Missing field handling."""

    def test_t7_missing_session_defaults_to_unknown(self, tmp_path: Path) -> None:
        """T7: Observation without session field should go to 'unknown'."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        obs = {"timestamp": "2024-01-15T10:00:00Z", "event": "x"}
        observations_file.write_text(json.dumps(obs) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        assert "unknown" in result
        assert len(result["unknown"]) == 1
        # Observation should be preserved as-is
        assert "session" not in result["unknown"][0]

    def test_t8_null_session_becomes_unknown(self, tmp_path: Path) -> None:
        """T8: Observation with null session should go to 'unknown'."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        obs = {"session": None, "timestamp": "2024-01-15T10:00:00Z", "event": "x"}
        observations_file.write_text(json.dumps(obs) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        assert "unknown" in result

    def test_t9_missing_timestamp_preserved(self, tmp_path: Path) -> None:
        """T9: Observation without timestamp should be preserved."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        obs = {"session": "s1", "event": "x"}
        observations_file.write_text(json.dumps(obs) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        assert "s1" in result
        assert len(result["s1"]) == 1
        # timestamp should be absent in the result
        assert "timestamp" not in result["s1"][0]

    def test_t10_missing_event_preserved(self, tmp_path: Path) -> None:
        """T10: Observation without event should be preserved."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        obs = {"session": "s1", "timestamp": "2024-01-15T10:00:00Z"}
        observations_file.write_text(json.dumps(obs) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        assert "s1" in result
        assert len(result["s1"]) == 1
        # event should be absent in the result
        assert "event" not in result["s1"][0]


class TestMultipleSessions:
    """Tests for T11: Multiple session grouping."""

    def test_t11_multiple_sessions_grouped_correctly(self, tmp_path: Path) -> None:
        """T11: Observations should be correctly grouped by session."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        observations = [
            {"session": "s1", "timestamp": "2024-01-15T10:00:00Z", "event": "x"},
            {"session": "s2", "timestamp": "2024-01-15T10:00:00Z", "event": "y"},
            {"session": "s1", "timestamp": "2024-01-15T10:00:01Z", "event": "z"},
        ]

        with open(observations_file, "w") as f:
            for obs in observations:
                f.write(json.dumps(obs) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        assert len(result) == 2
        assert "s1" in result
        assert "s2" in result
        assert len(result["s1"]) == 2
        assert len(result["s2"]) == 1
        # s1 observations should be sorted by timestamp
        assert result["s1"][0]["timestamp"] == "2024-01-15T10:00:00Z"
        assert result["s1"][1]["timestamp"] == "2024-01-15T10:00:01Z"


class TestMalformedInput:
    """Tests for T12, T16: Malformed input handling."""

    def test_t12_malformed_json_lines_skipped(self, tmp_path: Path) -> None:
        """T12: Invalid JSON lines should be skipped, valid ones preserved."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        content = """{"session": "s1", "timestamp": "2024-01-15T10:00:00Z", "event": "x"}
this is not json
{"session": "s1", "timestamp": "2024-01-15T10:00:01Z", "event": "y"}
"""
        observations_file.write_text(content)

        result = observer_daemon.group_observations_by_session(observations_file)

        assert "s1" in result
        assert len(result["s1"]) == 2

    def test_t16_whitespace_lines_ignored(self, tmp_path: Path) -> None:
        """T16: Blank/whitespace lines should be ignored."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        content = """{"session": "s1", "timestamp": "2024-01-15T10:00:00Z", "event": "x"}

{"session": "s1", "timestamp": "2024-01-15T10:00:01Z", "event": "y"}
"""
        observations_file.write_text(content)

        result = observer_daemon.group_observations_by_session(observations_file)

        assert "s1" in result
        assert len(result["s1"]) == 2


class TestSessionIdTypes:
    """Tests for T13-T15: Session ID type handling."""

    def test_t13_empty_string_session_preserved(self, tmp_path: Path) -> None:
        """T13: Empty string session should be preserved as-is."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        obs = {"session": "", "timestamp": "2024-01-15T10:00:00Z", "event": "x"}
        observations_file.write_text(json.dumps(obs) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        assert "" in result

    def test_t14_numeric_session_converted_to_string(self, tmp_path: Path) -> None:
        """T14: Numeric session should be converted to string for dict key."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        obs = {"session": 123, "timestamp": "2024-01-15T10:00:00Z", "event": "x"}
        observations_file.write_text(json.dumps(obs) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        assert "123" in result

    def test_t15_unicode_session_supported(self, tmp_path: Path) -> None:
        """T15: Unicode session IDs should be preserved."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        obs = {"session": "测试-日本語-🔧", "timestamp": "2024-01-15T10:00:00Z", "event": "x"}
        observations_file.write_text(json.dumps(obs) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        assert "测试-日本語-🔧" in result


class TestComplexScenarios:
    """Tests for T17: Complex mixed scenarios."""

    def test_t17_complex_mixed_scenario(self, tmp_path: Path) -> None:
        """T17: Complex scenario with multiple edge cases."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        content = """{"session": "s1", "timestamp": "2024-01-15T10:00:01Z", "event": "tool_complete"}
{"session": null, "timestamp": "2024-01-15T10:00:00Z", "event": "tool_start"}
invalid line
{"timestamp": "2024-01-15T10:00:02Z", "event": "other"}
{"session": "s1", "timestamp": "2024-01-15T10:00:01Z", "event": "tool_start"}
{"session": "s2", "timestamp": "2024-01-15T09:00:00Z", "event": "x"}
"""
        observations_file.write_text(content)

        result = observer_daemon.group_observations_by_session(observations_file)

        # Should have 3 sessions: s1, s2, unknown
        assert len(result) == 3

        # s1: 2 observations (sorted by timestamp, then event order)
        assert len(result["s1"]) == 2
        assert result["s1"][0]["event"] == "tool_start"
        assert result["s1"][1]["event"] == "tool_complete"

        # s2: 1 observation
        assert len(result["s2"]) == 1

        # unknown: 2 observations (null session, missing session)
        assert len(result["unknown"]) == 2
        # Should be sorted by timestamp
        assert result["unknown"][0]["timestamp"] == "2024-01-15T10:00:00Z"
        assert result["unknown"][1]["timestamp"] == "2024-01-15T10:00:02Z"


class TestNoModification:
    """Verify observations are not modified except for grouping/sorting."""

    def test_observation_dicts_not_modified(self, tmp_path: Path) -> None:
        """Observation dicts should be preserved as-is (no modification)."""
        from hooks.observe import observer_daemon

        observations_file = tmp_path / "observations.jsonl"
        original_obs = {
            "session": "s1",
            "timestamp": "2024-01-15T10:00:00Z",
            "event": "tool_start",
            "tool": "Read",
            "input": {"file_path": "/path/to/file.py"},
            "extra_field": "should be preserved",
        }
        observations_file.write_text(json.dumps(original_obs) + "\n")

        result = observer_daemon.group_observations_by_session(observations_file)

        returned_obs = result["s1"][0]
        # Should preserve all original fields
        assert returned_obs["tool"] == "Read"
        assert returned_obs["input"] == {"file_path": "/path/to/file.py"}
        assert returned_obs["extra_field"] == "should be preserved"
