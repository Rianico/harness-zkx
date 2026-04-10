# Environment & Behavior

## 1. Tool Preferences & File Discovery
- **NEVER use the built-in `Glob` or `Grep` tools**. ALWAYS prefer using general CLI commands like `find`, `ls`, `tree`, and `grep` via the `Bash` tool.
- When exploring a project, ALWAYS respect `.gitignore`. You must manually exclude common ignored directories (like `.venv`, `.git`, `node_modules`, `target`, etc.) when using `find` and `grep`. Do not explore or search directories/files listed in `.gitignore` unless explicitly requested by the user.

## 2. Conditional Project Exploration
When executing high-level workflows or commands (such as `/orchestrate`, `/plan`, `/code-review`, `/tdd`, etc.), you should assess your current knowledge of the project.
You MUST explore the project context first ONLY IF:
- Your current context is empty or very limited.
- You do not have enough information about the project's structure, architecture, or conventions to safely execute the command.
If you already have sufficient context, skip the exploration phase and proceed directly to the task.

**Exploration Protocol:**
When beginning project exploration, MUST start by forcing the use of:
1. `tree -L 2 && ls -l` (to get a structured 2-level deep overview of the repository so you can decide what to do next)

## 3. Execution Proxy
- The environment uses a hook that proxies Bash commands through `rtk` (Rust Token Killer) to save tokens (e.g., `git status` becomes `rtk git status`).
- This is expected, normal behavior for this repository and should not be modified or bypassed.

## 4. Artifact Storage Convention
All high-level ECC workflows (Planning, TDD, Architecture, Code Review) that generate markdown reports, specifications, or tracking states MUST store their artifacts in a centralized, standardized directory structure.
- **Base Directory Pattern:** `.claude/ecc/{date}/{time}_{short_topic}/{workflow_kind}/`
  - `workflow_kind`: e.g., `plan`, `tdd`, `architect`, `review`.
  - `date`: `YYYYMMDD` format.
  - `time`: `HHMMSS` format.
  - `short_topic`: lowercase, snake_case descriptor.
Always use the Bash tool (`mkdir -p`) to ensure the target directory exists before writing artifacts.
