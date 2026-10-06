# Repository Instructions

## Talking Style

Plain English: short sentences (≤25 words), active voice, specific verbs, concise bullets. No jargon walls or conversational filler. Keep technical identifiers verbatim.

## AI Engineering Philosophy & Design (`ai-engineering-expert`)

This project implements the methodology in `skills/ai-engineering-expert/SKILL.md`:

- **Goal-Driven Development (GDD)**:
  - **BDD for Intent Alignment**: Bridge the intent-code gap with shared contracts (Given/When/Then).
  - **EDD for Empirical Truth**: Environmental truth is supreme authority. Trust only what the environment (tests, linters, compilers) says, never what the model claims.
- **Deterministic vs. Semantic Split**:
  - Default to building checks over writing rules.
  - Mechanical constraints (syntax, imports, file locations, banned APIs) → deterministic tools (linters, pre-commit, CI).
  - Markdown steering & prompts → reserved strictly for genuine qualitative **judgment calls** verified via adversarial orchestration ("Skeptic" reviewer).
- **Progressive Disclosure & Pointer-First**:
  - `AGENTS.md` is minimal and strictly for **navigation pointers**, never inline specs.
  - Follow the 80/20 rule: 20% in skill/pointer, 80% behind context pointers in `references/` or `docs/`.
  - Prune no-ops: delete instructions that don't measurably change agent behavior.
- **Context Pressure Asymmetry**:
  - **Implementer**: Max context pressure (exploration, drafting, debugging). Keep prompt free of styling/standards overhead.
  - **Reviewer**: Min context pressure (diff only, zero exploration). Place coding standards and qualitative checks here.
- **Subagent-First Execution**:
  - Orchestrator never writes or edits code directly; dispatches to specialized subagents.
  - Exchange state via **file paths/pointers**, not inlined text blobs.

## Navigation & Architecture

- **Skills**: Authored in `skills/<name>/SKILL.md`. Exposed via symlinks under `~/.agents/skills/<name>`.
  - Authoring & Verification: `skills/ai-engineering-expert/SKILL.md`.
  - Session Retros & Audit: `skills/harness-audit/SKILL.md`.
- **Domain & Architecture**:
  - Domain context & ubiquitous language: `CONTEXT.md` (see `docs/agents/domain.md`).
  - Architecture decisions: `docs/adr/` managed via `skills/adr/SKILL.md`.
  - Boundary & state governance: `skills/keel/SKILL.md`.
- **Tests**:
  - Strict placement: all tests live under root `tests/<name>/` matching `skills/<name>/`. Never place tests inside `skills/`.
  - Iterate narrow: `uv run pytest tests/<skill>` (or one file or test id). The full suite takes minutes, so rerun only the package you touched.
  - Land once: `bash scripts/check.sh` before handing off or pushing; add `--skip-tests` for a lint-and-types-only pass.
  - Test naming: `tests/<skill>/test_<component>.py`. Conftest handles runtime `sys.path`.
- **Multi-Agent Contract (Herdr)**:
  - When running under Herdr (`HERDR_ENV=1`), always use harness scripts in `skills/herdr/scripts/` (never raw CLI):
    - Dispatch: `uv run skills/herdr/scripts/herdr_dispatch.py <worker> --file <ticket>`
    - Reply: `uv run skills/herdr/scripts/herdr_reply.py <caller> "<STATUS> <artifacts> <issues>"`
- **Issue Tracker & Triage**:
  - GitHub CLI (`gh`). Vocabulary: `docs/agents/triage-labels.md`. Guide: `docs/agents/issue-tracker.md`.
- **Contribution & Changelog**:
  - Conventional commits (`CONTRIBUTING.md`). Ledger gated in CI (`changelog-check.yml`).
  - `.githooks/pre-commit` runs `scripts/check.sh` on every commit, pytest included. Prefix `HARNESS_CHECK_SKIP_TESTS=1` once the suite has passed for the change; keep `--no-verify` for emergencies.
- **Runtime**:
  - Python 3.14 via `uv run` (`pyproject.toml`). Quality: `oxlint`, `ruff`, `validate-deps.py`, `basedpyright --warnings`. `scripts/check.sh` is the single local gate mirroring CI.
