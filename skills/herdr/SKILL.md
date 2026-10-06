---
name: herdr
description: >-
  Herdr terminal-multiplexer reference for coding agents. Inspects and drives panes, tabs, workspaces, and sibling agents; waits on test or server output. Use when the user mentions Herdr or asks to inspect pane layout or drive agents. Requires HERDR_ENV=1; not for background terminals or delegation.
metadata:
  author: herdrdev
  version: '0.9.0'
---

# Herdr

Vendored from `herdrdev/herdr@v0.9.0`; `herdr --skill` prints the installed binary's own copy, authoritative for that binary.

Herdr organizes terminals into workspaces, tabs, and panes, recognizes coding agents running inside panes, and exposes the current session through the `herdr` CLI.

Before issuing any control command, verify that this agent is running inside a Herdr-managed pane:

```bash
[ "${HERDR_ENV:-}" = 1 ]
```

Prefer bracket syntax `[` over `test`: tool-rewriting extensions (such as `rtk` in `pix-optimizer`) hook `test` as an application test runner (e.g. `npm test`), causing `sh: 1: command not found`.

If the check fails, say that you are not running inside Herdr and stop. Do not inspect or control the focused Herdr session from outside Herdr.

When the check passes, the `herdr` binary in `PATH` talks to the current session. Use it to inspect neighboring work, create terminal layout, start agents and commands, read output, and wait for state changes.

## Know your post

Your post is your agent name at your pane id. Read it from the environment, never guess it:

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
uv run "$SKILL_DIR/scripts/herdr_overview.py" --current
```

`herdr-label` turns a bare pane into a post: it sets the pane label and the agent name to the same string, so the name a person reads off the border is the name you can address.

Every cross-pane message carries a script-rendered envelope:

```text
[2026-10-05T06:19:12.983Z]
Sender: orchestrator@w1:p1 - tab w1:t1 - kind pi
Group: orchestrator@w1:p1, impl-1@w1:p3, impl-2@w1:p4
Resume: "pi --resume /path/to/session.jsonl"
Cwd: /Users/zhengxk/workspace
Herdr: see skill ~/.agents/skills/herdr/SKILL.md — use scripts in ~/.agents/skills/herdr/scripts/ for communication, not bare herdr CLI

Receiver(You): impl-1@w1:p3 - tab w1:t1 - kind pi
```

`herdr-prompt`, `herdr-dispatch`, and `herdr-reply` render those lines from live Herdr state and prepend them to every payload, in both directions. Role, position, roster, and the resumption triple (`kind + session + cwd`) therefore arrive with the message whether or not the sender remembered them; an absent field renders no line at all. `Receiver(You)` closes the envelope alone and names *you* with *your* position — read it first when several panes were addressed at once. Relay a message with its envelope intact; a message that arrives without a `Sender:` line did not come from these scripts.

The token before `@` is the **live agent name**, the only human-readable target `herdr agent prompt` accepts besides the pane id. A pane **label** is border decoration and is never a target, so it always rides its own `label` field — a pane that carries only a label renders as its pane id:

```text
Sender: w1:p4 - label pr-orchestrator - tab w1:t1 - kind agy
```

To address that pane, use its pane id, or let `herdr-prompt --label pr-orchestrator` resolve the label for you. See `$SKILL_DIR/references/cli-reference.md` for the full names/labels/targets rules.

> [!IMPORTANT] Orient First, Then Use Harness Scripts
> Always use harness scripts in `$SKILL_DIR/scripts/` (e.g. `herdr_overview.py`, `herdr_pane.py`, `herdr_prompt.py`, `herdr_reply.py`, `herdr_dispatch.py`), NOT bare `herdr` CLI commands, for orientation, layout, agent communication, prompting, and waiting.

## Orient with `herdr-overview` first

One call answers "what is here, and which pane or agent do I act on?" — pane ids, agent kinds, agent names, labels, live subagent tokens (`delegating` state), and cwd, grouped by workspace, with the calling pane marked `*`. It joins pane labels with agent names and subagent tokens, which no single `herdr` list command returns. Reach for it before any `workspace list`, `tab list`, `pane list`, `pane layout`, or `agent list` probe: those return overlapping subsets, cost several round trips, and bloat the context.

```bash
uv run "$SKILL_DIR/scripts/herdr_overview.py"                 # every workspace: YAML when piped, table on a TTY
uv run "$SKILL_DIR/scripts/herdr_overview.py" --json          # JSON for programmatic parsing
uv run "$SKILL_DIR/scripts/herdr_overview.py" --workspace     # only the calling workspace
uv run "$SKILL_DIR/scripts/herdr_overview.py" --tab           # only the calling tab
uv run "$SKILL_DIR/scripts/herdr_overview.py" --current       # only the calling pane
uv run "$SKILL_DIR/scripts/herdr_overview.py" --format table  # force a format
```

Piped output is YAML with a `# Format: YAML (pass --json for JSON)` header; pass `--json` when a script parses it. Orientation is done when you can name the target pane id or agent name.

