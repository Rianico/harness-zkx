---
name: gh-release
description: >-
  Release via semantic-release dispatch. Validates conventional commits, runs verification, dispatches publish. TRIGGER: release, dispatch, publish, dry-run
argument-hint: |-
  "[--dry-run] -- dispatch semantic-release (dry-run previews version)"
metadata:
  managed-by: gh-router
---

# GH Release

Dispatch semantic-release from `main` — version from `feat`/`fix`/`!` since last tag.

## 1. Check

`$SKILL_DIR/scripts/check.sh` — tree clean, on `main`, `commitlint` passes.

## 2. Verify

`$SKILL_DIR/scripts/verify.sh` — runs repo verification (npm/cargo/ruff). Fail → BLOCKED.

## 3. Preview / Dispatch

`$SKILL_DIR/scripts/dispatch.sh [--dry-run]` — uses `GITHUB_TOKEN=$(gh auth token)` for `semantic-release --dry-run` preview; prompts `a: dispatch b: hold` then `gh api repos/<owner>/<repo>/dispatches`.

## 4. Confirm

`git log --oneline -5; git tag | tail -5; head -n 40 CHANGELOG.md`
