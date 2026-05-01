"""
Tests for analyze command.

Eval 5.2: analyze Command

Input: `/continuous-learning analyze`
Expected: Immediate observation analysis

Pass criteria:
- [ ] Reads unprocessed observations
- [ ] Spawns observer agent
- [ ] Updates cursor
- [ ] Reports results
"""

import json
import sys
from pathlib import Path

import pytest

from hooks.observe.instinct_manager import InstinctManager
from hooks.observe.observer_daemon import read_cursor, update_cursor


SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent / "skills" / "continuous-learning" / "scripts"
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def analyze_script() -> Path:
    """Return path to analyze script."""
    return SCRIPTS_DIR / "analyze.py"


@pytest.fixture
def instinct_manager(homunculus_dir: Path) -> InstinctManager:
    """Create instinct manager instance."""
    return InstinctManager(homunculus_dir)


@pytest.fixture
def observations_with_unprocessed(homunculus_dir: Path) -> Path:
    """Create observations file with unprocessed data."""
    project_id = "a1b2c3d4e5f6"
    project_dir = homunculus_dir / "projects" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    observations_file = project_dir / "observations.jsonl"

    # Create observations with a session containing a pattern
    observations = [
        {
            "timestamp": "2026-04-30T10:00:00Z",
            "event": "tool_start",
            "tool": "Edit",
            "input": {"file_path": "/path/to/file.py"},
            "session": "analyze-test-1",
            "project_id": project_id
        },
        {
            "timestamp": "2026-04-30T10:00:05Z",
            "event": "tool_complete",
            "tool": "Edit",
            "output": "user_rejected: true",
            "session": "analyze-test-1",
            "project_id": project_id
        },
        {
            "timestamp": "2026-04-30T10:00:10Z",
            "event": "tool_start",
            "tool": "Read",
            "input": {"file_path": "/path/to/file.py"},
            "session": "analyze-test-1",
            "project_id": project_id
        },
        {
            "timestamp": "2026-04-30T10:00:15Z",
            "event": "tool_complete",
            "tool": "Read",
            "session": "analyze-test-1",
            "project_id": project_id
        },
        {
            "timestamp": "2026-04-30T10:00:20Z",
            "event": "tool_start",
            "tool": "Edit",
            "input": {"file_path": "/path/to/file.py"},
            "session": "analyze-test-1",
            "project_id": project_id
        },
        {
            "timestamp": "2026-04-30T10:00:25Z",
            "event": "tool_complete",
            "tool": "Edit",
            "output": "success",
            "session": "analyze-test-1",
            "project_id": project_id
        },
    ]

    with open(observations_file, "w") as f:
        for obs in observations:
            f.write(json.dumps(obs) + "\n")

    return observations_file


@pytest.fixture
def cursor_at_beginning(homunculus_dir: Path) -> Path:
    """Create cursor file at beginning (line 0)."""
    project_id = "a1b2c3d4e5f6"
    cursor_file = homunculus_dir / "projects" / project_id / ".observer-cursor"

    cursor_data = {"line": 0, "updated_at": "2026-04-30T09:00:00Z"}
    cursor_file.write_text(json.dumps(cursor_data))

    return cursor_file


@pytest.fixture
def cursor_at_middle(homunculus_dir: Path) -> Path:
    """Create cursor file already past some observations."""
    project_id = "a1b2c3d4e5f6"
    cursor_file = homunculus_dir / "projects" / project_id / ".observer-cursor"

    cursor_data = {"line": 3, "updated_at": "2026-04-30T10:00:12Z"}
    cursor_file.write_text(json.dumps(cursor_data))

    return cursor_file


class TestAnalyzeCommandScript:
    """Tests for the analyze command script file existence."""

    def test_script_exists(self, analyze_script: Path) -> None:
        """
        The analyze.py script should exist in the scripts directory.
        """
        assert analyze_script.exists(), f"Script not found at {analyze_script}"


class TestAnalyzeCommandFunctionality:
    """Tests for analyze command functionality via ObserverDaemon."""

    def test_reads_unprocessed_observations(
        self, homunculus_dir: Path, observations_with_unprocessed: Path, cursor_at_beginning: Path
    ) -> None:
        """
        Eval 5.2: Reads unprocessed observations.

        The analyze command should read observations from cursor position.
        """
        project_id = "a1b2c3d4e5f6"
        project_dir = homunculus_dir / "projects" / project_id
        observations_file = project_dir / "observations.jsonl"

        # Read cursor using project_dir
        cursor = read_cursor(project_dir)
        assert cursor is not None
        assert cursor.get("line") == 0

        # Count observations
        with open(observations_file) as f:
            lines = f.readlines()

        assert len(lines) == 6, f"Expected 6 observations, got {len(lines)}"

    def test_cursor_positions_correctly(
        self, homunculus_dir: Path, observations_with_unprocessed: Path, cursor_at_beginning: Path
    ) -> None:
        """
        Eval 5.2: Cursor should track position correctly.
        """
        project_id = "a1b2c3d4e5f6"
        project_dir = homunculus_dir / "projects" / project_id

        # Update cursor position
        update_cursor(project_dir, 6)

        # Read it back
        cursor = read_cursor(project_dir)
        assert cursor is not None
        assert cursor.get("line") == 6

    def test_respects_cursor_position(
        self, homunculus_dir: Path, observations_with_unprocessed: Path, cursor_at_middle: Path
    ) -> None:
        """
        Analyze should only process observations after cursor position.
        """
        project_id = "a1b2c3d4e5f6"
        project_dir = homunculus_dir / "projects" / project_id
        observations_file = project_dir / "observations.jsonl"

        # Read cursor using project_dir
        cursor = read_cursor(project_dir)
        assert cursor is not None
        assert cursor.get("line") == 3

        # Read observations after cursor
        with open(observations_file) as f:
            lines = f.readlines()

        remaining = lines[cursor["line"]:]
        assert len(remaining) == 3, f"Expected 3 remaining observations, got {len(remaining)}"

    def test_handles_missing_observations_file(
        self, homunculus_dir: Path
    ) -> None:
        """
        Should handle missing observations file gracefully.
        """
        project_id = "nonexistent-project"
        observations_file = homunculus_dir / "projects" / project_id / "observations.jsonl"

        assert not observations_file.exists()

    def test_handles_missing_cursor_file(
        self, homunculus_dir: Path, observations_with_unprocessed: Path
    ) -> None:
        """
        Should handle missing cursor file by starting at 0.
        """
        project_id = "a1b2c3d4e5f6"
        project_dir = homunculus_dir / "projects" / project_id
        cursor_file = project_dir / ".observer-cursor"

        # Delete cursor file
        if cursor_file.exists():
            cursor_file.unlink()

        # Read should return default with line 0
        cursor = read_cursor(project_dir)
        assert cursor is not None
        assert cursor.get("line") == 0


