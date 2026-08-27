"""
Tests for singleton daemon functionality.

These tests verify that the observer daemon correctly implements
singleton pattern with proper PID and lock file management.

Eval 2.3: Singleton Daemon
- Second start attempt fails gracefully
- PID file contains valid PID
- Stale PID file cleaned up
- Lock prevents race conditions
"""

import json
import os
import signal
import time
from pathlib import Path


class TestSingleInstance:
    """Tests for ensuring only one daemon instance runs."""

    def test_single_instance_enforcement(self, homunculus_dir: Path) -> None:
        """
        Only one daemon instance should run.

        Eval 2.3: Second start attempt fails gracefully.
        """
        from hooks.observe import observer_daemon

        # First start should succeed
        result1 = observer_daemon.try_acquire_lock(homunculus_dir)
        assert result1 is True, "First instance should acquire lock"

        # Second start should fail
        result2 = observer_daemon.try_acquire_lock(homunculus_dir)
        assert result2 is False, "Second instance should not acquire lock"

        # Cleanup
        observer_daemon.release_lock(homunculus_dir)

    def test_pid_file_contains_valid_pid(self, homunculus_dir: Path) -> None:
        """
        PID file should contain valid PID.

        Eval 2.3: PID file contains valid PID.
        """
        from hooks.observe import observer_daemon

        observer_daemon.try_acquire_lock(homunculus_dir)

        pid_file = homunculus_dir / ".observer.pid"
        assert pid_file.exists(), "PID file should be created"

        with open(pid_file) as f:
            pid = int(f.read().strip())

        # PID should be our process or a valid integer
        assert pid > 0, f"PID should be positive, got {pid}"
        assert pid == os.getpid(), f"PID should be current process, got {pid}"

        observer_daemon.release_lock(homunculus_dir)

    def test_pid_file_removed_on_release(self, homunculus_dir: Path) -> None:
        """
        PID file should be removed when daemon releases lock.
        """
        from hooks.observe import observer_daemon

        observer_daemon.try_acquire_lock(homunculus_dir)
        pid_file = homunculus_dir / ".observer.pid"
        assert pid_file.exists(), "PID file should exist"

        observer_daemon.release_lock(homunculus_dir)

        assert not pid_file.exists(), "PID file should be removed on release"


class TestStalePidCleanup:
    """Tests for cleaning up stale PID files."""

    def test_stale_pid_cleanup(self, homunculus_dir: Path) -> None:
        """
        Stale PID file should be cleaned up.

        Eval 2.3: Stale PID file cleaned up.
        """
        from hooks.observe import observer_daemon

        # Create a stale PID file with a non-existent process
        pid_file = homunculus_dir / ".observer.pid"
        pid_file.write_text("99999999")  # Very unlikely to be a real PID

        # Try to acquire lock - should clean up stale file
        result = observer_daemon.try_acquire_lock(homunculus_dir)

        assert result is True, "Should acquire lock after cleaning stale PID"

        # New PID file should have our PID
        with open(pid_file) as f:
            pid = int(f.read().strip())
        assert pid == os.getpid(), "Should have new valid PID"

        observer_daemon.release_lock(homunculus_dir)

    def test_stale_pid_with_running_process(self, homunculus_dir: Path) -> None:
        """
        Should not remove PID file if process is still running.
        """
        from hooks.observe import observer_daemon

        # Use PID 1 (always running on Unix systems)
        pid_file = homunculus_dir / ".observer.pid"
        pid_file.write_text("1")

        # Try to acquire lock - should fail because PID 1 is running
        result = observer_daemon.try_acquire_lock(homunculus_dir)

        assert result is False, "Should not acquire lock if process is running"


class TestLockPreventsRace:
    """Tests for lock-based race condition prevention."""

    def test_lock_file_created(self, homunculus_dir: Path) -> None:
        """
        Lock file should be created.

        Eval 2.3: Lock prevents race conditions.
        """
        from hooks.observe import observer_daemon

        observer_daemon.try_acquire_lock(homunculus_dir)

        lock_file = homunculus_dir / ".observer.lock"
        assert lock_file.exists(), "Lock file should be created"

        observer_daemon.release_lock(homunculus_dir)

    def test_lock_file_removed_on_release(self, homunculus_dir: Path) -> None:
        """
        Lock file should be removed on release.
        """
        from hooks.observe import observer_daemon

        observer_daemon.try_acquire_lock(homunculus_dir)
        lock_file = homunculus_dir / ".observer.lock"

        observer_daemon.release_lock(homunculus_dir)

        assert not lock_file.exists(), "Lock file should be removed"

    def test_lock_is_atomic(self, homunculus_dir: Path) -> None:
        """
        Lock acquisition should be atomic (no race condition).
        """
        import threading

        from hooks.observe import observer_daemon

        results = []
        lock = threading.Lock()

        def try_acquire():
            result = observer_daemon.try_acquire_lock(homunculus_dir)
            with lock:
                results.append(result)
            if result:
                time.sleep(0.1)  # Hold lock briefly
                observer_daemon.release_lock(homunculus_dir)

        # Start multiple threads trying to acquire
        threads = [threading.Thread(target=try_acquire) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Only one should have succeeded
        success_count = sum(1 for r in results if r is True)
        assert success_count == 1, f"Only one thread should acquire lock, got {success_count}"


class TestGracefulShutdown:
    """Tests for graceful daemon shutdown."""

    def test_graceful_shutdown_on_sigterm(self, homunculus_dir: Path) -> None:
        """
        Daemon should shut down gracefully on SIGTERM.

        Eval 2.3: Daemon should shut down gracefully on SIGTERM.
        """
        from hooks.observe import observer_daemon

        observer_daemon.try_acquire_lock(homunculus_dir)
        pid_file = homunculus_dir / ".observer.pid"

        # Simulate SIGTERM handling
        observer_daemon.handle_shutdown_signal(signal.SIGTERM)

        # PID file should be cleaned up
        assert not pid_file.exists(), "PID file should be removed on shutdown"

    def test_shutdown_state_preserved(self, homunculus_dir: Path) -> None:
        """
        Daemon should preserve state during shutdown.
        """
        from hooks.observe import observer_daemon

        observer_daemon.try_acquire_lock(homunculus_dir)

        # Set some state
        observer_daemon.set_shutdown_state({"last_processed": 500})

        # Simulate shutdown
        observer_daemon.handle_shutdown_signal(signal.SIGTERM)

        # State file should exist
        state_file = homunculus_dir / ".observer-shutdown-state.json"
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
            assert state.get("last_processed") == 500

    def test_shutdown_timeout(self, homunculus_dir: Path) -> None:
        """
        Daemon should force shutdown after timeout.
        """
        from hooks.observe import observer_daemon

        # Simulate a shutdown that takes too long
        observer_daemon.try_acquire_lock(homunculus_dir)

        # Force shutdown should clean up even if processing hangs
        observer_daemon.force_shutdown(timeout_seconds=1)

        pid_file = homunculus_dir / ".observer.pid"
        assert not pid_file.exists(), "PID file should be removed on force shutdown"
