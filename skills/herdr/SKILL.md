---
name: herdr
description: >-
  Herdr terminal-multiplexer reference for coding agents. Inspects and drives panes, tabs, workspaces, and sibling agents, waits on test or server output. Use when the user mentions Herdr or asks to drive panes or agents. Requires HERDR_ENV=1; not for general background terminals or delegation.
metadata:
  author: herdrdev
  version: '0.9.0'
---

# Herdr

Vendored from `herdrdev/herdr@v0.9.0`; `herdr --skill` prints the installed binary's own copy, authoritative for that binary.

Herdr organizes terminals into workspaces, tabs, and panes, recognizes coding agents running inside panes, and exposes the current session through the `herdr` CLI.

Before issuing any control command, verify that this agent is running inside a Herdr-managed pane:

```bash
test "${HERDR_ENV:-}" = 1
```

If the check fails, say that you are not running inside Herdr and stop. Do not inspect or control the focused Herdr session from outside Herdr.

When the check passes, the `herdr` binary in `PATH` talks to the current session. Use it to inspect neighboring work, create terminal layout, start agents and commands, read output, and wait for state changes.

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

## Use IDs and caller context

Public IDs are opaque stable handles: workspace `w1`, tab `w1:t1`, pane `w1:p1`.

Herdr injects the caller's context into each managed pane:

```bash
printf '%s\n' "$HERDR_WORKSPACE_ID" "$HERDR_TAB_ID" "$HERDR_PANE_ID"
```

Prefer `--current` when a pane command should target the calling pane. Omitting a target may use the UI-focused pane, which can belong to the user or another client.

Orient with one compact view: pane ids, agent kinds, agent names, labels, and cwd, grouped by workspace.

```bash
uv run "$SKILL_DIR/scripts/herdr_overview.py"            # YAML when piped, table on a terminal
uv run "$SKILL_DIR/scripts/herdr_overview.py" --tab      # only the calling tab
uv run "$SKILL_DIR/scripts/herdr_overview.py" --current  # only the calling pane
```

Drop to the raw lists when you need a field the view omits:

```bash
herdr workspace list
herdr tab list --workspace "$HERDR_WORKSPACE_ID"
herdr pane current --current
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
herdr agent list
```

Creation responses expose the IDs to use next. `workspace create` returns `.result.workspace`, `.result.tab`, and `.result.root_pane`; `tab create` returns `.result.tab` and `.result.root_pane`; `pane split` returns the new pane as `.result.pane`.

## Name a target, then hand off

A person reads a pane's **label** off the pane border, so that is the name they will say when they ask you to hand something off. But no command accepts a label as a target. The **agent name** is the addressable handle, and it is cleared when that agent exits.

So give both the same string, in one command:

```bash
uv run "$SKILL_DIR/scripts/herdr_label.py" reviewer    # this pane's label and its agent name
```

`herdr-label` labels the calling pane and names its agent identically, so the name a person sees is the name you can address. It takes `--pane <id>` for another pane, `--label-only` when a multi-word label or an existing agent name must survive, and `--clear` to drop both.

When a person says "hand off to <name>", pass that name straight to the prompt helper:

```bash
uv run "$SKILL_DIR/scripts/herdr_prompt.py" reviewer --file brief.md --wait --timeout 15000
uv run "$SKILL_DIR/scripts/herdr_prompt.py" --label "review pane" --file brief.md --wait --timeout 15000
```

`--label` matches a pane label exactly. Labels are not unique — two panes may carry the same one — so an ambiguous label fails with the candidate pane ids listed instead of guessing.

### Dispatch & Yield (Event-Driven workflow)

Multi-agent coordination is event-driven via completion callbacks:

1. **Caller self-names:**
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_label.py" orchestrator
   ```
   Ensures the caller has a valid, addressable agent name so workers know whom to reply to.

2. **Dispatch with short grace period or fire-and-forget:**
   ```bash
   # Dedicated dispatch helper (validates agent name, verifies delivery revision):
   uv run "$SKILL_DIR/scripts/herdr_dispatch.py" worker --file task.md --no-wait

   # Or via herdr-prompt:
   uv run "$SKILL_DIR/scripts/herdr_prompt.py" worker --file task.md --wait --timeout 15000
   ```
   Never dispatch tasks via bare `herdr agent prompt worker` directly — doing so drops the `Caller:` context and reply contract.

3. **Yield turn on async execution:**
   If `herdr-prompt` exits 4 (timeout) or was dispatched with `--no-wait`, the prompt was delivered and the worker is working asynchronously. The orchestrator yields turn (stops calling tools, enters idle).

4. **Worker executes completion callback:**
   Upon completion or blocking, the worker executes the contract callback via `herdr_reply.py`:
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator "<STATUS> <artifacts> <issues>"
   ```
   This delivers prompt input directly to the orchestrator pane without shell mangling, waking its turn with the result. Never use bare `herdr agent prompt` directly for replies.

