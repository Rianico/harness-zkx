---
name: pr-enhance
description: >-
  PR description authoring from the git-diff-digest brief: template sections, diagrams, and checklists. Use when submitting a PR, a body is still the unfilled template, or own-PR prose has gone stale.
arguments: base_or_pr
argument-hint: |-
  "[base|pr_url] -- base branch, PR URL (https://github.com/.../pull/123) or number (123); default: inferred from context — PR base or cwd's base, fallback main)"
metadata:
  managed-by: gh-router
---

# PR Description — Brief → Schema → Draft → Hand off

Author `.lsz/tmp/pr_body.md` — the file `pr.py --check` writes and re-reads — from the git-diff-digest brief, in the shape of the resolved template. The body seeds the squash message, so `pr-land` refuses it when empty or unfilled — see [pr-land](../pr-land/SKILL.md).

**Ledger.** The PR carries curated entries under `## [Unreleased]` in `CHANGELOG.md` per `rules/common/git-convention.md` §5. The checks live in `scripts/changelog-gate.py`: invoke them, never restate them.

## Workflow

Invoked via `/pr-enhance [base|pr_url]`; the base defaults to the PR base or the cwd's base, fallback `main`.

1. **Brief** — `uv run $SKILL_DIR/../git-diff-digest/scripts/brief.py '<base>...HEAD' --pr --yaml > .lsz/tmp/pr.json`. The brief is the change-fact source. *Done when* `.lsz/tmp/pr.json` holds the range.
2. **Schema** — `uv run $SKILL_DIR/scripts/analyze-pr.py --print-template` prints the drafting schema: the target repo's `.github/pull_request_template.md` when present, else the canonical `skills/gh-router/references/pull_request_template.md`. Run it from the target repo — the lookup is cwd-relative, so a probe from elsewhere silently resolves that repo's schema. *Done when* the command prints one path (`3` when neither exists).
3. **Draft** — write `.lsz/tmp/pr_body.md` from `.lsz/tmp/pr.json` under the printed schema's headings and order — never a hard-coded skeleton. Emit related issue numbers on standalone lines (`Closes #NN`), one per line, so GitHub links and auto-closes them. *Done when* every printed heading carries authored content.
4. **Hand off** — present the draft, await approval, then Read `pr-land` and follow its flow with `.lsz/tmp/pr_body.md` as `--body-file`; clean `.lsz/tmp/` once the PR is open. *Done when* the PR URL is printed and the scratch files are gone.

## Boundaries

- pr-enhance writes only its own `.lsz/tmp/` scratch (`pr.json`, `pr_body.md`): never install or edit the target repo's `.github/`, and never write into an upstream contributor's repo.
- With no repo template, draft the canonical shape and *mention* `skills/gh-router/scripts/install-template.sh` in the PR text — do not run it.
