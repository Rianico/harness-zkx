---
paths:
  - 'pyproject.toml'
  - 'requirements.txt'
  - 'setup.py'
  - '**/*.py'
---

# Python Rules

You are operating in a Python codebase. Before proceeding, review and apply these rules.

## Core Python Standards (80% Base)

- **Tooling:** `uv` for all Python (`uv run`, `uv add`, `uv sync`; no `pip`/`venv`). `ruff` for format+lint, `basedpyright` for typecheck, `uv run pytest -q` for tests.
- **Formatting:** PEP 8 — `snake_case` funcs/vars, `CamelCase` classes, `SCREAMING_SNAKE` constants; absolute imports `stdlib → third-party → local`.
- **Typed boundaries:** External `object` → `Pydantic BaseModel.model_validate` → typed `model.field`; `model_dump()` only at transport/IPC/file boundaries. `object` forces validation, `Any` silences — prefer `object`.
- **No mutable defaults** (`def f(x=None):`), no private cross-module imports, annotate instance attrs in `__init__`.

## Type Safety (First Principle)

- **Fix over suppress;** narrowest suppression scope; document every `pyright: ignore` with why.
- **Keep typed models** — `model.field` inside; never `hasattr`/`getattr` or `dict.get` on untyped data; trace `Unknown` to its `object` source.

## Expertise Routing (Use `Skill` tool)

If your task needs deep methodology, you MUST pause and invoke `Skill` for `programming-expert` (`python-expert`):

- **Typing/boundaries:** `Skill(skill="programming-expert", args="python-expert type-safety")` — generics, `Protocol`, `TypeAlias`, strict mode, `Any`/`object` containment.
- **Async/jobs/resources:** `Skill(skill="programming-expert", args="python-expert async")` — never block event loop, `ContextVar`, job state machines.
- **Testing/review:** `Skill(skill="programming-expert", args="python-expert testing")` — fixtures, `freezegun`, coverage.

**CRITICAL:** Do not guess type fixes or retry logic without retrieving the expert skill first.
