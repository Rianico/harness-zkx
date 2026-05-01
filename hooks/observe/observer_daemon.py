# /// script
# dependencies = ["pydantic"]
# ///
"""
Observer daemon for continuous learning system.

Sleeps until signaled or interval elapsed, processes observations,
and spawns observer agent with structured payload.
"""
from __future__ import annotations

import json
import os
import signal
import sys
import threading
import traceback
from collections import defaultdict
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Support both standalone script execution and module import
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import config as config_module
except ImportError:
    from hooks.observe import config as config_module

# Log file for daemon operations
LOG_FILE = Path.home() / ".claude" / "hooks" / "observe" / "daemon.log"


def log_info(message: str) -> None:
    """Write info message to daemon log file with timestamp."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] INFO: {message}\n")
    except Exception:
        pass


def log_error(message: str) -> None:
    """Write error message to daemon log file with timestamp."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] ERROR: {message}\n")
    except Exception:
        pass


def log_exception(context: str) -> None:
    """Log exception with full traceback."""
    log_error(f"{context}: {traceback.format_exc()}")

# Global state for daemon
_wake_callback: Callable[[], None] | None = None
_state_callback: Callable[[str], None] | None = None
_sleep_interval: int = 300  # Default 5 minutes
_shutdown_state: dict[str, Any] = {}
_shutdown_requested: bool = False
_lock_acquired: bool = False
_current_homunculus_dir: Path | None = None
_wake_event: threading.Event = threading.Event()
_signal_handlers_installed: bool = False
_interval_timer: threading.Thread | None = None
_interval_timer_stop: threading.Event = threading.Event()


# Install signal handlers at module import time (from main thread only)
def _install_signal_handlers_if_main() -> None:
    """Install signal handlers if we're in the main thread."""
    global _signal_handlers_installed
    if threading.current_thread() is threading.main_thread():
        if not _signal_handlers_installed:
            _install_signal_handlers()
            _signal_handlers_installed = True


def _install_signal_handlers() -> None:
    """Actually install the signal handlers."""
    def handle_sigusr1(_signum: int, _frame: Any) -> None:
        """Handle SIGUSR1 - wake up daemon."""
        log_info("SIGUSR1 received - waking up")
        _wake_event.set()
        if _wake_callback:
            _wake_callback()

    def handle_sigterm(_signum: int, _frame: Any) -> None:
        """Handle SIGTERM - graceful shutdown."""
        log_info("SIGTERM received - initiating shutdown")
        _wake_event.set()  # Also wake up to handle shutdown
        handle_shutdown_signal()

    try:
        signal.signal(signal.SIGUSR1, handle_sigusr1)
        signal.signal(signal.SIGTERM, handle_sigterm)
        log_info("Signal handlers installed for SIGUSR1 and SIGTERM")
    except (ValueError, OSError) as e:
        log_error(f"Failed to install signal handlers: {e}")


# Try to install signal handlers when module is imported
_install_signal_handlers_if_main()


# =============================================================================
# Cursor Management
# =============================================================================


def read_cursor(project_dir: Path) -> dict[str, Any]:
    """
    Read cursor position from file.

    Args:
        project_dir: Path to the project directory.

    Returns:
        Cursor data with 'line' and 'updated_at' keys.
        Returns line 0 if file doesn't exist or is malformed.
    """
    cursor_file = project_dir / ".observer-cursor"

    if not cursor_file.exists():
        return {"line": 0, "updated_at": ""}

    try:
        with open(cursor_file) as f:
            data = json.load(f)
        if isinstance(data.get("line"), int):
            return data
        return {"line": 0, "updated_at": ""}
    except (json.JSONDecodeError, OSError):
        return {"line": 0, "updated_at": ""}


def update_cursor(project_dir: Path, line: int) -> None:
    """
    Update cursor position after processing.

    Args:
        project_dir: Path to the project directory.
        line: The new line position (1-indexed line count).
    """
    cursor_file = project_dir / ".observer-cursor"

    # Ensure parent directory exists
    cursor_file.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "line": line,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    with open(cursor_file, "w") as f:
        json.dump(data, f)


