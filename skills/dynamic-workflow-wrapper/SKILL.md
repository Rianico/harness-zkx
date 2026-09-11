---
name: dynamic-workflow-wrapper
description: >-
  Autonomous dispatcher and lifecycle operator for pi-dynamic-workflows. Aligns canonical subagent roles, inspects project stack, routes requests to target workflows (iterative convergence loops, batch shipping, or audits), and provides unified AFK status management. Use when running autonomous tasks, multi-round goal convergence, or batch PR workflows; not for single trivial edits.
---

# dynamic-workflow-wrapper

Goal: turn an autonomous user task or shipping request into an AFK (Away-From-Keyboard) execution run, routing to the appropriate dynamic workflow with canonical roles aligned and unified status tracking.

`$SKILL_DIR` is this file's directory.

## Step 0 — Align the roles

```bash
node "$SKILL_DIR/scripts/install-agents.mjs" --check
```

| Exit | Meaning | Action |
|---|---|---|
| 0 | aligned | continue |
| 2 | missing or drifted | run without `--check` to install missing files; on **drift**, show which installed `.pi/agents/*.md` differ and ask before `--refresh` |
| 3 | `agents.lock.json` stale after a canonical edit | `--update-lock`, then re-check |
| 1 | error | report it verbatim, stop |

Canonical roles live in `$SKILL_DIR/references/agents/` (`developer`, `gate-runner`, `code-reviewer`, `ticket-planner`, `merger`), locked by `$SKILL_DIR/references/agents.lock.json`, installed to `<repo>/.pi/agents/`.

**Done when** `--check` exits 0.

## Step 1 — Preflight & detect stack

Stop with a plain report if any prerequisite fails.

| Check | Command / signal |
|---|---|
| tree clean | `git status --porcelain` (untracked `.lsz/` is tolerated) |
| git tools | `git`, `gh` on PATH; `gh auth status` green |
| stack detection | Python (`pyproject.toml`, `uv`), Rust (`Cargo.toml`, `cargo`), Node (`package.json`, `pnpm`/`npm`), Go (`go.mod`) |
| wt / worktree | `wt` present if batch shipping; fallback to git branch/worktree for single-goal convergence |

**Done when** working tree is clean and runtime stack is identified.

## Step 2 — Classify workload & route workflow

Analyze the user's intent to select the target workflow:

| Workload Type | Workflow | Source |
|---|---|---|
| Single task, bug fix, feature, `/goal`, or open refactor | `converge-goal` | `$SKILL_DIR/workflows/converge-goal.js` |
| Batch tickets (`#69`, `#71`), multi-task DAG, or integration PR | `ship-tasks` | `scripts/workflows/ship-tasks.gen.js` |
| Codebase audit, dead code sweep, or cross-cutting compliance | `codebase-audit` | Built-in pattern (`name: "codebase-audit"`) |
| Skeptical claim verification or adversarial PR review | `adversarial-review` | Built-in pattern (`name: "adversarial-review"`) |

### Build Arguments

#### For `converge-goal`:

```json
{
  "task": "Implement async token refresh with lock guard",
  "maxAttempts": 5,
  "stack": "python-uv",
  "evalDir": null,
  "base": "main",
  "branch": "feat/token-refresh-lock"
}
```

`base` and `branch` are optional. Prepare resolves the base (falling back to the repo default) and derives `branch` as `converge/<task-slug>` when omitted. The run creates ONE persistent worktree for the whole loop — `wt switch --create … --no-cd` when `command -v wt` and `.config/wt.toml` both exist, else `git worktree add` — and reuses it on resume. Every round works inside that worktree through an explicit absolute-path contract, because `agent(prompt, { cwd })` is not forwarded by the runtime; the deterministic gate fails the round if the session root gains a tracked change. The worktree is left in place at the end: it holds the run's commits, and merge/PR ownership stays with the operator.
#### For `ship-tasks`:
```json
{
  "batch": "token-refresh",
  "integration": "ship/token-refresh",
  "base": "main",
  "maxRounds": 5,
  "tasks": [
    { "kind": "issue", "ref": "#69", "dependsOn": [] },
    { "kind": "task", "ref": "add token expiry test", "dependsOn": ["#69"] }
  ]
}
```

**Done when** target workflow is selected and arguments conform to its schema.

## Step 3 — Invoke AFK background workflow

Invoke the workflow via the Pi `workflow` tool with `background: true`:
- For custom scripts (`converge-goal`): pass file content as `script` with structured `args`.
- For built-in patterns (`codebase-audit`): pass `name` with structured `args`.

Report the assigned `runId` and confirm headless execution has started.

```bash
# Run status ledger location:
~/.pi/workflows/projects/<project>/runs/<runId>.json
```

**Done when** the run ID is captured and background task is active.

## Step 4 — Unified status tracking & reporting

Monitor execution or await completion. When the workflow terminates, parse the run ledger and return the Unified Status Table:

```markdown
### Workflow Run `<runId>` [<STATUS>]
**Workflow**: `<name>` | **Attempts**: `<n>/<max>` | **Duration**: `<elapsed>`
**Worktree**: `<path>` (branch `<branch>`, base `<base>`) — left in place for review/merge

| Task / Goal | Status | Attempts | Deterministic Gate | Crux Code Review | Touched Artifacts |
|---|---|---|---|---|---|
| <Task description> | **CONVERGED** | 2 | PASS (pytest) | PASS (0 issues) | `src/auth.py`, `tests/test_auth.py` |

**Outcome**:
- `<summary of converged outcome or exact blocking defect>`
```

| Status | Definition |
|---|---|
| `CONVERGED` | All deterministic tests pass AND Crux code review reports 0 P1/P2 issues. |
| `BLOCKED` | A subagent declared an impossible requirement, unresolvable merge, or scope violation. |
| `EXHAUSTED` | Reached `maxAttempts` without achieving convergence across both gates. |

**Done when** final status is delivered and merge/commit ownership is returned to the user.

## Rules

- Keep manual edits out of this skill: its writes are `install-agents.mjs` and workflow execution artifacts.
- Deterministic checks (`eval-gate`, compiler, tests) always gate before semantic review (`code-review`).
- Never mark a run `CONVERGED` if any P1 or P2 Crux invariant is unaddressed.
- Unified status contract is mandatory across all workflows: every node returns the Node Envelope.

## Reference

- [workflow-guidelines.md](references/workflow-guidelines.md) — Node envelope, schema rules, and evidence contracts.
- [resp-format.md](references/resp-format.md) — Dual-mode subagent response format (Markdown & JSON Schema).

