# Worktrunk Guide — Basics

Source: worktrunk **v0.74.0** (2026-08-14) — <https://github.com/max-sixty/worktrunk>
Raw: `$SKILL_DIR/worktrunk-guide-raw/001-switch.md` · `002-list.md` · `003-remove.md` · `004-merge.md`
Lead: **`switch`** — branch-addressed CRUD. Shell: Bash/Zsh/Fish/PowerShell. Package: `worktrunk`.

> Covers the 80% surface: `wt switch` / `list` / `remove` / `merge`. For hooks/templates see [automation](automation.md); for step ops see [operations](operations.md).

## `wt switch` — switch or create worktree

Branch-addressed switch. Unlike `git switch`, navigates between worktrees; path comes from `worktree-path` template. Shortcuts also apply to `--base`.

**Raw:** [`001-switch.md`](../worktrunk-guide-raw/001-switch.md)

### Syntax

```bash
wt switch [OPTIONS] [BRANCH] [-- EXECUTE_ARGS...]
```

### Flags

| Flag                       | Description                                          |
| -------------------------- | ---------------------------------------------------- |
| `-c, --create`             | Create a new branch                                  |
| `-b, --base <BASE>`        | Base branch for new branch (default: default branch) |
| `-x, --execute <CMD>`      | Command to run after switch                          |
| `--clobber`                | Remove stale non-worktree path at target             |
| `--no-cd`                  | Skip directory change                                |
| `--branches` / `--remotes` | Include branch types in picker                       |

> [!TIP]
> Shortcuts (`^` `@` `-` `pr:{N}` `mr:{N}`) live in SKILL.md in-file reference. They apply to both `BRANCH` and `--base`.

### Examples

```bash
wt switch feature-auth                         # switch to existing
wt switch --create new-feature                 # create + switch
wt switch --create hotfix --base production    # create from specific base
wt switch pr:123                               # GitHub PR #123
wt switch -                                    # previous worktree
wt switch --create fix -x claude -- 'Fix bug #42'  # create + launch agent
```

### Workflow on create

1. `pre-switch` hooks (blocking) → 2. Create worktree → 3. `cd` into it → 4. `pre-start` hooks (blocking) → 5. `post-start` + `post-switch` (background)

### Pitfalls

- **Branch doesn't exist** → add `--create`
- **Path occupied** → switch to that worktree or `wt remove` it
- **Stale directory** → `--clobber`

---

## `wt list` — list worktrees + status

Progressive table: branch names first, git status fills async. Shows uncommitted changes, divergence from default/remote, optional CI and LLM summaries.

**Raw:** [`002-list.md`](../worktrunk-guide-raw/002-list.md)

### Syntax

```bash
wt list [OPTIONS]
wt list statusline
```

### Flags

| Flag                       | Description                                          |
| -------------------------- | ---------------------------------------------------- |
| `--format <table\|json>`   | Output format (default: table)                       |
| `--full`                   | Show CI, diff analysis, LLM summaries                |
| `--branches` / `--remotes` | Include branches without worktrees / remote branches |
| `--progressive`            | Progressive render (auto for TTY)                    |

### Columns

| Column                 | Shows                                            |
| ---------------------- | ------------------------------------------------ |
| Branch                 | Branch name                                      |
| Status                 | Compact symbols (+ ! ? ^ _ ⊂ ↕ ⇡ ⇣)              |
| HEAD±                  | Uncommitted +added / -deleted lines              |
| main↕                  | Commits ahead/behind default branch              |
| Remote⇅                | Ahead/behind tracking branch                     |
| CI                     | Pipeline status (`--full`)                       |
| URL                    | Dev server URL from config                       |
| Commit / Age / Message | Short hash, time since commit, truncated message |

### Status symbols

| Symbol    | Meaning                         |
| --------- | ------------------------------- |
| `+`       | Staged                          |
| `!`       | Modified (unstaged)             |
| `?`       | Untracked                       |
| `^`       | Default branch                  |
| `_`       | Same commit as default, clean   |
| `⊂`       | Content integrated into default |
| `↕`       | Diverged                        |
| `⇡` / `⇣` | Ahead / behind remote           |

Rows dimmed when safe to delete (`_` or `⊂`).

### Examples

```bash
wt list
wt list --full
wt list --branches
wt list --format=json | jq '.[] | select(.is_current) | .branch'
wt list --format=json | jq '.[] | select(.main_state == "integrated") | .branch'
```

### JSON fields

`branch`, `path`, `kind`, `working_tree.{staged,modified,untracked}`, `main.{ahead,behind}`, `remote.{ahead,behind}`, `main_state`, `ci.status`

---

## `wt remove` — remove worktree + branch if merged

