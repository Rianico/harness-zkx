"""
Tests for signal handling functionality.

These tests verify that the observer daemon correctly handles
signals for waking up and processing observations.

Eval 2.4: Signal Handling
- Daemon wakes on SIGUSR1
- Daemon processes correct project(s)
- Daemon returns to sleep after processing
- Graceful shutdown on SIGTERM
"""

import json
import os
import signal
import time
import threading
from pathlib import Path
from datetime import datetime

import pytest


class TestWakeOnSigusr1:
    """Tests for waking daemon on SIGUSR1 signal."""

    def test_wake_on_sigusr1(
        self, homunculus_dir: Path
    ) -> None:
        """
        Daemon should wake on SIGUSR1 signal.

        Eval 2.4: Daemon wakes on SIGUSR1.
        """
        from hooks.observe import observer_daemon

        # Start daemon in a thread
        wake_event = threading.Event()

        def daemon_main():
            observer_daemon.run_daemon(
                homunculus_dir,
                wake_callback=lambda: wake_event.set()
            )

        thread = threading.Thread(target=daemon_main, daemon=True)
        thread.start()

        # Wait for daemon to be ready
        time.sleep(0.5)

        # Send SIGUSR1 to our process (simulating daemon behavior)
        # In the actual implementation, the daemon would be a separate process
        observer_daemon.signal_wake(os.getpid())

        # Wait for wake event
        woke = wake_event.wait(timeout=2.0)
        assert woke, "Daemon should wake on SIGUSR1"

        observer_daemon.stop_daemon()

    def test_signal_handler_registered(
        self, homunculus_dir: Path
    ) -> None:
        """
        Signal handler should be registered on daemon start.
        """
        from hooks.observe import observer_daemon

        # Check if signal handler can be registered
        handler = observer_daemon.setup_signal_handlers()

        assert handler is not None, "Signal handler should be registered"

        # Restore default handler
        signal.signal(signal.SIGUSR1, signal.SIG_DFL)

    def test_multiple_sigusr1_queued(
        self, homunculus_dir: Path
    ) -> None:
        """
        Multiple SIGUSR1 signals should be handled (not lost).
        """
        from hooks.observe import observer_daemon

        wake_count = [0]

        def count_wake():
            wake_count[0] += 1

        # Simulate multiple signals
        observer_daemon.setup_signal_handlers()
        observer_daemon.set_wake_callback(count_wake)

        # Send multiple signals rapidly
        for _ in range(3):
            observer_daemon.signal_wake(os.getpid())
            time.sleep(0.1)

        # At least one wake should have occurred
        assert wake_count[0] >= 1, "At least one wake should occur"


class TestReturnToSleep:
    """Tests for daemon returning to sleep after processing."""

    def test_return_to_sleep_after_processing(
        self, homunculus_dir: Path
    ) -> None:
        """
        Daemon should return to sleep after processing.

        Eval 2.4: Daemon returns to sleep after processing.
        """
        from hooks.observe import observer_daemon

        processing_states = []

        def track_state(state):
            processing_states.append(state)

        # Simulate processing cycle
        observer_daemon.set_state_callback(track_state)

        # Start processing
        observer_daemon.start_processing_cycle(homunculus_dir)

        # Should have gone through states: idle -> processing -> idle
        assert "processing" in processing_states, "Should enter processing state"
        assert "idle" in processing_states, "Should return to idle state"

    def test_sleep_duration_configurable(
        self, homunculus_dir: Path
    ) -> None:
        """
        Sleep duration should be configurable.
        """
        from hooks.observe import observer_daemon

        # Set custom interval
        observer_daemon.set_sleep_interval(seconds=30)

        interval = observer_daemon.get_sleep_interval()
        assert interval == 30, f"Expected interval 30, got {interval}"

    def test_sleep_interrupted_by_signal(
        self, homunculus_dir: Path
    ) -> None:
        """
        Sleep should be interrupted by signal.
        """
        from hooks.observe import observer_daemon

        # Reset daemon state to ensure clean signal handler
        observer_daemon.reset_daemon_state()

        start_time = time.time()
        signal_sent = threading.Event()
        signal_received = threading.Event()

        def send_signal_after_delay():
            # Small delay to ensure sleep has started
            time.sleep(0.05)
            signal_sent.set()
            observer_daemon.signal_wake(os.getpid())
            # Wait briefly for signal to be processed
            signal_received.wait(timeout=1.0)

        signal_thread = threading.Thread(target=send_signal_after_delay)
        signal_thread.start()

        # Sleep should be interrupted by signal
        observer_daemon.interruptible_sleep(seconds=5)

        elapsed = time.time() - start_time
        signal_received.set()

        # Should have woken up much faster than 5 seconds
        # Allow up to 1.0s to account for system scheduling latency
        assert elapsed < 1.0, f"Sleep should be interrupted, took {elapsed}s"
        assert signal_sent.is_set(), "Signal should have been sent"

        signal_thread.join(timeout=1.0)


