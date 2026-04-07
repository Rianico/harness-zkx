---
name: python-expert
description: Expert in the modern Python ecosystem (uv, ruff, pydantic, FastAPI) and advanced paradigms. Use PROACTIVELY for Python development, async concurrency optimization, testing strategies, and architectural decisions.
argument-hint: "[async|fastapi|testing|django|pytorch]"
---

# Python Expert Skill

You have invoked the Python Expert Skill. This consolidates the most critical, opinionated workflows for modern Python 3.12+ development, prioritizing high-performance and safety.

## 1. Async & Concurrency (FastAPI & I/O)
- **Non-blocking:** Never put blocking I/O (like `requests` or synchronous DB calls) inside an `async def` function. It blocks the entire event loop. Use `httpx` for async HTTP, or run blocking code in a threadpool (`run_in_executor`).
- **Context Variables:** Use `contextvars` instead of `threading.local()` for state management in async applications.
- **FastAPI Injection:** Heavily utilize FastAPI's `Depends()` for dependency injection to keep route handlers clean and testable.
- **Data Validation:** Use `pydantic` V2 for all data validation. Avoid hand-rolled validation logic.

## 2. Testing & Verification
- **Framework:** Always default to `pytest`. Do not use `unittest`.
- **Fixtures:** Use `pytest` fixtures for setup/teardown. Avoid class-based `setUp`/`tearDown`.
- **Async Testing:** Use `pytest-asyncio` for testing async functions.
- **Mocks:** Keep `unittest.mock` to a minimum. Prefer testing against local containerized dependencies (e.g., test databases) or using responses/VCR for HTTP.

## 3. Django Architecture
- **Fat Models, Skinny Views:** Push business logic down to the model or service layer. Views should only handle HTTP routing and permissions.
- **ORM Optimization:** Always audit querysets for N+1 issues. Proactively use `select_related()` for foreign keys and `prefetch_related()` for many-to-many/reverse relations.
- **Serialization:** Use Django Rest Framework (DRF) serializers for all API I/O.

## 4. PyTorch & Data Science
- **Device Agnosticism:** Write code that dynamically assigns devices (e.g., `device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')`).
- **Memory Management:** Remember to `optimizer.zero_grad()` before backprop. Use `torch.no_grad()` or `torch.inference_mode()` for evaluation to save memory.
- **Reproducibility:** Always set random seeds across all libraries (`torch`, `numpy`, `random`) for reproducible experiments.

## Instructions for the Agent
1. Apply the checklists above based on the context of the user's codebase (e.g., if you see FastAPI, apply the Async & Concurrency rules).
2. Write code assuming modern tooling is in place (`uv` for package management, `ruff` for formatting/linting).
3. If the task is simple, execute the implementation immediately.
4. For highly complex architectural setups, use the `Read` tool to fetch any extended reference documents in `skills/python-expert/references/` if they exist.