Panes and agents that do not exist yet come from creation responses, not from re-listing: `workspace create` returns `.result.workspace`, `.result.tab`, and `.result.root_pane`; `tab create` returns `.result.tab` and `.result.root_pane`; `pane split` returns `.result.pane`.

## Learn the current CLI

The installed binary is the authority for command syntax. Start with `herdr --help`, then print a command group by running the group without a subcommand (`herdr agent`, `herdr pane`, and the rest). Do not run bare `herdr` for discovery; it launches the TUI. Do not probe a mutating nested command by omitting arguments — commands such as `herdr workspace create` are valid with defaults and will execute.

Most control commands return JSON. Read identifiers and state from those responses instead of predicting them.

The full command-group inventory, read sources, and connection profiles live in `$SKILL_DIR/references/cli-reference.md`.

## Understand layout, panes, and agents

Choose the primitive that matches the job:

- Workspace, tab, and pane topology organize terminal locations.
- Pane commands control raw terminals, shells, tests, servers, input, and output.
- Agent commands control the recognized coding agent currently occupying a pane.

A pane exists whether or not it contains an agent. `agent start` requires an existing available shell pane and never creates, splits, or moves layout. Use pane commands for ordinary processes. Use agent commands when Herdr must validate agent identity or interpret `idle`, `working`, `blocked`, `done`, and `unknown` lifecycle states.

Agent commands accept either a unique live agent name or the pane ID currently hosting that agent — not terminal IDs or bare agent-kind labels. `idle` and `done` both mean ready for input, `blocked` means an approval or question UI, and `unknown` does not prove completion. Full lifecycle and naming rules live in `$SKILL_DIR/references/cli-reference.md`.

For the live instance of this topology, orient with `herdr-overview` above instead of enumerating with `pane list` / `agent list`.

> [!WARNING] Shell Input Constraint
> NEVER use `herdr pane send-text` or `herdr pane send-keys` to deliver prompts or replies. In a raw shell pane, this executes prompt text directly as shell commands.

## Use IDs and the calling pane

Public IDs are opaque stable handles: workspace `w1`, tab `w1:t1`, pane `w1:p1`.

Prefer `--current` when a pane command should target the calling pane. Omitting a target may use the UI-focused pane, which can belong to the user or another client.

Use `herdr-overview` to find an existing pane, tab, or agent by name or label; use the creation responses above for one that does not exist yet. Do not reconstruct layout from `pane list`, `tab list`, or `agent list` probes.

## Name a target, then hand off

A person reads a pane's **label** off the pane border, so that is the name they will say when they ask you to hand something off. But no command accepts a label as a target. The **agent name** is the addressable handle, and it is cleared when that agent exits.

So give both the same string, in one command:

```bash
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer    # this pane's label and its agent name
```

> [!IMPORTANT] Name Every Pane Immediately
> Unlabeled panes (`null`) cause blind spots in `herdr-overview` and break automated reply routing. Name each pane with meaningful text matching its role (`orchestrator`, `task-manager`, `impl-auth`, `reviewer`) using `herdr-pane --label` or `herdr-label`.

`herdr-label` labels the calling pane and names its agent identically, so the name a person sees is the name you can address. It takes `--pane <id>` for another pane, `--label-only` when a multi-word label or an existing agent name must survive, and `--clear` to drop both.

The pair is not stable on its own: the **agent name dies with the agent** while the **label outlives it**, so every exit leaves a labelled pane that nothing can address, and the next occupant inherits the stale label. `herdr-label` sets both in one command, and the two checks keep them together:

```bash
uv run "$SKILL_DIR/scripts/herdr_label.py" --verify   # exit 3 when a live agent disagrees with its label
uv run "$SKILL_DIR/scripts/herdr_label.py" --sync     # converge both directions, idempotent
```

`--sync` sets a drifting label from the agent name, and names an agent that came back without one from the label that survived. A descriptive `--label-only` label and a pane with no agent are reported, never guessed at. Run `--verify` before a dispatch wave and `--sync` after any agent exits or restarts.

When a person says "hand off to <name>", pass that name straight to the prompt helper:

```bash
uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --file brief.md --wait --timeout 15000
uv run "$SKILL_DIR/scripts/herdr_prompt.py" --label "review pane" --file brief.md --wait --timeout 15000
```

`--label` matches a pane label exactly. Labels are not unique — two panes may carry the same one — so an ambiguous label fails with the candidate pane ids listed instead of guessing.

### Target resolution failures & bare shell prevention

If target resolution fails or matches a pane without an active agent (e.g. an idle shell pane):
- **Refusal**: `herdr-prompt` and `herdr-reply` refuse delivery to raw shell panes to prevent prompt text executing as shell commands.
- **Suggested recovery hook**: Diagnostics detect previous agent clues in the pane (agent attribute, title, label) and output an exact copy-paste recovery command: `Suggested recovery: herdr agent start <name> --kind <kind> --pane <id>`.
- **Auto-start**: `herdr-reply` supports `--auto-start <KIND>` to automatically start the agent on an open shell pane before delivering the reply.
- **Queue/watch**: Wait for the agent to start or monitor the pane with `herdr pane wait-output`.
- **Start agent**: Explicitly start the agent via `herdr agent start <name> --kind <kind> --pane <id>`.
- **Graceful abort**: If the caller or target agent exited, abort gracefully rather than forcing unprompted execution.
- **Safety invariant**: NEVER fall back to bare `herdr pane send-text` or `herdr pane send-keys` to deliver prompts or replies into a shell pane. In an idle shell pane, this executes markdown prose as shell commands (potentially catastrophic!).

