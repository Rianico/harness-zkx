# CLI Scrape Standards — Global Options and Basic Arguments

Why CLI `--help` needs special handling: most CLI tools split flags into two layers — **per-command** (`wt merge --no-squash`) and **global** (`wt -C <path>`, `wt --config`, `wt -y`). A naive scrape that only extracts the command's own `Options:` section silently drops globals. That breaks automation: `wt -C <path> merge` fails without `-C`, and agents cannot run unattended without `-y/--yes`. The `worktrunk-guide` curated fix restored these; this standard prevents recurrence for every CLI scrape.

> [!warning] Dropping globals is a silent break
> Generated markdown still looks complete (6 flags for `wt merge`) but is wrong — consumers will `cd` before every call or prompt-block in CI. Treat missing globals as a correctness bug, not polish.

## Standard — MUST for any CLI doc_type

Applies whenever `doc_type` is CLI-shaped: `wt` (worktrunk), `gh`, `cargo`, `kubectl`, etc.

### a) Parse top-level globals once

Run the top-level help (`wt --help` or equivalent HTML landing page) and extract the **Global Options** section as a single source of truth:

- `-C <path>` — working directory override
- `--config <path>` — user config file path
- `--config-set <toml>` — inline TOML override (repeatable)
- `-v, --verbose` — verbose output (with `WORKTRUNK_VERBOSE` env note)
- `-y, --yes` — skip approval prompts
- `-h, --help` — print help

Store as a reusable table; do not re-parse per command.

### b) Merge per-command + automation + globals for every subcommand

For each subcommand (`wt merge`, `wt switch`, `wt list`, `wt remove`, etc):

1. Extract **Arguments** (`[TARGET]` etc).
2. Extract **Options** / `Options:` block (command-specific flags like `--no-squash`, `--stage`).
3. Extract **Automation** (`--no-hooks`, `--format`) if the command exposes it — in `wt merge` this is a separate `Automation:` section.
4. **Merge** the globals table from (a) into the curated output — never emit a command page without it.

### c) Rendering — cross-linked, not duplicated

```markdown
### Flags

| Flag        | Description            |
| ----------- | ---------------------- |
| --no-squash | Skip squashing commits |
| ...         | ...                    |

#### Automation

| Flag           | Description |
| -------------- | ----------- |
| --no-hooks     | Skip hooks  |
| --format <text | json>       | Output format |

#### Global Options — apply to every wt command

| Flag                | Description                                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------------ |
| -C <path>           | Working directory for this command — run `wt -C <path> merge` from any cwd without `cd`                      |
| --config <path>     | User config file path                                                                                        |
| --config-set <toml> | Override config with inline TOML, e.g. `--config-set list.full=true` (repeatable)                            |
| -v, --verbose       | Verbose output (`-v`: info + hook vars on stderr; `-vv`: also debug + `.git/wt/logs/`). `WORKTRUNK_VERBOSE=0 | 1   | 2`  |
| -y, --yes           | Skip approval prompts (use in agents/CI)                                                                     |
| -h, --help          | Print help (`-h` summary, `--help` full)                                                                     |
```

After the first command that renders the full table, subsequent commands may replace the table with a link:

> Global options: see `Global Options — apply to every wt command` (canonical table in `wt merge`).

> [!tip] Cross-link, don't copy forever
> Duplicate the full table for the first/primary command (`wt merge` for worktrunk). For remaining commands, a one-line link satisfies the eval and avoids drift — the eval accepts either the header or the `-C <path>` string.

### d) Verbatim descriptions — do not paraphrase globals

`-C` MUST be:

> Working directory for this command — run `wt -C <path> merge` from any cwd without `cd`

This sentence is the contract that prevents `cd` workarounds in scripts.

### e) Preserve env and repeatable notes

- Keep `WORKTRUNK_VERBOSE=0|1|2` alongside `-v/--verbose` (shell completion and subshells have no flag — env is the only path).
- Keep `(repeatable)` / `e.g. --config-set list.full=true` for `--config-set`.

## Heuristic — when to apply this standard

CLI docs have a distinct shape. Detect before falling back to generic scraping:

**Text / `--help` / markdown:**

- `Usage: wt.*[OPTIONS]` or `Usage: <tool> [OPTIONS] [COMMAND]` in header
- Section headers `Global Options:` / `Options:` / `Automation:` / `Arguments:`
- `COMMAND REFERENCE` or `Commands:` listing subcommands

**HTML:**

- `id="global-options"` or `id="options"` anchors
- `<h2>Global Options</h2>` / `<h2>Options</h2>` followed by a flag table

If neither shape is present, treat as non-CLI and skip the global merge — but log why.

## Example — `wt merge` before / after

**Before (broken — 6 flags only):**

