# Environment & Behavior

## 1. Tool Preferences & File Discovery
- **Hard ban for normal repo exploration:** Do NOT use the built-in `Glob` or `Grep` tools for file discovery or content search. Use `Bash` with CLI tools instead.
- **File discovery:** Use `fd` instead of `Glob`, `find`, or shell glob expansion for repository file lists. Example: `fd --glob "*.md" skills`.
- **Content search:** Use `rg` instead of `Grep`, `grep`, `ack`, `ag`, or editor/LSP text search for repository-wide text matching. Example: `rg -n "pattern" skills commands rules`.
- **Content reading:** NEVER use `cat`, `bat`, or similar CLI tools to read file content — they dump the entire file and bloat context. Use the built-in `Read` tool for targeted reading, or `head`/`tail` for partial inspection when you only need the beginning or end of a file.
- **Combined discovery:** When you need to identify both file paths and their content, chain `rg` and `fd` together: `rg -l "pattern" && fd "pattern"`. This locates files containing the content while also finding files matching the name pattern.
- **Structural overview:** Use `eza -T -L 3 .` for a directory TOC. Use `-L 2` for a compact summary when you already have context.
- **Exception:** Use built-in `Glob`/`Grep` only when a loaded command, skill, or tool contract explicitly requires those exact tools and no Bash-based equivalent is permitted. If using the exception, state why.
- When exploring a project, ALWAYS respect `.gitignore`. Prefer `rg` and `fd` because they naturally align better with fast code search. Manually exclude common ignored directories (like `.venv`, `.git`, `node_modules`, `target`, etc.) when needed. Do not explore or search directories/files listed in `.gitignore` unless explicitly requested by the user.

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

**Continuation Protocol:**
If you already have context but need to re-orient, use `eza -T -L 2` for a compact summary.
