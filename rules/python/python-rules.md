---
paths:
  - 'pyproject.toml'
  - 'requirements.txt'
  - 'setup.py'
  - '**/*.py'
---

# Python Rules

You are operating in a Python codebase. Before proceeding, review and apply these rules.

## Core Python Standards

- **Tooling:** `uv` for all Python workflows (`uv run`, `uv add`, `uv sync`; never call `python`, `pip`, or `venv` directly).
  - Standalone scripts: use PEP 723 inline script metadata (`# /// script`) and execute with `uv run script.py`.
  - Format & lint: `ruff` (target Python 3.12+, 120 line length; replaces black, isort, flake8).
  - Type checking: `basedpyright` as default LSP and type checker. If diagnostics contradict edited files, reload the language server.
  - Testing: `uv run pytest -q` (quiet by default).
  - Project config: default to `pyproject.toml`; avoid legacy `setup.py`.
- **Formatting & Style:** PEP 8 — `snake_case` functions/variables, `PascalCase` classes, `SCREAMING_SNAKE` constants; absolute imports (`stdlib → third-party → local`).
- **Modern Syntax (3.12+):**
  - Built-in generics: `list[str]`, `dict[str, int]`, `str | None` (never legacy `List`, `Dict`, `Optional`, `Union`).
  - PEP 695 type parameter syntax: `class Repository[T: BaseModel]:`, `def get[T](id: str) -> T | None:`.
  - Structural pattern matching: `match/case`.
- **Typed Boundaries (Pydantic-First):**
  - Admission boundary validates external `object` via `BaseModel.model_validate` into typed `model.field`.
  - Serialize via `model_dump()` strictly at transport/IPC/file boundaries, never internally.
  - `object` forces validation; `Any` silences checkers — prefer `object` at untrusted boundaries.
  - Use `Pydantic BaseModel` for domain models and boundary validation; use `dataclasses` only for unvalidated internal data holders.

## Critical Cruxes

- **No Mutable Defaults:** Never use mutable defaults (`def f(x=[])` is prohibited). Use `None` sentinel (`x: list[T] | None = None`) with runtime instantiation in functions, or `Field(default_factory=list)` in Pydantic models.
- **Structured Concurrency over `gather`:** Prefer `asyncio.TaskGroup` (Python 3.11+) over `asyncio.gather`. In `asyncio.gather`, when one task raises an exception, remaining tasks leak and continue running in the background as unmonitored orphans. `TaskGroup` guarantees sibling cancellation and awaits all tasks on failure.
- **Never Block the Event Loop:** Never invoke synchronous database queries (`psycopg2`, sync SQLAlchemy, `sqlite3`), `requests`, or `time.sleep` in `async def` routes. A single blocking call stalls the entire process. Use async-native drivers (`asyncpg`, `httpx.AsyncClient`) or offload blocking work via `await asyncio.to_thread(...)`.
- **Exception Chaining:** Always preserve causal error chains when transforming exceptions in `except` blocks: `raise BadRequestError(str(e)) from e`. Never swallow the original traceback without `from e` or `from None` (intentional suppression).
- **Late-Binding Closures in Loops:** Avoid creating closures in loops like `[lambda: i for i in range(5)]`, which resolve variables at call time. Bind arguments eagerly at definition time using `lambda i=i:` or `functools.partial`.
- **Type Checker Discipline:** Fix over suppress. When suppression is strictly necessary, use the narrowest scope with `# pyright: ignore[rule]` and document the reason.

## Expertise Routing (Use `Read` tool)

When deep methodology or architectural patterns are needed, use the `Read` tool to inspect `skills/programming-expert/subskills/python-expert/SKILL.md` and related reference documents:

- **Type safety & boundaries:** Read §1 Type Safety and `references/type-safety-pydantic.md` (generics, `Protocol`, `TypeAlias`, strict mode, `object` vs `Any`).
- **Async & concurrency:** Read §3 Async and `references/async-patterns.md` (`TaskGroup`, `asyncio.to_thread`, avoiding loop blocking, cancellation safety).
- **Background jobs & task queues:** Read §4 Background Jobs and `references/background-jobs.md` (job state machines, Celery config, idempotency).
- **Resource management:** Read §5 Resources and `references/resource-management.md` (`AsyncExitStack`, context managers, streaming cleanup).
- **Errors & resilience:** Read §6 Errors & Resilience, `references/error-handling.md`, and `references/resilience.md` (custom errors, tenacity retries, jitter).
- **Testing strategy:** Read §8 Testing and `references/testing-patterns.md` (fixtures, containers over mocks, coverage).
- **Type checker diagnostics:** Read `skills/programming-expert/subskills/basedpyright-expert/SKILL.md` for `basedpyright`/`pyright` configuration and suppression ladders.
