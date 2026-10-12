# Session JSONL Formats (Pi, qodercli, agy)

Deep reference for `harness-audit`'s scanner. See `SKILL.md` for usage.
All three schemas were verified against real session files on the host. Schemas drift with
agent versions — re-sample before trusting. Today the scripts resolve and parse only the Pi
root; the qodercli and agy sections document the shapes for the planned polyglot scanner
("the scanner" there means that future scanner).

## Pi Session JSONL Format

### File layout

Sessions live under `~/.pi/agent/sessions/<project-slug>/<timestamp>_<uuid>.jsonl`.
`$PI_SESSIONS_DIR` overrides the root when set. Filenames carry the uuid:

```
2026-09-06T14-48-05-310Z_01a07730-d9be-73cc-b7b1-a8caa2187f49.jsonl
```

One JSON object per line, no outer array.

### Record types

| `type`                                                  | Meaning                                                      |
| ------------------------------------------------------- | ------------------------------------------------------------ |
| `session`                                               | Session metadata (`id`, `cwd`, `timestamp`, `parentSession`) |
| `message`                                               | Conversation turn — inspect `message.role`                   |
| `message_end`                                           | Pi event-stream log (benchmark harness `stdout.jsonl`) — identical `message` payload; treated as `message` |
| `custom_message`                                        | UI/provider-specific payload                                 |
| `model_change`, `thinking_level_change`, `session_info` | Infra events — ignored by the scanner                        |

### Message roles relevant to bash audit

#### `assistant` with `toolCall`

```json
{
  "type": "message",
  "message": {
    "role": "assistant",
    "content": [{ "type": "toolCall", "id": "call_01a03e51...", "name": "bash", "arguments": { "command": "rg -n ... 2>&1 | head -100" } }]
  }
}
```

Only `name == "bash"` is collected. The `id` is stored to pair with the result.

#### `toolResult` for bash

```json
{
  "type": "message",
  "message": {
    "role": "toolResult",
    "toolCallId": "call_01a03e51...|fc_01a03e51...",
    "toolName": "bash",
    "content": [{ "type": "text", "text": "actual stdout/stderr\n..." }],
    "isError": false
  }
}
```

- `toolCallId` may be `"<callId>|<fcId>"`. The scanner matches exact id, then falls back to the prefix before `|` and finally the suffix — covering Pi's id-mapping variants across provider bridges.
- `content` is usually a single-element list with `type: "text"`. Text is joined across all such entries. The scanner ignores non-text content.
- Line count is `len(text.splitlines())` (handles trailing newline; empty text = 0).
- Only `toolName == "bash"` feeds the oversized table and `total_lines`; every tool still contributes to `tool_census` (printed by `--census`), so `read` / `edit` / `write` / `undo_last_edit` line counts are available rather than skipped.

### Event-stream logs (benchmark harness)

The harness logs each trial as `rounds/<n>/agent/stdout.jsonl` in the **Pi event-stream** schema
(`message_start` / `message_update` / `message_end`, `tool_execution_start|update|end`), not the
reference `type=message` schema. Only `message_end` carries the canonical turn:

```json
{
  "type": "message_end",
  "message": {
    "role": "toolResult",
    "toolCallId": "call_01a03e51...|fc_01a03e51...",
    "toolName": "bash",
    "content": [{ "type": "text", "text": "actual stdout/stderr\n..." }],
    "isError": false
  }
}
```

`message_end → message` is lossless for the scanners, so it is accepted directly (no normalizer
needed). `tool_execution_end` carries the same `result.content` but is not used.

### Delivery cap (produced vs delivered)

When a tool result exceeds the harness's 50 KB delivery cap the body ends with:

```
[Showing lines 1-100 of 4213 (50.0KB limit). Use offset=101 to continue]
```

`audit.py` parses that footer into `produced_lines` / `omitted_lines` (delivered = `len(text.splitlines())`,
produced = the `of Z` field) and sums them per tool and for the session. The trailing `(N.NKB limit)` is
load-bearing — a pattern ending at `of Z]` matches nothing.

Output shape: the default text report gains one summary line —
`Produced but not delivered (delivery cap): N lines omitted across M tool results, all tools` — **only
when at least one result was capped**. A truncation-free session's text report is byte-identical to the
pre-census version; `--json` always carries `total_produced_lines` / `total_omitted_lines` /
`truncated_count` / `tool_census`.

### Marker scoping caveat

`[E_*]` / `[W_*]` markers must be counted only in `edit` / `write` / `undo_last_edit` results: the codes
also appear verbatim inside `bash`/`read` output (e.g. bundled extension JS), so an unscoped `grep -o`
over a session overcounts. `audit_edits.py` counts markers only inside `edit` results (the narrowest
safe scope).

### Truncation

`truncate_body(text, keep)` keeps `keep` head + `keep` tail lines with a middle marker:

