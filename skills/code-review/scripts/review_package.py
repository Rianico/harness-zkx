#!/usr/bin/env python3
"""Pre-packages git diff, log, stat, and specification into a single review bundle.

Inspired by obra/superpowers review-package. Enables LLM orchestrator and subagents
to inspect the complete change context in a single read_file operation.
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _run_git(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    """Run a git command and return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def find_repo_root(cwd: Path | None = None) -> Path:
    """Find the root directory of the current git repository."""
    code, out, err = _run_git(["rev-parse", "--show-toplevel"], cwd=cwd)
    if code != 0:
        raise RuntimeError(f"Not a git repository: {err}")
    return Path(out)


def resolve_default_base(repo_root: Path, head_ref: str = "HEAD") -> str:
    """Determine the default base branch or commit for review.

    Tries merge-base against origin/main, main, origin/master, master,
    or falls back to HEAD~1.
    """
    candidates = ["origin/main", "main", "origin/master", "master"]
    for candidate in candidates:
        code, out, _ = _run_git(["merge-base", candidate, head_ref], cwd=repo_root)
        if code == 0 and out:
            return candidate

    # Fallback to HEAD~1 if commit has parents
    code, out, _ = _run_git(["rev-parse", "--verify", f"{head_ref}~1"], cwd=repo_root)
    if code == 0 and out:
        return f"{head_ref}~1"

    # Single root commit fallback
    code, out, _ = _run_git(["rev-parse", head_ref], cwd=repo_root)
    if code == 0 and out:
        return out
    return "HEAD"


def build_review_package(
    base: str | None = None,
    head: str = "HEAD",
    spec_path: str | Path | None = None,
    out_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> Path:
    """Generate a single consolidated review bundle file.

    Returns the Path to the written bundle file.
    """
    if repo_root is None:
        repo_root = find_repo_root()

    if base is None:
        base = resolve_default_base(repo_root, head)

    # Validate head ref
    code, head_sha, err = _run_git(["rev-parse", "--verify", head], cwd=repo_root)
    if code != 0:
        raise ValueError(f"Invalid head revision '{head}': {err}")

    # Validate base ref
    code, base_sha, err = _run_git(["rev-parse", "--verify", base], cwd=repo_root)
    if code != 0:
        raise ValueError(f"Invalid base revision '{base}': {err}")

    # Validate common ancestor exists
    code, merge_base, err = _run_git(["merge-base", base, head], cwd=repo_root)
    if code != 0 or not merge_base:
        raise ValueError(f"No common ancestor between base '{base}' and head '{head}': {err}")

    # Retrieve commit log
    code, commit_log, err = _run_git(["log", "--oneline", f"{base}..{head}"], cwd=repo_root)
    if code != 0:
        commit_log = f"(Error reading git log: {err})"

    # Retrieve diffstat
    code, diff_stat, err = _run_git(["diff", "--stat", f"{base}...{head}"], cwd=repo_root)
    if code != 0:
        diff_stat = f"(Error reading diffstat: {err})"

    # Retrieve extended context unified diff (-U10)
    code, full_diff, err = _run_git(["diff", "-U10", f"{base}...{head}"], cwd=repo_root)
    if code != 0:
        raise RuntimeError(f"Error computing git diff: {err}")

    # Compute digest over diff
    diff_digest = hashlib.sha256(full_diff.encode("utf-8")).hexdigest()

    # Read spec if provided
    spec_content = ""
    spec_resolved_path: Path | None = None
    if spec_path is not None:
        p = Path(spec_path)
        if not p.is_absolute():
            p = repo_root / p
        if p.exists() and p.is_file():
            spec_content = p.read_text(encoding="utf-8")
            spec_resolved_path = p
        else:
            spec_content = f"(Warning: spec file not found at {spec_path})"

    # Build bundle sections
    now_iso = datetime.now(UTC).isoformat()
    base7 = base_sha[:7]
    head7 = head_sha[:7]

    bundle_lines = [
        "=" * 80,
        f"REVIEW PACKAGE: {base}..{head} ({base7}..{head7})",
        f"Generated: {now_iso}",
        f"Base SHA: {base_sha} ({base})",
        f"Head SHA: {head_sha} ({head})",
        f"Merge Base: {merge_base}",
        f"Diff Digest (SHA256): {diff_digest}",
        "=" * 80,
        "",
        "-" * 80,
        "COMMIT LOG",
        "-" * 80,
        commit_log if commit_log else "(No commits in range)",
        "",
        "-" * 80,
        "CHANGED FILES SUMMARY",
        "-" * 80,
        diff_stat if diff_stat else "(No changes in range)",
        "",
        "-" * 80,
        "EXTENDED CONTEXT DIFF (-U10)",
        "-" * 80,
        full_diff if full_diff else "(Diff is empty)",
        "",
    ]

    if spec_content:
        spec_label = str(spec_resolved_path) if spec_resolved_path else str(spec_path)
        bundle_lines.extend(
            [
                "-" * 80,
                f"SPECIFICATION / INTENT CONTRACT: {spec_label}",
                "-" * 80,
                spec_content,
                "",
            ]
        )

    bundle_text = "\n".join(bundle_lines)

    # Determine destination
    if out_path is None:
        target_dir = repo_root / ".lane" / "reviews"
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = target_dir / f"review-{base7}..{head7}.diff"
    else:
        dest = Path(out_path)
        if not dest.is_absolute():
            dest = repo_root / dest
        dest.parent.mkdir(parents=True, exist_ok=True)

    _ = dest.write_text(bundle_text, encoding="utf-8")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Pre-package git diff, log, stat, and spec into a unified review bundle."
    )
    _ = parser.add_argument(
        "base",
        nargs="?",
        default=None,
        help="Base revision or branch (defaults to merge-base with main/master or HEAD~1)",
    )
    _ = parser.add_argument(
        "head",
        nargs="?",
        default="HEAD",
        help="Head revision (defaults to HEAD)",
    )
    _ = parser.add_argument(
        "--spec",
        type=str,
        default=None,
        help="Path to requirement spec, issue description, or design contract",
    )
    _ = parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Custom destination path for the review bundle",
    )
    _ = parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the generated bundle directly to stdout instead of only writing to file",
    )

    args = parser.parse_args()

    try:
        repo_root = find_repo_root()
        bundle_file = build_review_package(
            base=args.base,
            head=args.head,
            spec_path=args.spec,
            out_path=args.out,
            repo_root=repo_root,
        )
        if args.stdout:
            _ = sys.stdout.write(bundle_file.read_text(encoding="utf-8"))
        else:
            print(f"Review bundle written to: {bundle_file}")
        return 0
    except Exception as exc:
        print(f"Error generating review package: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
