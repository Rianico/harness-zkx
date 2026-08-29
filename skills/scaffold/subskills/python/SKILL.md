---
name: python
description: >-
  Python project scaffolding with uv, .python-version, pyproject, and verification wiring. Use when initializing or retrofitting a Python repo or selecting its toolchain. TRIGGER: python scaffold, uv, pyproject, pytest
metadata:
  managed-by: scaffold
---

# Python Scaffold

Projection of the scaffold spine onto Python. Declared runtime is `uv` + `.python-version`; verification closes the loop via deterministic gates.

## Declared Runtime

Per `development-patterns.md` §3:

- Single-runtime Python: `uv` owns version + deps; commit `.python-version` (default `3.14`) and `pyproject.toml` + `uv.lock`.
- Multi-runtime (Python + Node/Rust): `asdf` + `.tool-versions`; `asdf install` syncs all; `uv` still owns Python deps.

## Deterministic Artifacts — Tool Owns Bytes

Source of truth is `$SKILL_DIR/scripts/scaffold.py` (embedded `PYPROJECT_TOML_TMPL`, `PYTHON_VERSION`) — run `uv run $SKILL_DIR/scripts/scaffold.py --flavor python --dry-run` to preview.

```bash
uv run $SKILL_DIR/scripts/scaffold.py --flavor python --project-name <name>
uv run $SKILL_DIR/scripts/scaffold.py --flavor python --project-name <name> --dry-run
```

Pure-deterministic: `.python-version` (`3.14`), `.gitignore` dedup additions (shared `GITIGNORE_GIT` + `__pycache__/.venv`).

Mixed (script warns → proofread): `pyproject.toml` (`{{project_name}}`, description/readme), `AGENTS.md` `### Runtime` pointer (keeps existing 3 sections). Script emits `WARNING: ... proofread package name` on stderr.

Byte view: `uv run $SKILL_DIR/scripts/scaffold.py --flavor python --dry-run` (tool owns bytes).

## Steps — Tool Owns Determinism

1. Generate: `uv run $SKILL_DIR/scripts/scaffold.py --flavor python --project-name <name>` (handles `--cwd`, infers name, normalizes, warns on mixed).
2. Install: `uv sync --group dev` (pins `uv.lock`; `basedpyright` over `mypy` per `$SKILL_DIR/../basedpyright-expert/SKILL.md`).
3. Proofread mixed warnings: `pyproject.toml` name/description, `AGENTS.md` 3-section preservation.
4. Wire verification: `pytest`, `ruff check`, `basedpyright` via `uv run`.
5. Verify: `uv run $SKILL_DIR/scripts/scaffold.py --flavor python --dry-run` + `uv sync && uv run ruff check . && uv run basedpyright && uv run pytest`

> [!tip] Verification — before every push/PR
>
> - `uv run ruff check . && uv run basedpyright && uv run pytest` — if any fails → `BLOCKED`
> - Clean-build after `pyproject.toml` change; restart daemon after type-config change; clear test cache when stale

## Verification Split

- Deterministic: `ruff`, `basedpyright`/`ty`, `pytest` — env truth is `uv run ...` exit code.
- Semantic: API naming, module boundaries — verify via reviewer, not compiler.

## Grilling Selection

If Dialog 2 selected Tests and Dialog 3 selected 80%/90%/Other, add `--with-coverage --coverage-threshold <80|90|custom>` to the generator. Example: `uv run $SKILL_DIR/scripts/scaffold.py --flavor python --with-coverage --coverage-threshold 80 --project-name <name>`. Without Tests or with No coverage, omit the flag — `pyproject.toml` omits `pytest-cov` and `[tool.coverage.*]` and CI runs `uv run pytest` without `--cov`.

## Relation to Other Subskills

- Git contract stays canonical: do not duplicate `CONTRIBUTING.md` / `.releaserc.json` here; cross-reference `$SKILL_DIR/subskills/git/SKILL.md`.
- CI wiring belongs to `$SKILL_DIR/subskills/ci/SKILL.md`; Python CI job runs `uv run pytest` inside the shared verify gate.