```
… [N lines omitted] …
```

When `keep == 0`, only the marker remains. The filtered variant (`--emit-filtered`) rewrites only oversized `bash` bodies; every other record is serialised unchanged and the output has the same line count. Original file is never mutated.

### Edge cases handled by `audit.py`

- Malformed JSON line → skipped, counted in `parse_errors`.
- Empty lines → preserved.
- Unknown session id → `resolve_session` searches all `*.jsonl` under the roots, matches uuid fragment or full stem, picks newest by `mtime`.
- Missing root → skipped silently; error only when no candidate matches.
- Records read but no bash paired (`record_count > 0`, `bash_count == 0`) → loud schema warning on stderr and exit `3`; a scanner that cannot see must not report clean.

## qodercli (QoderCN CLI) session format

Verified against real files on the host (`version: "1.1.64"`).

### File layout

Sessions live under `~/.qoder-cn/projects/<cwd-slug>/<session-uuid>.jsonl`.
`<cwd-slug>` is the absolute cwd with every non-alphanumeric separator replaced by `-`
(a leading `-` for the root slash), e.g. `/Users/me/dev/app` → `-Users-me-dev-app`.
The stem is the bare uuid, no timestamp prefix:

```
a90a4492-cebb-4a17-a27c-00d07a341876.jsonl
```

A sibling directory `<session-uuid>/` holds session state (`state.json`, `compression-v2`).
One JSON object per line, no outer array. Records form a tree via `uuid` / `parentUuid`.

### Record types

| `type`                        | Meaning                                                                                          |
| ----------------------------- | ------------------------------------------------------------------------------------------------ |
| `user`                        | Conversation turn — `message.content` string (human) or blocks incl. `tool_result`                |
| `assistant`                   | Model turn — `message.content` blocks: `thinking`, `text`, `tool_use`                             |
| `system`                      | CLI notices (`subtype`, `content`, `level`) — ignored by the scanner                              |
| `attachment`                  | Injected context (e.g. `attachment.type: "skill_listing"`) — not a conversation turn             |
| `active-leaf`                 | Branch pointer (`leafUuid`); a session can have many — resume branches share one file            |
| `runtime-config`              | `model`, `contextWindow`, `reasoningEffort` at session start                                     |
| `workspace-directories`       | Root `directories` list                                                                            |
| `worktree-state`, `ai-title`, `last-prompt`, `file-history-snapshot` | Infra/bookkeeping — ignored by the scanner |

Conversation records (`user`, `assistant`, `system`, `attachment`) carry `sessionId`, `cwd`,
`timestamp` (ISO-8601), `gitBranch`, `version`, `entrypoint`, `isSidechain`, `userType`.
`user` records also carry `permissionMode`, `promptId`, `origin.kind` (e.g. `"human"`),
and — when the turn is a tool result — `sourceToolAssistantUUID`. `isSidechain: true` marks
subagent records; filter on it if you only audit the main lane.

### Message roles relevant to bash audit

qodercli uses Anthropic-style content blocks. Tool names are `Bash`, `Read`, `Edit`,
`Write`, `Skill` (capitalised — Pi uses lowercase).

#### `assistant` with `tool_use`

```json
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": [{ "type": "tool_use", "id": "call_711bd45c...", "name": "Bash",
                  "input": { "command": "git rev-parse HEAD && ...", "description": "Verify repo revision" } }]
  }
}
```

`Bash` `input` keys: `command`, `description`, optional `dir_path`, `timeout`,
`run_in_background` (only the first four observed on-host; the last exists in tool docs).
Only `name == "Bash"` is collected. The `id` pairs with the result.

#### `tool_result` for Bash

The result arrives as the next `user` record:

```json
{
  "type": "user",
  "message": { "role": "user",
    "content": [{ "type": "tool_result", "tool_use_id": "call_711bd45c...",
                  "content": "568bb0d4...\n?? tmp/\n..." }] },
  "toolUseResult": { "kind": "completed", "stdout": "568bb0d4...\n...", "stderr": "",
                     "exitCode": 0, "signal": null, "interrupted": false,
                     "isImage": false, "telemetryExecutionId": "bb5101ba-..." }
}
```

Pairing and extraction differences from Pi:

- Match `tool_result.tool_use_id` to the call's `tool_use.id` — exact match only, no `|` id variants.
- The result block has **no tool name**. Get `name` from the paired `tool_use` record
  (`sourceToolAssistantUUID` also points at the assistant record).
- `tool_result.content` is usually a plain string (delivered text), sometimes a block list;
  fall back to joining `type: "text"` entries when it is a list.
- `toolUseResult` is the structured twin: for Bash it carries full `stdout` / `stderr` /
  `exitCode`. Prefer `content` for the delivered-line count (what the model actually saw);
  use `toolUseResult.stdout` when you need produced-vs-delivered distinction.
