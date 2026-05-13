---
name: basedpyright-expert
description: |
  Domain expertise for the basedpyright Python type checker covering configuration, type inference, diagnostic rules, migration from mypy/pyright, and library authoring. TRIGGER when: configuring basedpyright or pyright; setting up pyrightconfig.json or pyproject.toml; fixing pyright errors; enabling strict mode; migrating from mypy; writing type stubs; verifying type completeness; resolving import issues; working with Any/Unknown types; type narrowing patterns; overload resolution; baseline workflow; basedpyright-exclusive diagnostic rules.
argument-hint: "[topic]"
---

# Basedpyright Expert

> **Version:** v1.39.4 | **Last Updated:** 2026-05-13
>
> Check for updates: https://github.com/DetachHead/basedpyright

Basedpyright is a Python static type checker forked from pyright with stricter defaults, new diagnostic rules, and improved type narrowing. It supports PEP 484 through PEP 764.

## Code Generation Rules

1. Use `# pyright: ignore[ruleName]` for line-level suppression (preferred over `# type: ignore`)
2. Prefer `Sequence`, `Mapping`, `Container` over `list`, `dict`, `set` for covariant type parameters
3. Use `reveal_type(expr)` to debug inferred types during development

## Quick Start

**Minimal pyproject.toml:**
```toml
[tool.basedpyright]
include = ["src"]
pythonVersion = "3.12"
typeCheckingMode = "recommended"
```

**Enable recommended mode with baseline for existing codebases:**
```bash
basedpyright --writebaseline  # Creates ./.basedpyright/baseline.json
```

## Type Checking Modes

| Mode | Description | Key Behavior |
|------|-------------|--------------|
| `off` | No type checking | Syntax errors only |
| `basic` | Minimal checking | No strict inference |
| `standard` | Default pyright | Standard checks |
| `strict` | Strict pyright | Most checks enabled |
| `recommended` | Basedpyright default | All checks as warning/error, failOnWarnings=true |
| `all` | Maximum strictness | All checks as errors |

## Configuration Hierarchy

1. `pyrightconfig.json` (highest priority)
2. `[tool.basedpyright]` in `pyproject.toml`
3. `[tool.pyright]` in `pyproject.toml` (backwards compat)
4. Language server settings (lowest priority)

## Key Configuration Settings

### Environment Options

| Setting | Type | Description |
|---------|------|-------------|
| `include` | array | Paths to include in analysis |
| `exclude` | array | Paths to exclude from analysis |
| `pythonVersion` | string | Target Python version (e.g., "3.12") |
| `pythonPlatform` | string | Target platform ("All", "Linux", "Windows", "Darwin") |
| `extraPaths` | array | Additional import search paths |
| `executionEnvironments` | array | Per-subdirectory config overrides |

### Basedpyright-Exclusive Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `failOnWarnings` | bool | true in recommended | Exit non-zero on warnings |
| `allowedUntypedLibraries` | array | [] | Suppress unknown types from untyped libs |
| `baselineFile` | path | ./.basedpyright/baseline.json | Path to baseline file |
| `strictGenericNarrowing` | bool | false | Narrow generics to bound/constraint |

### Discouraged Settings

| Setting | Reason |
|---------|--------|
| `venvPath` / `venv` | Use `.venv` convention or `--pythonpath` |
| `enableTypeIgnoreComments` | `# pyright: ignore` is safer |
| `enableReachabilityAnalysis` | Use `reportUnreachable` instead |

## Diagnostic Categories

| Category | CLI Behavior |
|----------|--------------|
| `error` | Exit code 1 |
| `warning` | Exit code 1 if `failOnWarnings=true` |
| `information` | Never fails CLI |
| `hint` | LSP only, not reported in CLI |
| `none` | Disabled |

## Common Patterns

### Suppress Specific Diagnostic
```python
x = some_func()  # pyright: ignore[reportUnknownVariableType]
```

### File-Level Strict Mode with Override
```python
# pyright: strict, reportPrivateUsage=false
```

### Debug Inferred Types
```python
x = some_expression
reveal_type(x)  # Shows inferred type in output
```

### Immutable Container for Covariance
```python
# WRONG: list[int] not assignable to list[int | None]
my_list_2: list[int | None] = my_list_1  # Error

# RIGHT: Use Sequence for covariant type parameter
my_list_2: Sequence[int | None] = my_list_1  # OK
```

### Type Narrowing with isinstance
```python
def func(val: int | str):
    if isinstance(val, int):
        reveal_type(val)  # int
    else:
        reveal_type(val)  # str
```

### Aliased Conditional for Guard Reuse
```python
def func(x: str | None):
    is_str = x is not None
    if is_str:
        reveal_type(x)  # str
```

### Baseline Workflow for Gradual Adoption
```bash
# 1. Enable recommended mode
# 2. Capture existing errors:
basedpyright --writebaseline
# 3. Fix new code; baselined errors auto-remove on save
# 4. In CI, use lock mode (default in CI):
basedpyright --baselinemode=lock
```

## Basedpyright-Exclusive Diagnostic Rules

