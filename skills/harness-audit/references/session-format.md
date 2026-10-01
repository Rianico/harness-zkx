# Pi Session JSONL Format

Deep reference for `harness-audit`'s scanner. See `SKILL.md` for usage.

## File layout

Sessions live under `~/.pi/agent/sessions/<project-slug>/<timestamp>_<uuid>.jsonl`.
`$PI_SESSIONS_DIR` overrides the root when set. Filenames carry the uuid:

```
2026-09-06T14-48-05-310Z_01a07730-d9be-73cc-b7b1-a8caa2187f49.jsonl
```

One JSON object per line, no outer array.

## Record types

| `type`                                                  | Meaning                                                      |
| ------------------------------------------------------- | ------------------------------------------------------------ |
| `session`                                               | Session metadata (`id`, `cwd`, `timestamp`, `parentSession`) |
| `message`                                               | Conversation turn — inspect `message.role`                   |
| `message_end`                                           | Pi event-stream log (benchmark harness `stdout.jsonl`) — identical `message` payload; treated as `message` |
| `custom_message`                                        | UI/provider-specific payload                                 |
| `model_change`, `thinking_level_change`, `session_info` | Infra events — ignored by the scanner                        |

## Message roles relevant to bash audit

### `assistant` with `toolCall`

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

### `toolResult` for bash

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

## Event-stream logs (benchmark harness)

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

## Delivery cap (produced vs delivered)

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

## Marker scoping caveat

`[E_*]` / `[W_*]` markers must be counted only in `edit` / `write` / `undo_last_edit` results: the codes
also appear verbatim inside `bash`/`read` output (e.g. bundled extension JS), so an unscoped `grep -o`
over a session overcounts. `audit_edits.py` counts markers only inside `edit` results (the narrowest
safe scope).

## Truncation

`truncate_body(text, keep)` keeps `keep` head + `keep` tail lines with a middle marker:

```
… [N lines omitted] …
```

When `keep == 0`, only the marker remains. The filtered variant (`--emit-filtered`) rewrites only oversized `bash` bodies; every other record is serialised unchanged and the output has the same line count. Original file is never mutated.

## Edge cases handled by `audit.py`

- Malformed JSON line → skipped, counted in `parse_errors`.
- Empty lines → preserved.
- Unknown session id → `resolve_session` searches all `*.jsonl` under the roots, matches uuid fragment or full stem, picks newest by `mtime`.
- Missing root → skipped silently; error only when no candidate matches.
- Records read but no bash paired (`record_count > 0`, `bash_count == 0`) → loud schema warning on stderr and exit `3`; a scanner that cannot see must not report clean.
