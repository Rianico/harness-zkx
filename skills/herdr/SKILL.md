---
name: herdr
description: >-
  Herdr terminal-multiplexer reference for coding agents. Inspects and drives panes, tabs, workspaces, and sibling agents; waits on test or server output. Use when the user mentions Herdr or asks to inspect pane layout or drive agents. Requires HERDR_ENV=1; not for background terminals or delegation.
metadata:
  author: herdrdev
  version: '0.9.0'
---

# Herdr

Vendored from `herdrdev/herdr@v0.9.0`; `herdr --skill` prints the installed binary's copy.

Herdr organizes terminals into workspaces, tabs, and panes, recognizes coding agents, and exposes the session through the `herdr` CLI.

Before issuing control commands, verify that this agent runs inside a Herdr-managed pane:

```bash
[ "${HERDR_ENV:-}" = 1 ]
```

Prefer bracket syntax `[` over `test`: tool-rewriting extensions hook `test` as an application runner. If the check fails, report that you are not running inside Herdr and stop. Do not control Herdr from outside.

When the check passes, `herdr` in `PATH` talks to the current session.

## Know your post

Your post is your agent name at your pane id. Read it from the environment:

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
uv run "$SKILL_DIR/scripts/herdr_overview.py" --current
```

`herdr-label` sets the pane label and agent name identically so the name on the border is addressable.

Every cross-pane message carries an A2A Markdown frontmatter envelope (`docs/adr/0020-a2a-markdown-frontmatter-envelope.md`): opened by `---` on line 1 and closed by `---`, holding exactly four keys — `id`, `context_id`, `status` (`state`, `timestamp`), and `metadata` (`ticket_id`, `sender`, `receiver`, `task_group`, `group`, and `in_reply_to` on replies). The Herdr skill notice rides as a plain line after the closing fence:

```text
---
id: '#182-herdr-msg-enhance#overview-rich'
context_id: pi-8f2c1d
status:
  state: TASK_STATE_WORKING
  timestamp: '2026-10-05T06:19:12.983Z'
metadata:
  ticket_id: '#182-herdr-msg-enhance'
  sender: orchestrator@w1:p1
  receiver: impl-1@w1:p3
  task_group: msg-enhance@w1:t1
  group:
  - orchestrator@w1:p1
  - impl-1@w1:p3
  - impl-2@w1:p4
---
Herdr: follow the herdr skill — run its helper scripts from ${herdr_skill}/scripts/ for all coordination, never the bare herdr CLI

<payload>
```

Harness scripts prepend the envelope to every payload. Unlinked messages receive a generated `unlinked-<UTC>` id. Recovery metadata (`metadata.cwd`/`metadata.resume`) lives in `.lane/tasks.yaml` (`--verbose` includes it). Relay messages with envelopes intact (`parse_envelope` refuses text without `---`). Full contract: [lane-coordination.md](references/lane-coordination.md).

The token before `@` is the **live agent name**, the addressable target `herdr agent prompt` accepts besides pane ids. Pane labels are border decorations, not targets; `metadata.sender` renders `<agent>@<pane>`. Address panes by pane id or pass `--label` to `herdr-prompt`. Details: `$SKILL_DIR/references/cli-reference.md`.

> [!IMPORTANT] Orient First, Then Use Harness Scripts
> Always use harness scripts in `$SKILL_DIR/scripts/` (e.g. `herdr_overview.py`, `herdr_pane.py`, `herdr_prompt.py`, `herdr_reply.py`, `herdr_dispatch.py`), NOT bare `herdr` CLI commands, for orientation, layout, agent communication, prompting, and waiting.

## Orient with `herdr-overview` first

One call answers "what is here, and which pane or agent do I act on?" — pane ids, kinds, names, labels, subagent tokens (`delegating`), and cwd, grouped by workspace, calling pane marked `*`:

```bash
uv run "$SKILL_DIR/scripts/herdr_overview.py"                 # every workspace: YAML when piped, table on a TTY
uv run "$SKILL_DIR/scripts/herdr_overview.py" --json          # JSON for programmatic parsing
uv run "$SKILL_DIR/scripts/herdr_overview.py" --workspace     # only the calling workspace
uv run "$SKILL_DIR/scripts/herdr_overview.py" --tab           # only the calling tab (task group)
uv run "$SKILL_DIR/scripts/herdr_overview.py" --tab w1:t2      # only that tab, by id or label
uv run "$SKILL_DIR/scripts/herdr_overview.py" --task-group msg-enhance  # only that task group by name
uv run "$SKILL_DIR/scripts/herdr_overview.py" --current       # only the calling pane
uv run "$SKILL_DIR/scripts/herdr_overview.py" --format table  # force a format
```

Piped output defaults to YAML (`# Format: YAML (pass --json for JSON)`); pass `--json` for scripts. Read created entities from creation responses instead of re-listing: `workspace create` returns `.result.workspace`, `tab create` returns `.result.tab`, and `pane split` returns `.result.pane`.

