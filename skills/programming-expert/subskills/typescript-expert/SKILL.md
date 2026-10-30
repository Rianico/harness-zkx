---
name: typescript-expert
description: >-
  TypeScript guide for advanced types, testing, and monorepo tooling. Use when writing complex types, decoding compiler errors, or tightening type safety.
meta:
  sources:
    - https://www.skills.sh/github/awesome-copilot/javascript-typescript-jest
    - https://www.skills.sh/wshobson/agents/typescript-advanced-types
    - https://www.skills.sh/lobehub/lobehub/typescript
    - https://www.skills.sh/sickn33/agentic-awesome-skills/typescript-expert
metadata:
  managed-by: programming-expert
---

# TypeScript Composed Expert

Four domains in one workflow: advanced type system, Jest testing, style conventions, and monorepo/tooling performance.

> [!tip] Attribution
> Raw sources live under `sources/` in this skill.

- `sources/github/awesome-copilot/javascript-typescript-jest/ORIGINAL.md` — Jest best practices.
- `sources/wshobson/agents/typescript-advanced-types/ORIGINAL.md` + `details.md` — advanced types.
- `sources/lobehub/lobehub/typescript/ORIGINAL.md` — LobeHub style and type safety.
- `sources/sickn33/agentic-awesome-skills/typescript-expert/ORIGINAL.md` — general expert, plus `references/` and `scripts/ts_diagnostic.py`.

## When invoked

0. **Route out-of-scope work:** if the task needs deep bundler internals, ESM/CJS cycle analysis, or compiler trace profiling, stop. Escalate to the orchestrator with your findings so far.

1. **Analyze project setup (adapt tooling):**

   ```bash
   npx tsc --version; node -v
   node -e "const p=require('./package.json');console.log(Object.keys({...p.devDependencies,...p.dependencies}||{}).join('\n'))" 2>/dev/null | grep -E 'biome|eslint|prettier|vitest|jest|turborepo|nx' || echo "No tooling detected"
   (test -f pnpm-workspace.yaml || test -f lerna.json || test -f nx.json || test -f turbo.json) && echo "Monorepo detected"
   uv run $SKILL_DIR/scripts/ts_diagnostic.py 2>&1 | head -n 80
   ```

   Respect existing `baseUrl`/`paths`, import style (absolute vs relative), and project scripts over raw tools. In monorepos, consider the [tooling — Monorepo Matrix](references/tooling.md) and project references before broad `tsconfig` changes.

2. **Classify the task** — type design, Jest testing, style fix, tooling/migration, or diagnostics — then apply the matching guidance below. Keep SKILL.md **tight** (20% solves 80%). Load deep detail behind pointers only when the branch needs it.

## Type system mastery

Load advanced types only when implementing complex type logic.

- **Generics** with constraints and multiple params — see [advanced-types — Generics](references/advanced-types.md)
- **Conditional types** (`extends ? :`, `infer`, distributive, nested) — see [advanced-types — Conditional Types](references/advanced-types.md)
- **Mapped types** (`Readonly`, `Partial`, key remapping, filtering by value) — see [advanced-types — Mapped Types](references/advanced-types.md)
- **Template literals** (`on${Capitalize<>}`, path building) — see [advanced-types — Template Literals](references/advanced-types.md)
- **Utility types** (`Pick`, `Omit`, `Record`, `Exclude`/`Extract`, `ReturnType`, `Awaited`) — see [cheatsheet — Utility Types](references/cheatsheet.md) and [utility-types.ts](references/utility-types.ts)
- **Branded types** for domain primitives (`Brand<string, 'UserId'>`) — see [advanced-types — Branded Types](references/advanced-types.md)
- **Patterns** — event emitter, type-safe API client, builder, `DeepReadonly`/`DeepPartial`, discriminated unions — see [advanced-types — Advanced Patterns](references/advanced-types.md)

### Critical cruxes