| Rule | Description | Severity in Recommended |
|------|-------------|------------------------|
| `reportAny` | Ban all Any usage | warning |
| `reportExplicitAny` | Ban explicit Any in annotations | warning |
| `reportIgnoreCommentWithoutRule` | Require rule in ignore comments | warning |
| `reportPrivateLocalImportUsage` | Private imports in own code | warning |
| `reportImplicitRelativeImport` | Ban implicit relative imports | error |
| `reportInvalidCast` | Casts to non-overlapping types | error |
| `reportUnsafeMultipleInheritance` | Multiple bases with __init__ | error |
| `reportUnusedParameter` | Unused function parameters | warning |
| `reportImplicitAbstractClass` | Abstract subclass without ABC | error |
| `reportEmptyAbstractUsage` | ABC with no abstract methods | warning |
| `reportIncompatibleUnannotatedOverride` | Incompatible override of unannotated attr | none (all: error) |
| `reportUnannotatedClassAttribute` | Require annotations on class attrs | warning |
| `reportInvalidAbstractMethod` | abstractmethod on non-abstract class | warning |
| `reportSelfClsDefault` | self/cls with default value | warning |

## Import Resolution Order

1. `stubPath` directory
2. Code within workspace (root, extraPaths, `src/`)
3. Installed packages (stub packages, inline stubs, py.typed, library code)
4. stdlib typeshed stubs
5. Third-party typeshed stubs
6. Same directory as importing file

## CLI Reference

| Flag | Description |
|------|-------------|
| `--writebaseline` | Write new errors to baseline file |
| `--baselinemode=auto\|lock\|discard` | Control baseline updates |
| `--verifytypes <lib>` | Verify type completeness |
| `--createstub <import>` | Generate type stubs |
| `--outputjson` | JSON output format |
| `--warnings` | Exit 1 on warnings (redundant with failOnWarnings=true) |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No errors |
| 1 | One or more errors |
| 2 | Fatal error, no diagnostics |
| 3 | Invalid configuration |
| 4 | Illegal command-line parameters |

## References

For detailed patterns and complete API documentation, read:

| Module | File | Source | Topics |
|--------|------|--------|--------|
| getting-started | `$SKILL_DIR/references/getting-started.md` | `basedpyright-expert-raw/005-features.md`, `006-getting-started.md` | PEP support, adoption progression, IDE commands |
| configuration | `$SKILL_DIR/references/configuration.md` | `basedpyright-expert-raw/001-command-line.md`, `002-comments.md`, `003-config-files.md`, `004-language-server-settings.md` | CLI, config files, comments, LSP settings, diagnostic defaults |
| type-basics | `$SKILL_DIR/references/type-basics.md` | `basedpyright-expert-raw/007-type-concepts.md`, `014-type-inference.md` | Assignability, generics, inference, Unknown vs Any |
| type-advanced | `$SKILL_DIR/references/type-advanced.md` | `basedpyright-expert-raw/013-type-concepts-advanced.md` | Narrowing, guards, overloads, class/instance vars |
| diagnostic-rules | `$SKILL_DIR/references/diagnostic-rules.md` | `basedpyright-expert-raw/020-new-diagnostic-rules.md` | Basedpyright-exclusive rules with motivation |
| migration | `$SKILL_DIR/references/migration.md` | `basedpyright-expert-raw/012-mypy-comparison.md`, `017-baseline.md`, `018-better-defaults.md` | mypy comparison, baseline workflow, better defaults |
| imports-and-stubs | `$SKILL_DIR/references/imports-and-stubs.md` | `basedpyright-expert-raw/010-import-resolution.md`, `015-type-stubs.md` | Import resolution, stubs, builtins |
| typed-libraries | `$SKILL_DIR/references/typed-libraries.md` | `basedpyright-expert-raw/016-typed-libraries.md` | Library authoring, type completeness, py.typed |

For edge cases and complete API surface, read `$SKILL_DIR/references/basedpyright-expert-raw/`.

## When to Use Raw Docs

Read `$SKILL_DIR/references/basedpyright-expert-raw/` when:
- Curated references lack the exact flag, option, or behavior you need
- You need the complete API surface for an uncommon command variant
- The curated summary conflicts with your observation -- raw docs are authoritative

## Path Convention

- **Prose text:** Use `$SKILL_DIR/references/...` -- cwd is unknown to the reader
- **Markdown links:** Use relative paths like `[text](references/getting-started.md)` -- standard relative-to-file convention

## When Writing Code

1. Prefer `# pyright: ignore[ruleName]` with explicit rule over bare `# pyright: ignore`
2. Use immutable container types (Sequence, Mapping) for covariant parameters
3. Add type annotations at boundaries; internal code can rely on inference
4. Run `basedpyright --verifytypes` for library packages

## When Answering Questions

1. Answer from patterns and tables above first
2. If the question involves deeper details, read `$SKILL_DIR/references/<module>.md`
3. For edge cases, read `$SKILL_DIR/references/basedpyright-expert-raw/`
4. If still insufficient, inform user and answer from built-in knowledge
