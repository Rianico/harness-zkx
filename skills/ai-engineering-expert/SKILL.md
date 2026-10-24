---
name: ai-engineering-expert
description: >-
  AI engineering methodology spine for LSZ harness — context-load, skill authoring, agent design, agent-doc writing, testing, subagent-first execution. Use when creating or editing skills, agents, rules, or agent docs (SKILL.md, AGENTS.md, CLAUDE.md), or diagnosing context bloat or discovery failure.
arguments: domain
argument-hint: |-
  skill-authoring -- loads skill design and diagnosis methodology: taxonomy, frontmatter, descriptions, invocation classes, description budgets, trigger diagnosis, progressive disclosure, rules-vs-skills boundary, platform sync, and authoring checklists
  subagent-engineering -- loads subagent methodology: context isolation firewalls, speculative drafting, dispatch gates, fresh versus inherited context, action space scoping, and orchestration constraints
  verification -- loads verification methodology: EDD, deterministic vs semantic verification, AI regression patterns, runtime trace fixtures, and eval-first loops
  writing-for-agents -- loads agent-document writing: context pointers, hierarchy, disclosure, completion criteria, leading words, pruning; use when writing/editing SKILL.md, AGENTS.md, CLAUDE.md or any agent-consumed doc
  writing-for-humans -- loads human-facing proposal writing: problem-first framing, evidence grounding, scannability, explicit asks; use when drafting/reviewing GitHub issues, RFCs, or proposals
  omitted -- loads only the core AI engineering philosophy and the sub-skill dispatch registry
metadata:
  manage: [skill-authoring, subagent-engineering, verification, writing-for-agents, writing-for-humans]
---

# AI Engineering Expert

Core principles for building reliable AI systems in the LSZ harness. This file holds the 20% that solves 80% of problems. Deep methodology lives in subskills and their references.

## The Foundation: IDD & GDD

AI engineering turns human intent into verified artifacts. **IDD** owns intent. **GDD** derives goals from intent.

- **Formal Substrate**: Compilers, linters, typecheckers, and tests return pass/fail. The substrate owns environmental truth and supplies verification data.
- **Semantic Reasoner**: The model navigates ambiguity, resolves conflicts, and proposes integrations when the substrate reports an impasse.

> Pointers:
> - [Information boundary pattern](references/information-boundary.md). Use when you split a check between tool and model.
> - [Tool design contracts](references/tool-design-contracts.md). Use when you design tool schemas, CLI output streams, or error recovery.

### 1. IDD (Intent-Driven Development): Source of Authority

IDD answers *Why change reality?* It anchors purpose and boundary invariants before code or goals exist.

Clear, concise human intent is the prerequisite of all execution. Ambiguous direction always causes disaster. Never assume intent arrives fully formed. Humans experience symptoms and solution biases. They carry unknown unknowns. The harness must actively draw out intent before formalizing goals.

#### Intent Probing Rules
- **Look Before You Ask**: Investigate the environment (code, git history, dependencies) first. Facts belong to the harness. Decisions belong to the user.
- **Excavate Unknown Unknowns**: Match ambiguity to the probing pattern (root-cause drilling, approaches matrix, decision frontiers).
- **Say Defaults Out Loud**: Never leave implicit architectural assumptions unvoiced. A default the user never heard is one they could not reject.
- **The Confirmation Gate**: Settle the **Intent Contract** with explicit human alignment before entering GDD.

#### The Intent Contract
- **Problem**: Concrete deficiency, friction, or regression in the current state.
- **Proposed Outcome**: Observable change in behavior, capability, or invariant once resolved.
- **Affected Seams**: Architectural boundaries, module interfaces, or protocols touched.
- **Non-Negotiable Constraints**: Invariants, backward compatibility, performance ceilings, and explicit **Non-Goals**.

> Pointer: [Intent-Driven Development](references/intent-driven-development.md). Use when probing ambiguous requests, excavating unknown unknowns, or establishing intent contracts.

