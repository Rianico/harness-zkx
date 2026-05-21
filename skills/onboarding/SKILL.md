---
name: onboarding
description: >-
  Systematically analyze a codebase at multiple scales. Use for global project onboarding (architecture map, entry points, conventions, CLAUDE.md) or for "zooming out" from a specific module to understand its neighbors and higher-level abstractions.
argument-hint: >-
  [--zoom-out] [--global]
---

# Codebase Onboarding & Exploration

Systematically analyze an unfamiliar codebase, either as a whole or centered around a specific area.

## Modes

| Mode | Flag | Focus | Output |
| :--- | :--- | :--- | :--- |
| **Global** | `--global` (default) | The entire repository | Onboarding Guide + `CLAUDE.md` |
| **Local** | `--zoom-out` | Current module & neighbors | High-level map of callers and data flow |

---

## Phase 1: Reconnaissance (Shared)

Gather raw signals about the project without reading every file. Run these checks in parallel:

1. **Package manifest detection** (package.json, go.mod, etc.)
2. **Framework fingerprinting** (next.config, django settings, etc.)
3. **Entry point identification** (main.js, cmd/, etc.)
4. **Directory structure snapshot** (Top 2 levels)
5. **Config detection** (.eslintrc, Dockerfile, etc.)

---

## Phase 2: Execution

### Option A: Global Onboarding (`--global`)

1. **Architecture Mapping**: Identify tech stack, patterns, and key directory purposes.
2. **Convention Detection**: Identify naming, error handling, and Git patterns.
3. **Generate Artifacts**:
   - **Onboarding Guide**: Durable summary of project structure.
   - **Starter CLAUDE.md**: Project-specific rules.

### Option B: Local Exploration (`--zoom-out`)

When you are lost in a specific area of code, perform a "Zoom Out" to regain perspective:

1. **Identify the Core**: Start with the current file/module and its immediate context.
2. **Map the Neighborhood**:
   - **Find Callers**: Search the codebase to identify who uses this module. Use semantic code navigation (LSP) or text search where appropriate.
   - **Analyze Dependencies**: Scan imports and module declarations to find what this module uses.
   - **Identify Interfaces/Contracts**: Determine the boundaries and contracts that define how this area interacts with the rest of the system.
3. **Abstract**: 
   - Move up one layer (e.g., from `Repository` to `Service`, or `Component` to `Page`).
   - Map how this module fits into the **Domain Glossary** (from `CONTEXT.md`).
4. **Output**: A concise mental map or diagram (text-based) of the local architecture.

---

## Best Practices

1. **Focus on Discovery**: Use file discovery and text search tools for mapping; use targeted reading only for verification.
2. **Respect CLAUDE.md**: Use existing project instructions to anchor the "Zoom Out" mapping.
3. **Domain-First**: Always use the terms found in `CONTEXT.md` to describe the map.


## Anti-Patterns

- **Global onboarding during a fix** — Use `--zoom-out` if you just need to understand a file; don't re-onboard the whole project.
- **Deep nesting in Zoom Out** — Only map immediate neighbors; don't chase the entire stack.
