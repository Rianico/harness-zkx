---
name: dynamic-workflow-wrapper
description: >-
  Autonomous dispatcher for pi-dynamic-workflows — aligns canonical subagent roles, inspects the project stack, routes to the target workflow (convergence or audit), and tracks AFK status. Use when running autonomous tasks or converging work to a verified branch; not for single trivial edits.
---

# dynamic-workflow-wrapper

Goal: turn an autonomous user task or shipping request into an AFK (Away-From-Keyboard) execution run, routing to the appropriate dynamic workflow with canonical roles aligned and unified status tracking.

`$SKILL_DIR` is this file's directory.

## Step 0 — Align the roles

```bash
node "$SKILL_DIR/scripts/install-agents.mjs" --check
```

| Exit | Meaning                                         | Action                                                                                                                                 |
| ---- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 0    | aligned                                         | continue                                                                                                                               |
| 2    | missing or drifted                              | run without `--check` to install missing files; on **drift**, show which installed `.pi/agents/*.md` differ and ask before `--refresh` |
| 3    | `agents.lock.json` stale after a canonical edit | `--update-lock`, then re-check                                                                                                         |
| 1    | error                                           | report it verbatim, stop                                                                                                               |

Canonical roles live in `$SKILL_DIR/references/agents/` (`developer`, `gate-runner`, `code-reviewer`, `ticket-planner`, `merger`), locked by `$SKILL_DIR/references/agents.lock.json`, installed to `<repo>/.pi/agents/`. Editing a role is a cross-repository contract change: bump the lock in the same commit and tell the operator to re-run `--refresh`.

**Done when** `--check` exits 0.

## Step 1 — Preflight & detect stack

Stop with a plain report if any prerequisite fails.

| Check             | Command / signal                                                                                                                                           |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| tree clean        | `git status --porcelain` (untracked `.lsz/` is tolerated)                                                                                                  |
| git tools         | `git` on PATH; `gh` on PATH and `gh auth status` green only when a task refs an issue or the operator wants a PR later                                     |
| stack detection   | Python (`pyproject.toml`, `uv`), Rust (`Cargo.toml`, `cargo`), Node (`package.json`, `pnpm`/`npm`), Go (`go.mod`)                                          |
| wt / worktree     | `wt` present for multi-task runs and preferred for all; `git worktree` is the fallback                                                                     |
| merge gate wiring | `rg -n '^\[pre-merge\]' .config/wt.toml` — when absent, merge attempts are not composite-gated and only the run's final gate covers the integration branch |

**Done when** working tree is clean and runtime stack is identified.

## Step 2 — Classify workload & route workflow

| Workload Type                                                                                                        | Workflow             | Source                                          |
| -------------------------------------------------------------------------------------------------------------------- | -------------------- | ----------------------------------------------- |
| Converging work: single task, bug fix, feature, `/goal`, open refactor, batch tickets (`#69`, `#71`), multi-task DAG | `converge-tasks`     | `$SKILL_DIR/workflows/converge-tasks.js`        |
| Codebase audit, dead code sweep, or cross-cutting compliance                                                         | `codebase-audit`     | Built-in pattern (`name: "codebase-audit"`)     |
| Skeptical claim verification or adversarial PR review                                                                | `adversarial-review` | Built-in pattern (`name: "adversarial-review"`) |

### Build Arguments

```json
{
  "tasks": [
    { "kind": "issue", "ref": "#69", "dependsOn": [] },
    { "kind": "task", "ref": "add token expiry test", "dependsOn": ["#69"] }
  ],
  "base": "main",
  "integration": "dev/token-refresh",
  "maxRounds": 5,
  "maxMergeAttempts": 2,
  "stack": "python-uv",
  "evalDir": null
}
```

| Argument           | Rule                                                                                                                                                                                                         |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `tasks`            | The interface. An array of `{ kind: "issue" \| "task", ref, dependsOn? }`; a single task is an array of one. Ids default to `ref`.                                                                           |
| `base`             | Optional; Prepare resolves it (falling back to the repo default) and reports `baseSource`.                                                                                                                   |
| `integration`      | Optional. Names the integration branch (default `dev/<batch-slug>`) **and** is the operator's authority to reuse an existing branch or worktree of that name. A derived name that already exists is refused. |
| `branch`           | Optional, single-task runs only: overrides the task branch name (default `task/<id-slug>`).                                                                                                                  |
| `batch`            | Optional label used for the derived integration branch name.                                                                                                                                                 |
| `maxRounds`        | Convergence rounds per task, 1-10, default 5.                                                                                                                                                                |
| `maxMergeAttempts` | Merge attempts per task, 1-3, default 2.                                                                                                                                                                     |
| `stack`, `evalDir` | Optional hints passed to the developer and gate nodes.                                                                                                                                                       |

