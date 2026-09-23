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
set rather than accuracy. At `a6b1d206` (2026-09-20) the check passed while `[Unreleased]` held
73 entries, 12 of them `herdr`, against 263 visible commits reachable from that commit and 3
`herdr` commits; two entry identities were duplicated. A global `entries ≤ commits` bound does not
catch it: 73 ≤ 263 holds, while the `herdr` scope alone is 12 entries against 3 commits.

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
integrity, duplicate identities, and a per-scope accounting bound: for every scope the ledger
carries, `entries(scope) ≤ commits(scope)`, where `commits(scope)` counts the commits reachable
from `HEAD` whose conventional subject projects an entry in that scope. A global
`entries ≤ commits` is kept only as a coarse pre-filter — it holds on the measured ledger
(73 ≤ 263) while the `herdr` scope alone is inflated (12 entries against 3 commits). The bound
counts and never deletes, so the rejection of reachability pruning below still applies. The
ceiling is an independent Skeptic
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
- Every merge pays one deterministic check. The ceiling runs only when the floor passes, so cheap
  failures fail before an expensive audit — the loop order of
  [ADR-0015](0015-goal-gate-and-convergence-loop-architecture.md) §4.
- The ceiling cannot run in GitHub CI, because the model command lives in a user-level
  `~/.config/worktrunk/config.toml`. CI enforces the floor and requires the accounting to be
  recorded in a PR-body section. A PR whose ceiling did not run returns `blocked` rather than passing.
- `max_loops` is 2 here, below the ADR-0015 default of 5. The ceiling is near-binary and cheap to
  satisfy, so further retries spend tokens without adding information.
- The attempt counter keys on the branch name and the hash of the squashed subject, not on `HEAD`:
  each remediation `--amend` changes the SHA, so a SHA-keyed counter resets every attempt and never
  trips. A changed subject earns fresh attempts; re-running an unchanged one does not, so a
  ledger-only fix that leaves the subject byte-identical does not reset the count and needs an
  explicit human route. The counter lives in the repository's shared git dir, resolved by git
  rather than string-built — `git rev-parse --path-format=absolute --git-common-dir` +
  `/gate-attempts/<branch>` — never a raw `<git-dir>` path: `--git-dir` is per-worktree (`.git`
  for the main worktree, `.git/worktrees/<name>` for a linked one, measured on git 2.55), so a raw
  path yields two counters and lets a capped branch be re-run from the other location with a fresh
  count. The `[post-start]` hook clears the counter.
- ADR-0015's Goal Gate predicate carries a `score ≥ 8/10` term. This ceiling is binary and never
  emits a score: it either reports `unrepresented: []` or it does not. That is a deliberate
  narrowing of the ADR-0015 predicate at this boundary, as `max_loops = 2` already is.
- A cap trip leaves no changelog-scoped escape. `wt merge --no-hooks` skips the whole gate, not the
  changelog check: it sets `verify = false` and yields an empty hook plan (worktrunk 0.76.0,
  `src/commands/merge.rs`), so the `ruff` and `pytest` commands in `[pre-merge]` do not run either.
  Declining the hook-approval prompt has the same effect. The human override must be defined
  explicitly rather than pointed at this flag.
- `.githooks/pre-push` loses its subject and is removed with the guard it serves.
- Load-bearing assumption: the ceiling's verdict is recorded but not mechanically verified.
  Coverage rests on the Skeptic being independent and the accounting being visible in the PR.
