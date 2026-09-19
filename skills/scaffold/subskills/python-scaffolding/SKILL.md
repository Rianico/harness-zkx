---
name: python-scaffolding
description: >-
  Python project scaffolding with uv, .python-version, pyproject, and verification wiring. Use when initializing or retrofitting a Python repo or selecting its toolchain.
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

Source of truth is `$SKILL_DIR/scripts/scaffold.py` (`build_pyproject` — computed, `PYTHON_VERSION`, `_py_module_name`) plus the rendered `templates/python/src/_pkg/__init__.py.j2` and `templates/python/tests/test_smoke.py.j2`, `$SKILL_DIR/templates/shared/CONTRIBUTING.python.md.j2` (rendered) — run `uv run $SKILL_DIR/scripts/scaffold.py --flavor python --dry-run` to preview.

> Existing repo? `--update` refreshes generated files but preserves `pyproject.toml` (project manifest); work the printed NEXT list. Per-field edits (confirm value with user first): `scaffold.py ensure py-dep --req "<pep508>"` / `ensure coverage-threshold --flavor python --value N` — see `git-scaffolding/SKILL.md` § Update.

```bash
uv run $SKILL_DIR/scripts/scaffold.py --flavor python --project-name <name>
uv run $SKILL_DIR/scripts/scaffold.py --flavor python --project-name <name> --dry-run
```

Pure-deterministic: `.python-version` (`3.14`), `src/<module>/__init__.py` (rendered — the covered package, so `--with-coverage` measures code instead of failing at 0%; `pythonpath = ["src"]` in `pyproject.toml` is what makes it importable), `tests/test_smoke.py` (rendered — the `verify` job's `uv run pytest` has nothing to collect without it), `.gitignore` dedup additions (shared `GITIGNORE_GIT` + `__pycache__/.venv`).

Project-owned: `src/<module>/__init__.py` and `tests/test_smoke.py` are starting points the project replaces, so `--update` preserves them (see `SOURCE_OWNED` + `SOURCE_OWNED_PATTERNS` — the package path carries a computed directory name).

Mixed (script warns → proofread): `pyproject.toml` (`{{project_name}}`, description/readme), `AGENTS.md` `### Runtime` pointer (keeps existing 3 sections). Script emits `WARNING: ... proofread package name` on stderr.

### ensure py-dep input surface (declared)

Supported: a `[project]` table whose `dependencies` key is an inline array or a multiline array, with or without a trailing comma, with either TOML string quote. New entries are appended to that array; an entry whose distribution name is already present, under either quote, is reported unchanged with exit 0.

Refused without mutating the file: no `[project]` table, no `dependencies` key inside it, a `dependencies` key belonging to any other table including an array of tables, or an input the scanner cannot prove is `[project].dependencies`.

Every refusal exits non-zero, leaves the file byte-identical, and names what was found rather than what to re-run. Anything outside this list is out of contract by construction.

Byte view: `uv run $SKILL_DIR/scripts/scaffold.py --flavor python --dry-run` (tool owns bytes).

## Steps — Tool Owns Determinism

1. Generate: `uv run $SKILL_DIR/scripts/scaffold.py --flavor python --project-name <name>` (handles `--cwd`, infers name, normalizes, warns on mixed).
2. Install: `uv sync --group dev` (pins `uv.lock`; `basedpyright` over `mypy` per `$SKILL_DIR/../basedpyright-expert/SKILL.md`).
3. Proofread mixed warnings: `pyproject.toml` name/description, `AGENTS.md` 3-section preservation.
4. Wire verification: `ruff check`, `ruff format --check`, `basedpyright`, `pytest` via `uv run`.
5. Verify: `uv run $SKILL_DIR/scripts/scaffold.py --flavor python --dry-run` + `uv sync && uv run ruff check . && uv run ruff format --check . && uv run basedpyright && uv run pytest`

> [!tip] Verification — before every push/PR
>
> - `uv run ruff check . && uv run ruff format --check . && uv run basedpyright && uv run pytest` — if any fails → `BLOCKED`
> - Clean-build after `pyproject.toml` change; restart daemon after type-config change; clear test cache when stale

## Verification Split

- Deterministic: `ruff check`/`ruff format --check`, `basedpyright`/`ty`, `pytest` — env truth is `uv run ...` exit code.
- `pyproject.toml` names its lint selection (`select = ["E", "F", "I", "UP", "B"]`, `ignore = ["E501"]`) because ruff's default is the tool's opinion — 413 rules in 0.16.7 and growing, which reds a generated repo on a lockfile bump nobody reviews; line length stays the formatter's call.
- Semantic: API naming, module boundaries — verify via reviewer, not compiler.

## Grilling Selection

If Dialog 2 selected Tests and Dialog 3 selected 80%/90%/Other, add `--with-coverage --coverage-threshold <80|90|custom>` to the generator. Example: `uv run $SKILL_DIR/scripts/scaffold.py --flavor python --with-coverage --coverage-threshold 80 --project-name <name>`. Without Tests or with No coverage, omit the flag — `pyproject.toml` omits `pytest-cov` and `[tool.coverage.*]` and CI runs `uv run pytest` without `--cov`. `fail_under` is meaningful because the flavor ships a covered package: `tests/scaffold/test_flavor_gates.py` runs the wired `pytest --cov --cov-fail-under`.

## Relation to Other Subskills

- Git contract stays canonical: do not duplicate `CONTRIBUTING.md` / `.releaserc.json` here; cross-reference `$SKILL_DIR/subskills/git-scaffolding/SKILL.md`.
- CI wiring belongs to `$SKILL_DIR/subskills/ci-scaffolding/SKILL.md`; Python CI job runs `uv run pytest` inside the shared verify gate.
