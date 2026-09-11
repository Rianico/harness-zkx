"""Pytest configuration and fixtures for eval-gate tests."""

import sys
from pathlib import Path

# Add skills/eval-gate/scripts to sys.path
SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "eval-gate"
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
