"""Shared import path for gh-router tests.

Sibling modules (`_github`, `_check`, ...) import each other as top-level
modules and reach `lib/range_authority.py` the same way. The one runtime
`sys.path` shim lives in `pr.py` (the CLI entry, for direct `python pr.py`
runs), so pytest sets both entries here instead of relying on per-module
shims (retired by #266-t3c).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
LIB_DIR = REPO_ROOT / "skills/gh-router/lib"

for _entry in (str(PR_SCRIPTS), str(LIB_DIR)):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)