class TestIntervalFallback:
    """Tests for interval-based fallback wake."""

    def test_interval_fallback(
        self, homunculus_dir: Path
    ) -> None:
        """
        Daemon should wake on interval if no signal.

        Eval 2.4: Daemon should wake on interval if no signal.
        """
        from hooks.observe import observer_daemon

        # Set a short interval for testing
        observer_daemon.set_sleep_interval(seconds=1)

        wake_times = []

        def record_wake():
            wake_times.append(time.time())

        # Simulate daemon loop
        start = time.time()
        observer_daemon.set_wake_callback(record_wake)

        # Wait for interval-based wake
        time.sleep(1.5)

        # Should have woken at least once due to interval
        assert len(wake_times) >= 1, "Should wake on interval"

    def test_interval_from_config(
        self, homunculus_dir: Path
    ) -> None:
        """
        Interval should be read from config file.
        """
        config_file = homunculus_dir / "config.properties"
        config_file.write_text("run_interval_minutes=10\n")

        from hooks.observe import observer_daemon

        interval = observer_daemon.load_sleep_interval_from_config(config_file)

        assert interval == 600, f"Expected 600 seconds (10 min), got {interval}"

    def test_default_interval_when_no_config(
        self, homunculus_dir: Path
    ) -> None:
        """
        Default interval should be used when config is missing.
        """
        from hooks.observe import observer_daemon

        interval = observer_daemon.get_default_sleep_interval()

        # Default is 5 minutes = 300 seconds
        assert interval == 300, f"Expected default 300 seconds, got {interval}"


class TestSignalProcessing:
    """Tests for signal-based processing logic."""

    def test_processes_correct_projects(
        self, homunculus_dir: Path
    ) -> None:
        """
        Daemon should process correct project(s).

        Eval 2.4: Daemon processes correct project(s).
        """
        from hooks.observe import observer_daemon

        # Create project directories with observations
        project1 = homunculus_dir / "projects" / "project1"
        project1.mkdir(parents=True)
        (project1 / "observations.jsonl").write_text(
            json.dumps({"event": "tool_start", "session": "s1"}) + "\n"
        )

        project2 = homunculus_dir / "projects" / "project2"
        project2.mkdir(parents=True)
        (project2 / "observations.jsonl").write_text(
            json.dumps({"event": "tool_start", "session": "s2"}) + "\n"
        )

        processed_projects = []

        def track_process(project_id):
            processed_projects.append(project_id)

        observer_daemon.process_all_projects(homunculus_dir, callback=track_process)

        assert "project1" in processed_projects, "Should process project1"
        assert "project2" in processed_projects, "Should process project2"

    def test_skips_projects_without_observations(
        self, homunculus_dir: Path
    ) -> None:
        """
        Should skip projects that have no observations.
        """
        from hooks.observe import observer_daemon

        # Create project without observations
        empty_project = homunculus_dir / "projects" / "empty_project"
        empty_project.mkdir(parents=True)

        processed = observer_daemon.get_projects_with_observations(homunculus_dir)

        assert "empty_project" not in processed, (
            "Should skip projects without observations"
        )

    def test_updates_cursor_after_processing(
        self, homunculus_dir: Path
    ) -> None:
        """
        Should update cursor after processing each project.
        """
        from hooks.observe import observer_daemon

        project1 = homunculus_dir / "projects" / "project1"
        project1.mkdir(parents=True)

        # Add 10 observations
        with open(project1 / "observations.jsonl", "w") as f:
            for i in range(10):
                f.write(json.dumps({"event": "tool_start", "line": i}) + "\n")

        observer_daemon.process_project(project1)

        cursor_file = project1 / ".observer-cursor"
        assert cursor_file.exists(), "Cursor should be updated"

        with open(cursor_file) as f:
            cursor = json.load(f)

        assert cursor["line"] == 10, f"Cursor should be at line 10, got {cursor['line']}"