- Non-Bash results have their own `toolUseResult` shape (e.g. Skill: `{commandName, status,
  success}`); unknown shapes should not crash the census — treat them as text-less entries.

### Edge cases specific to qodercli

- A crash-recovered session reuses one file across branches: multiple `active-leaf` records,
  orphaned `tool_use` without a paired result (interrupted turn). Count unpaired calls, never guess.
- `permissionMode` / `origin.kind` are audit-relevant (auto-approved vs human input) but do not gate scanning.
- Ids are `call_<hex>`; unlike Pi there is no `<fcId>` bridge variant.

## agy (Antigravity CLI) transcript format

Verified against real files on the host.

### File layout

Transcripts live under `~/.gemini/antigravity-cli/brain/<uuid>/.system_generated/`:

```
logs/transcript.jsonl        ← step log, fields may be truncated
logs/transcript_full.jsonl   ← same schema, lossless
```

`<uuid>` is the session/brain id (also the task id prefix). Sibling dirs:
`subagents/` (one `.json` per subagent), `messages/`, `steps/`, `tasks/`, `chunks/`.
Audit the main lane from `transcript*.jsonl`; subagent transcripts are separate files.

One JSON object per line. **Use `transcript_full.jsonl` for produced-vs-delivered audits**:
in `transcript.jsonl`, any record whose `truncated_fields` list is non-empty (observed:
`content`, `thinking`, `tool_calls`) has that field silently cut off — no footer marker.

### Record types

| `type`            | `source` values                        | Meaning                                                        |
| ----------------- | -------------------------------------- | -------------------------------------------------------------- |
| `USER_INPUT`      | `USER_EXPLICIT`                        | User prompt (`content` string, wrapped in `<USER_REQUEST>`)    |
| `PLANNER_RESPONSE`| `MODEL`                                | Model step: `thinking`, `content`, `tool_calls[]`              |
| `GENERIC`         | `MODEL`                                | Either a plain model text step or a **tool result** (see below)|
| `SYSTEM_MESSAGE`  | `SYSTEM`                               | System notices, subagent/task completions (`content` string)   |

Every record carries `step_index` (monotonic), `status` (`DONE`, or `RUNNING` for the
in-flight step), `created_at` (ISO-8601). There is no session id, cwd, or uuid field;
the directory name is the id. `tool_calls[].args` values are JSON-encoded strings with
extra quotes (e.g. `"\"ls -ld ~\""`); unescape before comparing commands.

### Steps relevant to bash audit

Observed tool names: `run_command`, `view_file`, `write_to_file`, `manage_task`,
`invoke_subagent`, `manage_subagents`. There are **no message roles and no call ids** —
the log is a flat step sequence.

#### Model step with a tool call (`PLANNER_RESPONSE`)

```json
{ "step_index": 3, "source": "MODEL", "type": "PLANNER_RESPONSE", "status": "DONE",
  "tool_calls": [{ "name": "run_command",
    "args": { "CommandLine": "\"ls -ld ~/.agents/skills/herdr\"", "Cwd": "\"/path\"",
              "WaitMsBeforeAsync": "5000", "toolSummary": "\"Check symlink\"" }] } }
```

`run_command` args keys: `CommandLine`, `Cwd`, `WaitMsBeforeAsync`, `toolAction`,
`toolSummary`. Only `name == "run_command"` feeds the bash table.

#### Tool result (`GENERIC`)

The result is the next `GENERIC` / `MODEL` record **without** `tool_calls`:

```json
{ "step_index": 4, "source": "MODEL", "type": "GENERIC", "status": "DONE",
  "content": "Created At: ...\nCompleted At: ...\n\nThe command exited with code 0.\nOutput:\n..." }
```

Pairing and extraction differences from Pi and qodercli:

- Pairing is **positional**: a step carrying `tool_calls` is followed by one result step per
  call, in list order. There is no id to match. A step with several `tool_calls` makes the
  1:1 mapping ambiguous — record the pairing count and flag it rather than guessing.
- The tool name exists only on the call side; carry it over positionally.
- Command output is prose inside `content` (`The command exited with code N.\nOutput:`);
  parse the exit code from that header if you need it. Line count = `splitlines()` of `content`.
- `view_file` results are also `GENERIC` steps with formatted file bodies — census-able the
  same way once you know which tool produced them.

### Edge cases specific to agy

- `status: "RUNNING"` steps are partial writes; skip or re-read (the log is append-live during a session).
- Truncated `content` in `transcript.jsonl` undercounts: audit against `transcript_full.jsonl`, or accept the truncation and say so.
- A dead/resumed session may leave a `tool_calls` step with no following result step — count unpaired calls.
- `SYSTEM_MESSAGE` steps carry subagent output inside `content`, which can embed `[E_*]`-style markers; the Pi marker-scoping caveat applies with equal force.
