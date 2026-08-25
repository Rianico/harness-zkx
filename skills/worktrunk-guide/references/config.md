# Worktrunk Guide — Config

Source: worktrunk **v0.74.0** (2026-08-14) — <https://github.com/max-sixty/worktrunk>
Raw: `$SKILL_DIR/worktrunk-guide-raw/005-config.md`
Lead: **`config`** — user/project config, shell integration, worktree path, state.

> For template engine details (variables/filters/functions) see [automation](automation.md). For LLM commit generation see [integrations](integrations.md).

## Configuration files

| File           | Location                          | Contains                       | Shared    |
| -------------- | --------------------------------- | ------------------------------ | --------- |
| User config    | `~/.config/worktrunk/config.toml` | Worktree path, LLM config      | No        |
| Project config | `.config/wt.toml`                 | Hooks, dev server URL, aliases | Yes (VCS) |
| System config  | Platform-specific                 | Shared defaults                | Yes       |

Raw: [`005-config.md`](../worktrunk-guide-raw/005-config.md)

## `wt config`

```bash
wt config <COMMAND>
```

| Subcommand  | Description                                         |
| ----------- | --------------------------------------------------- |
| `shell`     | Shell integration setup                             |
| `create`    | Create config file (`--project` for project config) |
| `show`      | Show config files & locations                       |
| `update`    | Update deprecated settings                          |
| `approvals` | Manage command approvals                            |
| `alias`     | Inspect/preview aliases                             |
| `state`     | Manage internal data & cache                        |

## Shell integration

Required for `wt switch` to change directories.

```bash
wt config shell install      # Bash→~/.bashrc  Zsh→~/.zshrc  Fish→wt.fish  PowerShell→profile
wt config shell uninstall
```

Without integration `wt switch` prints the target directory but cannot `cd` into it.

## Worktree path template

Controls where `wt switch --create` places new worktrees. Set in user config:

```toml
worktree-path = "{{ repo_path }}/../{{ repo }}.{{ branch | sanitize }}"
```

| Variable                      | Example                         |
| ----------------------------- | ------------------------------- |
| `{{ repo_path }}`             | `/Users/me/code/myproject`      |
| `{{ repo }}`                  | `myproject`                     |
| `{{ owner }}`                 | `group/subgroup` (remote owner) |
| `{{ branch }}`                | `feature/auth` (raw)            |
| `{{ branch \| sanitize }}`    | `feature-auth`                  |
| `{{ branch \| sanitize_db }}` | `feature_auth_x7k`              |
| `{{ branch \| codename(2) }}` | `malleable-opah`                |

### Example templates

```toml
# Default: sibling directory
worktree-path = "{{ repo_path }}/../{{ repo }}.{{ branch | sanitize }}"
# Inside repo
worktree-path = "{{ repo_path }}/.worktrees/{{ branch | sanitize }}"
# Centralized
worktree-path = "~/worktrees/{{ repo }}/{{ branch | sanitize }}"
# By remote owner
worktree-path = "~/development/{{ owner }}/{{ repo }}/{{ branch }}"
```

Full filter list: `sanitize`, `sanitize_db`, `sanitize_hash`, `hash`, `hash_port`, `dirname`, `basename`, `codename(n)` — see [automation](automation.md).

## Command defaults

```toml
[list]
summary = false    # LLM summaries (needs [commit.generation])
full = false       # Show CI, diffstat, summaries
branches = false   # Include branches without worktrees
remotes = false    # Include remote branches

[merge]
squash = true      # Squash commits into one
commit = true      # Commit uncommitted changes first
rebase = true      # Rebase onto target before merge
remove = true      # Remove worktree after merge
verify = true      # Run project hooks
ff = true          # Fast-forward merge

[switch]
cd = true          # Change directory after switch

[switch.picker]
pager = "delta --paging=never"
```

## Project config (`.config/wt.toml`)

Checked into VCS for team sharing.

```toml
# Hooks
pre-start = "npm ci"
post-start = "npm run dev"
pre-merge = "npm test"

# Dev server URL shown in wt list
[list]
url = "http://localhost:{{ branch | hash_port }}"

# Forge platform for pr:{N} / mr:{N}
[forge]
platform = "github"   # github | gitlab | gitea | azure-devops
hostname = "github.example.com"  # self-hosted

# Aliases
[aliases]
deploy = "make deploy BRANCH={{ branch }}"
url = "echo http://localhost:{{ branch | hash_port }}"
```