### Dispatch & Yield (Event-Driven workflow)

Multi-agent coordination is event-driven via completion callbacks:

1. **Caller self-names:**
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_label.py" orchestrator
   ```
   Ensures the caller has a valid, addressable agent name so callees know whom to reply to.

2. **Dispatch with Synthesized IDD/GDD Tickets & Task Leases:**
   ```bash
   # Dedicated dispatch helper (checks/acquires task leases, validates agent name):
   uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --file task.md --no-wait

   # Or bypass an existing active lease:
   uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --file task.md --force --no-wait

   # Or via herdr-prompt:
   uv run "$SKILL_DIR/scripts/herdr_prompt.py" callee --file task.md --wait --timeout 15000
   ```
   - **Synthesized IDD/GDD Ticket Format**: Dispatched tickets pair upstream teleological purpose (**IDD**: Problem, Proposed Outcome, Non-Negotiable Constraints) with downstream verifiable milestones (**GDD/EDD**: Check Command, Required Evidence), preventing both Goodhart gaming and semantic drift.
   - **Task Lease Invariant**: `herdr_dispatch.py` checks active ticket leases in `.lane/lease.json` (or `.herdr-lease.json`) before dispatching, preventing ticket collisions. Target identities are canonicalized across agent name and pane ID. Leases are acquired atomically pre-dispatch and rolled back if prompt delivery fails or is blocked. Leases are retained only on prompt acceptance (`EXIT_OK` or `WaitTimeout`), and automatically released upon delivery of `herdr_reply.py`.
   - Never dispatch tasks via bare `herdr agent prompt callee` directly — doing so drops the `Sender:`/`Receiver:` envelope, the resumption triple, and the reply contract.
   - *Prompt acceptance invariant*: Exit code 0 from `herdr agent prompt` confirms acceptance. Revision numbers are purely informational; prompts are never re-injected or dropped due to unchanged revisions (#193).

3. **Yield turn on async execution:**
   If `herdr-prompt` exits 4 (timeout) or was dispatched with `--no-wait`, the prompt was delivered and the callee is working asynchronously. The orchestrator yields turn (stops calling tools, enters idle).

4. **Callee executes completion callback (and releases lease):**
   Upon completion or blocking, the callee executes the contract callback via `herdr_reply.py`, adhering to the settled **Final Reply Template** (`resp-format.md`):
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file reply.md
   # Or inline:
   uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator "COMPLETED <sha> ..."
   # Or auto-start the caller agent if its turn exited back to an open shell pane:
   uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file reply.md --auto-start pi
   ```
   The reply payload contains:
   - Status Triad: `COMPLETED <commit-sha>` | `BLOCKED <reason>` | `REJECTED <reason>`
   - `## Summary` (Carmack-style technical rationale, ≤100 words)
   - `## Artifacts` (absolute paths with kinds: diff, spec, report, eval, pr)
   - `## Evidence` (deterministic command checks: PASS / FAIL)
   - `## Route` (`continue | remediate | blocked`)
   - `## Issues` (P1/P2/P3 severity with file:line, invariant, defect, remediation; or `None`)
   - `## Suggestions` (optional non-blocking environment observations)

   Delivering this reply prompts the caller pane directly without shell mangling, waking its turn with the result, and automatically releases the replying callee's active task lease. Never use bare `herdr agent prompt` directly for replies.

5. **Subagent Observability & `herdr-wait`:**
   **Subagent-First Execution**: In lane coordination, agents MUST use subagents for heavy tasks (exploration, bulk edits, test triage, and crux review). When agents spawn subagents, they may report `idle` while subagents work (the False-Idle Phenomenon). Herdr exposes live subagent status via Session Navigator tokens (`tokens`), displayed as `delegating` in `herdr-overview`.
   `herdr-wait` is subagent-aware: it checks `tokens.summary` and `tokens.title-suffix`, treating any agent with active subagent tokens as UNSETTLED (preventing premature wait barrier exits).
   `herdr-wait` is strictly a fallback for non-agent panes or watchdog recovery; Dispatch-&-Yield is the primary coordination pattern.
   **Dispatch-&-Yield is REQUIRED (not advisory) for `agy` and revision-0 agents**: Agents with background subagents (such as `agy`) report `idle` while their subagents work, and weakly-recognized agents never advance revision past 0. `herdr-wait` and `herdr-prompt --wait` CANNOT reliably observe `agy` agents to completion (they fail fast with exit 2 or hang to timeout). You must dispatch with `herdr-dispatch` or `herdr-prompt --no-wait`, yield turn, and await the `herdr_reply.py` callback.

