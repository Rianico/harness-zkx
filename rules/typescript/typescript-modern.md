---
paths:
  - 'package.json'
  - 'tsconfig.json'
  - 'pnpm-workspace.yaml'
  - '**/*.ts'
  - '**/*.tsx'
  - '**/*.mts'
  - '**/*.cts'
---

# Modern TypeScript Tooling & Syntax

Modern TypeScript 5.x/6.x environment setup and language features.

## Tooling (CRITICAL)

- **Package manager:** `pnpm` (preferred; fast, disk-efficient). Fallback `npm`. Avoid `yarn` classic.
- **Runtime version:** Use Node.js Active LTS via `corepack`/`nvm` + committed `.nvmrc`.
- **Runner:** `tsx` to execute TS/ESM scripts (replaces `ts-node` — faster, ESM-native, no config).
- **Type check:** `tsc --noEmit` (or `tsc -b` for project references) in CI — build tools (Vite/esbuild/Turbopack) strip types WITHOUT checking them. Run a dedicated typecheck step.
- **Lint/format:** Biome (default: fast, ~90 rules, formatter+linter+import-sort in one) or ESLint (depth/plugins/type-aware). Keep one; don't stack both.
- **Testing:** Vitest (default for Vite projects) or Jest (legacy/big ecosystems). Use `node:test` for small scripts.
- **Node types:** Install `@types/node` as a dev dependency.
- **`package.json` fields present:** `"type": "module"` (ESM-first), `"engines"`, `"private": true` unless published.
- **LSP freshness:** If diagnostics contradict edited files, restart/reload the language server before judging results.
- **Scripts:** Put `typecheck`, `test`, `lint`, `build` in `package.json` scripts; run via `pnpm run`.

## Project Configuration

- Default to `tsconfig.json` for compiler options, `pnpm-workspace.yaml` for monorepos, `biome.json`/`eslint.config.js` for lint.
- **Strict base** `tsconfig.json`:

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "target": "ES2022",
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "verbatimModuleSyntax": true
  }
}
```

- **Performance:** `incremental`, precise `include`/`exclude`, project references (`composite: true`) in monorepos. Diagnose slow compiles with `tsc --extendedDiagnostics`.
- **Migration (JS→TS):** `allowJs`/`checkJs`, `ts-migrate`/`typesync`, ESM-first `"type":"module"`.

## Language Features (TypeScript 5.x/6.x)

- **`satisfies` operator:** verify a value against a type without widening (`const c = {...} satisfies Config`). Prefer over `as`.
- **`const` type parameters / `const` type arguments:** `<const T>(xs: T[])` preserves literal types.
- **`import type { }`** for type-only imports; `verbatimModuleSyntax` enforces it.
- **`as const`** for literal/readonly tuples and object literals — prefer over explicit literal annotations.
- **Built-in generics syntax:** `<T>` (no constraint requirement); `T extends U` constraints; `infer` in conditional types.
- **Discriminated unions** with literal `type` tags for exhaustive, null-safe state models.
- **Utility types:** `Pick`, `Omit`, `Partial`, `Required`, `Readonly`, `Record`, `Exclude`, `Extract`, `ReturnType`, `Awaited`, `NoInfer`.
- **`satisfies` + `as const`** for typed constant maps/records — the modern replacement for `enum` in most cases.
- **Exact optional properties:** with `exactOptionalPropertyTypes`, an optional field is `T | undefined` — don't assign `undefined` to it; omit the key instead.
- **`Array.prototype.find`/`at` typed:** `find` returns `T | undefined`; `at()` allows negative indices (runtime). Narrow results before use.
- **`globalThis`** over `window`/`process` for portable cache/shared state.

## Node Runtime (ESM)

- Set `"type": "module"`; use `.mts`/`.cts` extensions to opt files in/out of ESM explicitly.
- Relative imports in ESM require file extensions: `import { x } from "./mod.js"` (even for `.ts` source — TS rewrites, the target is `.js`).
- Avoid CJS/ESM interop footguns: `import { createRequire }` only when you must load CJS; prefer `node:`-prefixed built-ins (`node:fs/promises`, `node:path`).

## Inline Scripts

For standalone scripts, use `tsx` with a typed header:

```ts
#!/usr/bin/env tsx
import { parseArgs } from 'node:util';
```

Run with `tsx script.ts` — no build step, ESM and TS types work out of the box.
