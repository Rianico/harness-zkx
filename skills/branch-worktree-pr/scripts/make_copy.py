#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""make-copy: create isolated wt child and print its absolute path."""

# ruff: noqa: I001,E402

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from _lib import (  # pyright: ignore[reportImplicitRelativeImport]
    current_branch,
    ensure_dependencies,
    print_err,
    run,
    wt_list,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Create isolated worktree child and print absolute path",
    )
    parser.add_argument("child_branch", help="Child branch feat/<name>--part")
    parser.add_argument("base_branch", help="Base branch map/<name> or feat/<name>")
    _ = parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip the dependency-health probe/repair after the copy",
    )
    _ = parser.add_argument(
        "--force-deps",
        action="store_true",
        help="Run the frozen-lockfile install even when the dependency probe passes",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args: argparse.Namespace = parse_args(argv)
    child: str = args.child_branch
    base: str = args.base_branch
    if not child.strip() or not base.strip():
        print_err("use: make_copy.py <child-branch> <base-branch>")
        sys.exit(1)

    print(f"-> wt switch --create {child} --base {base} --no-cd --yes", file=sys.stderr)
    result = run(["wt", "switch", "--create", child, "--base", base, "--no-cd", "--yes"])
    if result.returncode != 0:
        print_err(f"wt switch failed: {result.stderr or result.stdout}")
        sys.exit(1)

    # Find path via wt_list exact match
    path_out: str = ""
    try:
        worktrees = wt_list()
        for w in worktrees:
            if w.branch == child:
                path_out = w.path
                break
    except RuntimeError as e:
        print_err(f"wt list failed: {e}")

    if not path_out:
        # Fallback: try git worktree list parsing via wt_list already did git fallback,
        # but also try parent dir guess for debugging
        print_err(f"copy made but could not find path for {child}")
        try:
            for w in wt_list():
                print_err(f"  {w.branch} @ {w.path}")
        except Exception as _exc:
            print_err(f"wt list debug failed: {_exc}")
        sys.exit(1)

    path_obj: Path = Path(path_out)
    if not path_obj.is_dir():
        print_err(f"copy path does not exist: {path_out}")
        sys.exit(1)

    # Verify branch in copy
    try:
        cur_copy: str = current_branch(cwd=path_obj)
    except RuntimeError as e:
        print_err(f"could not read branch in {path_out}: {e}")
        sys.exit(1)
    if cur_copy != child:
        print_err(f"copy check failed: {path_out} branch {cur_copy} != {child}")
        sys.exit(1)

    # Dependency health: `wt step copy-ignored` can copy a node_modules skeleton whose
    # symlinks and native .node bindings are broken, so the developer dies on its first test
    # run (`Cannot find module '@vitest/utils/helpers'`) before writing a line. Probe and
    # repair here, once, instead of paying a manual `pnpm install` in every task copy.
    deps_note: str = "skipped (--skip-deps)"
    if not args.skip_deps:
        deps_ok, deps_note = ensure_dependencies(path_obj, force=args.force_deps)
        if not deps_ok:
            print_err(f"dependency repair failed in {path_out}: {deps_note}")
            sys.exit(1)

    # Print absolute path to stdout (only path)
    print(str(path_obj.resolve()))
    print(f"ok: copy {child} at {path_out} (base {base}, deps: {deps_note})", file=sys.stderr)


if __name__ == "__main__":
    main()
