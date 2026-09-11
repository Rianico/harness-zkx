# dynamic workflows guidelines

Authoring contract for workflows and roles managed by the `dynamic-workflow-wrapper` skill. Read this before editing workflows or role definitions — the schemas grow with every node, and this file is what keeps that growth maintainable.

Pointers: role definitions live in [`agents/`](agents/); the wrapper's operator steps live in [`../SKILL.md`](../SKILL.md); agent-document writing rules live in `skills/ai-engineering-expert/subskills/writing-for-agents/SKILL.md`; worktree and merge mechanics are owned by the external `branch-worktree-pr` skill (`make_copy.py`, `merge_copy.py`, `self_check.py`).

## Layout

```text
skills/dynamic-workflow-wrapper/
  workflows/converge-tasks.js
                         the run: tasks[] ➔ plan ➔ prepare ➔ per task [copy ➔ developer ➔ gate ➔
                         review ➔ merge] ➔ composite gate; never pushes, never opens a PR
  references/
    agents/*.md          canonical role definitions (developer, gate-runner, code-reviewer, ticket-planner, merger)
    agents.lock.json     cryptographic hash lock of canonical role files
    resp-format.md       dual-mode response format specification
    workflow-guidelines.md  this specification
  scripts/
    install-agents.mjs   synchronizes canonical roles to <repo>/.pi/agents/
```

The workflow body runs in a VM: no `import`, no `require`, no filesystem modules. Dynamic workflows declare explicit `meta`, call `phase()` at boundaries, and compose subagents via `agent()` and `gate()`.

## Node envelope

Every node returns the same envelope; role-specific fields sit beside it, never inside `summary`.

| Field          | Type                                   | Rule                                                                  |
| -------------- | -------------------------------------- | --------------------------------------------------------------------- |
| `summary`      | string                                 | ≤ 5 bullets of what happened; no file bodies, no logs                 |
| `artifacts`    | array of `{ path, kind }`              | absolute paths only; `kind` is `spec`, `report`, `diff`, `eval`, `pr` |
| `status`       | `COMPLETED` \| `BLOCKED` \| `REJECTED` | the route the graph reads                                             |
| `issues`       | array of issue objects                 | empty array when clean, never omitted                                 |
| `next_actions` | array of strings, optional             | only when a human decision is required                                |

An **issue** is `{ id, severity, file, line, invariant, defect, remediation }` with `severity` in `P1` (contract/correctness/security/fake test), `P2` (architecture/state safety/design drift), `P3` (real but small: dead code, missing negative test, doc drift). Formatting never becomes an issue — the gate owns it.

Downstream nodes receive **pointers plus distilled values**: `specPath`, `worktreePath`, `issues` JSON, `prUrl`. Paste a file body into a prompt and the run's context budget dies with it.

`next_actions` is the envelope's handoff field: `converge-tasks` populates it with the operator's delivery step, because the run deliberately stops before anything leaves the machine.

## Schema rules

- Plain JSON Schema, inline in the workflow script. No `$ref` between nodes — assembly inlines everything, so a shared fragment is a JS object spread, not a reference.
- A schema is a contract, not documentation: every field the workflow reads is listed in `required`, and the workflow never reads a field it did not require.
- **Open item:** `additionalProperties: false` is part of this rule and is not yet present in the shipped schemas. Until it is, a node may return extra fields that the workflow ignores.
- `summary` stays `string`; everything structured lives in its own field. If a downstream node needs a fact, it reads a named field — never prose.
- Adding a node means: add its schema, add its prompt builder, wire the call, and make sure its `agentType` is on the roster below. Three places, no more.
- A schema change is a workflow change: the role and the script move in the same commit, and the commit body says which node's contract moved.

## Evidence rules

- Deterministic work (compiler, tests, lint, format, commitlint, eval scripts) is measured by `gate-runner` and reported as `{ command, ok, exitCode, tail }` with the tail capped at 20 lines.
- Semantic work is measured by `code-reviewer` against the plan's acceptance criteria and the P1/P2/P3 ladder. It re-verifies every prior round's issue as `fixed` or `not-fixed`; an unverifiable claim is `not-fixed`.
- The pass condition is `issues.length === 0 && gate.ok`. Zero means zero: no waivers, no "minor", no deferral.
- Each round must carry the two isolation phases: `worktree-branch` (the copy is on the expected branch) and `root-untouched` (the session root gained no tracked change). They are the guards that make a per-node cwd contract enforceable without the runtime forwarding `cwd`.

### Merge evidence

Merging is the one node that mutates shared state, so its contract is stricter than the rest:

