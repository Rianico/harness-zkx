# TM review record: #266-t1-push-stamp @ ce3f5cd1

Reviewer: internal `code-reviewer` subagent (adversarial crux review), commissioned by the TM after implementer reply `e257c416`. Cwd: lane worktree `everything-claude-code.fix-pr-land-push-and-stamp`, range `04f38276..ce3f5cd1`.

## Verdict: PASS (5 minor findings, no blocker, no major)

Strongest reason: both ticket defects are fixed with falsifiable tests; the read-only invariant holds structurally and end-to-end; no force-push exists.

## Falsification results

1. **Vacuous tests — not vacuous.** Reviewer re-ran the 8 new tests against a scratch copy of base `04f38276`: **7 failed, 1 passed** (the implementer claimed 8 red). Tests 1, 2, 3, 4, 7 red behaviourally; test 6 red via the missing `remote=` kwarg; test 5 red only via a monkeypatch `AttributeError`; test 8 is a by-design in-sync guard that passes at base. The divergence test drives real control flow through a fake git, with the `ahead/behind` mapping load-bearing (an inverted mapping fails test 2).
2. **Read-only invariant — survives.** All four push sites enumerated: `_github.py:339`, `:362` (inside `ensure_branch_pushed`, single call site `pr.py:538`), `_changelog.py:117`, `:252` (only reachable via `stamp_changelog` ← `pr.py:692`, after a PR exists). `--check` returns at `pr.py:664` before `create_or_reuse_pr` (`pr.py:678`). Instrumented scratch run of `--check` made zero push calls.
3. **Remote resolution — survives.** No `origin` literal on the new push path; `_remote_branch_exists(name, cwd, remote="origin")` takes the resolved value. `refs/remotes/origin/HEAD` at `_github.py:382`/`:424` is pre-existing base-resolution fallback, outside the diff.
4. **Stale remote-tracking refs — confirmed, no fetch anywhere on the push path.** Safe by construction (a push is accepted only when the real remote head is an ancestor), so the worst case is a wrong refusal or a bare rejection, never data loss.
5. **Stamp recovery — correct on the main path**, pushes the same `head_ref` as the post-stamp push; `ahead > 0` is repaired; in-sync is a no-op.
6. **No regressions, no weakened tests.** `test_pr_land.py` loses no test or assertion and becomes strictly tighter (adds `calls.count(["git","push","origin","feat-x"]) == 1`). The new `remote=` kwarg is defaulted, so pre-existing call sites are unchanged.
7. **P3 note verified.** `_changelog.py:61` (`except OSError, UnicodeDecodeError:`) is byte-identical at base `04f38276` — legal Python 3.14 (PEP 758), not introduced here; `ast.parse` confirms.

## Findings (all minor; R1–R3 sent back, R4–R5 logged)

- **R1** `_changelog.py:105,117` — recovery push outside the `try`, so a timeout raises `PrError` and escapes to exit 1 after the PR URL is printed; contradicts the docstring and the deferred hard-fail contract.
- **R2** `_github.py:347-366` — with a stale tracking ref, a real divergence is rejected by git and surfaces as a bare `PrError` with no `remediation:` line.
- **R3** `tests/gh-router/test_pr_land_push_stamp.py:114` — no test asserts the push argv uses the *resolved* remote; a future hardcoded `"origin"` in the push argv would pass all 8.
- **R4** `_github.py:337-345` — `branch.<ref>.remote = "."` now hard-fails the creation path where base created the PR. Safe, rare; T2 owns the reporting contract.
- **R5** Evidence claim overstated: "8 new tests red before" measured as 7/1.

## Not checked

Full `scripts/check.sh` (run by the TM: 2920 passed, 1 skipped, 4/4 gates); lint/format/type (gate-owned); real GitHub API behaviour on an unpushed branch (no network); the `.`-remote scenario by execution.

## TM disposition

`REWORK` (bounded): R1, R2, R3. R4, R5 logged. Rationale: all three are cheap, and T2 rewrites this path's reporting — the guards belong in before the rewrite, not after it.
