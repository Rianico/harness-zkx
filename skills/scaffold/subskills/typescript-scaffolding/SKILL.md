---
name: typescript-scaffolding
description: >-
  TypeScript project scaffolding with pnpm v12, .nvmrc, package.json/tsconfig, Vite v8 + oxlint/oxfmt/vitest wiring (TS v7). Use when initializing or retrofitting a TS repo (lib, CLI, or pi-extension) or selecting its toolchain.
metadata:
  managed-by: scaffold
---

# TypeScript Scaffold

Projection of the scaffold spine onto TypeScript. Declared runtime is `pnpm v12` + `.nvmrc`; verification closes the loop via deterministic gates (`oxlint`, `oxfmt --check`, `tsc --noEmit` (TS v7 Go native), `vitest run` + `vite build`).

## Declared Runtime

Per `development-patterns.md` §3:

- Single-runtime TypeScript: `pnpm v12` (Rust native) owns version + deps; commit `.nvmrc` (`24`), `package.json` (`packageManager: pnpm@12.0.0`, `engines >=24`, `typescript >=7`, `vite >=8`, `oxlint` + `oxfmt`), `pnpm-lock.yaml`, `tsconfig.json`, `.oxlintrc.json` + `.oxfmtrc.json`.
- Multi-runtime (TS + Python/Rust): `asdf` + `.tool-versions`; `asdf install` syncs all; `pnpm` still owns Node deps.
- Native toolchain goal: minimize agent feedback latency — `pnpm` (content-addressed + Rust), `tsc v7` (Go + parallel), `Vite v8` (Rolldown + Oxc), `Oxlint` (rules) + `Oxfmt` (format, Prettier fallback).

## Deterministic Artifacts — Tool Owns Bytes

Source of truth is `$SKILL_DIR/scripts/scaffold.py` (`build_package_json`, `build_tsconfig`, `OXLINT_JSON`, `OXLINT_COMMENT_GATE_JS`, `OXFMT_JSON`, `VITEST_CONFIG_TMPL`, `INDEX_TS_TMPL`, `CLI_TS_TMPL`, `INDEX_TEST_TS_TMPL`) — run `uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --dry-run` to preview.

```bash
uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --ts-variant lib --project-name <name>
uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --ts-variant cli --project-name <name>
uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --ts-variant pi-extension --project-name <name>
uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --ts-variant lib --dry-run
```

Variants (`--ts-variant`, default `lib`):

| Variant        | Extra bytes                                                        | Entry                      |
| -------------- | ------------------------------------------------------------------ | -------------------------- |
| `lib`          | `main`/`exports` → `./src/index.ts`                                | `src/index.ts`             |
| `cli`          | `bin: {<name>: ./src/cli.ts}`, `chmod +x` (shebang `pnpm dlx tsx`) | `src/cli.ts` (+`index.ts`) |
| `pi-extension` | `pi.extensions: ["./src/index.ts"]`, no build step                 | `src/index.ts`             |

Every variant ships `src/index.ts` + `tests/index.test.ts` (vitest smoke test, `tests/` layout per `branch-worktree-pr`) so `pnpm test` is green day one — same precedent as `cargo new`.

