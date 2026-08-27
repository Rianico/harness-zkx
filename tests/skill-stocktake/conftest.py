"""Pytest configuration for skill-stocktake tests."""

import sys
from pathlib import Path

# Add scripts directory to Python path for imports
# tests/skill-stocktake/ -> skills/skill-stocktake/scripts/
scripts_dir = Path(__file__).parent.parent.parent / "skills" / "skill-stocktake" / "scripts"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))
