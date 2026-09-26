---
name: pr-land
description: >-
  Create PR, watch verification checks, and squash-merge via gh api. Use when opening pull requests, monitoring CI check-runs, or merging approved PRs.
arguments: title_or_branch
argument-hint: |-
  "[--title '…'] [--body '…' | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--merge] [--draft] [--no-stamp]"
metadata:
  managed-by: gh-router
---

# PR — Create → Watch → Squash-Merge

Deterministic GitHub PR lifecycle via `gh api` (avoids `gh pr create` GQL `Head sha blank`). Complements `pr-enhance` (description) — this subskill owns the `POST pulls` → `poll every check` → `PUT merge squash` loop.

**Ledger.** The PR carries curated entries under `## [Unreleased]` in `CHANGELOG.md` per `rules/common/git-convention.md` §5. The checks live in `scripts/changelog-gate.py`: invoke them, never restate them.

## Script

`$SKILL_DIR/scripts/pr.py` (755, Python >=3.14 via `uv run`, `GH_TOKEN` via `gh auth`; accompanied by thin backward-compatible `$SKILL_DIR/scripts/pr.sh`). Repo identity and the check verdict come from the skill's shared modules — `$SKILL_DIR/../../lib/repo.sh` (push remote first; `gh repo view` only as last resort) and `$SKILL_DIR/../../lib/checks.sh` — re-implemented cleanly in Python.

```bash
uv run $SKILL_DIR/scripts/pr.py --watch --merge --title "feat: …" --body-file tmp/pr_body.md
uv run $SKILL_DIR/scripts/pr.py --watch --merge  # infers head/base/title/body
```

Flags: `--base` (default `default_branch()` — push-remote slug → `origin/HEAD` → `main`), `--head` (`git rev-parse --abbrev-ref HEAD`), `--title` (default `git log -1 --pretty=%s`), `--body` / `--body-file` (default `.github/pull_request_template.md`), `--watch` (poll **every** check on the PR via `gh pr checks --json name,bucket`, 60×10s), `--merge` (requires a green watch; waits `mergeable_state clean`, refuses otherwise, then `PUT merge squash`), `--draft`, `--no-stamp` (skips auto-stamping `(#NUM)` into `CHANGELOG.md`).

## Flow

1. **Create/reuse** — `GET pulls?head=owner:HEAD` → reuse `number` + `PATCH title/body` if exists, else `POST pulls` → `number` + `html_url`. Auto-stamps `(#$NUM)` into unattributed unreleased entries in `CHANGELOG.md` and pushes to branch (disable via `--no-stamp`).
2. **Watch** (if `--watch`) — every check-run *and* commit status counts: `gh pr checks --json name,bucket` → `checks_verdict`. `success` → continue; `failure` (`fail`/`cancel`) → targets failing run ID from check link or completed failed run, runs `gh run view $RUN_ID --log-failed` (fallback `--log`) tail 200 + `gh pr checks` dump → `exit 1`; anything else — `pending`, an unrecognised bucket, or no checks reported yet — keeps polling to 60×10s, then times out. Never green on a partial verdict: the old name allowlist (`verify`/`check`/`changelog-check`) reported success off one check while others were still running.
3. **Merge** (if `--merge`) — always requires a green watch (even with `--no-watch`), then polls `pulls/$NUM mergeable_state` (5×2s) and **refuses** unless `clean` → `PUT pulls/$NUM/merge merge_method=squash`. The squash body cleans procedural noise from the PR body (stripping HTML comments, `## Checklist` items, `Landing:` / `Ledger-Waiver:` directives, and empty headings) while preserving authored sections (`## Summary`, `## What Changed`), `Co-authored-by` provenance trailers, and closing directives (`Closes #NN` on standalone lines), so GitHub auto-closes linked issues when the squash commit lands on the base branch; `commit_title` is `<title> (#N)`. If the PR body is empty, identical to the repo template, or contains only procedural noise, `commit_message` is omitted to fall back to commit subjects.

   An explicit `commit_message` disables GitHub's own co-author auto-attribution, so the
   merge step rebuilds it first: one `Co-authored-by` trailer per distinct PR commit
   author except the merger (PR author included; dedupe by lowercase email, skipping
   emails already trailered case-insensitively), spliced ahead of the first
   `Closes`/`Fixes`/`Resolves`/`Refs` directive line. The token gate runs
   only on a body that actually becomes the squash message: a body still holding the
   raw `CODE_AUTHORS` template token is refused pre-merge with remediation.
   Line length limits apply strictly to the commit title (`TITLE (#NUM) <= 100`),
   while body line limits are dropped (aligning with commit #135).
   An empty body, or one identical to the repo template, omits `commit_message` as
   before and falls back to commit subjects — the token can never reach a commit that
   way. `--check` runs the same gates the merge runs (token, trailers, title length) and prints the
   trailers that would be appended; it evaluates local `--body` / `--body-file` and creates nothing.

Fail-loud, no secrets in logs. Re-trigger is model-driven: script returns failure info, model edits, pushes, and re-runs `--watch --merge`. Exit: `0` ok · `1` checks failed or merge refused · `2` usage / unusable head ref. PR URL on stdout, progress on stderr.