def get_new_observations(project_dir: Path) -> list[dict[str, Any]]:
    """
    Get observations after cursor position.

    Args:
        project_dir: Path to the project directory.

    Returns:
        List of observations that haven't been processed yet.
    """
    observations_file = project_dir / "observations.jsonl"

    if not observations_file.exists():
        return []

    cursor = read_cursor(project_dir)
    start_line = cursor.get("line", 0)

    observations = []
    with open(observations_file) as f:
        for line_num, line in enumerate(f, start=1):
            if line_num > start_line:
                try:
                    obs = json.loads(line.strip())
                    observations.append(obs)
                except json.JSONDecodeError:
                    continue

    return observations


# =============================================================================
# Observation Grouping
# =============================================================================


def group_observations_by_session(
    observations_file: Path,
) -> dict[str, list[dict[str, Any]]]:
    """
    Group observations by session_id.

    Args:
        observations_file: Path to observations.jsonl file.

    Returns:
        Dict mapping session_id to list of observations.
        Observations without session_id go to "unknown".
        Observations within each session sorted by timestamp (asc),
        then event type order (tool_start < tool_complete < other).
    """
    if not observations_file.exists():
        return {}

    groups: dict[str, list[dict]] = defaultdict(list)

    with open(observations_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obs = json.loads(line)
                session = obs.get("session", "unknown")
                # Handle null session
                if session is None:
                    session = "unknown"
                groups[str(session)].append(obs)
            except json.JSONDecodeError:
                continue

    if not groups:
        return {}

    # Sort each group by timestamp, then event order
    event_order = {"tool_start": 0, "tool_complete": 1}
    for session in groups:
        groups[session].sort(
            key=lambda o: (
                o.get("timestamp", ""),
                event_order.get(o.get("event"), 2),
            )
        )

    return dict(groups)


def build_session_payload(observations_file: Path) -> dict[str, Any]:
    """
    Build structured JSON payload for observer agent.

    Args:
        observations_file: Path to observations.jsonl file.

    Returns:
        Payload with sessions list and metadata.
    """
    groups = group_observations_by_session(observations_file)

    sessions = []
    total_count = 0
    project_id = ""

    for session_id, events in groups.items():
        total_count += len(events)
        # Get project_id from first event if available
        if events and not project_id:
            project_id = events[0].get("project_id", "")

        sessions.append({
            "session_id": session_id,
            "events": events,
        })

    return {
        "sessions": sessions,
        "processed_count": total_count,
        "project_id": project_id,
    }


# =============================================================================
# Singleton Daemon
# =============================================================================


def _is_process_running(pid: int) -> bool:
    """Check if a process with given PID is running."""
    try:
        # Send signal 0 to check if process exists
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        # Process doesn't exist
        return False
    except PermissionError:
        # Process exists but we don't have permission to signal it
        # This means the process IS running
        return True
    except OSError:
        # Other errors - assume process doesn't exist
        return False


def try_acquire_lock(homunculus_dir: Path) -> bool:
    """
    Try to acquire the daemon lock.

    Creates PID file and lock file atomically.
    Cleans up stale PID files.

    Args:
        homunculus_dir: Path to the homunculus data directory.

    Returns:
        True if lock acquired, False if another instance is running.
    """
    global _lock_acquired, _current_homunculus_dir

    pid_file = homunculus_dir / ".observer.pid"
    lock_file = homunculus_dir / ".observer.lock"

    # Ensure directory exists
    homunculus_dir.mkdir(parents=True, exist_ok=True)

    # Check for existing PID file
    if pid_file.exists():
        try:
            with open(pid_file) as f:
                existing_pid = int(f.read().strip())

            # Check if process is still running
            if _is_process_running(existing_pid):
                log_info(f"Lock held by running process PID {existing_pid}")
                return False
            else:
                # Stale PID file - clean it up
                log_info(f"Cleaning stale PID file (was PID {existing_pid})")
                pid_file.unlink()
        except (ValueError, OSError):
            # Malformed PID file - clean it up
            log_info("Cleaning malformed PID file")
            pid_file.unlink()

    # Try to create lock file atomically
    # Using exclusive creation
    try:
        # Create lock file
        with open(lock_file, "x") as f:
            f.write(str(os.getpid()))

        # Create PID file
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))

        _lock_acquired = True
        _current_homunculus_dir = homunculus_dir
        log_info(f"Lock acquired (PID {os.getpid()})")
        return True
    except FileExistsError:
        # Lock file already exists - another instance is starting
        log_error("Lock file exists - another instance is starting")
        return False