Pure-deterministic: `.nvmrc` (`24`), `tsconfig.json` (`strict`, ESM `NodeNext`, `ES2022`, `types: ["node"]` — explicit because pnpm's symlinked `@types` defeats auto-inclusion; `include: ["src", "tests"]`), `.oxlintrc.json` (`harness/no-comments` via `jsPlugins: ["./scripts/oxlint-plugin-comment-gate.js"]` + `overrides` for `tests/**`, `**/*.test.ts` per ADR-0014) + `scripts/oxlint-plugin-comment-gate.js` (deterministic allowlist `SAFETY:|WHY:|Invariant:|See ADR-|via https://|TODO(#\\d+):|HACK:|GHERKIN` + `/**` JSDoc) + `.oxfmtrc.json` (ox native, `oxfmt` handles JS/TS/JSX/TSX + Prettier fallback), `src/*.ts` + `tests/*.ts`, `vitest.config.ts` (coverage only), `.gitignore` dedup additions (shared `GITIGNORE_GIT` + `node_modules/` + `dist/`). `biome.json` is deprecated — retained for compat, new projects use `oxlint`/`oxfmt`.

Mixed (script warns → proofread): `package.json` (`{{project_name}}` normalized to lowercase kebab-case, description, `packageManager: pnpm@12.0.0`, deps `typescript>=7` + `vite>=8` + `oxlint`/`oxfmt` + `vitest>=4`), `AGENTS.md` `### Runtime` pointer (keeps existing 3 sections). Script emits `WARNING: ... proofread package name` on stderr.

Byte view: `uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --dry-run` (tool owns bytes).

## Steps — Tool Owns Determinism

1. Generate: `uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --ts-variant <lib|cli|pi-extension> --project-name <name>` (handles `--cwd`, infers name, normalizes, warns on mixed).
2. Install: `pnpm install --no-frozen-lockfile` (corepack reads `packageManager: pnpm@12.0.0`; `--no-frozen-lockfile` because greenfield has no lockfile yet).
3. Proofread mixed warnings: `package.json` name/description, `AGENTS.md` 3-section preservation.
4. Wire verification: `pnpm run lint` (`oxlint .` with `harness/no-comments` allowlist — intercepts mismatched comments and outputs requirements `SAFETY:/WHY:/Invariant:/See ADR-/via https:///TODO(#\\d+):/HACK:/GHERKIN`), `pnpm run format --check` (`oxfmt --check .`), `pnpm run typecheck` (`tsc --noEmit`), `pnpm test` (`vitest run`) via `pnpm`. Loop is `edit → typecheck → lint → format → test/build → fix` with native latency.
5. Verify: `uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --dry-run` + `pnpm install && pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test`

> [!tip] Verification — before every push/PR
>
> - `pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test` — if any fails → `BLOCKED`
> - Reinstall after `package.json` change; `pnpm run coverage` after coverage-config change

## Verification Split

- Deterministic: `oxlint`, `oxfmt`, `tsc --noEmit` (TS v7 Go), `vitest`/`vite` — env truth is `pnpm run ...` exit code (structured file:line:rule output).
- Semantic: API naming, module boundaries — verify via reviewer, not compiler.

## Grilling Selection

If Dialog 2 selected Tests and Dialog 3 selected 80%/90%/Other, add `--with-coverage --coverage-threshold <80|90|custom>` to the generator. Example: `uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --ts-variant lib --with-coverage --coverage-threshold 80 --project-name <name>`. Without Tests or with No coverage, omit the flag — `package.json` omits the `coverage` script + `@vitest/coverage-v8`, no `vitest.config.ts`, and CI runs `pnpm test` without coverage. With the flag, `ci --ci-variant node` swaps the verify step to `pnpm run coverage` (thresholds owned by `vitest.config.ts`).

## Relation to Other Subskills

- Git contract stays canonical: do not duplicate `CONTRIBUTING.md` / `.releaserc.json` here; cross-reference `$SKILL_DIR/subskills/git-scaffolding/SKILL.md`. The TS flavor patches `.releaserc.json` `assets` deterministically (`package-lock.json` → `pnpm-lock.yaml`) because `package.json` declares pnpm — no manual proofread-swap.
- CI wiring belongs to `$SKILL_DIR/subskills/ci-scaffolding/SKILL.md`; the Node verify job runs `pnpm install` + `pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test` on Node 24 inside the shared verify gate (native toolchain keeps per-step cost low).
- Vite/React apps: this flavor now includes `vite>=8` (Rolldown + Oxc) — for full React + Astryx/StyleX wiring, use `pnpm create vite` upstream then overlay `oxlint`/`oxfmt` from this scaffold; `Other` fallback remains.
