"""Pytest fixtures for harness-audit tests."""

import sys
from pathlib import Path

scripts_path = (
    Path(__file__).parent.parent.parent / "skills" / "harness-audit" / "scripts"
).resolve()
if str(scripts_path) not in sys.path:
    sys.path.insert(0, str(scripts_path))
