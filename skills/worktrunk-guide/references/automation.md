# Worktrunk Guide — Automation

Source: worktrunk **v0.74.0** (2026-08-14) — <https://github.com/max-sixty/worktrunk>
Raw: `$SKILL_DIR/worktrunk-guide-raw/007-hook.md` · `008-extending.md`
Lead: **`hook`** — lifecycle hooks, template engine, aliases, custom subcommands. Single source for `{{ }}` variables/filters.

> For `switch`/`list`/`remove`/`merge` see [basics](basics.md). For `wt step` ops see [operations](operations.md). For project vs user config locations see [config](config.md).

## Hooks

Shell commands at worktree lifecycle points. Ten hooks across five events; each event has `pre-` (blocking, failure aborts) and `post-` (background, logged).

**Raw:** [`007-hook.md`](../worktrunk-guide-raw/007-hook.md)

| Event  | `pre-` (blocking) | `post-` (background) |
| ------ | ----------------- | -------------------- |
| switch | `pre-switch`      | `post-switch`        |
| start  | `pre-start`       | `post-start`         |
| commit | `pre-commit`      | `post-commit`        |
| merge  | `pre-merge`       | `post-merge`         |
| remove | `pre-remove`      | `post-remove`        |

| Hook          | Purpose                                                           |
| ------------- | ----------------------------------------------------------------- |
| `pre-switch`  | Before branch resolution or worktree creation                     |
| `post-switch` | All switch results: creating, switching, staying                  |
| `pre-start`   | New worktree setup (blocking): deps, env generation               |
| `post-start`  | Background tasks: dev servers, builds, watchers                   |
| `pre-commit`  | Formatters/linters during merge before squash commit              |
| `post-commit` | CI triggers, notifications                                        |
| `pre-merge`   | Tests, security scans after rebase, before merge                  |
| `post-merge`  | Deploy, notifications (runs in target worktree)                   |
| `pre-remove`  | Cleanup before deletion (runs in worktree being removed)          |
| `post-remove` | Stop servers, remove containers (vars reference removed worktree) |

### Configuration forms

**String** — single command:

```toml
pre-start = "npm install"
```

**Table** — multiple concurrent:

```toml
[post-start]
server = "npm run dev"
watch = "npm run watch"
```

**Pipeline** — sequential blocks, concurrent within each:

```toml
[[post-start]]
install = "npm ci"

[[post-start]]
build = "npm run build"
server = "npm run dev"
# install runs first, then build+server concurrent
```

### Project vs user hooks

| Aspect   | Project (`.config/wt.toml`)                       | User (`~/.config/worktrunk/config.toml`) |
| -------- | ------------------------------------------------- | ---------------------------------------- |
| Scope    | Single repo                                       | All repos                                |
| Approval | Required (→ `~/.config/worktrunk/approvals.toml`) | Not required                             |
| Order    | After user hooks                                  | First                                    |

Security: project commands require approval on first run; `wt hook ... --yes` bypasses in CI; `--no-hooks` skips entirely.

---

## Template engine — single source

Used by hooks, aliases, `worktree-path`, `wt step eval`, and `wt step for-each`.

**Raw:** [`007-hook.md`](../worktrunk-guide-raw/007-hook.md)

### Variables — active (current worktree)

| Variable              | Description                   |
| --------------------- | ----------------------------- |
| `{{ branch }}`        | Branch name                   |
| `{{ worktree_path }}` | Worktree directory path       |
| `{{ worktree_name }}` | Worktree directory name       |
| `{{ commit }}`        | Branch HEAD SHA               |
| `{{ short_commit }}`  | Abbreviated SHA               |
| `{{ upstream }}`      | Branch upstream (if tracking) |

### Variables — operation

| Variable                     | Description                           |
| ---------------------------- | ------------------------------------- |
| `{{ base }}`                 | Base branch name                      |
| `{{ base_worktree_path }}`   | Base worktree path                    |
| `{{ target }}`               | Target branch name                    |
| `{{ target_worktree_path }}` | Target worktree path                  |
| `{{ pr_number }}`            | PR/MR number (when via `pr:N`/`mr:N`) |
| `{{ pr_url }}`               | PR/MR web URL                         |

### Variables — repo

| Variable                      | Description                |
| ----------------------------- | -------------------------- |
| `{{ repo }}`                  | Repository directory name  |
| `{{ repo_path }}`             | Absolute path to repo root |
| `{{ owner }}`                 | Primary remote owner path  |
| `{{ primary_worktree_path }}` | Primary worktree path      |
| `{{ default_branch }}`        | Default branch name        |
| `{{ remote }}`                | Primary remote name        |
| `{{ remote_url }}`            | Remote URL                 |

### Variables — user

| Variable           | Description                                 |
| ------------------ | ------------------------------------------- |
| `{{ vars.<key> }}` | Per-branch vars from `wt config state vars` |

### Variable perspective

| Operation         | Bare vars            | `base`              | `target`         |
| ----------------- | -------------------- | ------------------- | ---------------- |
| `switch`/`create` | destination          | where you came from | = bare vars      |
| `merge`           | feature being merged | = bare vars         | merge target     |
| `remove`          | branch being removed | = bare vars         | where you end up |

### Filters

