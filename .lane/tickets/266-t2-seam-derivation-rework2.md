# TICKET: #266-t2-seam-derivation — REWORK round 2 (bounded)

Round-1 rework verified sound: R2 (injective, path-safe — I re-derived `feat%2Fx` / `feat-x` / `feat.x` / `feat%252Fx` myself), R4, R6, R7a, R8. History is linear and `312283a` is an unreachable superseded commit — fine.

But **R1 is not closed**, and the defect is worse than the round-1 report: the guards landed only on the reads the new test patches, so the same contract breach survives on the CLI entry path. Do not amend `14bd0b9`; add a follow-up commit.

## R9 — blocker: `--status` still exits 1 with empty stdout

`_status.py:921`, `_status.py:941`, `_status.py:964`. `run_status` catches only `UsageError` around `resolve_head` (`git rev-parse --abbrev-ref HEAD`), `resolve_title_and_body` (`git log -1 --pretty=%s`) and `resolve_repo` (`git config`). All three raise `PrError` now, so the pinned contract — "exits 0 on every path, never refuses" — is still breached by exactly the counterexample the round-1 blocker described. Reproduced at `14bd0b9`:

```
PATH=/nonexistent python3 skills/gh-router/subskills/pr-land/scripts/pr.py --status --head feat-status
  → exit 1, 0 bytes on stdout          (resolve_title_and_body, :941)
PATH=/nonexistent … pr.py --status                              → exit 1  (resolve_head, :921)
PATH=/nonexistent … pr.py --status --head feat-status --title x  → exit 1  (resolve_repo, :964)
```

`test_status_survives_read_failures` cannot see them: its `argv_prefix` list contains only the three reads round 1 touched.

**Fix**: widen those three handlers to `except PrError, OSError as exc:` and degrade — head/repo → `degraded_report` carrying the mapped refusal; title/body → empty title/body facts plus the refusal, and continue. **Extend the regression test's `argv_prefix` list** with `["git","rev-parse","--abbrev-ref","HEAD"]`, `["git","log","-1","--pretty=%s"]`, `["git","config"]`.

**Evidence**: the three counterexample commands above flipping to exit 0 with valid schema JSON, plus the extended in-process test failing before the fix and passing after.

## R10 — major: a failed compare must not fabricate push facts

`_status.py:570-573`, `_status.py:630`. When `git rev-list` raises, the guard returns `0/0` and the report then asserts `branch_pushed: true`, `head_pushed: true`, `ahead/behind: 0/0`, `failure_states: []` — and appends **no** `refusals[]` entry for the failed compare (codes present: `gh_query_failed`, `body_missing`); stderr is empty. A caller reading the machine interface is told the branch is pushed when nothing established that.

**Fix**: in the same `except`, append `pr_error_to_refusal(exc)` and force `branch_pushed = head_pushed = False`. State the invariant in a comment: **never assert a push fact from a failed read**. (`_worktree_clean → True` is the ticket-mandated advisory default; leave it.)

## R11 — minor: a `git` failure must never be labelled `gh_*`

`_status.py:258-279`, `pr.py:740`. `pr_error_to_refusal(e)` is called with no `tool`, and `_failing_tool` returns `""` for hand-rolled messages, so gh-only markers fire anyway:

```
PrError("failed to push feat-x to origin: fatal: Authentication failed for 'https://github.com/…'")
  → code gh_unauthenticated, site gh, remedy "run `gh auth login`"
```

**Fix**: gate the gh-only markers on `resolved == "gh"`; otherwise return the generic / `command_failed` entry. Pass the tool from the `pr.py:740` call site.

## R12 — minor: tie the range-authority assertion to the CLI

`tests/gh-router/test_pr_land_range_authority.py:260-270`. Both sides are computed in-test from `expected`; the subprocess contributes only `trailers: 2`, so a CLI deriving trailers from a *different two-author* range still passes.

**Fix**: assert the CLI's own behaviour — wrap `git` in the test's `bindir` (as it already does for `gh`) and assert the digest-range argv, or assert CLI-emitted trailer text.

## R13 — minor: cap the slug

`_status.py:158-171`. Expansion reaches 9 bytes per source character, so a legal ref can exceed `NAME_MAX`: `head_slug("ü"*86)` is 516 bytes and `"a/"*100` is 400. Today that refuses cleanly downstream (`_draft.py:497-501`, "File name too long") rather than crashing, which is why this is minor.

**Fix**: cap the stem and append a short digest of the full ref, keeping the mapping injective.

## Verification Contract (GDD/EDD)

- **Check Command**: `bash scripts/check.sh` (baseline on this branch: 2951 passed, 1 skipped) and `uv run pytest tests/gh-router -q`.
- **Required Evidence**:
  - R9: the three counterexample commands shown failing on `14bd0b9` and exiting 0 with valid JSON after; the extended test's name and its red-then-green run.
  - R10: a test patching `git rev-list` to raise, asserting `branch_pushed is False`, `head_pushed is False`, and a `refusals[]` entry naming the compare.
  - R11: the `Authentication failed` and `Could not resolve host` message cases routing to a non-`gh` code, while a genuine `gh`-missing case still routes to `gh_*`.
  - R12: the new CLI-level assertion, and the counterexample it now catches.
  - R13: `head_slug` outputs for `"ü"*86` and `"a/"*100` within `NAME_MAX` and still distinct.
  - Gate output, all SHAs, `git diff --stat`.

Reply with the standard template (`uv run skills/herdr/scripts/herdr_reply.py pi --file <payload> --ticket '#266-t2-seam-derivation'`). Commit locally; do not push, open a PR, or merge.
