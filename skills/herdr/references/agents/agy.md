# Antigravity (agy) Agent Reference

Reference for running Antigravity (agy) agent under Herdr.

## Command & Binary
- Binary: `agy`
- Launch via Herdr: `herdr agent start <name> --kind agy --pane <pane_id> -- <args>`

## Folder Trust & Approval
- Configured via Antigravity configuration (`~/.gemini/config/`).
- Permission hooks managed via `herdr_agy_bridge.py`.

## Provider & Model Configuration
- Model flag: `--model <model>`.
- Example: `--model gemini-2.5-pro`.

## Session Path & Resume
- Session identifier: UUID format, located in `~/.gemini/antigravity-cli/brain/<uuid>`.
- Resume command: `agy --conversation=<uuid>`.

## Known Quirks & Failure Modes
- Weakly recognized: stays at revision 0, reports `idle` while background subagents run.
- `herdr-wait` barrier fails fast with exit 2 on revision 0.
- Dispatch & Yield (`herdr-dispatch` / `herdr-reply`) is required; never barrier-wait agy panes.
- Install OSC 0 lifecycle hooks using `herdr_agy_bridge.py --install`.