**Every handoff carries the envelope, and requires a reply.** A callee cannot address a sender it was never told about, and a sender left to infer completion falls back on polling. So the prompt opens with the envelope from "Know your post" and closes with the reply contract:

```text
<envelope: timestamp, Sender, Group, Resume, Cwd, Herdr notice, blank line, Receiver(You)>

<the payload (Synthesized IDD/GDD Ticket)>

On completion, reply to the sender in one message using the herdr helper script:
  uv run ~/.agents/skills/herdr/scripts/herdr_reply.py orchestrator --file <reply-payload.md>
```

`STATUS` is `COMPLETED`, `BLOCKED`, or `REJECTED`; a blocked callee names what it needs instead of waiting silently. The **agent name** is the load-bearing part of a `Sender:` line — the pane id and label tell a person where to look, and only the name is addressable.

Underlying commands, if you drive them directly:

- `herdr pane rename <PANE_ID> [LABEL]... [--clear]` — the visible label; multi-word; **not** addressable.
- `herdr agent rename <TARGET> <NAME>|--clear` — the addressable name; `[a-z][a-z0-9_-]{0,31}`, unique among live agents.
- `herdr agent start <NAME> --kind <kind> --pane <id>` — name an agent as you create it.

The full split, including which response returns which name, is in `$SKILL_DIR/references/cli-reference.md`.

For multi-tier lanes where an in-lane Task Manager coordinates one or more Implementers, see [Hierarchical Lane Coordination](references/lane-coordination.md) for non-overlapping role boundaries (Orchestrator, TM, Implementer), bound architectural skills (`keel`, `coding-protocol`, `programming-expert`), reconnaissance budgets, TM code review subagents, implementer context isolation, the subagent-first execution mandate, task leases, and token observability.

## Start and coordinate an agent

Before starting any agent or orchestrating tasks, confirm with the user which role should use which coding agent kind, provider, and model (e.g. `pi` with Anthropic `claude-3-7-sonnet`, `qodercli` with a specific model). Never assume or pick defaults. See `$SKILL_DIR/references/agent-bootstrap.md` for the confirmation template, bootstrap command matrix, and provider/model flags.

Default to a sibling pane in the current tab and the current working directory. Do not create a workspace, tab, worktree, or different cwd unless the user explicitly requests that topology or location — except for multi-agent lane coordination (or whenever a worktree tool such as `wt` is present), where pre-allocating one isolated worktree per task group with `herdr_worktree.py` is required and overrides this single-agent `$PWD` default (see [Hierarchical Lane Coordination](references/lane-coordination.md)).

Split with `herdr-pane`, which runs the env check, resolves the caller, picks the direction from the caller's aspect ratio (`wide -> right`, `tall -> down`), and preserves the caller's `$PWD` and focus — one command, no `pane layout` round trip:

```bash
uv run "$SKILL_DIR/scripts/herdr_pane.py"              # auto direction from the caller's aspect ratio
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical     # stack below the caller (--direction down)
uv run "$SKILL_DIR/scripts/herdr_pane.py" horizontal   # place right of the caller (--direction right)
```

Honor a direction the user requested by passing the word that means it. Avoid repeated same-direction splits that create unusably narrow columns or short rows. The helper prints `new pane <id>  direction=…  caller=…  cwd=…  focus=…`; use that id for `agent start`.

An available shell pane must be at its interactive prompt, with the shell itself in the foreground and no foreground command, editor, or agent running. Start a supported agent in that pane with a useful unique name:

```bash
herdr agent start reviewer --kind <kind> --pane <returned-pane-id>
```

Always use the kind requested by the user. Run `herdr agent` to inspect installed kinds and list them when asking. Pass native agent arguments only after `--`:

```bash
herdr agent start reviewer --kind <kind> --pane <returned-pane-id> -- <agent-args...>
```

Different coding agents have different bootstrap commands and folder trust requirements:
- `pi`: supports `--approve` (`-a`) after `--` to trust project-local files without interactive blocking.
- `qodercli`: YOLO via `--permission-mode bypass_permissions` after `--`, and requires trusting the folder before automated prompts reach it. `agent start` still reports `interactive_ready: true` while the trust selector is up, and its `Ready` title is false — read the pane, then send one bare Enter (`herdr agent send-keys <name> enter`) or pre-seed `permissions.trustDirectories` in the config root the binary reads.
- Full agent matrix, model flags, and quirks: `$SKILL_DIR/references/agent-bootstrap.md`.

A successful `agent start` returns only after Herdr detects the expected agent in the same pane and considers it ready for interactive input. Verify folder trust and wait until the agent settles (`idle` or `done`) before prompting it.

Submit work through the agent surface:

```bash
herdr agent prompt reviewer "Review the current diff and report only actionable findings." --wait --timeout 120000
```

`agent prompt` honors the pane's live bracketed-paste mode and sends text followed by encoded Enter as one ordered submission. For multi-line or metacharacter-heavy payloads, deliver through the `herdr-prompt` helper below instead of quoting the text at the shell. For normal agent work, `--wait` is enough: it waits for the first settled `idle`, `done`, or `blocked` state. Do not repeat those defaults with `--until`; use `--until` only for a state-specific workflow, such as waiting for an already-running agent to request input:

