---
paths:
  - "pyproject.toml"
  - "requirements.txt"
  - "setup.py"
  - "**/*.py"
---

# Python Rules

Baseline behavior, style preferences, and lib selection for everyday Python development.

## Core Standards

- **Formatting:** PEP 8, `snake_case` for variables/functions, `CamelCase` for classes
- **Typing:** Type hints on all function signatures
- **Class state:** Annotate instance attributes in `__init__` unless the class is `@final`
- **Module APIs:** Do not import private helpers across modules; make cross-module helpers public
- **Immutability:** Never use mutable defaults (`def func(x=[]):` → BAD)
- **Imports:** Standard Library → Third Party → Local

## Type Safety (First Principle)

- **Fix over suppress:** Address real issues whenever possible; suppress only when pattern is intentional
- **Most precise scope:** Line-level > file-level > targeted config > project-level (follow Scoped Over Global in common rules)
- **Document suppressions:** Every suppression includes a comment explaining why
- **Unused parameters:** `_param` prefix convention
- **Unused call results:** Assign to `_` when intentionally discarding a meaningful return value
- **`hasattr()`/`getattr()` weaken types:** Prefer `Protocol` + `isinstance` or explicit dispatch
- **Dict narrowing:** After `isinstance(x, dict)`, cast/narrow to `dict[str, object]` before passing onward
- **Keep typed models:** Access `model.field` directly; call `model_dump()` only at output boundaries
- **`object` over `Any`:** `object` forces validation; `Any` silently propagates
- **Validate at boundaries:** External data → `object` → Pydantic → typed model; internal code trusts types
- **Concrete normalizers:** Response normalizers return concrete domain types, not `object`
- **Trace unknown types:** Never assume diagnostic is "legitimate" — find source, check spec, build model
- **Verification:** Static (basedpyright), LSP (workspace diagnostics), Pattern (`rg "# pyright: "`)

### Diagnostic Resolution Quick Reference

| Diagnostic | Resolution |
|------------|------------|
| `reportMissingTypeStubs` (internal) | `allowedUntypedLibraries` in config |
| `reportCallInDefaultInitializer` (Typer) | Line-level suppression |
| `reportImplicitStringConcatenation` | Fix code (use f-string or `+`) |
| `reportPrivateUsage` | Rename helper public or move ownership boundary |
| `reportUnannotatedClassAttribute` | Add explicit instance attribute annotations |
| `reportUnknownArgumentType` | Narrow/cast at the boundary before calling typed helpers |
| `reportUnusedCallResult` | Assign to `_` or use the result |
| `reportReturnType` from `object` | Strengthen helper return type and remove ignore |
| N803 (protocol names) | File-level suppression with comment |
| D107/D102 (trivial docstrings) | Disable rules or add docstrings |

**For complex diagnostics:** Invoke `python-expert` skill with `typing` argument.

## Code Quality

- Add type hints for all signatures and complex variables
- Prioritize readability and explicit error handling
- Favor stdlib before adding dependencies
- Profile (`py-spy`, `cProfile`) before optimizing

## Performance & Concurrency

- **I/O bound:** `asyncio` or async frameworks
- **CPU bound:** `concurrent.futures` or `multiprocessing`
- **Caching:** `functools.lru_cache` or `cache` for expensive deterministic functions

## Web & API

- **Framework:** FastAPI for new APIs
- **Validation:** Pydantic V2
- **Database:** SQLAlchemy 2.0 async, or modern async ORMs

## Terminal Output

- **Library:** `rich` for formatted output
- **Tables:** `HORIZONTALS` with `show_lines=True` for data; `ROUNDED` for summaries
- **Columns:** `no_wrap=True` on non-content columns
- **Width:** Pass `width` parameter in subprocesses without terminal

## Data & ML

- **Data processing:** Polars (preferred) or Pandas 2.0+
- **Deep learning:** PyTorch
- **Classical ML:** scikit-learn

## Expertise Routing

For complex patterns and domain gotchas, invoke the expert skill:

```
Skill(skill="python-expert", args="[async|fastapi|testing|django|pytorch|typing]")
```

**When to invoke:**
- Complex async/concurrency patterns
- Framework-specific architecture (Django, FastAPI)
- Testing strategy beyond basics
- PyTorch performance and memory patterns
- Type boundaries, Any/object containment, IPC generic types
