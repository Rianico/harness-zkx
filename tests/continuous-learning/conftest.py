"""
Pytest fixtures for continuous learning system tests.
"""

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


# Base directories
PROJECT_ROOT = Path(__file__).parent.parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "continuous-learning" / "fixtures"


@pytest.fixture
def temp_home(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary home directory for testing."""
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    original_home = os.environ.get("HOME")
    os.environ["HOME"] = str(home)
    yield home
    if original_home:
        os.environ["HOME"] = original_home
    else:
        os.environ.pop("HOME", None)


@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary project directory for testing."""
    project_dir = tmp_path / "my-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    original_cwd = os.getcwd()
    os.chdir(project_dir)
    yield project_dir
    os.chdir(original_cwd)


@pytest.fixture
def fake_git_repo_with_remote(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a fake git repo with remote URL."""
    repo_path = tmp_path / "git-repo-remote"
    repo_path.mkdir(parents=True, exist_ok=True)
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)

    # Create config with remote URL
    config_content = """[core]
	repositoryformatversion = 0
[remote "origin"]
	url = https://github.com/user/test-project.git
	fetch = +refs/heads/*:refs/remotes/origin/*
"""
    (git_dir / "config").write_text(config_content)

    yield repo_path


@pytest.fixture
def fake_git_repo_with_credentials(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a fake git repo with embedded credentials in remote URL."""
    repo_path = tmp_path / "git-repo-creds"
    repo_path.mkdir(parents=True, exist_ok=True)
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)

    # Create config with remote URL containing credentials
    config_content = """[core]
	repositoryformatversion = 0
[remote "origin"]
	url = https://user:secret-token@github.com/user/private-repo.git
	fetch = +refs/heads/*:refs/remotes/origin/*
"""
    (git_dir / "config").write_text(config_content)

    yield repo_path


@pytest.fixture
def fake_git_repo_no_remote(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a fake git repo without remote URL."""
    repo_path = tmp_path / "git-repo-no-remote"
    repo_path.mkdir(parents=True, exist_ok=True)
    git_dir = repo_path / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)

    # Create config without remote
    config_content = """[core]
	repositoryformatversion = 0
"""
    (git_dir / "config").write_text(config_content)

    yield repo_path


@pytest.fixture
def non_git_directory(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a non-git directory for testing global fallback."""
    dir_path = tmp_path / "non-git-dir"
    dir_path.mkdir(parents=True, exist_ok=True)
    yield dir_path


@pytest.fixture
def sample_observation() -> dict:
    """Return a sample observation payload."""
    return {
        "timestamp": "2026-04-30T10:00:00Z",
        "event": "tool_start",
        "tool": "Read",
        "input": {"file_path": "/path/to/file.py"},
        "output": None,
        "session": "test-session-123",
        "project_id": "a1b2c3d4e5f6",
        "project_name": "my-project",
        "tool_use_id": "toolu_abc123"
    }


@pytest.fixture
def sample_tool_event_pre() -> dict:
    """Return a sample PreToolUse event payload."""
    return {
        "tool_name": "Read",
        "tool_input": {"file_path": "/path/to/file.py"},
        "cwd": "/Users/test/my-project",
        "session_id": "test-session-123",
        "project_id": "a1b2c3d4e5f6"
    }


@pytest.fixture
def sample_tool_event_post() -> dict:
    """Return a sample PostToolUse event payload."""
    return {
        "tool_name": "Read",
        "tool_input": {"file_path": "/path/to/file.py"},
        "tool_result": "file contents here",
        "cwd": "/Users/test/my-project",
        "session_id": "test-session-123",
        "project_id": "a1b2c3d4e5f6"
    }


@pytest.fixture
def long_input_data() -> str:
    """Return input data exceeding 5000 characters."""
    return "x" * 10000


@pytest.fixture
def sample_observation_with_secrets() -> dict:
    """Return a sample observation containing secrets."""
    return {
        "timestamp": "2026-04-30T10:00:00Z",
        "event": "tool_complete",
        "tool": "Bash",
        "input": {
            "command": "curl -H 'Authorization: Bearer sk-proj-abcdef123456' https://api.example.com"
        },
        "output": "API_KEY=sk-12345678abcdefgh\nTOKEN=gpt_xxxxxxxxxxxxx\nPASSWORD=supersecret123",
        "session": "test-session-456",
        "project_id": "a1b2c3d4e5f6",
        "project_name": "my-project",
        "tool_use_id": "toolu_xyz789"
    }


@pytest.fixture
def secret_patterns() -> list[tuple[str, str]]:
    """Return list of (pattern, description) tuples for secret patterns."""
    return [
        ("sk-proj-abcdefghijklmnopqrstuvwxyz", "OpenAI API key"),
        ("sk-12345678abcdefgh", "API key pattern"),
        ("gpt_xxxxxxxxxxxxxxxxxxxxxxxx", "GPT token"),
        ("xoxb-123456789012-1234567890123-AbCdEfGhIjKlMnOpQrStUvWx", "Slack token"),
        ("ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "GitHub token"),
        ("AKIAIOSFODNN7EXAMPLE", "AWS access key"),
        ("wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "AWS secret key"),
    ]


@pytest.fixture
def expected_project_id_from_remote() -> str:
    """Return expected project ID for git repo with remote."""
    remote_url = "https://github.com/user/test-project.git"
    return hashlib.sha256(remote_url.encode()).hexdigest()[:12]


@pytest.fixture
def expected_project_id_from_path() -> str:
    """Return expected project ID for git repo without remote."""
    # This will be computed at test time based on actual path
    return None


@pytest.fixture
def homunculus_dir(temp_home: Path) -> Generator[Path, None, None]:
    """Create the homunculus data directory structure."""
    homunculus = temp_home / ".claude" / "lsz" / "homunculus"
    homunculus.mkdir(parents=True, exist_ok=True)

    # Create subdirectories
    (homunculus / "instincts" / "personal").mkdir(parents=True, exist_ok=True)
    (homunculus / "instincts" / "inherited").mkdir(parents=True, exist_ok=True)
    (homunculus / "projects").mkdir(parents=True, exist_ok=True)

    yield homunculus


@pytest.fixture
def project_observations_dir(homunculus_dir: Path) -> Generator[Path, None, None]:
    """Create a project-specific observations directory."""
    project_hash = "a1b2c3d4e5f6"
    project_dir = homunculus_dir / "projects" / project_hash
    project_dir.mkdir(parents=True, exist_ok=True)

    (project_dir / "instincts" / "personal").mkdir(parents=True, exist_ok=True)

    yield project_dir


# =============================================================================
# Phase 2 Fixtures - Observer Daemon
# =============================================================================

@pytest.fixture
def sample_observations_file() -> Path:
    """Return path to sample observations.jsonl fixture (1500 lines)."""
    obs_file = FIXTURES_DIR / "observations.jsonl"
    assert obs_file.exists(), f"Fixture not found: {obs_file}"
    return obs_file


@pytest.fixture
def sample_cursor_file() -> Path:
    """Return path to sample cursor.json fixture."""
    cursor_file = FIXTURES_DIR / "cursor.json"
    assert cursor_file.exists(), f"Fixture not found: {cursor_file}"
    return cursor_file


@pytest.fixture
def sample_cursor_data() -> dict:
    """Return sample cursor data."""
    return {"line": 500, "updated_at": "2026-04-30T10:30:00Z"}


@pytest.fixture
def sample_session_user_correction() -> list[dict]:
    """Return sample session with user correction pattern."""
    return [
        {"timestamp": "2026-04-30T10:00:00Z", "event": "tool_start", "tool": "Edit", "session": "correction-1"},
        {"timestamp": "2026-04-30T10:00:05Z", "event": "tool_complete", "tool": "Edit", "session": "correction-1", "output": "user_rejected: true"},
        {"timestamp": "2026-04-30T10:00:10Z", "event": "tool_start", "tool": "Read", "session": "correction-1"},
        {"timestamp": "2026-04-30T10:00:15Z", "event": "tool_complete", "tool": "Read", "session": "correction-1"},
        {"timestamp": "2026-04-30T10:00:20Z", "event": "tool_start", "tool": "Edit", "session": "correction-1"},
        {"timestamp": "2026-04-30T10:00:25Z", "event": "tool_complete", "tool": "Edit", "session": "correction-1", "output": "success"},
    ]


@pytest.fixture
def sample_session_repeated_workflow() -> list[dict]:
    """Return sample session with repeated workflow pattern."""
    from datetime import datetime, timedelta
    events = []
    base = datetime(2026, 4, 30, 11, 0, 0)
    for i in range(4):
        t = base + timedelta(minutes=i * 5)
        events.extend([
            {"timestamp": t.isoformat() + "Z", "event": "tool_start", "tool": "Read", "session": "workflow-1"},
            {"timestamp": (t + timedelta(seconds=5)).isoformat() + "Z", "event": "tool_complete", "tool": "Read", "session": "workflow-1"},
            {"timestamp": (t + timedelta(seconds=10)).isoformat() + "Z", "event": "tool_start", "tool": "Edit", "session": "workflow-1"},
            {"timestamp": (t + timedelta(seconds=15)).isoformat() + "Z", "event": "tool_complete", "tool": "Edit", "session": "workflow-1"},
            {"timestamp": (t + timedelta(seconds=20)).isoformat() + "Z", "event": "tool_start", "tool": "Bash", "session": "workflow-1"},
            {"timestamp": (t + timedelta(seconds=25)).isoformat() + "Z", "event": "tool_complete", "tool": "Bash", "session": "workflow-1"},
        ])
    return events


@pytest.fixture
def sample_session_error_resolution() -> list[dict]:
    """Return sample session with error resolution pattern."""
    return [
        {"timestamp": "2026-04-30T12:00:00Z", "event": "tool_start", "tool": "Bash", "session": "resolution-1"},
        {"timestamp": "2026-04-30T12:00:05Z", "event": "tool_complete", "tool": "Bash", "session": "resolution-1", "output": "error: command not found"},
        {"timestamp": "2026-04-30T12:00:10Z", "event": "tool_start", "tool": "Bash", "session": "resolution-1", "input": {"command": "modified command"}},
        {"timestamp": "2026-04-30T12:00:15Z", "event": "tool_complete", "tool": "Bash", "session": "resolution-1", "output": "success"},
    ]


@pytest.fixture
def daemon_pid_file(homunculus_dir: Path) -> Path:
    """Return path to daemon PID file."""
    return homunculus_dir / ".observer.pid"


@pytest.fixture
def daemon_lock_file(homunculus_dir: Path) -> Path:
    """Return path to daemon lock file."""
    return homunculus_dir / ".observer.lock"


@pytest.fixture
def config_file(homunculus_dir: Path) -> Path:
    """Return path to config file."""
    return homunculus_dir / "config.properties"


@pytest.fixture
def sample_config_content() -> str:
    """Return sample config file content."""
    return """# How many observations before signaling the daemon
signal_every_n=20

# Minimum new observations needed before spawning agent
min_observations_to_analyze=50

# Fallback interval (minutes) if no signal received
run_interval_minutes=5

# Observation retention in days
retention_days=30

# Max file size in MB before archiving
max_file_size_mb=10

# Model for observer agent
observer_model=haiku
"""


# =============================================================================
# Phase 2 Fixtures - Daemon State Reset
# =============================================================================

@pytest.fixture(autouse=True)
def reset_daemon_state():
    """Reset daemon state before each test."""
    # Import here to avoid circular imports
    try:
        from hooks.observe import observer_daemon
        observer_daemon.reset_daemon_state()
    except ImportError:
        pass
    yield
    try:
        from hooks.observe import observer_daemon
        observer_daemon.reset_daemon_state()
    except ImportError:
        pass