```bash
herdr agent wait reviewer --until blocked --timeout 120000
```
> [!warning] Never wait on a background agent with `--until idle` alone. Background completions settle to `done`, not `idle`, so the wait ignores the completion event and hangs (#83). Omit `--until` (defaults to `idle`, `done`, `blocked`) or pass `--until idle --until done`, and always set `--timeout` so no wait outlives the turn.
The submission-failure semantics (`agent_blocked`, `agent_prompt_stalled`, `timeout`) and the `--wait` activity gate live in `$SKILL_DIR/references/cli-reference.md`.

Use logical keys for interactive agent UI controls:

```bash
herdr agent send-keys reviewer esc
herdr agent send-keys reviewer ctrl+c
```

Herdr validates all keys before writing any bytes.

### Observe an agent deterministically

`herdr agent get <target>` returns the agent's session record, which includes a transcript the agent itself owns. Read the transcript path and then the file directly:

```bash
transcript=$(herdr agent get reviewer | jq -r '.result.agent.agent_session.value')
tail -n 40 "$transcript"
```

`agent_session.value` is a filesystem path (`kind: "path"`), for example `~/.pi/agent/sessions/<workspace>/<timestamp>_<uuid>.jsonl`. It holds the complete turn history, unlike a terminal snapshot, which clips once rendered rows scroll off or the agent uses the terminal's alternate screen.

Fall back to the terminal view only when the record carries no `agent_session` path:

```bash
herdr agent read reviewer --source recent-unwrapped --lines 120
```

If a wait fails or returns `blocked`, inspect `agent get` and the transcript before deciding what input to send. If a wait exits settled yet the pane still shows WORKING, re-enter the barrier and read the pane — the state feed is not a trustworthy completion signal on weakly-recognized (agy, revision 0, no session) panes; never poll it with a grep/read loop. A timeout or stalled response does not prove the prompt was never delivered; do not blindly submit it again. Use the pane surface only when raw terminal control is intentional.

## Coordinate several agents

The primary workflow for multi-agent fan-out is **Dispatch & Yield (Event-Driven)**:

1. **Dispatch, then yield.** The canonical sequence — caller self-names, callees receive the caller context and reply contract, the orchestrator yields turn, the `herdr-reply` callback wakes it — is the Dispatch & Yield block above. Broadcast to several callees in one call:

```bash
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee1 callee2 --file task.md --no-wait
```

2. **Inspect session transcripts on wake**, never a poll loop:

```bash
uv run "$SKILL_DIR/scripts/herdr_transcript.py" callee1 --last
```

**`herdr-wait` is strictly a fallback, not the primary coordination signal.** The event-driven callback model ensures completion arrives without the orchestrator holding a wait, burning context, or looping. External `agent_status` detection is untrustworthy for coding agents with background subagents (such as `agy`): the primary agent reports `idle` while waiting on subagents even though the task is still actively running, causing false early settlements or indefinite revision-0 holds. Event-driven `herdr_reply.py` callbacks are the only reliable completion signal. Keep `herdr-wait` strictly for non-agent panes, panes without an agent name, or watchdog recovery when a callee fails to report back. Sequential `herdr agent wait A && herdr agent wait B` starves B while A runs: if B finishes or blocks in 10s and A runs 5 minutes, B is ignored for 5 minutes. If using the barrier fallback:

```bash
uv run "$SKILL_DIR/scripts/herdr_wait.py" callee1 callee2 --timeout 300000
```

The barrier exits 3 the moment any target needs input — unblock it, then re-enter the barrier for the rest. Distrust its first tick: a callee that has not begun still reads `idle`, so a barrier can return in 0ms having observed the state *before* the work. Re-enter it rather than concluding the work is done.

### Sibling-reviewer pattern

Place the reviewer next to the implementer in the same working directory so findings cite the same tree: split a sibling pane from the implementer's pane, start the reviewer with the implementer's worktree as `--cwd`, prompt both with `--no-wait`, and yield turn for their `herdr-reply` completion callbacks. Agents with background subagents report `idle` while subagents run, so external `agent_status` cannot distinguish waiting on subagents from task completion; never barrier-wait them. Keep `herdr-wait` strictly as a fallback for non-agent panes or strongly-recognized agents that advance revision past 0. Confirm the reviewer kind with the user if unspecified. Agent arguments go after `--` (`agent start reviewer --kind <kind> --pane <id> -- --model <m>`); flags before `--` belong to Herdr and misplacing them breaks startup.

### Role-internal context isolation & review subagents

When an implementer faces a large task or operates under a constrained context window, it should spawn internal subagents for deep research, bulk edits, or test triage. Similarly, the Task Manager spawns internal subagents for adversarial crux code review under `keel`, `coding-protocol`, and `programming-expert` to keep its own context window clean and un-compacted. Internal subagents run in isolated contexts, returning pointer-based summaries. They never invoke Herdr CLI commands or reply scripts directly. Details: [Hierarchical Lane Coordination](references/lane-coordination.md).

### Banned: sleep/timer polling loops

Never `sleep`, `schedule`, or loop `herdr agent read` to poll for completion. Snapshot polling clips on alternate-screen agents, burns context, and re-enacts the #83 hang. Use `herdr-wait` (state barrier) for agents and `herdr pane wait-output --match` (content match) for commands.

Deep CLI semantics (wait activity gate, rejection vs settled outcomes, read sources) live in `$SKILL_DIR/references/cli-reference.md`.

## Run an ordinary command in another pane

Create a sibling pane with the same rule as above — `herdr-pane` preserves the caller's `$PWD` and focus and prints the new pane id:

```bash
uv run "$SKILL_DIR/scripts/herdr_pane.py"
```

Then run and inspect the command in that pane:

```bash
herdr pane run <returned-pane-id> "just test"
herdr pane wait-output <returned-pane-id> --match "test result" --timeout 120000
herdr pane read <returned-pane-id> --source recent-unwrapped --lines 120
```

`pane run` atomically sends command text and Enter. `pane wait-output` searches the selected snapshot immediately, so output that already exists can match. Use `--match <text>` for a literal substring or `--regex <pattern>` for a Rust regular expression. Omitting `--timeout` allows an indefinite wait.

Prefer `--source recent-unwrapped` for logs and transcripts. The other read sources, `--format ansi`, and the alternate-screen limit on `--lines` live in `$SKILL_DIR/references/cli-reference.md`.

## Safety and coordination rules

- Always use harness scripts in `$SKILL_DIR/scripts/` (e.g. `herdr_overview.py`, `herdr_pane.py`, `herdr_prompt.py`, `herdr_reply.py`, `herdr_dispatch.py`), NOT bare `herdr` CLI commands, for orientation, layout, agent communication, prompting, and waiting.
- Name Every Pane Immediately: Unlabeled panes (`null`) cause blind spots in `herdr-overview` and break automated reply routing. Name each pane with meaningful text matching its role (`orchestrator`, `task-manager`, `impl-auth`, `reviewer`) using `herdr-pane --label` or `herdr-label`.
- Orient with `herdr-overview` before enumerating panes, tabs, or agents. Do not run `herdr pane layout`, `pane list`, `tab list`, `workspace list`, or `agent list` to reconstruct layout.
- NEVER use `herdr pane send-text` or `herdr pane send-keys` to deliver prompts or replies. If target resolution fails or target has no agent, use the alternatives above (queue/watch, start agent, graceful abort). Raw text sent to a shell executes as shell commands.
- Confirm role-to-agent mapping (kind, provider, model) with user before starting agents or orchestrating; never assume or pick defaults.
- Verify folder trust and startup readiness before automated prompting (`qodercli` blocks on a trust selector that `agent start` does not report and that a prompt cannot dismiss; `pi` accepts `--approve`). See `$SKILL_DIR/references/agent-bootstrap.md`.
- Use `--no-focus` for background work unless the user asked to switch context.
- Use `--current`, an explicit pane ID, or a unique agent name. Do not rely on another client's focused pane.
- Parse IDs from JSON responses. Do not derive them from sidebar order or examples.
- CLI server errors are JSON on stderr with exit status 1. CLI syntax errors exit with status 2.

Never take a consent-gated or irreversible action — closing others' workspaces or tabs, `--trust-repository`, `herdr server stop`, killing the Herdr process — without explicit user intent. Read `$SKILL_DIR/references/safety-rules.md` before acting on any of them.

## Local helpers (not upstream)

> [!IMPORTANT] Method Constraint
> Always execute these 10 harness scripts in `$SKILL_DIR/scripts/` instead of bare `herdr` CLI commands. Bare CLI commands bypass argument quoting, caller context injection, target safety checks, and delivery verification.

All 10 scripts in `$SKILL_DIR/scripts/` are authoritative and documented here or in the orientation section above, with their options and exit codes; execute them directly without viewing script sources or running `--help`. They run through the repo runtime so no PATH setup is needed. All but `herdr_agy_bridge.py` (a file installer that needs no Herdr session) and `herdr_worktree.py` (a worktree allocator that needs only `wt`/`git`) require `HERDR_ENV=1` and share the `herdr_cli.py` adapter (imported, never run). All exit `0` ok, `1` herdr failure, `2` usage or missing precondition; `herdr-prompt`, `herdr-dispatch`, and `herdr-reply` add `3` for an agent that needs human input and `4` for a wait that timed out after delivery, `herdr-wait` adds `3` for a blocked target. `~/.local/bin/<helper>` symlinks to the same scripts are optional.

### `herdr-overview` — the session at a glance

Panes grouped by workspace with id, agent kind, agent name, label, and cwd; the calling pane marked `*`. Same script and flags as "Orient with `herdr-overview` first" above — that section is canonical.

### `herdr-label` — the one name that is both visible and addressable

Sets the pane label (what a person sees on the border) and the agent name (what a command accepts) to the same string:

```bash
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer            # label + agent name
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer --pane w1:p2
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer --label-only  # multi-word label, agent untouched
uv run "$SKILL_DIR/scripts/herdr_label.py" --clear             # drop both
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer --json
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer --dry-run   # print the calls, rename nothing
```

Refuses a name that breaks the agent-name pattern or that another live agent already holds, and validates before renaming anything, so a rejected name never leaves a half-applied label. A pane with no agent is labelled only; a pane with an agent needs `--label-only` for a multi-word label.

### `herdr-pane` — split the calling pane

The whole env-check → resolve → split sequence, as one command:

```bash
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical          # stack a pane below the caller (--direction down)
uv run "$SKILL_DIR/scripts/herdr_pane.py" horizontal        # place a pane right of the caller (--direction right)
uv run "$SKILL_DIR/scripts/herdr_pane.py"                   # caller wider than tall -> right, else down
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical --label reviewer  # split and label in one command (-l)
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical --focus --ratio 0.3 --env FOO=bar --cwd /tmp
uv run "$SKILL_DIR/scripts/herdr_pane.py" horizontal --dry-run  # print the herdr command, split nothing
```

Guards `HERDR_ENV=1`, resolves the caller with `herdr pane current --current`, picks the auto direction from `herdr pane layout --pane <id>`, prints `new pane <id>  direction=…  caller=…  cwd=…  focus=…  label=…` (with label when set).

### `herdr-worktree` — one isolated worktree per lane

Allocates the worktree a lane's panes run in, so Task Manager and Implementer start inside an isolated tree instead of improvising `.claude/worktrees/` directories in the repository root (which trips Worktrunk's `branch_worktree_mismatch` guard). Prefers Worktrunk (`wt`) when it is on `PATH` and falls back to `git worktree` under a predictable sibling path (`<repo>.<sanitized-branch>`):