## Learn the current CLI

The installed binary is authoritative for command syntax. Run `herdr --help`, or inspect command groups (`herdr agent`, `herdr pane`). Do not run bare `herdr` without arguments (launches TUI). Do not probe mutating commands without arguments — `herdr workspace create` executes with defaults. Control commands return JSON. Command groups and connection profiles live in `$SKILL_DIR/references/cli-reference.md`.

## Understand layout, panes, and agents

Choose the primitive matching the job:
- Workspaces, tabs, and panes organize terminal topology.
- Pane commands control raw terminals, shells, processes, input, and output.
- Agent commands control recognized coding agents occupying a pane.

A pane exists whether or not it hosts an agent. `agent start` requires an available shell pane and never mutates layout. Use pane commands for ordinary processes. Use agent commands when Herdr must validate agent identity or interpret `idle`, `working`, `blocked`, `done`, and `unknown` lifecycle states. Agent commands accept a unique live agent name or pane ID hosting that agent. Full lifecycle rules live in `$SKILL_DIR/references/cli-reference.md`.

> [!WARNING] Shell Input Constraint
> NEVER use `herdr pane send-text` or `herdr pane send-keys` to deliver prompts or replies. In a raw shell pane, this executes prompt text directly as shell commands.

## Use IDs and the calling pane

Public IDs are opaque stable handles: workspace `w1`, tab `w1:t1`, pane `w1:p1`. Prefer `--current` when targeting the calling pane; omitting targets defaults to the UI-focused pane. Use `herdr-overview` to locate entities; do not reconstruct layout via list probes.

## Name a target, then hand off

Pane labels appear on border decoration, but commands require an **agent name**. When an agent exits, its name is cleared while its label outlives it. Set both identically:

```bash
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer    # this pane's label and its agent name
```

> [!IMPORTANT] Name Every Pane Immediately
> Unlabeled panes (`null`) cause blind spots in `herdr-overview` and break automated reply routing. Name each pane with meaningful text matching its role (`orchestrator`, `task-manager`, `impl-auth`, `reviewer`) using `herdr-pane --label` or `herdr-label`.

`herdr-label` sets pane label and agent name together. Pass `--pane <id>` for remote panes, `--label-only` for multi-word labels, and `--clear` to drop both. Use `--verify` and `--sync` to maintain consistency:

```bash
uv run "$SKILL_DIR/scripts/herdr_label.py" --verify   # exit 3 when a live agent disagrees with its label
uv run "$SKILL_DIR/scripts/herdr_label.py" --sync     # converge both directions, idempotent
```

To hand off by name:

```bash
uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --file brief.md --wait --timeout 15000
uv run "$SKILL_DIR/scripts/herdr_prompt.py" --label "review pane" --file brief.md --wait --timeout 15000
```

`--label` matches pane labels exactly; ambiguous matches fail with candidates instead of guessing.

### Target resolution failures & bare shell prevention

If target resolution fails or matches an idle shell pane:
- **Refusal**: `herdr-prompt` and `herdr-reply` refuse delivery to raw shell panes to prevent executing prose as shell commands.
- **Recovery hook**: Diagnostics print the exact recovery command: `Suggested recovery: herdr agent start <name> --kind <kind> --pane <id>`.
- **Auto-start**: `herdr-reply` supports `--auto-start <KIND>` to start the agent on an open shell pane before delivering the reply, settling it (`--settle SEC`, default 5). When the target exited or is a bare shell, it prints `--auto-start <kind>` or stored `resume_cmd` from `.lane/tasks.yaml`.
- **Queue/watch**: Wait for the agent to start or monitor the pane with `herdr pane wait-output`. Explicitly start agents via `herdr agent start <name> --kind <kind> --pane <id>`. If the target exited, abort gracefully.
- **Safety invariant**: NEVER use `herdr pane send-text` or `herdr pane send-keys` to deliver prompts or replies into a shell pane.

### Dispatch & Yield (Event-Driven workflow)

Multi-agent coordination is event-driven via completion callbacks:

