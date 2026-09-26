## Talking Style

Sacrifice the grammar for the sake of concision.

## Test Placement Convention

All tests MUST be placed in the project root `tests/` directory, never inside skill or feature directories.

- **Anti-Pattern:** Placing tests alongside source code in `skills/<name>/tests/` or `features/<name>/tests/`. This fragments test discovery, complicates CI configuration, and duplicates conftest.py files.
- **LSZ Pattern:** All tests live under `tests/` at project root. Test directory names MUST exactly match their corresponding skill directory names:

  ```
  tests/
  ├── conftest.py              # Shared fixtures for all tests
  ├── continuous-learning/     # Tests for skills/continuous-learning
  ├── docs-scraper/            # Tests for skills/docs-scraper
  ├── skill-comply/            # Tests for skills/skill-comply
  └── skill-stocktake/         # Tests for skills/skill-stocktake
  ```

- **Naming rule:** `tests/<name>/` must correspond to `skills/<name>/`. No exceptions.
- **Test file naming:** Within `tests/<skill>/`, individual test files follow `test_<component>.py` (e.g., `test_render.py`, `test_validate_flavor.py`, `test_contract.py`). Shared fixtures live in `conftest.py` at the skill test directory level. This convention is NOT yet enforced — see the gap note below.
- **Known gap:** The individual test file naming convention (`test_<component>.py`) is observed but not enforced by any tooling. New test files should follow it by convention.
- **Path resolution:** Test conftest.py files must add the source directory to `sys.path` for imports. Use `Path(__file__).parent.parent.parent / "skills" / "<skill-name>" / "scripts"` pattern.
- **Known gap:** Individual test files still duplicate the `sys.path.insert()` boilerplate from conftest.py at module level (e.g., `test_validate_flavor.py`, `tests/docs-scraper/test_skillsh.py`). This is needed at *runtime* because conftest.py's `sys.path` manipulation happens at fixture definition time, which is after module-level imports in test files are resolved. Static analysis no longer depends on the duplication: `pyrightconfig.json` `executionEnvironments` restate the same roots for basedpyright (issue #121 follow-up). The correct fix remains moving the source module(s) into a proper package structure under the skill directory so imports resolve naturally; until then, each test file independently manages its own runtime import path.
- **Benefits:** Single `pytest` command runs all tests. Shared fixtures are discoverable. No duplicate test infrastructure.

## Agent skills

### Harness exposure model

This repo is the harness project. Skills are authored under `skills/<name>/` and exposed externally via symlinks under `~/.agents/skills/<name>`.
Downstream projects consuming skills never have `skills/` or `skills/herdr/SKILL.md` at their repo root. They discover and invoke skills from `~/.agents/skills/<name>/`.

### Multi-agent contract

When running under Herdr (`HERDR_ENV=1`), caller and callee MUST notice the `herdr` skill (`~/.agents/skills/herdr/SKILL.md`, or `skills/herdr/SKILL.md` in this harness) and use communication scripts in `~/.agents/skills/herdr/scripts/` (or `skills/herdr/scripts/` in this harness), NEVER raw `herdr` CLI directly (`herdr agent prompt`), or caller context and reply contracts drop:
- **Caller dispatch:** Dispatch tasks with `uv run ~/.agents/skills/herdr/scripts/herdr_dispatch.py <worker> --file <ticket>` (or `herdr_prompt.py`; in harness: `skills/herdr/scripts/...`). Injects `Caller:`, Herdr skill notice, sibling worker addresses, and reply contract.
- **Callee reply:** Terminate task by running caller's reply command (`uv run ~/.agents/skills/herdr/scripts/herdr_reply.py <caller> "<STATUS> <artifacts> <issues>"`).

### Issue tracker

Issues live as GitHub issues. Use `gh` CLI for all operations. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: `CONTEXT.md` + `docs/adr/` at repo root. See `docs/agents/domain.md`.

### Contribution

Conventional commits & changelog: see CONTRIBUTING.md
The changelog ledger is gated in CI (`changelog-check.yml`): every entry names the PR that landed it, and the release job retires the migration baseline.

### Runtime

Python: uv + .python-version (3.14), run via uv run; see pyproject.toml

```

```
