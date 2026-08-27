#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""merge-copy: thin router — wt merge then detect conflict vs gate.

Deterministic: wt merge -C <absolute-path> --stage tracked --yes avoids
cd issues (wt switch never cds in pi bash) and avoids staging .lsz/.pi.
Headless note: when rebase hits conflict, fixer must use
  GIT_EDITOR=true GIT_SEQUENCE_EDITOR=true git -C <path> rebase --continue
This script only detects and exits — it does not rebase or fix hunks.
Hunk work belongs to fixer via resolving-merge-conflicts skill.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from _lib import print_err, run  # pyright: ignore[reportImplicitRelativeImport]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Merge copy worktree into target; detect conflict vs gate",
    )
    _ = parser.add_argument("copy_path", help="Absolute path to copy worktree")
    _ = parser.add_argument("target_branch", help="Target branch map/<name> or main")
    return parser.parse_args(argv)


def git_porcelain(cwd: Path) -> list[str]:
    result = run(["git", "status", "--porcelain"], cwd=cwd)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def git_status_text(cwd: Path) -> str:
    result = run(["git", "status"], cwd=cwd)
    return (result.stdout or "") + (result.stderr or "")


def main(argv: list[str] | None = None) -> None:
    args: argparse.Namespace = parse_args(argv)
    copy_path: Path = Path(args.copy_path).resolve()
    target: str = args.target_branch

    if not copy_path.is_dir():
        print_err(f"copy folder not found: {copy_path}")
        sys.exit(1)
    if not target.strip():
        print_err("use: merge_copy.py <copy-path> <target-branch>")
        sys.exit(1)

    br = run(["git", "branch", "--show-current"], cwd=copy_path)
    copy_branch: str = br.stdout.strip()
    if not copy_branch:
        print_err(f"could not read branch in {copy_path}")
        sys.exit(1)

    print(f"-> merge {copy_branch} ({copy_path}) into {target}")
    # Absolute path + --stage tracked — keeps .lsz/.pi out, avoids cd bug
    result = run(["wt", "merge", "-C", str(copy_path), "--stage", "tracked", target, "--yes"])
    if result.returncode == 0:
        print(f"ok: merged {copy_branch} into {target}")
        return

    # Non-zero — print wt output, then classify gate vs conflict
    print(result.stdout[-2000:] if result.stdout else "", file=sys.stderr)
    print(result.stderr[-2000:] if result.stderr else "", file=sys.stderr)

    status_text: str = git_status_text(copy_path)
    porcelain: list[str] = git_porcelain(copy_path)

    rebase_markers = [
        "rebase in progress",
        "You are currently rebasing",
        "Unmerged paths",
        "fix conflicts and then run",
        "CONFLICT",
        "Rebase",
        "incomplete",
    ]
    has_rebase = any(m in status_text for m in rebase_markers)
    has_unmerged = any(
        line.startswith("UU") or line.startswith("AA") or line.startswith("DU") or line.startswith("DD")
        for line in porcelain
    )
    needs_fixer = has_rebase or has_unmerged

    if needs_fixer:
        print_err(f"conflict: rebase incomplete in {copy_path} — needs fixer")
        print_err(f"  copy={copy_path} branch={copy_branch} target={target}")
        print_err(f"  dispatch fixer: Resolve merge conflicts in copy at {copy_path}")
        # Headless hint for fixer (not run here):
        # GIT_EDITOR=true GIT_SEQUENCE_EDITOR=true git -C <copy-path> rebase --continue
        sys.exit(2)

    print_err("gate: merge failed but no rebase/conflict markers — pre-merge gate may have failed")
    print_err(f"  copy={copy_path} branch={copy_branch} target={target}")
    print_err("  check gate output above; fix gate inside copy then retry")
    sys.exit(result.returncode or 1)


if __name__ == "__main__":
    main()
