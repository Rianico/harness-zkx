# Worktrunk Guide — Operations

Source: worktrunk **v0.74.0** (2026-08-14) — <https://github.com/max-sixty/worktrunk>
Raw: `$SKILL_DIR/worktrunk-guide-raw/006-step.md`
Lead: **`step`** — building blocks for `commit` / `squash` / `copy-ignored` / `diff` / `prune` and other per-worktree ops.

> For `switch`/`list`/`remove`/`merge` see [basics](basics.md). For hook lifecycle see [automation](automation.md).

## `wt step`

```bash
wt step <COMMAND>
```

| Subcommand     | Description                                 |
| -------------- | ------------------------------------------- |
| `commit`       | Stage and commit with LLM-generated message |
| `squash`       | Squash commits since branching              |
| `rebase`       | Rebase onto target                          |
| `push`         | Fast-forward target to current branch       |
| `diff`         | Show all changes since branching            |
| `copy-ignored` | Copy gitignored files between worktrees     |
| `eval`         | Evaluate a template expression              |
| `for-each`     | Run command in each worktree                |
| `promote`      | Swap a branch into the main worktree        |
| `prune`        | Remove worktrees merged into default branch |
| `relocate`     | Move worktrees to expected paths            |

Raw: [`006-step.md`](../worktrunk-guide-raw/006-step.md)

---

## `wt step commit`

Stage and commit with LLM-generated message. See [integrations](integrations.md) for LLM setup.

```bash
wt step commit [OPTIONS]
```

| Flag                           | Description                             |
| ------------------------------ | --------------------------------------- |
| `--stage <all\|tracked\|none>` | What to stage (default: all)            |
| `--dry-run`                    | Preview without committing              |
| `-b, --branch <BRANCH>`        | Branch to operate on (default: current) |

| Stage value | Behavior                              |
| ----------- | ------------------------------------- |
| `all`       | Stage all changes including untracked |
| `tracked`   | Stage only modified tracked files     |
| `none`      | Commit only what's already staged     |

```bash
wt step commit                      # LLM message
wt step commit --stage=tracked
wt step commit --dry-run            # preview
```

Default stage in `~/.config/worktrunk/config.toml`:

```toml
[commit]
stage = "tracked"
```

---

## `wt step squash`

Squash commits since branching. Stages changes and generates message with LLM.

```bash
wt step squash [OPTIONS] [TARGET]
```

| Flag                           | Description                             |
| ------------------------------ | --------------------------------------- |
| `--stage <all\|tracked\|none>` | What to stage (default: all)            |
| `--dry-run`                    | Preview without squashing               |
| `[TARGET]`                     | Target branch (default: default branch) |

```bash
wt step squash
wt step squash develop
wt step squash --dry-run
```

---

## `wt step diff`

Show all changes since branching — committed + staged + unstaged + untracked. This is what `wt merge` would include.

```bash
wt step diff [TARGET] [-- EXTRA_ARGS...]
```

```bash
wt step diff
wt step diff -- --stat
wt step diff -- --name-only
wt step diff -- -- '*.rs'
wt step diff | delta
```

---

## `wt step copy-ignored`

Copy gitignored files to another worktree. Eliminates cold starts (caches, dependencies, `.env`). Uses copy-on-write (reflink) — sharing blocks until modified.

```bash
wt step copy-ignored [OPTIONS]
```

| Flag            | Description                                     |
| --------------- | ----------------------------------------------- |
| `--from <FROM>` | Source worktree branch (default: main worktree) |
| `--to <TO>`     | Destination worktree branch (default: current)  |
| `--dry-run`     | Show what would be copied                       |
| `--force`       | Overwrite existing files                        |

What gets copied: all gitignored files except built-in excludes `.bzr/` `.hg/` `.jj/` `.pijul/` `.sl/` `.svn/` `.conductor/` `.entire/` `.worktrees/`

### Filter with `.worktreeinclude`

Only copy files that are **both** gitignored **and** in `.worktreeinclude`:

```text
# .worktreeinclude
.env
node_modules/
target/
```

Additional excludes in config:

```toml
[step.copy-ignored]
exclude = [".cache/", ".turbo/"]
```

```bash
wt step copy-ignored                    # to current
wt step copy-ignored --from main
wt step copy-ignored --dry-run
```

Hook setup:

```toml
# .config/wt.toml
[post-start]
copy = "wt step copy-ignored"
# Use pre-start if --execute needs files immediately
```