5. **`herdr-wait` is strictly a fallback:**
   Do not poll workers with loops or barriers during normal execution. `herdr-wait` is strictly a fallback for non-agent panes, panes lacking an agent name, or watchdog recovery.

**Every handoff carries the caller's context, and requires a reply.** A worker cannot address an orchestrator it was never told about, and a caller left to infer completion falls back on polling. So the prompt opens with the caller and Herdr skill notice, and closes with the reply contract:

```text
Caller: pane=w1:p1 label=orchestrator agent=orchestrator
Herdr: see skill ~/.agents/skills/herdr/SKILL.md — use scripts in ~/.agents/skills/herdr/scripts/ for communication, not bare herdr CLI

<the payload>

On completion, reply to the caller in one message using the herdr helper script:
  uv run ~/.agents/skills/herdr/scripts/herdr_reply.py orchestrator "<STATUS> <artifacts> <issues>"
```

`STATUS` is `COMPLETED`, `BLOCKED`, or `REJECTED`; a blocked worker names what it needs instead of waiting silently. `herdr-prompt` prepends both blocks, reading the pane id from `HERDR_PANE_ID` (falling back to `herdr pane current --current`), the label from `herdr pane list`, and the agent name from `herdr agent list`; `--no-caller-context` opts out for a broadcast where no single caller owns the result. The **agent name** is the load-bearing part — the pane id and label tell a person where to look, and only the name is addressable.

Underlying commands, if you drive them directly:

- `herdr pane rename <PANE_ID> [LABEL]... [--clear]` — the visible label; multi-word; **not** addressable.
- `herdr agent rename <TARGET> <NAME>|--clear` — the addressable name; `[a-z][a-z0-9_-]{0,31}`, unique among live agents.
- `herdr agent start <NAME> --kind <kind> --pane <id>` — name an agent as you create it.

The full split, including which response returns which name, is in `$SKILL_DIR/references/cli-reference.md`.

## Start and coordinate an agent

Default to a sibling pane in the current tab and the current working directory. Do not create a workspace, tab, worktree, or different cwd unless the user explicitly requests that topology or location.

Honor a direction requested by the user. Otherwise inspect the caller pane:

```bash
herdr pane layout --pane "$HERDR_PANE_ID"
```

Split a wide pane to the right and a narrow or tall pane down. Avoid repeated same-direction splits that create unusably narrow columns or short rows. Keep the user's focus in the calling pane and preserve the caller's working directory:

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

Replace `right` with `down` when appropriate. Read the new pane ID from `.result.pane.pane_id`.

An available shell pane must be at its interactive prompt, with the shell itself in the foreground and no foreground command, editor, or agent running. Start a supported agent in that pane with a useful unique name:

```bash
herdr agent start reviewer --kind <kind> --pane <returned-pane-id>
```

Always use the kind requested by the user. If the user did not specify the type of coding agent, confirm with them first rather than picking a random or default kind. Run `herdr agent` to inspect installed kinds and list them when asking. Pass native agent arguments only after `--`:

```bash
herdr agent start reviewer --kind <kind> --pane <returned-pane-id> -- <agent-args...>
```

A successful `agent start` returns only after Herdr detects the expected agent in the same pane and considers it ready for interactive input. Wait until the agent settles (`idle` or `done`) before prompting it.

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

1. **Caller self-names:**
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_label.py" orchestrator
   ```
2. **Dispatch workers:**
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_prompt.py" worker1 worker2 --file brief.md --no-wait
   ```
3. **Yield turn:**
   The orchestrator yields turn (stops calling tools, enters idle).
