---
name: gh-router
description: >-
  GitHub delivery router for PR lifecycle, branch state, and releases. Reconciles merge/rebase conflicts, creates and merges PRs, watches CI, and dispatches releases. Use when a PR needs submitting, watching, or merging, a branch has conflicts or needs orienting, CI fails, or cutting a release.
argument-hint: |-
  gh-release [--dry-run] -- changelog and publish via dispatch
  pr-conflict [--file PATH] [--all] [--json] -- extract conflict hunks and commit intent
  git-diff-digest <spec> [PATH_FILTER] [--commit SHA] [--file PATH] [--hunks] [--max-lines N] [--yaml|--json] -- brief a commit range
  pr-enhance [base|pr_url] -- PR description generation
  pr-refine <number> -- take over a contributor's PR (Flow A/B), then hand to pr-land
  pr-land [--watch --merge] -- create PR, watch checks, squash-merge
metadata:
  manage: [gh-release, pr-land, pr-enhance, pr-refine, pr-conflict, git-diff-digest]
---

# GH Router

Goal: route GitHub work — diagnose, reconcile, land, release. Run one script per operation. Read its brief output instead of re-deriving it with `gh pr view`, `gh run list`, or `gh api …/jobs`.

## Common operations

| Phase & Goal | Run | Output |
| --- | --- | --- |
| **0: Orientation** | | |
| See where I stand | `$SKILL_DIR/scripts/state.sh` | 4 lines · `branch  <head> → <base> (ahead N, behind M)` · `pr  #N <mergeable>/<state> checks ok/total` (`-` when no PR) · `guard  ledger ok`, `ledger has findings`, or `no changelog script` · `main  <sha> <subject> (<tag>)` |
| Brief a commit range | `uv run $SKILL_DIR/subskills/git-diff-digest/scripts/brief.py <spec>` | text brief: commits, files, areas, signals |
| **1: Prep & Authoring** | | |
| Install the canonical PR template | `$SKILL_DIR/scripts/install-template.sh [--target DIR] [--check] [--force] [--dry-run]` | `installed:` / `already installed:` / `clean:` / `dry-run:` exit 0 · `drift:` / `missing:` / `refused:` exit 1 · usage exit 2 · missing or unusable source exit 3 |
| Draft a PR body from the digest | `uv run $SKILL_DIR/subskills/git-diff-digest/scripts/brief.py '<base>...HEAD' --pr --yaml` | the brief payload plus its `landing` block — the change-fact source for the body |
| Refresh an open PR description | `uv run $SKILL_DIR/subskills/pr-land/scripts/pr.py --title … --body-file …` | reuses the open PR for the head branch, PATCHes title/body, leaves its draft state alone. Prints `PR <url>` on stdout |
| **2: Conflict Reconcile** | | |
| Triage unmerged conflicts | `uv run $SKILL_DIR/subskills/pr-conflict/scripts/extract_conflict_context.py` | `repo: <root>` · `conflicted files: N` · one row per path: path, conflict type, stages, hunk count |
| Inspect one conflict | `uv run $SKILL_DIR/subskills/pr-conflict/scripts/extract_conflict_context.py --file <path>` | `operation:`, `author intent:` (ours/theirs sha, author, subject), compact hunks |
| **3: Landing & CI** | | |
| Create PR, watch checks, merge | `uv run $SKILL_DIR/subskills/pr-land/scripts/pr.py --watch --merge --body-file .lsz/tmp/pr_body.md --squash-message-file .lsz/tmp/squash_message.md` | `PR <url>` → `checks success` → `merged #N (squash) to main` |
| Watch a workflow | `$SKILL_DIR/scripts/ci.sh watch <run-id>` | quiet poll → `✔ run <id> completed: success`, else `✘ run <id> <conclusion>` exit 1 |
| Recent runs and step costs | `$SKILL_DIR/scripts/ci.sh runs [--branch B] [--limit N]` | one line per run (`#<id> <name> <conclusion> <dur>s`) plus its slowest steps (`Run all tests=15s`) |
| Why did a run fail | `$SKILL_DIR/scripts/ci.sh why <run-id>` | `▸ <job> › <step>` per failing step, then a 20-line log tail (exit 1). A green run reports `✔ run <conclusion> — nothing to explain` (exit 0) |
| **4: Release & Sync** | | |
| Preflight before releasing | `$SKILL_DIR/subskills/gh-release/scripts/check.sh` | tree, branch, and conventional-commit checks — one line each. Exits 1 on a dirty tree, off `main`, or a commitlint rejection |
| Verify before releasing | `$SKILL_DIR/subskills/gh-release/scripts/verify.sh` | one aggregated line, e.g. `✔ ruff check · basedpyright · pytest passed`. A failing step prints its tail only on failure |
| Cut a release | `$SKILL_DIR/subskills/gh-release/scripts/dispatch.sh [--dry-run]` | next-version preview → publish confirm → dispatch → workflow completion |
| Confirm a release landed | `$SKILL_DIR/subskills/gh-release/scripts/confirm.sh` | release tag, tag reachability from `main`, the `main` tip, and the changelog sections |
| Sync the changelog after a merge | `$SKILL_DIR/scripts/changelog.sh sync [--apply]` | `✔ CHANGELOG.md ledger is valid and curated` exit 0, else `✘ … ledger has findings` exit 1. Without the ledger gate: `rebuild would change N lines`, refusing more than 40 |

Run ids come from `ci.sh runs` or a PR's checks. `--help` prints a script's flag surface offline. The scripts `check.sh`, `verify.sh`, and `dispatch.sh` accept no `--help` — calling them starts the phase.

## Subskills (load for the deep flow)

| Subskill | Owns | Trigger |
| --- | --- | --- |
| `gh-release` | check → verify → preview → dispatch → confirm | `release`, dispatch semantic-release |
| `pr-land` | create → watch checks → squash-merge | `pr create`, `pr watch`, `pr merge` |
| `pr-conflict` | extract conflict hunks + commit intent → reconcile → continue | `git conflict`, `merge conflict`, `rebase conflict` |
| `pr-enhance` | own-PR description and diagram generation | `submit PR`, own-PR prose |
| `pr-refine` | refine / take over someone's PR up to push | `refine`, `take over`, `supersede`, land someone's PR |
| `git-diff-digest` | range → brief payload (commits, files, areas, signals) | `what changed`, `base..head range`, `range brief` |

Read `$SKILL_DIR/subskills/<name>/SKILL.md` for the deep flow: flags, title limits, gate refusals, and exit codes.

## Conventions

- Scripts beat raw `gh`: same queries, one call, brief output, deterministic exit codes.
- Exit codes: `0` ok · `1` failed check / verification · `2` usage · `3` missing tool.
- `GH_RELEASE_QUIET=1` drops informational lines. `NO_COLOR` disables ANSI.
