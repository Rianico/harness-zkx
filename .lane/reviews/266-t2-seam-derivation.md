# TM review record: #266-t2-seam-derivation

Lane `refactor/pr-land-seam`, from base `3424e110`. Reviewer: internal `code-reviewer` subagent (two adversarial passes, tower-delegated by the TM), plus independent TM re-derivation of every counterexample. Implementer replies: `d5f05e7c` (initial), `5a7c642f` (round 1), `925d6573` (round 2).

Commits: `b2aca52b`, `1d9f7a73` (initial, 23 files, +2408/-647) → `14bd0b9` (round 1, 9 files, +248/-89) → `dc21673` (round 2, 4 files, +271/-49). `312283a` is an unreachable superseded commit; history is linear.

## Round 1 review (on `1d9f7a73`): REWORK

Two contract breaches, both of which the implementer's own tests missed.

- **blocker** — `--status` could exit 1. `_head_sha`, `_worktree_clean` and the `gh pr checks` read called `run_command` unguarded (`_status.py:526/527/585`), and the change itself made `run_command` raise on timeout, so a failure escaped to `main` and returned 1 with no JSON. The new `test_gh_failure_is_a_structured_refusal_not_a_traceback` could not see it: `_query_pr` fails first and masks the later reads.
- **major** — the head-ref slug was not injective: `head_slug("feat/x") == head_slug("feat-x") == "feat-x"`, re-creating the cross-branch body pickup ADR-0021 §2 exists to remove.
- Six minors, all bundled into the rework.

Verified at the same time: `draft.json`, the scaffold signature machinery and `--out-dir` are gone with no surviving consumer; `_squash.py` semantics unchanged; T1's push/stamp-recovery behaviour intact; `--check` still exits 1/2.

## Round 1 rework reviewed (`14bd0b9` → narrow delta review): REWORK again

R2 (injective, path-safe), R4, R6, R7a and R8 verified sound. **R1 was not closed:** the guards landed only on the three reads the new test patches, while `run_status` still caught only `UsageError` around the CLI entry path (`resolve_head`, `resolve_title_and_body`, `resolve_repo`), all of which raise `PrError`. The regression test's `argv_prefix` list could not reach them.

The TM reproduced it independently with an absolute interpreter (an earlier attempt with `PATH=/nonexistent uv run` was invalid — it broke `uv`, exit 127):

```
pr.py --status --head feat-status            → exit 1, stdout 0 bytes, JSON on stderr
pr.py --status                               → exit 1, stdout 0 bytes, JSON on stderr
pr.py --status --head feat-status --title x  → exit 1, stdout 0 bytes, JSON on stderr
```

That added **R9b**, which the review had not named: the payload was on **stderr**, so `--status --json | jq` yielded nothing on any degraded path, contrary to ADR-0021 §1 ("facts go to stdout"). R9b was written as an addendum ticket and **could not be delivered** — the receiver held an active ticket lease, and the helper refused twice; forcing it mid-flight was rejected deliberately. It did not need delivery: the round-2 fix already puts JSON on stdout.

Also found: **R10 (major)** — a failed `git rev-list` compare returned `0/0` and the report then asserted `branch_pushed: true`, `head_pushed: true` with no `refusals[]` entry, silently claiming the branch was pushed. `_worktree_clean → True` is the ticket-mandated advisory default and was left alone.

## Round 2 rework reviewed (`dc21673`): PASS

Re-derived by the TM, not accepted on report:

| Check | Result |
|---|---|
| Three entry-path counterexamples, `PATH=/nonexistent`, absolute interpreter | exit **0**; stdout parses as JSON; schema `gh-router/pr-land/status@1`; all 11 pinned keys present |
| `refusals[]` attribution on those paths | `('command_failed', 'git')` — a git failure is no longer labelled `gh_*` |
| Push facts on a failed compare | `branch_pushed: False`, `head_pushed: False`; invariant comment at `_status.py:622`; `compare_failed` folded into `branch_pushed` at `:639` |
| stderr on a degraded read-only run | 0 bytes |
| Slug cap (`"ü"*86`, `"a/"*100`) | 137 bytes each, distinct, single component |
| `hard_slug` injectivity (`feat/x`, `feat-x`, `feat.x`, `feat%2Fx`) | distinct |
| Gate (TM-run) | 2959 passed, 1 skipped, all four gates passed |

## Not checked

Live GitHub API behaviour (no network in the lane); the `.`-remote scenario by execution; semantics of a degraded report on a real diverged branch (unit-tested only).

## TM disposition

`PASS`. Gate green, contract re-derived at the CLI, both breaches closed with falsifiable tests, and one defect (R9b) found by TM re-derivation rather than by the implementer's evidence.
