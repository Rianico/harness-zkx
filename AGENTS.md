# Repository Instructions

## Talking Style

Sacrifice grammar for concision.

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
  - Run all: `uv run pytest`.
  - Test naming: `tests/<skill>/test_<component>.py`. Conftest handles runtime `sys.path`.
- **Multi-Agent Contract (Herdr)**:
  - When running under Herdr (`HERDR_ENV=1`), always use harness scripts in `skills/herdr/scripts/` (never raw CLI):
    - Dispatch: `uv run skills/herdr/scripts/herdr_dispatch.py <worker> --file <ticket>`
    - Reply: `uv run skills/herdr/scripts/herdr_reply.py <caller> "<STATUS> <artifacts> <issues>"`
- **Issue Tracker & Triage**:
  - GitHub CLI (`gh`). Vocabulary: `docs/agents/triage-labels.md`. Guide: `docs/agents/issue-tracker.md`.
- **Contribution & Changelog**:
  - Conventional commits (`CONTRIBUTING.md`). Ledger gated in CI (`changelog-check.yml`).
- **Runtime**:
  - Python 3.14 via `uv run` (`pyproject.toml`). Quality: `oxlint`, `ruff`, `validate-deps.py`, `basedpyright`.
