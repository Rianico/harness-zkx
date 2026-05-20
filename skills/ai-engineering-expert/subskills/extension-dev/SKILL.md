---
name: extension-dev
description: MCP server patterns, hook development, language selection, output format, and transport decisions for the LSZ architecture.
metadata:
  managed-by: ai-engineering-expert
---

# Extension Development

Designing MCP servers and hooks that integrate with the LSZ architecture.

## MCP Server Patterns

**Core Concepts**
- **Tools**: Actions the model can invoke (e.g., search, run command)
- **Resources**: Read-only data the model can fetch (e.g., file contents, API responses)
- **Prompts**: Reusable, parameterized prompt templates
- **Transport**: stdio (local clients) vs Streamable HTTP (remote/Cursor/cloud)

**Best Practices**
- Schema-first: Define input schemas for every tool
- Structured errors: Return messages the model can interpret
- Idempotency: Prefer idempotent tools for safe retries
- SDK versioning: Pin version, check release notes on upgrade

[Full details: mcp-server-patterns.md](references/mcp-server-patterns.md)

## Hook Development

**Language Selection**
- **Bash**: High-frequency hooks (>10/session), simple I/O, no dependencies
- **Python**: Complex logic (>50 lines), external libs, stateful operations
- **Hybrid**: Bash entrypoint + Python helper when both matter

**Output Format**
- **`systemMessage`**: User-visible alert in transcript
- **`additionalContext`**: LLM-only context injection (silent to user)
- **`hookSpecificOutput.hookEventName`**: Required for event-specific fields

**Decision Drivers**
- Frequency: Python startup ~50-100ms; Bash ~5-10ms
- Complexity: Bash with `jq` matches Python for simple JSON transforms
- Dependencies: Python ecosystem justifies overhead when needed

[Language selection: hook-language-selection.md](references/hook-language-selection.md)
[Output format: hook-output-format.md](references/hook-output-format.md)
