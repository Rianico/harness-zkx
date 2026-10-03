# Cursor Agent Reference

Reference for running Cursor coding agent under Herdr.

## Command & Binary
- Binary: `cursor-agent`
- Launch via Herdr: `herdr agent start <name> --kind cursor --pane <pane_id> -- <args>`

## Folder Trust & Approval
- Inherits workspace trust from Cursor editor settings.

## Provider & Model Configuration
- Model flag: `--model <model>`.
- Example: `--model claude-3-7-sonnet`.

## Session Path & Resume
- Session identifier: Cursor workspace session handle.
- Resume command: `cursor-agent --resume <session_id>`.

## Known Quirks & Failure Modes
- Requires headless agent bridge or background daemon.
- Dependent on active editor daemon connection.
