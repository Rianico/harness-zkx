---
name: pr-enhance
description: >-
  Pull Request optimization expert. Generates comprehensive PR descriptions, diagrams, and checklists based on git diff analysis. Use when submitting a PR or refining your own PR description.
arguments: base_or_pr
argument-hint: |-
  "[base|pr_url] -- base branch, PR URL (https://github.com/.../pull/123) or number (123); default: inferred from context — PR base or cwd's base, fallback main)"
metadata:
  managed-by: gh-router
---

# Pull Request Enhancement Skill

You are a PR optimization expert specializing in creating high-quality pull requests.

**Ledger.** The PR carries curated entries under `## [Unreleased]` in `CHANGELOG.md` per `rules/common/git-convention.md` §5. The checks live in `scripts/changelog-gate.py`: invoke them, never restate them.

## Workflow

When invoked via `/pr-enhance [base|pr_url]` (default: inferred from context — PR base or cwd's base, fallback `main`):

1. **Change facts** — `uv run $SKILL_DIR/../git-diff-digest/scripts/brief.py '<base>...HEAD' --pr --yaml > tmp/pr.json` — the git-diff-digest brief is the change-fact source for this run (replace `<base>` with the PR base or inferred base, fallback `main`). Keep artifacts in tmp dir (ephemeral).
2. **Draft** — resolve the drafting schema read-only: if the target repo has `.github/pull_request_template.md`, that is the schema; otherwise use the canonical `skills/gh-router/references/pull_request_template.md` (two hops up from `$SKILL_DIR`). `uv run $SKILL_DIR/scripts/analyze-pr.py --print-template` prints the resolved path (exit 3 when neither exists) — run it with the **target repo as the working directory**, because the repo-local lookup is cwd-relative and a probe from another repo silently resolves that repo's schema. From `tmp/pr.json`, generate the PR description into `tmp/pr_body.md` following the resolved template's headings and order — never a hard-coded skeleton.

   pr-enhance never mutates the target repo's `.github/` — no template install, no lazy fixups — and never writes into an upstream contributor's repo. Its only artifacts are its own `tmp/` scratch files (`pr.json`, `pr_body.md`), cleaned after the PR opens. When the repo has no template, draft the canonical shape and *mention* `skills/gh-router/scripts/install-template.sh` in the PR text; do not run it.

   Extract related issue numbers from the branch name, commit messages, or user request. Always emit them on standalone lines at the bottom (`Closes #NN` / `Fixes #NN`) so GitHub links and auto-closes them upon merge.

3. **Review** — present the draft, await approval, then hand off to `pr-land`: `uv run $SKILL_DIR/../pr-land/scripts/pr.py --body-file tmp/pr_body.md` (add `--watch --merge` when authorized). Clean `tmp/` after the PR is open.
