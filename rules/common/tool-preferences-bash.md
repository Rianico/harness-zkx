---
agents:
  - claude
  - codex
  - agy
---

# Tool Preferences — Bash Tool Choices

Which binary a shell command should use.

- **Search:** Prefer `rg` over `grep` or `grep -r`. Ripgrep respects `.gitignore` rules and supports fast scoped queries with `--glob`, `-g`, or `--type`.
- **File discovery:** Prefer `fd` over `find`. It respects ignore files and provides simple syntax (`fd <pattern> <path>`). Use `fd --type f` or `fd --type d`.
- **Listing:** Prefer `eza` over `ls` or `tree` (`eza -la` or `eza --tree`). When `eza` is unavailable, fall back to `ls` or `tree`.

## Runtimes — Package Manager and Runner

- **Python:** Prefer `uv` over `pip`, `poetry`, or `pipenv` (`uv run`, `uv add`, `uv sync`).
- **TypeScript / Node:** Prefer `pnpm` over `npm` or `yarn`.
  - Runner: Prefer `tsx` over `ts-node`.
  - Lint and format: Use `oxlint` and `oxfmt` with Prettier fallback (`biome` remains as deprecated compatibility).
