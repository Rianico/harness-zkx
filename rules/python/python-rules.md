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
- **Immutability:** Never use mutable defaults (`def func(x=[]):` → BAD)
- **Imports:** Standard Library → Third Party → Local

## Type Safety (First Principle)

- **NO suppressions:** Never use `# pyright: ignore` or `# type: ignore` — fix underlying issues
- **Unused parameters:** `_param` prefix convention
- **File-level suppressions:** Only in designated zones (transport/IPC layers, external lib stubs), NEVER in pyrightconfig.json
- **`getattr()` returns `Any`:** Avoid it; use explicit method dispatch instead
- **Keep typed models:** Access `model.field` directly; call `model_dump()` only at output boundaries
- **`object` over `Any`:** `object` forces validation; `Any` silently propagates
- **Validate at boundaries:** External data → `object` → Pydantic → typed model; internal code trusts types
- **Trace unknown types:** Never assume diagnostic is "legitimate" — find source, check spec, build model
- **Serialization layering:** If `model_dump()` or type narrowing is complex in application layer, move it to transport/IPC boundary
- **Verification:** Static (basedpyright), LSP (workspace diagnostics), Pattern (`rg "# pyright: "`)

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