1. **Caller self-names:**
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_label.py" orchestrator
   ```
   Ensures the caller has an addressable agent name for replies.

2. **Dispatch with Synthesized IDD/GDD Tickets & Task Leases:**
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --file task.md --no-wait
   uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --file task.md --force --no-wait
   uv run "$SKILL_DIR/scripts/herdr_prompt.py" callee --file task.md --wait --timeout 15000
   ```
   Tickets pair purpose (**IDD**) with verifiable milestones (**GDD/EDD**). `herdr_dispatch.py` checks active ticket leases in `.lane/tasks.yaml` before dispatching; leases are acquired atomically and retained on prompt acceptance (`EXIT_OK` or `WaitTimeout`). Leases with dead pane IDs release automatically; `--force` overrides live leases. Store base resolves from `HERDR_LANE_DIR`, else repo root, else `~/.herdr/lane`.
   `.lane/tasks.yaml` holds `active_leases` and durable `tasks` with an append-only `trajectory`. Canonical statuses: `TASK_STATE_SUBMITTED`, `TASK_STATE_WORKING`, `TASK_STATE_INPUT_REQUIRED`, `TASK_STATE_FAILED`, `TASK_STATE_COMPLETED` — every write emits these. Historical tokens stay readable through `STATUS_ALIASES` in `herdr_lease.py`, are never written, and historical records are never migrated; the store is a shared live database read by worktrees that cannot be upgraded in lockstep:
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_lease.py" show --yaml --limit 10
   uv run "$SKILL_DIR/scripts/herdr_lease.py" transition msg-impl-1 TASK_STATE_WORKING --note "starting edits"
   ```
   Never dispatch tasks via bare `herdr agent prompt callee` directly — doing so drops envelope, caller recovery, and reply contract. Exit code 0 from `herdr agent prompt` confirms acceptance.

3. **Yield turn on async execution:**
   When `herdr-prompt` exits 4 (timeout) or was dispatched with `--no-wait`, the prompt was delivered and the callee is working asynchronously. Yield turn (stop calling tools, enter idle).

4. **Callee executes completion callback (and soft-releases its lease):**
   Upon completion or blocking, the callee executes the contract callback via `herdr_reply.py`, adhering to the settled **Final Reply Template** (`skills/ai-engineering-expert/references/resp-format.md`):
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file reply.md --ticket '<ticket-id>'
   printf 'COMPLETED <commit-sha>\n\n## Evidence\n- <check_name>: PASS (`<command>`)\n' | uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file - --ticket '<ticket-id>'
   uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file reply.md --ticket '<ticket-id>' --auto-start pi
   ```
   Payload sections: Status Triad (`COMPLETED <commit-sha>` | `BLOCKED <reason>` | `REJECTED <reason>`), `## Summary` (≤100 words), `## Artifacts`, `## Evidence` (PASS/FAIL), `## Route`, `## Issues` (P1/P2/P3), `## Suggestions`. Delivering this reply prompts caller pane directly, waking its turn. `herdr_reply.py` maps status tokens, records events, and soft-releases only sender lease. When target exited or is a bare shell, it prints recovery diagnostics (`--auto-start <kind>` or stored `resume_cmd`). Never use bare `herdr agent prompt` directly for replies.

5. **Subagent Observability & `herdr-wait`:**
   **Subagent-First Execution**: In lane coordination, agents MUST use subagents for heavy tasks. Agents spawning subagents may report `idle` while subagents work (False-Idle Phenomenon). Herdr exposes subagent status via Session Navigator tokens (`tokens`), displayed as `delegating` in `herdr-overview`. `herdr-wait` is subagent-aware, treating active tokens as UNSETTLED.
   **Dispatch-&-Yield is REQUIRED (not advisory) for `agy` and revision-0 agents**: Agents with background subagents (such as `agy`) report `idle` while subagents work, and weakly-recognized agents never advance revision past 0. `herdr-wait` and `herdr-prompt --wait` CANNOT reliably observe `agy` agents to completion (they fail fast with exit 2 or hang to timeout). Dispatch with `herdr-dispatch` or `herdr-prompt --no-wait`, yield turn, and await `herdr_reply.py` callback.

**Every handoff carries the envelope, and requires a reply.** Prompts open with the envelope from "Know your post" and close with the reply contract:

