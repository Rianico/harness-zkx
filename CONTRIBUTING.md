# Contributing to everything-claude-code

## Conventional commits

- `feat[(scope)]: description` → MINOR, `fix[(scope)]:` → PATCH, `feat!:` / `BREAKING CHANGE:` → MAJOR
- Other types `docs|style|refactor|perf|test|build|ci|chore|revert` hidden unless `!`
- Scope is noun, description imperative present, lowercase, no period, ≤72 chars
- Enforced by `commitlint` + `husky` (`npx commitlint --from=origin/main --to=HEAD`)

## Changelog

`CHANGELOG.md` `## [Unreleased]` guarded by `pre-push` hook (`warn+block`, `uv run python scripts/changelog-unreleased.py update`) and `changelog-check.yml` (`pull_request` required, `diff -q` vs generated); `release.yml` runs `scripts/changelog-unreleased.py clear` then `semantic-release` owns versioned sections. Do not hand-edit versioned sections. Hidden types `style|chore|refactor|test|build|ci` only appear when `!`/`BREAKING CHANGE`.

## Before PR

`uv run ruff check . && uv run scripts/typecheck-budget.py && uv run pytest` must pass. See `AGENTS.md` for agent rules. The budget is inert until it is seeded once: `uv run scripts/typecheck-budget.py --seed`.

Do not run a repo-wide `ruff format`: `target-version` is `py314` while the standalone scripts under `skills/**/scripts/` declare `requires-python` floors back to `3.11`, so the formatter rewrites `except (A, B):` into the PEP 758 form only 3.14 parses — silently breaking the floor those scripts advertise to `uv run`.
