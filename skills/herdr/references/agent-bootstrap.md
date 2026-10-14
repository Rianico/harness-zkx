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
   Bootstrap then waits a bounded settle (`--settle SEC`, default 5) before it reports the pane bootstrapped: a pane spawned a moment ago can report `interactive_ready: true` while it is still initialising (#238), so the first prompt would be swallowed. Only a fresh spawn settles — a dispatch to an already-running pane pays nothing — and `--settle 0` waits not at all.
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
| `pi`, `claude` | `agent start --append-system-prompt <path>` | `.lane/invariants/<agent-name>.md` |
| `cline` | `AGENTS.md` append (prefers an existing `.clinerules`) | `.clinerules` \| `AGENTS.md` |
| `codex`, `copilot`, `qodercli`, `agy`, unknown | `AGENTS.md` append | `AGENTS.md` |

Delivery follows `skills/herdr/references/kinds.yaml`: `inline` kinds (`pi`, `claude`) receive `--append-system-prompt`; `file` kinds and unknown kinds get the universal `AGENTS.md` append. Trust flags ride after `--` as native agent args, configured per kind (verified: `pi` → `--approve`, `claude` → `--dangerously-skip-permissions`); unverified kinds carry none. The same file declares `revision_moves` per kind. `agy` sets it false because its revision never moves, so the unconfirmed-acceptance warning does not send that kind to a revision-based re-check — a wanted state at revision 0 is unsatisfiable and the wait helper exits 2 — and names the agy bridge's status title instead. When `--cwd` names a worktree, bootstrap cds the pane there first (`--cwd-timeout`, default 10s) and refuses to start when the pane does not converge. The file target dir is `--cwd`, else the `--pane` cwd read from `herdr pane list`, else `$PWD`.

### The spawn settle

A pane spawned moments ago can honestly report `interactive_ready: true` and `agent_status: idle` while it is still initialising, so the first prompt can be swallowed (#238). After `agent start` returns, bootstrap therefore waits `--settle SEC` — default 5, `0` waits not at all, and a `0` wait is exactly zero rather than a token sleep — and only then reports the pane bootstrapped. The wait is one fixed sleep, never a poll until a steady state, and it is paid only by a spawn: a dispatch or a prompt to an already-running pane adds no settle delay. `--dry-run` never sleeps and reports the planned wait as `settle` in its JSON plan. The prompt helper's own 5s acceptance handshake is untouched and corroborates the settle rather than replacing it. The reply helper's `--auto-start` revive carries the same `--settle` for the caller it spawns.

```bash
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" msg-impl-1 --kind codex --pane w1:p3 --role impl-1 --task-group msg
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" --kind pi --pane w1:p3 --role tm --task-group msg --model claude-3-7-sonnet
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" msg-tm --kind claude --pane w1:p2 --role tm --dry-run
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" msg-tm --kind claude --pane w1:p2 --role tm --settle 0
```

### The ROLE INVARIANT snippet

```text
ROLE INVARIANT: You are {a|an} {role} in a Herdr lane. Follow the lane coordination pattern.
Subagent-First: MUST delegate deep search, multi-file edits, and test triage to subagents.
Reply Contract: MUST reply via `uv run $SKILL_DIR/scripts/herdr_reply.py <caller> --file <reply.md>` on completion or blocker; never exit silently.
```

Implementer roles — the docs' `impl-<n>` vocabulary, scoped or bare (`impl-1`, `msg-impl-1`) — append the cooperation contract:

```text
Implementer: single writer for your task; never edit outside your worktree.
Evidence: red-then-green test results, artifacts reported by path.
Blockers: report immediately, never idle.
```

Task Manager roles — the coordination-authority vocabulary (`tm`, `task-manager`, `orch`,
`orchestrator`, `coord`, `coordinator`), scoped or bare (`msg-tm`, `lane-orch`), matched on whole
role segments — append the Task Manager contract:

```text
Task Manager: coordination, design, and review authority only; NEVER edit source or test code directly.
Dispatch: explore problem space; decompose briefs into atomic tickets; dispatch via `herdr-dispatch`.
Eval & Review: run verification gates in pane; audit callee diffs with review subagents before accepting.
Synthesize: track lane progress; synthesize results and report completion to caller via `herdr-reply`.
```

That block is role-conditional: it rides only for an implementer role, so a coordination-only role does not pay for it and stays inside the original 45-word budget, while the implementer variant is capped at 80. The discriminator is segment-aware because the lane convention is `<task-group-slug>-<role>[-<subrole|index>]`: `herdr228-impl-1` and `msg-impl-1` carry the block, `herdr228-task-manager` and `msg-tm` stay coordination-only. Accepted over-match: a lane *slug* segment that itself begins with `impl` (an `impl-hardening` lane) drags its coordination roles into the block too. The shared Reply Contract already owes the reply, so the block adds only implementer-only content and stays at 69 words. The article follows the role's first letter (`a tm`, `an impl-1`). The reply command is **absolute** on purpose: the rendered text embeds the lane's own helper, resolved from the running `herdr_bootstrap.py`'s own directory, and `uv run` stays in front, so an agent whose shell sits anywhere — `/tmp`, `$HOME` — still spawns it. The `~/.agents/skills/herdr` symlink is deliberately not used: it resolves into another worktree whose `herdr_*` code may be older.

### The per-agent invariant file

The `inline` kinds read one file per **resolved agent name**: `<lane>/.lane/invariants/<agent-name>.md`. The name keeps `[A-Za-z0-9._-]` and replaces every other character with `_`; an empty result, `.`, and `..` are refused, so a garbled name can never name a file outside the directory. The directory is created as needed. Bootstrapping one agent therefore never overwrites another's text, and re-bootstrapping an agent replaces only its own file. The file is **launch-time input only**: bootstrap writes it and passes the path to `--append-system-prompt`; nothing reads it back at runtime. The `file` kinds keep their `AGENTS.md` append and its committed-block behaviour, unchanged.

### The idempotent marker

The file append is idempotent. The block is wrapped in `<!-- herdr-bootstrap:role-invariant -->` … `<!-- /herdr-bootstrap:role-invariant -->` and written only when the start marker is absent, so re-bootstrapping the same directory never duplicates the snippet and never rewrites an untouched file; existing content and its trailing newline are preserved.

### Version-controlled targets are refused

The target file *is* the delivery mechanism for the file kinds: they have no `--append-system-prompt`, and bootstrap has no message-prefix channel, so the invariant reaches the agent only because the agent reads `AGENTS.md` (or `.clinerules`) at launch. Moving it to a lane-local file the agent never reads would silently drop the invariant, which is worse than dirtying a tree. Bootstrap therefore guards the write instead:

- **Tracked, block absent** → refuse. Bootstrap exits 2 naming the absolute target file, the reason (a launch must not modify a tracked file), and `--allow-tracked-invariant`. Nothing is launched, no pane is renamed, no file is written.
- **Tracked, block already there** → skip the write and launch. The committed block is **not** role-checked: any block carrying the marker pair means no write, so the agent reads whatever block is committed — deliberately left unchanged even when it names a different role than the launch. Refreshing a role's contract is the per-agent invariant file's job, and that file serves the `inline` kinds only; the `file` kinds still read the committed block, so this bootstrap only guarantees the marker pair is present.
- **`--allow-tracked-invariant`** → append anyway and leave that tracked file modified, on the record (`git status` shows it). The same flag overrides the *undetermined* refusal below: a repository that exists on disk whose tracked state git could not read is a refusal, not a permanent dead end for the invariant, and the flag appends through it.
- **Untracked in a repo, or outside any repo** → append as before. This is not "the tree is unchanged": a freshly created or edited lane-local file shows as `?? AGENTS.md` in `git status`, while outside a repo `git status` cannot answer at all.

Version-control state comes from git against the file's real location: `git rev-parse --is-inside-work-tree`, then `git ls-files --error-unmatch -- <path>`, asked about the file's on-disk entry name (a case-insensitive volume lists "agents.md" where bootstrap computed `AGENTS.md`, and a case-variant name counts only when it is the *same file*). Only an answer about the file's own repository and index is trusted. When the answer cannot be had, the fallback splits on whether a repository is there at all: **a repository that exists on disk whose tracked state git could not read is refused** (exit 2, same message family), because the file may be tracked. That covers a repository git confirmed whose index or `ls-files` read failed, and every case where git itself refused to answer while a `.git` entry stands at or above the target — dubious ownership, an unreadable `.git`, or a `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` override pointing the probe away from the file's own repository. `--allow-tracked-invariant` overrides that refusal too. **A host where git could not run at all is not refused**: it still gets the append, so a missing git never withholds the invariant, and prints one warning line saying the tracked state could not be determined — though a tracked tree may still be dirtied and the operator sees just that one line. A target git could answer about — untracked inside a repository (an unborn HEAD included), or outside any repository, where no `.git` entry stands above it either — is appended with no warning at all.

`--dry-run` reports the verdict before anything launches: `agents_md_tracked` is `true`/`false`, or `null` when the tracked state could not be determined. `would_refuse` carries the refusal string when the append would be refused, and `note` carries the warning when an undetermined target would still be appended. Both keys appear only for the file kinds, whose run has a target file; the inline kinds report neither.

```bash
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" msg-impl-1 --kind codex --pane w1:p3 --role impl-1 --task-group msg --allow-tracked-invariant
```

### Scoped-prefix rule

Every lane name follows `<task-group-slug>-<role>[-<subrole|index>]`. For the `msg-enhance` lane: `msg-orch`, `msg-tm`, `msg-impl-1`, `msg-reviewer`. `--task-group <slug>` prefixes a bare role (`tm` → `msg-tm`, `impl-1` → `msg-impl-1`) and leaves an already-scoped value unchanged; the same string is the pane label and the agent name, and it must satisfy `[a-z][a-z0-9_-]{0,31}` (max 32 chars).
