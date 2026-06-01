---
paths:
  - "pyproject.toml"
  - "requirements.txt"
  - "setup.py"
  - "**/*.py"
---

# Modern Python Tooling & Syntax

Modern Python 3.12+ environment setup and language features.

## Tooling (CRITICAL)

- **`uv`**: ALWAYS use instead of `python`, `pip`, `venv`
  - Run scripts: `uv run script.py`
  - Add dependencies: `uv add <pkg>`
  - Install: `uv pip install <pkg>`
- **`ruff`**: Formatting and linting (replaces black, isort, flake8)
- **`basedpyright`**: Default LSP and type checker. Fallback to `mypy` only when unavailable.
- **LSP freshness**: If diagnostics contradict edited files, restart/reload the language server before judging results.
- **`pytest`**: Run with `uv run pytest -q` (quiet by default, verbose only when needed)

## Project Configuration

- Default to `pyproject.toml` for all configurations
- Avoid legacy `setup.py` unless constrained by existing project

## Language Features (3.12+)

- Structural pattern matching: `match/case`
- Built-in generics: `list[str]`, `dict[str, int]`, `str | None` (NOT `List`, `Dict`, `Union`, `Optional`)
- Type parameter syntax: `def func[T](x: T) -> T:`
- `dataclasses` or `pydantic` for data structures

## Inline Script Metadata

For standalone scripts, use inline metadata:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich>=13.0.0"]
# ///
```

Run with `uv run script.py` — dependencies auto-installed.
