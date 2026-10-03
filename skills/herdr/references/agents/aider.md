# Aider Agent Reference

Reference for running Aider coding agent under Herdr.

## Command & Binary
- Binary: `aider`
- Launch via Herdr: `herdr agent start <name> --kind aider --pane <pane_id> -- <args>`

## Folder Trust & Approval
- Auto-detects git repository in working directory.
- No interactive folder trust screen.

## Provider & Model Configuration
- Model flag: `--model <model>`.
- Example: `--model anthropic/claude-3-7-sonnet`.

## Session Path & Resume
- Session history file: `.aider.chat.history.md` or `.aider.input.history`.
- Resume command: `aider --restore-chat-history` (or `--chat-history-file <path>`).

## Known Quirks & Failure Modes
- Commits changes automatically unless `--no-auto-commits` is passed.
- Mutates git working tree directly.
