# Tool Preferences

- **Reading:** `read` for files you will edit (not `cat`/`bat`)
- **Paths:** absolute only — cwd resets between subagent turns
- **Code nav:** AST/treesitter for overview; LSP for cross-file renames (`rename`, `references`)

## Runtimes — native tool owns version + deps; commit version file

- **Python:** `uv` > `pip`/`poetry`/`pipenv` — `uv run` / `uv add` / `uv sync`; respects `.python-version` (default 3.14) and `.tool-versions` when present
- **TypeScript/Node:** `pnpm` > `npm`/`yarn` — `pnpm -r` workspaces; runner `tsx` > `ts-node`; check `tsc --noEmit` (`tsc -b`), lint `biome` or `eslint`, test `vitest` / `node --test`
- **Rust:** `cargo` — `cargo test` / `cargo clippy` / `cargo fmt` + `rust-toolchain.toml`
- **Go:** `go` — `go test ./...` / `go vet` / `gofumpt` / `golangci-lint` + `go.mod` / `go.work`
- **Multi (2+ runtimes):** `asdf` + `.tool-versions` → `asdf install` syncs all; other tools respect it; `corepack`/`nvm` + `.nvmrc` for Node fallback when single
