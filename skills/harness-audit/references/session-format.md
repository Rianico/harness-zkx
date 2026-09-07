# Pi Session JSONL Format

Deep reference for `harness-audi`'s scanner. See `SKILL.md` for usage.

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
- Only `toolName == "bash"` is measured — other tools (`read`, `edit`, `write`, etc.) are skipped even when large.

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
