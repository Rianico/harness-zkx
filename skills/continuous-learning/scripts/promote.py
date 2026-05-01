#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "pydantic"]
# ///
"""
Promote command for continuous learning system.

Promotes a project-scoped instinct to global scope.

Eval 5.4: promote Command
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

from hooks.observe.agent_runner import Promotion
from hooks.observe.instinct_manager import InstinctManager


def get_homunculus_dir() -> Path:
    """Get the homunculus data directory."""
    home = Path(os.environ.get("HOME", "~")).expanduser()
    return home / ".claude" / "lsz" / "homunculus"


def main() -> int:
    """Main entry point for promote command."""
    parser = argparse.ArgumentParser(description="Promote instinct to global")
    parser.add_argument("instinct_id", help="The instinct ID to promote")
    parser.add_argument("--force", action="store_true", help="Bypass criteria checks")
    parser.add_argument("--reason", help="Reason for promotion")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen")
    parser.add_argument("--check", action="store_true", help="Check eligibility only")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    homunculus_dir = get_homunculus_dir()
    manager = InstinctManager(homunculus_dir)

    # Check eligibility
    is_eligible, reason = manager.check_promotion_eligibility(args.instinct_id)

    if args.check:
        if args.json:
            print(json.dumps({
                "instinct_id": args.instinct_id,
                "eligible": is_eligible,
                "reason": reason,
            }, indent=2))
        else:
            status = "ELIGIBLE" if is_eligible else "NOT ELIGIBLE"
            print(f"Instinct '{args.instinct_id}': {status}")
            print(f"  Reason: {reason}")
        return 0 if is_eligible else 1

    if not args.force and not is_eligible:
        if args.json:
            print(json.dumps({
                "instinct_id": args.instinct_id,
                "promoted": False,
                "reason": reason,
            }, indent=2))
        else:
            print(f"Cannot promote '{args.instinct_id}': {reason}")
            print("Use --force to bypass eligibility checks.")
        return 1

    if args.dry_run:
        if args.json:
            print(json.dumps({
                "instinct_id": args.instinct_id,
                "promoted": False,
                "dry_run": True,
                "message": f"Would promote '{args.instinct_id}' to global scope",
            }, indent=2))
        else:
            print(f"Dry run: Would promote '{args.instinct_id}' to global scope.")
            print(f"  Reason: {args.reason or 'User requested'}")
        return 0

    # Perform promotion
    promotion = Promotion(
        id=args.instinct_id,
        reason=args.reason or "User requested promotion",
    )

    global_path = manager.promote_instinct(promotion, force=args.force)

    if global_path:
        if args.json:
            print(json.dumps({
                "instinct_id": args.instinct_id,
                "promoted": True,
                "global_path": str(global_path),
                "reason": promotion.reason,
            }, indent=2))
        else:
            print(f"Successfully promoted '{args.instinct_id}' to global scope.")
            print(f"  Path: {global_path}")
        return 0
    else:
        if args.json:
            print(json.dumps({
                "instinct_id": args.instinct_id,
                "promoted": False,
                "reason": "Promotion failed - instinct may not exist",
            }, indent=2))
        else:
            print(f"Failed to promote '{args.instinct_id}'. Instinct may not exist.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
