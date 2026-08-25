# Worktrunk Guide — Patterns

Source: worktrunk **v0.74.0** (2026-08-14) — <https://github.com/max-sixty/worktrunk>
Raw: `$SKILL_DIR/worktrunk-guide-raw/011-tips-patterns.md` · `012-faq.md`
Lead: **`pattern`** — recipes for dev servers, DB isolation, cold-start elimination, validation, and FAQ.

> Hook and template engine: single source is [automation](automation.md). `wt step` building blocks: [operations](operations.md).

## Dev server per worktree

Each worktree runs its own server on deterministic `hash_port`. The `hash_port` filter (see [automation](automation.md)) maps branch → port 10000-19999 stably.

**Raw:** [`011-tips-patterns.md`](../worktrunk-guide-raw/011-tips-patterns.md)

```toml
# .config/wt.toml
[post-start]
server = "npm run dev -- --port {{ branch | hash_port }}"

[list]
url = "http://localhost:{{ branch | hash_port }}"

[pre-remove]
server = "lsof -ti :{{ branch | hash_port }} -sTCP:LISTEN | xargs kill 2>/dev/null || true"
```

`wt list` URL column shows each worktree's server, dimmed when not listening. `fix-auth` always maps to same port (e.g., 16460) across machines.

---

## Database per worktree

Isolated DB per branch via pipeline: first block derives names/ports as vars, second block uses them.

```toml
[[post-start]]
set-vars = """
wt config state vars set \
  container='{{ repo }}-{{ branch | sanitize }}-postgres' \
  port='{{ ('db-' ~ branch) | hash_port }}' \
  db_url='postgres://postgres:dev@localhost:{{ ('db-' ~ branch) | hash_port }}/{{ branch | sanitize_db }}'
"""

[[post-start]]
db = """
docker run -d --rm \
  --name {{ vars.container }} \
  -p {{ vars.port }}:5432 \
  -e POSTGRES_DB={{ branch | sanitize_db }} \
  -e POSTGRES_PASSWORD=dev \
  postgres:16
"""

[pre-remove]
db-stop = "docker stop {{ vars.container }} 2>/dev/null || true"
```

`('db-' ~ branch)` hashes differently than plain `branch`, so DB and dev server ports don't collide.

```bash
DATABASE_URL=$(wt config state vars get db_url) npm start
```

---

## Eliminate cold starts

Copy gitignored caches/deps/env between worktrees.

```toml
[post-start]
copy = "wt step copy-ignored"
```

When another hook needs the copy, sequence with a pipeline:

```toml
[[post-start]]
copy = "wt step copy-ignored"

[[post-start]]
install = "pnpm install"
```

Use `pre-start` instead when `--execute` needs copied files immediately. See [`wt step copy-ignored`](operations.md) for `.worktreeinclude` and performance notes.

---

## Progressive validation

Split checks: fast before each commit, heavy before merge.

```toml
[[pre-commit]]
lint = "npm run lint"
typecheck = "npm run typecheck"

[[pre-merge]]
test = "npm test"
build = "npm run build"
```

`pre-commit` runs on every squash commit during `wt merge`; `pre-merge` runs once after rebase.

---

## Target-specific hooks

Branch on `{{ target }}` to vary by merge destination.

```toml
post-merge = """
if [ {{ target }} = main ]; then
    npm run deploy:production
elif [ {{ target }} = staging ]; then
    npm run deploy:staging
fi
"""
```

`{{ target }}` is the merge destination; `post-merge` runs in target's worktree (or primary if target has none).

---

## Agent handoffs

Spawn a worktree with an agent CLI in background.

**tmux (detached):**

```bash
tmux new-session -d -s fix-auth-bug "wt switch --create fix-auth-bug -x claude -- \
  'The login session expires after 5 minutes. Find and extend the timeout.'"
```

**Zellij (new pane):**

```bash
zellij run -- wt switch --create fix-auth-bug -x claude -- \
  'The login session expires after 5 minutes. Find and extend the timeout.'
```

**cmux (new workspace):**

```bash
cmux new-workspace --command "wt switch --create fix-auth-bug -x claude -- \
  'The login session expires after 5 minutes. Find and extend the timeout.'"
```

Hooks run inside the multiplexer session/pane.

---

## Tmux session per worktree

Each worktree gets its own tmux session with multi-pane layout.

```toml
# .config/wt.toml
[pre-start]
tmux = """
S={{ branch | sanitize }}
W={{ worktree_path }}
tmux new-session -d -s "$S" -c "$W" -n dev

# Create 4-pane layout
tmux split-window -h -t "$S:dev" -c "$W"
tmux split-window -v -t "$S:dev.0" -c "$W"
tmux split-window -v -t "$S:dev.2" -c "$W"

# Start services
tmux send-keys -t "$S:dev.1" 'npm run backend' Enter
tmux send-keys -t "$S:dev.2" 'claude' Enter
tmux send-keys -t "$S:dev.3" 'npm run frontend' Enter

tmux select-pane -t "$S:dev.0"
"""

[pre-remove]
tmux = "tmux kill-session -t {{ branch | sanitize }} 2>/dev/null || true"
```

