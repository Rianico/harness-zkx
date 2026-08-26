#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""Verify CLI global options are present in scraped markdown output.

Deterministic eval for docs-scraper CLI standards (EDD). Checks:

- Every ``*.md`` under ``output_dir`` contains ``Global Options`` header
  or ``-C <path>`` string (or ``-C`` with path-like usage).
- For worktrunk output, the ``wt merge`` page contains both ``--no-squash``
  and ``-C``.

Exit 0 on pass, non-zero with a missing-flags report on fail.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def has_global_marker(content: str) -> bool:
    """Return True if content contains Global Options marker."""
    return "Global Options" in content or "-C <path>" in content


def has_basic_flags(content: str) -> bool:
    """Return True if basic automation/global flags appear (broad check)."""
    return "-C" in content


def is_merge_candidate(path: Path, content: str) -> bool:
    """Heuristic for worktrunk wt merge page."""
    name = path.name.lower()
    if "merge" in name:
        return True
    # content-based fallback — matches `wt merge` heading or title
    lowered = content.lower()
    return "wt merge" in lowered or "wt-merge" in lowered


def collect_md_files(output_dir: Path) -> list[Path]:
    """Recursively collect ``*.md`` files under output_dir."""
    if output_dir.is_file() and output_dir.suffix == ".md":
        return [output_dir]
    if not output_dir.is_dir():
        return []
    return sorted(output_dir.rglob("*.md"))


def check_output_dir(output_dir: Path) -> tuple[bool, list[str]]:
    """Check output_dir and return (passed, error_lines)."""
    errors: list[str] = []

    md_files = collect_md_files(output_dir)
    if not md_files:
        return False, [f"No *.md files found under {output_dir}"]

    # 1) Every md must contain Global Options or -C <path>
    missing_global: list[Path] = []
    for f in md_files:
        try:
            content = f.read_text(encoding="utf-8")
        except Exception as e:
            errors.append(f"{f}: failed to read ({e})")
            continue
        if not has_global_marker(content):
            missing_global.append(f)

    if missing_global:
        errors.append("Missing Global Options marker in:")
        for f in missing_global:
            # show relative if possible
            try:
                rel = f.relative_to(output_dir) if output_dir.is_dir() else f
            except ValueError:
                rel = f
            errors.append(f"  - {rel}")

    # 2) Worktrunk-specific: if any merge-like file exists, it must have --no-squash and -C
    # Detect worktrunk context: output_dir name contains worktrunk OR any file mentions wt merge
    is_worktrunk_context = "worktrunk" in output_dir.name.lower()
    merge_files: list[Path] = []
    for f in md_files:
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        if is_merge_candidate(f, content):
            merge_files.append(f)
        if "wt merge" in content.lower():
            is_worktrunk_context = True

    if is_worktrunk_context or merge_files:
        # need at least one merge file to check; if none found but
        # context is worktrunk, check all files for wt merge
        if not merge_files:
            # fallback: treat any file containing wt merge as merge file
            for f in md_files:
                try:
                    c = f.read_text(encoding="utf-8")
                except Exception:
                    continue
                if "wt merge" in c.lower():
                    merge_files.append(f)
        # if still none and worktrunk context, require that at least one file has --no-squash and -C
        if is_worktrunk_context and not merge_files:
            # check if any file in worktrunk context has required flags
            found = False
            for f in md_files:
                try:
                    c = f.read_text(encoding="utf-8")
                except Exception:
                    continue
                if "--no-squash" in c and has_basic_flags(c):
                    found = True
                    break
            if not found:
                errors.append(
                    "Worktrunk check failed: no file contains "
                    "--no-squash and -C (expected wt merge page)"
                )

        for mf in merge_files:
            try:
                c = mf.read_text(encoding="utf-8")
            except Exception as e:
                errors.append(f"{mf}: failed to read for worktrunk check ({e})")
                continue
            missing: list[str] = []
            if "--no-squash" not in c:
                missing.append("--no-squash")
            if not has_basic_flags(c):
                missing.append("-C")
            if missing:
                try:
                    rel = mf.relative_to(output_dir) if output_dir.is_dir() else mf
                except ValueError:
                    rel = mf
                errors.append(f"Worktrunk merge file {rel} missing: {', '.join(missing)}")

    passed = len(errors) == 0
    return passed, errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify CLI global options in scraped markdown output.",
        epilog="Exit 0 if Global Options / -C present; non-zero otherwise.",
    )
    _ = parser.add_argument(
        "output_dir",
        type=Path,
        help="Output directory (or file) containing scraped *.md files",
    )
    _ = parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    output_dir: Path = args.output_dir
    verbose: bool = args.verbose

    if verbose:
        print(f"Checking {output_dir} ...")

    passed, errors = check_output_dir(output_dir)

    if passed:
        print(f"PASS: {output_dir} — Global Options and basic flags present")
        if verbose:
            md_files = collect_md_files(output_dir)
            print(f"  Checked {len(md_files)} md file(s)")
        sys.exit(0)
    else:
        print(f"FAIL: {output_dir} — missing flags", file=sys.stderr)
        for line in errors:
            print(f"  {line}", file=sys.stderr)
        # also suggest fix pointer
        print("\nHint: see skills/docs-scraper/references/cli-scrape-standards.md", file=sys.stderr)
        print(
            "Expected: Global Options header or '-C <path>' "
            "in every *.md; wt merge must have --no-squash and -C",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
