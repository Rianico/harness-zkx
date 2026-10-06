---
name: pr-land
description: >-
  Create PR, watch verification checks, and squash-merge via gh api. Use when opening pull requests, monitoring CI check-runs, or merging approved PRs.
arguments: title_or_branch
argument-hint: |-
  "[--title '…'] [--body '…' | --body-file FILE] [--base main] [--head BRANCH] [--watch] [--merge] [--draft] [--no-stamp] [--squash-message '…' | --squash-message-file FILE]"
metadata:
  managed-by: gh-router
---

# PR — Create → Watch → Squash-Merge

Deterministic GitHub PR lifecycle via `gh api` (avoids `gh pr create` GQL `Head sha blank`). Owns the `POST pulls` → `poll every check` → `PUT merge squash` loop. Description authoring composes with `pr-enhance` — see [Body Preflight](#body-preflight).

**Ledger.** The PR carries curated entries under `## [Unreleased]` in `CHANGELOG.md` per `rules/common/git-convention.md` §5. The checks live in `scripts/changelog-gate.py`: invoke them, never restate them.

## Script

`$SKILL_DIR/scripts/pr.py` (755, Python >=3.14 via `uv run`, `GH_TOKEN` via `gh auth`; accompanied by thin backward-compatible `$SKILL_DIR/scripts/pr.sh`). Repo identity and the check verdict come from the skill's shared modules — `$SKILL_DIR/../../lib/repo.sh` (push remote first; `gh repo view` only as last resort) and `$SKILL_DIR/../../lib/checks.sh` — re-implemented cleanly in Python.

```bash
uv run $SKILL_DIR/scripts/pr.py --watch --merge --title "feat: …" --body-file tmp/pr_body.md
uv run $SKILL_DIR/scripts/pr.py --title "feat: …" --body-file tmp/pr_body.md --check  # dry run
uv run $SKILL_DIR/scripts/pr.py --watch --merge --body-file tmp/pr_body.md  # infers head/base/title only
```

Flags: `--base` (default `default_branch()` — push-remote slug → `origin/HEAD` → `main`), `--head` (`git rev-parse --abbrev-ref HEAD`), `--title` (default `git log -1 --pretty=%s`), `--body` / `--body-file` (required to open a PR — takes no template default), `--squash-message` / `--squash-message-file` (explicit squash commit message; mutually exclusive; sanitized through the same hygiene as a derived message), `--watch` (poll **every** check on the PR via `gh pr checks --json name,bucket`, 60×10s), `--merge` (requires a green watch; waits `mergeable_state clean`, refuses otherwise, then `PUT merge squash`), `--draft` (keep the PR draft after stamping — skips the ready flip; default ends a newly created PR ready; an existing open PR is never readied or re-drafted, and a reused draft without `--draft` exits `1` naming the manual `gh pr ready` remediation), `--no-stamp` (skips auto-stamping `(#NUM)` into `CHANGELOG.md`; the ready flip still happens).

## Body Preflight

The caller authors the description. Draft it with `pr-enhance` before landing:

1. `uv run $SKILL_DIR/../pr-enhance/scripts/analyze-pr.py [base|pr_url] > tmp/pr.json`
2. Draft `tmp/pr_body.md` from `tmp/pr.json` — see [pr-enhance](../pr-enhance/SKILL.md) §Workflow step 2.
3. Pass `--body-file tmp/pr_body.md` to `pr.py`.

## Invariants & Gates

- **Title Length Gate**: Strict limit `TITLE (#NUM) <= 100` chars. Keep raw `--title` ≤ 90 chars to allow room for ` (#NNN)`.
- **Changelog Auto-Stamping**: When `CHANGELOG.md` carries unattributed entries in `## [Unreleased]`, `pr.py` automatically commits and pushes `(#PR)` attribution to the branch (disable via `--no-stamp`).
- **Pre-flight Push**: The current working branch must be pushed to remote before running `pr.py`.
- **Squash Body Hygiene**: Strips HTML comments, fenced ```mermaid blocks, line-anchored `<details>…</details>` blocks (a `<details>` opened mid-line is prose and is left alone), the review-only `## Architecture` / `## Verification Evidence` sections, `## Checklist` items, `Landing:` / `Ledger-Waiver:` directives, and empty headings; unclosed fences/blocks stop at the next heading, `Closes` keyword, or trailer line. Preserves `## Summary`, `## What Changed`, `## Blast Radius & Safety`, `## Evidence`, `Closes #NN` on standalone lines, and `Co-authored-by` trailers, appending the latter automatically. The sanitizer is idempotent — the merge path cleans twice. Refuses bodies with raw `CODE_AUTHORS` token.
- **Body Gate**: `pr.py` refuses create or update with no `--body`/`--body-file`, or with a body that is empty or the unfilled `.github/pull_request_template.md` — exit `1` with remediation.
- **Fail-Closed Squash Gate**: a squash merge always carries an explicit `commit_message` — from `--squash-message`/`--squash-message-file` or derived from the PR body. There is no path that omits it; an empty/template body without an explicit message exits `1` with remediation naming `--squash-message`. GitHub's commit-subject synthesis is never a supported outcome.
- **Dry-run Gate (`--check`)**: Runs all validation gates (title budget, token checks, trailer generation) without opening a PR.
- **CI Runs Once Ready**: Workflows trigger on `opened`/`synchronize`/`reopened`/`ready_for_review` and every job skips drafts; jobs stage `changelog-gate` → `typecheck` → `tests`. CI is deliberately silent while draft and runs the full chain once the ready flip lands.

## Flow

1. **Create/reuse** — `GET pulls?head=owner:HEAD` → reuse `number` + `PATCH title/body` if exists, else `POST pulls` (always `draft=true`) → `number` + `html_url`. Auto-stamps `(#$NUM)` into unattributed unreleased entries in `CHANGELOG.md` and pushes to branch (disable via `--no-stamp`). **Draft handshake**: after stamping, a new PR is flipped ready via `gh pr ready` so CI's `ready_for_review` fires; a failed flip prints the verbatim manual command and exits `1`. `--draft` keeps it draft. Existing open PRs are reused untouched — never readied, never re-drafted.
2. **Watch** (if `--watch`) — every check-run *and* commit status counts: `gh pr checks --json name,bucket` → `checks_verdict`. `success` → continue; `failure` (`fail`/`cancel`) → targets failing run ID from check link or completed failed run, runs `gh run view $RUN_ID --log-failed` (fallback `--log`) tail 200 + `gh pr checks` dump → `exit 1`; anything else — `pending`, an unrecognised bucket, or no checks reported yet — keeps polling to 60×10s, then times out. Never green on a partial verdict: the old name allowlist (`verify`/`check`/`changelog-check`) reported success off one check while others were still running.
3. **Merge** (if `--merge`) — always requires a green watch (even with `--no-watch`), then polls `pulls/$NUM mergeable_state` (5×2s) and **refuses** unless `clean` → `PUT pulls/$NUM/merge merge_method=squash`. The squash body cleans review-only ephemera from the PR body — HTML comments, fenced ```mermaid blocks, line-anchored `<details>…</details>` blocks (mid-line `<details>` is prose, left alone), the `## Architecture` / `## Verification Evidence` sections, `## Checklist` items, `Landing:` / `Ledger-Waiver:` directives, and empty headings, with unclosed fences/blocks stopping at the next heading, `Closes` keyword, or trailer line — while preserving authored sections (`## Summary`, `## What Changed`, `## Blast Radius & Safety`, `## Evidence`), `Co-authored-by` provenance trailers, and closing directives (`Closes #NN` on standalone lines), so GitHub auto-closes linked issues when the squash commit lands on the base branch; the sanitizer is idempotent (this cleaning runs twice on the merge path); `commit_title` is `<title> (#N)`. The message is `--squash-message`/`--squash-message-file` when given, else derived from the PR body; if that derivation is empty (body empty, repo template, or procedural noise only), the merge **refuses** with exit `1` — `commit_message` is never omitted and commit-subject synthesis never happens.

   An explicit `commit_message` disables GitHub's own co-author auto-attribution, so the
   merge step rebuilds it first: one `Co-authored-by` trailer per distinct PR commit
   author except the merger (PR author included; dedupe by lowercase email, skipping
   emails already trailered case-insensitively), spliced ahead of the first
   `Closes`/`Fixes`/`Resolves`/`Refs` directive line. The token gate runs
   only on a body that actually becomes the squash message: a body still holding the
   raw `CODE_AUTHORS` template token is refused pre-merge with remediation.
   Line length limits apply strictly to the commit title (`TITLE (#NUM) <= 100`),
   while body line limits are dropped (aligning with commit #135).
   An empty body, or one identical to the repo template, is refused with exit `1` and
   remediation naming `--squash-message` — the merge never omits `commit_message` and
   never falls back to commit-subject synthesis, so the token can never reach a commit
   that way. `--check` runs the same gates the merge runs (fail-closed squash gate, token,
   trailers, title length) and prints the
   trailers that would be appended; it evaluates local `--body` / `--body-file` and creates nothing.

Fail-loud, no secrets in logs. Re-trigger is model-driven: script returns failure info, model edits, pushes, and re-runs `--watch --merge`. Exit: `0` ok · `1` checks failed, body refused, ready flip failed, or merge refused · `2` usage / unusable head ref. PR URL on stdout, progress on stderr.
