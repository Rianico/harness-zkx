# TypeScript Scaffold — Oxc references (pointer)

Canonical Oxc docs live at `toolchain-wiki/subskills/oxlint/references/` (linter) and `toolchain-wiki/subskills/oxfmt/references/` (formatter) — single source per concern, no duplication.

## Canonical index

| File                  | Location                                                                               |
| --------------------- | -------------------------------------------------------------------------------------- |
| `oxc-introduction.md` | `toolchain-wiki/subskills/oxlint/references/oxc-introduction.md` (and `oxfmt` copy) |
| `oxlint.md`           | `toolchain-wiki/subskills/oxlint/references/oxlint.md`               |
| `oxlint raw` (7 pp.)  | `toolchain-wiki/subskills/oxlint/references/oxc-raw/`                |
| `oxfmt.md`            | `toolchain-wiki/subskills/oxfmt/references/oxfmt.md`                 |
| `oxfmt raw` (9 pp.)   | `toolchain-wiki/subskills/oxfmt/references/oxc-raw/`                 |

## Why pointer

`scaffold/subskills/typescript-scaffolding` is `managed-by: scaffold` / `depends-on: [toolchain-wiki]`. Toolchain owns bytes at `toolchain-wiki/subskills/oxlint/` (lint) and `toolchain-wiki/subskills/oxfmt/` (format); scaffold is a projection, not an owner. Wrapper copies were removed (previously duplicated 18 files) — read canonical via `toolchain-wiki/subskills/oxlint/references/` and `toolchain-wiki/subskills/oxfmt/references/` (80% curated + 20% raw per `docs-scraper`).

## Refresh

Canonical refresh is owned by `toolchain-wiki/subskills/oxlint` (linter) and `toolchain-wiki/subskills/oxfmt` (formatter) — see `toolchain-wiki/subskills/oxlint/references/README.md` and `toolchain-wiki/subskills/oxfmt/references/README.md` for `scrape.py site` recipes. Do not regenerate here.