```text
<envelope: A2A frontmatter — id (Task-ID), context_id (sender session), status (state, timestamp), metadata (ticket_id, sender, receiver, task_group, group, and in_reply_to on replies; pass --verbose to add cwd/resume) — then the Herdr skill notice on its own line>

<the payload (Synthesized IDD/GDD Ticket)>

On completion, reply to the sender in one message using the herdr helper script:
  uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file <reply-payload.md> --ticket '<ticket-id>'
```

The rendered contract also carries the SHA guard's waiver route in prose, quoted verbatim from the rendered line: "If the reply quotes a review id such as '0c81f04c' that names no commit, the SHA guard refuses it: waive that token by name with --allow-unresolvable-sha '0c81f04c' (one flag per token, reported on stderr)."

`STATUS` is `COMPLETED`, `BLOCKED`, or `REJECTED`; a blocked callee names what it needs. `metadata.sender` holds the addressable agent name. Underlying commands, if driven directly:
- `herdr pane rename <PANE_ID> [LABEL]... [--clear]` — visible label; multi-word; **not** addressable.
- `herdr agent rename <TARGET> <NAME>|--clear` — addressable name; `[a-z][a-z0-9_-]{0,31}`, unique among live agents.
- `herdr agent start <NAME> --kind <kind> --pane <id>` — name an agent as you create it.
Full command splits: `$SKILL_DIR/references/cli-reference.md`. Multi-tier lane details: [Hierarchical Lane Coordination](references/lane-coordination.md) with bound architectural skills (`keel`, `coding-protocol`, `programming-expert`).

## Start and coordinate an agent

Before starting agents, confirm with user role-to-agent mapping (kind, provider, model). Never assume defaults. See `$SKILL_DIR/references/agent-bootstrap.md` for templates and model flags.

Default to sibling panes in current tab and `$PWD`. Pre-allocating one isolated worktree per task group with `herdr_worktree.py` is required for multi-agent lane coordination (see [Hierarchical Lane Coordination](references/lane-coordination.md)). Split with `herdr-pane`:

```bash
uv run "$SKILL_DIR/scripts/herdr_pane.py"              # auto direction from caller aspect ratio
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical     # stack below caller (--direction down)
uv run "$SKILL_DIR/scripts/herdr_pane.py" horizontal   # place right of caller (--direction right)
```

Start supported agents in available shell panes with unique names:

```bash
herdr agent start reviewer --kind <kind> --pane <returned-pane-id>
```

`herdr_bootstrap.py` folds setup into one command: stamps ROLE INVARIANT, sets pane label, starts agent ([agent-bootstrap.md](references/agent-bootstrap.md)). Pass native args after `--`:

```bash
herdr agent start reviewer --kind <kind> --pane <returned-pane-id> -- <agent-args...>
```

Agent quirks: `pi` supports `--approve` (`-a`); `qodercli` bypasses permissions via `--permission-mode bypass_permissions` and requires folder trust (`herdr agent send-keys <name> enter`). Details: `$SKILL_DIR/references/agent-bootstrap.md`. Wait until agents settle (`idle` or `done`) before prompting:

```bash
herdr agent prompt reviewer "Review the current diff and report only actionable findings." --wait --timeout 120000
herdr agent wait reviewer --until blocked --timeout 120000
```

> [!WARNING] Never wait on a background agent with `--until idle` alone. Background completions settle to `done`, not `idle`, causing waits to hang. Omit `--until` (defaults to `idle`, `done`, `blocked`) or pass `--until idle --until done`, and set `--timeout`.

Control keys:
```bash
herdr agent send-keys reviewer esc
herdr agent send-keys reviewer ctrl+c
```

### Observe an agent deterministically

`herdr agent get <target>` returns the agent session record including its transcript file path:

```bash
transcript=$(herdr agent get reviewer | jq -r '.result.agent.agent_session.value')
tail -n 40 "$transcript"
```

`agent_session.value` holds complete turn history. Fall back to terminal snapshots only when no session path exists:

```bash
herdr agent read reviewer --source recent-unwrapped --lines 120
```

If waits fail or return `blocked`, inspect `agent get` and transcripts before sending input.

## Coordinate several agents

The primary workflow for multi-agent fan-out is **Dispatch & Yield (Event-Driven)**:

1. **Dispatch, then yield.** Broadcast to several callees in one call:
```bash
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee1 callee2 --file task.md --no-wait
```
2. **Inspect session transcripts on wake**, never a poll loop:
```bash
uv run "$SKILL_DIR/scripts/herdr_transcript.py" callee1 --last
```

**`herdr-wait` is strictly a fallback, not the primary coordination signal.** Coding agents with background subagents report `idle` while waiting on subagents, causing premature settlement. `herdr_reply.py` callbacks are the only reliable completion signal. If using the barrier fallback:

