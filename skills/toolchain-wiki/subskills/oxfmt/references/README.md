# Oxfmt — toolchain-wiki references

Curated LLM-friendly reference for `toolchain-wiki/subskills/oxfmt` — Oxfmt native formatter (pnpm v12 + TS 7 Go, 30× Prettier).

Pair with sibling `oxlint` (`../oxlint/references/`) for linting.

## Quick index

| File                  | Covers                                                                          | Source                                        |
| --------------------- | ------------------------------------------------------------------------------- | --------------------------------------------- |
| `oxc-introduction.md` | What is Oxc, getting-started entry points, scaffold mapping, verify gate        | <https://oxc.rs/docs/guide/introduction.html> |
| `oxfmt.md`            | Install, scripts, config discovery, printWidth etc., CLI, ignore                | <https://oxc.rs/docs/guide/usage/formatter/>  |
| `oxc-raw/`            | Raw 7-page formatter scrape snapshot (introduction + formatter + coding-agents) | `scrape.py site` 2026-09-08                   |

## Deterministic artifacts (tool owns bytes)

Preview:

```bash
uv run $SKILL_DIR/../../scaffold/scripts/scaffold.py --flavor typescript --ts-variant lib --project-name my-lib --dry-run
```

Generates (per `scaffold.py` → `OXFMT_JSON`, `build_package_json`):

- `.nvmrc` → `24`
- `package.json` → `packageManager: pnpm@12.0.0`, `engines node >=24`, `typescript >=7`, `oxfmt >=0.15`, `tsx >=4`, `@types/node >=24` (+ `@semantic-release/*` — see `scaffold.py:build_package_json`), scripts `format: oxfmt --check .`, `format:fix: oxfmt .`, `typecheck: tsc --noEmit`, `test: vitest run`
- `.oxfmtrc.json` → `{ "$schema": "./node_modules/oxfmt/configuration_schema.json" }`
- `tsconfig.json` → strict, ESM NodeNext, ES2022, `types: ["node"]`

Canonical for `scaffold/subskills/typescript-scaffolding` formatter side — see `typescript-scaffolding` `depends-on: [toolchain-wiki]`. Single source; scaffold wrapper is pointer-only. Pair with `../oxlint` for linter.

Raw snapshot files are self-contained; curated file is the 80% surface. For byte truth, read `scaffold.py`.

## Verify gate (before push/PR)

```bash
pnpm install --no-frozen-lockfile
pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test
# --check gate: oxfmt --check .  (fix locally: oxfmt .)
```

CI verify job (`ci-scaffolding`, Node 24) runs the same steps on pnpm (`pnpm run coverage` when `--with-coverage` enabled).

## Refreshing the snapshot

Regenerate raw (formatter only):

```bash
uv run $SKILL_DIR/../../../docs-scraper/scripts/scrape.py site \
  https://oxc.rs/docs/guide/introduction.md \
  https://oxc.rs/docs/guide/what-is-oxc.md \
  https://oxc.rs/docs/guide/usage/formatter.md \
  https://oxc.rs/docs/guide/usage/formatter/config.md \
  https://oxc.rs/docs/guide/usage/formatter/cli.md \
  https://oxc.rs/docs/guide/usage/formatter/config-file-reference.md \
  https://oxc.rs/docs/guide/usage/formatter/generated-config.md \
  https://oxc.rs/docs/guide/usage/formatter/embedded-formatting.md \
  --output-dir .lsz/tmp/oxfmt-raw --force
cp .lsz/tmp/oxfmt-raw/*.md $SKILL_DIR/references/oxc-raw/
```

Then update curated file `oxfmt.md` for scaffold-facing delta; keep raw as self-contained layer per `docs-scraper` layered-skill contract (curated + raw).

## Upstream docs

- Oxc intro: <https://oxc.rs/docs/guide/introduction.html>
- Oxfmt: <https://oxc.rs/docs/guide/usage/formatter.html>
- llms.txt: <https://oxc.rs/llms.txt>
