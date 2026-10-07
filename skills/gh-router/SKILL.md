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

Router for GitHub work: diagnose, reconcile, land, release. Every operation is one script call with a fixed
brief output — do not re-derive it with `gh pr view`, `gh run list`, or `gh api …/jobs`.

## Common operations

| Phase & Goal | Run | Output |
| --- | --- | --- |
| **0: Orientation** | | |
| See where I stand | `$SKILL_DIR/scripts/state.sh` | 4 lines: branch→base divergence · PR state + checks · changelog guard · base tip |
| Brief a commit range | `uv run $SKILL_DIR/subskills/git-diff-digest/scripts/brief.py <spec>` | commits, files, areas, signals |
| **1: Prep & Authoring** | | |
| Install the canonical PR template | `$SKILL_DIR/scripts/install-template.sh [--target DIR] [--check|--force|--dry-run]` | `installed:`/`already installed:`/`clean:`/`dry-run:` exit 0 · `drift:`/`missing:`/`refused:` exit 1 · usage exit 2 · missing/unusable source exit 3; `--target` must be an existing directory (default `.`), never overwrites without `--force` |
| Draft PR body from the digest | `uv run $SKILL_DIR/subskills/git-diff-digest/scripts/brief.py '<base>...HEAD' --pr --yaml` | brief payload: commits, files, areas, signals |
| Refresh existing PR description | `uv run $SKILL_DIR/subskills/pr-land/scripts/pr.py --title … --body-file …` | reuses PR by head branch; pass title/body or untouched |
| **2: Conflict Reconcile** | | |
| Triage unmerged conflicts | `uv run $SKILL_DIR/subskills/pr-conflict/scripts/extract_conflict_context.py` | repo-level unmerged paths, types, hunk counts |
| Inspect conflict & commit intent | `uv run $SKILL_DIR/subskills/pr-conflict/scripts/extract_conflict_context.py --file <path>` | operation + ours/theirs author intent + compact hunks |
| **3: Landing & CI** | | |
| Create PR, watch checks, merge | `uv run $SKILL_DIR/subskills/pr-land/scripts/pr.py --watch --merge --body-file tmp/pr_body.md` | `PR <url>` → `checks success` → `merged #N (squash) to main` |
| Watch a workflow | `$SKILL_DIR/scripts/ci.sh watch <run-id>` | quiet poll → `✔ run <id> completed: success`, or `✘` + exit 1 |
| Recent runs and step costs | `$SKILL_DIR/scripts/ci.sh runs [--branch B] [--limit N]` | one line per run + slowest steps (`Run all tests=15s`) |
| Why did a run fail | `$SKILL_DIR/scripts/ci.sh why <run-id>` | failing `job › step`, then the log tail |
| **4: Release & Sync** | | |
| Preflight before releasing | `$SKILL_DIR/subskills/gh-release/scripts/check.sh` | tree/branch/commit checks, one line each |
| Verify before releasing | `$SKILL_DIR/subskills/gh-release/scripts/verify.sh` | one line per lint/typecheck/test |
| Cut a release | `$SKILL_DIR/subskills/gh-release/scripts/dispatch.sh [--dry-run]` | `✔ next version: vX` → `a: dispatch / b: hold` → quiet watch |
| Confirm a release landed | `$SKILL_DIR/subskills/gh-release/scripts/confirm.sh` | release + URL · tag→commit · base tip · changelog sections |
| Sync changelog after a merge | `$SKILL_DIR/scripts/changelog.sh sync [--apply]` | `rebuild would change N lines` · refuses >40 lines churn |

Run ids come from `$SKILL_DIR/scripts/ci.sh runs`, a PR's checks, or `gh run list`. All paths are relative to
`$SKILL_DIR`; `--help` answers from the file header without `gh` or network.

## Subskills (load for the deep flow)

| Subskill | Owns | Trigger |
| --- | --- | --- |
| `gh-release` | check → verify → preview → dispatch → confirm | `release`, dispatch semantic-release |
| `pr-land` | create → watch checks → squash-merge | `pr create`, `pr watch`, `pr merge` |
| `pr-conflict` | extract conflict hunks + commit intent → reconcile → continue | `git conflict`, `merge conflict`, `rebase conflict` |
| `pr-enhance` | own-PR description and diagram generation | `submit PR`, own-PR prose |
| `pr-refine` | refine / take over someone's PR up to push | `refine`, `take over`, `supersede`, land someone's PR |
| `git-diff-digest` | range → brief payload (commits, files, areas, signals) | `what changed`, `base..head range`, `range brief` |

Read `$SKILL_DIR/subskills/<name>/SKILL.md` for full flag options (`--title`, `--body-file`, `--check`, `--no-stamp`), title length limits, exit codes, and failure contracts.

## Conventions

- Scripts beat raw `gh`: same queries, one call, brief output, deterministic exit codes.
- Exit codes: `0` ok · `1` failed check / verification · `2` usage · `3` missing tool.
- `GH_RELEASE_QUIET=1` drops informational lines; `NO_COLOR` disables ANSI.
