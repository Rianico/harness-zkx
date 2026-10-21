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
- `pi --help` documents `--model <pattern>`: "Model pattern or ID (supports `"provider/id"` and optional `:<thinking>`)". So `opencode-go/muse-spark-1.3-contributor` and `sonnet:high` are both valid; the provider segment must match a catalog provider key.
- The combined form splits on the first `/`. A model id that itself contains `/` cannot be written this way — pass `--provider` and `--model` separately.
- Verified 2026-10-05: `herdr agent start <name> --kind pi --pane <id> -- --model opencode-go/muse-spark-1.3-contributor --approve` resolved. The session's `model_change` entry records `provider: opencode-go`, `modelId: muse-spark-1.3-contributor`, and the agent ran.
- `herdr` echoes back the raw argument it was given, so `agent start` output is **not** proof the model resolved. Confirm from the session file's `model_change` entry instead.
- The in-session `/model` command is a search picker over catalog models, not an ID field. A model that looks "unrecognized" there is a picker artifact, not a resolution failure; pass `--provider`/`--model` on the command line for an exact choice.

## Session Path & Resume
- Session file format: `~/.pi/agent/sessions/<workspace>/<timestamp>_<uuid>.jsonl`.
- Session kind in Herdr record: `path`.
- Resume command: `pi --session <path|id>` — it takes either the session file or the id, so one form covers both.
  - `--resume`/`-r` is the *value-less picker* ("Select a session to resume"), so `pi --resume <path>` opens the picker and never re-attaches. Verified 2026-10-09 in a non-TTY `--print` run: the path argument was ignored and the session list rendered (#211).
  - `--session-id <id>` creates the session when missing, which is the idempotent form for a bare id.

## Recovery Handles By Kind

Each kind's resume command is built in `herdr_prompt.py:build_resume_cmd`. Only pi's daemon
handle is a file path, so only pi is shortened (`short_session_id`) before it reaches
`context_id` and `resume_cmd`; the full path stays in verbose recovery metadata
(`session_path`).

| Kind | Handle form | Short/long | Verified by |
|---|---|---|---|
| pi | `--session <id>` (id or file both accepted) | short id | 2026-10-20: `pi --session 00000000-… --offline` -> `No session found matching '<id>'` exit 1; `pi --session 01a154f2-…` (real session's id) -> found the session (project-mismatch prompt) exit 0, no model call |
| claude | `--resume <session_id>` | already short (daemon reports the id) | `references/agents/claude.md` "Session Path & Resume"; unchanged by #267 |
| qodercli / qoderclicn | `resume` (latest), or `-r [id]` for a specific session | no path involved | `references/agents/qodercli.md` "Session & Resume" |
| agy | `--conversation=<uuid>` | short uuid | `references/agents/agy.md` "Session Path & Resume" |

The shortening rule is deliberately narrow: a value is rewritten only when its file name is
`<timestamp>_<uuid-v4-shape>.jsonl`. Another kind's handle, an already-short id, or an
unfamiliar path passes through untouched.

## Known Quirks & Failure Modes
- Background completions settle to `done`, not `idle`. Waiting with `--until idle` alone hangs.
- Extract clean assistant text from session files with `uv run skills/herdr/scripts/herdr_transcript.py <target> --last`.
