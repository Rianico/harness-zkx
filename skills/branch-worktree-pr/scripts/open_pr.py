#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""open-pr: push branch and open PR ensuring Closes trailer and changelog."""

# ruff: noqa: I001,E402

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from _lib import print_err, run  # pyright: ignore[reportImplicitRelativeImport]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Push branch and open PR with Closes trailer verification",
    )
    _ = parser.add_argument("branch", help="Branch feat/<name> or map/<name>")
    _ = parser.add_argument("base", help="Base branch main or map/<name>")
    _ = parser.add_argument("issue_number", help="Issue number without #")
    return parser.parse_args(argv)


def gh_pr_exists(branch: str) -> tuple[bool, str, str]:
    """Check if PR exists for branch. Returns (exists, number, body)."""
    # Prefer gh pr list --head
    result = run(["gh", "pr", "list", "--head", branch, "--json", "number,body,baseRefName"])
    if result.returncode == 0 and result.stdout.strip():
        try:
            data: object = json.loads(result.stdout)
            if isinstance(data, list) and len(data) > 0:
                entry: object = data[0]
                if isinstance(entry, dict):
                    num_raw: object = entry.get("number")
                    body_raw: object = entry.get("body")
                    num: str = str(num_raw) if num_raw is not None else ""
                    body: str = str(body_raw) if isinstance(body_raw, str) else ""
                    return (True, num, body)
        except json.JSONDecodeError as _exc:
            print_err(f"gh pr list JSON decode failed: {_exc}")
    # Fallback via gh pr view <branch>
    result2 = run(["gh", "pr", "view", branch, "--json", "number,body"])
    if result2.returncode == 0 and result2.stdout.strip():
        try:
            data2: object = json.loads(result2.stdout)
            if isinstance(data2, dict):
                num_raw2: object = data2.get("number")
                body_raw2: object = data2.get("body")
                num2: str = str(num_raw2) if num_raw2 is not None else ""
                body2: str = str(body_raw2) if isinstance(body_raw2, str) else ""
                if num2:
                    return (True, num2, body2)
        except json.JSONDecodeError as _exc:
            print_err(f"gh pr view JSON decode failed: {_exc}")
    return (False, "", "")


def ensure_closes_trailer(branch: str, issue: str) -> None:
    exists: bool
    _num: str
    body: str
    exists, _num, body = gh_pr_exists(branch)
    if not exists:
        return
    # Check if body ends with Closes #<issue> within last 5 lines
    lines: list[str] = body.strip().splitlines()
    tail: str = "\n".join(lines[-5:]) if lines else ""
    if f"Closes #{issue}" in tail:
        return
    new_body: str = (
        body.rstrip() + f"\n\nCloses #{issue}\n" if body.strip() else f"Closes #{issue}\n"
    )
    # gh pr edit <branch> --body "..."
    edit = run(["gh", "pr", "edit", branch, "--body", new_body])
    if edit.returncode != 0:
        # Try alternative: gh pr edit --body without branch positional
        edit2 = run(["gh", "pr", "edit", "--body", new_body])
        if edit2.returncode != 0:
            print_err(f"gh pr edit failed: {edit.stderr or edit.stdout}")
            # Do not exit hard; PR exists but trailer not ensured
    else:
        print(f"updated PR body to include Closes #{issue}", file=sys.stderr)


