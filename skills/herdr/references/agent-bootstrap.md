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
   uv run "$SKILL_DIR/scripts/herdr_pane.py" right --label reviewer --cwd "$WORKTREE_PATH" --no-focus
   ```
3. **Agent Start**: Start through `herdr-bootstrap` — it stamps the ROLE INVARIANT, injects the kind's trust flags from `skills/herdr/references/kinds.yaml`, and cds the pane into `--cwd` before start. Raw `agent start` (native arguments strictly after `--`) is the fallback when bootstrap cannot express the launch.
   ```bash
   herdr agent start <name> --kind <kind> --pane <pane-id> -- <native-flags>
   ```
4. **Folder Trust Handling**:
   - For `pi`: `--approve` is injected automatically from `kinds.yaml` — verify `-- --approve` is in the start argv instead of hand-adding flags.
   - For `qodercli`: `agent start` reports `interactive_ready: true` and a `Ready` title even while the trust selector is up, so read the pane. Either send one bare Enter (`herdr agent send-keys <name> enter`) and confirm the `YOLO` status line, or pre-seed `permissions.trustDirectories` in the config root the binary reads (`~/.qoder`, or `~/.qoder-cn` for the CN build) before starting. A prompt cannot dismiss the selector. See [Qoder CLI](agents/qodercli.md).
   - For other agents: Inspect pane output for any initial consent/login prompts.
5. **State Settling**: Confirm the agent is ready before dispatching tickets or prompts. Read the pane text: a freshly started agent can be weakly recognized — its record reports `idle`/`done` with revision 0 — and a wanted state at revision 0 is unsatisfiable, so the wait helper exits 2 instead of settling, because `herdr-wait` cannot observe a weakly-recognized agent to completion. The `--source recent-unwrapped` pane read exits 0 and prints what the pane shows, so a trust selector or login prompt is visible before the first prompt; `herdr-prompt` and `herdr-dispatch` then re-check readiness themselves and abort with a `UsageError` when the pane never converges. Wait on the state barrier only for a strongly-recognized agent, and use Dispatch-&-Yield for `agy` and revision-0 agents ([Safety Rules](safety-rules.md)).
   ```bash
   herdr agent read <name> --source recent-unwrapped --lines 120
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

Delivery follows `skills/herdr/references/kinds.yaml`: `inline` kinds (`pi`, `claude`) receive `--append-system-prompt`; `file` kinds and unknown kinds get the universal `AGENTS.md` append. Trust flags ride after `--` as native agent args, configured per kind (verified: `pi` → `--approve`, `claude` → `--dangerously-skip-permissions`); unverified kinds carry none. When `--cwd` names a worktree, bootstrap cds the pane there first (`--cwd-timeout`, default 10s) and refuses to start when the pane does not converge. The file target dir is `--cwd`, else the `--pane` cwd read from `herdr pane list`, else `$PWD`.

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

### Version-controlled targets are refused

The target file *is* the delivery mechanism for the file kinds: they have no `--append-system-prompt`, and bootstrap has no message-prefix channel, so the invariant reaches the agent only because the agent reads `AGENTS.md` (or `.clinerules`) at launch. Moving it to a lane-local file the agent never reads would silently drop the invariant, which is worse than dirtying a tree. Bootstrap therefore guards the write instead:

- **Tracked, block absent** → refuse. Bootstrap exits 2 naming the absolute target file, the reason (a launch must not modify a tracked file), and `--allow-tracked-invariant`. Nothing is launched, no pane is renamed, no file is written.
- **Tracked, block already there** → skip the write and launch. The committed block is **not** role-checked: any block carrying the marker pair means no write, so the agent reads whatever block is committed — deliberately left unchanged even when it names a different role than the launch. Refreshing a role's contract belongs to the per-role invariant file (#236); this bootstrap only guarantees the marker pair is present.
- **`--allow-tracked-invariant`** → append anyway and leave that tracked file modified, on the record (`git status` shows it). The same flag overrides the *undetermined* refusal below: a confirmed repository whose tracked state git could not read is a refusal, not a permanent dead end for the invariant, and the flag appends through it.
- **Untracked in a repo, or outside any repo** → append as before. This is not "the tree is unchanged": a freshly created or edited lane-local file shows as `?? AGENTS.md` in `git status`, while outside a repo `git status` cannot answer at all.

Version-control state comes from git against the file's real location: `git rev-parse --is-inside-work-tree`, then `git ls-files --error-unmatch -- <path>`, asked about the file's on-disk entry name (a case-insensitive volume lists `agents.md` where bootstrap computed `AGENTS.md`, and a case-variant name counts only when it is the *same file*). Only an answer about the file's own repository and index is trusted. When detection cannot run, refuses, or answers about another repository, the fallback is split and honest. A repository git confirms but whose tracked state it could not read — an unreadable index, dubious ownership, an unreadable `.git`, or a `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` override that points the probe at another repository — is refused (exit 2, same message family), because the file may be tracked; `--allow-tracked-invariant` overrides that refusal too. A repository git cannot confirm still gets the append, so a missing git never withholds the invariant, and prints one warning line saying the tracked state could not be determined — meaning a tracked tree may still be dirtied and the operator sees just that one line.

`--dry-run` reports the verdict before anything launches: `agents_md_tracked` is `true`/`false`, or `null` when the tracked state could not be determined. `would_refuse` carries the refusal string when the append would be refused, and `note` carries the warning when an undetermined target would still be appended. Both keys appear only for the file kinds, whose run has a target file; the inline kinds report neither.

```bash
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" msg-impl-1 --kind codex --pane w1:p3 --role impl-1 --task-group msg --allow-tracked-invariant
```

### Scoped-prefix rule

Every lane name follows `<task-group-slug>-<role>[-<subrole|index>]`. For the `msg-enhance` lane: `msg-orch`, `msg-tm`, `msg-impl-1`, `msg-reviewer`. `--task-group <slug>` prefixes a bare role (`tm` → `msg-tm`, `impl-1` → `msg-impl-1`) and leaves an already-scoped value unchanged; the same string is the pane label and the agent name, and it must satisfy `[a-z][a-z0-9_-]{0,31}` (max 32 chars).
