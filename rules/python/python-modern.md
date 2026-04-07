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
- **Use `pyright` / `mypy`**: Use for static type checking.

## 2. Project Configuration
- Default to `pyproject.toml` for all project and tool configurations.
- Avoid legacy `setup.py` unless explicitly required by existing project constraints.

## 3. Language Features
- Use modern Python 3.12+ features (e.g., structural pattern matching `match/case`, modern type parameter syntax).
- Use built-in generic types (`list[str]`, `dict[str, int]`, `str | None`) instead of importing from `typing` (`List`, `Dict`, `Union`, `Optional`).
- Leverage `async`/`await` patterns for I/O-bound operations.
- Prefer `dataclasses` or `pydantic` for data structures and validation.

## 4. Code Quality
- Add comprehensive type hints for all function signatures and complex variables.
- Prioritize code readability, immutability where sensible, and explicit error handling over silent failures.
- Favor standard library solutions before adding external dependencies.

## 5. Performance & Concurrency
- **I/O Bound**: Always default to `asyncio` (or async frameworks) for I/O bound operations.
- **CPU Bound**: Use `concurrent.futures` or `multiprocessing` for heavy CPU-bound tasks to bypass the GIL.
- **Optimization**: Use built-in `functools.lru_cache` or `cache` for expensive deterministic functions. Profile with `py-spy` or `cProfile` before optimizing.

## 6. Web Development & APIs
- **Frameworks**: Default to `FastAPI` for new APIs and microservices.
- **Validation**: Use `Pydantic` (V2) for data validation, serialization, and settings management.
- **Database**: Prefer `SQLAlchemy 2.0` using its async features, or modern async ORMs.

## 7. Data & Machine Learning
- **Data Processing**: Consider `Polars` for high-performance data manipulation, or modern `Pandas` 2.0+.
- **Notebooks**: When working with Jupyter notebooks, manage dependencies and execution through `uv` to ensure isolated environments.
- **ML Stack**: Default to `PyTorch` for deep learning and `scikit-learn` for classical ML workflows.