```bash
WORKTREE_PATH=$(uv run "$SKILL_DIR/scripts/herdr_worktree.py" allocate feat/184-worktree --base main)
uv run "$SKILL_DIR/scripts/herdr_worktree.py" allocate feat/184-worktree --json
uv run "$SKILL_DIR/scripts/herdr_worktree.py" resolve feat/184-worktree
uv run "$SKILL_DIR/scripts/herdr_worktree.py" list --json
```

`allocate` prints only the absolute path, so `CWD=$(...)` substitution works; `--json` adds the engine and status. `resolve` and `list` read existing state. Unlike its siblings this helper needs no `HERDR_ENV=1` session — it only shells out to `wt`/`git`.

### `herdr-dispatch` — manager-side task dispatch

Dispatches a ticket file to one or more callees with caller context and reply contract, validates callee agent names (refusing kinds), and verifies post-dispatch delivery (`revision` increment) in one command:

```bash
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --file task.md --no-wait
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --file task.md --wait --timeout 15000
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee1 callee2 --file task.md --no-wait
```

Requires `--file` unless `--draft` is passed, so tickets are dispatched from a durable file. Refuses agent kinds (e.g. `qodercli`) with the live agent names listed. Prints `prompted <callee> (<pane>)  bytes=...  revision=...` to verify delivery.

