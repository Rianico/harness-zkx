---
name: oxlint
description: >-
  Domain guide for Oxlint — categories, plugins, config, CLI, writing custom rules and JS plugins, migration from ESLint. Use when configuring lint, enabling rules or plugins, or writing linter rules.
metadata:
  managed-by: toolchain-wiki
---

# Oxlint

Native Rust linter — **50–100× ESLint**, type-aware via tsgo (TS 7), on shared Oxc compiler stack. Scaffold linter is **oxlint ≥1** (see `$SKILL_DIR/../../scaffold/subskills/typescript-scaffolding/SKILL.md`).

Pair with sibling `oxfmt` (`$SKILL_DIR/../oxfmt/SKILL.md`) for formatting.

## Quick Start

```bash
pnpm add -D oxlint        # scaffold pins via scaffold.py:build_package_json
```

`package.json` (via `scaffold.py`):

```json
{ "scripts": { "lint": "oxlint .", "format": "oxfmt --check .", "format:fix": "oxfmt .", "typecheck": "tsc --noEmit", "test": "vitest run" } }
```

Gate: `pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test` — if any fails → `BLOCKED`. Fix: `oxlint --fix .`.

## Config

`.oxlintrc.json` / `.oxlintrc.jsonc` / `oxlint.config.ts` (one per dir, `$schema` → `./node_modules/oxlint/configuration_schema.json`). Scaffold default: `{ "$schema": "./node_modules/oxlint/configuration_schema.json", "rules": {} }`. See `$SKILL_DIR/references/oxlint.md` and `$SKILL_DIR/references/oxc-raw/004-config.md`.

Top keys: `rules`, `categories` (`correctness` default), `plugins` (`--import-plugin`, `--react-plugin`, etc.), `overrides`, `ignorePatterns`, `options` (`typeAware`). See `references/oxc-raw/006-config-file-reference.md` for full schema.

## Writing Linter Rules

Read `$SKILL_DIR/references/oxc-raw/003-linter.md` for intent, then:

- Categories left-to-right: `-D correctness -A no-debugger`, `-A all -D no-debugger` (`-A/--allow`, `-W/--warn`, `-D/--deny`).
- Plugins built-in (no dep tree) — enable via flags or `plugins` in config: `--import-plugin --react-plugin --jest-plugin --vitest-plugin --jsx-a11y-plugin --promise-plugin` etc.; disable with `--disable-unicorn-plugin`. Ruleset 500+; list via `oxlint --rules`.
- JS plugins (**alpha**) for ESLint compat — `jsPlugins` in config; see `$SKILL_DIR/references/oxc-raw/004-config.md` + <https://oxc.rs/docs/guide/usage/linter/js-plugins>.
- **Custom rules:** canonical doc is <https://oxc.rs/docs/contribute/linter/adding-rules> — scrape to `.lsz/tmp/oxc-rules` then curate to `$SKILL_DIR/references/linter-rules.md` if needed. Current snapshot lacks `adding-rules.md` — run `scrape.py site https://oxc.rs/docs/contribute/linter/adding-rules.md --output-dir .lsz/tmp/oxc-rules --force` before writing rules.
- Type-aware: `oxlint --type-aware` / `--type-check` (tsgo, TS 7); `options: { typeAware: true }`.
- Fixes: `--fix` (safe), `--fix-suggestions`, `--fix-dangerously`. Verify via `oxlint --print-config src/file.ts`.

**Template:** `oxlint --init` for starter `.oxlintrc.json`; TypeScript config wraps with `defineConfig` from `oxlint`.

## CLI Cheatsheet

```
oxlint [-c <config>] [PATH]  -A/-W/-D <rule|category>  --fix/--fix-suggestions/--fix-dangerously  --ignore-pattern <PAT>  -f <format>  --type-aware  --print-config --rules
```

Ignore: `.eslintignore` / `.gitignore` + `node_modules`; `ignorePatterns` in config.

See `$SKILL_DIR/references/oxc-raw/005-cli.md` for full flags.

## References

| Module        | File                                        | Source                                                                                                      |
| ------------- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| introduction  | `$SKILL_DIR/references/oxc-introduction.md` | `oxc-raw/001-introduction.md`, `002-what-is-oxc.md`                                                         |
| oxlint        | `$SKILL_DIR/references/oxlint.md`           | `oxc-raw/003-linter.md`, `004-config.md`, `005-cli.md`, `006-config-file-reference.md`, `007-quickstart.md` |
| raw           | `$SKILL_DIR/references/oxc-raw/`            | 7-page linter scrape `2026-09-08` via `scrape.py site` — self-contained                                     |
| writing rules | `$SKILL_DIR/references/linter-rules.md`     | _to scrape_ `https://oxc.rs/docs/contribute/linter/adding-rules.md`                                         |
| formatter     | `$SKILL_DIR/../oxfmt/SKILL.md`              | sibling — Oxfmt (format) lives separately                                                                   |

For freshness, re-scrape via `uv run $SKILL_DIR/../../../docs-scraper/scripts/scrape.py site https://oxc.rs/docs/guide/usage/linter.md https://oxc.rs/docs/guide/usage/linter/config.md https://oxc.rs/docs/guide/usage/linter/cli.md https://oxc.rs/docs/guide/usage/linter/config-file-reference.md https://oxc.rs/docs/guide/usage/linter/quickstart.md --output-dir .lsz/tmp/oxc-raw --force` — see `references/oxc-raw/README.md`.

## When to Use Raw

Read `references/oxc-raw/` when curated lacks flag/option, you need full API surface, or curated conflicts with observation — raw is authoritative.

## Path Convention

- **Prose:** `$SKILL_DIR/references/...` — cwd unknown
- **Links:** `[text](references/oxlint.md)` — relative to SKILL.md
