#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""merge-pr: squash-merge a PR and watch checks/runs to completion.

Mirrors dispatch.sh final stage (gh run watch) for the PR flow:
  1) verify PR exists and show checks snapshot
  2) watch PR checks to green (gh pr checks --watch) — pre-merge gate
  3) gh pr merge --squash --delete-branch (or chosen strategy)
  4) watch post-merge workflow run on base branch via gh run watch

Usage:
  uv run scripts/merge_pr.py <branch|pr_number|pr_url> [--base main] [--no-watch] [--watch-interval 10]
  uv run scripts/worktree.py merge-pr <branch> [--base main] ...
"""

# ruff: noqa: I001,E402

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from _lib import print_err, run  # pyright: ignore[reportImplicitRelativeImport]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Merge PR (squash) and watch checks/runs to completion",
    )
    _ = parser.add_argument(
        "pr",
        help="PR branch, number, or URL (gh pr merge identifier)",
    )
    _ = parser.add_argument(
        "--base",
        default="",
        help="Expected base branch (checked, not passed to gh pr merge which infers from PR)",
    )
    strat = parser.add_mutually_exclusive_group()
    _ = strat.add_argument(
        "--squash",
        dest="strategy",
        action="store_const",
        const="squash",
        default="squash",
        help="Squash merge (default)",
    )
    _ = strat.add_argument(
        "--merge", dest="strategy", action="store_const", const="merge", help="Merge commit"
    )
    _ = strat.add_argument(
        "--rebase", dest="strategy", action="store_const", const="rebase", help="Rebase"
    )
    _ = parser.add_argument(
        "--no-delete-branch", action="store_true", help="Keep branch after merge (default: delete)"
    )
    _ = parser.add_argument(
        "--auto", action="store_true", help="Enable auto-merge (waits for checks)"
    )
    _ = parser.add_argument(
        "--admin", action="store_true", help="Admin merge (bypass requirements)"
    )
    _ = parser.add_argument(
        "--no-watch", action="store_true", help="Skip watching checks/runs (default: watch)"
    )
    _ = parser.add_argument(
        "--watch-interval",
        type=int,
        default=10,
        help="Interval for gh pr checks --watch (default: 10)",
    )
    _ = parser.add_argument(
        "--fail-fast", action="store_true", help="Fail fast during pre-merge checks watch"
    )
    _ = parser.add_argument(
        "--post-merge-watch",
        action="store_true",
        default=True,
        help="Watch post-merge runs on base branch (default: on)",
    )
    _ = parser.add_argument(
        "--no-post-merge-watch",
        dest="post_merge_watch",
        action="store_false",
        help="Skip post-merge run watch",
    )
    return parser.parse_args(argv)


def resolve_pr(pr: str) -> tuple[str, str, str, str]:
    """Resolve pr identifier to (pr_id, number, url, baseRef). pr_id is usable for gh pr commands."""
    # Try gh pr view <pr> --json number,url,baseRefName,state
    res = run(["gh", "pr", "view", pr, "--json", "number,url,baseRefName,state,headRefName"])
    if res.returncode == 0 and res.stdout.strip():
        try:
            j: object = json.loads(res.stdout)
            if isinstance(j, dict):
                n = j.get("number")
                u = j.get("url")
                b = j.get("baseRefName")
                s = j.get("state")
                num = str(n) if isinstance(n, int) else (str(n) if isinstance(n, str) else pr)
                url = str(u) if isinstance(u, str) else ""
                base = str(b) if isinstance(b, str) else ""
                _state = str(s) if isinstance(s, str) else ""
                return (num or pr, num or "", url, base)
        except json.JSONDecodeError:
            pass
    # Fallback: treat as branch, try list
    lst = run(["gh", "pr", "list", "--head", pr, "--json", "number,url,baseRefName,state"])
    if lst.returncode == 0 and lst.stdout.strip():
        try:
            data: object = json.loads(lst.stdout)
            if isinstance(data, list) and data:
                entry = data[0]
                if isinstance(entry, dict):
                    n = entry.get("number")
                    u = entry.get("url")
                    b = entry.get("baseRefName")
                    num = str(n) if n is not None else pr
                    url = str(u) if isinstance(u, str) else ""
                    base = str(b) if isinstance(b, str) else ""
                    return (num, num, url, base)
        except json.JSONDecodeError:
            pass
    return (pr, "", "", "")


def main(argv: list[str] | None = None) -> None:
    args: argparse.Namespace = parse_args(argv)
    pr: str = args.pr
    expected_base: str = args.base
    strategy: str = args.strategy
    delete_branch: bool = not bool(args.no_delete_branch)
    use_auto: bool = bool(args.auto)
    use_admin: bool = bool(args.admin)
    no_watch: bool = bool(args.no_watch)
    watch_interval: int = args.watch_interval
    fail_fast: bool = bool(args.fail_fast)
    post_merge_watch: bool = bool(args.post_merge_watch)

    pr_id, number, url, base_ref = resolve_pr(pr)
    print(
        f"-> resolved PR {pr!r} -> id={pr_id!r} number={number!r} url={url!r} base={base_ref!r}",
        file=sys.stderr,
    )
    if expected_base and base_ref and expected_base != base_ref:
        print_err(f"warning: expected base {expected_base!r} != PR base {base_ref!r}")
    effective_base: str = expected_base or base_ref or "main"

    # 1) snapshot of current checks (non-blocking)
    print(f"-> gh pr checks {pr_id} (snapshot)", file=sys.stderr)
    snap = run(["gh", "pr", "checks", pr_id, "--json", "bucket,name,state,workflow,link"])
    if snap.returncode == 0 and snap.stdout.strip():
        try:
            checks: object = json.loads(snap.stdout)
            if isinstance(checks, list):
                buckets: dict[str, int] = {}
                for c in checks:
                    if isinstance(c, dict):
                        b = str(c.get("bucket", "unknown"))
                        buckets[b] = buckets.get(b, 0) + 1
                print(f"checks snapshot buckets={buckets}", file=sys.stderr)
                # print fails for quick diagnosis
                fails = [c for c in checks if isinstance(c, dict) and c.get("bucket") == "fail"]
                if fails:
                    print_err(f"{len(fails)} failing check(s):")
                    for f in fails[:10]:
                        print_err(
                            f"  - {f.get('name')} state={f.get('state')} workflow={f.get('workflow')} link={f.get('link')}"
                        )
        except json.JSONDecodeError:
            print(snap.stdout[:3000], file=sys.stderr)
    else:
        if snap.stderr:
            print(snap.stderr[:2000], file=sys.stderr)

    # 2) pre-merge watch (gh pr checks --watch) — mirrors dispatch.sh gh run watch
    if not no_watch:
        print(
            f"-> watch PR checks (gh pr checks {pr_id} --watch, interval {watch_interval}s)",
            file=sys.stderr,
        )
        watch_cmd: list[str] = [
            "gh",
            "pr",
            "checks",
            pr_id,
            "--watch",
            "--interval",
            str(watch_interval),
        ]
        if fail_fast:
            watch_cmd.append("--fail-fast")
        watch_res = run(watch_cmd)
        if watch_res.returncode != 0:
            # 0 = pass, 1 = fail, 8 = pending (older gh). Treat non-zero as block unless auto-merge.
            print_err(f"checks watch exited {watch_res.returncode} for PR {pr_id}")
            if watch_res.stdout:
                print(watch_res.stdout[-4000:], file=sys.stderr)
            if watch_res.stderr:
                print(watch_res.stderr[-4000:], file=sys.stderr)
            if not use_auto:
                # show diagnostic then abort merge
                diag = run(["gh", "pr", "checks", pr_id, "--json", "bucket,name,state,link"])
                if diag.returncode == 0:
                    print(diag.stdout[:5000], file=sys.stderr)
                print_err(
                    "hint: fix checks or re-run with --auto to enable auto-merge, or --no-watch to skip gate"
                )
                sys.exit(watch_res.returncode or 1)
            else:
                print(
                    f"auto-merge enabled — proceeding despite checks exit {watch_res.returncode}",
                    file=sys.stderr,
                )
        else:
            print(f"ok: checks passed for PR {pr_id}", file=sys.stderr)
    else:
        print("-> watch skipped via --no-watch (pre-merge gate not waited)", file=sys.stderr)

    # Capture base branch latest run before merge for post-merge watch (like dispatch.sh BEFORE_ID)
    before_run: str = ""
    if post_merge_watch and not no_watch:
        br = run(
            [
                "gh",
                "run",
                "list",
                "--branch",
                effective_base,
                "--limit",
                "1",
                "--json",
                "databaseId",
            ]
        )
        if br.returncode == 0 and br.stdout.strip():
            try:
                data: object = json.loads(br.stdout)
                if isinstance(data, list) and data:
                    entry = data[0]
                    if isinstance(entry, dict) and entry.get("databaseId") is not None:
                        before_run = str(entry.get("databaseId"))
            except json.JSONDecodeError:
                pass

    # 3) merge
    merge_cmd: list[str] = ["gh", "pr", "merge", pr_id, f"--{strategy}"]
    if delete_branch:
        merge_cmd.append("--delete-branch")
    if use_auto:
        merge_cmd.append("--auto")
    if use_admin:
        merge_cmd.append("--admin")
    print(f"-> {' '.join(merge_cmd)}", file=sys.stderr)
    merged = run(merge_cmd)
    if merged.stdout:
        print(merged.stdout[-4000:])
    if merged.stderr:
        print(merged.stderr[-4000:], file=sys.stderr)
    if merged.returncode != 0:
        # Check if already merged
        st = run(["gh", "pr", "view", pr_id, "--json", "state"])
        if st.returncode == 0 and "MERGED" in st.stdout:
            print(f"PR {pr_id} already MERGED", file=sys.stderr)
        else:
            print_err(f"gh pr merge failed (exit {merged.returncode})")
            if not use_auto:
                print_err("hint: if checks were pending, retry with --auto")
            sys.exit(merged.returncode)

    # Verify merged state
    view = run(["gh", "pr", "view", pr_id, "--json", "state,number,url"])
    _pr_state: str = ""
    if view.returncode == 0:
        print(view.stdout[:2000], file=sys.stderr)
        try:
            j2: object = json.loads(view.stdout)
            if isinstance(j2, dict):
                _pr_state = str(j2.get("state", ""))
                url = str(j2.get("url", url))
        except json.JSONDecodeError:
            pass

    # 4) post-merge watch (gh run watch) on base branch — mirrors dispatch.sh watch
    if post_merge_watch and not no_watch and not use_auto:
        # auto-merge case is enqueued, not immediately merged, so skip post watch
        print(f"-> post-merge watch on {effective_base} (gh run watch)", file=sys.stderr)
        run_id: str = ""
        # poll up to ~60s for new run on base branch that is not before_run
        for _ in range(30):
            time.sleep(2)
            lst = run(
                [
                    "gh",
                    "run",
                    "list",
                    "--branch",
                    effective_base,
                    "--limit",
                    "5",
                    "--json",
                    "databaseId,headBranch,status,conclusion,event,createdAt,url",
                ]
            )
            if lst.returncode != 0 or not lst.stdout.strip():
                continue
            try:
                data: object = json.loads(lst.stdout)
                if isinstance(data, list) and data:
                    # newest first; find first with different id than before_run
                    for entry in data:
                        if not isinstance(entry, dict):
                            continue
                        did = str(entry.get("databaseId", ""))
                        if did and did != before_run:
                            run_id = did
                            break
                    if run_id:
                        break
            except json.JSONDecodeError:
                continue
        if not run_id:
            print(
                f"post-merge: no new run detected on {effective_base} within 60s (before={before_run})",
                file=sys.stderr,
            )
            print(f"check: gh run list --branch {effective_base} --limit 5", file=sys.stderr)
        else:
            print(f"-> gh run watch {run_id} --exit-status", file=sys.stderr)
            watch = run(["gh", "run", "watch", run_id, "--exit-status"])
            if watch.returncode == 0:
                print(
                    f"ok: post-merge workflow succeeded on {effective_base} — run {run_id}",
                    file=sys.stderr,
                )
            else:
                print_err(f"post-merge workflow {watch.returncode} — run {run_id}")
                log = run(["gh", "run", "view", run_id, "--log-failed"])
                if log.returncode == 0:
                    print(log.stdout[-8000:] if log.stdout else "", file=sys.stderr)
                    if log.stderr:
                        print(log.stderr[-4000:], file=sys.stderr)
                else:
                    view2 = run(["gh", "run", "view", run_id])
                    if view2.stdout:
                        print(view2.stdout[-4000:])
                print_err(f"view: gh run view {run_id} --log-failed")
                sys.exit(watch.returncode or 1)

    print(
        f"ok: PR {pr_id} merged (strategy={strategy}) into {effective_base}"
        + (f" {url}" if url else "")
    )


if __name__ == "__main__":
    main()
