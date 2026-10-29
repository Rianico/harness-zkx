"""`pr.py --sync`: merge the base into the head and hand a stopped merge to pr-conflict.

The defect this closes is route friction. A hand `git merge` followed by a hand edit was
cheaper than loading pr-conflict and running its extractor, so conflicts were settled
without either side's intent. One command now performs the whole step: fetch, merge,
push a clean result, and on a stop print the dual-intent report before any file is
edited. History is never rewritten and no push is ever forced.
"""

from __future__ import annotations

import sys
from pathlib import Path

import _github
from _errors import PrError, RefusalError, make_refusal, make_transition

# The dual-intent reader sits beside this package. Resolve it from this file, not the
# cwd, so the hand-off works from any repository the harness is installed into.
HELPER_SCRIPT = (
    Path(__file__).resolve().parents[2] / "pr-conflict" / "scripts" / "extract_conflict_context.py"
)

# A stopped operation owns the worktree and its index: merging on top of it corrupts both.
_IN_PROGRESS_REFS = (
    ("MERGE_HEAD", "a merge"),
    ("CHERRY_PICK_HEAD", "a cherry-pick"),
    ("REVERT_HEAD", "a revert"),
)
_IN_PROGRESS_PATHS = (("rebase-merge", "a rebase"), ("rebase-apply", "a rebase"))

RESUME = "resolve, `git add` each path, `git commit`, then re-run `pr.py --sync`"


def _repo_root(cwd: Path | None = None) -> Path:
    """The physical repository root: the conflict helper reports repo-relative paths."""
    res = _github.run_command(["git", "rev-parse", "--show-toplevel"], cwd=cwd, required=True)
    return Path(res.stdout.strip())


def _operation_in_progress(cwd: Path | None = None) -> str | None:
    """The stopped git operation holding the worktree, or None when it is free."""
    for ref, label in _IN_PROGRESS_REFS:
        res = _github.run_command(["git", "rev-parse", "-q", "--verify", ref], cwd=cwd)
        if res.returncode == 0:
            return label
    for name, label in _IN_PROGRESS_PATHS:
        res = _github.run_command(["git", "rev-parse", "--git-path", name], cwd=cwd)
        if res.returncode != 0 or not res.stdout.strip():
            continue
        path = Path(res.stdout.strip())
        if not path.is_absolute():
            path = (cwd or Path.cwd()) / path
        if path.exists():
            return label
    return None


def _commit_count(spec: str, cwd: Path | None = None) -> int:
    """Commits in `spec` (a `rev-list` range), refusing on an unreadable count."""
    res = _github.run_command(["git", "rev-list", "--count", spec], cwd=cwd, required=True)
    try:
        return int(res.stdout.strip())
    except ValueError:
        raise PrError(
            f"cannot count {spec}: unexpected rev-list output {res.stdout.strip()!r}"
        ) from None


def _unmerged_paths(cwd: Path | None = None) -> list[str]:
    """Every path still carrying an unmerged index entry; empty when the merge was clean."""
    res = _github.run_command(["git", "diff", "--name-only", "--diff-filter=U"], cwd=cwd)
    if res.returncode != 0:
        return []
    return [line.strip() for line in res.stdout.splitlines() if line.strip()]


def print_conflict_report(root: Path) -> None:
    """Run the pr-conflict extractor and print its facts verbatim on stdout."""
    if not HELPER_SCRIPT.is_file():
        print(
            f"conflict helper missing at {HELPER_SCRIPT}; run '{_github.CONFLICT_HELPER}' manually",
            file=sys.stderr,
        )
        return
    res = _github.run_command([sys.executable, str(HELPER_SCRIPT), "--all"], cwd=root)
    if res.stdout.strip():
        print(res.stdout.rstrip())
    if res.returncode != 0:
        print(res.stderr.rstrip() or "conflict helper failed", file=sys.stderr)


def refuse_stopped_operation(stopped: str) -> RefusalError:
    """Refuse a sync while another git operation owns the worktree."""
    remedy = f"finish it first ('{_github.CONFLICT_HELPER} --all' prints the hunks), then re-run"
    print(f"refusing to sync: {stopped} is already in progress", file=sys.stderr)
    print(f"remediation: {remedy}", file=sys.stderr)
    return RefusalError(
        f"{stopped} is already in progress",
        refusals=[
            make_refusal(
                "sync_in_progress",
                f"{stopped} is already in progress; a second merge would corrupt the index",
                remedy,
                "worktree",
            )
        ],
        transitions=[
            make_transition(
                "pr.py --sync",
                ["no merge, rebase, cherry-pick, or revert in progress"],
                "local",
            )
        ],
    )


def refuse_stopped_merge(base_ref: str, paths: list[str]) -> RefusalError:
    """Refuse a merge that stopped on conflicts, naming the continue path."""
    reason = f"the merge of {base_ref} stopped on {len(paths)} conflicted path(s)"
    print(f"sync stopped on conflicts in {len(paths)} path(s)", file=sys.stderr)
    print(f"remediation: {RESUME}", file=sys.stderr)
    return RefusalError(
        reason,
        refusals=[
            make_refusal("sync_conflict", reason, RESUME, "worktree"),
        ],
        transitions=[
            make_transition("pr.py --sync", ["conflicts resolved and committed"], "local"),
        ],
    )


def run_sync(*, head_ref: str, base: str, cwd: Path | None = None) -> int:
    """Merge `<remote>/<base>` into the head; exit 0 when the head ends current.

    A clean merge, and an already-current head carrying local commits, both push the
    head. A stopped merge prints the pr-conflict report and refuses (exit 1), so no
    file is edited before both sides' intent is read.
    """
    root = _repo_root(cwd)
    stopped = _operation_in_progress(cwd)
    if stopped is not None:
        raise refuse_stopped_operation(stopped)

    remote = _github.repo_remote_for_ref(head_ref, cwd=cwd)
    base_ref = f"{remote}/{base}"
    _ = _github.run_command(["git", "fetch", remote, base], cwd=cwd, required=True)
    behind = _commit_count(f"HEAD..{base_ref}", cwd=cwd)
    if behind == 0:
        print(f"already current with {base_ref}", file=sys.stderr)
        _github.ensure_branch_pushed(head_ref, cwd=cwd)
        return 0

    merge = _github.run_command(["git", "merge", "--no-edit", base_ref], cwd=cwd)
    if merge.returncode == 0:
        _github.ensure_branch_pushed(head_ref, cwd=cwd)
        print(f"synced {head_ref} with {base_ref} ({behind} commit(s))", file=sys.stderr)
        return 0

    paths = _unmerged_paths(cwd)
    if not paths:
        detail = merge.stderr.strip() or merge.stdout.strip() or "no output"
        raise PrError(f"git merge {base_ref} failed: {detail}")

    shown = paths[: _github.CONFLICT_FILES_MAX]
    extra = len(paths) - len(shown)
    more = f" (+{extra} more)" if extra > 0 else ""
    print(f"conflicted paths: {' '.join(shown)}{more}", file=sys.stderr)
    print_conflict_report(root)
    raise refuse_stopped_merge(base_ref, paths)
