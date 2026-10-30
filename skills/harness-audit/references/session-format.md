# Session JSONL Formats (Pi, pi-subagents, qodercli, agy)

Deep reference for `harness-audit`'s scanners. See `SKILL.md` for usage.
All four schemas were verified against real session files on the host. Schemas drift with
agent versions — re-sample before trusting. Today the scripts resolve and parse the Pi root
(`audit.py`, `audit_edits.py`) and, for the edit workload, pi-subagents transcripts beside it
(`audit_edits.py`); the qodercli and agy sections document the shapes for the planned polyglot
scanner ("the scanner" there means that future scanner).

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
| `custom`                                                | Structured side-channel (`customType`: `session-run-time`, `timeline`, `pi-rules.scan`, `permissions`, `btw-thread-entry`, …) — not a conversation turn |
| `context_edit`                                          | Context-window bookkeeping (`targetId`, `replacement`) — not a conversation turn |
| `model_change`, `thinking_level_change`, `session_info` | Infra events — ignored by the scanner                        |

`custom` and `context_edit` were observed on the host in the evidence session; the `customType`
list is drift-prone like every row here — re-sample.

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

### Delivery cap and paging footers (produced vs delivered)

Two tools emit a footer, and they are not interchangeable.

**`bash` delivery cap.** When a bash result exceeds the harness's 50 KB delivery cap the body ends with:

```
[Showing lines 6-84 of 84 (50.0KB limit). Full output: /var/folders/…/pi-bash-<hex>.log]
```

The trailing `(N.NKB limit)` is load-bearing, and `Full output: <path>` points at the untruncated
log. `audit.py`'s `TRUNCATION_FOOTER_RE` (`\[Showing lines (\d+)-(\d+) of (\d+) \(([\d.]+)KB limit\)`)
consumes this footer into the delivery-cap fields: `produced_lines` / `omitted_lines` (delivered =
`len(text.splitlines())`, produced = the `of Z` field), summed per tool and for the session, plus
`truncated_calls`. A pattern ending at `of Z]` matches nothing.

**`read` paging footer.** A paged read result instead ends with:

```
[Showing lines 90-139 of 586. Use offset=140 to continue.]
```

This footer carries no `(N.NKB limit)` and no `Full output:` path, so `TRUNCATION_FOOTER_RE` does
**not** match it and it never feeds `produced_lines` / `omitted_lines`. Read paging is not a delivery
cap — the model asks for the next window with `offset=`. `audit.py` still counts the read result's
delivered lines in `tool_census` (the `read` row), just not as truncation.

Both footers appear in the evidence session; `audit.py` reads only the bash one.

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

## pi-subagents transcript format

Deep reference for `audit_edits.py`'s transcript path. Verified against 22
`*_transcript.jsonl` files in the evidence session on the host. Schemas drift with
pi-subagents versions — re-sample before trusting.

### File layout

pi-subagents writes one transcript per subagent run beside the session directory:

```
<session_dir>/subagent-artifacts/<uuid>_<agent>_transcript.jsonl
```

22 files in the evidence session. `audit_edits.py` auto-discovers
`subagent-artifacts/*_transcript.jsonl` beside the resolved session (opt out with
`--no-transcripts`), or accepts a transcript path directly. One JSON object per line, no outer
array.

### Record types

| `recordType` | Meaning |
| ------------ | ------- |
| `message`    | A turn body — `role` in (`user`, `system`, `assistant`, `toolResult`, `custom`); the body rides both top-level `text` and a nested `message` object |
| `tool_start` | Tool call (`toolName`, `toolCallId`, `argsPayload` JSON string, `argsPreview`) |
| `tool_end`   | Tool completion (`toolName`, `toolCallId`, `isError`) — no text body |

`sourceEventType` is the underlying event name: `initial_prompt`, `message_end`,
`tool_execution_start`, `tool_execution_end`.

Every record also carries `version`, `source`, `runId`, `agent`, `childIndex`, `cwd`, `ts`
(epoch ms), and `timestamp` (ISO-8601). There is **no `type` key**, so the Pi
`type == "message"` predicate matches nothing in a transcript.

