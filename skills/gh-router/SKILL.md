---
name: gh-router
description: >-
  GitHub workflow router — release via dispatch, PR enhancement, and PR create/watch/merge. Use when releasing, dispatching semantic-release, submitting or refining PRs, or creating/merging PRs via gh api.
argument-hint: |-
  gh-release [--dry-run] -- changelog and publish via dispatch
  pr-enhance [base|pr_url] -- PR description generation
  pr-land [--watch --merge] -- create PR, watch checks, squash-merge
metadata:
  manage: [gh-release, pr-land, pr-enhance]
---

# GH Router

GitHub workflow router. Model-invocable — dispatches to `gh-release`, `pr-land`, or `pr-enhance` via subskill load.

## Subskills

| Subskill     | Trigger                              |
| ------------ | ------------------------------------ |
| `gh-release` | `release`, dispatch semantic-release |
| `pr-enhance` | `submit PR`, `refine PR`             |
| `pr-land`    | `pr create`, `pr watch`, `pr merge`, `squash merge` |

Load via `Read $SKILL_DIR/subskills/<name>/SKILL.md`.