- **`exactOptionalPropertyTypes`:** optional field `{ prop?: string }` rejects `{ prop: undefined }`. Use conditional spreading to omit keys rather than assigning undefined: `...(val !== undefined && { val })`.
- **`noUncheckedIndexedAccess`:** array and record lookups yield `T | undefined`. Safely narrow before use (`const [first] = arr; if (first !== undefined)`) or iterate via `for...of`.
- **Zod boundary admission:** `JSON.parse`, fetch, or file reads return untyped data. Parse at admission boundaries via Zod schema (`Schema.parse(raw)`) to admit strictly typed models into domain code. Serialize only at egress.
- **Async `forEach` trap:** `items.forEach(async ...)` creates unhandled, unawaited floating promises. Use `await Promise.all(items.map(...))` for concurrency or `for (const item of items) await ...` for sequential execution.

> [!note] Writing rule
> Use `unknown` over `any`. Prefer `interface` for object shapes and `type` for unions. Leverage inference, create helper types, and document complex types with JSDoc. See [cheatsheet — Best Practices](references/cheatsheet.md) and [style-guide — Types and Type Safety](references/style-guide.md).

## Jest testing

Use when writing or fixing JavaScript/TypeScript tests.

- **Structure:** `*.test.ts` next to code or `__tests__/`, `describe('Unit', () => it('should ...'))` nesting — see [jest-testing — Test Structure](references/jest-testing.md)
- **Mocking:** `jest.mock()` for modules, `jest.spyOn()` for fns, `mockReturnValue()`/`mockImplementation()`, `jest.resetAllMocks()` in `afterEach` — see [jest-testing — Effective Mocking](references/jest-testing.md)
- **Async:** `async/await` or `resolves`/`rejects`, `jest.setTimeout()` for slow tests — see [jest-testing — Testing Async Code](references/jest-testing.md)
- **Snapshots & React:** small focused snapshots. Use React Testing Library + `userEvent` over `fireEvent`. Query by role/label — see [jest-testing — Snapshot Testing and React](references/jest-testing.md)
- **Matchers:** `toBe`/`toEqual`, `toBeTruthy`, `toMatch`, `toHaveLength`, `toHaveProperty`, `toThrow`, `toHaveBeenCalledWith` — see [jest-testing — Common Jest Matchers](references/jest-testing.md)

## Style and safety (LobeHub conventions)

Enforce when editing `*.ts`/`*.tsx`/`*.mts`.

- **Type safety:** avoid explicit annotations when inference covers them. Never write implicit `any`. Prefer `Record<PropertyKey, unknown>` over `object` — see [style-guide — Types and Type Safety](references/style-guide.md)
- **Async-first:** new IO must use `fs/promises`. Use `*Sync` only for a sync-locked contract or `process.on('exit')` — see [style-guide — Async Patterns](references/style-guide.md)
- **Imports:** separate `import type { }` (never `import { type }`), `simple-import-sort/imports`, alphabetical specifiers — see [style-guide — Imports](references/style-guide.md)
- **Structure:** destructuring, named exports over `default` (except framework-required), reuse `packages/utils` helpers (`isRecord`, `isPlainRecord`, etc.) — see [style-guide — Code Structure](references/style-guide.md)
- **Logging:** never log secrets. Use `console.error` in catch. Never silence with `.catch(() => fallback)` — see [style-guide — Logging](references/style-guide.md)

## Tooling, monorepo, and performance

- **Strict tsconfig** — enable `strict`, `noUncheckedIndexedAccess`, `noImplicitOverride`, `exactOptionalPropertyTypes`. Copy [tsconfig-strict.json](references/tsconfig-strict.json). Rationale: [cheatsheet — TSConfig Essentials](references/cheatsheet.md)
- **Module** — `ESNext`, `bundler` resolution, `esModuleInterop`, `target ES2022` — see [cheatsheet — TSConfig Essentials](references/cheatsheet.md)
- **Build perf** — `skipLibCheck`, `incremental`, precise `include`/`exclude`, project references `composite:true`. Diagnose via `npx tsc --extendedDiagnostics` and [ts_diagnostic.py](scripts/ts_diagnostic.py) — see [tooling — Debugging Mastery](references/tooling.md)
- **Linter choice** — Biome for speed (64 rules) vs ESLint for depth/plugins/type-aware — see [tooling — Biome vs ESLint](references/tooling.md)
- **Monorepo** — Turborepo (<20 pkgs, speed) vs Nx (>50 pkgs, plugins) — see [tooling — Monorepo Matrix](references/tooling.md)
- **Migration** — `allowJs`/`checkJs` incremental, `ts-migrate`/`typesync`, ESM-first `"type":"module"` — see [tooling — Migration](references/tooling.md)

