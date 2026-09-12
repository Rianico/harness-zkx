"""Pytest fixtures for the herdr skill tests (herdr-pane helper)."""

import sys
from pathlib import Path

scripts_path = (Path(__file__).parent.parent.parent / "skills" / "herdr" / "scripts").resolve()
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))
