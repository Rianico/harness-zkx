---
name: python-expert
description: Python domain expertise for Python 3.12+, uv, ruff, pydantic, FastAPI, Django, pytest, pytest-asyncio, async I/O, contextvars, PyTorch, data science workflows, testing strategy, and architecture review. Use for Python implementation, debugging, testing, concurrency fixes, framework work, and refactoring tasks.
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
- **Framework:** Always default to `pytest`. Do not use `unittest`. When running through `uv`, prefer `uv run pytest -q` rather than `uv run pytest -v` unless verbose output is explicitly needed.
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

## 5. Type Checking & LSP
- **Default LSP:** Use `basedpyright` as the primary type checker and LSP server. It is a stricter, more feature-rich fork of pyright with better type inference.
- **Fallback:** Use `mypy` only when basedpyright is unavailable or explicitly required by project constraints.
- **Configuration:** Configure type checking in `pyproject.toml` under `[tool.basedpyright]`.

## 6. Terminal Output (Rich)
- **Library:** Use `rich` for all terminal formatted output. Add `rich` to `dependencies` in script frontmatter.
- **Box Style:** Prefer `HORIZONTALS` with `show_lines=True` for tables with row separators, no vertical column borders.
- **Columns:** Default to `no_wrap=True` on all columns. Let Rich wrap content naturally in cells by omitting `no_wrap` on the content column.
- **Summary Tables:** Use `ROUNDED` box style for small summary/counts tables.
- **Width Detection:** Rich auto-detects terminal width. If subprocess doesn't get width (e.g., in Claude Code), pass `width` parameter or add `--width` CLI flag.
- **Example:**
  ```python
  from rich.box import HORIZONTALS, ROUNDED
  from rich.console import Console
  from rich.table import Table

  console = Console()  # Auto-detect width

  # Summary table with rounded style
  summary = Table(show_header=False, box=ROUNDED)
  summary.add_column("Category", style="bold")
  summary.add_column("Count", justify="right")
  summary.add_row("Keep", "21")
  console.print(summary)

  # Main data table with horizontal separators
  table = Table(title="Results", box=HORIZONTALS, show_lines=True)
  table.add_column("Name", style="cyan", no_wrap=True, width=15)
  table.add_column("Count", justify="right", no_wrap=True, width=5)
  table.add_column("Description", style="dim")  # Let this wrap naturally
  table.add_row("example", "42", "A long description that will wrap...")
  console.print(table)
  ```

## Instructions for the Agent
1. Apply the checklists above based on the context of the user's codebase (e.g., if you see FastAPI, apply the Async & Concurrency rules).
2. Write code assuming modern tooling is in place (`uv` for package management, `ruff` for formatting/linting).
3. For highly complex architectural setups, use the `Read` tool to fetch any extended reference documents in `skills/python-expert/references/` if they exist.