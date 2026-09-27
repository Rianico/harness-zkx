# Coding Agent Bootstrap & Trust Reference

Depth for `$SKILL_DIR/SKILL.md`. Details bootstrap commands, folder trust behaviors, provider/model flags, and pre-orchestration user confirmation protocols for coding agents running under Herdr.

---

## 1. Pre-Orchestration Confirmation Protocol

Before starting any agent, creating task panes, or launching workflows, the orchestrator **MUST** explicitly confirm with the user the mapping of roles to coding agent kinds, providers, and models.

Never assume or default to a specific agent kind, provider, or model.

### Information Required from User
1. **Roles needed**: e.g., Task Manager (TM), Implementer, Reviewer, Researcher.
2. **Agent kind (`--kind`) per role**: e.g., `pi`, `qoderclicn` / `qodercli`, `claude`, `agy`.
3. **Provider and model per role**: e.g., `pi` with `--provider anthropic --model claude-3-7-sonnet`, `qoderclicn` with `-m qwen-max`, `claude` with `--model claude-3-7-sonnet`.

### Standard Confirmation Template

Ask the user using the following structure:

```markdown
Before provisioning Herdr lanes and launching agents, please confirm the role configuration:

| Role | Agent Kind (`--kind`) | Provider | Model | Native Flags |
|---|---|---|---|---|
| Task Manager | pi | anthropic | claude-3-7-sonnet | `--approve` |
| Implementer | qodercli | custom | deepseek-r1 | `--permission-mode accept_edits` |
| Reviewer | pi | google | gemini-2.5-pro | `--approve` |

Please approve this configuration or provide desired overrides for agent kind, provider, or model.
```

---

## 2. Agent Bootstrap Matrix

| Kind | Command / Binary | Folder Trust / Approval Behavior | Provider & Model Flags | Key Quirks |
|---|---|---|---|---|
| `pi` | `pi` | Supports `--approve` (`-a`) to trust project-local files and skip interactive trust prompts. | `--provider <name>`, `--model <pattern>` (or `<provider>/<model>`) | Structured JSONL session files in `~/.pi/agent/sessions/`. |
| `qoderclicn` / `qodercli` | `qodercli` / `qoderclicn` | **Requires trusting the folder in terminal UI**. If untrusted, displays an interactive terminal trust prompt. Automated `--approve` flag is **NOT** supported for folder trust. Operator must confirm trust interactively in terminal or via `herdr agent send-keys` before prompting. | `-m`, `--model <model>` | Permission bypass via `--permission-mode accept_edits` (or `--dangerously-skip-permissions` if authorized). |
| `claude` | `claude` | Prompts on first run in folder; accepts `--dangerously-skip-permissions` (consent-gated). | `--model <model>` | Interactive auth/login check on startup. |
| `agy` | `agy` | Standard project trust configuration. | `--model <model>` | Weakly recognized in some versions (revision 0, no session path); status bar may read `WORKING` while settled. |
| `gemini` | `gemini` | Workspace approval on directory change. | `--model <model>` | Terminal wrapper integration. |
| `cursor` | `cursor-agent` | Workspace trust inheritance. | `--model <model>` | GUI/agent bridge dependency. |
| `cline` | `cline` | Interactive configuration on first run. | Config file / `--model <model>` | Custom API endpoint mapping. |
| `copilot` | `github-copilot-cli` | GitHub CLI auth token required. | Default model endpoint | Interactive confirmation required. |
| `aider` | `aider` | Git repo auto-detection; no interactive trust screen. | `--model <model>` | Modifies git index directly if git repo detected. |

---

## 3. Agent Details & Startup Commands

Flags before `--` belong to Herdr (`herdr agent start <name> --kind <kind> --pane <pane_id>`). All native agent arguments must follow `--`.

### `pi`
- **Trust Behavior**: Pass `--approve` (or `-a`) after `--` to trust project-local files, preventing interactive confirmation prompts.
- **Provider & Model**: `--provider <provider> --model <model>` or `--model <provider>/<model>`.
- **Startup**:
  ```bash
  herdr agent start worker-1 --kind pi --pane w1:p2 -- --approve --provider anthropic --model claude-3-7-sonnet
  ```
- **Quirks**: Session records exist in `~/.pi/agent/sessions/<workspace>/<timestamp>_<uuid>.jsonl`. Clean session extraction available via `herdr-transcript`.

### `qoderclicn` / `qodercli`
- **Trust Behavior**: **Folder trust is interactive**. When launching in an untrusted directory, `qoderclicn` halts at a terminal confirmation dialog ("Do you trust the authors of the files in this folder?"). It does **NOT** accept `--approve` for folder trust. The operator or orchestrator must confirm trust in the terminal UI or send confirmation keys (`herdr agent send-keys <name> enter`) before sending prompts.
- **Permission Mode**: Once the folder is trusted, pass `--permission-mode accept_edits` to allow tool execution without per-tool confirmation prompts. `--dangerously-skip-permissions` may be used only with explicit consent.
- **Model**: `-m <model>` or `--model <model>`.
- **Startup**:
  ```bash
  # 1. Start agent in pane:
  herdr agent start worker-1 --kind qodercli --pane w1:p2 -- -m deepseek-r1 --permission-mode accept_edits
  # 2. Inspect pane for folder trust prompt:
  herdr agent read worker-1 --source recent-unwrapped --lines 20
  # 3. If folder trust dialog is present, confirm interactively or via keys:
  herdr agent send-keys worker-1 enter
  ```
- **Quirks**: `qoderclicn` is the binary name for domestic/China distributions; `qodercli` is standard. Both share identical CLI semantics.

### `claude` (Claude Code)
- **Trust Behavior**: Prompts for workspace trust on initial run.
- **Permissions**: Accepts `--dangerously-skip-permissions` to suppress tool prompts (consent-gated; requires explicit user authorization).
- **Model**: `--model <model>`.
- **Startup**:
  ```bash
  herdr agent start reviewer --kind claude --pane w1:p3 -- --model claude-3-7-sonnet
  ```

### `agy` (Antigravity)
- **Model**: `--model <model>`.
- **Startup**:
  ```bash
  herdr agent start reviewer --kind agy --pane w1:p3 -- --model gemini-2.5-pro
  ```
- **Quirks**: Weakly recognized in some versions (revision 0, no session path). Always verify pane output directly with `herdr agent read` rather than trusting state alone.

---

## 4. Startup Checklist

Follow this 5-step sequence when provisioning any coding agent in Herdr:

1. **User Confirmation**: Confirm role ↔ agent kind ↔ provider ↔ model mapping with user.
2. **Pane Allocation**: Split pane with `--no-focus` and `--cwd "$PWD"` (or worktree path).
   ```bash
   herdr pane split --current --direction right --cwd "$PWD" --no-focus
   ```
3. **Agent Start**: Launch agent with native arguments placed strictly after `--`.
   ```bash
   herdr agent start <name> --kind <kind> --pane <pane-id> -- <native-flags>
   ```
4. **Folder Trust Handling**:
   - For `pi`: Ensure `--approve` was passed after `--`.
   - For `qoderclicn` / `qodercli`: Inspect pane output (`herdr agent read <name> --source recent-unwrapped`) to check for interactive folder trust prompts, and confirm trust before proceeding.
   - For other agents: Inspect pane output for any initial consent/login prompts.
5. **State Settling**: Wait until the agent settles into `idle` or `done` before dispatching tickets or prompts.
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_wait.py" <name> --timeout 30000
   ```