### Topology rules

- **`tasks.length === 1`** — no integration branch. The task branch is the deliverable and its worktree is left in place.
- **`tasks.length > 1`** — every task branch is copied off the _current_ integration head, so later tasks see earlier merges; each successful task is merged into the integration branch, and the run ends with a full-stack gate on the integration worktree. The integration branch lives in its OWN worktree — the session root's branch is never switched.
- **Delivery is a verified local branch.** The run never pushes and never opens a PR; it returns `nextActions` naming the operator step (merger Mode D). Nothing external is emitted unattended.
- **Merge attempts are one per round.** A non-zero `merge_copy.py` exit ends the round, so the repaired copy is re-gated and re-reviewed before the next attempt. The merger reports exit codes; the workflow decides re-verification.
- **Worktrees:** a successful merge removes the task copy (`merge_copy.py`); a blocked run leaves every worktree in place with its branch intact.
- **Batching is stop-the-line:** a task that ends `BLOCKED` or `EXHAUSTED` halts the run and every later task is reported `DEFERRED`, so the integration branch never grows past the last verified task.
- **`agent(prompt, { cwd })` is not forwarded** by the runtime, so every node receives an absolute-path contract; the deterministic gate fails the round if the session root gains a tracked change.

**Done when** target workflow is selected and arguments conform to its schema.

## Step 3 — Invoke AFK background workflow

Invoke the workflow via the Pi `workflow` tool with `background: true`:

- For custom scripts (`converge-tasks`): pass the file content as `script` with structured `args`.
- For built-in patterns (`codebase-audit`, `adversarial-review`): pass `name` with structured `args`.

Report the assigned `runId` and confirm headless execution has started.

```bash
# Run status ledger location:
~/.pi/workflows/projects/<project>/runs/<runId>.json
```

**Done when** the run ID is captured and background task is active.

## Step 4 — Unified status tracking & reporting

Monitor execution or await completion. The run result owns per-task evidence; the run ledger owns lifecycle. Return the Unified Status Table from those, never hand-authored:

```markdown
### Workflow Run `<runId>` [<STATUS>]

**Workflow**: `converge-tasks` | **Rounds**: `<n>/<max>` per task | **Duration**: `<elapsed>`
**Delivery**: `<branch>` at `<path>` (mode `<task-branch|integration-branch>`, base `<base>`) — verified local branch, NOT pushed

| Task             | Status     | Rounds | Merge              | Deterministic Gate | Crux Review           | Worktree |
| ---------------- | ---------- | ------ | ------------------ | ------------------ | --------------------- | -------- |
| `<id>` — `<ref>` | **MERGED** | 2      | exit 0 (1 attempt) | PASS (pytest)      | PASS (0 issues, 9/10) | `<path>` |

**Next actions**:

- `<verbatim result.nextActions>`
```

| Status             | Definition                                                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------- |
| `CONVERGED` (run)  | Every task is `MERGED` or `CONVERGED` and, for a multi-task run, the composite gate on the integration worktree is green. |
| `CONVERGED` (task) | Single-task run: all deterministic checks pass AND Crux review reports 0 P1/P2 issues.                                    |
| `MERGED` (task)    | The task's copy was merged into the integration branch (one attempt, exit 0).                                             |
| `DEFERRED` (task)  | Not attempted because an earlier task halted the run.                                                                     |
| `BLOCKED`          | A node declared an impossible requirement, an unresolvable merge, or a scope violation; also a red final composite gate.  |
| `EXHAUSTED`        | A task reached `maxRounds` without convergence, or exhausted `maxMergeAttempts`.                                          |

**Done when** the final status is delivered, the delivery branch and worktree are named, and merge/PR ownership is returned to the user with `nextActions`.

## Rules

- Keep manual edits out of this skill: its writes are `install-agents.mjs` and workflow execution artifacts.
- Deterministic checks (`eval-gate`, compiler, tests) always gate before semantic review (`code-review`).
- Never mark a run `CONVERGED` if any P1 or P2 Crux invariant is unaddressed.
- The workflow never pushes and never opens a PR. Merge approval is the human's (merger Mode D).
- Re-verification after a merge repair is derived from merge exit codes, never from a subagent's self-report.
- Unified status contract is mandatory across all workflows: every node returns the Node Envelope, and `nextActions` is populated whenever a human decision remains.

## Reference

- [workflow-guidelines.md](references/workflow-guidelines.md) — Node envelope, schema rules, merge evidence, and role contract rules.
- [resp-format.md](references/resp-format.md) — Dual-mode subagent response format (Markdown & JSON Schema).
- [agents/merger.md](references/agents/merger.md) — Worktree lifecycle, merge attempt, and the operator-invoked PR.
