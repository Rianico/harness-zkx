# TICKET: #266-t1-push-stamp — REWORK (bounded)

Verdict from the TM's review of `ce3f5cd1`: **REWORK — 3 findings, all minor, all cheap.** The ticket's acceptance criteria are met (both defects fixed, tests falsifiable, read-only invariant verified structurally and end-to-end, no force-push). These three are sent back because T2 rewrites this path's reporting, so the guards belong in before the rewrite, not after it.

Do not amend `ce3f5cd1`. Add a follow-up commit and report both SHAs. Keep the change set to the three items below — no other files, no refactors.

## R1 — Stamp recovery must stay soft (fix)

`_changelog.py:105,117`. The docstring promises "`False` when the push failed (warning on stderr, the same soft failure as the stamp's own push)", but `repo_remote_for_ref` and the push sit outside the `try`, so a timeout raises `PrError` and escapes `stamp_changelog` → `pr.py:692` → exit 1 after the PR URL was already printed. That is the "hard-fail after PR creation" behaviour this tranche defers to T2, so it must not appear here.

**Fix**: move the remote resolution and the push inside the `try`, catch `PrError` → warning on stderr + `return False`, matching the sibling post-stamp push at `:252`.

## R2 — An undetected divergence must carry the remediation (fix)

`_github.py:347-366`. Divergence is judged from local remote-tracking refs with no fetch, so a teammate's push leaves a stale ref showing `behind == 0, ahead == 1`; the push is then rejected by git and surfaces as a bare `PrError("failed to push …")` with raw stderr and no `remediation:` line — while the detected divergence case prints one.

**Fix**: in the `ahead > 0` push-failure branch, print the same `remediation:` line; when stderr matches `non-fast-forward|fetch first`, raise `RefusalError` (divergence) instead of `PrError`. **Do not add a `git fetch`** — the compare stays network-free; the stale-ref judgement is documented, not fixed, in this tranche.

## R3 — Add the guard test for the resolved remote (test)

`tests/gh-router/test_pr_land_push_stamp.py:114`. Every fixture resolves `origin`, so a future `ensure_branch_pushed` that hardcodes `"origin"` in the push argv — while resolving the remote only for the existence check — passes all 8 tests today. The "never hardcodes it" requirement is currently unverified for the push itself.

**Fix**: one case with `branch.feat-x.remote = upstream` asserting the push argv is `["git", "push", "upstream", "feat-x"]`, and that the existence check consults `refs/remotes/upstream/feat-x`.

## Logged, not fixed (do not address)

- **Non-pushable branch remote**: `branch.feat-x.remote = "."` makes the creation path refuse before the PR where base created it. Safe (non-zero, no mutation) and the slug still resolves globally. T2 owns the reporting contract for this.
- **Evidence claim overstated**: the reply says "8 new tests red before"; measured on a scratch copy of base, **7 failed / 1 passed** (test 5 was red via a monkeypatch `AttributeError`, test 8 is a by-design in-sync guard). No code impact. State the measured figure in your next reply.

## Verification Contract (GDD/EDD)

- **Check Command**: `bash scripts/check.sh` and `uv run pytest tests/gh-router/test_pr_land_push_stamp.py -q`.
- **Required Evidence**:
  - Red-then-green for R1 and R2: the new assertions failing before the fix and passing after, with commands and exit codes.
  - R3's new test name and its assertion output.
  - `bash scripts/check.sh` tail showing `All gates passed.` and the new total (baseline for this branch is 2920 passed, 1 skipped).
  - Both SHAs: `ce3f5cd1` and the follow-up.
- Scope guard: no `--status`, no `draft.json`/scaffold/schema work, no `docs/`, `GLOSSARY.md`, `.lane/`, or `.github/` edits. Commit locally; do not push, open a PR, or merge.

Reply with the standard template to the caller (`uv run skills/herdr/scripts/herdr_reply.py pi --file <payload> --ticket '#266-t1-push-stamp'`).
