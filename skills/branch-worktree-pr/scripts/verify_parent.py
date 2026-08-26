#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""verify-parent: run parent heavy gate and check clean status."""

# ruff: noqa: I001,E402

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from _lib import git_status_clean, print_err, read_gate, run, run_gate  # pyright: ignore[reportImplicitRelativeImport]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Run parent heavy gate and check clean status",
    )
    return parser.parse_args(argv if argv is not None else [])


def main(argv: list[str] | None = None) -> None:
    if argv is not None and len(argv) == 1 and argv[0] in ("-h", "--help"):
        print("use: verify_parent.py", file=sys.stderr)
        print("run parent heavy gate and check clean status", file=sys.stderr)
        sys.exit(0)
    # Also support sys.argv handling
    if argv is None and len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("use: verify_parent.py", file=sys.stderr)
        print("run parent heavy gate and check clean status", file=sys.stderr)
        sys.exit(0)
    # Parse (no required args)
    _ = parse_args(argv)

    # Gate via read_gate (auto-scaffold if missing)
    gate: str | None = None
    try:
        gate = read_gate()
    except FileNotFoundError as e:
        print_err(str(e))
        sys.exit(1)
    except ValueError as e:
        print_err(str(e))
        sys.exit(1)

    if gate:
        print(f"-> gate from .config/wt.toml: {gate}")
        result = run_gate(gate)
        print(result.stdout[-2000:] if result.stdout else "")
        if result.stderr:
            print(result.stderr[-2000:], file=sys.stderr)
        if result.returncode != 0:
            print_err("gate failed")
            sys.exit(1)
    else:
        # Fallback (should not happen — read_gate scaffolds). Kept for safety.
        for cmd_str in ["npm run typecheck", "npm test", "npm run build"]:
            print(f"-> {cmd_str}")
            # Shell not used; split for list execution not needed as fallback is legacy
            # Use shell via run_gate for consistency (trusted fallback)
            res = run_gate(cmd_str)
            print(res.stdout[-2000:] if res.stdout else "")
            if res.returncode != 0:
                print_err(f"{cmd_str} failed")
                if res.stderr:
                    print(res.stderr[-2000:], file=sys.stderr)
                sys.exit(1)

    # git diff --check (typed list, no shell)
    diff = run(["git", "diff", "--check"])
    out: str = (diff.stdout or "") + (diff.stderr or "")
    if out.strip() and diff.returncode != 0:
        print_err("git diff --check found issues:")
        print_err(out)
        sys.exit(1)
    # Note: git diff --check returns 0 when clean, 1 when whitespace errors;
    # output empty means clean even if returncode 0.

    # git status clean check, allow .lsz/tmp
    is_clean: bool
    bad: list[str]
    is_clean, bad = git_status_clean()
    if not is_clean:
        print_err("git status not clean (only .lsz/tmp allowed):")
        for line in bad:
            print_err(line)
        sys.exit(1)

    print("ok: parent gate passed and status clean")


if __name__ == "__main__":
    main()
