# QoderCLI Agent Reference

Reference for running QoderCLI (`qodercli` / `qoderclicn`) coding agent under Herdr.

## Command & Binary
- Binary: `qodercli` (standard) or `qoderclicn` (China distribution). Both share identical CLI semantics.
- Launch via Herdr: `herdr agent start <name> --kind qodercli --pane <pane_id> -- <args>`

## Folder Trust & Approval
- Folder trust requires interactive confirmation in terminal UI on first launch in an untrusted directory.
- Automated `--approve` flag is not supported for folder trust.
- Operator must confirm trust interactively or send enter key (`herdr agent send-keys <name> enter`) before sending prompts.
- Permission mode bypass after folder trust: `--permission-mode accept_edits` (or consent-gated `--dangerously-skip-permissions`).

## Provider & Model Configuration
- Model flags: `-m <model>` or `--model <model>`.
- Example: `-m deepseek-r1`.

## Session Path & Resume
- Session identifier: managed in local session store.
- Resume command: `qodercli resume` or `qoderclicn resume`.

## Known Quirks & Failure Modes
- Unconfirmed folder trust dialog blocks automated prompt injection.
- Inspect pane startup with `herdr agent read <name> --source recent-unwrapped --lines 20` to verify readiness.
