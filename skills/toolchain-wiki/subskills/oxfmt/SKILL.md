---
name: oxfmt
description: >-
  Domain guide for Oxfmt — config, CLI, embedded formatting, Prettier/Biome compat, language support. Use when configuring or migrating formatters, sorting imports, or handling formatter ignore. TRIGGER: oxfmt, formatter, prettier, oxc formatter
metadata:
  managed-by: toolchain-wiki
---

# Oxfmt

Native Rust formatter — **30× Prettier, 100% conformance** on shared Oxc compiler stack. Scaffold formatter is **oxfmt ≥0.15** (see `$SKILL_DIR/../../scaffold/subskills/typescript-scaffolding/SKILL.md`).

Pair with sibling `oxlint` (`$SKILL_DIR/../oxlint/SKILL.md`) for linting.

## Quick Start

```bash
pnpm add -D oxfmt        # scaffold pins via scaffold.py:build_package_json
```

`package.json` (via `scaffold.py`):

```json
{ "scripts": { "lint": "oxlint .", "format": "oxfmt --check .", "format:fix": "oxfmt .", "typecheck": "tsc --noEmit", "test": "vitest run" } }
```

Gate: `pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test` — if any fails → `BLOCKED`. Fix: `oxfmt .`.

## Config

`.oxfmtrc.json` / `.oxfmtrc.jsonc` / `oxfmt.config.ts` (nearest wins for per-package overrides, `$schema` → `./node_modules/oxfmt/configuration_schema.json`). Scaffold default: `{ "$schema": "./node_modules/oxfmt/configuration_schema.json" }`. See `$SKILL_DIR/references/oxfmt.md` and `$SKILL_DIR/references/oxc-raw/009-config.md`.

Top keys: `printWidth` (100), `tabWidth` (2), `semi`, `singleQuote`, `sortPackageJson` enabled, `sortImports`, `sortTailwindcss`, `ignorePatterns`, `embedded`. See `references/oxc-raw/011-config-file-reference.md` / `012-generated-config.md`.

## Formatter

Batteries included — `sortImports`, `sortTailwindcss`, `sortPackageJson` (enabled), embedded (CSS-in-JS/GraphQL). Init via `oxfmt --init`, migrate `oxfmt --migrate prettier|biome`. CLI: `--check` (gate), `--write` (default), `--list-different`, `-c <path>`, `--disable-nested-config`. See `$SKILL_DIR/references/oxfmt.md`.

Prettier compat: CLI follows Prettier conventions, 100% JS/TS conformance — differences are bugs vs <https://github.com/oxc-project/oxc/issues/18717>.

## CLI Cheatsheet

```
oxfmt  [-c <path>] [PATH]  --check|--write|--list-different  --migrate prettier|biome  --lsp  --stdin-filepath <PATH>
```

Ignore: `.gitignore` + `.prettierignore` + `node_modules`; `ignorePatterns` in config.

See `$SKILL_DIR/references/oxc-raw/010-cli.md` for full flags.

## References

| Module       | File                                        | Source                                                                                                               |
| ------------ | ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| introduction | `$SKILL_DIR/references/oxc-introduction.md` | `oxc-raw/001-introduction.md`, `002-what-is-oxc.md`                                                                  |
| oxfmt        | `$SKILL_DIR/references/oxfmt.md`            | `oxc-raw/008-formatter.md`, `009-config.md`, `010-cli.md`, `011-config-file-reference.md`, `012-generated-config.md` |
| raw          | `$SKILL_DIR/references/oxc-raw/`            | 7-page formatter scrape `2026-09-08` via `scrape.py site` — self-contained                                           |
| linter       | `$SKILL_DIR/../oxlint/SKILL.md`             | sibling — Oxlint (lint) lives separately                                                                             |

For freshness, re-scrape via `uv run $SKILL_DIR/../../../docs-scraper/scripts/scrape.py site https://oxc.rs/docs/guide/usage/formatter.md https://oxc.rs/docs/guide/usage/formatter/config.md https://oxc.rs/docs/guide/usage/formatter/cli.md https://oxc.rs/docs/guide/usage/formatter/config-file-reference.md https://oxc.rs/docs/guide/usage/formatter/generated-config.md --output-dir .lsz/tmp/oxc-raw --force` — see `references/oxc-raw/README.md`.

## When to Use Raw

Read `references/oxc-raw/` when curated lacks flag/option, you need full API surface, or curated conflicts with observation — raw is authoritative.

## Path Convention

- **Prose:** `$SKILL_DIR/references/...` — cwd unknown
- **Links:** `[text](references/oxfmt.md)` — relative to SKILL.md
