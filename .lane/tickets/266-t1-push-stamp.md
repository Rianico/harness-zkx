# TICKET / BRIEF: #266-t1-push-stamp — pr-land push precondition and stamp recovery

Target files / Seams: `skills/gh-router/subskills/pr-land/scripts/pr.py` (`create_or_reuse_pr`), `skills/gh-router/subskills/pr-land/scripts/_github.py` (`_remote_branch_exists`, `repo_remote_for_ref`), `skills/gh-router/subskills/pr-land/scripts/_changelog.py` (`stamp_changelog`), `tests/gh-router/`.

## 1. Intent (IDD)

- **Problem**: two defects in `pr-land` that break a re-run from a partially-completed state.
  1. `create_or_reuse_pr` calls `gh api` for the PR before anything pushes the branch. The branch only reaches the remote later, inside `stamp_changelog` (`_changelog.py:216`) — and never when `--no-stamp` is passed. So creating a PR on an unpushed branch fails.
  2. `stamp_changelog` commits `chore(changelog): …` and then pushes. If the commit lands and the push fails, a re-run finds `(#N)` already present and returns early at `_changelog.py:126`, leaving the commit stranded and the PR head stale. Recovery is not idempotent.
- **Proposed Outcome**: creating a PR from a branch whose remote ref is missing or behind pushes first, so the PR is created against the real head. A re-run after a failed stamp push repairs the remote instead of returning early. Both behaviours are covered by tests that fail before the fix.
- **Non-Negotiable Constraints**:
  - Push **only** from the creation path inside `create_or_reuse_pr`. `--check` and every other read-only path must never push, even though they call `gh api`.
  - Resolve the remote through `repo_remote_for_ref` (`_github.py:145`). Do not hardcode `origin`.
  - `_remote_branch_exists` currently hardcodes `refs/remotes/origin/<name>` in its body **and** its docstring (`_github.py:290-296`); parameterize it with the resolved remote.
  - Refuse (non-zero, no mutation) when the push fails, and when the remote is ahead (divergence) — never force-push, and never `--force-with-lease`.
  - Leave `_changelog.py`'s post-stamp push in place; the early push is an addition, not a replacement.
  - Keep the changelog stamping semantics unchanged apart from recovery: same entry identity, same baseline behaviour, no new bullets stamped.
  - **Out of scope** (a later tranche owns these; do not touch them): `--status`, `draft.json` deletion, `--out-dir`, scaffold leaves or signatures, the `refusals[]`/`transitions[]` schema, and the "hard-fail after PR creation" reporting change for stamp failures. Do not edit `docs/`, `GLOSSARY.md`, `.lane/`, or `.github/`.
  - Do not push to any remote, open a PR, or merge: commit locally in this lane worktree and report. Integration is the Task Manager's job.

## 2. Verification Contract (GDD/EDD)

- **Check Command**: `bash scripts/check.sh` (mirrors CI: ruff, ruff format, basedpyright, pytest) plus the targeted file `uv run pytest tests/gh-router/test_pr_land.py -x -q`.
- **Required Evidence**:
  - Red-then-green logs: the new tests failing against `HEAD~` (or before the edit) and passing after, with the command and exit codes shown.
  - `bash scripts/check.sh` tail showing `All gates passed.` (the baseline on this base commit is 2912 passed, 1 skipped).
  - Commit SHA(s), a `git diff --stat` summary, and the exact remote/push assertions you added.
- **Required tests** (at minimum, in `tests/gh-router/`):
  1. Remote ref missing → the creation path pushes, then creates the PR.
  2. Remote ref behind → the creation path pushes; up to date → it does **not**.
  3. Remote ahead (divergence) → refuses with the remediation, and no `git push` runs.
  4. A read-only path (`--check`) performs no push — assert the push helper was never invoked.
  5. `_remote_branch_exists` honours a non-`origin` remote resolved by `repo_remote_for_ref`.
  6. Stamp recovery: entry already carries `(#N)` and the local branch is ahead of its remote → the rerun pushes the existing commit instead of returning early; when not ahead, it stays a no-op.

## 3. Execution Strategy (Subagent-First Mandate)

- Delegate heavy codebase exploration (Scout), multi-file editing (Editor), and test-failure log triage (Test Runner) to ephemeral subagents.
- Keep this host pane's context lean: ingest only summaries, diffs, and artifact paths from subagents.
- **The Iron Curtain**: never let a subagent call Herdr CLI commands or scripts (`herdr_reply.py`, `herdr_dispatch.py`). Aggregate everything in this host pane.

On completion, reply to the caller in one message using the herdr helper script:

```bash
uv run skills/herdr/scripts/herdr_reply.py pi --file <reply-payload.md> --ticket '#266-t1-push-stamp'
```

Use the reply template: `COMPLETED <commit-sha>` (or `BLOCKED <reason>` / `REJECTED <invariant-violation>`), then `## Summary` (≤100 words), `## Artifacts` (absolute paths), `## Evidence` (`check: PASS|FAIL (command)`), `## Route` (`continue | remediate | blocked`), `## Issues` (P1/P2/P3 with `file:line`, the invariant threatened, and the concrete fix).

If a requirement is ambiguous or the fix would need to touch out-of-scope files, reply `BLOCKED` with the question rather than guessing.
