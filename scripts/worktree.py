#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""Root dispatcher: forwards to skills/branch-worktree-pr/scripts/worktree.py."""

# ruff: noqa: I001,E402

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

# Resolve skill dispatcher location
_SKILL_WORKTREE: Path = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "branch-worktree-pr"
    / "scripts"
    / "worktree.py"
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    # Delegate parsing to skill dispatcher to keep single source
    if not _SKILL_WORKTREE.is_file():
        raise FileNotFoundError(f"skill dispatcher not found: {_SKILL_WORKTREE}")
    spec = importlib.util.spec_from_file_location("_skill_worktree", _SKILL_WORKTREE)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load spec for {_SKILL_WORKTREE}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # pyright: ignore[reportUnknownMemberType]
    parser: argparse.ArgumentParser = mod.build_parser()  # pyright: ignore[reportUnknownMemberType,reportAttributeAccessIssue]
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    if not _SKILL_WORKTREE.is_file():
        print(f"skill dispatcher not found: {_SKILL_WORKTREE}", file=sys.stderr)
        sys.exit(1)
    spec = importlib.util.spec_from_file_location("_skill_worktree_main", _SKILL_WORKTREE)
    if spec is None or spec.loader is None:
        print(f"could not load skill dispatcher: {_SKILL_WORKTREE}", file=sys.stderr)
        sys.exit(1)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_skill_worktree_main"] = mod
    spec.loader.exec_module(mod)  # pyright: ignore[reportUnknownMemberType]
    # Delegate entire argv to skill dispatcher
    mod.main(argv if argv is not None else sys.argv[1:])  # pyright: ignore[reportUnknownMemberType,reportAttributeAccessIssue]


if __name__ == "__main__":
    main()
