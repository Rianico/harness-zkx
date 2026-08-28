#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""self-check: phase-0 admission gate for every dispatched worktree subagent.

Verifies the subagent is inside the correct copy worktree on the correct
branch — never the base branch directory (the session worktree on the parent
branch). Exit 0 = safe to edit; exit 1 = wrong worktree, agent must edit
nothing and return BLOCKED with the printed hint.

Checks, in order:
  1. cwd is inside a git repository.
  2. cwd is the expected worktree path (equal or a subdirectory) — when the
     expected path is passed. Catches the base branch dir / sibling worktree.
  3. git branch --show-current at cwd equals the expected branch.
  4. cwd is a registered worktree (wt list / git worktree list) whose branch
     matches — cross-checks against the worktree registry.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from _lib import (  # pyright: ignore[reportImplicitRelativeImport]
    current_branch,
    ensure_git_repo,
    print_err,
    wt_list,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Verify cwd is the expected worktree on the expected branch",
    )
    parser.add_argument("branch", help="Expected branch (e.g. feat/<slug>--auth)")
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Expected absolute worktree path (default: cwd)",
    )
    return parser.parse_args(argv)


def where_am_i() -> str:
    """Human-readable '<path> on branch <branch>' for the actual cwd."""
    cwd: Path = Path.cwd().resolve()
    try:
        branch: str = current_branch(cwd)
    except RuntimeError:
        branch = "<unknown>"
    for w in wt_list(cwd):
        wpath: Path | None = Path(w.path).resolve() if w.path else None
        if wpath is not None and (wpath == cwd or cwd.is_relative_to(wpath)):
            return f"{wpath} on branch {w.branch}"
    return f"{cwd} on branch {branch}"


def main(argv: list[str] | None = None) -> None:
    args: argparse.Namespace = parse_args(argv)
    expected_branch: str = args.branch.strip()
    if not expected_branch:
        print_err("use: self_check.py <branch> [expected-path]")
        sys.exit(1)

    try:
        ensure_git_repo()
    except RuntimeError as e:
        print_err(f"SELF-CHECK FAIL: {e}")
        sys.exit(1)

    cwd: Path = Path.cwd().resolve()

    # 1. Path check — cwd must be the expected worktree (or a subdir of it).
    expected_path: Path | None = Path(args.path).resolve() if args.path else None
    if expected_path is not None and not (
        cwd == expected_path or cwd.is_relative_to(expected_path)
    ):
        print_err(
            "\n".join(
                [
                    f"SELF-CHECK FAIL: cwd {cwd} is not the expected worktree {expected_path} (expected branch {expected_branch}).",
                    "  You are in the wrong directory — likely the base branch directory.",
                    f"  Move to the copy worktree: cd {expected_path}",
                    "  Do NOT edit anything here. Report BLOCKED with this hint.",
                ]
            )
        )
        sys.exit(1)

    # 2. Branch check at cwd.
    try:
        actual_branch: str = current_branch(cwd)
    except RuntimeError as e:
        print_err(f"SELF-CHECK FAIL: {e}")
        sys.exit(1)
    if actual_branch != expected_branch:
        print_err(
            "\n".join(
                [
                    f"SELF-CHECK FAIL: {where_am_i()} — expected branch {expected_branch} at {expected_path or cwd}.",
                    "  Wrong worktree — this looks like the base branch directory.",
                    "  Move to the copy worktree and re-run before touching any file.",
                    "  Do NOT edit anything here. Report BLOCKED with this hint.",
                ]
            )
        )
        sys.exit(1)

    # 3. Registry cross-check — cwd must be a registered worktree on that branch.
    registered: bool = False
    for w in wt_list(cwd):
        wpath: Path | None = Path(w.path).resolve() if w.path else None
        if (
            wpath is not None
            and (wpath == cwd or cwd.is_relative_to(wpath))
            and w.branch == expected_branch
        ):
            registered = True
            break
    if not registered:
        print_err(
            "\n".join(
                [
                    f"SELF-CHECK FAIL: {where_am_i()} is not a registered worktree for branch {expected_branch} — wrong directory (base branch dir or stray checkout).",
                    "  Do NOT edit anything here. Report BLOCKED with this hint.",
                ]
            )
        )
        sys.exit(1)

    print(f"ok: in {cwd} on branch {actual_branch} — correct worktree")


if __name__ == "__main__":
    main()
