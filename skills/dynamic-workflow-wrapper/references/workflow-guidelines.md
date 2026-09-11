# dynamic workflows guidelines

Authoring contract for workflows and roles managed by the `dynamic-workflow-wrapper` skill. Read this before editing workflows or role definitions — the schemas grow with every node, and this file is what keeps that growth maintainable.

Pointers: role definitions live in [`agents/`](agents/); the wrapper's operator steps live in [`../SKILL.md`](../SKILL.md); agent-document writing rules live in `skills/ai-engineering-expert/subskills/writing-for-agents/SKILL.md`.

## Layout

```text
skills/dynamic-workflow-wrapper/
  workflows/
    converge-goal.js     standalone AFK goal convergence loop (developer ➔ eval-gate ➔ code-review)
  references/
    agents/*.md          canonical role definitions (developer, gate-runner, code-reviewer, etc.)
    agents.lock.json     cryptographic hash lock of canonical role files
    resp-format.md       dual-mode response format specification
    workflow-guidelines.md  this specification
  scripts/
    install-agents.mjs   synchronizes canonical roles to <repo>/.pi/agents/
```

The workflow body runs in a VM: no `import`, no `require`, no filesystem modules. Dynamic workflows declare explicit `meta`, call `phase()` at boundaries, and compose subagents via `agent()`, `gate()`, and `parallel()`.


## Node envelope

Every node returns the same envelope; role-specific fields sit beside it, never inside `summary`.

| Field | Type | Rule |
|---|---|---|
| `summary` | string | ≤ 5 bullets of what happened; no file bodies, no logs |
| `artifacts` | array of `{ path, kind }` | absolute paths only; `kind` is `spec`, `report`, `diff`, `eval`, `pr` |
| `status` | `COMPLETED` \| `BLOCKED` \| `REJECTED` | the route the graph reads |
| `issues` | array of issue objects | empty array when clean, never omitted |
| `next_actions` | array of strings, optional | only when a human decision is required |

An **issue** is `{ id, severity, file, line, invariant, defect, remediation }` with `severity` in `P1` (contract/correctness/security/fake test), `P2` (architecture/state safety/design drift), `P3` (real but small: dead code, missing negative test, doc drift). Formatting never becomes an issue — the gate owns it.

Downstream nodes receive **pointers plus distilled values**: `specPath`, `worktree.path`, `issues` JSON, `prUrl`. Paste a file body into a prompt and the run's context budget dies with it.

## Schema rules

- Plain JSON Schema, inline in `schemas.js`. No `$ref` between nodes — assembly inlines everything, so a shared fragment is a JS object spread (`...ENVELOPE.properties`), not a reference.
- A schema is a contract, not documentation: `additionalProperties: false`, every field in `required`, no optional chaining in the workflow body without a null guard.
- `summary` stays `string`; everything structured lives in its own field. If a downstream node needs a fact, it reads a named field — never prose.
- Adding a node means: add its schema, add its prompt builder, wire the call, and add its `agentType` to the roster in this file's sibling `agents/`. Three places, no more.
- A schema change is a workflow change: rebuild (`node scripts/workflows/ship-tasks/build.mjs`) in the same commit, and say in the commit body which node's contract moved.

## Evidence rules

- Deterministic work (compiler, tests, lint, format, commitlint, eval scripts) is measured by `gate-runner` and reported as `{ command, ok, exitCode, tail }` with the tail capped at 20 lines.
- Semantic work is measured by `code-reviewer` against the spec's acceptance criteria and the P1/P2/P3 ladder. It re-verifies every prior round's issue as `fixed` or `not-fixed`; an unverifiable claim is `not-fixed`.
- The pass condition is `issues.length === 0 && gate.ok`. Zero means zero: no waivers, no "minor", no deferral.
- `maxRounds` defaults to 5. Exhaustion leaves the worktree in place and returns `BLOCKED` with the failing evidence; the batch stops rather than skipping ahead.

## Agents

Role definitions are canonical in `references/agents/*.md`, locked by `references/agents.lock.json`, installed to `<repo>/.pi/agents/` by `scripts/install-agents.mjs`.

Frontmatter rules for every role:

| Key | Value | Why |
|---|---|---|
| `tools` | explicit allowlist, including the full pi-lens set | omitting it grants everything; a partial pi-lens set makes tool availability a surprise |
| `skills` | parent skills only (`programming-expert`, `toolchain-wiki`, `ai-engineering-expert`) | preloaded deterministically; sub-skills stay reachable through their parents and the prompt's path pointers |
| `inheritSkills` | `false` | the role gets its declared set, not the operator's whole catalog |
| `inheritProjectContext` | `true` | AGENTS.md, CONTEXT.md, and project rules reach the child |
| `systemPromptMode` | `replace` | the role prompt is the agent, not an addition to a generic one |
| `completionGuard` | `false` for read-only validators (planner, reviewer, gate) | those roles must not be judged as implementers |
| `model` | absent | the workflow's `tier` owns routing; one place to retune |

Each round spawns a **fresh** agent (stateless iteration): hand it the worktree path, spec path, and prior issues — never resume a previous subagent.

Change protocol for a role:

```bash
node scripts/install-agents.mjs --update-lock   # after editing references/agents/*
node scripts/install-agents.mjs --refresh       # install the canonical copy over the drifted one
node scripts/install-agents.mjs --check         # must exit 0
```

Drift (exit 2) means the installed copy differs from canonical — show the diff and get explicit approval before `--refresh`. Lock mismatch (exit 3) means a canonical file changed without relocking.

## Reviewing a workflow change

1. Syntax check workflow script (`node -c <workflow.js>`) — must exit 0.
2. `node scripts/install-agents.mjs --check` — roles aligned and locked.
3. Judge the change against this file: envelope intact, pointers not pasted content, evidence rules untouched, roster consistent.