## Deep module design & architecture

- **Reject classitis & layer bloat:** avoid Java-style enterprise stacks of 5 shallow layers (`Controller → DTO → Service → Mapper → Repository → Entity`). Each layer there merely shuffles fields. Functions, plain objects, and modules are first-class. Avoid classes that wrap a single method.
- **Narrow public surface, deep internals:** public entrypoints (`index.ts`) expose a minimal, cohesive API (e.g. `resolve()`, `mutate()`). Internal modules absorb caching (LRU), CAS addressing, atomic transactions, and boundary normalization without leaking internal helper types.
- **Design deepening:** submodule decomposition curing code smells (God files, Divergent Change, Shotgun Surgery) is permitted design deepening. Never widen public barrel exports without mandate.
- **Counterexample refutation & oracles:** reviewers and implementers must provide concrete minimal failing inputs (`input -> expected vs observed`) to prove defects. Verify non-trivial state machines or combinatorial logic with minimal exhaustive small-input oracle tables or property-based tests.

## Code review checklist

Apply exhaustively. Every item is a blocker.

- **Architecture:** narrow public API, zero shallow pass-through layers or classitis, internal modules absorbing complexity. Multi-step mutations bound in single transactions. Bug claims carry counterexamples.
- **Type safety:** no implicit `any` (`unknown` instead), strict null checks, minimal `as`, generic constraints, discriminated unions, explicit public return types
- **Best practices:** `interface` for shapes, const assertions, type guards over `as`, branded types for primitives, template literals where appropriate
- **Performance:** no deep instantiation (>10 recursion), no hot-path mapped types, `skipLibCheck` set, references configured
- **Modules:** consistent imports, no circular deps, barrel exports not over-bundled, ESM/CJS handled
- **Jest:** files named `*.test.ts`, behavior + a11y assertions, `userEvent`, snapshots reviewed
- **Style:** separate type imports, named exports, `satisfies` over `as`, `==` via `Object.is` pitfalls covered — see [style-guide](references/style-guide.md)

## Validate thoroughly

```bash
npm run -s typecheck || npx tsc --noEmit
npm test -s || npx vitest run --reporter=basic --no-watch || npx jest --no-coverage
# only if build affects outputs/config
npm run -s build
# optional trace
npx tsc --traceResolution > resolution.log 2>&1; grep "Module resolution" resolution.log | head
npx tsc --generateTrace trace --incremental false; npx @typescript/analyze-trace trace 2>&1 | head
```

> [!warning] Safety
> Avoid watch/serve (`--watch`, `serve`) in validation — use one-shot diagnostics only. Check `any` and `as` via `grep -rn ': any' --include='*.ts' src/` and [ts_diagnostic.py](scripts/ts_diagnostic.py).

## References

Deep content behind pointers (one level from SKILL.md):

- [Advanced Types & Patterns](references/advanced-types.md) — generics/conditional/mapped/template, builder/event-emitter/API client, type guards
- [TypeScript Cheatsheet](references/cheatsheet.md) — type basics, aliases, utility types, guards, unions, branded types, module declarations, TSConfig essentials
- [Utility Types Library](references/utility-types.ts) — `Brand`, `Result`, `Option`, `DeepReadonly`, `PickByType`, `UnionToTuple`, `assertNever`
- [TSConfig Strict](references/tsconfig-strict.json) — strict baseline to copy
- [Jest Testing](references/jest-testing.md) — Jest structure, mocking, async, snapshots, matchers
- [Style Guide](references/style-guide.md) — LobeHub type safety, async-first, imports, structure, logging
- [Tooling & Monorepo](references/tooling.md) — Biome/ESLint, Turborepo/Nx, migration, ESM, debugging, performance
- Diagnostic script: `uv run $SKILL_DIR/scripts/ts_diagnostic.py`
