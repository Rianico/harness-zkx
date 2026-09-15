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
import json
import sys
from pathlib import Path

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from _lib import print_err, run  # pyright: ignore[reportImplicitRelativeImport]

# commitlint's conventional default for `body-max-line-length`. Only enforced when the repo
# actually wires commitlint; a project without it must never be blocked by this pre-check.
BODY_MAX_LINE = 100
COMMITLINT_CONFIG_NAMES: tuple[str, ...] = (
    "commitlint.config.js",
    "commitlint.config.cjs",
    "commitlint.config.mjs",
    "commitlint.config.ts",
    ".commitlintrc",
    ".commitlintrc.json",
    ".commitlintrc.js",
    ".commitlintrc.cjs",
    ".commitlintrc.yml",
    ".commitlintrc.yaml",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Merge copy worktree into target; detect conflict vs gate",
    )
    _ = parser.add_argument("copy_path", help="Absolute path to copy worktree")
    _ = parser.add_argument("target_branch", help="Target branch map/<name> or main")
    _ = parser.add_argument(
        "--body-max-line",
        type=int,
        default=BODY_MAX_LINE,
        help=f"Commit body line budget for the pre-check (default {BODY_MAX_LINE})",
    )
    _ = parser.add_argument(
        "--skip-commitlint-precheck",
        action="store_true",
        help="Do not pre-check commit body line lengths before merging",
    )
    return parser.parse_args(argv)


def git_porcelain(cwd: Path) -> list[str]:
    result = run(["git", "status", "--porcelain"], cwd=cwd)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def git_status_text(cwd: Path) -> str:
    result = run(["git", "status"], cwd=cwd)
    return (result.stdout or "") + (result.stderr or "")


def commitlint_configured(cwd: Path) -> bool:
    """True when the repo wires commitlint — the only reason to police body line length."""
    if any((cwd / name).is_file() for name in COMMITLINT_CONFIG_NAMES):
        return True
    pkg: Path = cwd / "package.json"
    if not pkg.is_file():
        return False
    try:
        data: object = json.loads(pkg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(data, dict) and "commitlint" in data


def commit_body_offenders(cwd: Path, target: str, limit: int) -> list[str]:
    """Commits in `target..HEAD` whose body has a line longer than `limit`.

    `wt merge` squashes the task branch, concatenating every commit body into ONE message. A
    single over-long line anywhere in the task history therefore fails commitlint at merge
    time - after the developer has moved on. Surface the exact commit and line before merging.
    """
    result = run(
        ["git", "log", f"{target}..HEAD", "--no-merges", "--pretty=format:%h%x1f%B%x1e"],
        cwd=cwd,
    )
    if result.returncode != 0:
        return []
    offenders: list[str] = []
    for record in result.stdout.split("\x1e"):
        record = record.lstrip("\n")
        if not record.strip():
            continue
        sha, _, body = record.partition("\x1f")
        # line 1 is the subject; commitlint bounds it with header-max-length instead
        for lineno, line in enumerate(body.splitlines()[1:], start=2):
            if len(line) > limit:
                offenders.append(f"{sha}:{lineno}: {len(line)} chars: {line[:80]}")
    return offenders


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

    # Pre-check the squash message before `wt merge` builds it: the merge concatenates every
    # task-branch commit body into ONE commit, so an over-long body line is a composite-gate
    # failure the operator sees only at merge time. Fail loud with the offending line instead.
    if not args.skip_commitlint_precheck and commitlint_configured(copy_path):
        offenders = commit_body_offenders(copy_path, target, args.body_max_line)
        if offenders:
            print_err(
                f"pre-check: {len(offenders)} commit body line(s) exceed {args.body_max_line} "
                f"chars on {copy_branch}; `wt merge` squashes every body into one message, so "
                "commitlint's body-max-line-length would fail the composite gate at merge time."
            )
            for item in offenders[:10]:
                print_err(f"  {item}")
            print_err(
                "  fix: reword the offending commit message(s) so each body line is "
                f"<= {args.body_max_line} chars (message-only rewrite), then retry the merge."
            )
            sys.exit(1)

    print(f"-> merge {copy_branch} ({copy_path}) into {target}")
    # Absolute path + --stage tracked — keeps .lsz/.pi out, avoids cd bug
    result = run(["wt", "merge", "-C", str(copy_path), "--stage", "tracked", target, "--yes"])
    if result.returncode == 0:
        print(f"ok: merged {copy_branch} into {target}")
        return

    # Non-zero — print wt output, then classify gate vs conflict
    wt_out: str = (result.stdout or "") + "\n" + (result.stderr or "")
    # print full wt output (cap 8000 to avoid flood, but keep tail where hook prints)
    if wt_out.strip():
        tail = wt_out[-8000:] if len(wt_out) > 8000 else wt_out
        print(tail, file=sys.stderr)
    # changelog / pre-push hook hint
    changelog_hit = any(
        k in wt_out
        for k in ("CHANGELOG", "[Unreleased]", "changelog-unreleased", "pre-push", "pre_push")
    )
    if changelog_hit:
        print_err("hint: CHANGELOG guard blocked — run inside copy:")
        print_err("  uv run python scripts/changelog-unreleased.py update")
        print_err("  git add CHANGELOG.md && git commit --amend --no-edit  # or new commit")
        print_err("  then retry: uv run $SKILL_DIR/scripts/merge_copy.py <copy-path> <target>")
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
        line.startswith("UU")
        or line.startswith("AA")
        or line.startswith("DU")
        or line.startswith("DD")
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