Defaults to current worktree. Runs in background (returns immediately); use `--foreground` to block.

**Raw:** [`003-remove.md`](../worktrunk-guide-raw/003-remove.md)

### Syntax

```bash
wt remove [OPTIONS] [BRANCHES]...
```

### Flags

| Flag                 | Description                                  |
| -------------------- | -------------------------------------------- |
| `--no-delete-branch` | Keep branch after removal                    |
| `-D, --force-delete` | Delete branch even if unmerged               |
| `--foreground`       | Run in foreground                            |
| `-f, --force`        | Force worktree removal (has untracked files) |

| Flag                    | Scope    | Use when                 |
| ----------------------- | -------- | ------------------------ |
| `--force` (`-f`)        | Worktree | Untracked files present  |
| `--force-delete` (`-D`) | Branch   | Unmerged commits present |

### Branch cleanup criteria (checked in order)

1. Same commit as target → 2. Ancestor of target → 3. Three-dot diff empty → 4. Trees match → 5. Simulated merge tree same as target → 6. Patch-id matches squash-merge on target

### Examples

```bash
wt remove                        # current worktree
wt remove feature-branch
wt remove feature --force        # untracked files
wt remove experimental -D        # force unmerged
wt remove --no-delete-branch feature
```

---

## `wt merge` — merge current → target, then cleanup

Like GitHub "Merge PR" locally, but direction is current **into** target (inverse of `git merge`). Pipeline: commit → squash → rebase → pre-merge hooks → fast-forward merge → pre-remove hooks → remove worktree → post hooks (background).

**Raw:** [`004-merge.md`](../worktrunk-guide-raw/004-merge.md)

### Syntax

```bash
wt merge [OPTIONS] [TARGET]
```

### Flags

| Flag                           | Description                       |
| ------------------------------ | --------------------------------- |
| `--no-squash`                  | Skip squashing commits            |
| `--no-commit`                  | Skip commit + squash              |
| `--no-rebase`                  | Skip rebase onto target           |
| `--no-remove`                  | Keep worktree after merge         |
| `--no-ff`                      | Create merge commit (semi-linear) |
| `--stage <all\|tracked\|none>` | What to stage (default: all)      |

### Examples

```bash
wt merge                 # to default branch
wt merge develop
wt merge --no-remove     # keep worktree
wt merge --no-squash     # preserve history
wt merge --no-ff         # create merge commit
```

### Local CI hook

```toml
# .config/wt.toml
[[pre-merge]]
test = "cargo test"
lint = "cargo clippy"
```

> [!NOTE]
> For `step`-level overrides (`wt step commit` / `squash` / `rebase`) see [operations](operations.md). For hook lifecycle see [automation](automation.md).

---

## Changes since v0.49 → v0.74 (sync 2026-08-25)

Sync to raw `v0.74.0` (2026-08-14). Curated diff highlights — raw is authoritative.

- **`wt switch` accepts full forge URLs** — `wt switch https://github.com/owner/repo/pull/123` ≡ `pr:123`; works for `pr:N`/`mr:N` anywhere incl. `--base`; shape-based `/pull/N` `/merge_requests/N` covers GitHub/GitLab/Gitea/Azure, self-hosted. (0.55)
- **`wt switch -x` without branch** — `wt switch -x claude` opens picker, runs against selection; composes with `--branches`/`--remotes`/`--prs`. (0.67)
- **`--execute` deprecation** — `-x` string now warns; migrate to `--execute sh -- -c '…'` (argv model). (0.53)
- **Picker:** digits → filter (tabs via `Alt-1..5`/`Tab`, 0.59), live CI/review per row + cached PR numbers, `Alt-r` refresh clears preview cache (0.62-0.63), `--prs` streams open PRs/MRs (0.62), gutter `/` local branch vs `|` remote (0.60), `Alt-x` flashes keep reason (0.65)
- **`wt list`:** `main…±` now default (persistent cache) not only `--full` (0.62), `[list] columns` selects/orders built-ins + custom columns (0.62-0.63), narrowed columns run only needed git probes (0.63), `repo_url`/`repo` JSON + `main.diff` always (0.56/0.62)
- **`wt remove`/`prune`:** accepts worktree path anywhere branch accepted (0.70), `⚑` duplicate-branch flag (0.70), `wt remove --reap` kills `cwd` processes (0.67, Unix), `--force` ownership gate requires registration ↔ directory mutual match (0.74)
- **Universal `--config-set <toml>`** for all commands (e.g., `wt --config-set list.full=true list`) (0.61)
- **Bare-repo/unborn handling:** `wt config create --project` guides bare repos, `list`/`prune` degrade gracefully on `--orphan` null OID (0.55-0.56)
