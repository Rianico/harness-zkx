# Subagent `cwd` vs managed worktree — neutral mapping

Persistent `wt` siblings already own the branch + hooks (`post-start` copy-ignored, `pre-merge` gate, `hash_port`). The subagent must not create a second managed copy.

## Rule

- **Persistent write sibling** (needs `wt merge` back to parent) → `cwd=<absolute wt sibling path>`, managed worktree **off**, one writer per `cwd`.
- **Throwaway audit** (no merge, synthesis only) → `cwd` unset, managed worktree **on** allowed. Patch stays in worker output, not in a branch.

## Tool-variant mapping — model adjusts via tool introspection

Don't hardcode a package name. At call time the model checks the installed subagent tool's input schema (`describe`/`inputSchema`) and maps the semantics:

| Semantics                | Spelling variants observed                             | How to detect                                                      |
| ------------------------ | ------------------------------------------------------ | ------------------------------------------------------------------ |
| Managed worktree **off** | `worktree:false`, `isolation:"off"`, or omit the field | tool input has `worktree` enum `worktree\|off` or `isolation` enum |
| Managed worktree **on**  | `worktree:true` / `isolation:"worktree"`               | same field                                                         |
| Child checkout           | `cwd` absolute path                                    | tool has `cwd: string`                                             |

If the tool lacks `cwd`, dispatch via a new session whose `cwd` is the sibling path (outer orchestration). If it lacks a managed flag, the absence of `cwd` means on, presence means the outer checkout is used — treat that as `off`.

## Pre-flight

```bash
# subagent tool shape is the source of truth — branch-worktree-pr never restates it
# list siblings the model will target
wt list --format=json | jq '.[] | {branch, path}'
# gate stays in wt
cat .config/wt.toml | rg "pre-merge" -A 2
```

Model always prefers `cwd` on + managed off for write siblings; fallback is a fresh agent started in that worktree's directory.
