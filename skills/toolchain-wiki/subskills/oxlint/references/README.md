# Oxlint — toolchain-wiki references

Curated LLM-friendly reference for `toolchain-wiki/subskills/oxlint` — Oxlint native linter (pnpm v12 + TS 7 Go, 50–100× ESLint).

Pair with sibling `oxfmt` (`../oxfmt/references/`) for formatting.

## Quick index

| File                  | Covers                                                                                     | Source                                        |
| --------------------- | ------------------------------------------------------------------------------------------ | --------------------------------------------- |
| `oxc-introduction.md` | What is Oxc, getting-started entry points, scaffold mapping, verify gate                   | <https://oxc.rs/docs/guide/introduction.html> |
| `oxlint.md`           | Install, scripts, config discovery, categories/plugins, CLI for verify gate, writing rules | <https://oxc.rs/docs/guide/usage/linter/>     |
| `oxc-raw/`            | Raw 7-page linter scrape snapshot (introduction + linter)                                  | `scrape.py site` 2026-09-08                   |

## Deterministic artifacts (tool owns bytes)

Preview:

```bash
uv run $SKILL_DIR/../../scaffold/scripts/scaffold.py --flavor typescript --ts-variant lib --project-name my-lib --dry-run
```

Generates (per `scaffold.py` → `OXLINT_JSON`, `build_package_json`):

- `.nvmrc` → `24`
- `package.json` → `packageManager: pnpm@12.0.0`, `engines node >=24`, `typescript >=7`, `oxlint >=1`, `tsx >=4`, `@types/node >=24` (+ `@semantic-release/*` — see `scaffold.py:build_package_json`), scripts `lint: oxlint .`, `typecheck: tsc --noEmit`, `test: vitest run`
- `.oxlintrc.json` → `{ "$schema": "./node_modules/oxlint/configuration_schema.json", "rules": {} }`
- `tsconfig.json` → strict, ESM NodeNext, ES2022, `types: ["node"]`

Canonical for `scaffold/subskills/typescript-scaffolding` linter side — see `typescript-scaffolding` `depends-on: [toolchain-wiki]`. Single source; scaffold wrapper is pointer-only. Pair with `../oxfmt` for formatter.

Raw snapshot files are self-contained; curated file is the 80% surface. For byte truth, read `scaffold.py`.

## Verify gate (before push/PR)

```bash
pnpm install --no-frozen-lockfile
pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test
# --check gate: oxlint .  (fix locally: oxlint --fix .)
```

CI verify job (`ci-scaffolding`, Node 24) runs the same steps on pnpm (`pnpm run coverage` when `--with-coverage` enabled).

## Refreshing the snapshot

Regenerate raw (linter only):

```bash
uv run $SKILL_DIR/../../../docs-scraper/scripts/scrape.py site \
  https://oxc.rs/docs/guide/introduction.md \
  https://oxc.rs/docs/guide/what-is-oxc.md \
  https://oxc.rs/docs/guide/usage/linter.md \
  https://oxc.rs/docs/guide/usage/linter/config.md \
  https://oxc.rs/docs/guide/usage/linter/cli.md \
  https://oxc.rs/docs/guide/usage/linter/config-file-reference.md \
  https://oxc.rs/docs/guide/usage/linter/quickstart.md \
  --output-dir .lsz/tmp/oxlint-raw --force
cp .lsz/tmp/oxlint-raw/*.md $SKILL_DIR/references/oxc-raw/
```

Then update curated file `oxlint.md` for scaffold-facing delta; keep raw as self-contained layer per `docs-scraper` layered-skill contract (curated + raw).

## Upstream docs

- Oxc intro: <https://oxc.rs/docs/guide/introduction.html>
- Oxlint: <https://oxc.rs/docs/guide/usage/linter.html>
- llms.txt: <https://oxc.rs/llms.txt>
