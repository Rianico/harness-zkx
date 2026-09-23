# 16. Changelog Ledger Gate with Deterministic Floor and Adversarial Accounting

Date: 2026-09-20

## Status

Proposed — Applies [ADR-0015](0015-goal-gate-and-convergence-loop-architecture.md) to the
changelog boundary. Amends the earlier draft of this record in place: that draft assumed every
merge squashes, and the ledger's release source and landing rule have since changed. The
deterministic floor is implemented (`scripts/changelog-gate.py`); the ceiling is not.

Relates to [13. Worktree Python Shims with wt Gate Delegation and Auto-Scaffold](0013-worktree-python-shims-with-wt-gate-delegation.md)

The measurements below were read on 2026-09-22 at `e3badd92` (`main`) and at `a6b1d206`.

## Context

`CHANGELOG.md` `## [Unreleased]` is the ledger: the record of what has landed but not been
released. It is authored by branch commits while merges squash, so it is a projection of commit
subjects that the merge strategy destroys. The existing `check` diffs the file against
`scripts/changelog-unreleased.py update` output, so it verifies synchronisation with the commit
set, never accuracy. At `a6b1d206` the check passed while `[Unreleased]` held 73 entries, 12 of
them `herdr`, against 263 visible commits reachable from that commit and 3 `herdr` commits; two
entry identities were duplicated.

The failure is live on `main`. At `e3badd92` the same check fails — `changelog-check.yml` is red
on `push: main` and green on the PR head for the same work — because the PR's branch commits
minted entries that the squash destroyed, while `update` on `main` regenerates them from the
squash subject. Under attribution the same debt is one class, named per entry: of the 101
`[Unreleased]` entries at `e3badd92`, 74 name no PR at all and 27 resolve to a landing commit.
The entries whose commits the squash destroyed — `pr-land`, `pr-refine`, `pr-enhance`,
`gh-router/ci`, `gh-router/pr-land` — are unattributed, not mis-counted.

Two further decisions move the ledger's unit:

- **The ledger is the published changelog's source.** `release.yml` runs
  `changelog-unreleased.py clear` before `semantic-release`, whose notes generator rebuilds
  versioned sections from commit subjects. A curated ledger is therefore deleted at release and
  never published.
- **Landing is declared per PR, not fixed.** A PR whose commits are one change plus its docs and
  follow-up fixes lands as a squash; a PR carrying several changes lands as a merge commit that
  preserves its commits. A squash destroys the subjects a multi-entry digest rests on; a merge
  does not. Which one will happen is an input to the gate, and it must be known before the
  digest is written.

Whether a digest describes the change set is a semantic question, and no check answers it.

## Decision

We will gate the changelog at two boundaries, following the Floor/Ceiling split of ADR-0015.

**Entry birth — inside the ticket squash.** `update` runs in the `Copy` before `wt merge`, so
the squashed commit carries its code and its own entry. No `chore: sync changelog` commit is
minted anywhere; a `Target` accumulates one commit and one entry per ticket, which is what makes
the ticket squash the only place a bullet's source exists.

**Ticket-Boundary Check (deterministic floor).** After the squash, `wt merge` checks the single
squashed commit: its subject is conventional and projects exactly one well-formed entry. Failure
blocks the merge and leaves the worktree and the target unchanged.

**PR-Boundary Check (floor and ceiling).** The floor is deterministic; the ceiling curates.

