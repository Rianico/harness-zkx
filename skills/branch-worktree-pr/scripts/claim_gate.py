#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""claim-gate: check ticket is ready then claim it."""

# ruff: noqa: I001,E402

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from _lib import print_err, run  # pyright: ignore[reportImplicitRelativeImport]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Check ticket is unblocked and unassigned, then claim it",
    )
    _ = parser.add_argument("issue", help="Issue number without #")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    # Validate .scratch hint for pluggable tracker
    if Path(".scratch").is_dir():
        print(
            "hint: .scratch exists — tracker may be local markdown, not GitHub; "
            "claim_gate uses gh issue view",
            file=sys.stderr,
        )
    # Custom handling for help / argc to keep legacy behavior (1 arg required)
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) == 1 and argv[0] in ("-h", "--help"):
        print("use: claim_gate.py <issue-number>", file=sys.stderr)
        print(
            "check ticket is unblocked and unassigned, then claim it",
            file=sys.stderr,
        )
        sys.exit(0)
    if len(argv) != 1:
        print("use: claim_gate.py <issue-number>", file=sys.stderr)
        print(
            "check ticket is unblocked and unassigned, then claim it",
            file=sys.stderr,
        )
        sys.exit(1)

    args: argparse.Namespace = parse_args(argv)
    issue: str = args.issue.lstrip("#")
    if not issue.isdigit():
        print_err(f"issue-number must be digits, got: {issue}")
        sys.exit(1)

    # Fetch issue data via typed list args (no shell injection)
    result = run(
        [
            "gh",
            "issue",
            "view",
            issue,
            "--json",
            "number,title,assignees,labels,blockedBy",
        ]
    )
    if result.returncode != 0:
        print_err(f"failed to read issue {issue}: {result.stdout} {result.stderr}")
        sys.exit(1)

    out: str = result.stdout.strip()
    # Strip leading warning lines if any
    idx: int = out.find("{")
    if idx > 0:
        out = out[idx:]
    try:
        data: object = json.loads(out)
    except json.JSONDecodeError as e:
        print_err(f"could not parse issue data: {e}\n{result.stdout}")
        sys.exit(1)

    if not isinstance(data, dict):
        print_err(f"unexpected issue data shape: {type(data)}")
        sys.exit(1)

    # Typed extraction with concrete types (no Any)
    assignees_raw: object = data.get("assignees")
    blocked_raw: object = data.get("blockedBy")

    assignees: list[object] = assignees_raw if isinstance(assignees_raw, list) else []
    blocked_by: list[object] = blocked_raw if isinstance(blocked_raw, list) else []

    if assignees:
        names: list[str] = []
        for item in assignees:
            if isinstance(item, dict):
                login: object = item.get("login")
                if isinstance(login, str):
                    names.append(login)
        name_str: str = ", ".join(names) if names else str(len(assignees))
        print_err(f"ticket {issue} already assigned to {name_str} — not ready")
        sys.exit(1)

    if blocked_by:
        nums: list[str] = []
        for item in blocked_by:
            if isinstance(item, dict):
                n: object = item.get("number")
                if n is not None:
                    nums.append(str(n))
                else:
                    nums.append(str(item))
            else:
                nums.append(str(item))
        print_err(f"ticket {issue} is blocked by {nums} — not ready")
        sys.exit(1)

    # Claim
    claim = run(["gh", "issue", "edit", issue, "--add-assignee", "@me"])
    if claim.returncode != 0:
        print_err(f"failed to claim {issue}: {claim.stdout} {claim.stderr}")
        sys.exit(1)

    print(f"claimed ticket {issue}")


if __name__ == "__main__":
    main()
