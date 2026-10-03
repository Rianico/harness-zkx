# Claude Code Agent Reference

Reference for running Claude Code agent under Herdr.

## Command & Binary
- Binary: `claude`
- Launch via Herdr: `herdr agent start <name> --kind claude --pane <pane_id> -- <args>`

## Folder Trust & Approval
- Prompts for workspace trust on initial run in a directory.
- Accepts `--dangerously-skip-permissions` to bypass tool approval prompts (consent-gated; requires explicit user authorization).

## Provider & Model Configuration
- Model flag: `--model <model>`.
- Example: `--model claude-3-7-sonnet`.

## Session Path & Resume
- Session identifier: UUID format.
- Resume command: `claude --resume <session_id>`.

## Known Quirks & Failure Modes
- Prompts for interactive authentication if credentials expired.
- Alternate screen mode clips standard snapshots; read with `herdr agent read <name> --source recent-unwrapped`.
