# Phase 2: Observer Daemon - RED Phase Summary

## Status: COMPLETE

## Tests Created

### Test Files (43 tests total)
- `tests/continuous-learning/phase2/__init__.py`
- `tests/continuous-learning/phase2/test_cursor_management.py` (11 tests)
- `tests/continuous-learning/phase2/test_observation_grouping.py` (11 tests)
- `tests/continuous-learning/phase2/test_singleton_daemon.py` (11 tests)
- `tests/continuous-learning/phase2/test_signal_handling.py` (10 tests)

### Test Fixtures
- `tests/continuous-learning/fixtures/observations.jsonl` (1500 lines)
- `tests/continuous-learning/fixtures/cursor.json`
- `tests/continuous-learning/fixtures/sessions/user_correction.json`
- `tests/continuous-learning/fixtures/sessions/repeated_workflow.json`
- `tests/continuous-learning/fixtures/sessions/error_resolution.json`
- `tests/continuous-learning/fixtures/generate_fixtures.py` (regeneration script)

### Conftest Updates
Added Phase 2 fixtures to `tests/continuous-learning/conftest.py`:
- `sample_observations_file`
- `sample_cursor_file`
- `sample_cursor_data`
- `sample_session_user_correction`
- `sample_session_repeated_workflow`
- `sample_session_error_resolution`
- `daemon_pid_file`
- `daemon_lock_file`
- `config_file`
- `sample_config_content`

## Eval Criteria Coverage

| Eval | Tests |
|------|-------|
| 2.1 Cursor Management | `test_cursor_management.py` - read, update, create, filtering |
| 2.2 Observation Grouping | `test_observation_grouping.py` - session grouping, ordering, truncated fields |
| 2.3 Singleton Daemon | `test_singleton_daemon.py` - single instance, stale PID, lock, shutdown |
| 2.4 Signal Handling | `test_signal_handling.py` - SIGUSR1 wake, sleep, interval fallback |

## Test Execution Results

```
collected 43 items
FAILED (43 failures)
```

All tests fail with `ImportError: cannot import name 'observer_daemon' from 'hooks.observe'` - expected for RED phase.

## Implementation Required

Create `hooks/observe/observer_daemon.py` with:
- `read_cursor(project_dir)` - Read cursor position from file
- `update_cursor(project_dir, line)` - Update cursor position
- `get_new_observations(project_dir)` - Get observations after cursor
- `group_observations_by_session(observations_file)` - Group by session_id
- `build_session_payload(observations_file)` - Build JSON payload for agent
- `try_acquire_lock(homunculus_dir)` - Singleton lock acquisition
- `release_lock(homunculus_dir)` - Lock release
- `handle_shutdown_signal(sig)` - Graceful shutdown
- `setup_signal_handlers()` - SIGUSR1/SIGTERM handlers
- `signal_wake(pid)` - Send wake signal
- `run_daemon()` - Main daemon loop