def release_lock(homunculus_dir: Path) -> None:
    """
    Release the daemon lock.

    Removes PID file and lock file.

    Args:
        homunculus_dir: Path to the homunculus data directory.
    """
    global _lock_acquired, _current_homunculus_dir

    pid_file = homunculus_dir / ".observer.pid"
    lock_file = homunculus_dir / ".observer.lock"

    try:
        if pid_file.exists():
            pid_file.unlink()
    except OSError:
        pass

    try:
        if lock_file.exists():
            lock_file.unlink()
    except OSError:
        pass

    _lock_acquired = False
    _current_homunculus_dir = None
    log_info("Lock released")


def force_shutdown(timeout_seconds: int = 5) -> None:
    """
    Force shutdown after timeout.

    Args:
        timeout_seconds: Seconds to wait before forcing shutdown (reserved for future use).
    """
    _ = timeout_seconds  # Mark as intentionally unused (reserved for future implementation)
    global _lock_acquired, _current_homunculus_dir

    if _current_homunculus_dir:
        release_lock(_current_homunculus_dir)


# =============================================================================
# Signal Handling
# =============================================================================


def setup_signal_handlers() -> Any:
    """
    Set up signal handlers for SIGUSR1 and SIGTERM.

    Returns:
        The SIGUSR1 handler that was registered, or None if not in main thread.
    """
    _install_signal_handlers_if_main()
    return signal.getsignal(signal.SIGUSR1)


def signal_wake(pid: int) -> None:
    """
    Send SIGUSR1 to wake the daemon.

    Args:
        pid: PID of the daemon process.
    """
    try:
        os.kill(pid, signal.SIGUSR1)
    except OSError:
        pass


def handle_shutdown_signal(sig: int = 0) -> None:
    """
    Handle shutdown signal (SIGTERM).

    Preserves state and cleans up.

    Args:
        sig: The signal number (unused, for API compatibility).
    """
    _ = sig  # Mark as intentionally unused
    global _shutdown_requested, _lock_acquired, _current_homunculus_dir

    log_info("Shutdown signal received")
    _shutdown_requested = True

    # Save shutdown state if any
    if _shutdown_state and _current_homunculus_dir:
        state_file = _current_homunculus_dir / ".observer-shutdown-state.json"
        try:
            with open(state_file, "w") as f:
                json.dump(_shutdown_state, f)
            log_info(f"Shutdown state saved to {state_file}")
        except OSError as e:
            log_error(f"Failed to save shutdown state: {e}")

    # Release lock
    if _lock_acquired and _current_homunculus_dir:
        release_lock(_current_homunculus_dir)


def set_shutdown_state(state: dict[str, Any]) -> None:
    """
    Set state to preserve during shutdown.

    Args:
        state: State dictionary to preserve.
    """
    global _shutdown_state
    _shutdown_state = state


def set_wake_callback(callback: Callable[[], None]) -> None:
    """
    Set the callback to invoke when waking up.

    Also starts an interval timer that calls the callback periodically.

    Args:
        callback: Function to call on wake.
    """
    global _wake_callback, _interval_timer

    _wake_callback = callback

    if callback is None:
        # Stop the interval timer if callback is cleared
        _stop_interval_timer()
    else:
        # Start interval timer if not already running
        if _interval_timer is None or not _interval_timer.is_alive():
            _start_interval_timer()


def _start_interval_timer() -> None:
    """Start the interval timer thread."""
    global _interval_timer, _interval_timer_stop

    _interval_timer_stop.clear()

    def timer_loop():
        while not _interval_timer_stop.is_set():
            # Wait for a short time then check, instead of waiting for the full interval
            # This allows the interval to be changed dynamically
            elapsed = 0
            while elapsed < _sleep_interval and not _interval_timer_stop.is_set():
                wait_time = min(0.5, _sleep_interval - elapsed)
                if _interval_timer_stop.wait(timeout=wait_time):
                    return  # Stop was requested
                elapsed += wait_time

            if _interval_timer_stop.is_set():
                break

            # Call the wake callback
            if _wake_callback:
                _wake_callback()

    _interval_timer = threading.Thread(target=timer_loop, daemon=True)
    _interval_timer.start()


