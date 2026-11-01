---
name: toolchain-wiki
description: >-
  Toolchain wiki router for Oxlint/Oxfmt, Basedpyright, Worktrunk (wt), Jinja, and LSP 3.17. Use when fixing lint errors, configuring typecheckers, managing git worktrees with wt, or troubleshooting LSP servers.
metadata:
  manage:
    - oxlint
    - oxfmt
    - basedpyright-expert
    - worktrunk
    - jinja
    - lsp
  depends-on: [docs-scraper, scaffold]
---

# Toolchain Wiki

Orchestration router for the native toolchain-wiki that minimizes agent feedback latency. A single-runtime stack (`pnpm v12`, `TS 7`, `Vite 8`, `Basedpyright`, `Worktrunk`, `Jinja 3.1`) shares one spine. The spine is: **declared runtime → deterministic artifacts → verification gate**.

This skill owns **sequencing only** — no bytes. Each subskill owns its bytes inside `$SKILL_DIR/subskills/<name>/`.

## Dispatch

Read the subskill that matches the task. Use `Read` (not `Skill` tool — subskills hidden from discovery).

| Domain | Subskill | When to load |
| `oxlint` | `$SKILL_DIR/subskills/oxlint/SKILL.md` | Oxlint config, CLI, categories/plugins, writing custom rules & JS plugins, ESLint migration — [oxlint](subskills/oxlint/SKILL.md) |
| `oxfmt` | `$SKILL_DIR/subskills/oxfmt/SKILL.md` | Oxfmt config, CLI, embedded formatting, Prettier/Biome compat — [oxfmt](subskills/oxfmt/SKILL.md) |
| `basedpyright-expert` | `$SKILL_DIR/subskills/basedpyright-expert/SKILL.md` | Basedpyright setup, strict mode, diagnostics, stubs, baseline — [basedpyright-expert](subskills/basedpyright-expert/SKILL.md) |
| `worktrunk` | `$SKILL_DIR/subskills/worktrunk/SKILL.md` | Branch-addressed worktrees, hooks, `hash_port`, LLM commits — [worktrunk](subskills/worktrunk/SKILL.md) |
| `jinja` | `$SKILL_DIR/subskills/jinja/SKILL.md` | Jinja 3.1 templates, `Environment`/loader config, filters/tests, autoescaping, extensions, sandbox — [jinja](subskills/jinja/SKILL.md) |
| `lsp` | `$SKILL_DIR/subskills/lsp/SKILL.md` | LSP 3.17 server/client lifecycle, diagnostics pull/push, progress streaming, daemon process handling — [lsp](subskills/lsp/SKILL.md) |

Omitted domain loads only the spine above.

## Spine

- **Runtime:** `pnpm v12` (`pnpm@12.4.1`, `.nvmrc 26`) for JS/TS, `uv` (`.python-version 3.14`) for Python, `wt` (branch-addressed) for worktrees. Owners: `$SKILL_DIR/subskills/oxlint/SKILL.md`, `$SKILL_DIR/subskills/oxfmt/SKILL.md`, `$SKILL_DIR/subskills/basedpyright-expert/SKILL.md`, and `worktrunk`.
- **Verify gate:** `pnpm run lint` (`oxlint .`) + `pnpm run format --check` (`oxfmt --check .`) + `tsc --noEmit` (TS 7) + `basedpyright` (`reportAny` etc.) + `wt merge` pre-merge. Env truth is `pnpm run ...` / `basedpyright` / `wt list` exit code.
- **Templating:** `jinja2` ≥3.1 (Python) — one `Environment` per app, `select_autoescape()` for markup, loader-backed templates, sandbox for untrusted input. Gate: `Environment().parse(src)` + a render smoke test. See `$SKILL_DIR/subskills/jinja/SKILL.md`.
- **LSP lifecycle:** sequence `initialize` → `initialized` → `shutdown` → `exit` → transport stop. Shutdown precedes exit, and both precede transport teardown. Keep daemons isolated per workspace, and stream progress with `$/progress` begin/report/end. See `$SKILL_DIR/subskills/lsp/SKILL.md`.
- **Performance goal:** native Rust/Go tooling — `oxlint` 50–100× ESLint, `oxfmt` 30× Prettier, `tsc v7` parallel, `basedpyright` tsgo, `wt hash_port` deterministic.

## Deterministic Gates

Tool owns bytes. Model proofreads intent.

- `scaffold` skill → `scripts/scaffold.py --flavor typescript --dry-run` — preview TS artifacts
- `pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test` — JS/TS gate (see `oxlint` + `oxfmt`)
- `basedpyright --writebaseline && basedpyright --baselinemode=lock` — Python gate (see `basedpyright-expert`)
- `wt switch --create <branch> && wt merge` — worktree gate (see `worktrunk`)
- LSP gate — assert shutdown before exit, no orphaned server process after teardown, and a closed `$/progress` stream (see `lsp`)

## Trade-offs

- Router lean, subskills deep — on-demand `Read` keeps `TOOLCHAIN-WIKI` prompt cheap.
- One concept one location — oxlint/oxfmt docs live in `toolchain-wiki/subskills/oxlint/references/` and `toolchain-wiki/subskills/oxfmt/references/`, not duplicated in `typescript-scaffolding`.
- Native bias — `oxlint`/`oxfmt`/`basedpyright`/`wt` over JS emulation. Agent latency beats compatibility edge cases.

## Relation

- `scaffold` (`typescript-scaffolding`) `depends-on: [toolchain-wiki]` — TS flavor reuses `toolchain-wiki/subskills/oxlint/` (linter) + `toolchain-wiki/subskills/oxfmt/` (formatter).
- `basedpyright-expert` is canonical via `toolchain-wiki/subskills/basedpyright-expert/` — Python typing, checker config, diagnostics, and stubs. `programming-expert` and `python-expert` delegate here.
- `worktrunk` is canonical via `toolchain-wiki/subskills/worktrunk/` — native worktree + `hash_port` + hooks. No proxy.
- `jinja` is canonical via `toolchain-wiki/subskills/jinja/` — Jinja 3.1 language + API, raw snapshot in `references/jinja-raw/`.
- `lsp` is canonical via `toolchain-wiki/subskills/lsp/` — LSP 3.17 protocol patterns, daemon lifecycle, diagnostics pull/push, and spec excerpts in `references/`.
