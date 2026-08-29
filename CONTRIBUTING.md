# Contributing to everything-claude-code

## Conventional commits

- `feat[(scope)]: description` → MINOR, `fix[(scope)]:` → PATCH, `feat!:` / `BREAKING CHANGE:` → MAJOR
- Other types `docs|style|refactor|perf|test|build|ci|chore|revert` hidden unless `!`
- Scope is noun, description imperative present, lowercase, no period, ≤72 chars
- Enforced by `commitlint` + `husky` (`npx commitlint --from=origin/main --to=HEAD`)

## Changelog

`CHANGELOG.md` has two writers: `changelog-preview.yml` (on `push` to `main`) stages notes under `## [Unreleased]` via `scripts/changelog-unreleased.py update`; `release.yml` (on `repository_dispatch`/`workflow_dispatch`) runs `scripts/changelog-unreleased.py clear` then `semantic-release` owns versioned sections. Do not hand-edit versioned sections.

## Before PR

`uv run ruff check . && uv run basedpyright && uv run pytest` must pass. See `AGENTS.md` for agent rules.