```bash
uv run "$SKILL_DIR/scripts/herdr_wait.py" callee1 callee2 --timeout 300000
```

The barrier exits 3 if any target blocks. Re-enter the barrier after unblocking.
- **Sibling reviewer**: Place on isolated worktrees or detached reads; inspect `git diff <base>..<sha>` and `git show <sha>:<path>`. Never write to implementer trees.
- **Context isolation**: Spawning internal subagents keeps orchestrator/TM contexts clean ([Hierarchical Lane Coordination](references/lane-coordination.md)).
- **Banned: polling loops**: Never `sleep`, `schedule`, or loop `herdr agent read`. Use `herdr-wait` or `herdr pane wait-output --match`. Pre-flight readiness checks use one `herdr agent read --source visible` snapshot. Details: `$SKILL_DIR/references/cli-reference.md`.

## Run an ordinary command in another pane

Create a sibling pane:

```bash
uv run "$SKILL_DIR/scripts/herdr_pane.py"
```

Run and inspect commands:

```bash
herdr pane run <returned-pane-id> "just test"
herdr pane wait-output <returned-pane-id> --match "test result" --timeout 120000
herdr pane read <returned-pane-id> --source recent-unwrapped --lines 120
```

`pane run` sends command text and Enter. `pane wait-output` matches with `--match <text>` or `--regex <pattern>`. `uv run "$SKILL_DIR/scripts/herdr_pane.py" --pane <id> --command '<line>'` sends a launch line with an exit sentinel (`[herdr-launch] finished exit=<rc>`). Group background jobs as `( <line> & )`. Details: `$SKILL_DIR/references/cli-reference.md`.

## Safety and coordination rules

- Always use harness scripts in `$SKILL_DIR/scripts/` (e.g. `herdr_overview.py`, `herdr_pane.py`, `herdr_prompt.py`, `herdr_reply.py`, `herdr_dispatch.py`), NOT bare `herdr` CLI commands, for orientation, layout, agent communication, prompting, and waiting.
- Name every pane immediately with meaningful text matching its role (`orchestrator`, `task-manager`, `impl-auth`, `reviewer`) using `herdr-pane --label` or `herdr-label`.
- Orient with `herdr-overview` before enumerating panes, tabs, or agents. Do not run `herdr pane layout`, `pane list`, `tab list`, `workspace list`, or `agent list` to reconstruct layout.
- NEVER use `herdr pane send-text` or `herdr pane send-keys` to deliver prompts or replies. Raw text sent to an idle shell executes as shell commands.
- Confirm role-to-agent mapping (kind, provider, model) with user before starting agents. Verify folder trust ($SKILL_DIR/references/agent-bootstrap.md).
- Use `--no-focus` for background work unless switching context is requested.
- Use `--current`, an explicit pane ID, or unique agent name. Do not rely on another client's focus.
- Parse IDs from JSON responses. Server errors exit 1; syntax errors exit 2.
- Never take consent-gated or irreversible actions (closing workspaces, `--trust-repository`, `herdr server stop`) without explicit user intent ($SKILL_DIR/references/safety-rules.md).

## Local helpers (not upstream)

> [!IMPORTANT] Method Constraint
> Always execute these 11 harness scripts in `$SKILL_DIR/scripts/` instead of bare `herdr` CLI commands. Bare CLI commands bypass argument quoting, caller context injection, target safety checks, and delivery verification.

All 11 scripts run directly through `uv run`. All except `herdr_agy_bridge.py` and `herdr_worktree.py` require `HERDR_ENV=1` and share the `herdr_cli.py` adapter. All exit `0` ok, `1` herdr failure, `2` usage or missing precondition; `herdr-prompt`, `herdr-dispatch`, and `herdr-reply` exit `3` for human input needed and `4` for timeout; `herdr-wait` exits `3` for blocked targets.

