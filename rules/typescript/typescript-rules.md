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

You are operating in a TypeScript codebase.

## Core TypeScript Standards (80% Base)

- **Package manager & tooling:** prefer `pnpm` (fallback `npm`). Avoid yarn classic. Runner: `tsx` for scripts/ESM. Lint/format: `oxlint` and `oxfmt`. Use ESLint only for type-aware depth. Treat Biome as deprecated compatibility. Dedicated typecheck: `tsc --noEmit` (or `tsc -b` for project references) in CI.
- **Strict tsconfig:** enable `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `verbatimModuleSyntax`, `skipLibCheck`. Target modern ESM (`"type": "module"`, `module: "ESNext"`, `moduleResolution: "bundler"`).
- **Typed boundaries with Zod:** `JSON.parse`, fetch, env vars, and file reads return untyped data (`any`/`unknown`). Parse at admission boundaries with Zod schemas (`Schema.parse(raw)`) to admit strictly typed models. Internal domain logic relies on typed models. Serialize only at egress.
- **Formatting & structure:** `camelCase` vars/functions, `PascalCase` types/classes/components. Use `import type { }` for type-only imports. Sort imports `stdlib → third-party → local`. Prefer named exports over `default` (except framework-mandated routes/configs).
- **Immutability:** `readonly`/`ReadonlyArray`/`as const` over mutation. Use `undefined` for missing values. Reserve `null` for explicit sentinel values.

## Critical Cruxes (Blockers)

- **`exactOptionalPropertyTypes` key omission:** an optional property `{ prop?: string }` rejects `{ prop: undefined }`. Use conditional spreading `...(val !== undefined && { val })` to omit keys instead of assigning `undefined`.
- **`noUncheckedIndexedAccess` narrowing:** array indices (`arr[i]`) and record lookups (`map[key]`) return `T | undefined`. Safely narrow before use (`const [first] = arr; if (first !== undefined) ...`) or use `for...of`.
- **`any` elimination:** never introduce or allow `any`. Use `unknown` for unadmitted data. Derive types with `z.infer<typeof Schema>`. Use `satisfies` over `as` for literal validation without widening. Use custom type guards (`val is T`) or assertion functions (`asserts val is T`) instead of type casts.
- **Async `forEach` trap:** never use `items.forEach(async ...)`. It ignores returned promises and creates unhandled floating executions. Use `await Promise.all(items.map(...))` for concurrent operations or `for (const item of items) await ...` for sequential operations.
- **`assertNever` exhaustiveness:** end every discriminated-union `switch` with `default: return assertNever(state);`. Union additions then fail at compile time.

## Expertise Routing (Use `Read` tool)

`typescript-expert` is a managed subskill of the `programming-expert` router. Subskills are hidden from discovery (`managed-by`). Do not invoke `Skill(skill="typescript-expert")` or `Skill(skill="programming-expert", args="typescript-expert")`. Instead, read the required reference directly:

- `skills/programming-expert/subskills/typescript-expert/SKILL.md` — subskill guide
- `skills/programming-expert/subskills/typescript-expert/references/advanced-types.md` — advanced types & patterns
- `skills/programming-expert/subskills/typescript-expert/references/cheatsheet.md` — cheatsheet, TSConfig essentials, Zod boundaries
- `skills/programming-expert/subskills/typescript-expert/references/jest-testing.md` — testing (Jest / Vitest)
- `skills/programming-expert/subskills/typescript-expert/references/tooling.md` — tooling, monorepo, strict config
- `skills/programming-expert/subskills/typescript-expert/references/style-guide.md` — style guide & conventions

**CRITICAL:** Do not guess type fixes, loose casts, or `strict` workarounds without reading the expert documentation first.
