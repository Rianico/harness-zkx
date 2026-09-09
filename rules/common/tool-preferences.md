# Tool Preferences

- **Reading:** `read` for files you will edit (not `cat`/`bat`)
- **Paths:** absolute only — cwd resets between subagent turns
- **Code nav:** AST/treesitter for overview; LSP for cross-file renames (`rename`, `references`)
- **Search:** `rg` > `grep`/`grep -r` — ripgrep (respects `.gitignore`, faster, scope with `--glob`/`-g`/`--type`)
- **File discovery:** `fd` > `find` — respects ignores, simpler `fd <pattern> <path>`; use `fd --type f`/`--type d`
- **Listing:** `eza` > `ls`/`tree` — `eza -la` / `eza --tree` (icons, git); fallback `ls`/`tree` when `eza` unavailable

## Runtimes — native tool owns version + deps; commit version file

- **Python:** `uv` > `pip`/`poetry`/`pipenv` — `uv run` / `uv add` / `uv sync`; respects `.python-version` (default 3.14) and `.tool-versions` when present
- **TypeScript/Node:** `pnpm v12` > `npm`/`yarn` — `pnpm -r` workspaces (Rust native, content-addressed, `packageManager: pnpm@12.0.0` + `.nvmrc 24`); runner `tsx` > `ts-node`; check `tsc --noEmit` (TS v7 Go native, `tsc -b` parallel), lint `oxlint` + format `oxfmt` (native, Prettier fallback; `biome` deprecated compat), test `vitest` / `node --test`, build `vite v8` (Rolldown + Oxc)
- **Rust:** `cargo` — `cargo test` / `cargo clippy` / `cargo fmt` + `rust-toolchain.toml`
- **Go:** `go` — `go test ./...` / `go vet` / `gofumpt` / `golangci-lint` + `go.mod` / `go.work`
- **Multi (2+ runtimes):** `asdf` + `.tool-versions` → `asdf install` syncs all; other tools respect it; `corepack`/`nvm` + `.nvmrc` for Node fallback when single
