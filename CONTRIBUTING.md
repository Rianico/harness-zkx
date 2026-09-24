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

Do not run a repo-wide `ruff format` yet: `target-version` is `py314` and every PEP 723 floor now matches it, so the formatter no longer crosses a floor a script declares. What blocks the pass is the typecheck budget — the formatter's layout changes which warnings `basedpyright` reports, and a shrink-only budget refuses to absorb that growth, so the sites it surfaces have to be paid down before the bytes can move.
