# Coding Agent Bootstrap & Trust Reference

Depth for `$SKILL_DIR/SKILL.md`. Details bootstrap commands, folder trust behaviors, provider/model flags, and pre-orchestration user confirmation protocols for coding agents running under Herdr. Individual agent details live in `agents/<agent>.md`.

---

## 1. Pre-Orchestration Confirmation Protocol

Before starting any agent, creating task panes, or launching workflows, the orchestrator **MUST** explicitly confirm with the user the mapping of roles to coding agent kinds, providers, and models.

Never assume or default to a specific agent kind, provider, or model.

### Information Required from User
1. **Roles needed**: e.g., Task Manager (TM), Implementer, Reviewer, Researcher.
2. **Agent kind (`--kind`) per role**: e.g., `pi`, `qodercli`, `claude`, `agy`. Use a name from `herdr agent start --help`; the Qoder builds share one kind (see [Qoder CLI](agents/qodercli.md)).
3. **Provider and model per role**: e.g., `pi` with `--provider anthropic --model claude-3-7-sonnet`, `qodercli` with `-m qwen-max`, `claude` with `--model claude-3-7-sonnet`.

### Standard Confirmation Template

Ask the user using the following structure:

```markdown
Before provisioning Herdr lanes and launching agents, please confirm the role configuration:

| Role | Agent Kind (`--kind`) | Provider | Model | Native Flags |
|---|---|---|---|---|
| Task Manager | pi | anthropic | claude-3-7-sonnet | `--approve` |
| Implementer | qodercli | custom | deepseek-r1 | `--permission-mode bypass_permissions` |
| Reviewer | pi | google | gemini-2.5-pro | `--approve` |

Please approve this configuration or provide desired overrides for agent kind, provider, or model.
```

---

## 2. Agent Bootstrap Matrix

| Kind | Details | Command / Binary | Folder Trust / Approval Behavior | Provider & Model Flags | Key Quirks |
|---|---|---|---|---|---|
| `pi` | [pi.md](agents/pi.md) | `pi` | Supports `--approve` (`-a`) to trust project-local files and skip interactive trust prompts. | `--provider <name>`, `--model <pattern>` (or `<provider>/<model>`) | Structured JSONL session files in `~/.pi/agent/sessions/`. |
| `qodercli` | [qodercli.md](agents/qodercli.md) | `qodercli` / `qoderclicn` | **Blocking trust selector on an untrusted folder.** `agent start` still reports `interactive_ready: true` and a `Ready` title, and a prompt is swallowed by the selector. Clear it with one bare Enter or pre-seed `permissions.trustDirectories`. No `--approve` flag exists. | `-m`, `--model <model>`, `--reasoning-effort`, `--thinking` | YOLO via `--permission-mode bypass_permissions`, which does not skip folder trust. Trust and hooks are per config root: `~/.qoder` vs `~/.qoder-cn`. |
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
   - For `qodercli`: `agent start` reports `interactive_ready: true` and a `Ready` title even while the trust selector is up, so read the pane. Either send one bare Enter (`herdr agent send-keys <name> enter`) and confirm the `YOLO` status line, or pre-seed `permissions.trustDirectories` in the config root the binary reads (`~/.qoder`, or `~/.qoder-cn` for the CN build) before starting. A prompt cannot dismiss the selector. See [Qoder CLI](agents/qodercli.md).
   - For other agents: Inspect pane output for any initial consent/login prompts.
5. **State Settling**: Wait until the agent settles into `idle` or `done` before dispatching tickets or prompts.
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_wait.py" <name> --timeout 30000
   ```
6. **Name the Pane**: The agent name dies with the agent while the pane label survives, so a restart or a new occupant can inherit a stale label. Set both in one step, then confirm the session is consistent:
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_label.py" <name> --pane <pane_id>
   uv run "$SKILL_DIR/scripts/herdr_label.py" --verify   # exit 3 on a live agent that disagrees with its label
   ```
   After an agent exits or is replaced, `herdr-label --sync` converges the pair again — it relabels from the agent name, or names an agent that came back without one from the label it left behind.

---

## 4. Role Invariant Bootstrap (`herdr-bootstrap`)

A compacted agent forgets its lane: it stops delegating to subagents and exits without replying. `herdr_bootstrap.py` stamps a compaction-proof **ROLE INVARIANT** into the one surface the target agent reads at launch, sets the pane label to the scoped name, then starts the agent. Two delivery mechanisms follow from whether the kind accepts an inline system prompt:

| Kind | Mechanism | Written artifact |
|---|---|---|
| `pi`, `claude` | `agent start --append-system-prompt <snippet>` | none |
| `cline` | `AGENTS.md` append (prefers an existing `.clinerules`) | `.clinerules` \| `AGENTS.md` |
| `codex`, `copilot`, `qodercli`, `agy`, unknown | `AGENTS.md` append | `AGENTS.md` |

Only `pi` and `claude` receive `--append-system-prompt`; no permission or approval flags are injected (the operator's herdr config owns those); an unknown kind falls back to the universal `AGENTS.md` append. The target dir is `--cwd`, else the `--pane` cwd read from `herdr pane list`, else `$PWD`.

```bash
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" msg-impl-1 --kind codex --pane w1:p3 --role impl-1 --task-group msg
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" --kind pi --pane w1:p3 --role tm --task-group msg --model claude-3-7-sonnet
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" msg-tm --kind claude --pane w1:p2 --role tm --dry-run
```

### The ROLE INVARIANT snippet

```text
ROLE INVARIANT: You are an {role} in a Herdr lane.
1. Subagent-First: MUST delegate deep search, multi-file edits, and test triage to internal subagents.
2. Reply Contract: MUST reply to caller via `uv run ~/.agents/skills/herdr/scripts/herdr_reply.py <caller> --file <reply.md>` upon completion or blocker. Never exit silently.
```

### The idempotent marker

The file append is idempotent. The block is wrapped in `<!-- herdr-bootstrap:role-invariant -->` … `<!-- /herdr-bootstrap:role-invariant -->` and written only when the start marker is absent, so re-bootstrapping the same directory never duplicates the snippet and never rewrites an untouched file; existing content and its trailing newline are preserved.

### Scoped-prefix rule

Every lane name follows `<task-group-slug>-<role>[-<subrole|index>]`. For the `msg-enhance` lane: `msg-orch`, `msg-tm`, `msg-impl-1`, `msg-reviewer`. `--task-group <slug>` prefixes a bare role (`tm` → `msg-tm`, `impl-1` → `msg-impl-1`) and leaves an already-scoped value unchanged; the same string is the pane label and the agent name, and it must satisfy `[a-z][a-z0-9_-]{0,31}` (max 32 chars).
