# Coding Agent Bootstrap & Trust Reference

Depth for `$SKILL_DIR/SKILL.md`. Details bootstrap commands, folder trust behaviors, provider/model flags, and pre-orchestration user confirmation protocols for coding agents running under Herdr. Individual agent details live in `agents/<agent>.md`.

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

| Kind | Details | Command / Binary | Folder Trust / Approval Behavior | Provider & Model Flags | Key Quirks |
|---|---|---|---|---|---|
| `pi` | [pi.md](agents/pi.md) | `pi` | Supports `--approve` (`-a`) to trust project-local files and skip interactive trust prompts. | `--provider <name>`, `--model <pattern>` (or `<provider>/<model>`) | Structured JSONL session files in `~/.pi/agent/sessions/`. |
| `qoderclicn` / `qodercli` | [qodercli.md](agents/qodercli.md) | `qodercli` / `qoderclicn` | **Requires trusting the folder in terminal UI**. If untrusted, displays an interactive terminal trust prompt. Automated `--approve` flag is **NOT** supported for folder trust. Operator must confirm trust interactively in terminal or via `herdr agent send-keys` before prompting. | `-m`, `--model <model>` | Permission bypass via `--permission-mode accept_edits` (or `--dangerously-skip-permissions` if authorized). |
| `claude` | [claude.md](agents/claude.md) | `claude` | Prompts on first run in folder; accepts `--dangerously-skip-permissions` (consent-gated). | `--model <model>` | Interactive auth/login check on startup. |
| `agy` | [agy.md](agents/agy.md) | `agy` | Standard project trust configuration. | `--model <model>` | Weakly recognized in some versions (revision 0, no session path); status bar may read `WORKING` while settled. |
| `gemini` | [gemini.md](agents/gemini.md) | `gemini` | Workspace approval on directory change. | `--model <model>` | Terminal wrapper integration. |
| `cursor` | [cursor.md](agents/cursor.md) | `cursor-agent` | Workspace trust inheritance. | `--model <model>` | GUI/agent bridge dependency. |
| `cline` | [cline.md](agents/cline.md) | `cline` | Interactive configuration on first run. | Config file / `--model <model>` | Custom API endpoint mapping. |
| `copilot` | [copilot.md](agents/copilot.md) | `github-copilot-cli` | GitHub CLI auth token required. | Default model endpoint | Interactive confirmation required. |
| `aider` | [aider.md](agents/aider.md) | `aider` | Git repo auto-detection; no interactive trust screen. | `--model <model>` | Modifies git index directly if git repo detected. |

---

## 3. Startup Checklist

Follow this 6-step sequence when provisioning any coding agent in Herdr:

0. **Worktree Pre-provisioning**: For multi-agent lane coordination, allocate one isolated worktree for the lane before any pane starts, so Task Manager and Implementer run inside it from turn zero.
   ```bash
   WORKTREE_PATH=$(uv run "$SKILL_DIR/scripts/herdr_worktree.py" allocate <branch-name>)
   ```
1. **User Confirmation**: Confirm role ↔ agent kind ↔ provider ↔ model mapping with user.
2. **Pane Allocation**: Split pane with `--no-focus`, `--label <role>`, and `--cwd "$WORKTREE_PATH"` (the worktree pre-provisioned in Step 0).
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_pane.py" --direction right --label reviewer --cwd "$WORKTREE_PATH" --no-focus
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