`--draft` prints a ticket skeleton with routing prefilled from live state (or writes it to `--file`) and sends nothing:

```bash
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --draft --file task.md
```

Fill the Task/Context/Acceptance sections and delete the `herdr-draft: unfilled` marker, then dispatch that file with `--file`. Dispatch refuses a ticket that still carries the marker, or whose three sections are all empty; free-form tickets pass untouched.

### `herdr-reply` — callee completion callback

Delivers `<STATUS> <artifacts> <issues>` or a result payload to the sender agent, wrapped in the same timestamped envelope `herdr-prompt` uses, with `Receiver(You)` naming the sender it is answering. A reply carries no `Group:`, `Resume:`, or `Cwd:` — it reports a result, it does not re-open the lane:

```bash
uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator "COMPLETED artifacts=[...] issues=[]"
uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file result.md
echo "COMPLETED" | uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator
uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator "COMPLETED" --wait --timeout 15000
```

Validates the target agent name (refusing kinds) and reports post-delivery revision in one line. Never use bare `herdr agent prompt` directly for replies.

### `herdr-prompt` — deliver a payload verbatim

For multi-line briefs, code fences, `$`, backticks, and quotes: the payload reaches `herdr agent prompt` as one argv element, so nothing is interpolated or re-quoted.

```bash
uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --file brief.md --wait --timeout 120000
uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --file - < brief.md
git diff | uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --wait
uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --file brief.md --wait --dry-run
```

Reads the payload from `--file` (or stdin when `--file` is omitted or `-`) and forwards `--wait`, `--until`, and `--timeout`. Accepts several TARGETs for one broadcast (`herdr-prompt callee1 callee2 --file brief.md --no-wait`); `--no-wait` dispatches without waiting and is rejected alongside `--wait`. A `--wait` that times out after delivery exits 4 — prompt accepted, agent working asynchronously: yield turn and await reply callback, or resume with `herdr-wait` instead of resubmitting; only a true dispatch failure exits 1. `--label <LABEL>` takes an exact pane label instead of a TARGET, failing with the candidates when more than one pane carries it. `--dry-run` prints the exact argv as one JSON array per target and submits nothing.

