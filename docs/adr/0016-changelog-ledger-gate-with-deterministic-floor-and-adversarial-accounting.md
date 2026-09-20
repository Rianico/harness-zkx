# 16. Changelog Ledger Gate with Deterministic Floor and Adversarial Accounting

Date: 2026-09-20

## Status

Proposed — Applies [ADR-0015](0015-goal-gate-and-convergence-loop-architecture.md) to the
changelog boundary.

Relates to [13. Worktree Python Shims with wt Gate Delegation and Auto-Scaffold](0013-worktree-python-shims-with-wt-gate-delegation.md)

The measurements in Context and the merge mechanics in Decision were observed on 2026-09-20.
No implementation exists yet.

## Context

`CHANGELOG.md` `## [Unreleased]` is authored by branch commits (`.githooks/pre-push`,
`changelog-check.yml`) while merges squash. The check diffs the file against
`scripts/changelog-unreleased.py update` output, so it verifies synchronisation with the commit
set rather than accuracy. On 2026-09-20 `main` passed that check while listing eleven `herdr`
entries against two `herdr` commits, four of which matched no commit.

Three measured failures follow from deriving entries from commit subjects:

- A squash replaces N subjects with one, so the check goes red after every merge. `main` carries
  15 `chore: sync changelog` commits against 30 squash merges.
- `merge_unreleased` never drops an on-disk entry, so entries whose commits a squash erased
  persist. The ledger grows monotonically and cannot shrink.
- `.githooks/pre-push` triggers on the pushed ref's range but runs `update` against `HEAD`.
  Pushing a branch that is not checked out amends the wrong commit, leaves the pushed branch
  undocumented, and passes on retry.

Whether a digest describes the change set is a semantic question, and no check answers it.

## Decision

We will gate the changelog at two boundaries, following the Floor/Ceiling split of ADR-0015.

**Tier 1 — `[pre-merge]` gate (deterministic floor).** After the squash, `wt merge` checks the
single squashed commit: its subject is conventional, and it projects one well-formed entry.
That commit is the only place a bullet's source exists. Failure blocks the merge and leaves the
worktree and the target unchanged.

**Tier 2 — PR boundary (floor and ceiling).** The floor checks well-formedness, section
integrity, duplicate identities, and `entries ≤ commits`. The ceiling is an independent Skeptic
that receives only the commit list and the digest. It returns the ADR-0015 unified JSON, with
unrepresented commits in `issues`, and must report none.

The model never enters the release path. It proposes; a script validates and renders. No new
`CHANGELOG.md` syntax is added.

Outcomes map to ADR-0015 routes: a pass returns `continue` and opens the PR; a fixable failure
returns `remediate`; the cap or a missing model returns `blocked` for a human.

### Considered Options

- **Rejected: marker-based mechanical closure.** Entries carry invisible `<!-- covers: … -->`
  markers, so coverage is fully checkable. Rejected because it moves qualitative coverage into
  the floor, which ADR-0015 reserves for non-LLM execution, and adds syntax to a human-facing file.
- **Rejected: reachability pruning in `update`.** Drop entries whose subject no longer resolves
  to a reachable commit. Rejected because consolidation retires entries whose commits still exist,
  so pruning deletes intended output.
- **Rejected: keep the synchronisation check.** It passes on a wrong ledger, as measured above.
- **Rejected: a model confirmation.** A confirmation is an assertion. It always passes and costs
  one token.

## Consequences

- The ledger's unit becomes the squash commit and the PR, not the loop's keystrokes. A squash no
  longer desynchronises the ledger, and ghost entries cannot accumulate.
- Every merge pays one deterministic check. The ceiling runs only when the floor fails, so cheap
  failures fail before an expensive audit, per ADR-0015.
- The ceiling cannot run in GitHub CI, because the model command lives in a user-level
  `~/.config/worktrunk/config.toml`. CI enforces the floor and requires the accounting to be
  recorded in a PR-body section. A PR whose ceiling did not run returns `blocked` rather than passing.
- `max_loops` is 2 here, below the ADR-0015 default of 5. The ceiling is near-binary and cheap to
  satisfy, so further retries spend tokens without adding information.
- The attempt counter keys on the branch name, not `HEAD`, because each remediation amend changes
  the SHA. A SHA-keyed counter resets every attempt and never trips. The `[post-start]` hook clears it.
- `.githooks/pre-push` loses its subject and is removed with the guard it serves.
- Load-bearing assumption: the ceiling's verdict is recorded but not mechanically verified.
  Coverage rests on the Skeptic being independent and the accounting being visible in the PR.
