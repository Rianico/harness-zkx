"""Pytest configuration for branch-worktree-pr script tests."""

import sys
from pathlib import Path

SCRIPTS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "skills" / "branch-worktree-pr" / "scripts"
)
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
