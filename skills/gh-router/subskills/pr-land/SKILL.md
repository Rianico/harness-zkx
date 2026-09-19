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

Deterministic GitHub PR lifecycle via `gh api` (avoids `gh pr create` GQL `Head sha blank`). Complements `pr-enhance` (description) — this subskill owns the `POST pulls` → `poll every check` → `PUT merge squash` loop.

## Script

`$SKILL_DIR/scripts/pr.sh` (755, `set -euo pipefail`, `GH_TOKEN` via `gh auth`). Repo identity and the check verdict come from the skill's shared modules — `$SKILL_DIR/../../lib/repo.sh` (push remote first; `gh repo view` only as last resort) and `$SKILL_DIR/../../lib/checks.sh` — so this script re-derives neither.

```bash
uv run $SKILL_DIR/scripts/pr.sh --watch --merge --title "feat: …" --body-file tmp/pr_body.md
uv run $SKILL_DIR/scripts/pr.sh --watch --merge  # infers head/base/title/body
```

Flags: `--base` (default `default_branch()` — push-remote slug → `origin/HEAD` → `main`), `--head` (`git rev-parse --abbrev-ref HEAD`), `--title` (default `git log -1 --pretty=%s`), `--body` / `--body-file` (default `.github/pull_request_template.md`), `--watch` (poll **every** check on the PR via `gh pr checks --json name,bucket`, 60×10s), `--merge` (requires a green watch; waits `mergeable_state clean`, refuses otherwise, then `PUT merge squash`), `--draft`.

## Flow

1. **Create/reuse** — `GET pulls?head=owner:HEAD` → reuse `number` + `PATCH title/body` if exists, else `POST pulls` → `number` + `html_url`
2. **Watch** (if `--watch`) — every check-run *and* commit status counts: `gh pr checks --json name,bucket` → `checks_verdict`. `success` → continue; `failure` (`fail`/`cancel`) → `gh run view $RUN_ID --log` tail 200 + `gh pr checks` dump → `exit 1`; anything else — `pending`, an unrecognised bucket, or no checks reported yet — keeps polling to 60×10s, then times out. Never green on a partial verdict: the old name allowlist (`verify`/`check`/`changelog-check`) reported success off one check while others were still running.
3. **Merge** (if `--merge`) — always requires a green watch (even with `--no-watch`), then polls `pulls/$NUM mergeable_state` (5×2s) and **refuses** unless `clean` → `PUT pulls/$NUM/merge merge_method=squash`. The squash body defaults to the PR body, so the `Co-authored-by` provenance trailer survives the squash; `commit_title` is `<title> (#N)`.

Fail-loud, no secrets in logs. Re-trigger is model-driven: script returns failure info, model edits, pushes, and re-runs `--watch --merge`. Exit: `0` ok · `1` checks failed or merge refused · `2` usage / unusable head ref. PR URL on stdout, progress on stderr.
