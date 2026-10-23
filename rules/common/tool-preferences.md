# Tool Preferences

- **Reading:** Use `read` for files you intend to edit instead of `cat` or `bat`.
- **Paths:** Use absolute paths only. The working directory resets between subagent turns.
- **Code navigation:** Use AST or treesitter for code structure overviews. Use LSP for cross-file renames and references (`rename`, `references`).
- **Search:** Prefer `rg` over `grep` or `grep -r`. Ripgrep respects `.gitignore` rules and supports fast scoped queries with `--glob`, `-g`, or `--type`.
- **File discovery:** Prefer `fd` over `find`. It respects ignore files and provides simple syntax (`fd <pattern> <path>`). Use `fd --type f` or `fd --type d`.
- **Listing:** Prefer `eza` over `ls` or `tree` (`eza -la` or `eza --tree`). Fall back to `ls` or `tree` when `eza` is unavailable.
- **Skill paths:** The `$SKILL_DIR` token represents the directory that contains the active `SKILL.md`. For a subskill document, use the subskill directory rather than the parent root. When identical skill names exist globally and locally, prefer the repository-local copy whenever the working directory is that repository.

## Runtimes — Native Tool Governs Dependencies and Versions

Commit the project version file alongside tool configurations.

- **Python:** Prefer `uv` over `pip`, `poetry`, or `pipenv` (`uv run`, `uv add`, `uv sync`). Respect `.python-version` (default 3.14) and `.tool-versions`.
- **TypeScript / Node:** Prefer `pnpm v12` over `npm` or `yarn`. Use `pnpm -r` workspaces (`packageManager: pnpm@12.4.1` with `.nvmrc 26`).
  - Runner: Prefer `tsx` over `ts-node`.
  - Type check: Run `tsc --noEmit` (`tsc -b` for parallel project builds).
  - Lint and format: Use `oxlint` and `oxfmt` with Prettier fallback (`biome` remains as deprecated compatibility).
  - Test: Run `vitest` or `node --test`.
  - Build: Run `vite v8` with Rolldown and Oxc.
- **Rust:** Use `cargo` for builds, tests, and checks (`cargo test`, `cargo clippy`, `cargo fmt`). Specify versions in `rust-toolchain.toml`.
- **Go:** Use `go` for builds and verification (`go test ./...`, `go vet`, `gofumpt`, `golangci-lint`). Pin versions in `go.mod` and `go.work`.
- **Multi (2+ runtimes):** Use `asdf` with `.tool-versions` across two or more runtimes. Run `asdf install` to synchronize all tools. Other tools respect this version synchronization. Use `corepack` or `nvm` with `.nvmrc` as a fallback for standalone Node projects.
