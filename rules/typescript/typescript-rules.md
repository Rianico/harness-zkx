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

# TypeScript Rules

Baseline behavior, style preferences, and lib selection for everyday TypeScript development.

## Core Standards

- **Formatting:** `camelCase` for variables/functions, `PascalCase` for types/classes/components.
- **Typing:** No implicit `any`; annotate public function/method signatures; let inference fill the body.
- **Nullability:** `null` and `undefined` are distinct. Prefer `undefined` for "missing"; use `null` only for explicit "no value" sentinels (esp. DOM/API interop). Enable `strictNullChecks`.
- **Imports:** `import type { }` for type-only imports (never inline `import { type X }`). Standard lib → third party → local, sorted.
- **Immutability:** Use `readonly`/`ReadonlyArray`/`as const` instead of mutating. Avoid `Array.push`/mutators on shared state.
- **Exports:** Prefer named exports over `default` (except framework-required).
- **Entry point:** Enable `strict` (`strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, …) in every `tsconfig.json`.

## Type Safety (First Principle)

- **Fix over suppress:** Address real issues; suppress only when the pattern is intentional; never blanket-disable rules.
- **`unknown` over `any`:** `any` silently propagates and disables checking; `unknown` forces a type guard/cast at the boundary.
- **`satisfies` over `as`:** Use `as const` + `satisfies` to check a value against a type without widening; reserve `as` for genuinely un-narrowable boundaries.
- **Type guards over casts:** Write `x is T` predicates (`typeof`/`in`/discriminated checks) instead of `as`.
- **Prefer `interface` for object shapes, `type` for unions/intersections/tuples.** An interface + `type` union is the idiomatic discriminated-union combo.
- **`Record<string, unknown>` over `object`/`{}`:** Bare `{}` accepts almost anything; use explicit shapes.
- **Exhaustiveness:** End `switch`/union handling with a `never` branch so new members fail to compile.
- **Enum vs union:** Prefer `const obj = {...} as const` + `type T = keyof typeof obj` (or string literal unions) over `enum` — `enum` is structurally opaque and import-order fragile. Use `enum` only for a true numeric/duplicated identity you must persist.
- **Index access:** With `noUncheckedIndexedAccess`, `obj[key]` is `T | undefined` — narrow before use. `Object.keys()` does NOT narrow key type.
- **`JSON.parse` returns `any`:** Validate external/untrusted JSON with a schema (zod) at the boundary; never trust the parsed type.
- **Discriminated unions:** Tag with a literal `type` field and narrow by it; prefer over multiple optional fields (which allow half-valid states).
- **Generics params:** Constrain with `extends`, prefer inferring over explicit `any`; return the same generic (`<T>(x: T): T`) not `T | undefined` unless documented.
- **Trust types inside:** Validate once at the admission boundary (zod/schema), then operate on typed models; serialize only at boundaries.
- **Trace unknown types:** Never assume a diagnostic is legitimate — find the source, check the spec, build the type.

### Diagnostic Resolution Quick Reference

| Diagnostic                             | Resolution                                                                                |
| -------------------------------------- | ----------------------------------------------------------------------------------------- |
| `implicit any`                         | Annotate the boundary or introduce a domain type; use `unknown` if truly untyped          |
| `noUncheckedIndexedAccess`             | Use a `Map`, default, `??`, or narrow before access — don't suppress                      |
| `exactOptionalPropertyTypes`           | Don't assign `undefined` to an omitted optional field; omit it or use `?: T \| undefined` |
| `strictPropertyInitialization`         | Use definite-assignment `!` only for real DI; prefer constructor init or strict init      |
| `noUnusedLocals/Parameters`            | Delete, or `_`-prefix intentionally unused params                                         |
| `ts(2307)` module not found (NodeNext) | Add `.js` extension to relative imports; check `package.json` `exports`/`type`            |
| `noPropertyAccessFromIndexSignature`   | `obj["k"]` instead of `obj.k` for index-signature keys                                    |
| `noFallthroughCasesInSwitch`           | Add `break`/`return` per case                                                             |
| `noUnnecessaryCondition`               | Simplify the now-always-true branch after narrowing                                       |
| `returnType` from `unknown`            | Strengthen the helper return type; remove the cast                                        |

**For complex types/diagnostics:** Invoke `typescript-expert` skill with the relevant argument (see Expertise Routing).

## Code Quality

- Prefer typed, small, single-responsibility modules over deep type gymnastics.
- Explicit error handling: `throw` typed errors or return `Result`; never silent `.catch(() => …)`.
- Async-first: use `await`/`async` and promise-native APIs; use `*Sync` only in sync-locked contracts or `process.on('exit')`.
- Avoid `!` non-null assertion except where provably safe (checked above) — it hides null bugs.
- Don't reach into vendored/private types across package boundaries.

## Performance & Concurrency

- **Profile before optimizing:** `--turbopack` build logs, React profiler, or `perf` profiling; don't guess.
- **Expensive work:** memoize with `useMemo`/`useCallback`/`cache` where semantics allow; avoid re-creating objects in hot render paths.
- **Large data:** streaming/chunked processing; avoid blocking the main thread with synchronous heavy work.
- **Bundles/deps:** `analyze` bundle output; prefer tree-shakeable ESM deps.

## Web & API

- **Runtime:** Node.js LTS + modern V8; `node:test`/Vitest for tests.
- **Framework:** React/Next.js or plain framework per project; `fetch` (undici) for HTTP.
- **Validation:** zod at every external boundary (API, file, env, config).
- **Data:** Prisma/Drizzle typed ORMs; never trust untyped SQL rows.

## Terminal Output & Scripting

- **Runner:** `tsx` for running TS/ESM scripts directly (replaces `ts-node`).
- **CLI args:** `parseArgs` (node) or `commander` for complex CLIs.
- **Output:** `chalk`/`nanocolors` for ANSI; JSON output via `JSON.stringify` for machine consumption.

## Expertise Routing

For complex types and domain gotchas, invoke the expert skill:

```
Skill(skill="typescript-expert", args="[types|testing|style|tooling]")
```

**When to invoke:**

- `types` — advanced generics/conditional/mapped/template-literal types, `infer`, utility types
- `testing` — Jest/Vitest structure, mocking, React Testing Library
- `style` — type-safety conventions, import ordering, naming rules
- `tooling` — strict tsconfig, monorepo (Turborepo/Nx), build performance, ESM/CJS migration

**Frontend (React/Next/Vue):** Invoke `frontend-expert` with `[react|vue|nextjs|nuxt|performance|state|forms|accessibility]` for component composition, SSR/hydration, and state management.
