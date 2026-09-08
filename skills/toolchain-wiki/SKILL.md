---
description: 'Native toolchain wiki router for JS/TS/Python — Oxlint/Oxfmt (oxc),
  Basedpyright, Worktrunk. Use when configuring linters/formatters, writing linter
  rules/plugins, type-checking Python, or managing parallel worktrees. TRIGGER: toolchain-wiki,
  oxc, oxlint, oxfmt, basedpyright, worktrunk, wt'
metadata:
  manage:
    - oxlint
    - oxfmt
    - typecheck
    - worktrunk
name: toolchain-wiki
---

# Toolchain Wiki

Orchestration router for the native toolchain-wiki that minimizes agent feedback latency. Single-runtime `pnpm v12` + `TS 7` (Go) + `Vite 8` (Rolldown + Oxc) + `Basedpyright` (strict) + `Worktrunk` (branch-addressed worktrees) share one spine: **declared runtime → deterministic artifacts → verification gate**.

This skill owns **sequencing only** — no bytes. Each projection owns its bytes via `$SKILL_DIR/scripts/` or canonical skill.

## Dispatch

Read the subskill that matches the task. Use `Read` (not `Skill` tool — subskills hidden from discovery).

| Domain | Subskill | When to load |
| `oxlint` | `$SKILL_DIR/subskills/oxlint/SKILL.md` | Oxlint config, CLI, categories/plugins, writing custom rules & JS plugins, ESLint migration — [oxlint](subskills/oxlint/SKILL.md) |
| `oxfmt` | `$SKILL_DIR/subskills/oxfmt/SKILL.md` | Oxfmt config, CLI, embedded formatting, Prettier/Biome compat — [oxfmt](subskills/oxfmt/SKILL.md) |
| `typecheck` | `$SKILL_DIR/subskills/typecheck/SKILL.md` | Basedpyright setup, strict mode, diagnostics, stubs — proxy to `programming-expert/subskills/basedpyright-expert` |
| `worktrunk` | `$SKILL_DIR/subskills/worktrunk/SKILL.md` | Branch-addressed worktrees, hooks, `hash_port`, LLM commits — [worktrunk](subskills/worktrunk/SKILL.md) |

Omitted domain loads only the spine above.

## Spine

- **Runtime:** `pnpm v12` (`pnpm@12.0.0`, `.nvmrc 24`) for JS/TS, `uv` (`.python-version 3.14`) for Python, `wt` (branch-addressed) for worktrees. See `$SKILL_DIR/subskills/oxlint/SKILL.md` + `$SKILL_DIR/subskills/oxfmt/SKILL.md`, `programming-expert/subskills/basedpyright-expert/SKILL.md`, and `worktrunk` for owners.
- **Verify gate:** `pnpm run lint` (`oxlint .`) + `pnpm run format --check` (`oxfmt --check .`) + `tsc --noEmit` (TS 7) + `basedpyright` (`reportAny` etc.) + `wt merge` pre-merge. Env truth is `pnpm run ...` / `basedpyright` / `wt list` exit code.
- **Performance goal:** native Rust/Go tooling — `oxlint` 50–100× ESLint, `oxfmt` 30× Prettier, `tsc v7` parallel, `basedpyright` tsgo, `wt hash_port` deterministic.

## Deterministic Gates

Tool owns bytes; model proofreads intent.

- `uv run $SKILL_DIR/../scaffold/scripts/scaffold.py --flavor typescript --dry-run` — preview TS artifacts (canonical: `scaffold`)
- `pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test` — JS/TS gate (see `oxlint` + `oxfmt`)
- `basedpyright --writebaseline && basedpyright --baselinemode=lock` — Python gate (see `typecheck`)
- `wt switch --create <branch> && wt merge` — worktree gate (see `worktrunk`)

## Trade-offs

- Router lean, subskills deep — on-demand `Read` keeps `TOOLCHAIN-WIKI` prompt cheap.
- One concept one location — oxlint/oxfmt docs live in `toolchain-wiki/subskills/oxlint/references/` and `toolchain-wiki/subskills/oxfmt/references/`, not duplicated in `typescript-scaffolding`.
- Native bias — `oxlint`/`oxfmt`/`basedpyright`/`wt` over JS emulation; agent latency > compatibility edge cases.

## Relation

- `scaffold` (`typescript-scaffolding`) `depends-on: [toolchain-wiki]` — TS flavor reuses `toolchain-wiki/subskills/oxlint/` (linter) + `toolchain-wiki/subskills/oxfmt/` (formatter).
- `programming-expert` remains canonical for `basedpyright-expert`; `toolchain-wiki/subskills/typecheck/` is a proxy/index.
- `worktrunk` is canonical via `toolchain-wiki/subskills/worktrunk/` — native worktree + `hash_port` + hooks; no proxy.
