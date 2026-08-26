#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""worktree dispatcher: forward subcommands to phase scripts via same _lib."""

# ruff: noqa: I001,E402

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

# Also ensure root scripts path not needed; this file lives with siblings


def load_module(name: str, filename: str) -> object:
    path: Path = Path(__file__).parent / filename
    if not path.is_file():
        raise FileNotFoundError(f"module file not found: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load spec for {name} from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # pyright: ignore[reportUnknownMemberType]
    return mod


def build_parser() -> argparse.ArgumentParser:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Branch-worktree-pr dispatcher (uv run scripts/worktree.py)",
        prog="worktree.py",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_claim = sub.add_parser("claim", help="Claim ticket")
    _ = p_claim.add_argument("issue", help="Issue number")

    p_target = sub.add_parser("create-target", help="Create target branch in place")
    _ = p_target.add_argument("branch", help="Branch feat/<name> or map/<name>")
    _ = p_target.add_argument(
        "base",
        nargs="?",
        default="origin/main",
        help="Base (default origin/main)",
    )

    p_copy = sub.add_parser("make-copy", help="Create isolated copy")
    _ = p_copy.add_argument("child_branch", help="Child branch")
    _ = p_copy.add_argument("base_branch", help="Base branch")

    p_merge = sub.add_parser("merge-copy", help="Merge copy into target")
    _ = p_merge.add_argument("copy_path", help="Absolute path to copy")
    _ = p_merge.add_argument("target_branch", help="Target branch")

    _ = sub.add_parser("verify", help="Verify parent gate and clean status")
    _ = sub.add_parser("check-history", help="Check commits and changelog")

    p_pr = sub.add_parser("open-pr", help="Open PR with Closes trailer")
    _ = p_pr.add_argument("branch", help="Branch")
    _ = p_pr.add_argument("base", help="Base branch")
    _ = p_pr.add_argument("issue_number", help="Issue number")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser: argparse.ArgumentParser = build_parser()
    args: argparse.Namespace = parser.parse_args(argv)

    cmd: str = args.cmd
    # Dispatch via loading sibling modules and calling main with adjusted argv
    if cmd == "claim":
        mod = load_module("claim_gate", "claim_gate.py")
        mod.main([args.issue])  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
    elif cmd == "create-target":
        mod = load_module("create_target", "create_target.py")
        base: str = args.base
        # create_target expects [branch, base]? It handles default, but we pass explicitly
        argv2: list[str] = [args.branch]
        if base != "origin/main" or True:
            # Always pass base to preserve default handling; if caller omitted, it will be default
            argv2.append(base)
        mod.main(argv2)  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
    elif cmd == "make-copy":
        mod = load_module("make_copy", "make_copy.py")
        mod.main([args.child_branch, args.base_branch])  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
    elif cmd == "merge-copy":
        mod = load_module("merge_copy", "merge_copy.py")
        mod.main([args.copy_path, args.target_branch])  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
    elif cmd == "verify":
        mod = load_module("verify_parent", "verify_parent.py")
        mod.main([])  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
    elif cmd == "check-history":
        mod = load_module("check_history", "check_history.py")
        mod.main([])  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
    elif cmd == "open-pr":
        mod = load_module("open_pr", "open_pr.py")
        mod.main([args.branch, args.base, args.issue_number])  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
