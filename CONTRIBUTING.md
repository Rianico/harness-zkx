# Contributing to everything-claude-code

## Conventional commits

- `feat[(scope)]: description` → MINOR, `fix[(scope)]:` → PATCH, `feat!:` / `BREAKING CHANGE:` → MAJOR
- Other types `docs|style|refactor|perf|test|build|ci|chore|revert` hidden unless `!`
- Scope is noun, description imperative present, lowercase, no period, ≤72 chars
- Enforced by `commitlint` + `husky` (`npx commitlint --from=origin/main --to=HEAD`)

## Changelog

`CHANGELOG.md` `## [Unreleased]` gated by `scripts/changelog-gate.py` in `changelog-check.yml` (a PR run reads the `Landing:` declaration from the PR body; the `main` run is the durable one); `release.yml` runs `semantic-release`, whose `scripts/release-changelog.mjs` plugin promotes the curated ledger into the versioned section and re-opens an empty `## [Unreleased]`. Do not hand-edit versioned sections. Commit a sync as a hidden type (e.g. `chore: sync changelog unreleased section`) so it mints no ledger entry. Hidden types only appear when `!`/`BREAKING CHANGE`.

## Before PR

`bash scripts/check.sh` (runs ruff check, ruff format --check, basedpyright --warnings, pytest) plus `uv run python3 scripts/changelog-gate.py ledger` must pass. The `.githooks/pre-commit` hook runs the gate automatically on commit. Normal escape hatch when the suite is not yours to run: `HARNESS_CHECK_SKIP_TESTS=1 git commit ...` runs the gate without pytest. `git commit --no-verify` is a last resort only — repo rules (`rules/common/gotcha.md`) forbid agents from using it. Setup is one-time per clone: `git config core.hooksPath .githooks` — that setting is repository-local and not versioned, so a fresh clone needs it again. See `AGENTS.md` for agent rules.

`ruff format` is gated too: the verify job runs `uv run ruff format --check .`, so the tree stays formatted. `[tool.ruff] exclude` keeps `*.md` out of that pass — ruff also reformats Python fences inside Markdown, and this repo's 73 reference docs are the product, not code to reflow.

Type checking is native: `uv run basedpyright --warnings`. There is no separate budget script anymore. `.basedpyright/baseline.json` is the only remaining baseline; it must stay empty and `tests/test_typecheck_native.py` keeps it that way. Measure the true inventory with that layer set aside — never with `--writebaseline`, which absorbs the current state into a masking baseline:

```
uv run basedpyright --baselinefile /dev/null --outputjson > /tmp/tc.json
python3 -c "import json,collections; print(collections.Counter(d['severity'] for d in json.load(open('/tmp/tc.json'))['generalDiagnostics']))"
```

As of #121 that reports 3831 warnings and 169 errors against the budget's 995, so the budget's number is not this repo's warning count. And a change that alters a diagnostic's shape — wrapping a long call, reordering arguments — stops matching its entry in the second layer, so masked diagnostics resurface as apparent budget growth: check `.basedpyright/baseline.json` before believing such a report. Draining the error floor is #121.
