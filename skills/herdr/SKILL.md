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

Discover live state with:

```bash
herdr workspace list
herdr tab list --workspace "$HERDR_WORKSPACE_ID"
herdr pane current --current
herdr pane list --workspace "$HERDR_WORKSPACE_ID"
herdr agent list
```

Creation responses expose the IDs to use next. `workspace create` returns `.result.workspace`, `.result.tab`, and `.result.root_pane`; `tab create` returns `.result.tab` and `.result.root_pane`; `pane split` returns the new pane as `.result.pane`.

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
herdr agent start reviewer --kind codex --pane <returned-pane-id>
```

Use the kind requested by the user; run `herdr agent` to inspect the installed kind list and options. Pass native agent arguments only after `--`:

```bash
herdr agent start reviewer --kind codex --pane <returned-pane-id> -- <agent-args...>
```

A successful `agent start` returns only after Herdr detects the expected agent in the same pane and considers it ready for interactive input. Wait until the agent becomes idle before prompting it.

Submit work through the agent surface:

```bash
herdr agent prompt reviewer "Review the current diff and report only actionable findings." --wait --timeout 120000
```

`agent prompt` honors the pane's live bracketed-paste mode and sends text followed by encoded Enter as one ordered submission. For normal agent work, `--wait` is enough: it waits for the first settled `idle`, `done`, or `blocked` state. Do not repeat those defaults with `--until`; use `--until` only for a state-specific workflow, such as waiting for an already-running agent to request input:

```bash
herdr agent wait reviewer --until blocked --timeout 120000
```

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

If a wait fails or returns `blocked`, inspect `agent get` and the transcript before deciding what input to send. A timeout or stalled response does not prove the prompt was never delivered; do not blindly submit it again. Use the pane surface only when raw terminal control is intentional.

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

- Use `--no-focus` for background work unless the user asked to switch context.
- Use `--current`, an explicit pane ID, or a unique agent name. Do not rely on another client's focused pane.
- Parse IDs from JSON responses. Do not derive them from sidebar order or examples.
- CLI server errors are JSON on stderr with exit status 1. CLI syntax errors exit with status 2.

Never take a consent-gated or irreversible action — closing others' workspaces or tabs, `--trust-repository`, `herdr server stop`, killing the Herdr process — without explicit user intent. Read `$SKILL_DIR/references/safety-rules.md` before acting on any of them.

## Local helper — `herdr-pane` (not upstream)

The whole env-check → resolve → split sequence above, as one command. Run it through the repo's declared runtime so no PATH setup is required:

```bash
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical          # stack a pane below the caller (--direction down)
uv run "$SKILL_DIR/scripts/herdr_pane.py" horizontal        # place a pane right of the caller (--direction right)
uv run "$SKILL_DIR/scripts/herdr_pane.py"                   # caller wider than tall -> right, else down
uv run "$SKILL_DIR/scripts/herdr_pane.py" vertical --focus --ratio 0.3 --env FOO=bar --cwd /tmp
uv run "$SKILL_DIR/scripts/herdr_pane.py" horizontal --dry-run  # print the herdr command, split nothing
```

`HERDR_ENV=1` is still required; `uv` supplies the interpreter declared in the script's PEP 723 block. `~/.local/bin/herdr-pane` is an optional convenience symlink to the same script.

Guards `HERDR_ENV=1`, resolves the caller with `herdr pane current --current`, picks the auto direction from `herdr pane layout --pane <id>`, prints `new pane <id>  direction=…  caller=…  cwd=…  focus=…`. Exit `0` ok, `1` herdr failure, `2` usage or missing precondition. Tests: `tests/herdr/`.
