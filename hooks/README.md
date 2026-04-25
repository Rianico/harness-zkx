# Hooks

This directory is the index for reusable Claude Code hook helpers.

## Layout

- `notify/`
  - Notification hook utilities
  - current scripts:
    - `hooks/notify/install.py`
    - `hooks/notify/notify_user.py`
    - installed through `install-hooks.py notify ...`
- `ensure_todo/`
  - Stop hook + PostToolUse test runner utilities
  - current scripts:
    - `hooks/ensure_todo/install.py`
    - `hooks/ensure_todo/ensure_todo_stop.py`
    - `hooks/ensure_todo/ensure_todo_post_tool_use.py`
    - installed through `install-hooks.py ensure_todo ...`

Add future hook families as their own subdirectories under `hooks/`.

## Quick guideline

- Group each hook family in its own subdirectory.
- Keep family-specific install logic in `hooks/<family>/install.py`.
- Use the root `install-hooks.py` as the user-facing installer entrypoint.
- Installers should update a target Claude Code `settings.json` and copy any runtime hook scripts or assets into a family-specific target `.claude/hooks/<family>/` directory.
- Keep source scripts in `hooks/<family>/` as the canonical editable versions.
- When the command is complex, use a script rather than inline code in `settings.json`.

## Unified installer usage

Show help:

```bash
uv run install-hooks.py --help
```

Install one hook family:

```bash
uv run install-hooks.py notify install <settings.json>
uv run install-hooks.py ensure_todo install <settings.json>
```

Install all hook families:

```bash
uv run install-hooks.py all install <settings.json>
```

Uninstall one hook family:

```bash
uv run install-hooks.py notify uninstall <settings.json>
uv run install-hooks.py ensure_todo uninstall <settings.json>
```

Uninstall all hook families:

```bash
uv run install-hooks.py all uninstall <settings.json>
```

Examples:

```bash
uv run install-hooks.py notify install ~/.claude/settings.json
uv run install-hooks.py ensure_todo install ~/.claude/settings.json
uv run install-hooks.py all install /path/to/project/.claude/settings.json
```

## ensure_todo behavior

The `ensure_todo` family installs:
- a `Stop` hook that checks for unfinished Markdown checkbox tasks
- a `PostToolUse` hook that runs a configured test command after `Edit`, `Write`, and `MultiEdit`

TODO file lookup order:
1. `CLAUDE_ENSURE_TODO_FILE`
2. `.claude/tasks/current.md`
3. `.claude/tasks/plan.md`
4. `TODO.md`
5. `CLAUDE.md`

Supported task format:

```md
- [ ] open task
- [x] done task
* [ ] another open task
```

Recommended env vars:

```bash
export CLAUDE_ENSURE_TODO_FILE=/absolute/path/to/.claude/tasks/current.md
export CLAUDE_ENSURE_TODO_TEST_COMMAND='uv run pytest'
```

## macOS notification with sound

The notify hook uses this `osascript` pattern on macOS:

```bash
osascript -e 'display notification "{msg}" with title "Claude Code" subtitle "{project_name}" sound name "Heroine"'
```
