# GitHub Copilot CLI Reference

Reference for running GitHub Copilot CLI agent under Herdr.

## Command & Binary
- Binary: `github-copilot-cli` (or `copilot`)
- Launch via Herdr: `herdr agent start <name> --kind copilot --pane <pane_id> -- <args>`

## Folder Trust & Approval
- Requires GitHub CLI authentication (`gh auth login`).
- Prompts for interactive confirmation before executing suggested shell commands.

## Provider & Model Configuration
- Provider: GitHub Copilot backend.
- Model flag: `--model <model>` where supported.

## Session Path & Resume
- Session identifier: session handle.
- Resume command: `github-copilot-cli --resume <session_id>`.

## Known Quirks & Failure Modes
- Requires authenticated GitHub session.
- Halts on command confirmation prompts unless non-interactive mode is set.
