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

Every cross-pane message carries a script-rendered A2A Markdown frontmatter envelope (`docs/adr/0020-a2a-markdown-frontmatter-envelope.md`): a block opened by `---` on line 1 and closed by `---`, holding exactly four top-level keys — `id` (the Task-ID), `context_id` (the sender's session), `status` (`state` plus `timestamp`), and `metadata` (`ticket_id`, the `sender`/`receiver` addresses, `task_group`, the live `group` roster, and `in_reply_to` on replies). The Herdr skill notice rides as its own plain line after the closing fence, then the payload follows. `status.state` is authoritative for the task lifecycle:

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

Recovery metadata (`metadata.cwd`/`metadata.resume`) is not in the default envelope — it lives in `.lane/tasks.yaml`; pass `--verbose` to `herdr-prompt`, `herdr-dispatch`, or `herdr-reply` to opt that pair back in for debugging. The retired Style 2 blocks (`Routing:`, `Hierarchy:`, `Runtime:`, `Protocol:`) are never rendered or parsed: the cutover ships no compatibility shim.

`herdr-prompt`, `herdr-dispatch`, and `herdr-reply` render the envelope from live Herdr state and prepend it to every payload, in both directions. The frontmatter fence doubles as the paging line, so transport headers never blur into message content. An absent `metadata` field renders no key; `id` always renders and is never empty — a message that bound no task gets a generated `unlinked-<compact UTC stamp>` id, which names no task and never reaches `metadata`. `context_id` renders `''` when the harness knows no session, and no session is invented. `metadata.receiver` names the addressee — read it first when several panes were addressed at once. Relay a message with its envelope intact; text that opens without the `---` frontmatter fence is not an envelope these scripts rendered — `parse_envelope` refuses it. The dispatch/reply samples and the Ticket-ID/Task-ID contract live in [lane-coordination.md](references/lane-coordination.md).

The token before `@` is the **live agent name**, the only human-readable target `herdr agent prompt` accepts besides the pane id. A pane **label** is border decoration and is never a target, so it rides no envelope field: `metadata.sender` renders the strict `<agent>@<pane>` address, or the bare pane id when the pane carries only a label.

To address that pane, use its pane id, or let `herdr-prompt --label pr-orchestrator` resolve the label for you. See `$SKILL_DIR/references/cli-reference.md` for the full names/labels/targets rules.

> [!IMPORTANT] Orient First, Then Use Harness Scripts
> Always use harness scripts in `$SKILL_DIR/scripts/` (e.g. `herdr_overview.py`, `herdr_pane.py`, `herdr_prompt.py`, `herdr_reply.py`, `herdr_dispatch.py`), NOT bare `herdr` CLI commands, for orientation, layout, agent communication, prompting, and waiting.

## Orient with `herdr-overview` first

One call answers "what is here, and which pane or agent do I act on?" — pane ids, agent kinds, agent names, labels, live subagent tokens (`delegating` state), and cwd, grouped by workspace, with the calling pane marked `*`. It joins pane labels with agent names and subagent tokens, which no single `herdr` list command returns. Reach for it before any `workspace list`, `tab list`, `pane list`, `pane layout`, or `agent list` probe: those return overlapping subsets, cost several round trips, and bloat the context.

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

The pair is not stable on its own: the **agent name dies with the agent** while the **label outlives it**, so every exit leaves a labelled pane that nothing can address, and the next occupant inherits the stale label. `herdr-label` sets both in one command, and `--verify`/`--sync` keep the pair together:

```bash
uv run "$SKILL_DIR/scripts/herdr_label.py" --verify   # exit 3 when a live agent disagrees with its label
uv run "$SKILL_DIR/scripts/herdr_label.py" --sync     # converge both directions, idempotent
```

`--sync` sets a drifting label from the agent name, and names an agent that came back without one from the label that survived. A descriptive `--label-only` label is never guessed at (it is listed as `descriptive` in `--json`). Neither `--verify` nor `--sync` reports a pane with no live agent — that label is waiting for an occupant — so the **dispatch advisory** prints it on stderr during a normal dispatch, and `herdr-label --clear --pane <pane_id>` drops it (or re-label it for the next occupant). Run `--verify` before a dispatch wave and `--sync` after any agent exits or restarts; the orphan case needs no pass, because every dispatch checks it.

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
- **Auto-start & JIT recovery**: `herdr-reply` supports `--auto-start <KIND>` to start the agent on an open shell pane before delivering the reply. The revived caller is a fresh spawn, so the helper settles it first (`--settle SEC`, default 5; `0` waits not at all) so the reply is not swallowed by a pane still initialising (#238). When the reply target's agent has exited or is a bare shell, it reads the stored `caller_recovery` from `.lane/tasks.yaml` and prints a copy-paste diagnostic — `--auto-start <kind>` revive-and-deliver, or the stored `resume_cmd` to resume manually — falling back to the shell-pane diagnostic above when no recovery metadata exists.
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
   - **Task Lease Invariant**: `herdr_dispatch.py` checks active ticket leases in `.lane/tasks.yaml` before dispatching, preventing ticket collisions. Target identities are canonicalized across agent name and pane ID. Leases are acquired atomically pre-dispatch and rolled back if prompt delivery fails or is blocked. Leases are retained only on prompt acceptance (`EXIT_OK` or `WaitTimeout`). A lease whose recorded `pane_id` no longer exists is stale, so `herdr_dispatch.py` releases it and dispatches anyway (with one stderr line) — `--force` stays reserved for overriding a lease whose pane is still live (#210). Reads fall back `.lane/tasks.yaml` → `.lane/lease.yaml` → `.lane/lease.json` (a legacy JSON file loads as active leases with no trajectory); writes always go to `.lane/tasks.yaml`. Release is soft: `herdr_reply.py` drops the `active_leases` lock on any reply and keeps the durable task record and its append-only `trajectory`. The store base is one resolved path per lane — `HERDR_LANE_DIR`, else the git common dir's repository root (the common dir itself when it is not named `.git`: bare repositories, submodules, `--separate-git-dir`), else, for an ad-hoc pane with neither anchor, one deterministic user-level store at `<home>/.herdr/lane`; never PWD, and the fallback is never cwd-derived (#229, #182 h3). Taking that third layer prints one stderr advisory per process naming the path, so repo lanes and ad-hoc panes are visibly different stores, and the directory is created only by the first write. `herdr-pane split` still exits 2 in a directory with no anchor — it resolves through the primitive that refuses to guess — and always re-exports the resolved anchor, and each lease records its store and a release compares the two physically (`os.path.samefile`), so a release resolving another store logs the mismatch on stderr instead of moving the write. Reach: that diagnostic needs the lease to be in the resolving store — a lease in a store this process never resolves is an honest silent no-op, never a write into the store the lease names. Reply lease bookkeeping is best-effort and never blocks delivery — the correlation lookup runs before the send, the trajectory note and the release after it — and each unresolvable step prints one stderr line; a skipped correlation drops `metadata.ticket_id`/`metadata.in_reply_to` from the envelope (#229).
   - **Task state & trajectory**: `.lane/tasks.yaml` holds `active_leases` (the mutual-exclusion locks) and `tasks` (durable records keyed by `task_id`, each with `ticket_id`, `ticket_path`, `task_group`, `status`, `assignee`, `caller`, `caller_recovery`, and an append-only `trajectory` of `{seq, timestamp, event, actor, role, from_status, to_status, note, sha?}`). Canonical statuses: `TASK_STATE_SUBMITTED`, `TASK_STATE_WORKING`, `TASK_STATE_INPUT_REQUIRED`, `TASK_STATE_FAILED`, `TASK_STATE_COMPLETED` — every write emits these. The historical tokens (`unassigned`, `dispatched`, `in_progress`, `blocked`, `rework`, `completed`) stay readable through the one alias table `STATUS_ALIASES` in `herdr_lease.py`, are never written, and historical records are never migrated; the store is a shared live database read by worktrees that cannot be upgraded in lockstep. The `event` field is an action token (`dispatched`, `delivered`) and is deliberately not canonicalized, while `status`/`from_status`/`to_status` are. Inspect with `show`; record a milestone with `transition` (it accepts either spelling and persists the canonical one):
     ```bash
     uv run "$SKILL_DIR/scripts/herdr_lease.py" show --yaml --limit 10
     uv run "$SKILL_DIR/scripts/herdr_lease.py" transition msg-impl-1 TASK_STATE_WORKING --note "starting edits"
     ```
   - Never dispatch tasks via bare `herdr agent prompt callee` directly — doing so drops the envelope, the stored caller-recovery metadata, and the reply contract.
   - *Prompt acceptance invariant*: Exit code 0 from `herdr agent prompt` confirms acceptance. Revision numbers are purely informational; prompts are never re-injected or dropped due to unchanged revisions (#193).

3. **Yield turn on async execution:**
   If `herdr-prompt` exits 4 (timeout) or was dispatched with `--no-wait`, the prompt was delivered and the callee is working asynchronously. The orchestrator yields turn (stops calling tools, enters idle).

4. **Callee executes completion callback (and soft-releases its lease):**
   Upon completion or blocking, the callee executes the contract callback via `herdr_reply.py`, adhering to the settled **Final Reply Template** (`skills/ai-engineering-expert/references/resp-format.md`):
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file reply.md --ticket '<ticket-id>'
   # Or an inline stdin payload (a here-doc or a pipe keeps it off the shell's argv):
   printf 'COMPLETED <commit-sha>\n\n## Evidence\n- <check_name>: PASS (`<command>`)\n' | uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file - --ticket '<ticket-id>'
   # Or auto-start the caller agent if its turn exited back to an open shell pane:
   uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file reply.md --ticket '<ticket-id>' --auto-start pi
   ```
   The reply payload contains:
   - Status Triad: `COMPLETED <commit-sha>` | `BLOCKED <reason>` | `REJECTED <reason>`
   - `## Summary` (Carmack-style technical rationale, ≤100 words)
   - `## Artifacts` (absolute paths with kinds: diff, spec, report, eval, pr)
   - `## Evidence` (deterministic command checks: PASS / FAIL)
   - `## Route` (`continue | remediate | blocked`)
   - `## Issues` (P1/P2/P3 severity with file:line, invariant, defect, remediation; or `None`)
   - `## Suggestions` (optional non-blocking environment observations)

   Delivering this reply prompts the caller pane directly without shell mangling, waking its turn with the result. The reply maps its first token to a status (`COMPLETED`→`completed`, `BLOCKED`→`blocked`, `REJECTED`→`rework`), appends that event (with the mapped status token and the commit SHA as the note) to the sender's leased task `trajectory` in `.lane/tasks.yaml`, and releases only the sender's lease — a soft completion that preserves the task record. When the reply target's agent has exited or is a bare shell, `herdr-reply` reads `caller_recovery` from `.lane/tasks.yaml` and prints a copy-paste diagnostic (`--auto-start <kind>` revive-and-deliver, or the stored `resume_cmd`), falling back to the older shell-pane diagnostic when no recovery metadata exists. Never use bare `herdr agent prompt` directly for replies.

5. **Subagent Observability & `herdr-wait`:**
   **Subagent-First Execution**: In lane coordination, agents MUST use subagents for heavy tasks (exploration, bulk edits, test triage, and crux review). When agents spawn subagents, they may report `idle` while subagents work (the False-Idle Phenomenon). Herdr exposes live subagent status via Session Navigator tokens (`tokens`), displayed as `delegating` in `herdr-overview`.
   `herdr-wait` is subagent-aware: it checks `tokens.summary` and `tokens.title-suffix`, treating any agent with active subagent tokens as UNSETTLED (preventing premature wait barrier exits).
   `herdr-wait` is strictly a fallback for non-agent panes or watchdog recovery; Dispatch-&-Yield is the primary coordination pattern.
   **Dispatch-&-Yield is REQUIRED (not advisory) for `agy` and revision-0 agents**: Agents with background subagents (such as `agy`) report `idle` while their subagents work, and weakly-recognized agents never advance revision past 0. `herdr-wait` and `herdr-prompt --wait` CANNOT reliably observe `agy` agents to completion (they fail fast with exit 2 or hang to timeout). You must dispatch with `herdr-dispatch` or `herdr-prompt --no-wait`, yield turn, and await the `herdr_reply.py` callback. Nothing in the helpers points such a kind at a revision-based re-check: the unconfirmed-acceptance warning names the agy bridge's status title instead (#238), because a wanted state at revision 0 is unsatisfiable.

**Every handoff carries the envelope, and requires a reply.** A callee cannot address a sender it was never told about, and a sender left to infer completion falls back on polling. So the prompt opens with the envelope from "Know your post" and closes with the reply contract:

```text
<envelope: A2A frontmatter — id (Task-ID), context_id (sender session), status (state, timestamp), metadata (ticket_id, sender, receiver, task_group, group, and in_reply_to on replies; pass --verbose to add cwd/resume) — then the Herdr skill notice on its own line>

<the payload (Synthesized IDD/GDD Ticket)>

On completion, reply to the sender in one message using the herdr helper script:
  uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator --file <reply-payload.md> --ticket '<ticket-id>'
```

The rendered contract also carries the SHA guard's waiver route in prose, quoted
verbatim from the rendered line: "If the reply quotes a review id such as '0c81f04c' that names no commit, the SHA guard refuses it: waive that token by name with --allow-unresolvable-sha '0c81f04c' (one flag per token, reported on stderr)."

`STATUS` is `COMPLETED`, `BLOCKED`, or `REJECTED`; a blocked callee names what it needs instead of waiting silently. The **agent name** inside `metadata.sender` is the load-bearing part — the pane id tells a person where to look, and only the name is addressable.

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

`herdr_bootstrap.py` folds this sequence into one command: it stamps the ROLE INVARIANT (compaction-proof lane identity plus the subagent-first and reply mandates) into the launch surface, sets the pane label to the scoped name, and starts the agent. See [agent-bootstrap.md](references/agent-bootstrap.md) for the kind→mechanism matrix and the scoped-prefix rule.

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

Place the reviewer on a commit-addressed snapshot: the reviewer's own per-role worktree, or an ephemeral detached read, never a moving implementer tree. Start it with `--cwd` set to that path, prompt both with `--no-wait`, and yield turn for their `herdr-reply` completion callbacks. Reviewers read `git diff <base>..<sha>` and `git show <sha>:<path>`; they never check out, stash, or write in the implementer tree. Agents with background subagents report `idle` while subagents run, so external `agent_status` cannot distinguish waiting on subagents from task completion; never barrier-wait them. Keep `herdr-wait` strictly as a fallback for non-agent panes or strongly-recognized agents that advance revision past 0. Confirm the reviewer kind with the user if unspecified. Agent arguments go after `--` (`agent start reviewer --kind <kind> --pane <id> -- --model <m>`); flags before `--` belong to Herdr and misplacing them breaks startup.

### Role-internal context isolation & review subagents

When an implementer faces a large task or operates under a constrained context window, it should spawn internal subagents for deep research, bulk edits, or test triage. Similarly, the Task Manager spawns internal subagents for adversarial crux code review under `keel`, `coding-protocol`, and `programming-expert` to keep its own context window clean and un-compacted. Internal subagents run in isolated contexts, returning pointer-based summaries. They never invoke Herdr CLI commands or reply scripts directly. Details: [Hierarchical Lane Coordination](references/lane-coordination.md).

### Banned: sleep/timer polling loops

Never `sleep`, `schedule`, or loop `herdr agent read` to poll for completion. Snapshot polling clips on alternate-screen agents, burns context, and re-enacts the #83 hang. Use `herdr-wait` (state barrier) for agents and `herdr pane wait-output --match` (content match) for commands.

`herdr-prompt` and `herdr-dispatch` confirm a settled readiness claim with exactly **one** `herdr agent read --source visible` snapshot, taken the moment the status feed first claims ready, before any bytes are injected — a startup trust selector or permission dialog lives on the screen, not in the status feed. The wait loop itself reads no screen, so this one-shot check stays inside the ban above. An unreadable screen is not evidence of a dialog: the status signal decides, with one stderr line saying so.

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

`uv run "$SKILL_DIR/scripts/herdr_pane.py" --pane <id> --command '<line>'` sends a launch line through the pane path with a completion sentinel appended (#230): the pane prints `[herdr-launch] finished exit=<rc>` when the line exits, so a launched callee that crashes or never replies still leaves end-of-line evidence without cooperating. It reports process exit, never task success, and the composed argv is visible with `--dry-run`. Only lines launched this way carry a sentinel: panes started with `herdr agent start`, `herdr-dispatch --auto-start`, or `herdr-bootstrap` have none, so completion there is cooperative too. Two line shapes cannot emit one, so an absent sentinel is an honest signal rather than a fabricated success: an inline `#` comment swallows the appended sentinel, and a line that ends its own shell (`exit`, `exec`) leaves nothing to print it. The composed line is validated with `sh -n` before anything launches, so a line that would break once the sentinel is appended — a trailing bare `&` or `;`, or an operator escaped an odd number of times — is refused with the fix: group background work as `( <line> & )`. The positional DIRECTION and the split-only flags (`--label`, `--task-group`, `--cwd`, `--ratio`, `--env`, `--focus/--no-focus`) are refused with `--command`.

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
> Always execute these 11 harness scripts in `$SKILL_DIR/scripts/` instead of bare `herdr` CLI commands. Bare CLI commands bypass argument quoting, caller context injection, target safety checks, and delivery verification.

All 11 scripts in `$SKILL_DIR/scripts/` are authoritative and documented here or in the orientation section above, with their options and exit codes; execute them directly without viewing script sources or running `--help`. They run through the repo runtime so no PATH setup is needed. All but `herdr_agy_bridge.py` (a file installer that needs no Herdr session) and `herdr_worktree.py` (a worktree allocator that needs only `wt`/`git`) require `HERDR_ENV=1` and share the `herdr_cli.py` adapter (imported, never run). All exit `0` ok, `1` herdr failure, `2` usage or missing precondition; `herdr-prompt`, `herdr-dispatch`, and `herdr-reply` add `3` for an agent that needs human input and `4` for a wait that timed out after delivery, `herdr-wait` adds `3` for a blocked target. `~/.local/bin/<helper>` symlinks to the same scripts are optional.

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

Panes grouped by workspace and Task Group (Tab) with id, agent kind, agent name, label, live subagent tokens (`delegating`), and cwd; the calling pane marked `*`. Interactive TTY defaults to a styled `rich` table; non-TTY / piped output defaults to clean Markdown tables (`--format markdown`). Pass `--json` or `--yaml` for data pipelines. Filter by tab or task group with `--tab [ID|NAME]` or `--task-group <NAME>`. Same script and flags as "Orient with `herdr-overview` first" above — that section is canonical.

### `herdr-label` — the one name that is both visible and addressable

Sets the pane label (what a person sees on the border) and the agent name (what a command accepts) to the same string:

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

Refuses a name that breaks the agent-name pattern or that another live agent already holds, and validates before renaming anything, so a rejected name never leaves a half-applied label. A pane with no agent is labelled only; a pane with an agent needs `--label-only` for a multi-word label. `--task-group <slug>` scopes a bare role before naming; `--tab <NAME>` renames the calling tab (or the `--pane` tab) instead of labelling a pane.

### `herdr-pane` — split the calling pane

The whole env-check → resolve → split sequence, as one command:

```bash
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical          # stack a pane below the caller (--direction down)
uv run "$SKILL_DIR/scripts/herdr_pane.py" horizontal        # place a pane right of the caller (--direction right)
uv run "$SKILL_DIR/scripts/herdr_pane.py"                   # caller wider than tall -> right, else down
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical --label reviewer  # split and label in one command (-l)
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical --label impl-1 --task-group msg  # label: msg-impl-1
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical --focus --ratio 0.3 --env FOO=bar --cwd /tmp
uv run "$SKILL_DIR/scripts/herdr_pane.py" horizontal --dry-run  # print the herdr command, split nothing
```

Guards `HERDR_ENV=1`, resolves the caller with `herdr pane current --current`, picks the auto direction from `herdr pane layout --pane <id>`, prints `new pane <id>  direction=…  caller=…  cwd=…  focus=…  label=…` (with label when set). `--task-group <slug>` scopes `--label` before setting it (`reviewer` → `msg-reviewer`).

### `herdr-bootstrap` — stamp the role invariant, then start the agent

Writes a compaction-proof `ROLE INVARIANT` into the surface the target agent reads at launch, sets the pane label to the scoped name, and starts the agent — so an agent that loses context keeps its lane, its subagent-first mandate, and its reply contract:

```bash
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" msg-impl-1 --kind codex --pane w1:p3 --role impl-1 --task-group msg
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" --kind pi --pane w1:p3 --role tm --task-group msg --model claude-3-7-sonnet
uv run "$SKILL_DIR/scripts/herdr_bootstrap.py" msg-tm --kind claude --pane w1:p2 --role tm --dry-run
```

`pi` and `claude` receive the snippet inline through `agent start --append-system-prompt` (delivery per `references/kinds.yaml`); every other kind (`cline`, `codex`, `copilot`, `qodercli`, `agy`, and unknown kinds) reads it from an idempotent marker block appended to `AGENTS.md` (`cline` prefers an existing `.clinerules`). Trust flags ride after `--` as native agent args from `references/kinds.yaml` (`pi` → `--approve`, `claude` → `--dangerously-skip-permissions`); unverified kinds carry none. `--cwd` cds the pane into the requested path, refuses on mismatch (`--cwd-timeout`, default 10s), then validates the target: a missing directory, a path that is not a registered linked worktree, and the main checkout in a repository that already has linked worktrees are refused (exit 2) with the expected worktree and the actual pane cwd. `--task-group <slug>` scopes a bare `--role` (`tm` → `msg-tm`); `--dry-run` prints the planned file path and start argv without mutating anything. Matrix, snippet, and marker: [agent-bootstrap.md](references/agent-bootstrap.md).

### `herdr-worktree` — one isolated worktree per role

Binds one worktree per role, not per feature branch, so Task Manager, each Implementer, and the reviewer of a ticket start inside an isolated tree. The layout is `<repo>.<task-group>.<role>` and the branch namespace is `lane/<task-group>/<role>/<ticket>`. `claim` performs a guarded in-place transition: it requires a clean tree, an explicit `--base`, and a branch inside that namespace; it refuses a branch already checked out elsewhere and never forces. Allocations are persisted in `.lane/tasks.yaml` under the top-level `worktrees` mapping, keyed by worktree real path and anchored by `resolve_lane_base_dir` (never `PWD`). Read-only `allocate|resolve|list` still prefer Worktrunk (`wt`); the lifecycle verbs use `git` directly. A **bare** repository always allocates through `git worktree`: Worktrunk's `{{ repo_path }}` is then the git directory itself, so its sibling convention collapses to `<git-dir>.<slug>` and the lane would start without a checkout (#207).

```bash
WORKTREE_PATH=$(uv run "$SKILL_DIR/scripts/herdr_worktree.py" claim ../repo.w11-t7.impl-1 lane/w11-t7/impl-1/184-worktree --base main)
uv run "$SKILL_DIR/scripts/herdr_worktree.py" status --worktree "$WORKTREE_PATH" --json
uv run "$SKILL_DIR/scripts/herdr_worktree.py" retire "$WORKTREE_PATH"
uv run "$SKILL_DIR/scripts/herdr_worktree.py" doctor --prune
uv run "$SKILL_DIR/scripts/herdr_worktree.py" list --json
```

`claim` prints only the absolute path, so `CWD=$(...)` substitution works; `--json` adds the engine and status. `status` reports branch, clean/dirty, detached HEAD, namespace violations, and layout mismatches; `retire` removes only a clean worktree, deletes the branch only when fully merged (`git branch -d`, never `-D`), and prunes admin entries; `doctor` audits unlinked, orphaned, and namespace-violating entries, and `--prune` drops only admin entries for missing directories. Never run `git switch -C`, `-B`, or `-f`, `git stash`, or `git worktree add --force` inside a lane tree: they rewrite or carry state across the single-writer boundary. Legacy `allocate` remains for feature-bound trees with the `<repo>.<sanitized-branch>` layout; the `layout` flag reports that shape until the lane is re-claimed onto a per-role path. Unlike its siblings this helper needs no `HERDR_ENV=1` session — it only shells out to `wt`/`git`.

### `herdr-dispatch` — manager-side task dispatch

Dispatches a ticket file to one or more callees with caller context and reply contract, validates callee agent names (refusing kinds), acquires a task lease, and verifies post-dispatch delivery (`revision` increment) in one command:

```bash
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --file task.md --no-wait
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --file task.md --ticket-id "#182-msg" --task-id "#182-msg#impl-1" --no-wait
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --file task.md --wait --timeout 15000
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee1 callee2 --file task.md --no-wait
```

Requires `--file` unless `--draft` is passed, so tickets are dispatched from a durable file. `--ticket-id <ID>` and `--task-id <ID>` explicitly set the correlation handles; the Task-ID mirrors the Ticket-ID when not given. When both are omitted, `herdr-dispatch` derives the Ticket-ID from the file basename (a leading-number stem like `182-foo.md` becomes `#182-foo`; a stem already starting with `#` is used as-is; any other stem is used verbatim; `-`/stdin yields none). It creates or updates the task record in `.lane/tasks.yaml`, appends a `dispatched` trajectory event, and persists `caller_recovery` (`pane_id`, `kind`, `session_path`, `resume_cmd`, `cwd`; missing fields omitted; `session_path` is the agent session handle). Refuses agent kinds (e.g. `qodercli`) with the live agent names listed. Prints `prompted <callee> (<pane>)  bytes=...  revision=...` to verify delivery.

`--auto-start <KIND>` (#225) structurally closes the raw-`agent start` shortcut: when the callee has no live agent (a bare shell pane), dispatch bootstraps it through the `herdr_bootstrap` contract — kind trust flags from `references/kinds.yaml`, the ROLE INVARIANT surface, and the pane-cwd guarantee — then dispatches the ticket. A spawned pane is settled before the ticket goes in (`--settle` defaults to 5s in `herdr-bootstrap`; a live agent pays nothing). `--role`, `--cwd`, and `--model` ride through to bootstrap; `--task-group` scopes the bootstrapped name. A live agent dispatches with no extra herdr calls. `--dry-run` prints the would-bootstrap plan without mutating anything, including the planned settle. Without `--auto-start`, a bare shell pane still refuses safely.

Before injecting bytes, `herdr-dispatch` runs the same pre-flight gate as `herdr-prompt`: it probes `herdr agent get <target>`, polling every 200ms up to 10s until `interactive_ready` is not false and `agent_status` is `idle` or `done`; a timeout aborts with a `UsageError` naming the auth/approval-dialog unblock path. Under `--no-wait` it then observes for up to 5s (100ms intervals, the window `herdr agent prompt` itself documents) whether the agent started working or its revision moved; an unconfirmed observation warns on stderr and still exits 0, because exit 0 from the CLI already confirms acceptance (#193). Caveat: the gate is not a screen oracle. It confirms a settled claim with exactly one `herdr agent read --source visible` snapshot and refuses a structured trust/permission dialog — the question plus whole-line option rows — unless a documented idle input row (`Type your message or @path/to/file`) appears below the dialog block. It matches that row's leading phrase (`Type your message`) as an unanchored substring, so neither surrounding chrome nor a clip of the row's right side can silence it, and a row only vetoes when no selector-shaped row sits below it: below the box, only a row carrying the selector cursor (`❯ n. …`) or a whole-line trust/permission question blocks the veto, while numbered chrome (`1. fix the parser`, `2. pending dispatch`, a markdown list) never does, because a live modal replaces the input box; that second witness is also what bounds the risk of agent prose echoing the phrase. So agent prose that quotes a dialog block does not refuse: the quote sits above the pane's live input row, and only that row vetoes. The row's render is captured in `references/agents/qodercli.md`, evidenced for qodercli only; on another agent's pane that row is undocumented, and two residuals stay unguarded — an operator who has typed leaves no placeholder, and a pane narrower than the matched core clips below it — so a quoted block with no matching idle row below still refuses. An unreadable screen falls back to the status signal, and `--source visible` is exercised only through the test stub — on an alternate-screen pane that returns clipped or empty output the gate silently degrades to trusting the status feed. When it refuses a pane that shows no dialog, `--skip-screen-check` dispatches without consulting the screen.

`--draft` prints a ticket skeleton with routing prefilled from live state (or writes it to `--file`) and sends nothing:

```bash
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" callee --draft --file task.md
```

Fill the Task/Context/Acceptance sections and delete the `herdr-draft: unfilled` marker, then dispatch that file with `--file`. Dispatch refuses a ticket that still carries the marker, or whose three sections are all empty; free-form tickets pass untouched.

### `herdr-reply` — callee completion callback

Delivers `<STATUS> <artifacts> <issues>` or a result payload to the sender agent, wrapped in the same A2A frontmatter envelope `herdr-prompt` uses, with `metadata.receiver` naming the sender it is answering and `status.state` carrying the lifecycle state the reply's first token maps to:

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

`herdr-reply` automatically inspects `.lane/tasks.yaml` for the replying sender's lease and task, populates the envelope's `id`, `metadata.ticket_id`, and `metadata.in_reply_to` (the `<Task-ID>` it answers), maps the payload's first token (`COMPLETED`→`completed`, `BLOCKED`→`blocked`, `REJECTED`→`rework`), appends that event (with the mapped status token and the commit SHA as the note) to the sender's task `trajectory`, and soft-releases only the sender's active lease upon successful prompt delivery — the task record survives. The record's `task_id` linkage is resolved separately from the envelope's correlation: an explicit `--ticket <ID>` (task id, or a ticket id whose sender-owned open task is unique) or `--in-reply-to <RECORD>` wins, else the sender's active lease. The rendered dispatch contract supplies the ticket — it binds `--ticket` to the dispatcher's derived id (#246 E1.1) — so a reply that names no ticket is never guessed at: with no lease and no flag it is recorded unlinked, mutating no task. A second reply for the same ticket still carries the linkage after the first reply consumed the lease by passing `--ticket`/`--in-reply-to`. Zero, one, or several open tasks, or a flag that does not name one of the sender's open tasks, records the reply unlinked with one warning line on stderr, never a guessed linkage; the line leads with a stable severity marker — `unlinked reply (open work refused)` when the step refused to bind what it was told (open work it would not guess at, or a flag that names no open task of the sender), `unlinked reply (nothing to link)` when it holds none, and the third wording `unlinked reply (sender or store unreadable)` when there was no answer at all because no sender resolved or the anchor/store could not be read (a store that cannot be read says so instead of claiming the sender holds no open task) — and it never claims a record the run did not write: the `; recording the reply unlinked` tail is appended only after the store took the record, and `; no store record was written` when it did not, so the warning cannot contradict the `NOT RECORDED` pointer in the prompt delivered in the same run. Every warning now accompanies an unlinked reply; the explicit `--ticket`/`--in-reply-to` bindings are the caller's instruction, so they stay silent. Validates the target agent name (refusing kinds) and reports post-delivery revision in one line. Never use bare `herdr agent prompt` directly for replies.

Before that, the payload itself must be honest about its SHAs: every backticked 7-40 lowercase-hex token in the outbound body is checked with `git rev-parse --verify <token>^{commit}` against this lane's repository, because a backticked hex token is an instruction rather than prose — a "do not rewrite" list whose token drifted by one digit points at nothing (#247). The outbound *body* is the only text checked: the A2A frontmatter envelope is composed afterwards and is never inspected, so a token inside a frontmatter field is not a claim the guard reads. The repository is this lane's anchor rather than the ambient working directory, so one payload gets one verdict from any directory, and when the caller's environment relocates git's object store — `GIT_DIR`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY` or `GIT_ALTERNATE_OBJECT_DIRECTORIES` — the check is unverifiable and is skipped loudly in the same `SHA guard skipped` line, naming every unchecked token, instead of letting one resolve in another repository; the two location overrides that cannot move an object lookup, `GIT_WORK_TREE` and `GIT_INDEX_FILE`, never skip for that reason alone, so a token that names no commit is still refused with them set (a non-existent `GIT_WORK_TREE` still leaves git unable to answer — `git rev-parse --is-inside-work-tree` exits 128 — and the check is then reported unchecked rather than passed). A token that names no commit refuses the reply on the spot: exit 2, naming the token and the payload path, before any record is written, so a refused payload consumes no lease. `--dry-run` reports it the same way instead of accepting it silently, and a payload with no such token — or with hex only in prose — is untouched. A genuinely intentional non-resolving token, such as a review-record id or a mutant label that no shape rule can distinguish from a commit abbreviation, is waived by name with `--allow-unresolvable-sha <TOKEN>`, and every waiver is reported on stderr.

Before delivery it persists the reply into the lane store — the body to `.lane/replies/<id>.md` beside one metadata-only sidecar `.lane/replies/<id>.yaml` per record, a lossless layout of one file per record with no lock and no read-modify-write, so two concurrent replies cannot lose each other's row. A pre-#231 `.lane/replies.yaml` is merged on read (deduped by id, the sidecar winning) and never rewritten, so it can never be clobbered. The sidecar holds no payload text — `status` (mapped token only), `sha` only when it is a hex commit token, `evidence` as a closed-vocabulary label, `artifacts` as a count, plus `digest`, `bytes`, `payload`, `recorded_at`, `sender`, `caller`, `ticket_id`, `in_reply_to`, `shape`, `task_id` — and reading verifies it: `get_reply` (the reader the advance gate uses) returns a row only while the payload file exists and its sha256 equals the recorded `digest`, and a row whose `sender`/`task_id` do not match the lease being advanced cannot advance it. It inserts a short pointer block between the envelope and the body: `Payload: COMPLETE` with the record id, path and digest, or `Payload: INCOMPLETE` when a `COMPLETED` payload carries no evidence section, in which case the reply is recorded as incomplete (shape=incomplete) and the sender's task state is not advanced to `completed` at all; a `BLOCKED`/`REJECTED` record carries no pointer, so its payload is unchanged. When the store cannot be resolved or written, delivery still succeeds: the payload is unchanged **except** for the added `Payload: NOT RECORDED` pointer naming the reason, whatever the shape. An unreadable index is never destroyed — the damaged file is moved aside byte-for-byte to `<name>.corrupt-<utc-stamp>` and the reply degrades to `Payload: NOT RECORDED`. An evidence section is a heading whose word starts with an evidence stem (evidence, verification, validation, gate, proof, witness, reproduction, artifact, test, pytest, check, log, result, benchmark, coverage, report, command, output, diff, run, status, outcome, acceptance) or is exactly `ci`, a bold inline `**Evidence:** …`, or a fenced block with content; any recognized heading with a non-blank body counts too unless its normalized label is on the deny-list (`notes`, `note`, `next steps`, `next`, `todo`, `tbd`, `plan`, `questions`, `changelog`). The ledger records `evidence:` as that normalized label and `artifacts:` as a count — a shape floor, not a quality grade. Read any record back with `uv run "$SKILL_DIR/scripts/herdr_lease.py" replies [ID]`. The store record is the authority and prompt text is never provenance: a reply that never reached the store advances nothing, so a callee that bypasses the helper degrades to silence, never to a false success.

### `herdr-prompt` — deliver a payload verbatim

For multi-line briefs, code fences, `$`, backticks, and quotes: the payload reaches `herdr agent prompt` as one argv element, so nothing is interpolated or re-quoted.

```bash
uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --file brief.md --wait --timeout 120000
uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --file - < brief.md
git diff | uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --wait
uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --file brief.md --wait --dry-run
```

Reads the payload from `--file` (or stdin when `--file` is omitted or `-`) and forwards `--wait`, `--until`, and `--timeout`. Positional arguments are always TARGETs: a payload passed as a second positional is refused by name before the payload is read (`target '...' contains whitespace, so it cannot be an agent name or pane id`), and the empty-payload refusal names `--file`/stdin (#212). Accepts several TARGETs for one broadcast (`herdr-prompt callee1 callee2 --file brief.md --no-wait`); `--no-wait` dispatches without waiting and is rejected alongside `--wait`. A `--wait` that times out after delivery exits 4 — prompt accepted, agent working asynchronously: yield turn and await reply callback, or resume with `herdr-wait` instead of resubmitting; the advice is per target, so a revision-0 kind (whose wanted state is unsatisfiable, #238) is pointed at the agy bridge's status title instead of `herdr-wait`. Only a true dispatch failure exits 1. `--label <LABEL>` takes an exact pane label instead of a TARGET, failing with the candidates when more than one pane carries it. `--dry-run` prints the exact argv as one JSON array per target and submits nothing.

Unless `--no-caller-context` is passed, it prepends the A2A frontmatter envelope — carrying the `sender`/`receiver` addresses and the live `group` roster — and the Herdr skill notice, then appends the completion-reply contract (see "Name a target, then hand off"), so the convention does not depend on a sender remembering it; `--verbose` adds `metadata.cwd`/`metadata.resume` back for debugging. When the sending pane has no agent name, the contract says so instead of naming a target that cannot be reached. `--no-caller-context` warns loudly on stderr if targeting named agents.

Before injecting bytes it runs the pre-flight gate: it probes `herdr agent get <target>`, polling every 200ms up to 10s until `interactive_ready` is not false and `agent_status` is `idle` or `done`; a timeout aborts with a `UsageError` naming the auth/approval-dialog unblock path. Under `--no-wait` it then observes for up to 5s (100ms intervals, the window `herdr agent prompt` itself documents) whether the agent started working or its revision moved; an unconfirmed observation warns on stderr and still exits 0, because exit 0 from the CLI already confirms acceptance (#193). Caveat: the gate is not a screen oracle. It confirms a settled claim with exactly one `herdr agent read --source visible` snapshot and refuses a structured trust/permission dialog — the question plus whole-line option rows — unless a documented idle input row (`Type your message or @path/to/file`) appears below the dialog block. It matches that row's leading phrase (`Type your message`) as an unanchored substring, so neither surrounding chrome nor a clip of the row's right side can silence it, and a row only vetoes when nothing dialog-shaped sits below it, because a live modal replaces the input box; that second witness is also what bounds the risk of agent prose echoing the phrase. So agent prose that quotes a dialog block does not refuse: the quote sits above the pane's live input row, and only that row vetoes. The row's render is captured in `references/agents/qodercli.md`, evidenced for qodercli only; on another agent's pane that row is undocumented, and two residuals stay unguarded — an operator who has typed leaves no placeholder, and a pane narrower than the matched core clips below it — so a quoted block with no matching idle row below still refuses. An unreadable screen falls back to the status signal, and `--source visible` is exercised only through the test stub — on an alternate-screen pane that returns clipped or empty output the gate silently degrades to trusting the status feed. When it refuses a pane that shows no dialog, `--skip-screen-check` prompts without consulting the screen.

### `herdr-wait` — one barrier over many agents

Polls `herdr agent get <target>` per target on a short tick — never concurrent `herdr agent wait` subprocesses (blind to the #83 event bug) and never `sleep` loops. Barrier mode waits for ALL targets; `--any` returns when ANY settles:

```bash
uv run "$SKILL_DIR/scripts/herdr_wait.py" action1 action2 --timeout 300000
uv run "$SKILL_DIR/scripts/herdr_wait.py" review1 review2 --any
uv run "$SKILL_DIR/scripts/herdr_wait.py" action1 action2 --json
```

Settled means `idle`, `done`, or `blocked`; `--until idle` without `done` auto-expands with a warning. A wanted state with revision 0 (agent unrecognized — seen on agy panes whose status bar still reads WORKING or while awaiting background subagents) is held, never settled: the wait is unsatisfiable, so it fails fast with exit 2 and an error steering callers to the event-driven Dispatch & Yield pattern (`herdr-reply`) instead of barrier-waiting. Dispatch-&-Yield is REQUIRED, not advisory, for `agy` and revision-0 agents: `herdr-wait` and `herdr-prompt --wait` cannot observe them to completion. Any `blocked` target exits 3 immediately. The watchdog `--timeout` always applies (default 300000); expiry exits 1 naming the unsettled targets. Prints an aligned `TARGET STATUS REVISION ELAPSED SESSION_PATH` table, or JSON with `--json`.

`--stale-after SEC` is an opt-in staleness advisory (#230), off by default: once a target's status and revision have been unchanged for SEC seconds, the helper prints one advisory on stderr naming the target, the held status, and the elapsed window, then stays quiet until the target moves again (one report per stall episode). The window must be a finite number of seconds greater than 0, and it restarts each time the target's status or revision changes: a target already silent when the wait begins still waits a further full window. It is warning-only. It never kills, retries, restarts, or interrupts a target, never establishes a result, and never changes the wait's exit status: it asks you to collect evidence (read the pane, prompt the target, check its transcript). For a pane the skill did not launch there is no sentinel, so completion there is cooperative, not guaranteed.

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

Tests for all eleven: `tests/herdr/`.
