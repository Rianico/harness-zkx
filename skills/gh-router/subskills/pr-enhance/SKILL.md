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

1. **Analyze** — `uv run $SKILL_DIR/scripts/analyze-pr.py [base|pr_url] > tmp/pr.json` — captures files changed, stats, categories (base, PR URL, or number; inferred from context if omitted). Keep artifacts in tmp dir (ephemeral).
2. **Draft** — from `tmp/pr.json` generate PR description and save to `tmp/pr_body.md`:

   ````markdown
   ## Summary

   [2-3 sentence why, based on diff]
   **Impact**: [X] files ([Y] +, [Z] -) · **Risk**: Low/Medium/High

   ## What Changed

   [grouped by feature/system; flag migrations/API changes]

   ## Architecture

   [Mermaid before/after only if structural shift]

   ```mermaid
   graph LR
     ...
   ```
   ````

   ## Checklist

   [review checklist derived from categories]

   <!-- Closing directives: one issue per line with keyword (never comma-separated like "Closes #1, #2") -->
   Closes #NN
   ````

   Extract related issue numbers from the branch name, commit messages, or user request. Always emit them on standalone lines at the bottom (`Closes #NN` / `Fixes #NN`) so GitHub links and auto-closes them upon merge.

3. **Review** — present draft, await approval, then create PR and clean tmp artifacts.