4. **Completion callback wakes caller:**
   Each worker finishes its assignment and executes the reply callback injected in the caller context:
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_reply.py" orchestrator "<STATUS> <artifacts> <issues>"
   ```
   This delivers prompt input directly to the orchestrator pane without shell mangling, waking its turn with the result.
5. **Inspect session transcripts on wake:**
   ```bash
   uv run "$SKILL_DIR/scripts/herdr_transcript.py" worker1 --last
   ```

**`herdr-wait` is strictly a fallback, not the primary coordination signal.** The event-driven callback model ensures completion arrives without the orchestrator holding a wait, burning context, or looping. Keep `herdr-wait` strictly for non-agent panes, panes without an agent name, or watchdog recovery when a worker fails to report back. Sequential `herdr agent wait A && herdr agent wait B` starves B while A runs: if B finishes or blocks in 10s and A runs 5 minutes, B is ignored for 5 minutes. If using the barrier fallback:

```bash
uv run "$SKILL_DIR/scripts/herdr_wait.py" worker1 worker2 --timeout 300000
```

The barrier exits 3 the moment any target needs input — unblock it, then re-enter the barrier for the rest. Distrust its first tick: a worker that has not begun still reads `idle`, so a barrier can return in 0ms having observed the state *before* the work. Re-enter it rather than concluding the work is done.

### Sibling-reviewer pattern

Place the reviewer next to the implementer in the same working directory so findings cite the same tree: split a sibling pane from the implementer's pane, start the reviewer with the implementer's worktree as `--cwd`, prompt both with `--no-wait`, and barrier-wait both. Confirm the reviewer kind with the user if unspecified. Agent arguments go after `--` (`agent start reviewer --kind <kind> --pane <id> -- --model <m>`); flags before `--` belong to Herdr and misplacing them breaks startup.

### Banned: sleep/timer polling loops

Never `sleep`, `schedule`, or loop `herdr agent read` to poll for completion. Snapshot polling clips on alternate-screen agents, burns context, and re-enacts the #83 hang. Use `herdr-wait` (state barrier) for agents and `herdr pane wait-output --match` (content match) for commands.

Deep CLI semantics (wait activity gate, rejection vs settled outcomes, read sources) live in `$SKILL_DIR/references/cli-reference.md`.

## Run an ordinary command in another pane

Create a sibling pane with the same geometry rule, preserve the caller's working directory, and keep user focus unchanged:

```bash
herdr pane split --current --direction right --cwd "$PWD" --no-focus
```

Read the new pane ID from `.result.pane.pane_id`, then run and inspect the command:

```bash
herdr pane run <returned-pane-id> "just test"
herdr pane wait-output <returned-pane-id> --match "test result" --timeout 120000
herdr pane read <returned-pane-id> --source recent-unwrapped --lines 120
```

`pane run` atomically sends command text and Enter. `pane wait-output` searches the selected snapshot immediately, so output that already exists can match. Use `--match <text>` for a literal substring or `--regex <pattern>` for a Rust regular expression. Omitting `--timeout` allows an indefinite wait.

Prefer `--source recent-unwrapped` for logs and transcripts. The other read sources, `--format ansi`, and the alternate-screen limit on `--lines` live in `$SKILL_DIR/references/cli-reference.md`.

## Safety and coordination rules

- Confirm coding agent kind with user first if unspecified; never pick a random or default kind.
- Use `--no-focus` for background work unless the user asked to switch context.
- Use `--current`, an explicit pane ID, or a unique agent name. Do not rely on another client's focused pane.
- Parse IDs from JSON responses. Do not derive them from sidebar order or examples.
- CLI server errors are JSON on stderr with exit status 1. CLI syntax errors exit with status 2.

Never take a consent-gated or irreversible action — closing others' workspaces or tabs, `--trust-repository`, `herdr server stop`, killing the Herdr process — without explicit user intent. Read `$SKILL_DIR/references/safety-rules.md` before acting on any of them.

## Local helpers (not upstream)

All 8 scripts in `$SKILL_DIR/scripts/` are authoritative and fully documented below with their options and exit codes; execute them directly without viewing script sources or running `--help`. They run through the repo runtime so no PATH setup is needed. All require `HERDR_ENV=1` and share the `herdr_cli.py` adapter (imported, never run). All exit `0` ok, `1` herdr failure, `2` usage or missing precondition; `herdr-prompt`, `herdr-dispatch`, and `herdr-reply` add `3` for an agent that needs human input and `4` for a wait that timed out after delivery, `herdr-wait` adds `3` for a blocked target. `~/.local/bin/<helper>` symlinks to the same scripts are optional.

### `herdr-overview` — the session at a glance

Panes grouped by workspace with the id, agent kind, agent name, label, and cwd: YAML when stdout is not a terminal, an aligned table when it is. The calling pane is marked `*` and the calling workspace header `, current`.

```bash
uv run "$SKILL_DIR/scripts/herdr_overview.py"                 # every workspace
uv run "$SKILL_DIR/scripts/herdr_overview.py" --workspace     # only the calling workspace
uv run "$SKILL_DIR/scripts/herdr_overview.py" --tab           # only the calling tab
uv run "$SKILL_DIR/scripts/herdr_overview.py" --current       # only the calling pane
uv run "$SKILL_DIR/scripts/herdr_overview.py" --format table  # force a format
```

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
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical --focus --ratio 0.3 --env FOO=bar --cwd /tmp
uv run "$SKILL_DIR/scripts/herdr_pane.py" horizontal --dry-run  # print the herdr command, split nothing
```

