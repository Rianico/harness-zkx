# One-shot prompt for generating the ensure_todo hook feature

Use this prompt in Claude Code when you want the full ensure_todo hook feature generated in one shot.

```md
Implement a reusable Claude Code hook family under `hooks/ensure_todo/` and wire it through the root `install-hooks.py` installer.

Goal:
- Prevent Claude from stopping when unfinished project tasks remain.
- Run tests immediately after edit-like tool usage.
- Install everything through `uv run install-hooks.py <sub_module> <command> <settings.json>`.

Requirements:
- Create or update these files:
  - `install-hooks.py`
  - `hooks/ensure_todo/install.py`
  - `hooks/ensure_todo/ensure_todo_stop.py`
  - `hooks/ensure_todo/ensure_todo_post_tool_use.py`
  - `hooks/README.md`
- Use Python and run installed scripts with `uv run`.
- Prefer scripts over inline code in `settings.json`.
- Keep source-of-truth files under `hooks/ensure_todo/`.
- Copy runtime scripts into target `.claude/hooks/` during installation.

Installer behavior:
- Root CLI must support:
  - `uv run install-hooks.py ensure_todo install <settings.json>`
  - `uv run install-hooks.py ensure_todo uninstall <settings.json>`
  - `uv run install-hooks.py all install <settings.json>`
  - `uv run install-hooks.py --help`
- Ensure `all` installs every hook family.
- The ensure_todo family installer must be idempotent.

Settings behavior:
- Install a `Stop` hook with:
  - `matcher: "*"`
  - command: `uv run "<absolute target path>/.claude/hooks/ensure_todo_stop.py"`
- Install a `PostToolUse` hook with:
  - `matcher: "Edit|Write|MultiEdit"`
  - command: `uv run "<absolute target path>/.claude/hooks/ensure_todo_post_tool_use.py"`

Stop hook behavior:
- Read JSON payload from stdin.
- Determine project cwd from payload `cwd`.
- Support TODO file lookup in this order:
  1. `CLAUDE_ENSURE_TODO_FILE`
  2. `<cwd>/.claude/tasks/current.md`
  3. `<cwd>/.claude/tasks/plan.md`
  4. `<cwd>/TODO.md`
  5. `<cwd>/CLAUDE.md`
- Parse Markdown checkbox items.
- If unfinished tasks remain, return exactly JSON like:
  - `{"decision":"block","reason":"..."}`
- If everything is done or no task file exists, return:
  - `{"decision":"approve"}`
- Keep the behavior soft-fail for repos without a TODO file.

PostToolUse behavior:
- Read JSON payload from stdin.
- Detect `Edit`, `Write`, and `MultiEdit` activity.
- Extract edited file paths from `tool_input.file_path` and `tool_input.edits[*].file_path`.
- Run tests immediately after edit-like tool usage.
- Resolve test command from `CLAUDE_ENSURE_TODO_TEST_COMMAND`.
- If no test command is configured, print a concise stderr message and exit successfully.
- Never block the tool flow.
- Add a timeout.

README requirements:
- Update `hooks/README.md` as the index for hook families.
- Include `ensure_todo/` in the layout.
- Document unified installer usage for `notify`, `ensure_todo`, and `all`.
- Explain the supported TODO file locations and checkbox format.
- Mention recommended env vars:
  - `CLAUDE_ENSURE_TODO_FILE`
  - `CLAUDE_ENSURE_TODO_TEST_COMMAND`

Verification:
- Run `uv run install-hooks.py --help`
- Run `uv run install-hooks.py ensure_todo install <settings.json>`
- Verify target runtime scripts exist in target `.claude/hooks/`
- Verify `Stop` and `PostToolUse` entries are written correctly
- Verify the Stop hook returns block/approve JSON correctly
- Verify the PostToolUse hook runs the configured test command without blocking
```
