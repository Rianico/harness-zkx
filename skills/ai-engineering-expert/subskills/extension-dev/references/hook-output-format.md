# Claude Hook Output Format

Claude Code hooks communicate back to the system via JSON output on stdout.
The output format determines whether information is shown to the user, injected
into the LLM context, or both.

## Quick Reference

| Field | Visibility | Purpose |
|-------|------------|---------|
| `systemMessage` | User + LLM | Visible alert in transcript |
| `additionalContext` | LLM only | Silent context injection |
| `hookSpecificOutput.hookEventName` | System | Required for event-specific fields |

## Output Structure

### Minimal Output (User-Visible Only)
```json
{
  "systemMessage": "[LSP] file.py: 2 error(s), 0 warning(s)"
}
```

### Full Output (Both User + LLM)
```json
{
  "systemMessage": "[LSP] file.py: 2 error(s), 0 warning(s)\n\nError: \"x\" is not defined...",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Error: \"x\" is not defined..."
  }
}
```

## Field Details

### `systemMessage`

**Visibility:** User sees this in the transcript as an attachment.

**Use for:**
- Status alerts user should see
- Diagnostic summaries
- Warnings about operations
- Progress notifications

**Example:**
```bash
jq -n --arg msg "[Hook] Processing complete" '{systemMessage: $msg}'
```

### `additionalContext`

**Visibility:** Injected directly into LLM context window—user does NOT see it.

**Use for:**
- Detailed analysis results
- File metadata
- Code context
- Large data that would clutter UI

**Example:**
```bash
jq -n --arg ctx "File has 500 lines, 10 functions" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: $ctx
  }
}'
```

### Combining Both

For maximum effectiveness, provide both:
- **`systemMessage`** — Short summary for user awareness
- **`additionalContext`** — Full details for LLM to act on

```bash
jq -n \
  --arg summary "[LSP] file.py: 2 error(s)" \
  --arg details "Error: undefined variable at line 10\nError: type mismatch at line 25" \
  '{
    systemMessage: $summary,
    hookSpecificOutput: {
      hookEventName: "PostToolUse",
      additionalContext: $details
    }
  }'
```

## Hook Event Names

Each hook event has specific output fields available:

| Event | `hookEventName` | Special Fields |
|-------|-----------------|----------------|
| PreToolUse | `"PreToolUse"` | `updatedInput`, `permissionDecision` |
| PostToolUse | `"PostToolUse"` | `additionalContext`, `updatedMCPToolOutput` |
| PostToolUseFailure | `"PostToolUseFailure"` | `additionalContext` |
| SessionStart | `"SessionStart"` | `additionalContext`, `initialUserMessage`, `watchPaths` |
| UserPromptSubmit | `"UserPromptSubmit"` | `additionalContext` |
| Notification | `"Notification"` | (uses `systemMessage` only) |

## Bash Implementation Pattern

### Clean JSON Construction with jq

Always use `jq -n` with `--arg`/`--argjson` for safe JSON construction:

```bash
#!/usr/bin/env bash
# PostToolUse hook example

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# ... do work ...

error_count=3
details="Error 1\nError 2\nError 3"
filename=$(basename "$file_path")

# Safe JSON output
jq -n \
  --arg summary "[LSP] $filename: $error_count error(s)" \
  --arg details "$details" \
  '{
    systemMessage: "\($summary)\n\n\($details)",
    hookSpecificOutput: {
      hookEventName: "PostToolUse",
      additionalContext: $details
    }
  }'
```

### Anti-Pattern: Manual JSON Strings

**DON'T do this:**
```bash
# Fragile - breaks if details contains quotes or newlines
echo "{\"systemMessage\": \"$details\"}"
```

**DO this instead:**
```bash
# Safe - jq handles escaping
jq -n --arg d "$details" '{systemMessage: $d}'
```

## Conditional Output

Hooks should be silent when there's nothing to report:

```bash
#!/usr/bin/env bash

# ... process input ...

if [[ "$error_count" -gt 0 ]]; then
  jq -n \
    --arg msg "Found $error_count issue(s)" \
    '{systemMessage: $msg}'
fi

# Exit 0 always - don't block the tool use
exit 0
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success - output is processed |
| 2 | Block tool call (PreToolUse only) - show stderr to model |
| Other | Show stderr to user only, continue |

**Important:** Always exit 0 for PostToolUse hooks to avoid blocking completed operations.

## Real Example: LSP Diagnostics Hook

```bash
#!/usr/bin/env bash
# LSP diagnostics hook for post-edit file checking

set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // empty')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')
cwd=$(echo "$input" | jq -r '.cwd // "'"$(pwd)"'"')

# Only process Edit, Write, MultiEdit on Python files
case "$tool_name" in
    Edit|Write) ;;
    MultiEdit) file_path=$(echo "$input" | jq -r '.tool_input.edits[0].file_path // empty') ;;
    *) exit 0 ;;
esac

[[ -z "$file_path" || "$file_path" != *.py ]] && exit 0

# Skip test directories
case "$file_path" in */tests/*|*/test/*) exit 0 ;; esac

cd "$cwd"

# Send did-change and get diagnostics
uv run llm-lsp-cli lsp did-change "$file_path" >/dev/null 2>&1 || true
json_output=$(uv run llm-lsp-cli lsp diagnostics "$file_path" --format json 2>/dev/null)

# Count errors and warnings
error_count=$(echo "$json_output" | jq '[.items[] | select(.severity_name == "Error")] | length' 2>/dev/null || echo "0")
warning_count=$(echo "$json_output" | jq '[.items[] | select(.severity_name == "Warning")] | length' 2>/dev/null || echo "0")
total=$((error_count + warning_count))

# Only output if there are issues
if [[ "$total" -gt 0 ]]; then
    text_output=$(uv run llm-lsp-cli lsp diagnostics "$file_path" --format text 2>/dev/null)
    filename=$(basename "$file_path")
    summary="[LSP] $filename: $error_count error(s), $warning_count warning(s)"

    jq -n \
        --arg summary "$summary" \
        --arg text "$text_output" \
        '{
            systemMessage: "\($summary)\n\n\($text)",
            hookSpecificOutput: {
                hookEventName: "PostToolUse",
                additionalContext: $text
            }
        }'
fi

exit 0
```

## Gotchas

- **Always use `jq` for JSON** — Manual string construction breaks on special characters
- **`hookEventName` must match event** — The hook system validates this field
- **Exit 0 for PostToolUse** — Non-zero exit doesn't block completed operations but shows stderr
- **`additionalContext` is LLM-only** — User won't see it, only Claude will
- **`systemMessage` is visible** — User sees this in transcript, keep it concise
