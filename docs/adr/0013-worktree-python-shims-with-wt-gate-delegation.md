# 13. Worktree Python Shims with wt Gate Delegation and Auto-Scaffold

Date: 2026-08-26

## Status

Accepted

Implements [Worktree Workflow](../../CONTEXT.md#worktree-workflow) and [Respect Tool Feedback](../../CONTEXT.md#respect-tool-feedback)

## Context

`skills/branch-worktree-pr` shipped 6 bash/python helpers (`create_target.sh`, `make_copy.sh`, `merge_copy.sh`, `open_pr.sh`, `claim_gate.py`, `verify_parent.py` + `check_history.py`) that drifted: `merge_copy.sh` hardcoded `npm run typecheck && npm test`, `verify_parent.py` read `.config/wt.toml [pre-merge].gate` with `npm` fallback, `wt-template.toml` documented `cargo`/`uv` only as comments. Bash path-guessing (`refs/heads` vs `[branch]`) and `shell=True` injection made typing and polyglot (rust/python/typescript) impossible. Grilling revealed `wt.toml` is template until copied via `wt config create --project`, and `wt merge` is the final deterministic gate — not the orchestrator. The choice was: one comprehensive Python CLI that absorbs `wt`, one monolith that absorbs shims, or thin Python shims sharing a typed lib.

## Decision

We will keep the phase-mapped shape but replace bash with Python:

- **Stack ownership:** `.config/wt.toml [pre-merge].gate` is the single writer. `wt merge` executes it verbatim. Scripts never synthesize a gate at runtime and never hardcode `npm`.
- **First-run scaffold (once):** When `.config/wt.toml` is absent, `scripts/_lib.py:read_gate()` scaffolds from `references/wt-template.toml` → `.config/wt.toml` with a stack-detected `gate`:
  - `Cargo.toml` → `cargo test && cargo clippy -- -D warnings`
  - `pyproject.toml` → `uv run ruff check . && uv run basedpyright && uv run pytest -q`
  - `package.json` → `npm run typecheck && npm test`
  - Unknown → fail loud with `missing .config/wt.toml — run wt config create --project and set [pre-merge].gate`
    After scaffold, `wt.toml` is the only source; no sniffing.
- **Python package:** `scripts/_lib.py` owns the typed boundary (`read_gate() -> str`, `wt_list() -> list[Worktree]`, `git_status_clean(allow=[.lsz/tmp]) -> Result`, `Worktree` dataclass). Six thin entrypoints (`claim_gate.py`, `create_target.py`, `make_copy.py`, `merge_copy.py`, `verify_parent.py`, `check_history.py`; `open_pr.py`) each `<60` lines delegate to `_lib` and `wt`/`gh`/`git`. Optional dispatcher `scripts/worktree.py` forwards to same lib for discoverability (`uv run scripts/worktree.py make-copy -- ...`). `uv run` + inline `// script` metadata, `ruff` + `basedpyright`.
- **Delete bash shims** (`git rm scripts/*.sh`) — no compat shims. `SKILL.md` phases 0–6 and `scripts/README.md` examples updated to `uv run scripts/...py`. `wt` stays the final gate; Python never re-implements `wt switch`/`wt merge`/`copy-ignored`/`hash_port`.

### Considered Options

- **Rejected: One monolith `workflow.py` absorbing all phases** — single God file, blast radius couples unrelated phases, loses 1:1 phase → script mapping that the skill's `Phase 0–6` mental model depends on.
- **Rejected: Python absorbs `wt`** — re-implements `wt` hooks and port allocation, duplicates deterministic gate, drifts from `wt` as source of truth.
- **Rejected: Keep bash shims, Python only as lib** — bash fragility remains, `shell=True` and path-guessing untyped, no `basedpyright` coverage.
- **Rejected: Keep `npm` fallback / runtime sniffing** — two writers, drift per Q2, breaks polyglot determinism.

## Consequences

- Polyglot projects declare gate once in `wt.toml`; `merge_copy.py` now calls `wt step pre-merge` / `read_gate()` instead of hardcoded `npm`, fixing drift across three prior sites.
- Fresh repo bootstrap is one call: first shim auto-scaffolds correct gate for rust/python/ts; unknown stack fails with actionable hint instead of silent `npm` wrong gate.
- Phase diffs stay isolated (atomic commits per skill), but shared helpers are typed and testable (`tests/branch-worktree-pr/test_*.py` per `tests/<skill>/test_<component>.py` convention, `uv run pytest`).
- `wt` remains the deterministic pre-merge blocker; scripts are pure delegates — no duplication of `copy-ignored`/`hash_port` logic.
- Bash deletion is a breaking change for cached `scripts/*.sh` strings in prompts — mitigated by dispatcher alias and `SKILL.md` pointer update.
- Future stacks (deno/bun/go) add one row to the scaffold matrix in `_lib.py` and `wt-template.toml`, not a rewrite.
