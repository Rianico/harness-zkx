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

You are operating in a TypeScript codebase. Before proceeding, review and apply these rules.

## Core TypeScript Standards (80% Base)

- **Package manager & tooling:** `pnpm` (preferred; fallback `npm`, avoid yarn classic). Runner: `tsx` for scripts/ESM. Lint/format: Biome (fast lint+format) or ESLint; keep one. Dedicated typecheck: `tsc --noEmit` (or `tsc -b` for project references) in CI.
- **Strict tsconfig:** Enable `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `verbatimModuleSyntax`, `skipLibCheck`. Target modern ESM (`"type": "module"`, `module: "ESNext"`, `moduleResolution: "bundler"`).
- **Typed boundaries with Zod:** `JSON.parse`, fetch, env vars, and file reads return untyped data (`any`/`unknown`). Parse at admission boundaries with Zod schemas (`Schema.parse(raw)`) to admit strictly typed models; internal domain logic relies on typed models; serialize only at egress.
- **Formatting & structure:** `camelCase` vars/functions, `PascalCase` types/classes/components; `import type { }` for type-only imports; sorted imports `stdlib → third-party → local`; named exports over `default` (except framework-mandated routes/configs).
- **Immutability:** `readonly`/`ReadonlyArray`/`as const` over mutation; `undefined` for missing values, `null` only for explicit sentinel values.

## Critical Cruxes (Blockers)

- **`exactOptionalPropertyTypes` key omission:** An optional property `{ prop?: string }` rejects `{ prop: undefined }`. Use conditional spreading `...(val !== undefined && { val })` to omit keys instead of assigning `undefined`.
- **`noUncheckedIndexedAccess` narrowing:** Array indices (`arr[i]`) and record lookups (`map[key]`) return `T | undefined`. Safely narrow before use (`const [first] = arr; if (first !== undefined) ...`) or use `for...of`.
- **`any` elimination:** Never introduce or allow `any`. Use `unknown` for unadmitted data, derive types with `z.infer<typeof Schema>`, use `satisfies` over `as` for literal validation without widening, and use custom type guards (`val is T`) or assertion functions (`asserts val is T`) instead of type casts.
- **Async `forEach` trap:** Never use `items.forEach(async ...)`. It ignores returned promises and creates unhandled floating executions. Use `await Promise.all(items.map(...))` for concurrent operations or `for (const item of items) await ...` for sequential operations.
- **`assertNever` exhaustiveness:** Always enforce exhaustiveness on discriminated unions / `switch` statements with `default: return assertNever(state);` so additions to union variants trigger compile-time errors.

## Expertise Routing (Use `Read` tool)

`typescript-expert` is a managed subskill of `programming-expert` router. Subskills are hidden from discovery (`managed-by: programming-expert`). Do NOT invoke `Skill(skill="typescript-expert")` or `Skill(skill="programming-expert", args="typescript-expert")`. Instead, read the required reference directly using the `Read` tool:

- **Subskill guide:** `Read skills/programming-expert/subskills/typescript-expert/SKILL.md`
- **Advanced types & patterns:** `Read skills/programming-expert/subskills/typescript-expert/references/advanced-types.md`
- **Cheatsheet & Zod boundaries:** `Read skills/programming-expert/subskills/typescript-expert/references/cheatsheet.md`
- **Testing (Jest / Vitest):** `Read skills/programming-expert/subskills/typescript-expert/references/jest-testing.md`
- **Tooling, monorepo & strict config:** `Read skills/programming-expert/subskills/typescript-expert/references/tooling.md`
- **Style guide & conventions:** `Read skills/programming-expert/subskills/typescript-expert/references/style-guide.md`

**CRITICAL:** Do not guess type fixes, loose casts, or `strict` workarounds without reading the expert documentation first.