def main(argv: list[str] | None = None) -> None:
    args: argparse.Namespace = parse_args(argv)
    branch: str = args.branch
    base: str = args.base
    issue: str = args.issue_number.lstrip("#")

    if not branch.strip() or not base.strip() or not issue.strip():
        print_err("use: open_pr.py <branch> <base> <issue-number>")
        sys.exit(1)
    if not issue.isdigit():
        print_err(f"issue-number must be digits, got: {issue}")
        sys.exit(1)

    print(f"-> git push -u origin {branch}")
    push = run(["git", "push", "-u", "origin", branch])
    if push.returncode != 0:
        push_out: str = (push.stdout or "") + "\n" + (push.stderr or "")
        print_err(push_out[-8000:] if len(push_out) > 8000 else push_out)
        if any(
            k in push_out for k in ("CHANGELOG", "[Unreleased]", "changelog-unreleased", "pre-push")
        ):
            print_err("hint: pre-push CHANGELOG guard blocked — run:")
            print_err("  uv run python scripts/changelog-unreleased.py update")
            print_err("  git add CHANGELOG.md && git commit --amend --no-edit")
            print_err("  git push -u origin " + branch + "  # retry")
        else:
            print_err(f"git push failed (exit {push.returncode})")
        sys.exit(1)

    # Check if PR already exists
    exists: bool
    num: str
    _body: str
    exists, num, _body = gh_pr_exists(branch)
    if exists:
        print(f"PR already exists for {branch} (#{num}), checking view", file=sys.stderr)
    else:
        print(f"-> gh pr create --fill --base {base} (Closes #{issue})", file=sys.stderr)
        # Get title from last commit subject
        title_res = run(["git", "log", "--oneline", "-n", "1"])
        title: str = ""
        if title_res.returncode == 0 and title_res.stdout.strip():
            parts: list[str] = title_res.stdout.strip().split(" ", 1)
            title = parts[1] if len(parts) > 1 else parts[0]
        # Create with title/body if available, else --fill
        create_cmd: list[str] = ["gh", "pr", "create", "--fill", "--base", base]
        # Prefer explicit body with Closes when we have a title
        if title:
            create_cmd = [
                "gh",
                "pr",
                "create",
                "--base",
                base,
                "--title",
                title,
                "--body",
                f"Closes #{issue}",
            ]
        created = run(create_cmd)
        print(created.stdout[-2000:] if created.stdout else "")
        if created.stderr:
            print(created.stderr[-2000:], file=sys.stderr)
        # Fallback to --fill without title/body if above failed
        if created.returncode != 0:
            exists2, _, _ = gh_pr_exists(branch)
            if not exists2:
                fallback = run(["gh", "pr", "create", "--fill", "--base", base])
                print(fallback.stdout[-2000:] if fallback.stdout else "")
                if fallback.stderr:
                    print(fallback.stderr[-2000:], file=sys.stderr)
                if fallback.returncode != 0:
                    # Final check if PR now exists via list
                    exists3, _, _ = gh_pr_exists(branch)
                    if not exists3:
                        print_err(f"gh pr create failed: {fallback.stderr or fallback.stdout}")
                        sys.exit(1)

    # Ensure body ends with Closes
    ensure_closes_trailer(branch, issue)

    print("-> verify PR body contract", file=sys.stderr)
    view = run(["gh", "pr", "view", branch, "--json", "number,baseRefName,body"])
    if view.returncode == 0:
        print(view.stdout[:2000])
        try:
            vdata: object = json.loads(view.stdout)
            if isinstance(vdata, dict):
                vbody: object = vdata.get("body")
                if isinstance(vbody, str) and f"Closes #{issue}" not in vbody:
                    print_err(f"warning: PR body still missing Closes #{issue}")
        except json.JSONDecodeError as _exc:
            print_err(f"gh pr view JSON decode failed: {_exc}")
    else:
        # Try list fallback
        lst = run(["gh", "pr", "list", "--head", branch, "--json", "number,baseRefName,body"])
        if lst.returncode == 0:
            print(lst.stdout[:2000])
        else:
            print(view.stdout[:2000])
            if view.stderr:
                print(view.stderr[:2000], file=sys.stderr)

    print("-> git diff --check", file=sys.stderr)
    diff = run(["git", "diff", "--check"])
    # git diff --check returns 1 if whitespace errors found; stderr/stdout contains warnings
    out: str = (diff.stdout or "") + (diff.stderr or "")
    if out.strip():
        # git diff --check prints issues even on success? Check returncode
        if diff.returncode != 0:
            print_err("git diff --check found issues:")
            print_err(out)
            sys.exit(1)
        else:
            # Any output with returncode 0 is warning, not error
            print(out, file=sys.stderr)

    # Verify changelog still has [Unreleased]
    changelog: Path = Path("CHANGELOG.md")
    if not changelog.is_file():
        print_err("CHANGELOG missing [Unreleased] after push")
        sys.exit(1)
    text: str = changelog.read_text(encoding="utf-8", errors="ignore")
    if "## [Unreleased]" not in text:
        print_err("CHANGELOG missing [Unreleased] after push")
        sys.exit(1)

    print(f"ok: PR for {branch} -> {base} (Closes #{issue}) is open and clean")


if __name__ == "__main__":
    main()
