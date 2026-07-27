#!/usr/bin/env python3
"""Validate that a flavor's style.css covers all required classes from the rendering contract.

Usage:
    uv run python3 scripts/validate_flavor.py <flavor_dir>    # Check a flavor
    uv run python3 scripts/validate_flavor.py --list          # List required items
    uv run python3 scripts/validate_flavor.py kami            # Check by name (resolved to flavors/<name>)
"""

import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.absolute()
SKILL_DIR = SCRIPT_DIR.parent
CONTRACT_PATH = SKILL_DIR / "references" / "flavors" / "RENDERING-CONTRACT.md"


def parse_required_classes(contract_path):
    """Extract required items from the machine-readable section."""
    text = contract_path.read_text()

    start = text.find("<!-- required-classes:start -->")
    end = text.find("<!-- required-classes:end -->")

    if start == -1 or end == -1:
        print("ERROR: Machine-readable class manifest not found in contract.")
        sys.exit(1)

    manifest = text[start + len("<!-- required-classes:start -->"):end]
    items = []
    for line in manifest.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            items.append(line)
    return items


def check_flavor(flavor_dir, required):
    """Check a flavor's style.css for each required selector or property."""
    style_path = Path(flavor_dir) / "style.css"
    if not style_path.exists():
        print(f"ERROR: style.css not found at {style_path}")
        sys.exit(1)

    css = style_path.read_text()
    comments_stripped = re.sub(r'/\*.*?\*/', '', css, flags=re.DOTALL)

    # Extract :root block for token checking
    root_match = re.search(r':root\s*\{(.*?)\}', css, re.DOTALL)
    root_vars = root_match.group(1) if root_match else ""

    missing = []
    found = 0

    for item in required:
        if item.startswith("--"):
            # CSS custom property: must appear in :root block
            if item not in root_vars:
                missing.append(item)
            else:
                found += 1
        elif item.startswith("[") or item.startswith("::"):
            # Attribute selector or pseudo-element: check in CSS
            if item not in comments_stripped:
                missing.append(item)
            else:
                found += 1
        else:
            # CSS class or element selector: check in CSS
            if item not in css:
                missing.append(item)
            else:
                found += 1

    return missing, found


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate a flavor's style.css against the rendering contract"
    )
    parser.add_argument("flavor", nargs="?", default=None,
                        help="Flavor name or path to flavor directory")
    parser.add_argument("--list", action="store_true",
                        help="List all required classes and exit")
    args = parser.parse_args()

    required = parse_required_classes(CONTRACT_PATH)

    if args.list:
        print(f"Required items ({len(required)} total):\n")
        for item in required:
            if item.startswith("--"):
                label = f"  {item}\t\t(design token)"
            elif item.startswith("[") or item.startswith("::"):
                label = f"  {item}\t\t(attribute/pseudo)"
            else:
                label = f"  {item}\t\t(CSS class)"
            print(label)
        return

    if args.flavor is None:
        parser.print_help()
        sys.exit(1)

    # Resolve flavor path
    if Path(args.flavor).is_dir():
        flavor_dir = args.flavor
    else:
        candidate = SKILL_DIR / "references" / "flavors" / args.flavor
        if candidate.is_dir():
            flavor_dir = str(candidate)
        else:
            print(f"ERROR: flavor '{args.flavor}' not found as a directory.")
            sys.exit(1)

    missing, found = check_flavor(flavor_dir, required)
    total = len(required)

    if missing:
        print(f"✘ {flavor_dir}/style.css is missing {len(missing)}/{total} required items:\n")
        for item in missing:
            item_type = "token" if item.startswith("--") else "selector"
            print(f"  ✘  {item}  ({item_type})")
        print(f"\n  Found: {found}/{total}")
        sys.exit(1)
    else:
        print(f"✓  {flavor_dir}/style.css covers all {total} required items.")


if __name__ == "__main__":
    main()