| Script / Helper | Primary Purpose | Standard Invocation | Key Options |
|---|---|---|---|
| `herdr-overview` | Orient session, list task groups & panes | `uv run $SKILL_DIR/scripts/herdr_overview.py --tab` | `--tab [ID\|NAME]`, `--task-group <SLUG>`, `--format [rich\|markdown\|yaml\|json]`, `--json` |
| `herdr-bootstrap` | Bootstrap agent with role invariant & scoped name | `uv run $SKILL_DIR/scripts/herdr_bootstrap.py <name> --kind <kind> --pane <id> --role <role>` | `--task-group <SLUG>`, `--model <M>`, `--cwd <DIR>`, `--settle <SEC>`, `--dry-run` |
| `herdr-label` | Name/label pane, scope role, rename tab | `uv run $SKILL_DIR/scripts/herdr_label.py <name> [--task-group <slug>]` | `--tab <NAME>`, `--task-group <SLUG>`, `--pane <ID>`, `--verify`, `--sync` |
| `herdr-pane` | Split caller pane, or run a launch line with a sentinel | `uv run $SKILL_DIR/scripts/herdr_pane.py horizontal --label <name>` | positional `DIRECTION` (`vertical`/`horizontal`), `--command <LINE>`, `--label <L>`, `--task-group <SLUG>`, `--cwd <DIR>`, `--no-focus` |
| `herdr-worktree` | Bind each role to an isolated git worktree | `uv run $SKILL_DIR/scripts/herdr_worktree.py` | `allocate`, `resolve`, `list`, `claim`, `status`, `retire`, `doctor [--prune]`, `--base <B>`, `--json` |
| `herdr-dispatch` | Dispatch ticket with task lease & envelope | `uv run $SKILL_DIR/scripts/herdr_dispatch.py <callee> --file <task.md> --no-wait` | `--ticket-id <ID>`, `--task-id <ID>`, `--draft`, `--settle <SEC>`, `--wait`, `--no-wait`, `--force` |
| `herdr-reply` | Deliver completion callback & release lease | `uv run $SKILL_DIR/scripts/herdr_reply.py <caller> --file <reply.md>` | Auto-populates `metadata.in_reply_to` & `metadata.ticket_id`, `--ticket <ID>`, `--in-reply-to <RECORD>`, `--auto-start <KIND>`, `--settle <SEC>`, `--wait`, `--allow-unresolvable-sha <TOKEN>` |
| `herdr-prompt` | Deliver byte-exact payload with envelope | `uv run $SKILL_DIR/scripts/herdr_prompt.py <target> --file <brief.md> --no-wait` | `--label <L>`, `--wait`, `--no-wait`, `--timeout <MS>`, `--no-caller-context` |
| `herdr-wait` | Multi-agent state barrier (fallback) | `uv run $SKILL_DIR/scripts/herdr_wait.py <target1> <target2> --timeout 300000` | `--any`, `--until [idle\|done\|blocked]`, `--json` |
| `herdr-transcript`| Read clean assistant text from session JSONL | `uv run $SKILL_DIR/scripts/herdr_transcript.py <target> --last` | `--last`, `--role [user\|assistant\|all]`, `--lines <N>`, `--json` |
| `herdr-agy-bridge`| Install OSC 0 lifecycle hooks for Antigravity | `uv run $SKILL_DIR/scripts/herdr_agy_bridge.py --install` | `--install`, `--uninstall`, `--status`, `--project` |

### `herdr-overview` — the session at a glance

Displays panes grouped by workspace and Task Group (Tab) with id, agent kind, agent name, label, live subagent tokens (`delegating`), and cwd; calling pane marked `*`. TTY outputs styled rich tables; piped output defaults to markdown tables (`--format markdown`) or `--json` / `--yaml`. Filter with `--tab [ID|NAME]` or `--task-group <NAME>`.

### `herdr-label` — the one name that is both visible and addressable

Sets pane label and agent name to the same string:

```bash
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer            # label + agent name
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer --pane w1:p2
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer --label-only  # multi-word label, agent untouched
uv run "$SKILL_DIR/scripts/herdr_label.py" --clear             # drop both
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer --json
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer --dry-run   # print the calls, rename nothing
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer --task-group msg   # scoped name: msg-reviewer
uv run "$SKILL_DIR/scripts/herdr_label.py" --tab msg-enhance     # rename the calling tab (Task Group)
```

Refuses names violating agent name patterns or already held by live agents. Validates before renaming. Use `--label-only` for multi-word labels on occupied panes. `--task-group <slug>` scopes bare roles; `--tab <NAME>` renames the calling tab.

### `herdr-pane` — split the calling pane

Env-check, resolution, and splitting in one command:

```bash
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical          # stack a pane below the caller (--direction down)
uv run "$SKILL_DIR/scripts/herdr_pane.py" horizontal        # place a pane right of the caller (--direction right)
uv run "$SKILL_DIR/scripts/herdr_pane.py"                   # caller wider than tall -> right, else down
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical --label reviewer  # split and label in one command (-l)
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical --label impl-1 --task-group msg  # label: msg-impl-1
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical --focus --ratio 0.3 --env FOO=bar --cwd /tmp
uv run "$SKILL_DIR/scripts/herdr_pane.py" horizontal --dry-run  # print the herdr command, split nothing
```