> [!NOTE]
> For 14 GB `target/`: `cp -R` ~2 min, `cp -Rc` / `wt step copy-ignored` ~20 s (reflink). Rust `target/` copy cuts first build ~68 s → ~3 s. Node without native deps: symlink `ln -sf {{ primary_worktree_path }}/node_modules .` is faster. Python venvs contain absolute paths — use `uv sync` instead.

---

## `wt step eval`

Evaluate a template expression. Prints to stdout for scripting.

```bash
wt step eval [OPTIONS] <TEMPLATE>
```

```bash
wt step eval '{{ branch | hash_port }}'
curl http://localhost:$(wt step eval '{{ branch | hash_port }}')/health
wt step eval '{{ branch | hash_port }},{{ ("db-" ~ branch) | hash_port }}'
wt step eval --dry-run '{{ branch }}'
```

---

## `wt step for-each`

Run a command in each worktree sequentially with real-time output; continues on failure.

```bash
wt step for-each -- ARGS...
```

```bash
wt step for-each -- git status --short
wt step for-each -- npm install
wt step for-each -- sh -c 'git status | wc -l'
git fetch --prune && wt step for-each -- sh -c 'git rev-parse @{u} 2>/dev/null && git pull --autostash || true'
# Template per worktree:
wt step for-each -- echo 'Branch: {{ branch }}'
```

---

## `wt step prune`

Remove worktrees merged into default branch (same criteria as `wt remove`).

```bash
wt step prune [OPTIONS]
```

| Flag              | Description                                    |
| ----------------- | ---------------------------------------------- |
| `--dry-run`       | Show what would be removed                     |
| `--min-age <AGE>` | Skip worktrees younger than this (default: 1h) |
| `--foreground`    | Run in foreground                              |

Guard: `--min-age` prevents deleting worktrees just created from default (same commit looks "merged").

```bash
wt step prune --dry-run
wt step prune
wt step prune --min-age=0s    # no guard
wt step prune --min-age=2d    # skip < 2 days old
```

---

## `wt step promote`

Swap a branch into the main worktree. Exchanges branches and gitignored files.

```bash
wt step promote [BRANCH]
```

Requirements: both worktrees clean; branch must have existing worktree.

```bash
# From ~/project (main worktree):
wt step promote feature
# Before: main→~/project, feature→~/project.feature
# After:  feature→~/project, main→~/project.feature
# Restore: wt step promote main  or  wt step promote  (from main)
```

---

## `wt step relocate`

Move worktrees to expected paths when `worktree-path` template changed.

```bash
wt step relocate [OPTIONS] [BRANCHES]...
```

| Flag        | Description                                  |
| ----------- | -------------------------------------------- |
| `--dry-run` | Show what would be moved                     |
| `--commit`  | Commit uncommitted changes before relocating |
| `--clobber` | Backup non-worktree paths at target          |

```bash
wt step relocate --dry-run
wt step relocate
wt step relocate feature bugfix
wt step relocate --commit --clobber
```

---

## Changes since v0.49 → v0.74 (sync 2026-08-25)

- **`wt step tether` [experimental] (0.52)** — `wt step tether -- npm run dev` runs in own `process group`, `killpg`/`taskkill /T` on exit/remove; replaces `post-start`+`pre-remove` pair and cleans `git worktree remove`/`rm -rf`/crash leaks ( `fseventsd` ). Args after `--` no shell, like `for-each`
- **`wt step diff --branch/-b` (0.57)** — diff another worktree's branch without `cd`; mirrors `commit --branch`
- **`wt step eval -v` (0.59)** — prints vars gutter `source`/`result`, `--dry-run` removed; result still `stdout`
- **Squash templates:** `{{ commit_details }}` (`{subject,body}`) alongside `{{ commits }}` (0.57), now `commit_details` renders bare subject (0.59); `wt config update` migrates
- **`wt step copy-ignored`**: skips vanishing source file mid-parallel copy (0.74), faster macOS `clonefile` chmod skip (0.61), respects `FICLONE` vs `chmod`
- **`wt step prune`**: bundled parallel scan, streams removals, never mid-scan prompt — unapproved hooks `SKIPPED (approval required)` (0.54), 24 candidates 12s→0.6s concurrent removals + ordered JSON (0.70), reuses scan plan
- **`wt step relocate`**: moves dirty linked worktrees (dirty-skip was policy, `git worktree move` allows) (0.60)
- **`wt step rebase`/`merge` refuse mid-operation** with clear message (0.69), measure squash/rebase span against target upstream not stale local `main` (0.69)
