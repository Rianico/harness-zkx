# Oxc — toolchain-wiki references

Curated LLM-friendly reference for `toolchain-wiki/subskills/oxc` — Oxlint + Oxfmt native toolchain-wiki (pnpm v12 + TS 7 Go + Vite 8 Rolldown).

## Quick index

| File                  | Covers                                                                                     | Source                                        |
| --------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------- |
| `oxc-introduction.md` | What is Oxc, getting-started entry points, scaffold mapping, verify gate                   | <https://oxc.rs/docs/guide/introduction.html> |
| `oxlint.md`           | Install, scripts, config discovery, categories/plugins, CLI for verify gate, writing rules | <https://oxc.rs/docs/guide/usage/linter/>     |
| `oxfmt.md`            | Install, scripts, config discovery, printWidth etc., CLI, ignore                           | <https://oxc.rs/docs/guide/usage/formatter/>  |
| `oxc-raw/`            | Raw 14-page scrape snapshot (introduction, linter/_, formatter/_, coding-agents)           | `scrape.py site` 2026-09-08                   |

## Deterministic artifacts (tool owns bytes)

Preview:

```bash
uv run $SKILL_DIR/../../scaffold/scripts/scaffold.py --flavor typescript --ts-variant lib --project-name my-lib --dry-run
```

Generates (per `scaffold.py` → `OXLINT_JSON`, `OXFMT_JSON`, `build_package_json`):

- `.nvmrc` → `24`
- `package.json` → `packageManager: pnpm@12.0.0`, `engines node >=24`, `typescript >=7`, `vite >=8`, `oxlint >=1`, `oxfmt >=0.15`, `tsx >=4`, `@types/node >=24` (+ `@semantic-release/*` — see `scaffold.py:build_package_json`), scripts `lint: oxlint .`, `format: oxfmt --check .`, `format:fix: oxfmt .`, `typecheck: tsc --noEmit`, `test: vitest run`
- `.oxlintrc.json` → `{ "$schema": "./node_modules/oxlint/configuration_schema.json", "rules": {} }`
- `.oxfmtrc.json` → `{ "$schema": "./node_modules/oxfmt/configuration_schema.json" }`
- `tsconfig.json` → strict, ESM NodeNext, ES2022, `types: ["node"]`

Canonical for `scaffold/subskills/typescript-scaffolding` — see `typescript-scaffolding` `depends-on: [toolchain-wiki]`. Wrapper copies remain in `scaffold/subskills/typescript-scaffolding/references/` for compat.

Raw snapshot files are self-contained; curated files are the 80% surface. For byte truth, read `scaffold.py`.

## Verify gate (before push/PR)

```bash
pnpm install --no-frozen-lockfile
pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test
# --check gate: oxlint .  +  oxfmt --check .
# fix locally: oxlint --fix .  /  oxfmt .
```

CI verify job (`ci-scaffolding`, Node 24) runs the same 4 steps on pnpm (`pnpm run coverage` when `--with-coverage` enabled).

## Refreshing the snapshot

Regenerate raw:

```bash
uv run $SKILL_DIR/../../../docs-scraper/scripts/scrape.py site \
  https://oxc.rs/docs/guide/introduction.md \
  https://oxc.rs/docs/guide/what-is-oxc.md \
  https://oxc.rs/docs/guide/usage/linter.md \
  https://oxc.rs/docs/guide/usage/linter/config.md \
  https://oxc.rs/docs/guide/usage/linter/cli.md \
  https://oxc.rs/docs/guide/usage/linter/config-file-reference.md \
  https://oxc.rs/docs/guide/usage/formatter.md \
  https://oxc.rs/docs/guide/usage/formatter/config.md \
  https://oxc.rs/docs/guide/usage/formatter/cli.md \
  https://oxc.rs/docs/guide/usage/formatter/config-file-reference.md \
  https://oxc.rs/docs/guide/usage/formatter/generated-config.md \
  --output-dir .lsz/tmp/oxc-raw --force
cp .lsz/tmp/oxc-raw/*.md $SKILL_DIR/references/oxc-raw/
# also sync wrapper for compat:
cp $SKILL_DIR/references/oxc-raw/*.md ../../scaffold/subskills/typescript-scaffolding/references/oxc-raw/
```

Then update curated files `oxlint.md` / `oxfmt.md` for scaffold-facing delta; keep raw as self-contained layer per `docs-scraper` layered-skill contract (curated + raw).

## Upstream docs

- Oxc intro: <https://oxc.rs/docs/guide/introduction.html>
- Oxlint: <https://oxc.rs/docs/guide/usage/linter.html>
- Oxfmt: <https://oxc.rs/docs/guide/usage/formatter.html>
- llms.txt: <https://oxc.rs/llms.txt>
