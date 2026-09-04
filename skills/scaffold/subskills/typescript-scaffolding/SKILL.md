---
name: typescript-scaffolding
description: >-
  TypeScript project scaffolding with pnpm, .nvmrc, package.json/tsconfig, and biome/vitest wiring. Use when initializing or retrofitting a TS repo (lib, CLI, or pi-extension) or selecting its toolchain. TRIGGER: typescript scaffold, pnpm, package.json, tsconfig, vitest, pi-extension
metadata:
  managed-by: scaffold
---

# TypeScript Scaffold

Projection of the scaffold spine onto TypeScript. Declared runtime is `pnpm` + `.nvmrc`; verification closes the loop via deterministic gates (`biome check`, `tsc --noEmit`, `vitest run`).

## Declared Runtime

Per `development-patterns.md` §3:

- Single-runtime TypeScript: `pnpm` owns version + deps; commit `.nvmrc` (`24`), `package.json` (`packageManager: pnpm@10.0.0`, `engines >=24`), `pnpm-lock.yaml`, `tsconfig.json`, `biome.json`.
- Multi-runtime (TS + Python/Rust): `asdf` + `.tool-versions`; `asdf install` syncs all; `pnpm` still owns Node deps.

## Deterministic Artifacts — Tool Owns Bytes

Source of truth is `$SKILL_DIR/scripts/scaffold.py` (`build_package_json`, `build_tsconfig`, `BIOME_JSON`, `VITEST_CONFIG_TMPL`, `INDEX_TS_TMPL`, `CLI_TS_TMPL`, `INDEX_TEST_TS_TMPL`) — run `uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --dry-run` to preview.

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

Pure-deterministic: `.nvmrc` (`24`), `tsconfig.json` (`strict`, ESM `NodeNext`, `ES2022`, `types: ["node"]` — explicit because pnpm's symlinked `@types` defeats auto-inclusion; `include: ["src", "tests"]`), `biome.json` (`indentStyle: space`, 2-wide — matches emitted bytes so `biome check` self-passes), `src/*.ts` + `tests/*.ts`, `vitest.config.ts` (coverage only), `.gitignore` dedup additions (shared `GITIGNORE_GIT` + `node_modules/` + `dist/`).

Mixed (script warns → proofread): `package.json` (`{{project_name}}` normalized to lowercase kebab-case, description), `AGENTS.md` `### Runtime` pointer (keeps existing 3 sections). Script emits `WARNING: ... proofread package name` on stderr.

Byte view: `uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --dry-run` (tool owns bytes).

## Steps — Tool Owns Determinism

1. Generate: `uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --ts-variant <lib|cli|pi-extension> --project-name <name>` (handles `--cwd`, infers name, normalizes, warns on mixed).
2. Install: `pnpm install --no-frozen-lockfile` (corepack reads `packageManager: pnpm@10.0.0`; `--no-frozen-lockfile` because greenfield has no lockfile yet).
3. Proofread mixed warnings: `package.json` name/description, `AGENTS.md` 3-section preservation.
4. Wire verification: `pnpm run lint` (`biome check .`), `pnpm run typecheck` (`tsc --noEmit`), `pnpm test` (`vitest run`) via `pnpm`.
5. Verify: `uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --dry-run` + `pnpm install && pnpm run lint && pnpm run typecheck && pnpm test`

> [!tip] Verification — before every push/PR
>
> - `pnpm run lint && pnpm run typecheck && pnpm test` — if any fails → `BLOCKED`
> - Reinstall after `package.json` change; `pnpm run coverage` after coverage-config change

## Verification Split

- Deterministic: `biome`, `tsc --noEmit`, `vitest` — env truth is `pnpm run ...` exit code.
- Semantic: API naming, module boundaries — verify via reviewer, not compiler.

## Grilling Selection

If Dialog 2 selected Tests and Dialog 3 selected 80%/90%/Other, add `--with-coverage --coverage-threshold <80|90|custom>` to the generator. Example: `uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --ts-variant lib --with-coverage --coverage-threshold 80 --project-name <name>`. Without Tests or with No coverage, omit the flag — `package.json` omits the `coverage` script + `@vitest/coverage-v8`, no `vitest.config.ts`, and CI runs `pnpm test` without coverage. With the flag, `ci --ci-variant node` swaps the verify step to `pnpm run coverage` (thresholds owned by `vitest.config.ts`).

## Relation to Other Subskills

- Git contract stays canonical: do not duplicate `CONTRIBUTING.md` / `.releaserc.json` here; cross-reference `$SKILL_DIR/subskills/git-scaffolding/SKILL.md`. The TS flavor patches `.releaserc.json` `assets` deterministically (`package-lock.json` → `pnpm-lock.yaml`) because `package.json` declares pnpm — no manual proofread-swap.
- CI wiring belongs to `$SKILL_DIR/subskills/ci-scaffolding/SKILL.md`; the Node verify job runs `corepack enable` + `pnpm install` + `pnpm run lint && pnpm run typecheck && pnpm test` on Node 24 inside the shared verify gate.
- Vite/React apps are out of scope (`Other` → `pnpm create vite` upstream). This flavor embeds minimal `lib`/`cli`/`pi-extension` templates only.
