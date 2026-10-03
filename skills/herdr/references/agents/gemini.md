# Gemini CLI Agent Reference

Reference for running Gemini CLI agent under Herdr.

## Command & Binary
- Binary: `gemini`
- Launch via Herdr: `herdr agent start <name> --kind gemini --pane <pane_id> -- <args>`

## Folder Trust & Approval
- Prompts for workspace approval on directory change or initial run.

## Provider & Model Configuration
- Model flag: `--model <model>`.
- Example: `--model gemini-2.5-pro` or `--model gemini-2.5-flash`.

## Session Path & Resume
- Session identifier: stored in local cache.
- Resume command: `gemini --resume <session_id>`.

## Known Quirks & Failure Modes
- Terminal wrapper integration may capture key combinations.
- Verify agent settles to `idle` or `done` before dispatching automated prompts.