```markdown
### Flags

| Flag         | Description               |
| ------------ | ------------------------- |
| --no-squash  | Skip squashing commits    |
| --no-commit  | Skip commit + squash      |
| --no-rebase  | Skip rebase onto target   |
| --no-remove  | Keep worktree after merge |
| --no-ff      | Create merge commit       |
| --stage <all | tracked                   | none> | What to stage |
```

Missing: automation (`--no-hooks`, `--format`) and globals (`-C`, `--config`, `--config-set`, `-v`, `-y`, `-h`). An agent reading this before will `cd` into the worktree and block on approval prompts.

**After (correct — 6 + 2 + 6):**

```markdown
### Flags

| Flag         | Description               |
| ------------ | ------------------------- |
| --no-squash  | Skip squashing commits    |
| --no-commit  | Skip commit + squash      |
| --no-rebase  | Skip rebase onto target   |
| --no-remove  | Keep worktree after merge |
| --no-ff      | Create merge commit       |
| --stage <all | tracked                   | none> | What to stage |

#### Automation

| Flag           | Description |
| -------------- | ----------- |
| --no-hooks     | Skip hooks  |
| --format <text | json>       | Output format (default: text; json prints structured result) |

#### Global Options — apply to every wt command

| Flag                | Description                                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------------ |
| -C <path>           | Working directory for this command — run `wt -C <path> merge` from any cwd without `cd`                      |
| --config <path>     | User config file path                                                                                        |
| --config-set <toml> | Override config with inline TOML, e.g. `--config-set list.full=true` (repeatable)                            |
| -v, --verbose       | Verbose output (`-v`: info + hook vars on stderr; `-vv`: also debug + `.git/wt/logs/`). `WORKTRUNK_VERBOSE=0 | 1   | 2`  |
| -y, --yes           | Skip approval prompts (use in agents/CI)                                                                     |
| -h, --help          | Print help (`-h` summary, `--help` full)                                                                     |
```

> Global options table: `worktrunk-guide` `references/basics.md` is the curated reference. Raw flags come from `$SKILL_DIR/worktrunk-guide-raw/004-merge.md` (`Global Options:` block from `wt merge --help`).

## Canonical example — worktrunk-guide fix

The `wt merge` help includes critical globals that were dropped because `docs-scraper` only scraped command-specific flags, not the `Global Options` / `Automation` sections. Fix applied to `worktrunk-guide` (`references/basics.md`):

- Raw source: `worktrunk-guide-raw/004-merge.md` — `Global Options:` lists `-C`, `--config`, `--config-set`, `-v/--verbose` (+ `WORKTRUNK_VERBOSE`), `-y/--yes`, `-h/--help`; `Automation:` lists `--no-hooks`, `--format`.
- Curated fix: `references/basics.md` § `wt merge` now renders `### Flags` (6) + `#### Automation` (2) + `#### Global Options — apply to every wt command` (6) with verbatim `-C` description and `WORKTRUNK_VERBOSE` / repeatable notes preserved. See raw:

```
Global Options:
  -C <path>           Working directory for this command
      --config <path> User config file path
      --config-set <toml> Override config with inline TOML, e.g. --config-set list.full=true (repeatable)
  -v, --verbose...    Verbose output (-v: info logs + hook/alias template variables on stderr; -vv: also debug
                      logs and raw subprocess output written to .git/wt/logs/). Set WORKTRUNK_VERBOSE=0|1|2 to
                      apply the same level everywhere — including shell completion, which no flag can reach
  -y, --yes           Skip approval prompts
```

All future CLI scrapes MUST follow the same merge pattern. Validate with `scripts/verify_cli_globals.py <output_dir>` — see Verification below.

## Verification

Run deterministic eval:

```bash
uv run skills/docs-scraper/scripts/verify_cli_globals.py <output_dir>
# or for worktrunk output:
uv run skills/docs-scraper/scripts/verify_cli_globals.py ./references/worktrunk-docs
```

Checks:

- Every `*.md` contains `Global Options` header or `-C <path>` string.
- Worktrunk `wt merge` file contains both `--no-squash` and `-C`.

Exit `0` = pass; non-zero prints missing-flags report.

> [!note] Scraped output exception
> This reference itself is **standard markdown** (scraped docs use standard markdown per repo rule). Skills/notes use Obsidian callouts and wikilinks; scraper output stays standard markdown — this file bridges both by documenting the standard in Obsidian-flavored reference form while prescribing standard markdown for output.

## Links

- Canonical fix: `~/.pi/agent/skills/worktrunk-guide/references/basics.md` § `wt merge → Global Options`
- Raw source: `~/.pi/agent/skills/worktrunk-guide/worktrunk-guide-raw/004-merge.md`
- Eval script: `scripts/verify_cli_globals.py`
- Related: `references/cleanup-patterns.md` (Global Options sections must NOT be cleaned)
