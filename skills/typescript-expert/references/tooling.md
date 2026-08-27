# Tooling, Monorepo & Performance

> Source: `sickn33/agentic-awesome-skills/typescript-expert` (tooling/monorepo/migration/performance/debug sections). Deduped: type-level content lives in [[advanced-types]] and [[cheatsheet]], here focuses on config and workflow.

## Modern Tooling Expertise

### Biome vs ESLint

**Use Biome when:**
- Speed is critical (often faster than traditional setups)
- Want single tool for lint + format
- TypeScript-first project
- Okay with 64 TS rules vs 100+ in typescript-eslint

**Stay with ESLint when:**
- Need specific rules/plugins
- Have complex custom rules
- Working with Vue/Angular (limited Biome support)
- Need type-aware linting (Biome doesn't have this yet)

### Type Testing Strategies

**Vitest Type Testing (Recommended)**
```typescript
// in avatar.test-d.ts
import { expectTypeOf } from 'vitest'
import type { Avatar } from './avatar'

test('Avatar props are correctly typed', () => {
  expectTypeOf<Avatar>().toHaveProperty('size')
  expectTypeOf<Avatar['size']>().toEqualTypeOf<'sm' | 'md' | 'lg'>()
})
```

**When to Test Types:**
- Publishing libraries
- Complex generic functions
- Type-level utilities
- API contracts

## Debugging Mastery

### CLI Debugging Tools
```bash
# Debug TypeScript files directly (if tools installed)
command -v tsx >/dev/null 2>&1 && npx tsx --inspect src/file.ts
command -v ts-node >/dev/null 2>&1 && npx ts-node --inspect-brk src/file.ts

# Trace module resolution issues
npx tsc --traceResolution > resolution.log 2>&1
grep "Module resolution" resolution.log

# Debug type checking performance (use --incremental false for clean trace)
npx tsc --generateTrace trace --incremental false
# Analyze trace (if installed)
command -v @typescript/analyze-trace >/dev/null 2>&1 && npx @typescript/analyze-trace trace

# Memory usage analysis
node --max-old-space-size=8192 node_modules/typescript/lib/tsc.js
```

### Custom Error Classes
```typescript
// Proper error class with stack preservation
class DomainError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number
  ) {
    super(message);
    this.name = 'DomainError';
    Error.captureStackTrace(this, this.constructor);
  }
}
```

## Current Best Practices

### Strict by Default
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "noPropertyAccessFromIndexSignature": true
  }
}
```

### ESM-First Approach
- Set `"type": "module"` in package.json
- Use `.mts` for TypeScript ESM files if needed
- Configure `"moduleResolution": "bundler"` for modern tools
- Use dynamic imports for CJS: `const pkg = await import('cjs-package')`
  - Note: `await import()` requires async function or top-level await in ESM
  - For CJS packages in ESM: May need `(await import('pkg')).default` depending on the package's export structure and your compiler settings

### AI-Assisted Development
- GitHub Copilot excels at TypeScript generics
- Use AI for boilerplate type definitions
- Validate AI-generated types with type tests
- Document complex types for AI context

## Debugging (from same source)

### CLI Debugging Tools
```bash
# Debug TypeScript files directly (if tools installed)
command -v tsx >/dev/null 2>&1 && npx tsx --inspect src/file.ts
command -v ts-node >/dev/null 2>&1 && npx ts-node --inspect-brk src/file.ts

# Trace module resolution issues
npx tsc --traceResolution > resolution.log 2>&1
grep "Module resolution" resolution.log

# Debug type checking performance (use --incremental false for clean trace)
npx tsc --generateTrace trace --incremental false
# Analyze trace (if installed)
command -v @typescript/analyze-trace >/dev/null 2>&1 && npx @typescript/analyze-trace trace

# Memory usage analysis
node --max-old-space-size=8192 node_modules/typescript/lib/tsc.js
```

### Custom Error Classes
```typescript
// Proper error class with stack preservation
class DomainError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number
  ) {
    super(message);
    this.name = 'DomainError';
    Error.captureStackTrace(this, this.constructor);
  }
}
```

## Current Best Practices (Strict & ESM)

### Strict by Default
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "exactOptionalPropertyTypes": true,
    "noPropertyAccessFromIndexSignature": true
  }
}
```

### ESM-First Approach
- Set `"type": "module"` in package.json
- Use `.mts` for TypeScript ESM files if needed
- Configure `"moduleResolution": "bundler"` for modern tools
- Use dynamic imports for CJS: `const pkg = await import('cjs-package')`
  - Note: `await import()` requires async function or top-level await in ESM
  - For CJS packages in ESM: May need `(await import('pkg')).default` depending on the package's export structure and your compiler settings

### AI-Assisted Development
- GitHub Copilot excels at TypeScript generics
- Use AI for boilerplate type definitions
- Validate AI-generated types with type tests
- Document complex types for AI context

> [!tip] Scripts
> Use `uv run $SKILL_DIR/scripts/ts_diagnostic.py` for project diagnostics (versions, tsconfig, tooling, monorepo, `any`/`as` counts, `tsc --extendedDiagnostics`).
