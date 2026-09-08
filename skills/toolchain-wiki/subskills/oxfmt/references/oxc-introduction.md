# Oxc Introduction — scaffold reference

Source: <https://oxc.rs/docs/guide/introduction.html> and <https://oxc.rs/docs/guide/what-is-oxc>
Raw snapshot: `references/oxc-raw/001-introduction.md`, `002-what-is-oxc.md`
Scraped: 2026-09-08

## What is Oxc

The Oxidation Compiler is a Rust-native collection of high-performance JS/TS tools — parser, transformer, minifier, resolver, **Oxlint** and **Oxfmt**. Powers Rolldown (Vite 8 bundler) and VoidZero's unified toolchain. Philosophy: performance as feature, shared building blocks, correctness with documented boundaries, sensible defaults.

> Source: <https://oxc.rs/docs/guide/what-is-oxc.md>

## Getting Started entry points

- Lint or format a codebase:
  - Lint → [Oxlint](https://oxc.rs/docs/guide/usage/linter.html)
  - Format → [Oxfmt](https://oxc.rs/docs/guide/usage/formatter.html)
- Build tooling on top: Parser, Transformer, Minifier, Resolver, TypeScript Runner (`oxc-node`)
- Learn / contribute / troubleshooting / benchmarks → see introduction.md index

## Scaffold relevance

`typescript-scaffolding` selects Oxc's native toolchain for minimal agent feedback latency:

| Concern           | Tool                            | Scaffold artifact                                                   |
| ----------------- | ------------------------------- | ------------------------------------------------------------------- |
| Lint (rules/bugs) | **oxlint** ≥1                   | `.oxlintrc.json` + `pnpm run lint` → `oxlint .`                     |
| Format (style)    | **oxfmt** ≥0.15                 | `.oxfmtrc.json` + `pnpm run format` → `oxfmt --check .` / `oxfmt .` |
| Type              | `tsc --noEmit` (TS 7 Go native) | `tsconfig.json` (strict, ESM NodeNext)                              |
| Test/Bundler      | `vitest` ≥4 + `vite` ≥8         | `vitest.config.ts`                                                  |

Declared runtime is `pnpm v12` + `.nvmrc` (24) + `package.json` (`packageManager: pnpm@12.0.0`, `engines >=24`, `typescript >=7`, `tsx >=4`, `@types/node >=24` + `@semantic-release/*` — see `scaffold.py:build_package_json`). See `SKILL.md` → Deterministic Artifacts.

Variants: `lib` (main/exports) · `cli` (bin + `pnpm dlx tsx` shebang) · `pi-extension` (pi.extensions). Coverage optional: `--with-coverage --coverage-threshold 80` adds `coverage` script + `vitest.config.ts`; CI then runs `pnpm run coverage`.

## Choosing Oxc tools

- Choose **Oxlint** when you want a dedicated JS/TS linter with strong ESLint migration, 50–100× faster than ESLint (bench-linter), type-aware via tsgo (TS 7).
- Choose **Oxfmt** when you want Prettier-compatible formatting, ~30× faster than Prettier, 2× Biome, with built-in import/Tailwind/package.json sorting and embedded formatting.
- Choose **Vite+** if you want integrated toolchain; stay on ESLint/Prettier only for unsupported edge-case plugin behavior.

Sources: <https://oxc.rs/docs/guide/usage/linter.md>, <https://oxc.rs/docs/guide/usage/formatter.md>

## Quick scaffold wire

```bash
uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --ts-variant lib --project-name my-lib --dry-run  # preview
uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --ts-variant lib --project-name my-lib           # write
pnpm install --no-frozen-lockfile
pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test
```

Verify gate before push/PR (tip from `typescript-scaffolding/SKILL.md`):

```
pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test
# any failure → BLOCKED
```
