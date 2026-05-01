# /// script
# dependencies = []
# ///
"""
Project detection functionality for observation hook.

Determines the project context for tool events by examining
git remotes, environment variables, and directory paths.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from hooks.observe.config import get_homunculus_dir


def get_git_remote_url(git_dir: Path) -> str | None:
    """
    Get the git remote URL from .git/config.

    Args:
        git_dir: Path to the .git directory.

    Returns:
        The remote URL or None if not found.
    """
    config_path = git_dir / "config"
    if not config_path.exists():
        return None

    with open(config_path) as f:
        content = f.read()

    # Parse git config for remote URL
    # Match [remote "origin"] followed by url = ...
    match = re.search(r'\[remote\s+"[^"]+"\]\s+url\s*=\s*(.+)', content)
    if match:
        return match.group(1).strip()
    return None


def strip_credentials_from_url(url: str) -> str:
    """
    Remove embedded credentials from a URL.

    Args:
        url: URL that may contain credentials.

    Returns:
        URL with credentials removed.
    """
    # Match pattern like https://user:password@host/...
    pattern = r"(https?://)([^:@]+:[^@]+@)?(.+)"
    match = re.match(pattern, url)
    if match:
        return f"{match.group(1)}{match.group(3)}"
    return url


def get_project_id(cwd: str | Path | None = None) -> str:
    """
    Get the project ID for the current context.

    Priority:
    1. CLAUDE_PROJECT_DIR environment variable
    2. Git remote URL (with credentials stripped)
    3. Git repository path
    4. 'global' fallback

    Args:
        cwd: Optional working directory. If None, uses Path.cwd().

    Returns:
        A 12-character project ID or 'global'.
    """
    # Check for environment variable override
    env_project = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_project:
        return hashlib.sha256(env_project.encode()).hexdigest()[:12]

    # Determine the working directory
    if cwd is None:
        cwd = Path.cwd()
    else:
        cwd = Path(cwd)

    # Check for git repository
    git_dir = cwd / ".git"
    if git_dir.exists() and git_dir.is_dir():
        # Try to get remote URL
        remote_url = get_git_remote_url(git_dir)
        if remote_url:
            # Strip credentials before hashing
            clean_url = strip_credentials_from_url(remote_url)
            return hashlib.sha256(clean_url.encode()).hexdigest()[:12]

        # No remote, use repo path
        return hashlib.sha256(str(cwd).encode()).hexdigest()[:12]

    # No project detected
    return "global"


def get_project_name(cwd: str | Path | None = None) -> str:
    """
    Get the project name for the current context.

    Priority:
    1. CLAUDE_PROJECT_DIR basename
    2. Current directory basename

    Args:
        cwd: Optional working directory. If None, uses Path.cwd().

    Returns:
        The project name or 'global'.
    """
    env_project = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_project:
        return Path(env_project).name

    # Determine the working directory
    if cwd is None:
        cwd = Path.cwd()
    else:
        cwd = Path(cwd)

    # Check if we're in a git repo
    git_dir = cwd / ".git"
    if git_dir.exists() and git_dir.is_dir():
        return cwd.name

    return "global"


def get_projects_file() -> Path:
    """Get the path to projects.json."""
    return get_homunculus_dir() / "projects.json"


def register_project(project_id: str, project_name: str, cwd: str) -> None:
    """
    Register or update a project in the projects registry.

    Args:
        project_id: The project ID (12-char hash).
        project_name: The project name.
        cwd: The current working directory.
    """
    projects_file = get_projects_file()

    # Load existing projects
    projects = {}
    if projects_file.exists():
        with open(projects_file) as f:
            projects = json.load(f)

    # Update or create project entry
    now = datetime.now(timezone.utc).isoformat()

    if project_id in projects:
        # Update existing project
        projects[project_id]["last_seen_at"] = now
        projects[project_id]["path"] = cwd
    else:
        # Create new project entry
        projects[project_id] = {
            "name": project_name,
            "path": cwd,
            "created_at": now,
            "last_seen_at": now,
        }

    # Ensure parent directory exists
    projects_file.parent.mkdir(parents=True, exist_ok=True)

    # Write back
    with open(projects_file, "w") as f:
        json.dump(projects, f, indent=2)


def get_project_observations_dir(project_id: str) -> Path:
    """
    Get the observations directory for a project.

    Args:
        project_id: The project ID.

    Returns:
        Path to the project's observations directory.
    """
    if project_id == "global":
        return get_homunculus_dir()

    project_dir = get_homunculus_dir() / "projects" / project_id
    return project_dir


def get_observations_file(project_id: str) -> Path:
    """
    Get the observations.jsonl file path for a project.

    Args:
        project_id: The project ID.

    Returns:
        Path to observations.jsonl.
    """
    if project_id == "global":
        return get_homunculus_dir() / "observations.jsonl"

    project_dir = get_project_observations_dir(project_id)
    return project_dir / "observations.jsonl"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Project detection utilities")
    parser.add_argument("--project-id", metavar="CWD", help="Get project ID for given directory")
    parser.add_argument("--project-name", metavar="CWD", help="Get project name for given directory")
    parser.add_argument(
        "--register",
        nargs=3,
        metavar=("PROJECT_ID", "PROJECT_NAME", "CWD"),
        help="Register a project",
    )

    args = parser.parse_args()

    if args.project_id:
        print(get_project_id(args.project_id))
    elif args.project_name:
        print(get_project_name(args.project_name))
    elif args.register:
        project_id, project_name, cwd = args.register
        register_project(project_id, project_name, cwd)
    else:
        parser.print_help()
        exit(1)
