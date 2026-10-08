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

Goal: dispatch semantic-release from `main` and confirm the tag landed. The version comes from `feat`/`fix`/`!`
commits since the last tag. Run the five steps in order. Each one exits `0` before the next starts.

## Flow

| #   | Step     | Run                                        | Done when                                                                                                                                                             |
| --- | -------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Check    | `$SKILL_DIR/scripts/check.sh`              | `✔ working tree clean` · `✔ on branch main` · `✔ <N> commit(s) — conventional commits ok` · `✔ Phase 1 ok — all checks passed`                                          |
| 2   | Verify   | `$SKILL_DIR/scripts/verify.sh`             | `✔ ruff check · basedpyright · pytest passed` then `✔ Phase 2 ok — verification passed`                                                                                |
| 3   | Preview  | `$SKILL_DIR/scripts/dispatch.sh --dry-run` | `✔ next version: vX` plus the release-note body, or `⚠ no new version — nothing to release`                                                                            |
| 4   | Dispatch | `$SKILL_DIR/scripts/dispatch.sh`           | `Publish vX ?` → answer `a` → `✔ dispatched <owner/repo>` → `✔ workflow completed: success` → `✔ release workflow succeeded — run <id>`                                  |
| 5   | Confirm  | `$SKILL_DIR/scripts/confirm.sh`            | `release <tag> <kind> <date>  <url>` · `tag <tag> → <sha> (<type>) · reachable from main` · `main <sha> <subject>` · `changelog <sections>`                             |

## Failures

- Step 1 exits `1` on a dirty tree, off `main`, or on a commitlint rejection. With no commits ahead of `origin/main`, it warns and passes.
- Step 2 detects node/rust/python and prints one aggregated line per toolchain group. A failing step prints its 80-line tail and exits `1`. `pytest` warns instead (`⚠ pytest failed or not configured (rc=N)`) and the phase continues.
- Steps 3 and 4 exit `1` when semantic-release itself fails (`⚠ semantic-release dry-run failed (exit N)` plus a 20-line tail).
- Step 4 holds on `b` (`⚠ hold — not dispatched`, exit `0`). A failed release workflow exits `1` at `✘ workflow completed: <conclusion>`. No run visible within ~60s warns (`⚠ dispatched but no workflow run appeared within ~60s`) and exits `0`.
- Step 5 exits `1` when the tag is not reachable from the base branch. A re-rooted history otherwise keeps planning the same next version every time.

## Without a preview

`$SKILL_DIR/scripts/release-watch.sh --watch` dispatches from `main` and polls `release.yml` with no preview and no
prompt. Success prints `release success`, the run URL, and the new tag. Failure prints
`release <conclusion> — fetching logs` plus a 300-line log tail and exits `1`. Off `main`, or with an unresolvable
push remote, it exits `2`.

Set `GH_RELEASE_QUIET=1` to drop the `→` / `·` lines and the banner bar, leaving the phase banner and the `✔` / `⚠` / `✘` markers.
