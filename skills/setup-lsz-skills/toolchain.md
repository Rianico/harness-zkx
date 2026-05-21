# Toolchain

The preferred CLI tools available in this environment. Engineering skills use this file to determine which tools to invoke and what fallbacks to use when a preferred tool is missing.

## Detected Tools

| Tool | Status | Purpose | Fallback |
|------|--------|---------|----------|
| `adr` | **DETECTED** | ADR CLI for architecture decision records | manual `mkdir` + template |
| `fd` | **DETECTED** | File discovery (replaces Glob/find) | `find` |
| `rg` | **DETECTED** | Content search (replaces grep/ack/ag) | `grep` |
| `eza` | **DETECTED** | Directory structure (replaces ls/tree) | `ls` / `tree` |
| `llm-lsp-cli` | **DETECTED** | LSP code intelligence | (optional, no fallback) |
| `wt` | **DETECTED** | Worktree management (replaces git worktree) | `git worktree` |
| `uv` | **DETECTED** | Python tooling (replaces pip/venv) | `pip` / `venv` |

> Edit the **Status** column to match what was actually detected during setup.
> Remove rows for tools that were explicitly excluded during setup.

## Usage Rules

When a tool is **DETECTED**, use it as the primary choice for its task. When a tool is **NOT DETECTED**, use the fallback.

- **ADR CLI:** `adr init docs/adr` — initialize architecture decision records directory
- **File discovery:** `fd --glob "*.md" skills` over `find . -name "*.md"`
- **Content search:** `rg -n "pattern"` over `grep -rn "pattern"`
- **Directory overview:** `eza -T -L 3 .` over `ls -R` or `tree`
- **LSP intelligence:** `llm-lsp-cli lsp definition <file> <line> <col>` — no fallback; skip semantic navigation if absent
- **Worktree management:** `wt switch --create <name>` over `git worktree add`
- **Python tooling:** `uv run python` over `python -m`; `uv pip install` over `pip install`

## How Skills Read This

Engineering skills that need to invoke CLI tools check this file (via the `docs/agents/` path referenced in `CLAUDE.md` / `AGENTS.md`) to determine which commands are safe to use in this environment. If a tool is not listed or marked NOT DETECTED, the skill uses the fallback or skips the step.
