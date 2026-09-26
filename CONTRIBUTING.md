# Contributing to everything-claude-code

## Conventional commits

- `feat[(scope)]: description` → MINOR, `fix[(scope)]:` → PATCH, `feat!:` / `BREAKING CHANGE:` → MAJOR
- Other types `docs|style|refactor|perf|test|build|ci|chore|revert` hidden unless `!`
- Scope is noun, description imperative present, lowercase, no period, ≤72 chars
- Enforced by `commitlint` + `husky` (`npx commitlint --from=origin/main --to=HEAD`)

## Changelog

`CHANGELOG.md` `## [Unreleased]` gated by `scripts/changelog-gate.py` in `changelog-check.yml` (a PR run reads the `Landing:` declaration from the PR body; the `main` run is the durable one); `release.yml` runs `scripts/changelog-unreleased.py clear` then `semantic-release` owns versioned sections. Do not hand-edit versioned sections. Commit a sync as a hidden type (e.g. `chore: sync changelog unreleased section`) so it mints no ledger entry. Hidden types only appear when `!`/`BREAKING CHANGE`.

## Before PR

`uv run ruff check . && uv run ruff format --check . && uv run scripts/typecheck-budget.py && uv run pytest && uv run python3 scripts/changelog-gate.py ledger` must pass. See `AGENTS.md` for agent rules. The budget is inert until it is seeded once: `uv run scripts/typecheck-budget.py --seed`.

`ruff format` is gated too: the verify job runs `uv run ruff format --check .`, so the tree stays formatted. `[tool.ruff] exclude` keeps `*.md` out of that pass — ruff also reformats Python fences inside Markdown, and this repo's 73 reference docs are the product, not code to reflow.

Type checking has two suppression layers, and only one of them is reviewed. `.config/basedpyright-baseline.txt` is the shrink-only budget that `scripts/typecheck-budget.py` enforces; `.basedpyright/baseline.json` is basedpyright's own baseline, applied first, so it masks whatever the budget does not record. Measure the true inventory with that layer set aside — never with `--writebaseline`, which absorbs the budget's own entries:

```
uv run basedpyright --baselinefile /dev/null --outputjson > /tmp/tc.json
python3 -c "import json,collections; print(collections.Counter(d['severity'] for d in json.load(open('/tmp/tc.json'))['generalDiagnostics']))"
```

As of #121 that reports 3831 warnings and 169 errors against the budget's 995, so the budget's number is not this repo's warning count. And a change that alters a diagnostic's shape — wrapping a long call, reordering arguments — stops matching its entry in the second layer, so masked diagnostics resurface as apparent budget growth: check `.basedpyright/baseline.json` before believing such a report. Draining the error floor is #121.
