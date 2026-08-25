# BDD scenarios — branch-worktree-pr

Scenarios for this orchestration's EDD loop. Deterministic steps use `wt`/`gh` signals; semantic assertions require human review of PR shape and history.

## Happy — single feat with two parallel write worktrees

```gherkin
Given ticket #42 "add token refresh" is unblocked and unassigned
  And docs/agents/issue-tracker.md declares GitHub as tracker
When  I claim the ticket (gh issue edit 42 --add-assignee @me)
  And create parent worktree `wt switch --create feat/add-token-refresh --base origin/main`
  And fan out two write worktrees `feat/add-token-refresh--tdd` and `feat/add-token-refresh--refactor`
  And each subagent returns COMPLETED in its isolated worktree
  And I merge children into parent from the child worktree: `wt merge feat/add-token-refresh` (target = parent feat; pre-merge gate green)
  And parent gate `npm run typecheck && npm test && npm run build` + `git diff --check` is green
  And CHANGELOG.md has one bullet under ## [Unreleased] with (#42)
Then  parent log shows atomic commits (bisectable)
  And PR opens as `gh pr create --base main --body "Closes #42"`
  And `gh pr view --json body --jq .body` ends with `Closes #42`
  And squash message will carry `Co-authored-by: <author>` when ticket author ≠ merger
  And `wt list --format=json` shows no child worktrees
  And PR state is OPEN — not merged
```

## Happy — map integration (huge scope)

```gherkin
Given Wayfinder map #10 "auth overhaul" with child tickets #11, #12 blocked by #11
When  I create integration branch in place: `git switch -c map/auth-overhaul <base>` on the main worktree
  And create `feat/token-refresh` with base `map/auth-overhaul` after #11 unblocks
  And create `feat/session-lifecycle` after #12 unblocks, base `map/auth-overhaul`
  And each feat's children merge via `wt merge <parent feat>` from the child worktree
  And feats merge into `map/auth-overhaul` via `wt merge map/auth-overhaul` from each feat worktree
  And map gate green, CHANGELOG bullets aggregated
Then  map PR targets main with body `Closes #10` (or parent tracker)
  And child feat PRs targeted `map/auth-overhaul` with `Part of #10`
```

## Edge — read-only ticket (no worktree)

```gherkin
Given ticket #50 "audit session state" is read-only
When  parent worktree `feat/audit-session` exists
Then  no child worktree is created
  And subagent runs in parent cwd or read-only mode
  And PR still follows squash hygiene
```

## Edge — tracker is local markdown (.scratch)

```gherkin
Given docs/agents/issue-tracker.md declares local markdown (.scratch/)
  And spec at `.scratch/feat-foo/spec.md` with Author: Alice <alice@example.com>
When  I create `feat/foo` from that spec
  And PR body links spec path `Closes .scratch/feat-foo/spec.md` (no GitHub #)
Then  squash message still carries `Co-authored-by: Alice <alice@example.com>` when merger ≠ Alice
  And CHANGELOG bullet uses linkless form
```

## Error — pre-merge gate blocks merge

```gherkin
Given child worktree `feat/foo--tdd` fails `pre-merge` gate (npm test red)
When  I run `wt merge` from child worktree `feat/foo--tdd` (target = parent branch)
Then  merge is blocked — hook exits non-zero, child remains in `wt list`
  And orchestrator re-dispatches fix in child worktree — no force merge
```

## Error — PR must not auto-merge

```gherkin
Given PR #99 is OPEN with body "Closes #42" and CI green
When  orchestrator reaches end of Phase 6
Then  model does NOT run `gh pr merge` or `wt merge main`
  And state is BLOCKED: awaiting PR approval
  And model may run `gh pr view --json` / `gh pr diff` for review assistance only
```

## Error — tag/release not proactive

```gherkin
Given PR #99 was approved and squash-merged to main
When  orchestrator reaches Phase 7
Then  model does NOT run `npm run release` or create tag `vX.Y.Z`
  And model presents dialog:
    [a] merge PR now?
    [b] tag/release vX.Y.Z after merge?
    [c] publish to registry? (interactive_shell, OTP)
    [d] hold — keep PR open
  And waits for user's explicit choice
  And only on user "b" does it run `npm run release -- X.Y.Z` (clean worktree, annotated tag)
  And only on user "c" via interactive_shell does it run `npm publish --registry ...`
```

## Error — fork supersede disclosed

```gherkin
Given PR #33 from fork cannot be pushed to
When  this skill detects `fork` authorAssociation
Then  it discloses to [[git-merge-pr]] — does not handle inline
  And expects `pr_prefix/33-*` branch with `Co-authored-by` trailer
```

## Deterministic verification checklist (EDD)

Run after each scenario:

```bash
wt list --format=json | jq '.[].branch'
git log --oneline --no-merges origin/main..HEAD | head
gh pr view <N> --json number,baseRefName,body,state --jq .
git show -s HEAD --format=%B | grep -q "Co-authored-by:" || echo "trailer check done"
cat CHANGELOG.md | rg "## \\[Unreleased\\]" -A 5
git status --porcelain  # only .lsz/tmp allowed untracked
```

## Semantic verification (skeptic)

- History is linear (squash boundary), one intent per atomic commit, no `fixup` noise in PR squash.
- CHANGELOG subsection (Added/Changed/Fixed) correct, imperative, no prose padding.
- PR body tells what was done, closes ticket/spec, and `by @<author>` when external — readable without opening ticket.
- No doc duplication — `git-workflow-conventions` owns reset/changelog, `git-merge-pr` owns fork shape, `worktrunk-guide` owns `wt` mechanics.
