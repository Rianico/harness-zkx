# Cline Agent Reference

Reference for running Cline CLI agent under Herdr.

## Command & Binary
- Binary: `cline`
- Launch via Herdr: `herdr agent start <name> --kind cline --pane <pane_id> -- <args>`

## Folder Trust & Approval
- Interactive configuration prompt on initial execution.
- Prompts for directory read/write permissions.

## Provider & Model Configuration
- Provider and model flags: `--model <model>`, `--api-provider <provider>`.
- Example: `--api-provider openrouter --model anthropic/claude-3.7-sonnet`.

## Session Path & Resume
- Session identifier: task ID located in `~/.cline/tasks/<task_id>`.
- Resume command: `cline --resume <task_id>`.

## Known Quirks & Failure Modes
- Requires API credentials configured in environment or settings before launch.
- Halts at interactive onboarding if initial config is absent.
