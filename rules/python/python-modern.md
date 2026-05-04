---
paths:
  - "pyproject.toml"
  - "requirements.txt"
  - "setup.py"
  - "**/*.py"
---

# Modern Python Development Rules

You are working in a modern Python 3.12+ environment. Adhere strictly to the following tools and practices:

## 1. Tooling (CRITICAL)
- **Use `uv`**: ALWAYS use `uv` instead of `python`, `python3`, `pip`, `venv`, or `pip3` for running scripts and managing dependencies.
  - Run scripts: `uv run script.py` (NOT `python script.py`)
  - Install dependencies: `uv pip install <pkg>` or `uv add <pkg>`
  - Manage environments: Let `uv` handle virtual environments.
- **Use `ruff`**: Use `ruff` for all formatting and linting (replaces `black`, `isort`, `flake8`).
- **Use `basedpyright`**: Default LSP server and type checker (displaces pyright). Use `mypy` only when basedpyright is unavailable.

## 2. Project Configuration
- Default to `pyproject.toml` for all project and tool configurations.
- Avoid legacy `setup.py` unless explicitly required by existing project constraints.

## 3. Language Features
- Use modern Python 3.12+ features (e.g., structural pattern matching `match/case`, modern type parameter syntax).
- Use built-in generic types (`list[str]`, `dict[str, int]`, `str | None`) instead of importing from `typing` (`List`, `Dict`, `Union`, `Optional`).
- Leverage `async`/`await` patterns for I/O-bound operations.
- Prefer `dataclasses` or `pydantic` for data structures and validation.

## 4. Type Safety (basedpyright/mypy strict)
- **File-Level Suppressions Over Global:** Use `# pyright: reportX=false` at file top, NEVER disable in pyrightconfig.json.
- **Container Annotations Before Iteration:** Annotate containers before `.items()`, `.values()` to help type inference.
- **Pydantic model_validate:** Use `Model.model_validate(response)` for runtime validation of JSON/dict data.
- **dict[str, object] Limitation:** `object` lacks `.get()` - use `dict[str, Any]` with suppression or Pydantic for truly dynamic data.
- **Acceptable Warnings:** `reportUnusedCallResult`, `reportImplicitStringConcatenation`, `reportUnusedParameter` are often acceptable style choices, not type safety issues.

## 5. Code Quality
- Add comprehensive type hints for all function signatures and complex variables.
- Prioritize code readability, immutability where sensible, and explicit error handling over silent failures.
- Favor standard library solutions before adding external dependencies.

## 6. Performance & Concurrency
- **I/O Bound**: Always default to `asyncio` (or async frameworks) for I/O bound operations.
- **CPU Bound**: Use `concurrent.futures` or `multiprocessing` for heavy CPU-bound tasks to bypass the GIL.
- **Optimization**: Use built-in `functools.lru_cache` or `cache` for expensive deterministic functions. Profile with `py-spy` or `cProfile` before optimizing.

## 7. Web Development & APIs
- **Frameworks**: Default to `FastAPI` for new APIs and microservices.
- **Validation**: Use `Pydantic` (V2) for data validation, serialization, and settings management.
- **Database**: Prefer `SQLAlchemy 2.0` using its async features, or modern async ORMs.

## 8. Terminal Output (Rich)
- **Library:** Use `rich` for all terminal formatted output. Add to `dependencies` in script frontmatter.
- **Box Style:** `HORIZONTALS` with `show_lines=True` for data tables (row separators, no vertical borders); `ROUNDED` for small summary tables.
- **Columns:** Default `no_wrap=True` on non-content columns. Let content columns wrap naturally by omitting `no_wrap`.
- **Width:** Rich auto-detects terminal width. In subprocesses without width (e.g., Claude Code hooks), pass `width` parameter or `--width` CLI flag.

## 9. Data & Machine Learning
- **Data Processing**: Consider `Polars` for high-performance data manipulation, or modern `Pandas` 2.0+.
- **Notebooks**: When working with Jupyter notebooks, manage dependencies and execution through `uv` to ensure isolated environments.
- **ML Stack**: Default to `PyTorch` for deep learning and `scikit-learn` for classical ML workflows.