Guards `HERDR_ENV=1`, resolves the caller with `herdr pane current --current`, picks the auto direction from `herdr pane layout --pane <id>`, prints `new pane <id>  direction=…  caller=…  cwd=…  focus=…`.

### `herdr-dispatch` — manager-side task dispatch

Dispatches a ticket file to one or more workers with caller context and reply contract, validates worker agent names (refusing kinds), and verifies post-dispatch delivery (`revision` increment) in one command:

```bash
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" worker --file task.md --no-wait
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" worker --file task.md --wait --timeout 15000
uv run "$SKILL_DIR/scripts/herdr_dispatch.py" worker1 worker2 --file task.md --no-wait
```

Requires `--file` so tickets are always dispatched from a durable file. Refuses agent kinds (e.g. `qodercli`) with the live agent names listed. Prints `prompted <worker> (<pane>)  bytes=...  revision=...` to verify delivery.

### `herdr-reply` — callee completion callback

Delivers `<STATUS> <artifacts> <issues>` or a result payload back to the caller agent without shell mangling, without injecting another `Caller:` header or reply contract:

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

Reads the payload from `--file` (or stdin when `--file` is omitted or `-`) and forwards `--wait`, `--until`, and `--timeout`. Accepts several TARGETs for one broadcast (`herdr-prompt worker1 worker2 --file brief.md --no-wait`); `--no-wait` dispatches without waiting and is rejected alongside `--wait`. A `--wait` that times out after delivery exits 4 — prompt accepted, agent working asynchronously: yield turn and await reply callback, or resume with `herdr-wait` instead of resubmitting; only a true dispatch failure exits 1. `--label <LABEL>` takes an exact pane label instead of a TARGET, failing with the candidates when more than one pane carries it. `--dry-run` prints the exact argv as one JSON array per target and submits nothing.

Unless `--no-caller-context` is passed, it prepends the caller block, Herdr skill notice, sibling workers, and the completion-reply contract (see "Name a target, then hand off"), so the convention does not depend on a caller remembering it. When the caller has no agent name, the block says so instead of naming a target that cannot be reached. `--no-caller-context` warns loudly on stderr if targeting named agents.

### `herdr-wait` — one barrier over many agents

Polls `herdr agent get <target>` per target on a short tick — never concurrent `herdr agent wait` subprocesses (blind to the #83 event bug) and never `sleep` loops. Barrier mode waits for ALL targets; `--any` returns when ANY settles:

```bash
uv run "$SKILL_DIR/scripts/herdr_wait.py" action1 action2 --timeout 300000
uv run "$SKILL_DIR/scripts/herdr_wait.py" review1 review2 --any
uv run "$SKILL_DIR/scripts/herdr_wait.py" action1 action2 --json
```

Settled means `idle`, `done`, or `blocked`; `--until idle` without `done` auto-expands with a warning. A wanted state with revision 0 (agent unrecognized — seen on agy panes whose status bar still reads WORKING) is held, never settled: the barrier warns and keeps waiting. Any `blocked` target exits 3 immediately. The watchdog `--timeout` always applies (default 300000); expiry exits 1 naming the unsettled targets. Prints an aligned `TARGET STATUS REVISION ELAPSED SESSION_PATH` table, or JSON with `--json`.

### `herdr-transcript` — clean text from the session file

Resolves `agent_session.value` via `herdr agent get <target>` and extracts assistant text from the session JSONL (Pi and Claude Code shapes), skipping spinners, status bars, and tool-call noise. With no `agent_session` path it falls back to the pane snapshot itself (`herdr agent read <target> --source recent-unwrapped --lines 120`; tune with `--source`/`--lines`). Prefer it over bare `herdr agent read`, whose terminal snapshot clips on alternate-screen agents:

```bash
uv run "$SKILL_DIR/scripts/herdr_transcript.py" review1 --last
uv run "$SKILL_DIR/scripts/herdr_transcript.py" review1 --role user
uv run "$SKILL_DIR/scripts/herdr_transcript.py" review1 --role all --json
```

Tests for all eight: `tests/herdr/`.
