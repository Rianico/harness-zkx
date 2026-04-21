# One-shot prompt for generating the notify hook feature

Use this prompt in Claude Code when you want the full notification hook feature generated in one shot.

```md
Implement a reusable Claude Code notification hook feature in this repository in one shot.

Goal:
- Create a hook family under `hooks/notify/`.
- The feature must install a Claude Code `Notification` hook into a target `settings.json`.
- The installed runtime script must live in the target `.claude/hooks/notify_user.py`.
- The source-of-truth editable files must live in this repo under `hooks/notify/`.

Requirements:
- Create or update these files:
  - `hooks/notify/notify_user.py`
  - `hooks/notify/install.py`
  - `hooks/README.md`
- Do not create extra docs or alternative implementations.
- Use Python and run scripts with `uv run`.
- Prefer editing existing files if they already exist.

Behavior:
- Support Claude Code `Notification` events.
- Install a hook entry under `hooks.Notification` in the target settings file.
- Use matcher `"*"`.
- The installed command must be:
  - `uv run "<absolute path to target .claude/hooks/notify_user.py>"`
- The installer must copy the runtime hook script into the target `.claude/hooks/` directory.
- The installer must support:
  - `install <settings.json>`
  - `uninstall <settings.json>`
  - `--help`
- The installer should append the notification hook if missing and avoid duplicating the same hook entry.
- The uninstall path should remove the matching Notification hook entry and delete the copied runtime script if present.

Runtime notification script requirements:
- Read JSON payload from stdin.
- Use these payload fields when present:
  - `message`
  - `title`
  - `notification_type`
  - `cwd`
  - `hook_event_name`
  - `event_name`
- Derive project name from `cwd` using the final path segment.
- Cross-platform behavior:
  - macOS: use `osascript`
  - Windows: use `powershell`
  - Linux: use `notify-send` when available
- macOS notification pattern must be exactly:
  - `display notification "{msg}" with title "Claude Code" subtitle "{project_name}" sound name "Heroine"`
- On Windows and Linux, include project name and notification type in the displayed message.
- If stdin is not valid JSON, exit cleanly with status 0.
- Do not hard-fail if desktop notification tools are unavailable.

README requirements:
- `hooks/README.md` should act as the index for hook families.
- Mention that each hook family should live in its own subdirectory.
- Mention that installers update a target `settings.json` and copy runtime scripts into target `.claude/hooks/`.
- Document how to use:
  - `uv run hooks/notify/install.py --help`
  - `uv run hooks/notify/install.py install <settings.json>`
  - `uv run hooks/notify/install.py uninstall <settings.json>`
- Include the macOS notification-with-sound `osascript` pattern.

Implementation constraints:
- Keep the change minimal and focused.
- Do not inline giant shell commands in `settings.json`; use the Python runtime script.
- Do not introduce unrelated refactors.
- Do not add comments unless necessary.
- Keep paths and behavior aligned with this repository layout.

Verification:
- After editing, run:
  - `uv run hooks/notify/install.py --help`
- Verify the help text is correct.
- If the target project `.claude/settings.json` exists, install into it and verify the `Notification` hook entry points to `.claude/hooks/notify_user.py`.

Deliverable:
- Make the code changes directly.
- Then provide a concise summary listing the changed files and the verification result.
```
