#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "pydantic"]
# ///
"""
Status command for continuous learning system.

Displays all instincts with confidence scores, domains, and triggers.

Eval 5.1: status Command
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports
_project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(_project_root))

from hooks.observe.instinct_manager import InstinctManager


def get_homunculus_dir() -> Path:
    """Get the homunculus data directory."""
    home = Path(os.environ.get("HOME", "~")).expanduser()
    return home / ".claude" / "lsz" / "homunculus"


def main() -> int:
    """Main entry point for status command."""
    parser = argparse.ArgumentParser(description="Show instincts status")
    parser.add_argument("--project", help="Filter by project ID")
    parser.add_argument("--scope", choices=["project", "global"], help="Filter by scope")
    parser.add_argument("--domain", help="Filter by domain")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    homunculus_dir = get_homunculus_dir()
    manager = InstinctManager(homunculus_dir)

    # List instincts
    instincts = manager.list_instincts(project_id=args.project, scope=args.scope)

    # Filter by domain if specified
    if args.domain:
        instincts = [i for i in instincts if i["frontmatter"].get("domain") == args.domain]

    if args.json:
        output = {
            "instincts": [
                {
                    "id": i["frontmatter"]["id"],
                    "trigger": i["frontmatter"]["trigger"],
                    "confidence": i["frontmatter"]["confidence"],
                    "domain": i["frontmatter"]["domain"],
                    "scope": i["frontmatter"]["scope"],
                    "project_id": i["frontmatter"]["project_id"],
                    "evidence_count": i["frontmatter"].get("evidence_count", 0),
                }
                for i in instincts
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        if not instincts:
            print("No instincts found.")
            return 0

        for i in instincts:
            fm = i["frontmatter"]
            print(f"- {fm['id']}")
            print(f"  Trigger: {fm['trigger']}")
            print(f"  Confidence: {fm['confidence']}")
            print(f"  Domain: {fm['domain']}")
            print(f"  Scope: {fm['scope']}")
            print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
