# Herdr safety and coordination rules

Depth for `$SKILL_DIR/SKILL.md`. Read before any consent-gated or irreversible action.

## Coordination

- Always use harness scripts in `$SKILL_DIR/scripts/` (e.g. `herdr_prompt.py`, `herdr_reply.py`, `herdr_dispatch.py`, `herdr_overview.py`), NOT bare `herdr` CLI commands, for agent communication, prompting, waiting, and overview.
- NEVER use `herdr pane send-text` or `herdr pane send-keys` to deliver prompts or replies. If target resolution fails or target has no agent, use safe alternatives (queue/watch via `herdr pane wait-output`, start agent via `herdr agent start`, or abort gracefully). Raw text sent to a shell executes directly as shell commands.
- For `agy` and revision-0 agents, Dispatch-&-Yield is REQUIRED, not advisory. Never attempt to observe `agy` agents to completion via `herdr-wait` or `herdr-prompt --wait`.
- Confirm role-to-agent mapping (role, agent kind, provider, and model) with the user before starting agents or orchestrating; never assume or pick defaults.
- Verify folder trust and agent bootstrap state before dispatching tasks (`qoderclicn` requires terminal UI trust confirmation; `pi` requires `--approve` after `--`). Ensure agent settles into `idle` or `done` before prompting (see [Agent Bootstrap](agent-bootstrap.md)).
- Use `--no-focus` for background work unless the user asked to switch context.
- Use `--current`, an explicit pane ID, or a unique agent name. Do not rely on another client's focused pane.
- Parse IDs from JSON responses. Do not derive them from sidebar order or examples.
- Client and server versions can differ after an update. Check `herdr status` before relying on new server features. A missing method is not permission to stop or upgrade a server.
- CLI server errors are JSON on stderr with exit status 1. CLI syntax errors exit with status 2.

## Worktrees

Where a repository declares a worktree tool (`wt.toml` / `.config/wt.toml`), create worktrees through it rather than `herdr worktree` — repo hooks, port allocation, and the pre-merge gate run only there (see [branch-worktree-pr](../../branch-worktree-pr/SKILL.md)).

## Consent-gated or irreversible actions

> [!warning] Consent-gated or irreversible actions
> - Do not close workspaces, tabs, panes, or sessions you did not create unless the user explicitly asked. `workspace close --group` closes the primary workspace and its linked worktree workspaces; never add it merely to bypass `workspace_group_close_required`.
> - Use `--trust-repository` only after the user has verified the repository. It grants per-request Git trust; it is not a routine retry for a failed worktree command.
> - Never run `herdr server stop` from an active session unless the user explicitly intends to stop the server and its pane processes.
> - Never kill the main Herdr process. Use named test sessions for experiments that need an isolated server.