Guards `HERDR_ENV=1`, resolves the caller with `herdr pane current --current`, selects auto direction from `herdr pane layout --pane <id>`, and prints the new pane id, direction, caller, cwd, and focus.

### `herdr-bootstrap` — stamp the role invariant, then start the agent

Writes a compaction-proof `ROLE INVARIANT` into the target agent launch surface, sets the pane label, and starts the agent:

```bash
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" msg-impl-1 --kind codex --pane w1:p3 --role impl-1 --task-group msg
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" --kind pi --pane w1:p3 --role tm --task-group msg --model claude-3-7-sonnet
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" msg-tm --kind claude --pane w1:p2 --role tm --dry-run
```

Appends system prompt directly for supported agents (per `references/kinds.yaml`) or writes an idempotent marker to `AGENTS.md`. Sets trust flags from `references/kinds.yaml`. Validates pane cwd and worktree registration. Details: [agent-bootstrap.md](references/agent-bootstrap.md).

### `herdr-worktree` — one isolated worktree per role

Binds one isolated git worktree per role (`<repo>.<task-group>.<role>`) with branches under `lane/<task-group>/<role>/<ticket>`. `claim` executes a guarded in-place transition requiring a clean tree and explicit `--base`. Allocations persist in `.lane/tasks.yaml`.

```bash
WORKTREE_PATH=$(uv run "$SKILL_DIR/scripts/herdr_worktree.py" claim ../repo.w11-t7.impl-1 lane/w11-t7/impl-1/184-worktree --base main)
uv run "$SKILL_DIR/scripts/herdr_worktree.py" status --worktree "$WORKTREE_PATH" --json
uv run "$SKILL_DIR/scripts/herdr_worktree.py" retire "$WORKTREE_PATH"
uv run "$SKILL_DIR/scripts/herdr_worktree.py" doctor --prune
uv run "$SKILL_DIR/scripts/herdr_worktree.py" list --json
```

`status` reports branch state and namespace conformance. `retire` cleans merged trees safely. `doctor` audits stale entries. Never run force-switch or stash commands inside lane trees.

### `herdr-dispatch` — manager-side task dispatch

Dispatches tickets with caller context and reply contracts, acquires task leases, and verifies delivery:

```bash
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --file task.md --no-wait
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --file task.md --ticket-id "#182-msg" --task-id "#182-msg#impl-1" --no-wait
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --file task.md --wait --timeout 15000
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee1 callee2 --file task.md --no-wait
```

Requires `--file` unless `--draft` is passed. When omitted, `herdr-dispatch` derives Ticket-ID from file basenames (a leading-number stem like `182-foo.md` becomes `#182-foo`; stems starting with `#` are used as-is; others are used verbatim). Persists task records and `caller_recovery` into `.lane/tasks.yaml`. Refuses bare agent kinds.

`--auto-start <KIND>` bootstraps bare shell panes using `herdr_bootstrap.py` rules before dispatching. Settles new spawns before ticket delivery (`--settle` default 5s). Live agents dispatch with no extra overhead.

Before injecting bytes, it runs the pre-flight gate: probes `herdr agent get <target>` up to 10s until ready, confirms readiness with a `herdr agent read --source visible` snapshot to detect modal dialogs (falling back to `--skip-screen-check` if needed), and prompts. Under `--no-wait`, unconfirmed observation warns on stderr and exits 0 (acceptance confirmed by `herdr agent prompt`).

`--draft` generates ticket skeletons prefilled from live state:

```bash
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --draft --file task.md
```

### `herdr-reply` — callee completion callback

Delivers `<STATUS> <artifacts> <issues>` or result payloads to the sender, wrapped in the A2A envelope:

```bash
uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator "COMPLETED deadbeef evidence: 660 passed; scripts/check.sh" --ticket '<ticket-id>'
uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file result.md --ticket '<ticket-id>'
uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file - --ticket '<ticket-id>' <<'EOF'
COMPLETED deadbeef

## Evidence
- 660 passed; scripts/check.sh
EOF
uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator "COMPLETED deadbeef evidence: 660 passed; scripts/check.sh" --ticket '<ticket-id>' --wait --timeout 15000
uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file result.md --ticket '<ticket-id>' --auto-start pi
```

