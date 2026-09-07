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

- **Formatting:** `camelCase` vars/funcs, `PascalCase` types/classes/components; `import type {}` for type-only imports; sorted `stdlib → third-party → local`; named exports over `default`.
- **Strict:** `strict` + `noUncheckedIndexedAccess` + `exactOptionalPropertyTypes` + `noImplicitOverride` in every `tsconfig.json`.
- **Typed boundaries:** `JSON.parse` returns `any` → `zod`/`valibot` `parse` at admission boundary (API/file/env/config); typed model inside; serialize only at output.
- **Immutability:** `readonly`/`ReadonlyArray`/`as const` over mutation; avoid `Array.push` on shared state; `undefined` for missing, `null` only for explicit sentinel.

## Type Safety (First Principle)

- **Fix over suppress;** narrowest suppression scope; never blanket-disable.
- **`unknown` over `any`, `satisfies` over `as`, type guards over casts:** `unknown` forces `typeof`/`in`/discriminated guard; `as const satisfies` checks without widening; `x is T` predicates over `as`.
- **Shape vs union:** `interface` for object shapes, `type` for unions/intersections/tuples; discriminated union with literal `type` tag; `Record<string, unknown>` over `{}`/`object`.
- **Exhaustiveness:** `never` branch on `switch`/union so new members fail to compile; `with noUncheckedIndexedAccess`, `obj[key]` is `T | undefined` — narrow before use.
- **Generics:** `T extends U` constraints, avoid explicit `any`; `enum` → `as const` map + `keyof typeof` unless true persisted identity.

## Expertise Routing (Use `Skill` tool)

If your task needs deep methodology, you MUST pause and invoke `Skill` for `programming-expert` (`typescript-expert`):

- **Types/boundaries:** `Skill(skill="programming-expert", args="typescript-expert types")` — generics, conditional/mapped/template literal, branded types, utility types.
- **Testing:** `Skill(skill="programming-expert", args="typescript-expert testing")` — Vitest/Jest, mocking, React Testing Library.
- **Tooling/style:** `Skill(skill="programming-expert", args="typescript-expert tooling")` — strict config, monorepo, ESM/CJS, lint choice.

**CRITICAL:** Do not guess type fixes or `strict` workarounds without retrieving the expert skill first.
