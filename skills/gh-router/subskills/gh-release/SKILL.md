---
name: gh-release
description: >-
  Release dispatch via semantic-release. Validates conventional commits and runs verification. Use when dispatching releases, publishing packages, or running dry-run release checks.
argument-hint: |-
  "[--dry-run] -- dispatch semantic-release (dry-run previews version)"
metadata:
  managed-by: gh-router
---

# GH Release

Dispatch semantic-release from `main` — version from `feat`/`fix`/`!` since last tag.

## Phases

| # | Script | Banner | Output contract |
|---|--------|--------|-----------------|
| 2 | `verify.sh` | `━━━ Phase 2/3: Verify ━━━` | auto-detects `node`/`rust`/`python`; prints each `▸ lint/typecheck/test` substep with a one-line result (`✔ <step> passed`) — command output (warnings/test details) shown as a tail **only on failure**; ends `✔ Phase 2 ok`. |
| 3 | `dispatch.sh [--dry-run]` | `━━━ Phase 3/3: Preview → Dispatch → Watch ━━━` | single `semantic-release --dry-run` (token fetched once), prints only `✔ next version: vX` + condensed release-note body (full trace discarded) or `⚠ no new version`; prompt `a: dispatch (publish vX)  b: hold`; on dispatch polls `gh run list --workflow release.yml --event repository_dispatch` for new run (fallback `Verify and Release`), then **quiet-polls the run status** (no `gh run watch` frames) emitting nothing until completion; success → `✔ workflow completed: success` + tags/CHANGELOG head + run URL, failure → `✘ workflow <conclusion>` + `gh run view --log-failed`. No run in ~60s → `⚠ watch skipped` + manual check hint. |
| 4 | `release-watch.sh [--watch]` | `━━━ Watch release.yml ━━━` | `POST dispatches` (fallback `workflow_dispatch`) → polls `actions/workflows/release.yml/runs` by `head_sha`, quiet-polls `status/conclusion` (10s), `success` → tags + `git describe`, `failure` → `gh run view --log` tail 300 + `exit 1` for model fix |

All scripts source `scripts/_common.sh` for `phase`/`ok`/`warn`/`fail`/`step` helpers with ANSI (respects `NO_COLOR`). No duplicate dry-run; no `npm` prefix noise; no `--verbose` unless failed. Set `GH_RELEASE_QUIET=1` to suppress informational lines (`info`/`dim`/`step` + banner bar) — only `ok`/`warn`/`fail`/`phase` markers print, cutting each script to ~5 lines for context-limited harness runs.

## Run

```bash
$SKILL_DIR/scripts/check.sh
$SKILL_DIR/scripts/verify.sh
$SKILL_DIR/scripts/dispatch.sh --dry-run   # preview only
$SKILL_DIR/scripts/dispatch.sh             # preview → prompt → dispatch → quiet watch
$SKILL_DIR/scripts/release-watch.sh --watch  # dispatch + poll (no preview), dumps logs on fail
```

## Confirm

`git log --oneline -5; git tag | tail -5; head -n 40 CHANGELOG.md`
