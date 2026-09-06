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

    p_check = sub.add_parser("self-check", help="Verify cwd is the expected worktree on the expected branch")
    _ = p_check.add_argument("branch", help="Expected branch")
    _ = p_check.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Expected absolute worktree path (default: cwd)",
    )
    p_merge = sub.add_parser("merge-copy", help="Merge copy into target")
    _ = p_merge.add_argument("copy_path", help="Absolute path to copy")
    _ = p_merge.add_argument("target_branch", help="Target branch")

    _ = sub.add_parser("verify", help="Verify parent gate and clean status")
    _ = sub.add_parser("check-history", help="Check commits and changelog")

    p_pr = sub.add_parser("open-pr", help="Open PR with Closes trailer")
    _ = p_pr.add_argument("branch", help="Branch")
    _ = p_pr.add_argument("base", help="Base branch")
    _ = p_pr.add_argument("issue_number", help="Issue number")
    _ = p_pr.add_argument("--no-watch", action="store_true", help="Skip watching checks")
    _ = p_pr.add_argument("--watch-interval", type=int, default=10, help="Watch interval")
    _ = p_pr.add_argument("--fail-fast", action="store_true", help="Fail fast during watch")

    p_mpr = sub.add_parser("merge-pr", help="Merge PR and watch runs")
    _ = p_mpr.add_argument("pr", help="PR branch, number, or URL")
    _ = p_mpr.add_argument("--base", default="", help="Expected base branch")
    _ = p_mpr.add_argument("--squash", dest="strategy", action="store_const", const="squash", default="squash")
    _ = p_mpr.add_argument("--merge", dest="strategy", action="store_const", const="merge")
    _ = p_mpr.add_argument("--rebase", dest="strategy", action="store_const", const="rebase")
    _ = p_mpr.add_argument("--no-delete-branch", action="store_true")
    _ = p_mpr.add_argument("--auto", action="store_true")
    _ = p_mpr.add_argument("--admin", action="store_true")
    _ = p_mpr.add_argument("--no-watch", action="store_true")
    _ = p_mpr.add_argument("--watch-interval", type=int, default=10)
    _ = p_mpr.add_argument("--fail-fast", action="store_true")
    _ = p_mpr.add_argument("--no-post-merge-watch", dest="post_merge_watch", action="store_false")

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
    elif cmd == "self-check":
        mod = load_module("self_check", "self_check.py")
        check_args: list[str] = [args.branch]
        if args.path:
            check_args.append(args.path)
        mod.main(check_args)  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
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
        extra: list[str] = [args.branch, args.base, args.issue_number]
        if args.no_watch:
            extra.append("--no-watch")
        if args.watch_interval != 10:
            extra.extend(["--watch-interval", str(args.watch_interval)])
        if args.fail_fast:
            extra.append("--fail-fast")
        mod.main(extra)  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
    elif cmd == "merge-pr":
        mod = load_module("merge_pr", "merge_pr.py")
        extra2: list[str] = [args.pr]
        if args.base:
            extra2.extend(["--base", args.base])
        extra2.extend([f"--{args.strategy}"])
        if args.no_delete_branch:
            extra2.append("--no-delete-branch")
        if args.auto:
            extra2.append("--auto")
        if args.admin:
            extra2.append("--admin")
        if args.no_watch:
            extra2.append("--no-watch")
        if args.watch_interval != 10:
            extra2.extend(["--watch-interval", str(args.watch_interval)])
        if args.fail_fast:
            extra2.append("--fail-fast")
        if not args.post_merge_watch:
            extra2.append("--no-post-merge-watch")
        mod.main(extra2)  # pyright: ignore[reportAttributeAccessIssue,reportUnknownMemberType]
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
