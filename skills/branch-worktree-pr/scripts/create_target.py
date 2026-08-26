#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""create-target: make parent branch in place and verify."""

# ruff: noqa: I001,E402

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure sibling _lib is importable when run as script (uv run scripts/...)
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from _lib import current_branch, print_err, run, wt_list  # pyright: ignore[reportImplicitRelativeImport]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Create target branch in place and verify",
        epilog="Stay in session cwd; validates via git and wt list.",
    )
    _ = parser.add_argument("branch", help="Target branch feat/<name> or map/<name>")
    _ = parser.add_argument(
        "base",
        nargs="?",
        default="origin/main",
        help="Git base (default origin/main)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args: argparse.Namespace = parse_args(argv)
    branch: str = args.branch
    base: str = args.base
    if not branch.strip():
        print_err("use: create_target.py <branch> [base]")
        sys.exit(1)

    print(f"-> git switch -c {branch} {base}")
    result = run(["git", "switch", "-c", branch, base])
    if result.returncode != 0:
        print_err(f"git switch failed: {result.stderr or result.stdout}")
        sys.exit(1)

    try:
        cur: str = current_branch()
    except RuntimeError as e:
        print_err(str(e))
        sys.exit(1)
    if cur != branch:
        print_err(f"branch check failed: current {cur} != {branch}")
        sys.exit(1)

    # Verify via wt list that current worktree matches
    try:
        worktrees = wt_list()
        current_entries = [w for w in worktrees if w.is_current]
        if current_entries:
            cw = current_entries[0]
            # Normalize: if wt not available fallback is path-based, still check branch
            if cw.branch and cw.branch != branch:
                print_err(f"wt list does not show {branch} as current (found {cw.branch})")
                # Show list for debugging but not fatal if wt missing? Keep strict per spec.
                sys.exit(1)
        else:
            # Fallback: ensure at least one worktree path matches cwd
            cwd_resolved: Path = Path.cwd().resolve()
            matched: bool = any(
                Path(w.path).resolve() == cwd_resolved and w.branch == branch for w in worktrees
            )
            if not matched and worktrees:
                print_err(f"wt list does not show {branch} as current")
                for w in worktrees:
                    print_err(f"  {w.branch} @ {w.path} current={w.is_current}")
                sys.exit(1)
    except RuntimeError as e:
        # wt/git list failed — report but allow if git branch already verified
        print_err(f"warning: wt list check skipped: {e}")

    print(f"ok: on branch {branch} at {Path.cwd()}")


if __name__ == "__main__":
    main()