### Tool calls and results

`tool_start` (edit example):

```json
{
  "recordType": "tool_start",
  "sourceEventType": "tool_execution_start",
  "runId": "71241daa-138b-4aef-b15e-ba7162b6ab0e",
  "toolCallId": "call_00_vhmjchw123nwewd1wfi6hxf7",
  "toolName": "edit",
  "argsPayload": "{\"file\": \".pi/agent/extensions/skill-router-injector.ts\", \"edits\": [{\"anchor_from\": \"cbo7\", \"anchor_to\": \"cWkw\"}]}",
  "argsPreview": "file=.pi/agent/extensions/skill-router-injector.ts"
}
```

`tool_end` carries the same `toolName` / `toolCallId` plus `isError`, and no body.

The result body rides a **separate** `recordType: message`, `role: toolResult` record — not the
`tool_end`:

```json
{
  "recordType": "message",
  "sourceEventType": "message_end",
  "runId": "71241daa-138b-4aef-b15e-ba7162b6ab0e",
  "role": "toolResult",
  "toolName": "edit",
  "toolCallId": "call_00_e4dumgfuj5jtrbisbgtfqxlr",
  "isError": true,
  "text": "[MODEL] edit[0] (...) failed: [E_FOREIGN_ANCHOR] ...",
  "message": { "role": "toolResult", "toolName": "edit", "toolCallId": "call_00_e4dumgfuj5jtrbisbgtfqxlr", "isError": true, "content": [{ "type": "text", "text": "..." }] }
}
```

Counting rule used by `audit_edits.py` (each result appears twice — once as `tool_end`, once as
`message`):

- call args (`file`, `anchor_from` / `anchor_to`) come from `tool_start.argsPayload`; the assistant
  `message` `toolCall` is a fallback when a transcript omits `tool_start`;
- the result body and error flag come from the `message` / `toolResult` record; `tool_end.isError`
  is the fallback when no message record exists;
- results are keyed by `(runId, toolCallId)`, so the `tool_end` + `message` pair counts exactly once.

### Merge contract and additive keys

Auto-discovery is default-on: a scan of a session file also reads
`subagent-artifacts/*_transcript.jsonl` beside it. `--no-transcripts` opts out and audits
only the resolved file.

A file whose schema is unrecognized is named on stderr, excluded from the counts, and the run
continues. The exit code is `3` **iff no file yielded recognized records** — a single
unrecognized transcript (or an all-unrecognized merge) still exits `3`, so the scanner never
reports clean on nothing seen. One bad file among good ones no longer discards the good signal.

T1 and T3 added these `--json` keys; every pre-existing key is unchanged:

- `transcripts` — the discovered `*_transcript.jsonl` paths (list);
- `transcript_count` — how many were discovered;
- `skipped_files` — unrecognized files excluded from the counts (list);
- `source_file` / `context_key` on each failure and warning — the origin transcript name and a
  `<source_file>:<line>` locator.

The internal `schema_recognized` flag drives the exit-3 decision and is not emitted.

### Marker scoping caveat

The Pi caveat applies with equal force: `[E_*]` / `[W_*]` codes also appear in `read` / `bash`
output. A raw grep finds 16 `[E_*]` occurrences across the evidence transcripts, but only 4 sit
inside `edit` results. `audit_edits.py` counts markers only inside `edit` results.

### Edge cases handled by `audit_edits.py`

- Unknown record shapes (`recordType` absent or unrecognized) → the file's `schema_recognized` flag
  is false; the CLI exits `3` with a schema warning instead of reporting a false clean.
- `tool_end` without a paired `message` / `toolResult` → the `isError` fallback counts the result
  once (empty body, so `E_EMPTY_RESULT`).
- `argsPayload` is a JSON **string**; decode it before reading `file` / `edits`.
- A transcript path already inside `subagent-artifacts/` discovers no siblings, so pointing at one
  file stays scoped.


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
