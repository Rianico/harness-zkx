# Herdr CLI reference

Depth for `$SKILL_DIR/SKILL.md`. The installed binary is always the authority; run `herdr --help`, then a command group without a subcommand.

## Command groups

```bash
herdr agent
herdr pane
herdr workspace
herdr tab
herdr worktree
herdr terminal
herdr notification
herdr integration
herdr session
herdr machine
```

Do not run bare `herdr` for discovery; it launches or attaches the TUI. Do not probe a mutating nested command by omitting arguments — commands such as `herdr workspace create` are valid with defaults and will execute.

Most control commands return JSON. Read identifiers and state from those responses instead of predicting them.

## Agent lifecycle states

`idle` and `done` both mean the agent is ready for input — unless the record is weakly recognized. A record reporting `idle`/`done` with revision 0 and no `agent_session` path (seen on agy panes whose status bar still reads WORKING) proves nothing; hold the barrier and confirm via the pane. The CLI/API uses the server's seen state to distinguish them; explicit focus commands mark the target seen, while reads do not. Each TUI client tracks viewed completions independently, so its Done badge can differ from the CLI or another client's badge. `blocked` means Herdr recognized an approval or question UI. `unknown` means an agent is present but Herdr cannot classify it confidently; it does not prove completion.

Agent commands accept either a unique live agent name or the pane ID currently hosting that agent. They do not accept terminal IDs or bare agent-kind labels. Names must match `[a-z][a-z0-9_-]{0,31}` and be unique among live agents. A name follows the current pane occupant and is cleared when that agent exits, is released, or is replaced.

## Names, labels, and targets

Two kinds of names exist, and they disagree about who can use them:

| command | sets | where it shows | accepted as a target |
| --- | --- | --- | --- |
| `herdr pane rename <PANE_ID> [LABEL]...` | pane `label` | the **pane border** — the name a person reads off the screen | **no** — `pane get <label>` fails with `pane_not_found` |
| `herdr agent rename <TARGET> <NAME>` | agent `name` | only through `ui.show_agent_labels_on_pane_borders`, and only when no manual label is set | **yes** — `agent prompt`, `wait`, `read`, `send-keys`, `focus` |

The label is durable: it belongs to the pane and outlives the agent. The name is an alias for the current agent in that pane and is cleared when that agent exits, is released, or is replaced — the upstream docs say plainly that it "does not permanently rename the pane".

Labels are **not unique**: `pane rename` accepts the same label on any number of panes. A name must match `[a-z][a-z0-9_-]{0,31}` and be unique among live agents. Both take `--clear`, and a label may be several words.

Because a person names what they can see, `herdr-label` sets both to the same string, and `herdr-prompt --label` resolves an exact label to its pane id, failing with the candidate pane ids when several panes carry it.

No single response answers "which pane is this, by name": `PaneInfo` carries `label` and never the agent `name`; `AgentInfo` carries `name` and never `label`. Joining the two by `pane_id` is what `herdr-overview` does.

## Agent start and prompt semantics

A successful `agent start` returns only after Herdr detects the expected agent in the same pane and considers it ready for interactive input. If the agent is blocked during startup, the command returns `agent_not_ready` immediately but keeps the name available for `agent read` and `agent send-keys`. Startup defaults to a 30-second timeout. Always confirm the agent kind (`--kind`) with the user first if unspecified; never pick a random or default agent kind.

`agent prompt` reports successful submission only after the text and encoded Enter are both written; that alone does not prove the agent started a turn. The submit delay grows with prompt size for Codex on Windows. It rejects an agent already waiting at an approval or question dialog with `agent_blocked` before sending any input — inspect the blocked UI and ask the user before answering it. For normal agent work, `--wait` is enough: it waits for the first settled `idle`, `done`, or `blocked` state. Do not repeat those defaults with `--until`.

With `--wait`, a prompt sent from a non-working state must produce observed `working` or `blocked` activity. After submission, Herdr waits up to five seconds for that activity; unrelated `idle`, `done`, or session changes do not satisfy this gate. It returns `agent_prompt_stalled` if no activity is observed, or `timeout` if the caller's timeout expires first. The caller timeout includes submission time. Without a timeout, the settled-state wait is indefinite after activity is observed. This wait tracks lifecycle state, not an individual turn; if the agent is already working, completion of the active turn may satisfy it.

Without `--until`, standalone `agent wait` uses the same settled-state defaults as `agent prompt --wait`.

Read the outcome two ways. A *rejection* is a client error: `agent_blocked` arrives as `{"error":{"code":"agent_blocked","message":"…"},"id":"cli:agent:prompt"}` on stderr with exit status 1, and nothing was sent. A *settled* wait is a success: `--wait` that matches `blocked` exits 0 with `result.agent.agent_status = "blocked"`, meaning the prompt was delivered and the target now awaits input. Inspect the returned state, not just the exit status.

## Read sources and formats

Use the read source that matches the task:

- `visible`: the currently rendered viewport.
- `recent`: recent rendered output, including soft wraps.
- `recent-unwrapped`: recent output with soft wraps joined; prefer it for logs and transcripts.
- `detection`: the plain-text bottom-buffer snapshot used for agent detection.

Use `--format ansi` when colors and terminal styling are evidence. Otherwise use text.

`--lines` asks Herdr for more rows from the pane's available screen and host scrollback. If increasing it does not reveal more of a completed response, the pane is probably running the agent on the terminal's alternate screen. Rows that leave the alternate screen do not enter Herdr's host scrollback, so a larger line count cannot recover them. Prefer the agent's own transcript (`agent get` → `agent_session.value`) over a terminal snapshot.

## IDs across servers

IDs and live agent names are scoped to one server. Two saved SSH machines can both have `w1:p1` or an agent named `reviewer`. Selecting a machine in the TUI does not retarget commands running in your pane: they still use the inherited session and socket context. Run remote control commands on the intended host with its explicit session, and rediscover IDs there.

Closed tab and pane IDs are not reused. A pane moved into another workspace receives a new workspace-qualified pane ID. After `pane move`, continue with `.result.move_result.pane.pane_id` or the live agent name. The old value is reported as `.result.move_result.previous_pane_id`; only the moved process's inherited caller context keeps resolving that old ID, so do not use it as a general agent target.

## Machine connection profiles

`herdr machine list` lists saved connection profiles, not a cross-machine pane inventory; add `--json` for scripts. Only add, remove, enable, or disable profiles when the user asks. Removing a profile disconnects the client but does not stop remote sessions. Adding a machine uses the remote default session unless `--remote-session` is explicitly supplied. Setup asks before stopping an incompatible server and defaults to No; do not approve replacement without the user's consent. Experimental handoff is not part of `machine add`.
