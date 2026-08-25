# Worktrunk Guide — Integrations

Source: worktrunk **v0.74.0** (2026-08-14) — <https://github.com/max-sixty/worktrunk>
Raw: `$SKILL_DIR/worktrunk-guide-raw/009-llm-commits.md` · `010-claude-code.md`
Lead: **`llm`** — LLM-generated commit messages and Claude Code plugin.

## LLM commit messages

Worktrunk builds a templated prompt from diffs and pipes it to an external command via `sh -c`. Integrates with `wt merge`, `wt step commit`, and `wt step squash`.

**Raw:** [`009-llm-commits.md`](../worktrunk-guide-raw/009-llm-commits.md)

### Setup — add to `~/.config/worktrunk/config.toml`

**Claude Code:**

```toml
[commit.generation]
command = "CLAUDECODE= MAX_THINKING_TOKENS=0 claude -p --no-session-persistence --model=haiku --tools='' --disable-slash-commands --setting-sources='' --system-prompt=''"
```

`CLAUDECODE=` clears nesting guard so `claude -p` works inside a Claude Code session. `--no-session-persistence` prevents the commit conversation from polluting `--continue`.

**Codex:**

```toml
[commit.generation]
command = "codex exec -m gpt-5.1-codex-mini -c model_reasoning_effort='low' -c system_prompt='' --sandbox=read-only --json - | jq -sr '[.[] | select(.item.type? == \"agent_message\")] | last.item.text'"
```

Requires `jq`.

**Other tools:**

```toml
# OpenCode
command = "opencode run -m anthropic/claude-haiku-4.5 --variant fast"
# llm
command = "llm -m claude-haiku-4.5"
# aichat
command = "aichat -m claude:claude-haiku-4.5"
```

### How it works

When worktrunk needs a message it renders the template, pipes to `command` via `sh -c`, and uses stdout as the message. Env vars can be set inline before the command.

### Template variables

| Variable               | Description                                   |
| ---------------------- | --------------------------------------------- |
| `{{ git_diff }}`       | Diff content (staged, or combined for squash) |
| `{{ git_diff_stat }}`  | Diff statistics                               |
| `{{ branch }}`         | Current branch name                           |
| `{{ repo }}`           | Repository name                               |
| `{{ recent_commits }}` | Recent commit subjects (style reference)      |
| `{{ commits }}`        | Commits being squashed (squash template only) |
| `{{ target_branch }}`  | Merge target (squash template only)           |

### Custom templates

Override defaults:

```toml
[commit.generation]
command = "llm -m claude-haiku-4.5"

template = """
Write a commit message for this diff. One line, under 50 chars.

Branch: {{ branch }}
Diff:
{{ git_diff }}
"""

squash-template = """
Combine these {{ commits | length }} commits into one message:
{% for c in commits %}
- {{ c }}
{% endfor %}

Diff:
{{ git_diff }}
"""
```

### Template syntax

Minijinja (Jinja2-like):

- **Variables:** `{{ branch }}`, `{{ repo | upper }}`
- **Filters:** `{{ commits | length }}`
- **Conditionals:** `{% if recent_commits %}...{% endif %}`
- **Loops:** `{% for c in commits %}{{ c }}{% endfor %}`
- **Whitespace control:** `{%- ... -%}` strips surroundings

### Branch summaries

With `[commit.generation]` configured and `summary = true`, worktrunk generates one-line branch summaries (changes since default branch).

```toml
[list]
summary = true
```

Shown in `wt switch` picker (preview tab 5) and `wt list --full` Summary column. Cached until diff changes.

### Fallback

Without LLM configured, worktrunk generates deterministic messages from filenames (e.g., "Changes to auth.rs & config.rs").

---

## Claude Code integration

Plugin provides config skill, worktree isolation, and activity markers.

**Raw:** [`010-claude-code.md`](../worktrunk-guide-raw/010-claude-code.md)

### Installation

```bash
wt config plugins claude install        # recommended
# Manual:
claude plugin marketplace add max-sixty/worktrunk
claude plugin install worktrunk@worktrunk
```

### Configuration skill

Skill (markdown) that Claude Code can read — helps with:

- LLM commit setup
- Adding project hooks (`pre-start`, `pre-merge`, `pre-commit`)
- Worktree path templates
- Shell integration debugging

### Activity tracking

Plugin marks Claude sessions in `wt list`:

| Marker | Meaning                     |
| ------ | --------------------------- |
| `🤖`   | Claude is working           |
| `💬`   | Claude is waiting for input |

Manual:

```bash
wt config state marker set "🚧"                      # current branch
wt config state marker set "✅" --branch feature
git config worktrunk.state.feature.marker '{"marker":"💬","set_at":0}'
```

### Worktree isolation

Claude Code agents can run with `isolation: "worktree"`. The plugin's `WorktreeCreate` / `WorktreeRemove` hooks route through `wt switch --create` / `wt remove`, so naming, hooks, and lifecycle stay consistent.

### Statusline

```bash
wt list statusline --format=claude-code   # single-line for Claude Code statusline
# When CI cache stale, fetches from network (~1-2 s)
```

In `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "wt list statusline --format=claude-code"
  }
}
```

When Claude Code passes context-window usage via stdin JSON, a moon-phase gauge appears (full → new moon as context fills).

---

## Changes since v0.49 → v0.74 (sync 2026-08-25)

- **Gemini CLI extension (0.52)** — `gemini extensions install max-sixty/worktrunk`, activity `🤖/💬` via `wt list` like Claude/Codex; manifest at repo root
- **Codex activity markers (0.66)** — Codex-native hooks `🤖`/`💬`; Claude events no longer leak into Codex; OpenCode/Gemini also tracked; Codex no exit event so rests at `💬` until next session
- **LLM commit model bumps:** Codex `gpt-5.1-codex-mini` → `gpt-5.4-mini` (0.56), Claude recommends `MAX_THINKING_TOKENS=0 ... --safe-mode --setting-sources='user'` without `CLAUDECODE=` prefix (old guard removed 0.57)
- **Commit templates:** `{{ commit_details }}` preferred over `{{ commits }}` (0.59), append experimental `appending to prompt` (0.53)
- **Statusline/CI:** CI column now `#3041`/`!3041` linked + review magenta/cyan (0.58), `ci.number`/`ci.review_state` JSON; Claude Code statusline OSC 8 links + dimmed dev-URL until port answers (0.69), rate-limit `1.3×pace(10am–3pm)` Bayesian forecast (0.54)
- **Diagnostics:** `-vv` pointer lists `trace.log`/`subprocess.log`/`diagnostic.md` with gist hint, profile led, `diagnostic.md` bundle (0.54-0.65)
