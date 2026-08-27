"""
Tests for project detection functionality.

These tests verify that the observation hook correctly identifies
the project context for tool events.
"""

import hashlib
from pathlib import Path

import pytest


class TestProjectDetection:
    """Tests for detect-project.sh functionality."""

    def test_project_id_from_git_remote(
        self, fake_git_repo_with_remote: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Project ID should be SHA256 hash of remote URL.

        Eval 1.2: Git remote URL hashed correctly.
        """
        # Set up environment to use fake git repo
        monkeypatch.chdir(fake_git_repo_with_remote)

        # Import the module under test (will fail until implemented)
        from hooks.observe import detect_project

        result = detect_project.get_project_id()

        # Expected: SHA256("https://github.com/user/test-project.git")[:12]
        expected_remote = "https://github.com/user/test-project.git"
        expected_id = hashlib.sha256(expected_remote.encode()).hexdigest()[:12]

        assert result == expected_id, f"Expected {expected_id}, got {result}"

    def test_project_id_without_remote(
        self, fake_git_repo_no_remote: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Project ID should be SHA256 hash of repo path when no remote.

        Eval 1.2: Fallback to repo path when no remote.
        """
        monkeypatch.chdir(fake_git_repo_no_remote)

        from hooks.observe import detect_project

        result = detect_project.get_project_id()

        # Expected: SHA256(repo_path)[:12]
        expected_id = hashlib.sha256(str(fake_git_repo_no_remote).encode()).hexdigest()[:12]

        assert result == expected_id, f"Expected {expected_id}, got {result}"

    def test_project_id_with_env_override(
        self, non_git_directory: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        CLAUDE_PROJECT_DIR should take precedence.

        Eval 1.2: CLAUDE_PROJECT_DIR set case.
        """
        monkeypatch.chdir(non_git_directory)
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/custom/project/path")

        from hooks.observe import detect_project

        result = detect_project.get_project_id()

        # Expected: SHA256(env_value)[:12]
        expected_id = hashlib.sha256(b"/custom/project/path").hexdigest()[:12]

        assert result == expected_id, f"Expected {expected_id}, got {result}"

    def test_global_fallback(
        self, non_git_directory: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Should return 'global' when no project detected.

        Eval 1.2: Global fallback when no project detected.
        """
        monkeypatch.chdir(non_git_directory)
        monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)

        from hooks.observe import detect_project

        result = detect_project.get_project_id()

        assert result == "global", f"Expected 'global', got {result}"

    def test_credentials_stripped_from_remote(
        self, fake_git_repo_with_credentials: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Embedded credentials in remote URL should be stripped before hashing.

        Eval 1.2: Credentials stripped from remote URL before hashing.
        """
        monkeypatch.chdir(fake_git_repo_with_credentials)

        from hooks.observe import detect_project

        result = detect_project.get_project_id()

        # Credentials should be stripped: "https://user:secret-token@github.com/..."
        # becomes "https://github.com/..."
        expected_remote = "https://github.com/user/private-repo.git"
        expected_id = hashlib.sha256(expected_remote.encode()).hexdigest()[:12]

        assert result == expected_id, f"Expected {expected_id} (credentials stripped), got {result}"

    def test_project_name_from_directory(
        self, fake_git_repo_with_remote: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Project name should be derived from directory basename.
        """
        monkeypatch.chdir(fake_git_repo_with_remote)

        from hooks.observe import detect_project

        result = detect_project.get_project_name()

        assert result == "git-repo-remote", f"Expected 'git-repo-remote', got {result}"

    def test_project_name_with_env_override(
        self, non_git_directory: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Project name should use CLAUDE_PROJECT_DIR basename when set.
        """
        monkeypatch.chdir(non_git_directory)
        monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/custom/project/path")

        from hooks.observe import detect_project

        result = detect_project.get_project_name()

        assert result == "path", f"Expected 'path', got {result}"


class TestProjectRegistry:
    """Tests for project registry management."""

    def test_project_registered_on_first_observation(
        self, homunculus_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        New projects should be registered in projects.json.
        """
        from hooks.observe import detect_project

        project_id = "test123abc456"
        project_name = "my-test-project"
        cwd = "/path/to/my-test-project"

        detect_project.register_project(project_id, project_name, cwd)

        projects_file = homunculus_dir / "projects.json"
        assert projects_file.exists(), "projects.json should be created"

        import json

        with open(projects_file) as f:
            projects = json.load(f)

        assert project_id in projects, f"Project {project_id} should be registered"
        assert projects[project_id]["name"] == project_name
        assert projects[project_id]["path"] == cwd

    def test_project_metadata_updated(
        self, homunculus_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Project metadata should be updated on subsequent observations.
        """
        from hooks.observe import detect_project

        project_id = "test123abc456"

        # First registration
        detect_project.register_project(project_id, "my-project", "/path/to/project")

        # Second registration with different path
        detect_project.register_project(project_id, "my-project", "/different/path")

        import json

        with open(homunculus_dir / "projects.json") as f:
            projects = json.load(f)

        # last_seen_at should be updated
        assert "last_seen_at" in projects[project_id]