- *Well-formedness, section integrity, duplicate identities, placeholders.* Every entry matches
  the renderer's bullet grammar, sits under a known section, shares no identity with another
  entry (using the generator's `(#N)`-stripping rule), and carries no placeholder.
- *Accounting, per PR.* Every entry names the PR that landed it, and for every `#N`:
  `entries(#N) ≤ commits(#N)`. `commits(#N)` is what that PR contributed to the log — one commit
  for a squash landing, whose subject carries `(#N)`, or the merge commit's second-parent range
  (`rev-list <merge>^1..<merge>^2`) for a merge landing. Merge subjects are read deliberately: the
  generator's own `--no-merges` read would skip exactly the commits a merge landing rests on. One
  basis, two scopes — the landing-scoped delta below is this rule for the PR that has not landed
  yet — so the aggregate is implied, no global pre-filter exists, and no scope ratio is computed.
  A violation names the PR that over-produced. The bound counts and never deletes, so the
  rejection of reachability pruning below still applies.
- *Attribution is mandatory.* An entry with no `(#N)`, or with one that resolves to no reachable
  commit, is unvalidated and fails. This is the failure class the projection model produced: the
  old scope ratio reported `herdr` as 12 entries against 3 commits, and attribution reports the
  same twelve as twelve entries that name no PR. The check verifies that a number exists and
  resolves, not that it is the *right* number for that entry — that stays the ceiling's job.
- *Landing-scoped delta.* The PR's ledger delta is bound to its declaration, on the same
  attribution: `squash ⟹ exactly one entry attributed to this PR`; `merge ⟹ 1 ≤ entries(#N) ≤
  commits(PR)`. Without this, a squashed PR raises its scopes' entry counts while contributing no
  commits, and `main` fails the accounting bound by construction.
- *Recorded waiver.* The only escape from `blocked` is `--waiver "<reason>"`. It accepts fixable
  findings and prints them with the reason; it never rescues a needs-human finding, and an empty
  reason is refused. The reason is written in the PR body's accounting section, so the bypass is
  visible rather than silent, and everything else — `ruff`, `pytest` — still runs.
- *Provenance.* Every `(#N)` in the ledger must appear in a reachable commit subject — the squash
  subject, or the merge subject `Merge pull request #N from …`, which the generator's own
  `--no-merges` read skips. The check verifies that a number exists, not that it is the right
  number for that entry.
- *Curation (ceiling).* An independent Skeptic receives only the commit list and the digest and
  returns the ADR-0015 unified JSON, with unrepresented commits in `issues`. Its contract is
  **representation, not enumeration**: it may rewrite, merge, and retitle entries, so a commit is
  unrepresented only when no entry describes it. Consolidation retires entries whose commits
  still exist — the same reasoning that rejects pruning below.
- *Declaration.* `Landing: squash|merge` is written in the PR body before curation, so the digest
  can be written to match it. `pr-land` reads it and selects the merge method.

The model never enters the release path. It proposes; a script validates and renders. No new
`CHANGELOG.md` syntax is added.

Outcomes map to ADR-0015 routes: a pass returns `continue`; a fixable failure returns
`remediate`; the cap or a missing model returns `blocked` for a human.

### Considered Options

- **Rejected: marker-based mechanical closure.** Entries carry invisible `<!-- covers: … -->`
  markers, so coverage is fully checkable. Rejected because it moves qualitative coverage into the
  floor, which ADR-0015 reserves for non-LLM execution, and adds syntax to a human-facing file.
- **Rejected: reachability pruning in `update`.** Drop entries whose subject no longer resolves to
  a reachable commit. Rejected because consolidation retires entries whose commits still exist, so
  pruning deletes intended output.
- **Rejected: keep the synchronisation check.** It passes on a wrong ledger, as measured above,
  and curation rewrites entries, so the file can never equal `update`'s output again. Both
  enforcement points are retired: `.githooks/pre-push` and `changelog-check.yml`.
- **Rejected: a model confirmation.** A confirmation is an assertion. It always passes and costs
  one token.
- **Rejected: derive-at-release (git-cliff / Commitizen style).** Generate notes from the tag range
  and commit no `[Unreleased]` at all. It is the field's default and would remove the two-tier
  machinery, but it gives up the in-tree ledger: the change set becomes visible only after the
  release, and curation has nowhere to happen before the tag.
- **Rejected: a scope-ratio bound with a shrink-only baseline.** `entries(scope) ≤ commits(scope)`
  counts a different basis — every commit reachable from `HEAD` — than the landing delta, so the
  verdict depends on which branch you stand on: green on the `Target`, red on `main` for the same
  digest, and every author pays for debt they did not create. Attribution derives the aggregate
  from the same basis as the delta, so one basis covers both scopes and no baseline is needed.
- **Rejected: optional attribution.** Verifying only the `(#N)`s that are present leaves
  unattributed entries unvalidated, so a ghost is smuggled by omitting the number.
- **Rejected: keep `([hash](url))` provenance.** Today's released sections link every entry to a
  commit. It cannot be authored before the merge: at curation time a squashed PR's commit does not
  exist, and a curated entry may represent several commits. `(#N)` is what survives.

## Consequences

- **`git-convention` §5 changes.** "Atomic inside, squash outside" becomes: atomic commits inside
  the topic, landing declared per PR — squash when the PR's commits are one change plus its docs
  and follow-up fixes, merge when it carries several changes. §5 also owns the obligation table:
  which artifacts each PR scenario carries and on which surface. The PR skills point at it and
  restate nothing, and no skill describes the checks — they invoke the gate.
- **`main` inherits the ticket commits of merged PRs.** A merged PR contributes its ticket commits
  to the log; a squashed PR contributes one subject. The ticket boundary already squashes
  intra-ticket churn, so this is smaller than the branch-commit era, but it is a real change in
  what `main`'s log looks like.
- **The ceiling runs only when the floor passes**, so cheap failures fail before an expensive
  audit — the loop order of [ADR-0015](0015-goal-gate-and-convergence-loop-architecture.md) §4.
- **The ceiling cannot run in GitHub CI**, because the model command lives in a user-level
  `~/.config/worktrunk/config.toml`. CI enforces the floor and requires the accounting to be
  recorded in a PR-body section. A PR whose ceiling did not run returns `blocked` rather than passing.
- **`max_loops` is 2 here**, below the ADR-0015 default of 5. The ceiling is near-binary and cheap
  to satisfy, so further retries spend tokens without adding information.
- **The attempt counter keys on the branch and the PR number**, not on `HEAD`: each remediation
  `--amend` changes the SHA, so a SHA-keyed counter resets every attempt and never trips, while a
  PR number survives every amend. It lives in the repository's shared git dir, resolved by git
  rather than string-built — `git rev-parse --path-format=absolute --git-common-dir` +
  `/gate-attempts/<branch>` — never a raw `<git-dir>` path: `--git-dir` is per-worktree (`.git` for
  the main worktree, `.git/worktrees/<name>` for a linked one, measured on git 2.55), so a raw path
  yields two counters and lets a capped branch be re-run from the other location with a fresh count.
  The `[post-start]` hook clears the counter.
- **The override is a recorded waiver, not a flag.** A cap trip's escape is `--waiver "<reason>"`,
  changelog-scoped and printed into the job log. `wt merge --no-hooks` is not it: it sets
  `verify = false` and yields an empty hook plan (worktrunk 0.76.0, `src/commands/merge.rs`), so
  `ruff` and `pytest` skip too, and declining the hook-approval prompt has the same effect. The
  waiver needs no second human — it exists to make the bypass visible, and a second approver would
  make it unreachable in a single-maintainer repo, recreating the deadlock the counter reset
  removed. A waiver that becomes routine is drift.
- **The scaffold owns the bytes.** `changelog-check.yml`, `.githooks/pre-push`, `.husky/pre-push`,
  `.releaserc.json`, and `scripts/changelog-unreleased.py` are replaced byte-identically by
  `scaffold --update` and hash-pinned in `tests/scaffold/test_templates.py`; `changelog-check.yml`
  is a required PR check. Retiring the guards, moving the notes source, and shipping the gate are
  therefore scaffold template changes plus a branch-protection change, not repo edits.
- **The release path changes.** Notes come from the ledger: a `generateNotes` plugin placed after
  `@semantic-release/release-notes-generator` can replace `nextRelease.notes` (the step is a chain,
  each plugin receiving the previous output), and `@semantic-release/changelog` prepends that string
  under the title. `changelog-unreleased.py clear` must move to *after* capture — as a `release.yml`
  step it currently deletes the source.
- **ADR-0015's Goal Gate predicate carries a `score ≥ 8/10` term.** This ceiling is binary and never
  emits a score: it either reports `unrepresented: []` or it does not. That is a deliberate narrowing
  of the ADR-0015 predicate at this boundary, as `max_loops = 2` already is.
- **Load-bearing assumptions, stated plainly.** The ceiling's verdict is recorded but not
  mechanically verified; coverage rests on the Skeptic being independent and the accounting being
  visible in the PR. The landing declaration is a judgement nothing verifies before the irreversible
  act; the floor can only check the digest against what was declared.
- **The migration is recorded, and it is a bridge, not a record.** At `e3badd92` the ledger carries
  74 unattributed entries (72 distinct identities), two duplicate identities, and one `(#N)` that
  resolves to nothing. A shrink-only baseline (`.config/changelog-unattributed-baseline.txt`,
  `--update-baseline`) records 71 identities as tolerated debt so the gate can be enabled now, while
  any *new* unattributed entry still fails. It cannot be permanent: a release empties `[Unreleased]`
  and every baselined identity with it, so the release job runs `--update-baseline` immediately
  after `clear` in the same commit, and the file is header-only once the migration is paid down. A
  baseline that has not shrunk across two releases is drift. Nothing here removes the debt —
  shrinking the ledger stays a human decision.
- `.githooks/pre-push` loses its subject and is removed with the guard it serves.
