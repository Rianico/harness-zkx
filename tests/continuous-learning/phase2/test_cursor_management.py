"""
Tests for cursor management functionality.

These tests verify that the observer daemon correctly manages
cursor positions for tracking processed observations.

Eval 2.1: Cursor Management
- Cursor read correctly
- Only new observations processed
- Cursor updated after processing
- Cursor file created if missing
"""

import json
from pathlib import Path

import pytest


class TestCursorRead:
    """Tests for reading cursor position."""

    def test_cursor_read_from_file(
        self, project_observations_dir: Path
    ) -> None:
        """
        Should read cursor position from file.

        Eval 2.1: Cursor read correctly.
        """
        # Create cursor file with known position
        cursor_file = project_observations_dir / ".observer-cursor"
        cursor_data = {"line": 500, "updated_at": "2026-04-30T10:00:00Z"}
        cursor_file.write_text(json.dumps(cursor_data))

        from hooks.observe import observer_daemon

        result = observer_daemon.read_cursor(project_observations_dir)

        assert result["line"] == 500, f"Expected line 500, got {result['line']}"
        assert "updated_at" in result, "updated_at should be present"

    def test_cursor_missing_returns_zero(
        self, project_observations_dir: Path
    ) -> None:
        """
        Should return line 0 when cursor file doesn't exist.

        Eval 2.1: Cursor file created if missing.
        """
        cursor_file = project_observations_dir / ".observer-cursor"
        assert not cursor_file.exists(), "Cursor file should not exist"

        from hooks.observe import observer_daemon

        result = observer_daemon.read_cursor(project_observations_dir)

        assert result["line"] == 0, f"Expected line 0, got {result['line']}"

    def test_cursor_malformed_returns_zero(
        self, project_observations_dir: Path
    ) -> None:
        """
        Should return line 0 when cursor file is malformed.
        """
        cursor_file = project_observations_dir / ".observer-cursor"
        cursor_file.write_text("not valid json")

        from hooks.observe import observer_daemon

        result = observer_daemon.read_cursor(project_observations_dir)

        assert result["line"] == 0, f"Expected line 0 for malformed JSON"


class TestCursorUpdate:
    """Tests for updating cursor position."""

    def test_cursor_update_after_processing(
        self, project_observations_dir: Path
    ) -> None:
        """
        Should update cursor after processing.

        Eval 2.1: Cursor updated after processing.
        """
        from hooks.observe import observer_daemon

        observer_daemon.update_cursor(project_observations_dir, line=750)

        cursor_file = project_observations_dir / ".observer-cursor"
        assert cursor_file.exists(), "Cursor file should be created"

        with open(cursor_file) as f:
            data = json.load(f)

        assert data["line"] == 750, f"Expected line 750, got {data['line']}"
        assert "updated_at" in data, "updated_at should be set"

    def test_cursor_update_overwrites_previous(
        self, project_observations_dir: Path
    ) -> None:
        """
        Should overwrite previous cursor position.
        """
        from hooks.observe import observer_daemon

        # First update
        observer_daemon.update_cursor(project_observations_dir, line=100)

        # Second update
        observer_daemon.update_cursor(project_observations_dir, line=200)

        cursor_file = project_observations_dir / ".observer-cursor"
        with open(cursor_file) as f:
            data = json.load(f)

        assert data["line"] == 200, f"Expected line 200, got {data['line']}"

    def test_cursor_timestamp_is_iso8601(
        self, project_observations_dir: Path
    ) -> None:
        """
        Cursor timestamp should be ISO 8601 format.
        """
        from hooks.observe import observer_daemon
        import re

        observer_daemon.update_cursor(project_observations_dir, line=100)

        cursor_file = project_observations_dir / ".observer-cursor"
        with open(cursor_file) as f:
            data = json.load(f)

        # ISO 8601 format: 2026-04-30T10:00:00Z or 2026-04-30T10:00:00.123Z
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        assert re.match(iso_pattern, data["updated_at"]), (
            f"Timestamp should be ISO 8601, got {data['updated_at']}"
        )


class TestCursorCreate:
    """Tests for cursor file creation."""

    def test_cursor_create_if_missing(
        self, project_observations_dir: Path
    ) -> None:
        """
        Should create cursor file if it doesn't exist.

        Eval 2.1: Cursor file created if missing.
        """
        cursor_file = project_observations_dir / ".observer-cursor"
        assert not cursor_file.exists(), "Cursor file should not exist initially"

        from hooks.observe import observer_daemon

        observer_daemon.update_cursor(project_observations_dir, line=0)

        assert cursor_file.exists(), "Cursor file should be created"
        with open(cursor_file) as f:
            data = json.load(f)
        assert data["line"] == 0, f"Expected line 0, got {data['line']}"

    def test_cursor_creates_parent_directory(
        self, tmp_path: Path
    ) -> None:
        """
        Should create parent directory if it doesn't exist.
        """
        project_dir = tmp_path / "new-project" / "deep" / "path"
        assert not project_dir.exists(), "Directory should not exist"

        from hooks.observe import observer_daemon

        observer_daemon.update_cursor(project_dir, line=100)

        assert project_dir.exists(), "Parent directory should be created"
        cursor_file = project_dir / ".observer-cursor"
        assert cursor_file.exists(), "Cursor file should be created"


class TestObservationFiltering:
    """Tests for filtering observations based on cursor."""

    def test_only_new_observations_processed(
        self, project_observations_dir: Path
    ) -> None:
        """
        Should only process observations after cursor position.

        Eval 2.1: Only new observations processed.
        """
        # Create observations file with 100 lines
        observations_file = project_observations_dir / "observations.jsonl"
        for i in range(100):
            obs = {"line": i, "event": "tool_start", "tool": "Read"}
            observations_file.write_text(
                observations_file.read_text() + json.dumps(obs) + "\n"
                if observations_file.exists()
                else json.dumps(obs) + "\n"
            )

        # Set cursor to line 50
        from hooks.observe import observer_daemon

        observer_daemon.update_cursor(project_observations_dir, line=50)

        # Get new observations
        new_obs = observer_daemon.get_new_observations(project_observations_dir)

        assert len(new_obs) == 50, f"Expected 50 new observations, got {len(new_obs)}"

    def test_no_observations_when_at_end(
        self, project_observations_dir: Path
    ) -> None:
        """
        Should return empty list when cursor is at end of file.
        """
        observations_file = project_observations_dir / "observations.jsonl"
        for i in range(10):
            obs = {"line": i, "event": "tool_start"}
            observations_file.write_text(
                observations_file.read_text() + json.dumps(obs) + "\n"
                if observations_file.exists()
                else json.dumps(obs) + "\n"
            )

        from hooks.observe import observer_daemon

        observer_daemon.update_cursor(project_observations_dir, line=10)

        new_obs = observer_daemon.get_new_observations(project_observations_dir)

        assert len(new_obs) == 0, f"Expected 0 observations, got {len(new_obs)}"

    def test_all_observations_when_no_cursor(
        self, project_observations_dir: Path
    ) -> None:
        """
        Should return all observations when cursor doesn't exist.
        """
        observations_file = project_observations_dir / "observations.jsonl"
        for i in range(10):
            obs = {"line": i, "event": "tool_start"}
            observations_file.write_text(
                observations_file.read_text() + json.dumps(obs) + "\n"
                if observations_file.exists()
                else json.dumps(obs) + "\n"
            )

        from hooks.observe import observer_daemon

        new_obs = observer_daemon.get_new_observations(project_observations_dir)

        assert len(new_obs) == 10, f"Expected 10 observations, got {len(new_obs)}"
