# Environment & Behavior

## 1. Tool Preferences & File Discovery
- **Hard ban for normal repo exploration:** Do NOT use the built-in `Glob` or `Grep` tools for file discovery or content search. Use `Bash` with CLI tools instead.
- **File discovery:** Use `fd` instead of `Glob`, `find`, or shell glob expansion for repository file lists. Example: `fd --glob "*.md" skills`.
- **Content search:** Use `rg` instead of `Grep`, `grep`, `ack`, `ag`, or editor/LSP text search for repository-wide text matching. Example: `rg -n "pattern" skills commands rules`.
- **Structural overview:** Use `eza -T -L 2` for a compact directory TOC before broad exploration.
- **Exception:** Use built-in `Glob`/`Grep` only when a loaded command, skill, or tool contract explicitly requires those exact tools and no Bash-based equivalent is permitted. If using the exception, state why.
- When exploring a project, ALWAYS respect `.gitignore`. Prefer `rg` and `fd` because they naturally align better with fast code search. Manually exclude common ignored directories (like `.venv`, `.git`, `node_modules`, `target`, etc.) when needed. Do not explore or search directories/files listed in `.gitignore` unless explicitly requested by the user.

## 2. Conditional Project Exploration
When executing high-level workflows or commands (such as `/orchestrate`, `/plan`, `/code-review`, `/tdd`, etc.), you should assess your current knowledge of the project.

**Exploration Protocol:**
If exploration is required under the conditions above, you MUST begin with:
1. `eza -T -L 2` (to get a structured 2-level deep overview of the repository so you can decide what to do next)

## 3. Execution Proxy
- The environment uses a hook that proxies Bash commands through `rtk` (Rust Token Killer) to save tokens (e.g., `git status` becomes `rtk git status`).
- This is expected, normal behavior for this repository and should not be modified or bypassed.

## 4. Artifact Storage Convention
All high-level LSZ workflows (Planning, TDD, Architecture, Code Review) that generate markdown reports, specifications, or tracking states MUST store their artifacts in a centralized, standardized directory structure.
- **Base Topic Pattern:** `.lsz/{date}/{topic_creation_time}_{short_topic}/`
- **Workflow Artifact Pattern:** `.lsz/{date}/{topic_creation_time}_{short_topic}/{workflow_kind}/`
  - `workflow_kind`: e.g., `plan`, `tdd`, `architect`, `review`.
  - `date`: `YYYYMMDD` format.
  - `topic_creation_time`: `HHMMSS` captured once when the topic is first created.
  - `short_topic`: lowercase, snake_case descriptor.
- The topic root MUST be created once at topic initialization and then reused by all downstream phases in the same workflow chain.
- Downstream phases MUST NOT generate a fresh timestamp. They MUST inherit the existing topic root and create only their workflow-specific subdirectory.
Always use the Bash tool (`mkdir -p`) to ensure the target directory exists before writing artifacts.
