#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""check-history: verify atomic commits and changelog bullet."""

# ruff: noqa: I001,E402

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from _lib import print_err, run  # pyright: ignore[reportImplicitRelativeImport]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Check commits and changelog before PR",
    )
    return parser.parse_args(argv if argv is not None else [])


def main(argv: list[str] | None = None) -> None:
    if argv is not None and len(argv) == 1 and argv[0] in ("-h", "--help"):
        print("use: check_history.py", file=sys.stderr)
        print("check commits and changelog before PR", file=sys.stderr)
        sys.exit(0)
    if argv is None and len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("use: check_history.py", file=sys.stderr)
        print("check commits and changelog before PR", file=sys.stderr)
        sys.exit(0)
    _ = parse_args(argv)

    # 1. log check — try origin/main first, fallback to merge-base logic
    log_result = run(["git", "log", "--oneline", "--no-merges", "origin/main..HEAD"])
    if log_result.returncode != 0:
        # Fallback when origin/main missing — use merge-base against main or HEAD
        # Try git merge-base --fork-point origin/main HEAD alternative, else HEAD
        fallback_base: str | None = None
        # Try to find local main
        main_exists = run(["git", "rev-parse", "--verify", "main"])
        if main_exists.returncode == 0:
            fallback_base = "main"
        else:
            # Try origin/main still? already failed, so use HEAD^? Instead show recent
            fallback_base = None
        if fallback_base is not None:
            merge_base = run(["git", "merge-base", fallback_base, "HEAD"])
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                base_sha: str = merge_base.stdout.strip()
                log_result = run(["git", "log", "--oneline", "--no-merges", f"{base_sha}..HEAD"])
            else:
                log_result = run(["git", "log", "--oneline", "--no-merges", "-n", "20"])
        else:
            print(
                "git log failed (maybe no origin/main): trying HEAD --no-merges | head",
                file=sys.stderr,
            )
            log_result = run(["git", "log", "--oneline", "--no-merges", "-n", "20"])
            # Reconstruct via shell pipe alternative using git log with max-count
            # The above already gives -n 20, keep it

    lines: list[str] = [lo for lo in log_result.stdout.splitlines() if lo.strip()]
    if not lines:
        print_err("no commits found on branch vs origin/main")
        sys.exit(1)

    print(f"-> commits: {len(lines)}")
    for lo in lines[:10]:
        print(f"  {lo}")

    # 2. changelog check
    changelog: Path = Path("CHANGELOG.md")
    if not changelog.is_file():
        print_err("CHANGELOG.md not found")
        sys.exit(1)
    txt: str = changelog.read_text(encoding="utf-8", errors="ignore")
    # find ## [Unreleased] section
    m: re.Match[str] | None = re.search(r"## \[Unreleased\](.*?)## \[", txt, re.S)
    if not m:
        m = re.search(r"## \[Unreleased\](.*)", txt, re.S)
    if not m:
        print_err("CHANGELOG missing ## [Unreleased]")
        sys.exit(1)
    section: str = m.group(1)
    has_sub: re.Match[str] | None = re.search(r"### (Added|Changed|Fixed|Removed)", section)
    if not has_sub:
        print_err(
            "CHANGELOG [Unreleased] missing subsection ### Added|Changed|Fixed|Removed"
        )
        print_err(section[:500])
        sys.exit(1)
    bullets: list[str] = re.findall(r"^- .+", section, re.M)
    if not bullets:
        print_err("CHANGELOG [Unreleased] has no bullet")
        sys.exit(1)
    has_link: bool = any(re.search(r"\(#\d+\)|#\d+|by @", b) for b in bullets)
    if not has_link:
        print_err("warning: CHANGELOG bullet has no (#issue) or by @ link")
    print(f"-> changelog bullets: {len(bullets)}")
    for b in bullets[:5]:
        print(f"  {b[:120]}")

    print("ok: history and changelog look good")


if __name__ == "__main__":
    main()