## State management

```bash
wt config state <SUBCOMMAND>
```

| Subcommand        | Description                         |
| ----------------- | ----------------------------------- |
| `default-branch`  | Get/set default branch              |
| `previous-branch` | Previous branch for `wt switch -`   |
| `logs`            | Operation & debug logs              |
| `ci-status`       | CI status cache                     |
| `marker`          | Branch markers (emoji in `wt list`) |
| `vars`            | Custom variables per branch         |

### Default branch

```bash
wt config state default-branch              # get
wt config state default-branch set main     # set
wt config state default-branch clear        # clear cache and re-detect
```

Detection order: Worktrunk cache → Git cache → Remote query → Local inference.

### Markers & custom variables

```bash
wt config state marker set "🚧"
wt config state marker set "✅" --branch feature
# Shows in wt list Status column

wt config state vars set env=staging
wt config state vars set config='{"port": 3000}'
wt config state vars get env
# Template: {{ vars.env }}, {{ vars.config.port }}
```

## Environment variables

Override config with `WORKTRUNK_` prefix; nested keys use `__`:

| Config                      | Env var                                 |
| --------------------------- | --------------------------------------- |
| `worktree-path`             | `WORKTRUNK_WORKTREE_PATH`               |
| `commit.generation.command` | `WORKTRUNK_COMMIT__GENERATION__COMMAND` |
| `commit.stage`              | `WORKTRUNK_COMMIT__STAGE`               |

| Variable                            | Purpose                                 |
| ----------------------------------- | --------------------------------------- |
| `WORKTRUNK_BIN`                     | Override binary path                    |
| `WORKTRUNK_CONFIG_PATH`             | Override user config location           |
| `WORKTRUNK_PROJECT_CONFIG_PATH`     | Override project config location        |
| `WORKTRUNK_MAX_CONCURRENT_COMMANDS` | Max parallel git commands (default: 32) |
| `NO_COLOR`                          | Disable colored output                  |

## Approvals

Project hooks/aliases require approval on first run (saved to `~/.config/worktrunk/approvals.toml`).

```bash
wt config approvals add          # pre-approve current project
wt config approvals clear
wt config approvals clear --global
# Use --yes to bypass prompts in CI
```

---

## Changes since v0.49 → v0.74 (sync 2026-08-25)

- **Inline overrides `--config-set <toml>`** — global, repeatable, before/after subcommand; deep-merge tables, `wt --config-set list.full=true list` (0.61)
- **Custom columns [experimental]** — `[list.custom-columns.<Header>]` minijinja over `branch`/`worktree_path`/`vars.*` + `{{ git.branch.* }}` (0.61-0.64); `[list] columns` ordered selection overrides `--full` presets (0.62-0.63), narrowed columns skip unused git probes (0.63)
- **JSON schema 2** — `[list] json-schema = 2` envelope (`schema`, `repo.default_branch`, `collected`) with `null` pending vs absent not-requested; v1 default still (0.66), `wt config update` now writes `=2` (0.68)
- **User project-specific settings wildcard** — `[projects."git.company.example/*"]` least→most specific, sets `forge.platform/hostname` per-host (0.72); single host needs one entry not per-repo
- **Worktree path template:** new `{{ remote_repo }}` (remote URL name vs `{{ repo }}` dir) (0.74), full filter list still in [automation](automation.md)
- **`wt config show`**: prints project identifier `<host>/<owner>/<repo>` + GEMINI section + `identifier` JSON (0.53/0.56)
- **Approvals:** `wt config approvals list` grouped + `clear --stale` + `--format=json` (0.66/0.72), `approvals add --yes` non-interactive (0.74)
- **Forge detection:** exact DNS label → substring (0.71) → reverted to substring (0.72) — hyphenated self-host `github-enterprise.acme.com` works again; `forge.platform = "github"` fallback; Azure `visualstudio.com` suffix (0.71)
- **Nushell vendor autoload** `wt.nu` now `$nu.vendor-autoload-dirs | last` (0.57), fish brace → `"$CLAUDE_PLUGIN_ROOT"` (0.57)
- **State:** `wt config state` flags stale `default-branch` vs `origin/HEAD` (0.68), `logs profile` BY CONTEXT table (0.67)