| Filter          | Example                         | Description                                  |
| --------------- | ------------------------------- | -------------------------------------------- |
| `sanitize`      | `{{ branch \| sanitize }}`      | Replace `/` `\` → `-`                        |
| `sanitize_db`   | `{{ branch \| sanitize_db }}`   | DB-safe: lowercase, underscores, hash suffix |
| `sanitize_hash` | `{{ branch \| sanitize_hash }}` | Filesystem-safe with hash suffix             |
| `hash`          | `{{ branch \| hash }}`          | 3-char base36 digest                         |
| `hash_port`     | `{{ branch \| hash_port }}`     | Port 10000–19999 from hash                   |
| `dirname`       | `{{ repo_path \| dirname }}`    | Strip last component                         |
| `basename`      | `{{ repo_path \| basename }}`   | Keep last component                          |
| `codename(n)`   | `{{ branch \| codename(2) }}`   | Deterministic friendly name                  |

`hash_port` hashes any string, so `{{ (repo ~ '-' ~ branch) \| hash_port }}` gives a different port than `{{ branch \| hash_port }}` — use to avoid collisions between dev server and DB ports.

```toml
[post-start]
dev = "npm run dev -- --port {{ branch | hash_port }}"
# Different hash for DB:
# port = "{{ ('db-' ~ branch) | hash_port }}"
```

### Functions

| Function                          | Example                                 | Description                      |
| --------------------------------- | --------------------------------------- | -------------------------------- |
| `worktree_path_of_branch(branch)` | `{{ worktree_path_of_branch('main') }}` | Look up worktree path for branch |

---

## Running hooks manually

```bash
wt hook <TYPE> [NAMES...] [-- KEY=VALUE...] [-- ARGS...]
```

```bash
wt hook pre-merge              # all pre-merge hooks
wt hook pre-merge test         # hook named "test"
wt hook pre-merge test build
wt hook pre-merge user:        # all user hooks
wt hook pre-merge project:     # all project hooks
wt hook pre-merge user:test
wt hook pre-merge --yes
wt hook pre-start --branch=feature/test    # override template var
wt hook pre-merge -- --extra args          # forward into {{ args }}
```

---

## Aliases

Aliases define `wt <name>` commands. Resolution: built-in → alias → custom subcommand.

**Raw:** [`008-extending.md`](../worktrunk-guide-raw/008-extending.md)

```toml
[aliases]
deploy = "fly deploy --config=fly.{{ env }}.toml --app=myapp-{{ branch }}"
open = "open http://localhost:{{ branch | hash_port }}"
since-main = "git log --oneline {{ default_branch }}..HEAD"
```

```bash
wt deploy --env=staging
wt open
```

Template variables: same engine as hooks, plus `{{ args }}` for positional arguments.

**Multi-step pipelines:**

```toml
[[aliases.release]]
test = "cargo test"

[[aliases.release]]
build = "cargo build --release"
package = "cargo package --no-verify"

[[aliases.release]]
publish = "cargo publish {{ args }}"
# Blocks run in order; keys within a block run concurrently
```

**Inspection:**

```bash
wt config alias show <name>
wt config alias dry-run <name>
wt config alias dry-run deploy -- --env=staging
```

---

## Custom subcommands

Any executable `wt-<name>` on `PATH` becomes `wt <name>`. Built-ins and aliases take precedence. Args pass verbatim, stdio inherited, exit propagated. No template variables.

```bash
cargo install worktrunk-sync
wt sync origin
```

---

## Extension comparison

|                | Hooks                 | Aliases              | Custom subcommands   |
| -------------- | --------------------- | -------------------- | -------------------- |
| **Trigger**    | Automatic (lifecycle) | Manual (`wt <name>`) | Manual (`wt <name>`) |
| **Defined in** | TOML config           | TOML config          | Executable on `PATH` |
| **Templates**  | Yes                   | Yes                  | No                   |
| **Shareable**  | `.config/wt.toml`     | `.config/wt.toml`    | Distribute binary    |
| **Language**   | Shell                 | Shell                | Any                  |

---

## Changes since v0.49 → v0.74 (sync 2026-08-25)

- **`pre-create`/`post-create` aliases (0.53)** — silent aliases for `pre-start`/`post-start` in config and `wt hook`; docs still recommend `pre-start`
- **Hook approval freeze (0.52)** — project hook commands frozen into immutable plan at approval gate; post-operation mutation (merge moves target, rebase rewrites config) can't execute unapproved command
- **Table `pre-*` concurrent (0.58 breaking)** — `[pre-merge]` multi-entry now concurrent (was serial); pipeline `[[pre-merge]]` for serial; `wt config update` migrates
- **Template rendering per-step (0.58)** — templates syntax-checked up front, rendered at execution so `{{ vars.* }}` reads fresh; undefined var fails at that step, background hook errors surface in hook log
- **Hook vars:** `{{ remote_repo }}` available wherever `owner` is (0.74), `{{ git.branch.* }}` via custom columns already (0.64)
- **`{{ vars.* }}` JSON bool/null** — `true`/`false`/`null` now `True`/`False`/`None` inside nested `vars` (0.74 breaking, whole-value string unchanged)
- **Hourly/daily rate-limit pace in statusline** `-vv` profile 20 slowest /10 redundant, `BY CONTEXT` table, env allowlist (0.54/0.65/0.67)