Attach:

```bash
wt switch --create feature -x 'tmux attach -t {{ branch | sanitize }}'
```

---

## Shell alias for new worktree + agent

```bash
alias wsc='wt switch --create --execute=claude'
wsc new-feature                       # create worktree, run hooks, launch Claude
wsc feature -- 'Fix GH #322'          # runs `claude 'Fix GH #322'`
```

---

## Subdomain routing with Caddy

Clean URLs like `http://feature-auth.myproject.localhost` without ports.

Prerequisites: [Caddy](https://caddyserver.com/docs/install) (`brew install caddy`)

```toml
# .config/wt.toml
[post-start]
server = "npm run dev -- --port {{ branch | hash_port }}"
proxy = """
  curl -sf --max-time 0.5 http://localhost:2019/config/ || caddy start
  curl -sf http://localhost:2019/config/apps/http/servers/wt || \
    curl -sfX PUT http://localhost:2019/config/apps/http/servers/wt -H 'Content-Type: application/json' \
      -d '{"listen":[":8080"],"automatic_https":{"disable":true},"routes":[]}'
  curl -sf -X DELETE http://localhost:2019/id/wt:{{ repo }}:{{ branch | sanitize }} || true
  curl -sfX PUT http://localhost:2019/config/apps/http/servers/wt/routes/0 -H 'Content-Type: application/json' \
    -d '{"@id":"wt:{{ repo }}:{{ branch | sanitize }}","match":[{"host":["{{ branch | sanitize }}.{{ repo }}.localhost"]}],"handle":[{"handler":"reverse_proxy","upstreams":[{"dial":"127.0.0.1:{{ branch | hash_port }}"}]}]}'
"""

[pre-remove]
proxy = "curl -sf -X DELETE http://localhost:2019/id/wt:{{ repo }}:{{ branch | sanitize }} || true"

[list]
url = "http://{{ branch | sanitize }}.{{ repo }}.localhost:8080"
```

---

## FAQ

**Raw:** [`012-faq.md`](../worktrunk-guide-raw/012-faq.md)

### Worktrunk vs plain `git worktree`

Git worktree works but requires manual lifecycle. Worktrunk automates:

- Consistent directory naming and cleanup validation
- Project-specific automation (deps, services)
- Unified status across worktrees (commits, CI, conflicts, changes)

### Shell integration issues

Debug with Worktrunk plugin for Claude Code:

1. Install plugin 2. Ask Claude to debug shell integration — it runs `wt config show`, inspects shell configs, identifies issue.

### Files worktrunk creates

| Category             | Location                             |
| -------------------- | ------------------------------------ |
| Worktree directories | Configured via `worktree-path`       |
| User config          | `~/.config/worktrunk/config.toml`    |
| Project config       | `.config/wt.toml`                    |
| Approvals            | `~/.config/worktrunk/approvals.toml` |
| Metadata/cache       | `.git/wt/`                           |

### What can be deleted

- `wt remove` refuses if uncommitted changes (use `--force` for untracked)
- `git worktree lock` protects precious worktrees
- `-D` force-deletes branches with unmerged changes
- `--no-delete-branch` keeps branch regardless

### Windows support

Core, shell integration, and completion work in Git Bash and PowerShell.

- **Git for Windows required** — hooks use bash syntax
- **`wt switch` picker unavailable** — uses `skim` (no Windows). Use `wt list` + `wt switch <branch>`.

### Default branch detection

Order: 1. Worktrunk cache (`git config worktrunk.default-branch`) → 2. Git cache (remote HEAD) → 3. Remote query (`git ls-remote`) → 4. Local inference (heuristics).

If remote default changed: `wt config state default-branch clear`

### Installation C compilation errors

Without syntax highlighting:

```bash
cargo install worktrunk --no-default-features --features cli
```

Disables bash syntax highlighting in output, keeps core functionality.

---

## Changes since v0.49 → v0.74 (sync 2026-08-25)

- **New doc: Code Signing Policy (0.73)** — `013-code-signing.md` → `$SKILL_DIR/worktrunk-guide-raw/013-code-signing.md` (Windows release binaries, certificate provenance, per-release approval); also `docs/public/.well-known` agent-skills index
- **Dev server / DB:** `{{ remote_repo }}` now for renamed clones; `('db-' ~ branch)|hash_port` still avoids dev/DB collision; `wt step copy-ignored` reflink still 68s→3s Rust, symlink note for Node, `uv sync` for Python venv
- **List recipes:** custom columns now select/order whole table — use `[list] columns` + `custom-columns` templates to build trimmed fast views (narrowed columns skip git probes, 0.63, 36% warm-cache)
- **Prune recipe:** 12s→0.6s for 24 worktrees, ordered JSON, drains queue on first failure (0.70)
