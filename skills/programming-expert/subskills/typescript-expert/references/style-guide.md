# Style Guide — TypeScript Conventions

> Source: `lobehub/lobehub/typescript`. Enforce when editing `*.ts`/`*.tsx`/`*.mts`. Deduplicated against cheatsheet type-safety section.

---
name: typescript
description: 'Standard TypeScript style and type-safety guide. Use when editing TS/TSX/MTS, fixing types, choosing interface vs type, avoiding any/object, import type, async flow, or ts-expect-error.'
user-invocable: false
---

# TypeScript Code Style Guide

## Types and Type Safety

- Avoid explicit type annotations when TypeScript can infer
- Avoid implicitly `any`; explicitly type when necessary
- Use accurate types: prefer `Record<PropertyKey, unknown>` over `object` or `any`
- Prefer `interface` for object shapes (e.g., React props); use `type` for unions/intersections
- Prefer `as const satisfies XyzInterface` over plain `as const`
- Prefer `@ts-expect-error` over `@ts-ignore` over `as any`
- Avoid meaningless null/undefined parameters; design strict function contracts
- Prefer ES module augmentation (`declare module '...'`) over `namespace`; do not introduce `namespace`-based extension patterns
- When a type needs extensibility, expose a small mergeable interface at the source type and let each feature/plugin augment it locally instead of centralizing all extension fields in one registry file
- For package-local extensibility patterns like `PipelineContext.metadata`, define the metadata fields next to the processor/provider/plugin that reads or writes them

## Async Patterns

- Prefer `async`/`await` over callbacks or `.then()` chains
- **Async-first for IO**: new IO code (fs, child\_process, etc.) must use async APIs at its boundaries — use promise-based variants like `import { readFile } from 'fs/promises'`, never `*Sync` by default. Function coloring is asymmetric: async→sync migration is never needed, while sync→async (when IO gets slower, gains concurrency, or grows a subprocess/network call) forces rewriting every caller up the chain — sync-first debt that compounds. Micro-costs of async (thread-pool dispatch, cache races) are not valid reasons: races are solved by caching the promise instead of the result
- `*Sync` is acceptable in exactly one place: call sites locked inside a synchronous contract you don't control — an existing sync signature chain (don't virally refactor a legacy sync chain in a bugfix, but new standalone modules must not extend such chains), or sync-only callbacks like `process.on('exit')`. Module-load-time and CLI startup init are NOT exceptions — use top-level `await` (ESM) there
- Use `Promise.all`, `Promise.race` for concurrent operations where safe

## Imports

- This project uses `simple-import-sort/imports` and `consistent-type-imports` (`fixStyle: 'separate-type-imports'`)

- **Separate type imports**: always use `import type { ... }` for type-only imports, NOT `import { type ... }` inline syntax

- When a file already has `import type { ... }` from a package and you need to add a value import, keep them as **two separate statements**:

  ```ts
  import type { UserProfile } from './types';
  import { RequestTrigger } from './types';
  ```

- **Re-export scope (`export … from`)**: `export { Foo } from './foo'` forwards `Foo` without binding it in the local module scope. If code in the same file references `Foo`, write separate import and export statements: `import { Foo } from './foo'; export { Foo };`. When converting imports to re-exports, verify with a token-anchored grep (`rg -w Foo` or `\bFoo\b`) and run `tsc`.

- Within each import statement, specifiers are sorted **alphabetically by name**

## Code Structure

- Prefer object destructuring
- Use consistent, descriptive naming; avoid obscure abbreviations
- Replace magic numbers/strings with well-named constants
- Defer formatting to tooling
- Prefer **named exports** over `export default` — keeps refactor renames and IDE auto-import in sync, and avoids the `default` re-naming drift you get with `import Foo from './foo'`. Reserve `export default` for files where the framework requires it (Next.js page/route/layout, React.lazy targets, config files like `vitest.config.ts`). The codebase still has many `export default` occurrences — that's historical debt, not a pattern to copy; do not model new code on existing `export default` usage outside the framework-required cases above
- Before adding local helpers for common guards/parsing/normalization (record checks, string extraction, empty-string handling, timing helpers, JSON-safe utilities, etc.), search shared utility packages/directories first. If the helper already exists or clearly belongs there, import it from the shared utility module instead of duplicating tiny helpers across feature files.
- **Deep modules over classitis:** Avoid creating shallow 5-line classes or DTO/mapper hierarchies that do nothing but shuffle properties between layers (e.g. Controller → DTO → Service → Mapper → Repo). Expose simple, narrow module APIs that absorb rich internal complexity (caching, transactions, validation, persistence) behind clean functions or minimal facades.

## Strings and Regex

- **Precedence fallback tiers (`??`)**: Use `??`-chained tier functions (`resolveTier1() ?? resolveTier2() ?? fallback`) to preserve fallback order and lazy evaluation. Avoid `||` when `""`, `0`, or `false` are valid values. Note that `??` preserves `NaN` (`Number(raw) ?? fallback` returns `NaN`). Name tier functions for their precedence.
- **`String.raw` for backslash literals**: Use `String.raw` for string literals that must carry backslashes (Windows paths, `new RegExp` constructor sources, escape-sequence fixtures). Note that `String.raw` cannot end in a lone unescaped backslash; a trailing backslash escapes the closing delimiter and triggers a syntax error. Trailing backslashes require `"C:\\"`.
- **Precompiled regexes (non-global)**: Precompile static regexes at module scope with `.exec()`, but only for **non-global** patterns. Global `/g` regexes retain mutable `lastIndex` across calls and tests. For global iteration, use `str.matchAll(/.../g)` (requires `/g` or throws `TypeError`) or `str.replaceAll()`. Guard against catastrophic backtracking (ReDoS) by bounding input length (`^.{0,200}$`) or splitting ambiguous patterns (prefix-exec + linear suffix); verify rewrites via property tests over a generated corpus. `RegExp.exec()` returns `RegExpExecArray | null`, requiring explicit narrowing under `strict`.

## UI and Theming

- Use design system / UI component libraries instead of raw unstyled HTML tags
- Design for dark mode and mobile responsiveness
- Use design tokens or CSS theme variables instead of hard-coded colors

## Performance

- Query only required columns from database

## Reusability

- Reuse existing utils in shared utility packages or installed npm packages
- Do not hand-roll reusable record/object-map guards such as `typeof value === 'object' && value !== null`; import or centralize helpers like `isRecord`, `isPlainRecord`, `isObjectLike`, `toRecord`, `pickString`, `UnknownRecord`, etc. in a shared utils module.
- Assign `Date.now()` to a constant once and reuse for consistency

## Logging

- Never log user private information (API keys, etc.)
- Don't use `import { log } from 'debug'` directly (logs to console)
- Use `console.error` in catch blocks instead of debug package
- Always log the error in `.catch()` callbacks — silent `.catch(() => fallback)` swallows failures and makes debugging impossible

> [!tip] Deduplication note
> Type-safety overlap with [[cheatsheet#types-and-type-safety]] and [[advanced-types#utility-types]] is intentional split: cheatsheet is type reference, style-guide is project lint/import/async conventions.

> [!warning] Do not hand-roll `isRecord` helpers — reuse shared utility packages or project helpers.