def _stop_interval_timer() -> None:
    """Stop the interval timer thread."""
    global _interval_timer_stop
    _interval_timer_stop.set()


def set_state_callback(callback: Callable[[str], None]) -> None:
    """
    Set the callback to track daemon state changes.

    Args:
        callback: Function to call with state name.
    """
    global _state_callback
    _state_callback = callback


def set_sleep_interval(seconds: int) -> None:
    """
    Set the sleep interval in seconds.

    Args:
        seconds: Sleep interval in seconds.
    """
    global _sleep_interval
    _sleep_interval = seconds


def get_sleep_interval() -> int:
    """
    Get the current sleep interval in seconds.

    Returns:
        Sleep interval in seconds.
    """
    return _sleep_interval


def get_default_sleep_interval() -> int:
    """
    Get the default sleep interval (5 minutes = 300 seconds).

    Returns:
        Default sleep interval in seconds.
    """
    return 300


def load_sleep_interval_from_config(config_file: Path) -> int:
    """
    Load sleep interval from config file.

    Args:
        config_file: Path to config.properties file.

    Returns:
        Sleep interval in seconds.
    """
    if not config_file.exists():
        return get_default_sleep_interval()

    try:
        with open(config_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("run_interval_minutes="):
                    minutes = int(line.split("=", 1)[1].strip())
                    return minutes * 60
    except (OSError, ValueError):
        pass

    return get_default_sleep_interval()


def interruptible_sleep(seconds: int, event: threading.Event | None = None) -> None:
    """
    Sleep that can be interrupted by signal or event.

    Args:
        seconds: Maximum seconds to sleep.
        event: Optional event to wait on for interruption.
    """
    import time

    # Clear the wake event before sleeping
    _wake_event.clear()

    # Wait on both the provided event (if any) and the global wake event
    # This allows signals to interrupt regardless of which event is provided
    start_time = time.monotonic()

    while True:
        elapsed = time.monotonic() - start_time
        if elapsed >= seconds:
            break

        remaining = seconds - elapsed

        # Check if external event is set
        if event and event.is_set():
            break

        # Check if wake event is set (from signal)
        if _wake_event.is_set():
            break

        # Wait on both events simultaneously
        # Use a smaller polling interval for faster response
        wait_time = min(0.05, remaining)
        _wake_event.wait(timeout=wait_time)
        if event:
            event.wait(timeout=0.001)  # Quick check

    # Call wake callback after sleep completes (interval-based wake)
    # This is called for both signal-interrupted and interval-based wakes
    if _wake_callback:
        _wake_callback()


# =============================================================================
# Processing Functions
# =============================================================================


def get_projects_with_observations(homunculus_dir: Path) -> list[str]:
    """
    Get list of projects that have observations files.

    Args:
        homunculus_dir: Path to the homunculus data directory.

    Returns:
        List of project IDs that have observations.
    """
    projects_dir = homunculus_dir / "projects"
    if not projects_dir.exists():
        return []

    project_ids = []
    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir():
            obs_file = project_dir / "observations.jsonl"
            if obs_file.exists():
                project_ids.append(project_dir.name)

    return project_ids


def process_project(project_dir: Path) -> dict[str, Any]:
    """
    Process observations for a single project.

    Updates cursor after processing.

    Args:
        project_dir: Path to the project directory.

    Returns:
        Mock result from observer agent.
    """
    observations_file = project_dir / "observations.jsonl"
    project_id = project_dir.name

    if not observations_file.exists():
        log_info(f"No observations file for project {project_id}")
        return {"processed_count": 0, "cursor_position": 0}

    try:
        # Count total lines
        with open(observations_file) as f:
            line_count = sum(1 for _ in f)

        log_info(f"Processing project {project_id}: {line_count} observations")

        # Update cursor
        update_cursor(project_dir, line_count)

        result = {
            "instincts_created": [],
            "instincts_updated": [],
            "promotions": [],
            "processed_count": line_count,
            "cursor_position": line_count,
        }

        log_info(f"Project {project_id} processed: {result}")
        return result
    except Exception as e:
        log_exception(f"Error processing project {project_id}")
        return {"processed_count": 0, "cursor_position": 0, "error": str(e)}


def process_all_projects(
    homunculus_dir: Path,
    callback: Callable[[str], None] | None = None,
) -> None:
    """
    Process all projects with observations.

    Args:
        homunculus_dir: Path to the homunculus data directory.
        callback: Optional callback to call with project_id for each project processed.
    """
    projects = get_projects_with_observations(homunculus_dir)

    for project_id in projects:
        project_dir = homunculus_dir / "projects" / project_id
        process_project(project_dir)

        if callback:
            callback(project_id)


def start_processing_cycle(homunculus_dir: Path) -> None:
    """
    Start a processing cycle.

    Goes through states: idle -> processing -> idle

    Args:
        homunculus_dir: Path to the homunculus data directory.
    """
    global _state_callback

    log_info("Starting processing cycle")
    if _state_callback:
        _state_callback("idle")

    if _state_callback:
        _state_callback("processing")

    try:
        process_all_projects(homunculus_dir)
        log_info("Processing cycle completed")
    except Exception as e:
        log_exception("Error in processing cycle")

    if _state_callback:
        _state_callback("idle")


def run_daemon(
    homunculus_dir: Path,
    wake_callback: Callable[[], None] | None = None,
) -> None:
    """
    Main daemon loop.

    Sleeps until signaled or interval elapsed, then processes observations.

    Args:
        homunculus_dir: Path to the homunculus data directory.
        wake_callback: Optional callback when daemon wakes up.
    """
    global _wake_callback, _state_callback, _shutdown_requested

    log_info(f"Daemon starting (PID {os.getpid()}, interval {_sleep_interval}s)")
    log_info(f"Homunculus dir: {homunculus_dir}")

    if wake_callback:
        _wake_callback = wake_callback

    # Set up signal handlers
    setup_signal_handlers()
    log_info("Signal handlers installed")

    # Ensure user config exists before starting
    config_module.ensure_user_config(homunculus_dir)

    # Try to acquire lock
    if not try_acquire_lock(homunculus_dir):
        log_error("Failed to acquire lock - another instance is running")
        return

    try:
        cycle_count = 0
        while not _shutdown_requested:
            # Sleep until signaled or interval elapsed
            if _state_callback:
                _state_callback("idle")

            log_info(f"Sleeping for {_sleep_interval}s...")
            interruptible_sleep(_sleep_interval)

            if _shutdown_requested:
                log_info("Shutdown requested during sleep")
                break

            # Process observations
            cycle_count += 1
            log_info(f"Wake event #{cycle_count}")
            if _state_callback:
                _state_callback("processing")

            try:
                projects = get_projects_with_observations(homunculus_dir)
                log_info(f"Found {len(projects)} projects with observations")
                process_all_projects(homunculus_dir)
                log_info(f"Processing cycle #{cycle_count} completed")
            except Exception as e:
                log_exception(f"Error in processing cycle #{cycle_count}")

    finally:
        log_info(f"Daemon shutting down after {cycle_count} cycles")
        release_lock(homunculus_dir)


def stop_daemon() -> None:
    """
    Signal the daemon to stop.

    Sets the shutdown flag.
    """
    global _shutdown_requested
    _shutdown_requested = True


def reset_daemon_state() -> None:
    """
    Reset all global daemon state.

    Used for testing to ensure clean state between tests.
    """
    global _wake_callback, _state_callback, _sleep_interval
    global _shutdown_state, _shutdown_requested, _lock_acquired
    global _current_homunculus_dir, _signal_handlers_installed

    # Stop the interval timer
    _stop_interval_timer()

    # Reset all state
    _wake_callback = None
    _state_callback = None
    _sleep_interval = 300
    _shutdown_state = {}
    _shutdown_requested = False
    _lock_acquired = False
    _current_homunculus_dir = None
    _signal_handlers_installed = False

    # Clear events
    _wake_event.clear()
    _interval_timer_stop.set()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Observer daemon for continuous learning")
    parser.add_argument("--interval", type=int, default=300, help="Sleep interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run one processing cycle then exit")
    args = parser.parse_args()

    homunculus_dir = config_module.get_homunculus_dir()

    if args.interval != 300:
        set_sleep_interval(args.interval)

    if args.once:
        # Single processing cycle
        log_info("Running single processing cycle")
        try_acquire_lock(homunculus_dir)
        try:
            process_all_projects(homunculus_dir)
        finally:
            release_lock(homunculus_dir)
    else:
        # Run daemon loop
        run_daemon(homunculus_dir)
