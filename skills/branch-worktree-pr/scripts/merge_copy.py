#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""merge-copy: merge child worktree into target, fixing conflicts inside copy only."""

# ruff: noqa: I001,E402

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from _lib import (  # pyright: ignore[reportImplicitRelativeImport]
    has_conflict_markers,
    print_err,
    read_gate,
    run,
    run_gate,  # trusted gate execution
)

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Merge copy worktree into target; fix conflicts inside copy only",
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

    # Verify copy branch
    br = run(["git", "branch", "--show-current"], cwd=copy_path)
    copy_branch: str = br.stdout.strip()
    if not copy_branch:
        print_err(f"could not read branch in {copy_path}")
        sys.exit(1)

    print(f"-> merge {copy_branch} ({copy_path}) into {target}")

    # Attempt merge via wt inside copy
    result = run(["wt", "merge", target, "--yes"], cwd=copy_path)
    if result.returncode == 0:
        print(f"ok: merged {copy_branch} into {target}")
        return

    print("merge reported conflict or check failed, fixing inside copy", file=sys.stderr)
    print(result.stdout[-2000:] if result.stdout else "", file=sys.stderr)
    print(result.stderr[-2000:] if result.stderr else "", file=sys.stderr)

    status_text: str = git_status_text(copy_path)
    porcelain: list[str] = git_porcelain(copy_path)

    needs_fix: bool = (
        "rebase in progress" in status_text
        or "You are currently rebasing" in status_text
        or "Unmerged paths" in status_text
        or any(
            line.startswith("DU")
            or line.startswith("UU")
            or line.startswith("AA")
            for line in porcelain
        )
        or any(line.startswith("M ") for line in porcelain)
    )

    if not needs_fix:
        print_err("merge failed but no conflict markers — gate may have failed")
        sys.exit(result.returncode or 1)

    print(f"-> fixing conflicts inside {copy_path} (main folder not touched)", file=sys.stderr)

    # Fix DU: deleted on one side vs changed on other -> keep deletion
    du_files: list[str] = [line[3:].strip() for line in porcelain if line.startswith("DU")]
    if du_files:
        print(f"found delete vs change files: {du_files}", file=sys.stderr)
        for f in du_files:
            if not f:
                continue
            r = run(["git", "rm", f], cwd=copy_path)
            if r.returncode != 0:
                # fallback rm file
                try:
                    (copy_path / f).unlink(missing_ok=True)
                except Exception:
                    pass
            print(f"-> git rm {f} (keep deletion)", file=sys.stderr)

    # Check for UU/AA — need to ensure no conflict markers, then add
    unmerged: list[str] = [
        line[3:].strip()
        for line in porcelain
        if line.startswith("UU") or line.startswith("AA")
    ]
    if unmerged:
        print(f"remaining unmerged files: {unmerged}", file=sys.stderr)
        for f in unmerged:
            if not f:
                continue
            fp: Path = copy_path / f
            if has_conflict_markers(fp):
                print_err(f"conflict markers remain in {f} — manual fix needed")
                sys.exit(1)
            r = run(["git", "add", f], cwd=copy_path)
            if r.returncode != 0:
                print_err(f"git add {f} failed: {r.stderr}")
                sys.exit(1)
            print(f"-> git add {f}", file=sys.stderr)

    # Also add M files if any staged need
    for line in porcelain:
        if line.startswith("M "):
            f2: str = line[3:].strip()
            if f2:
                _ = run(["git", "add", f2], cwd=copy_path)

    # Run gate inside copy before continuing (trusted gate from wt.toml)
    print("-> run gate inside copy before continuing", file=sys.stderr)
    # Prefer wt step pre-merge if available, else read_gate
    gate_result: subprocess.CompletedProcess[str] | None = None
    # Try wt step pre-merge first
    step = run(["wt", "step", "pre-merge"], cwd=copy_path)
    if step.returncode == 0:
        gate_result = step
    else:
        try:
            gate: str = read_gate(cwd=copy_path)
            print(f"-> gate from .config/wt.toml: {gate}", file=sys.stderr)
            # trusted gate — single writer .config/wt.toml; delegated to _lib
            gate_result = run_gate(gate, cwd=copy_path)
        except FileNotFoundError as e:
            print_err(str(e))
            sys.exit(1)
        except ValueError as e:
            print_err(str(e))
            sys.exit(1)

    if gate_result is not None:
        print(gate_result.stdout[-3000:] if gate_result.stdout else "")
        if gate_result.stderr:
            print(gate_result.stderr[-3000:], file=sys.stderr)
        if gate_result.returncode != 0:
            print_err(f"gate failed inside {copy_path}")
            sys.exit(1)

    # Continue rebase or merge if in progress
    status_text = git_status_text(copy_path)
    if "rebase in progress" in status_text or "You are currently rebasing" in status_text:
        print(f"-> GIT_EDITOR=true git rebase --continue inside {copy_path}", file=sys.stderr)
        env = os.environ.copy()
        env["GIT_EDITOR"] = "true"
        cont = subprocess.run(
            ["git", "rebase", "--continue"],
            capture_output=True,
            text=True,
            cwd=copy_path,
            env=env,
        )
        print(cont.stdout[-3000:] if cont.stdout else "")
        if cont.stderr:
            print(cont.stderr[-3000:], file=sys.stderr)
        if cont.returncode != 0:
            print_err("rebase --continue failed, needs manual fix inside copy")
            sys.exit(1)
    elif "All conflicts fixed but you are still merging" in status_text:
        print("-> git commit --no-edit (merge in progress)", file=sys.stderr)
        commit = run(["git", "commit", "--no-edit"], cwd=copy_path)
        print(commit.stdout[-2000:] if commit.stdout else "")
        if commit.stderr:
            print(commit.stderr[-2000:], file=sys.stderr)
        if commit.returncode != 0:
            print_err("git commit failed during merge")
            sys.exit(1)

    print("-> retry merge after fix", file=sys.stderr)
    retry = run(["wt", "merge", target, "--yes"], cwd=copy_path)
    print(retry.stdout[-3000:] if retry.stdout else "")
    if retry.stderr:
        print(retry.stderr[-3000:], file=sys.stderr)
    if retry.returncode != 0:
        print_err(f"retry merge still failed, check {copy_path}")
        sys.exit(retry.returncode or 1)

    print(f"ok: merged {copy_branch} into {target} after fix")


if __name__ == "__main__":
    main()