### 2. GDD (Goal-Driven Development): Derived Operational Spine

GDD derives verifiable milestone world states from intent. It answers *What world state confirms the intent was realized?*

### 3. The Derivation Chain

1. **Intent (IDD)**: Establishes human purpose and boundary invariants.
2. **Derived Goals (GDD)**: Converts intent into discrete, ordered milestone states.
3. **BDD Contracts**: Defines behavior as Given/When/Then acceptance criteria.
4. **EDD Verification**: Runs `test`, `lint`, and `typecheck`. **Environmental Truth is the Supreme Authority**, above any model claim.

Both ends are mandatory:

- **Goal without intent** causes **Specification Gaming** (Goodhart's Law): the agent optimizes the metric itself.
- **Intent without goal** causes **Semantic Drift**: unbounded refactors that never converge.

### 4. Root-Cause Archetypes for Agent Failure

Build checks over writing rules. Classify each failure by cause:

- **Mechanical Violation** (syntax, types, banned APIs, file paths) → Add a deterministic tool to the Formal Substrate.
- **Semantic Ambiguity** (plausible but divergent reading) → Refine the prompt contract: tripartite formula, negative boundary, input/output specs, STE-100 terms.
- **Semantic Disregard** (clear rule, ignored under pressure) → Enforce via Context Pressure Asymmetry, or a hard tool gate.
- **Route Friction** (manual compliance) → Pack the steps into `scripts/<cmd>`. Make the governed path the cheapest.
- **Stale-context carryover** (the draft inherits the state it was asked to replace) → Regenerate the sentence from the artifact. Re-derive every count at the moment of use. Then sweep the prose that described the old state (ledger, commit message, PR body, reviewer brief). A patch inherits its host's defects, and a claim written for the old state outlives the reversal.

## Context Architecture & Progressive Disclosure

Context load is a primary architectural constraint. Attention degrades as context grows.

### The 80/20 Rule

`SKILL.md` holds the 20% that solves 80% of problems. Reference files behind context pointers hold the deep 80%, recursively across spine, subskills, and references.

Read the [context-load policy](subskills/skill-authoring/references/context-load-policy.md) for enforcement gates, description budgets, and platform sync. Use when you set a load cost or audit a violation.

- **Plain Language Standard**: Follow [plain-language.md](references/plain-language.md) for ASD-STE100 active voice, concise sentences, and banned filler.

### Root Steering via AGENTS.md

- `AGENTS.md` is the open standard ([agents.md](https://agents.md)). The closest file wins. Nested files are supported. `CLAUDE.md` and other agent variants are compatibility mirrors. Keep the file to navigation pointers.

### Activate Knowledge on Demand

- **Dispatch on Demand**: Isolate specialized workflows into subskills. Load them by handle. On-demand loading costs one invocation and keeps base context focused.
- **Parametric Anchoring**: Name the canonical source for cheap recall.
  - **Module design**: When a task places a seam, use Ousterhout's terms: deep module, information hiding, narrow interface.
  - **Test-first work**: When a test must fail first, use Kent Beck's red-green-refactor loop.
  - **Refactoring**: When a change touches existing code, name the smell first: divergent change, shotgun surgery.
  - **Interface contracts**: When you narrow an interface, state which caller expectation must still hold.

Parametric recall supplies shape, not proof. Confirm specifics against a check.

- **Invoke the Skill**: When a task needs domain methodology, invoke the installed skill for that domain. Keep the methodology out of the prompt.
- **Separate the Scopes**: The agent owns identity and action space. The skill supplies domain methodology. The rule holds repo-wide constraints. The phase prompt covers one step.

### Context Pressure Asymmetry

Split implementation from review. Each side carries a different context load:

- **Implementer**: Give it the full budget: exploration, drafts, failing output. Keep standards out of its prompt.
- **Reviewer**: Give it the diff only, with zero exploration. Load standards, invariants, and skepticism there.

### Pruning & Artifact Hygiene

Every change must preserve or improve organization. Accumulation creates bloat.

- **Prune No-Ops**: Delete steering instructions that do not measurably alter agent decisions.
- **Audit before you edit**: Find the redundancy, then the right home. Every addition names the old content it replaces.
- **One concept, one canonical location**: Group by topic. Reference the canonical source instead of copying it.
- **Signals of failure**: Files over the size budget, duplicated concepts, catch-all sections, unclear ordering.
- **Normalize paths**: Always use forward slashes.
- **Gate structural changes**: Run `validate-deps.py check` after a rename, move, or dependency change. Run `lint` after a metadata edit.
- **Tooling Preference**: Use `rg` for content search and `fd` for file discovery. Reserve `ls` and `tree` for structure.

## Execution & Delegation Boundaries

### Subagent-First Execution

**The orchestrator never does implementation work.** Route, dispatch, monitor, and synthesize in the primary agent. Keep code writing, file edits, and verbose test triage inside subagents. This mandate covers every coding agent.

- Orchestration contracts and execution: read `subskills/subagent-engineering/SKILL.md`. Use when you write a dispatch prompt, pick a context topology, define response contracts, or tier the model.
- **Hero-Mode Prevention**: Generic models ignore delegation under load, so dispatching skills SHOULD define explicit execution schemas.

### Model Routing

| Model Tier | Use For                                               | Avoid                                     |
| ---------- | ----------------------------------------------------- | ----------------------------------------- |
| Fast/Cheap | Classification, boilerplate, narrow edits             | Complex reasoning, architecture decisions |
| Balanced   | Implementation, refactors, multi-file work            | Root-cause analysis, subtle invariants    |
| Strong     | Architecture, root-cause analysis, complex invariants | Simple tasks (wasteful)                   |

Escalate tier only when a lower tier fails with a clear reasoning gap.

### High-Fidelity Handoffs

A handoff transfers intent and pointers to durable artifacts. The next agent initializes state from them.

- **Intent First**: Capture the "Why" and the user constraints.
- **Artifact Trail**: Pass absolute pointers to durable artifacts.
- **Zero Duplication**: Reference technical decisions, file lists, and test results through their artifacts.
- **Suggested Skills**: Name the next directive and the skills to invoke.

### Deterministic Script Packing

Plain shell steps that the model rewrites each time add variance. Tighten by packing.

- **Pack plain steps into scripts**: Put repeated `git`, `wt`, `gh`, and `npm` lines into `scripts/`. Use shell for file work and Python for `json` checks. The guide calls `scripts/<name> <args>`. A step is done when the script exits `0`. Remove the replaced inline lines.
- **Use plain words**: Keep prompts as `branch, copy, merge, conflict, fix, test, check, file, folder`. Plain words travel reliably and keep the guide short.

## Sub-Skill Dispatch

Dispatch on a task match or an explicit `domain` argument. Infer the domain from the task.

Load `writing-for-agents` for any agent-consumed document, including `SKILL.md` and `AGENTS.md`. Do this even when the primary domain is `skill-authoring`.

- `skill-authoring` -- Use when you create, edit, or debug a skill (`$SKILL_DIR/subskills/skill-authoring/SKILL.md`).
- `subagent-engineering` -- Use when you design an agent or a delegation workflow (`$SKILL_DIR/subskills/subagent-engineering/SKILL.md`).
- `verification` -- Use when you decide how to prove a change works (`$SKILL_DIR/subskills/verification/SKILL.md`).
- `writing-for-agents` -- Use when you write any agent-consumed doc (`$SKILL_DIR/subskills/writing-for-agents/SKILL.md`).
- `writing-for-humans` -- Use when you write an issue, RFC, or proposal (`$SKILL_DIR/subskills/writing-for-humans/SKILL.md`).

Run `validate-deps.py lint` to check conventions. Run `validate-deps.py context-check` to check the load budget.
