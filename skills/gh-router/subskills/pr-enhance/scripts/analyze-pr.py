#!/usr/bin/env python3
"""PR drafting-schema probe (diff analysis retired).

Change facts come from the git-diff-digest brief; this script keeps only the
read-only drafting-schema seam (`--print-template`).
"""

import json
import os
import sys
from pathlib import Path


def _resolve_template_path(cwd: Path | None = None) -> Path | None:
    """Read-only drafting-schema resolution: repo template first, else the canonical.

    Never creates or installs anything; GH_ROUTER_TEMPLATE_SRC overrides the canonical
    path, mirroring install-template.sh.
    """
    repo = cwd or Path.cwd()
    repo_template = repo / ".github" / "pull_request_template.md"
    if repo_template.is_file():
        return repo_template.resolve()
    override = os.environ.get("GH_ROUTER_TEMPLATE_SRC")
    canonical = (
        Path(override)
        if override
        else Path(__file__).resolve().parents[3] / "references" / "pull_request_template.md"
    )
    return canonical.resolve() if canonical.is_file() else None


if __name__ == "__main__":
    if "--print-template" in sys.argv[1:]:
        resolved = _resolve_template_path()
        if resolved is None:
            print(
                "error: no PR template found in repo .github/ or at the canonical path",
                file=sys.stderr,
            )
            sys.exit(3)
        print(resolved)
        sys.exit(0)
    # Retired: diff analysis moved to the git-diff-digest brief. Keep exit 0 with a
    # JSON pointer so legacy callers probing the old seam still get JSON, not a trace.
    print(
        json.dumps(
            {
                "error": (
                    "diff analysis retired; brief the range with "
                    "git-diff-digest scripts/brief.py '<base>...HEAD' --pr --yaml"
                )
            }
        )
    )
