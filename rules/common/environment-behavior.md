# Environment & Behavior

## 1. Tool Preferences & File Discovery

### File System Tools
- **File discovery:** Use `fd` instead of `Glob`, `find`, or shell glob expansion. Example: `fd --glob "*.md" skills`.
- **Content search (text):** Use `rg` instead of `Grep`, `grep`, `ack`, `ag` for text matching. Example: `rg -n "pattern" skills commands rules`.
- **Structural overview:** Use `eza -T -L 3 .` for directory TOC. Use `-L 2` for compact summaries.
- **Hard ban for normal repo exploration:** Do NOT use built-in `Glob` or `Grep` tools. Use `Bash` with CLI tools instead.

### LSP Code Intelligence
Use `llm-lsp-cli` for semantic code navigation when you need definitions, references, call chains, or type information:

- **Definition lookup:** `llm-lsp-cli lsp definition <file> <line> <col>` — find where a symbol is defined
- **Find references:** `llm-lsp-cli lsp references <file> <line> <col>` — all usages of a symbol
- **Call hierarchy:** `llm-lsp-cli lsp incoming-calls` / `outgoing-calls` — who calls this function / what does it call
- **Type and docs:** `llm-lsp-cli lsp hover <file> <line> <col>` — type signature and docstring
- **File structure:** `llm-lsp-cli lsp document-symbol <file> --depth 2` — all symbols in a file
- **Workspace search:** `llm-lsp-cli lsp workspace-symbol "pattern"` — find symbols by name across workspace
- **Diagnostics:** `llm-lsp-cli lsp diagnostics <file>` — type errors, warnings

**Prerequisite:** Ensure daemon is running before LSP operations:
```bash
llm-lsp-cli daemon status || llm-lsp-cli daemon start
```

### Tool Selection Guide
| Task | Tool |
|------|------|
| Find files by name/pattern | `fd` |
| Find text in files | `rg` |
| Find symbol definition | `llm-lsp-cli lsp definition` |
| Find all references to a symbol | `llm-lsp-cli lsp references` |
| Trace call chains | `llm-lsp-cli lsp incoming-calls` / `outgoing-calls` |
| Get type signature/docs | `llm-lsp-cli lsp hover` |
| Understand file structure | `llm-lsp-cli lsp document-symbol` |
| Find symbol by name (workspace-wide) | `llm-lsp-cli lsp workspace-symbol` |

### Reading Content
- **Targeted reading:** Use the built-in `Read` tool — never `cat`/`bat` (they dump entire files and bloat context).
- **Partial inspection:** Use `head`/`tail` when you only need the beginning or end of a file.
- **Specific lines:** Use `sed -n '10,20p' <file>` to extract a line range.

### Exceptions
- Use built-in `Glob`/`Grep` only when a loaded command, skill, or tool contract explicitly requires those exact tools and no Bash-based equivalent is permitted. State why when using the exception.

### Project Respect
When exploring a project, ALWAYS respect `.gitignore`. Prefer `rg` and `fd` because they naturally align with fast code search. Manually exclude common ignored directories (`.venv`, `.git`, `node_modules`, `target`, etc.) when needed. Do not explore or search directories/files listed in `.gitignore` unless explicitly requested.

## 2. Project Exploration Protocols

**Cold Start Protocol:**
When starting to explore a project without prior context:

1. **Confirm your location** — Verify the current working directory and repository context:
   ```
   pwd && git worktree list
   ```
   This prevents operations in the wrong directory (e.g., editing the main repo when you intended to work in a worktree).

2. **Understand the structure** — Get a 3-level overview of the project:
   ```
   eza -T -L 3 .
   ```
   This reveals the project's architecture, key directories, and file organization.

3. **Ensure LSP daemon** — Verify LSP intelligence is available:
   ```
   llm-lsp-cli daemon status || llm-lsp-cli daemon start
   ```

**Continuation Protocol:**
If you already have context but need to re-orient, use `eza -T -L 2` for a compact summary.

**Code Navigation Protocol:**
When you need to understand a specific code area:

1. **Get file structure:** `llm-lsp-cli lsp document-symbol <file> --depth 2`
2. **Find definition:** `llm-lsp-cli lsp definition <file> <line> <col>`
3. **Trace callers:** `llm-lsp-cli lsp incoming-calls <file> <line> <col>`
4. **Check references:** `llm-lsp-cli lsp references <file> <line> <col>`

This replaces grep-based searches when you need semantic understanding rather than text matching.
