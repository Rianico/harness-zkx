## Talking Style
Sacrifice the grammar for the sake of concision.

## Test Placement Convention
All tests MUST be placed in the project root `tests/` directory, never inside skill or feature directories.

* **Anti-Pattern:** Placing tests alongside source code in `skills/<name>/tests/` or `features/<name>/tests/`. This fragments test discovery, complicates CI configuration, and duplicates conftest.py files.
* **LSZ Pattern:** All tests live under `tests/` at project root. Test directory names MUST exactly match their corresponding skill directory names:
  ```
  tests/
  ├── conftest.py              # Shared fixtures for all tests
  ├── continuous-learning/     # Tests for skills/continuous-learning
  ├── docs-scraper/            # Tests for skills/docs-scraper
  ├── skill-comply/            # Tests for skills/skill-comply
  ├── skill-stocktake/         # Tests for skills/skill-stocktake
  └── test_hook_install_smoke.py
  ```
* **Naming rule:** `tests/<name>/` must correspond to `skills/<name>/`. No exceptions.
* **Test file naming:** Within `tests/<skill>/`, individual test files follow `test_<component>.py` (e.g., `test_render.py`, `test_validate_flavor.py`, `test_contract.py`). Shared fixtures live in `conftest.py` at the skill test directory level. This convention is NOT yet enforced — see the gap note below.
* **Known gap:** The individual test file naming convention (`test_<component>.py`) is observed but not enforced by any tooling. New test files should follow it by convention.
* **Path resolution:** Test conftest.py files must add the source directory to `sys.path` for imports. Use `Path(__file__).parent.parent.parent / "skills" / "<skill-name>" / "scripts"` pattern.
* **Known gap:** Individual test files currently duplicate the `sys.path.insert()` boilerplate from conftest.py at module level (e.g., `test_validate_flavor.py`, `test_contract.py`). This is needed because conftest.py's `sys.path` manipulation happens at fixture definition time, which is after module-level imports in test files are resolved. The correct fix is to move the source module(s) into a proper package structure under the skill directory so imports resolve naturally, eliminating the conftest dependency. Until then, the duplication is accepted but flagged — each test file independently manages its own import path.
* **Benefits:** Single `pytest` command runs all tests. Shared fixtures are discoverable. No duplicate test infrastructure.

## Agent skills

### Issue tracker

Issues live as GitHub issues. Use `gh` CLI for all operations. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: `CONTEXT.md` + `docs/adr/` at repo root. See `docs/agents/domain.md`.

### Contribution
Conventional commits & changelog: see CONTRIBUTING.md

### Runtime
Python: uv + .python-version (3.14), run via uv run; see pyproject.toml
