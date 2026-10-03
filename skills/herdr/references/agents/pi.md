# Pi Agent Reference

Reference for running Pi coding agent under Herdr.

## Command & Binary
- Binary: `pi`
- Launch via Herdr: `herdr agent start <name> --kind pi --pane <pane_id> -- <args>`

## Folder Trust & Approval
- Pass `--approve` (or `-a`) after `--` to trust project-local files and skip interactive approval prompts.
- Prevents UI blocking during automated task execution.

## Provider & Model Configuration
- Provider and model flags: `--provider <name> --model <model>` or `--model <provider>/<model>`.
- Example: `--provider anthropic --model claude-3-7-sonnet`.

## Session Path & Resume
- Session file format: `~/.pi/agent/sessions/<workspace>/<timestamp>_<uuid>.jsonl`.
- Session kind in Herdr record: `path`.
- Resume command:
  - If session path ends with `.jsonl`: `pi --resume <path>`
  - If session is an ID: `pi --session <session_id>`

## Known Quirks & Failure Modes
- Background completions settle to `done`, not `idle`. Waiting with `--until idle` alone hangs.
- Extract clean assistant text from session files with `herdr_transcript.py <target> --last`.
