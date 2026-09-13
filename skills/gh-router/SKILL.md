---
name: gh-router
description: >-
  GitHub workflow router — repo/PR/CI state, PR create-watch-merge, release dispatch via semantic-release. Use when a workflow run is failing, a branch needs orienting, a PR needs submitting, watching or merging, or a release needs cutting.
argument-hint: |-
  gh-release [--dry-run] -- changelog and publish via dispatch
  pr-enhance [base|pr_url] -- PR description generation
  pr-land [--watch --merge] -- create PR, watch checks, squash-merge
metadata:
  manage: [gh-release, pr-land, pr-enhance]
---

# GH Router

Router for GitHub work: diagnose, land, release. Every operation is one script call with a fixed
brief output — do not re-derive it with `gh pr view`, `gh run list`, or `gh api …/jobs`.

## Common operations

| I want to…                           | Run                                             | Output                                                                              |
| ------------------------------------ | ----------------------------------------------- | ----------------------------------------------------------------------------------- |
| See where I stand                    | `scripts/state.sh`                              | 4 lines: branch→base divergence · PR state + checks · changelog guard · base tip    |
| **Watch a workflow**                 | `scripts/ci.sh watch <run-id>`                  | quiet poll → `✔ run <id> completed: success`, or `✘` + exit 1                       |
| See recent runs and what they cost   | `scripts/ci.sh runs [--branch B] [--limit N]`   | one line per run + slowest steps (`Run all tests=15s Install uv=2s`)                |
| Why did a run fail                   | `scripts/ci.sh why <run-id>`                    | failing `job › step`, then the log tail                                             |
| Create a PR, watch it, merge it      | `pr-land/scripts/pr.sh --watch --merge`         | `PR <url>` → `checks success` → `merged #N (squash) to main`                        |
| Refresh an existing PR's description | `pr-land/scripts/pr.sh --title … --body-file …` | reuses the PR by head branch; pass title/body or they are not touched               |
| Draft PR body from the diff          | `pr-enhance/scripts/analyze-pr.py`              | changed files, stats, categories                                                    |
| Preflight before releasing           | `gh-release/scripts/check.sh`                   | tree/branch/commit checks, one line each                                            |
| Verify before releasing              | `gh-release/scripts/verify.sh`                  | one line per lint/typecheck/test                                                    |
| Cut a release                        | `gh-release/scripts/dispatch.sh [--dry-run]`    | `✔ next version: vX` → `a: dispatch / b: hold` → quiet watch                        |
| Confirm a release landed             | `gh-release/scripts/confirm.sh`                 | release + URL · tag→commit + reachability from base · base tip · changelog sections |

Run ids come from `scripts/ci.sh runs`, a PR's checks, or `gh run list`. All paths are relative to
`$SKILL_DIR`; `--help` answers from the file header without `gh` or network.

## Subskills (load for the deep flow)

| Subskill     | Owns                                          | Trigger                              |
| ------------ | --------------------------------------------- | ------------------------------------ |
| `gh-release` | check → verify → preview → dispatch → confirm | `release`, dispatch semantic-release |
| `pr-land`    | create → watch checks → squash-merge          | `pr create`, `pr watch`, `pr merge`  |
| `pr-enhance` | PR description and diagram generation         | `submit PR`, `refine PR`             |

Read `$SKILL_DIR/subskills/<name>/SKILL.md` for flags, exit codes and failure contracts.

## Conventions

- Scripts beat raw `gh`: same queries, one call, brief output, deterministic exit codes.
- Exit codes: `0` ok · `1` failed check / verification · `2` usage · `3` missing tool.
- `GH_RELEASE_QUIET=1` drops informational lines; `NO_COLOR` disables ANSI.
