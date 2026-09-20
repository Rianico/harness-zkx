# Herdr safety and coordination rules

Depth for `$SKILL_DIR/SKILL.md`. Read before any consent-gated or irreversible action.

## Coordination

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