| Rule                                                                                                                                                      | Why                                                                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| The merger reports `attempts[]` as `{ exitCode, command, tail }`; `merge_copy.py` defines the enum (0 merged, 2 conflict, 1 gate failure).                | The exit code is contract-defined, unlike a prose claim.                                                                                                    |
| The **workflow** decides re-verification: any non-zero attempt ends the round, and the repaired copy is re-gated and re-reviewed before the next attempt. | A subagent deciding whether its own repair needs review is a self-report, and self-reports are how a gate gets bypassed.                                    |
| The merger attempts **one** merge per call and never retries after a repair.                                                                              | Only the workflow can sequence repair ➔ re-verify ➔ retry, and `merge_copy.py` removes the copy after a successful merge, so repair must precede the retry. |
| Budgets: `maxRounds` per task (default 5) and `maxMergeAttempts` per task (default 2). A round may carry at most one merge attempt.                       | Both loops are bounded, and exhaustion returns `BLOCKED` with the failing evidence rather than looping.                                                     |
| The integration branch is allocated in its own worktree, never by checking out in the session worktree.                                                   | Keeps `root-untouched` universal and never switches the operator's branch behind their back.                                                                |
| A run ends with a full-stack gate on the integration worktree. The project's `[pre-merge]` hook additionally gates every merge when declared.             | Without the hook the composite is only verified at the end; the run says which of the two applied.                                                          |
| A derived integration branch name that already exists is refused; reuse requires the operator to pass `integration` explicitly.                           | Stacking on an earlier run's unverified commits is a decision, not a default.                                                                               |
| The run never pushes and never opens a PR.                                                                                                                | Delivery is the operator's step (merger Mode D); a mis-verified run must not be able to reach a remote.                                                     |

**Stop-the-line is the current batch policy:** a `BLOCKED` or `EXHAUSTED` task halts the run and later tasks are reported `DEFERRED`. **Review trigger:** the first real batch where a blocked task's siblings were genuinely independent decides whether to keep stop-the-line or halt only the dependents.

## Agents

Role definitions are canonical in `references/agents/*.md`, locked by `references/agents.lock.json`, installed to `<repo>/.pi/agents/` by `scripts/install-agents.mjs`.

Roster and the caller that owns each mode:

| Role             | Dispatched by                                                                                                     |
| ---------------- | ----------------------------------------------------------------------------------------------------------------- |
| `ticket-planner` | plan node: expand task refs into acceptance criteria and evidenced dependencies                                   |
| `merger`         | prepare (integration worktree), allocate (task copy), merge (one attempt) — and, outside a run, Mode D for the PR |
| `developer`      | per-round implementation and remediation                                                                          |
| `gate-runner`    | per-round deterministic gate and the final composite gate                                                         |
| `code-reviewer`  | per-round crux review                                                                                             |

Frontmatter rules for every role:

| Key                     | Value                                                                                | Why                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ----------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `tools`                 | explicit allowlist drawn only from `read`, `bash`, `edit`, `write`                   | those four are the subagent's entire tool set: pi-dynamic-workflows builds each subagent with a shared extension-free loader (`noExtensions: true`, upstream #109), so host-extension tools never register. `ast_grep_*`, `lens_diagnostics`, `lens_diagnostic_mark`, `lsp_navigation`, `pi_lens_activate_tools` (pi-lens) and `undo_last_edit` (pi-better-edit) match nothing when named; search happens through `bash` |
| `skills`                | parent skills only (`programming-expert`, `toolchain-wiki`, `ai-engineering-expert`) | preloaded deterministically; sub-skills stay reachable through their parents and the prompt's path pointers                                                                                                                                                                                                                                                                                                              |
| `inheritSkills`         | `false`                                                                              | the role gets its declared set, not the operator's whole catalog                                                                                                                                                                                                                                                                                                                                                         |
| `inheritProjectContext` | `true`                                                                               | AGENTS.md, CONTEXT.md, and project rules reach the child                                                                                                                                                                                                                                                                                                                                                                 |
| `systemPromptMode`      | `replace`                                                                            | the role prompt is the agent, not an addition to a generic one                                                                                                                                                                                                                                                                                                                                                           |
| `completionGuard`       | `false` for read-only validators (planner, reviewer, gate)                           | those roles must not be judged as implementers                                                                                                                                                                                                                                                                                                                                                                           |
| `model`                 | absent                                                                               | the workflow's `tier` owns routing; one place to retune                                                                                                                                                                                                                                                                                                                                                                  |

Each round spawns a **fresh** agent (stateless iteration): hand it the worktree path, the acceptance criteria, and prior issues — never resume a previous subagent.

Change protocol for a role:

```bash
node scripts/install-agents.mjs --update-lock   # after editing references/agents/*
node scripts/install-agents.mjs --refresh       # install the canonical copy over the drifted one
node scripts/install-agents.mjs --check         # must exit 0
```

Role files are installed into other repositories, so the role contract is a cross-boundary surface: the lock bump in the same commit **is** the cutover signal, and the operator must re-run `--refresh` in every repo that already has `.pi/agents/`. Drift (exit 2) means the installed copy differs from canonical — show the diff and get explicit approval before refreshing; lock mismatch (exit 3) means a canonical file changed without relocking.

## Reviewing a workflow change

1. Syntax-check every workflow script in the runtime's async-body model — `uv run pytest tests/dynamic-workflow-wrapper -q` does this, plus the contract checks below.
2. `node scripts/install-agents.mjs --check` — roles aligned, locked, and every dropped `agentType` still on the roster.
3. Judge the change against this file: envelope intact, pointers not pasted content, evidence rules untouched (especially the merge table), budgets still bounded, and no node given a decision that deterministic evidence already owns.
