# Contributing to {project_name}
## Conventional commits
- `feat[(scope)]: description` → MINOR, `fix[(scope)]:` → PATCH, `feat!:` / `BREAKING CHANGE:` → MAJOR
- Other types `docs|style|refactor|perf|test|build|ci|chore|revert` hidden unless `!`
- Scope is noun, description imperative present, lowercase, no period, ≤72 chars
- Enforced by `commitlint` + `husky` (`npx commitlint --from=origin/main --to=HEAD`)
## Changelog
`CHANGELOG.md` `## [Unreleased]` guarded by `pre-push` hook (`warn+block`, `uv run python scripts/changelog-unreleased.py update`) and `changelog-check.yml` (`pull_request` required); `release.yml` runs `scripts/changelog-unreleased.py clear` then `semantic-release` owns versioned sections. Do not hand-edit versioned sections. Commit the sync as a hidden type (e.g. `chore: sync changelog unreleased section`) — a visible type re-triggers the guard and loops forever. Hidden types only appear when `!`/`BREAKING CHANGE`.
## Reporting Issues
Pick the template that matches your intent — see `.github/ISSUE_TEMPLATE/` (blank issues disabled, `config.yml` links #38):
| Intent | Template | Structure |
|---|---|---|
| **Bug** | `01-bug_report.yml` | **Exemplar #38**: Summary → Environment (Version/Module/Trigger) → Steps to Reproduce (paste-complete file + operation map + exact payload) → Expected vs Actual (quote diff/logs) → Impact & Trigger Conditions → Root Cause / Suggested Fixes (optional, numbered tradeoffs) |
| **Feature** | `02-feature_request.yml` | Problem → Proposal → Alternatives → Additional context |
- Bugs: paste-complete, prefer text over screenshots, include `read` hashes / payload and `autoFixes`/balance delta. Link #38 as style reference.
- Features: state problem + proposal at minimum; alternatives optional.
Prompt rule: when the model helps file an issue, infer `bug` vs `feat` from intent, ask for any missing `body` field of that form, and render via `gh issue create --template <file>`. View exemplar with `gh issue view 38 --json title,body --repo Rianico/dsh-better-edit`.
## Before PR
`uv run ruff check . && uv run basedpyright && uv run pytest` must pass. See `AGENTS.md` for agent rules.
## Pull Requests
Prefer topic branch → PR → squash merge. Keep one concern per PR; link the issue with `Closes #NN`.
### Description
PR body is auto-populated from `.github/pull_request_template.md`. Keep the four headings — delete `Architecture` when no structural change:
- **Summary** — 2-3 sentences on *why*; include `**Impact**: X files (Y +, Z -) · **Risk**: Low | Medium | High`.
- **What Changed** — grouped by system/feature, not file list; flag migrations / API changes.
- **Architecture** — Mermaid before → after only for structural/layering changes.
- **Checklist** — start from template checklist; add category-specific items.
CI (`changelog-check.yml`, `verify`) must be green before requesting review.