`herdr-reply` inspects `.lane/tasks.yaml` for sender leases, populates correlation envelope fields, maps status tokens (`COMPLETED`→`completed`, `BLOCKED`→`blocked`, `REJECTED`→`rework`), appends trajectory events, and soft-releases the sender lease upon delivery. Explicit `--ticket <ID>` or `--in-reply-to <RECORD>` takes precedence. Unlinked replies warn on stderr without guessing linkage. Validates target agent names and reports delivery. Never use bare `herdr agent prompt` directly for replies.

Before that, the payload itself must be honest about its SHAs: every backticked 7-40 lowercase-hex token in the outbound body is checked with `git rev-parse --verify <token>^{commit}` against this lane's repository, because a backticked hex token is an instruction rather than prose — a "do not rewrite" list whose token drifted by one digit points at nothing (#247). Tokens that move the object store (`GIT_DIR`, `GIT_OBJECT_DIRECTORY`) skip loudly; non-commit tokens refuse delivery (exit 2). Waive intentional non-commit tokens by name using `--allow-unresolvable-sha <TOKEN>`.

Persists reply bodies to `.lane/replies/<id>.md` with metadata sidecar `.lane/replies/<id>.yaml`. Inserts `Payload: COMPLETE` or `Payload: INCOMPLETE` (if evidence is missing) between envelope and body; unrecorded stores degrade to `Payload: NOT RECORDED`. An evidence section requires an evidence keyword heading, `**Evidence:**`, or content code fence. Inspect stored replies via `uv run "$SKILL_DIR/scripts/herdr_lease.py" replies [ID]`.

### `herdr-prompt` — deliver a payload verbatim

Delivers byte-exact payloads without shell escaping issues:

```bash
uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --file brief.md --wait --timeout 120000
uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --file - < brief.md
git diff | uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --wait
uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --file brief.md --wait --dry-run
```

Reads payload from `--file` or stdin (`-`). Accepts multiple targets for broadcast (`herdr-prompt callee1 callee2 --file brief.md --no-wait`). Under `--wait`, timeout after delivery exits 4 (prompt accepted, callee working asynchronously). Prepends A2A frontmatter envelope and Herdr skill notice, and appends the reply contract. Shares the pre-flight readiness gate with `herdr-dispatch` (probing `herdr agent get <target>` and checking `herdr agent read --source visible`). Use `--skip-screen-check` or `--dry-run` as needed.

### `herdr-wait` — one barrier over many agents

Polls `herdr agent get <target>` across targets:

```bash
uv run "$SKILL_DIR/scripts/herdr_wait.py" action1 action2 --timeout 300000
uv run "$SKILL_DIR/scripts/herdr_wait.py" review1 review2 --any
uv run "$SKILL_DIR/scripts/herdr_wait.py" action1 action2 --json
```

Settled means `idle`, `done`, or `blocked`. Weakly-recognized revision-0 agents (`agy`) fail fast with exit 2 steering callers to Dispatch & Yield (`herdr-reply`). Any blocked target exits 3. Use `--stale-after SEC` for optional staleness advisories.

### Managed Antigravity (agy) bridge

Manages OSC 0 lifecycle hooks for Antigravity (`~/.gemini/config/hooks.json` globally, or `.agents/hooks.json` with `--project`), deploying `hooks/herdr-agy-bridge.sh`:

```bash
uv run "$SKILL_DIR/scripts/herdr_agy_bridge.py" --install             # global (default)
uv run "$SKILL_DIR/scripts/herdr_agy_bridge.py" --install --project   # repo .agents/hooks.json
uv run "$SKILL_DIR/scripts/herdr_agy_bridge.py" --status --json
uv run "$SKILL_DIR/scripts/herdr_agy_bridge.py" --uninstall
```

Publishes OSC 0 titles (`agy: idle`, `agy: working (subagents)`, `agy: blocked (permission)`). Generic helpers branch on observables, never agent kinds.

### `herdr-transcript` — clean text from the session file

Resolves session files via `herdr agent get <target>` and extracts clean assistant text:

```bash
uv run "$SKILL_DIR/scripts/herdr_transcript.py" review1 --last
uv run "$SKILL_DIR/scripts/herdr_transcript.py" review1 --role user
uv run "$SKILL_DIR/scripts/herdr_transcript.py" review1 --role all --json
```

Falls back to `herdr agent read <target> --source recent-unwrapped --lines 120` when no session file exists. Tests for all 11 helpers: `tests/herdr/`.
