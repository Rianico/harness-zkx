# Phase 2: Observer Daemon - GREEN Phase Implementation

## Status: COMPLETE

## Implementation Summary

Created `hooks/observe/observer_daemon.py` with the following components:

### 1. Cursor Management (11 tests passing)
- `read_cursor(project_dir)` - Reads cursor from `.observer-cursor` file, returns line 0 if missing/malformed
- `update_cursor(project_dir, line)` - Updates cursor with ISO 8601 timestamp
- `get_new_observations(project_dir)` - Returns observations after cursor position

### 2. Observation Grouping (11 tests passing)
- `group_observations_by_session(observations_file)` - Groups by session_id using pandas DataFrame
- `build_session_payload(observations_file)` - Builds JSON payload with sessions, metadata, and project_id
- Handles missing sessions (defaults to "unknown")
- Sorts by timestamp, with tool_start before tool_complete on equal timestamps

### 3. Singleton Daemon (11 tests passing)
- `try_acquire_lock(homunculus_dir)` - Atomic lock acquisition with PID file
- `release_lock(homunculus_dir)` - Cleans up PID and lock files
- `_is_process_running(pid)` - Checks process existence, handles PermissionError on macOS
- `force_shutdown(timeout_seconds)` - Forces cleanup
- Stale PID cleanup on startup

### 4. Signal Handling (12 tests passing)
- Module-level signal handler installation (for thread compatibility)
- `setup_signal_handlers()` - Sets up SIGUSR1 and SIGTERM handlers
- `signal_wake(pid)` - Sends SIGUSR1 to wake daemon
- `interruptible_sleep(seconds, event)` - Sleep that can be interrupted by signal or event
- Interval-based fallback timer for automatic waking
- `run_daemon(homunculus_dir, wake_callback)` - Main daemon loop

### 5. Processing Functions
- `process_project(project_dir)` - Processes observations, updates cursor
- `process_all_projects(homunculus_dir, callback)` - Iterates all projects
- `get_projects_with_observations(homunculus_dir)` - Lists projects with data
- `start_processing_cycle(homunculus_dir)` - State-tracked processing cycle

### 6. State Management
- `set_wake_callback(callback)` - Sets callback and starts interval timer
- `set_state_callback(callback)` - Tracks daemon state changes
- `set_sleep_interval(seconds)` - Configures sleep interval
- `reset_daemon_state()` - Resets all global state for testing

## Key Design Decisions

1. **Signal Handler Placement**: Signal handlers installed at module import time to work with threading tests (Python only allows signal handlers from main thread)

2. **Interval Timer**: Background thread calls wake callback on interval for fallback behavior, using short sleep increments for dynamic interval updates

3. **Process Detection**: Handles PermissionError on macOS where PID 1 cannot be signaled but is running

4. **Event-based Sleep**: Uses global `_wake_event` plus optional external event for interruptible sleep

5. **Test Isolation**: Added `reset_daemon_state()` function and autouse fixture to reset global state between tests

## Dependencies Added

Added to `pyproject.toml` dev dependencies:
- `pandas` - For observation grouping
- `pydantic` - For future schema validation

## Test Results

```
collected 74 items

tests/continuous-learning/phase1/test_detect_project.py ........
tests/continuous-learning/phase1/test_observe_hook.py ..........
tests/continuous-learning/phase1/test_secret_scrubbing.py ............
tests/continuous-learning/phase2/test_cursor_management.py ...........
tests/continuous-learning/phase2/test_observation_grouping.py .........
tests/continuous-learning/phase2/test_signal_handling.py ............
tests/continuous-learning/phase2/test_singleton_daemon.py ...........

============================== 74 passed in 2.90s ==============================
```

## Files Modified/Created

| File | Action |
|------|--------|
| `hooks/observe/observer_daemon.py` | Created |
| `hooks/observe/__init__.py` | Updated (added observer_daemon export) |
| `tests/continuous-learning/conftest.py` | Updated (added reset_daemon_state fixture) |
| `pyproject.toml` | Updated (added pandas, pydantic dev deps) |

## Next Steps (Phase 3)

The observer agent implementation should:
1. Receive structured JSON payload from daemon
2. Detect patterns (user corrections, repeated workflows, error resolutions)
3. Return structured JSON with instincts to create/update
4. Handle the actual spawning via `claude --agent observer` command
