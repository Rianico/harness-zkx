# Diagnostic Resolution Playbook

> **For type checker configuration, diagnostic rules, and suppression decisions, see the basedpyright-expert skill.**

Patterns and decisions for resolving Python type checker (basedpyright) and linter (ruff) warnings.

## Decision Framework

```
Diagnostic appears
    │
    ├─ Is it a real issue?
    │   ├─ Yes → Fix the code
    │   └─ No → Is it a false positive?
    │       ├─ Single occurrence → Line-level suppression
    │       ├─ Pattern in one file → File-level suppression with comment
    │       └─ Category-level false positive → Targeted config option
    │
    └─ Is it intentional pattern (e.g., Typer)?
        └─ Line-level suppression with comment
```

## Basedpyright Diagnostics

### `reportMissingTypeStubs`

**What it means:** Imported module has no `.pyi` stub file.

**Resolution Framework:**

| Scenario | Action | Rationale |
|----------|--------|-----------|
| Internal modules with inline types | `allowedUntypedLibraries` in config | Inline types are sufficient; stubs are redundant |
| Third-party library without types | Keep warning or add stubs | Signals missing type safety |
| C extension | Add stubs or use `allowedUntypedLibraries` | C code can't have inline types |

**Configuration:**
```json
{
  "allowedUntypedLibraries": ["my_internal_package"]
}
```

**Why `allowedUntypedLibraries` over `reportMissingTypeStubs = false`:**
- Precise: Only suppresss for specified packages
- Explicit: Documents which packages are intentionally untyped
- Future-proof: Third-party libraries still checked

---

### `reportCallInDefaultInitializer`

**What it means:** Function call or mutable object in parameter default.

**Resolution Framework:**

| Scenario | Action |
|----------|--------|
| Typer CLI patterns (`Argument`, `Option`) | Line-level suppression with comment |
| Mutable defaults (actual bug) | Fix: use `None` and check inside function |
| Intentional callable defaults | Line-level suppression with comment |

**Line-level suppression pattern:**
```python
def command(
    arg: str = typer.Argument(...),  # pyright: ignore[reportCallInDefaultInitializer]
) -> None:
    ...
```

**Note:** Pyright does NOT support file-level comment suppressions — only line-level or config-level.

---

### `reportImplicitStringConcatenation`

**What it means:** Two string literals adjacent without explicit concatenation.

**Resolution:** Always fix. Make concatenation explicit with f-strings or `+`.

**Why fix instead of suppress:**
- Implicit concatenation is a readability hazard
- Can mask bugs (missing comma in list)
- Easy to fix

---

## Ruff Diagnostics

### N803 — Argument Name Should Be Lowercase

**Resolution Framework:**

| Scenario | Action |
|----------|--------|
| Internal API | Fix: rename to snake_case |
| External protocol (IPC, API) | File-level suppression with comment |
| Matching third-party library API | File-level suppression with comment |

**File-level suppression pattern:**
```python
# ruff: noqa: N803
# Reason: Argument names match IPC protocol conventions (camelCase).
# Renaming would break API consistency with the protocol specification.
```

---

### D107/D102 — Missing Docstrings

**Resolution Framework:**

| Choice | When to use |
|--------|-------------|
| Add docstrings | Public API, complex behavior, needs documentation |
| Disable rules | Internal code where docstrings add noise, `__init__` is trivial |

**Configuration:**
```toml
[tool.ruff.lint]
ignore = ["D107", "D102"]
```

---

## Suppression Scope Hierarchy

From [common development patterns](rules/common/development-patterns.md):

1. **Fix the code** — Preferred, addresses the actual issue
2. **Line-level suppression** — Single instance, document why
3. **File-level suppression** — Pattern in one file (ruff only), document why
4. **Targeted config** — Category-level (e.g., `allowedUntypedLibraries`)
5. **Project-level disable** — Last resort
6. **Disable rule globally** — Never

## Category-Level Thinking

When a diagnostic appears 50+ times for the same category:
- **Don't add 50+ line suppressions** — Use targeted config
- **Example:** 150 `reportMissingTypeStubs` for internal modules → one `allowedUntypedLibraries` entry
- **Why:** Signals intent clearly, reduces noise, easier to maintain

## Document Every Suppression

```python
# pyright: ignore[reportCallInDefaultInitializer]
# Reason: Typer CLI uses callable defaults for parameter metadata injection.

# ruff: noqa: N803
# Reason: Names match external API contract (camelCase required by protocol).
```