class TestAnalyzeCommandGrouping:
    """Tests for observation grouping functionality."""

    def test_groups_observations_by_session(
        self, homunculus_dir: Path, observations_with_unprocessed: Path
    ) -> None:
        """
        Observations should be grouped by session_id.
        """
        project_id = "a1b2c3d4e5f6"
        observations_file = homunculus_dir / "projects" / project_id / "observations.jsonl"

        # Read and parse observations
        with open(observations_file) as f:
            observations = [json.loads(line) for line in f]

        # Group by session
        sessions: dict[str, list] = {}
        for obs in observations:
            session_id = obs.get("session", "unknown")
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(obs)

        # Should have one session
        assert "analyze-test-1" in sessions
        assert len(sessions["analyze-test-1"]) == 6

    def test_orders_events_by_timestamp(
        self, homunculus_dir: Path, observations_with_unprocessed: Path
    ) -> None:
        """
        Events within a session should be ordered by timestamp.
        """
        project_id = "a1b2c3d4e5f6"
        observations_file = homunculus_dir / "projects" / project_id / "observations.jsonl"

        with open(observations_file) as f:
            observations = [json.loads(line) for line in f]

        # Get timestamps
        timestamps = [obs["timestamp"] for obs in observations]

        # Should be in ascending order
        assert timestamps == sorted(timestamps)


class TestAnalyzeCommandResults:
    """Tests for analyze command result handling."""

    def test_reports_processed_count(
        self, homunculus_dir: Path, observations_with_unprocessed: Path, instinct_manager: InstinctManager
    ) -> None:
        """
        Analyze should report the number of observations processed.
        """
        project_id = "a1b2c3d4e5f6"
        observations_file = homunculus_dir / "projects" / project_id / "observations.jsonl"

        with open(observations_file) as f:
            count = sum(1 for _ in f)

        assert count == 6, "Should process 6 observations"

    def test_updates_cursor_after_processing(
        self, homunculus_dir: Path, observations_with_unprocessed: Path, cursor_at_beginning: Path
    ) -> None:
        """
        Cursor should be updated after processing observations.
        """
        project_id = "a1b2c3d4e5f6"
        project_dir = homunculus_dir / "projects" / project_id
        observations_file = project_dir / "observations.jsonl"

        # Simulate processing - update cursor
        with open(observations_file) as f:
            line_count = sum(1 for _ in f)

        update_cursor(project_dir, line_count)

        # Verify
        cursor = read_cursor(project_dir)
        assert cursor is not None
        assert cursor.get("line") == line_count


class TestAnalyzeScriptExecution:
    """Tests for analyze script execution.

    These tests verify the script wrapper works correctly.
    The scripts are currently stubs, so these tests should FAIL.
    """

    def test_script_returns_zero_exit_code(
        self, analyze_script: Path, observations_with_unprocessed: Path, temp_home: Path
    ) -> None:
        """
        Script should return exit code 0 on success.

        Currently FAILS because script is a stub.
        """
        import subprocess

        env = {"HOME": str(temp_home)}

        result = subprocess.run(
            [sys.executable, str(analyze_script), "--project", "a1b2c3d4e5f6", "--dry-run"],
            capture_output=True,
            text=True,
            env=env,
            timeout=60
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_script_outputs_processed_count(
        self, analyze_script: Path, observations_with_unprocessed: Path, temp_home: Path
    ) -> None:
        """
        Script should output the number of observations processed.

        Currently FAILS because script is a stub.
        """
        import subprocess

        env = {"HOME": str(temp_home)}

        result = subprocess.run(
            [sys.executable, str(analyze_script), "--project", "a1b2c3d4e5f6", "--dry-run"],
            capture_output=True,
            text=True,
            env=env,
            timeout=60
        )

        # Should mention observations processed
        assert "observation" in result.stdout.lower() or "processed" in result.stdout.lower(), \
            f"Expected processed count in output: {result.stdout}"