Unless `--no-caller-context` is passed, it prepends the `Sender:`/`Receiver:` envelope, the Herdr skill notice, the live `Group:` roster, the resumption fields, and the completion-reply contract (see "Name a target, then hand off"), so the convention does not depend on a sender remembering it. When the sending pane has no agent name, the contract says so instead of naming a target that cannot be reached. `--no-caller-context` warns loudly on stderr if targeting named agents.

### `herdr-wait` — one barrier over many agents

Polls `herdr agent get <target>` per target on a short tick — never concurrent `herdr agent wait` subprocesses (blind to the #83 event bug) and never `sleep` loops. Barrier mode waits for ALL targets; `--any` returns when ANY settles:

```bash
uv run "$SKILL_DIR/scripts/herdr_wait.py" action1 action2 --timeout 300000
uv run "$SKILL_DIR/scripts/herdr_wait.py" review1 review2 --any
uv run "$SKILL_DIR/scripts/herdr_wait.py" action1 action2 --json
```

Settled means `idle`, `done`, or `blocked`; `--until idle` without `done` auto-expands with a warning. A wanted state with revision 0 (agent unrecognized — seen on agy panes whose status bar still reads WORKING or while awaiting background subagents) is held, never settled: the wait is unsatisfiable, so it fails fast with exit 2 and an error steering callers to the event-driven Dispatch & Yield pattern (`herdr-reply`) instead of barrier-waiting. Dispatch-&-Yield is REQUIRED, not advisory, for `agy` and revision-0 agents: `herdr-wait` and `herdr-prompt --wait` cannot observe them to completion. Any `blocked` target exits 3 immediately. The watchdog `--timeout` always applies (default 300000); expiry exits 1 naming the unsettled targets. Prints an aligned `TARGET STATUS REVISION ELAPSED SESSION_PATH` table, or JSON with `--json`.

### Managed Antigravity (agy) bridge

`agy` reports revision 0 forever, so its pane state is only trustworthy when the agent itself publishes lifecycle titles. `herdr_agy_bridge.py` manages that bridge as an installation in Antigravity's own hooks (`~/.gemini/config/hooks.json` globally, `.agents/hooks.json` with `--project`), installing two hooks under the `herdr` group and deploying `hooks/herdr-agy-bridge.sh` beside the hooks file:

```bash
uv run "$SKILL_DIR/scripts/herdr_agy_bridge.py" --install             # global (default)
uv run "$SKILL_DIR/scripts/herdr_agy_bridge.py" --install --project   # repo .agents/hooks.json
uv run "$SKILL_DIR/scripts/herdr_agy_bridge.py" --status --json
uv run "$SKILL_DIR/scripts/herdr_agy_bridge.py" --uninstall
```

`Stop` evaluates the payload's `fullyIdle` and emits an OSC 0 title — `agy: idle` when fully idle, `agy: working (subagents)` while background subagents still run (absent `fullyIdle` counts as idle). `PreToolUse` with matcher `ask_permission` emits `agy: blocked (permission)` when a permission gate fires. Installs are idempotent — re-running updates the managed entries and preserves unrelated hooks; `--uninstall` removes only the managed entries and the deployed script. `--status` exits 0 when installed and active, 1 when missing or misconfigured (it checks the hook entries, the script, and that the hooks file parses). Restart the `agy` pane after installing so it reloads the hooks.

**Agent bridge convention:** per-agent lifecycle knowledge lives in exactly one adapter — `scripts/herdr_<agent>_bridge.py` — implementing the agy bridge's contract: marker-identified idempotent `--install/--uninstall/--status` into the agent's native config, publishing state as OSC 0 titles (`<agent>: idle | working (...) | blocked (...)`). Generic helpers (`herdr-prompt`, `herdr-wait`, `herdr-dispatch`) never branch on agent kind: they react only to observables (the revision-0 weak-recognition sentinel, herdr exit codes). When a second bridge lands, lift the shared constants (agent kinds, weak-revision predicate, OSC rendering) into `herdr_cli.py`; until then this section is the registry.

### `herdr-transcript` — clean text from the session file

Resolves `agent_session.value` via `herdr agent get <target>` and extracts assistant text from the session JSONL (Pi and Claude Code shapes), skipping spinners, status bars, and tool-call noise. With no `agent_session` path it falls back to the pane snapshot itself (`herdr agent read <target> --source recent-unwrapped --lines 120`; tune with `--source`/`--lines`). Prefer it over bare `herdr agent read`, whose terminal snapshot clips on alternate-screen agents:

```bash
uv run "$SKILL_DIR/scripts/herdr_transcript.py" review1 --last
uv run "$SKILL_DIR/scripts/herdr_transcript.py" review1 --role user
uv run "$SKILL_DIR/scripts/herdr_transcript.py" review1 --role all --json
```

Tests for all ten: `tests/herdr/`.
