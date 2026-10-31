# Tool Preferences

- **Bash binary choices:** Package managers, runners, formatters, `rg`/`fd`/`eza`, and `uv`/`pnpm`/`tsx`/`oxlint`/`oxfmt` live in [tool-preferences-bash.md](tool-preferences-bash.md).
- **Shell execution:**
  - **Atomic commands:** Run one command per tool call. Avoid compound chaining (`&&`, `;`). Use `&&` only when a subsequent command strictly depends on the previous exit status.
  - **No redundant navigation:** Never prefix commands with `cd <cwd>` or `cd .`. The tool runs in the current workspace directory.
  - **No decorative banners:** Omit divider echoes (e.g. `echo "---"`) between chained commands.
  - **No interactive TTY commands:** Never invoke interactive editors or monitors (`vim`, `nano`, `top`, `watch`, `tail -f`, unflagged `git commit`). Pass explicit non-interactive flags (`-m`, `-F`, `--no-edit`) or query flags.
- **Reading:** Use `read` for files you intend to edit instead of `cat` or `bat`.
- **Line endings & non-printing characters:** Never assume GNU `cat -A` on macOS. BSD `cat` rejects `-A`. Use `cat -vet`, `gcat -A` (Homebrew coreutils), `od -c`, or `xxd`. The `-A` display-tail is GNU-only and deferred (#176).
- **Paths:** Use absolute paths only. The working directory resets between subagent turns.
- **Code navigation:** Use AST or treesitter for code structure overviews. Use LSP for cross-file renames and references (`rename`, `references`).
- **Skill paths & `$SKILL_DIR`:** The system prompt's `<skills>` block defines the skill directory as `parent of SKILL.md / dirname of the path`. In skill instructions, `$SKILL_DIR` refers to this directory.
  - **Bash substitution:** Bash does not export `$SKILL_DIR` by default. Replace `$SKILL_DIR` with the resolved absolute path in shell commands. An unexpanded `$SKILL_DIR/scripts/x` evaluates to `/scripts/x` and crashes.
  - **Top-level skill:** Read `<location>` from the system prompt's `<skill>` XML block. `$SKILL_DIR` is `dirname(<location>)` (e.g. `<location>/path/to/foo/SKILL.md</location>` → `/path/to/foo`).
  - **Subskill:** For a subskill loaded dynamically (e.g. `.../subskills/bar/SKILL.md`), `$SKILL_DIR` is its own directory (`.../subskills/bar`), not the parent root.
  - **Reference file:** A file in `.../references/doc.md` is not a `SKILL.md`. It inherits `$SKILL_DIR` from its nearest ancestor `SKILL.md` (the directory above `references/`).

## Runtimes — Native Tool Governs Dependencies and Versions

Commit the project version file alongside tool configurations.

- **TypeScript / Node:**
  - Type check: Run `tsc --noEmit` (`tsc -b` for parallel project builds).
  - Test: Run `vitest` or `node --test`.
  - Build: Run `vite` with Rolldown and Oxc.
- **Rust:** Use `cargo` for builds, tests, and checks (`cargo test`, `cargo clippy`, `cargo fmt`). Specify versions in `rust-toolchain.toml`.
- **Go:** Use `go` for builds and verification (`go test ./...`, `go vet`, `gofumpt`, `golangci-lint`). Pin versions in `go.mod` and `go.work`.
- **Multi (2+ runtimes):** Use `asdf` with `.tool-versions` across two or more runtimes. Run `asdf install` to synchronize all tools. Other tools respect this version synchronization. Use `corepack` or `nvm` with `.nvmrc` as a fallback for standalone Node projects.
