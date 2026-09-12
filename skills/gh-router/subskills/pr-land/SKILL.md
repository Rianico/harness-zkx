---
name: pr-land
description: >-
  Create PR, watch verification checks, and squash-merge via gh api. Use when opening pull requests, monitoring CI check-runs, or merging approved PRs.
arguments: title_or_branch
argument-hint: |-
  "[--title '…'] [--body '…' | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--merge] [--draft]"
metadata:
  managed-by: gh-router
---

# PR — Create → Watch → Squash-Merge

Deterministic GitHub PR lifecycle via `gh api` (avoids `gh pr create` GQL `Head sha blank`). Complements `pr-enhance` (description) — this subskill owns the `POST pulls` → `poll check-runs` → `PUT merge squash` loop.

## Script

`$SKILL_DIR/scripts/pr.sh` (755, `set -euo pipefail`, `GH_TOKEN` via `gh auth`)

```bash
uv run $SKILL_DIR/scripts/pr.sh --watch --merge --title "feat: …" --body-file tmp/pr_body.md
uv run $SKILL_DIR/scripts/pr.sh --watch --merge  # infers head/base/title/body
```

Flags: `--base` (default `gh repo view --json defaultBranchRef` → `origin/HEAD` → `main`), `--head` (`git rev-parse --abbrev-ref HEAD`), `--title` (default `git log -1 --pretty=%s`), `--body` / `--body-file` (default `.github/pull_request_template.md`), `--watch` (poll `commits/$SHA/check-runs` for `verify`/`changelog-check`), `--merge` (waits `mergeable_state clean` then `PUT merge squash`), `--draft`.

## Flow

1. **Create/reuse** — `GET pulls?head=owner:HEAD` → reuse `number` + `PATCH title/body` if exists, else `POST pulls` → `number` + `html_url` + `head.sha`
2. **Watch** (if `--watch`) — `watch_checks` polls `commits/$SHA/check-runs` (30×10s): `success` → continue, `failure/timed_out/cancelled` → `gh run view $RUN_ID --log` tail 200 + `gh pr checks` dump → `exit 1` (model fixes → `git push` → re-run `--watch`)
3. **Merge** (if `--merge`) — ensures `watch_checks` passed, then polls `pulls/$NUM mergeable_state` (5×2s) → `PUT pulls/$NUM/merge merge_method=squash`

Fail-loud, no secrets in logs. Re-trigger is model-driven: script returns failure info, model edits, pushes, and re-runs `--watch --merge`.
