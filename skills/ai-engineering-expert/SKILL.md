---
name: ai-engineering-expert
description: >-
  AI engineering methodology spine for LSZ harness — context-load, skill/agent design, writing for agents, testing, subagent-first execution. Use when designing skills, agents, rules, or agent docs (SKILL.md, AGENTS.md, CLAUDE.md), or diagnosing context bloat or skill discovery failures.
arguments: domain
argument-hint: |-
  skill-authoring -- loads skill design and diagnosis methodology: taxonomy, frontmatter, descriptions, invocation classes, description budgets, trigger diagnosis, progressive disclosure, rules-vs-skills boundary, platform sync, and authoring checklists
  subagent-engineering -- loads subagent methodology: action space design, observation formats, error recovery, parallel execution, orchestration constraints, and agent frontmatter
  verification -- loads verification methodology: EDD, deterministic vs semantic verification, AI regression patterns, runtime trace fixtures, and eval-first loops
  writing-for-agents -- loads agent-document writing: context pointers, hierarchy, disclosure, completion criteria, leading words, pruning; use when writing/editing SKILL.md, AGENTS.md, CLAUDE.md or any agent-consumed doc
  writing-for-humans -- loads human-facing proposal writing: problem-first framing, evidence grounding, scannability, explicit asks; use when drafting/reviewing GitHub issues, RFCs, or proposals
  omitted -- loads only the core AI engineering philosophy and the sub-skill dispatch registry
metadata:
  manage: [skill-authoring, subagent-engineering, verification, writing-for-agents, writing-for-humans]
---

# AI Engineering Expert

Core principles for building reliable AI systems in the LSZ harness. This file holds the 20% that solves 80% of problems. Deep methodology lives in subskills and their references.

## The Foundation: IDD (Intent-Driven Development) & GDD (Goal-Driven Development)

AI engineering translates **Human Intent** into verifiable reality. LLMs are **Probabilistic Engines** operating in a **Deterministic World**. **IDD** is the upstream source of authority; **GDD** is the derived operational spine.

### 1. IDD (Intent-Driven Development): Source of Authority
Answers *"Why are we changing reality?"* Anchors teleological purpose and boundary invariants before any code or goals are authored. Defined by the **4-part Intent Formula**:
- **Problem**: Concrete deficiency, friction, or behavioral regression in the current world state.
- **Proposed Outcome**: Observable change in behavior, capability, or invariant once resolved.
- **Affected Seams**: Architectural boundaries, module interfaces, or protocols touched.
- **Non-Negotiable Constraints**: Invariants, backwards compatibility, performance ceilings, or forbidden patterns.

### 2. GDD (Goal-Driven Development): Derived Operational Spine
Derives verifiable milestone world states from Intent. Answers *"What world state confirms the intent was realized?"*

### 3. The Derivation Chain
1. **Intent (IDD)** establishes the human purpose and boundary invariants.
2. **Derived Goals (GDD)** operationalize intent into discrete, ordered milestone states.
3. **BDD Contracts** define behavior via Given/When/Then acceptance criteria — the shared contract that turns a creative guessing task into a structured translation task.
4. **EDD Verification** executes deterministic environment checks (`test`, `lint`, `typecheck`). We never trust what the model _says_ it did, only what the _environment says_ it did. **Environmental Truth is the Supreme Authority.**

Both ends are strictly required. A goal without intent invites **Specification Gaming** (Goodhart's Law): the agent optimizes the metric or test directly — mock tautologies, stubbed checks, deleted assertions, broken cross-cutting invariants — and defeats the human purpose. Intent without goal invites **Semantic Drift**: unbounded refactors of unrelated files that never converge on verifiable completion.

### 4. Root-Cause Archetypes for Agent Failure
Hard reality and qualitative alignment are distinct domains. Default to building checks over writing rules. When an agent fails, classify the root cause:

- **Mechanical Violation** (syntax, argument types, banned APIs, file paths, dump sizes) → deterministic tools (compilers, linters, property tests, pre-commit hooks). Never patch via prose.
- **Semantic Ambiguity** (model interpreted guidance plausibly but diverged from intent) → refine prompt contracts (tripartite formula, negative boundary, concrete input/output specs, STE-100 terminology).
- **Semantic Disregard / No-Op** (rule is clear, model ignored it under context pressure) → enforce via Context Pressure Asymmetry (move to Skeptic reviewer) or build a hard tool gate. Prune ignored prose.
- **Route Friction** (model bypassed rule because compliance was too manual or multi-step) → pack steps into a script (`scripts/<cmd>`). Make the governed path the cheapest path.

### 5. Unified Message Format
All inter-agent dispatches and completion replies adhere to an isomorphic dual-mode contract (Markdown prose and structured JSON schema) covering Summary (Carmack-style), Artifacts, Evidence, Route, and Issues. (See [Subagent Response Format](references/resp-format.md) and [Lane Coordination](../herdr/references/lane-coordination.md)).

## Information Boundary Design

- Tool owns what it can deterministically verify. Model owns intent. Never require the model to supply verification data or to re-read just to keep a check honest.
- Expose minimal anchors/handles for the model to reference. Hide verbose content and persistence details behind the tool. The model copies the handle, the tool resolves and verifies.
- Grade the boundary by determinism: hard checks (content, type, existence) go to the tool. Qualitative choices (what to change, wording) go to the model.

> Reference: [Information boundary pattern](references/information-boundary.md)

---

## Core Mental Model

AI system quality is constrained by nine factors:

1. **Action space quality** -- Can the agent express the right operations?
2. **Observation access** -- Does the agent see what it needs? Deliver runtime truth passively (tee server logs/pipes) rather than forcing blind query loops.
3. **Recovery quality** -- Can the agent handle errors gracefully?
4. **Tool feedback quality** -- Are automated signals (LSP, linters, compilers) treated as authoritative blockers?
5. **Tool economy** -- Are tool/MCP outputs streamlined to prevent token-bloated payloads?
6. **Context budget quality** -- Is guidance loaded when needed, not before? Are descriptions within budget and invocation classes declared correctly?
7. **Artifact hygiene** -- Are files organized, deduplicated, and free of bloat?
8. **Subagent-first execution** -- Is all implementation work delegated to subagents?
9. **Handoff quality** -- Is state captured such that a fresh agent can resume with full fidelity?

---

## Expert Role Placement

When assigning a specialist role (architect, TDD expert, refactoring expert, etc.), place it according to scope rather than stuffing it into one layer.

| Layer                         | Scope                                 | What Goes Here                                                             |
| ----------------------------- | ------------------------------------- | -------------------------------------------------------------------------- |
| **Agents**                    | Stable baseline identity              | Short, durable role framing that applies in nearly every use of that agent |
| **Skills**                    | Deep reusable methodology             | Checklists, heuristics, trade-off frameworks, discipline-specific guidance |
| **Orchestration / Workflows** | Workflow-specific overlay             | Phase-local emphasis, suppressions, artifact-specific instructions         |
| **Rules**                     | Lightweight cross-cutting constraints | Conventions, tool preferences, artifact locations, global guardrails       |

### Context Pressure Asymmetry

All work splits into implementation and review:
- **Implementer**: Max context pressure (exploration, drafting, debug loops). Keep free of style/standards overhead.
- **Reviewer**: Min context pressure (receives diff only, zero exploration). Place coding standards and qualitative checks here, not in implementation prompts.

**Default decision rule:**

- Almost everywhere for that agent → agent definition
- Deep and reusable across workflows → skill
- Specific to one workflow, phase, or artifact contract → orchestration skill
- Broad repository-wide constraint → rules

### Examples

- `developer` agent in TDD: keep the agent generic. Load the `tdd-expert` skill for methodology. Inject scope boundaries in the TDD workflow prompt.
- `onboarding` agent: load `onboarding` skill for codebase-specific context
- `code-reviewer` agent: keep it generally reusable. Inject "do not replay TDD verification" only in the code-review workflow

---

## 80/20 Principle

The 20% of knowledge that solves 80% of problems lives in SKILL.md files. The deep 80% lives in reference files behind context pointers. This applies recursively at every level -- parent spine, subskills, and subskill references.

Every line in a SKILL.md earns its place by passing the test: does this solve 80% of problems? If it's deep methodology, edge-case patterns, or platform-specific detail, disclose it behind a pointer. If the pointer fires unreliably on must-have material, sharpen its wording first. Pull it inline only if that fails.

- **Root steering file: `AGENTS.md`** — the open standard ([agents.md](https://agents.md); closest file wins, nested files supported). `CLAUDE.md` and other agent variants are compatibility mirrors. Keep minimal: strictly **navigation pointers**, never inline specs.
- **Prune No-Ops:** Aggressively delete steering instructions that don't measurably alter agent decisions.

---

## Context-Load Policy

Context load is a first-class architectural constraint. Every skill's `description` sits in the initial skill-list metadata on every turn, spending tokens and attention regardless of invocation class.

### Invocation Classes

Every skill declares one of two classes via the canonical `disable-model-invocation` field:

| Declaration                      | Class              | Behavior                                                                                       |
| -------------------------------- | ------------------ | ---------------------------------------------------------------------------------------------- |
| Omit (default `false`)           | `implicit-allowed` | Model can invoke autonomously; description triggers discovery                                  |
| `disable-model-invocation: true` | `explicit-only`    | Only user or `$skill` can invoke; on Pi omitted from `<available_skills>` XML (true zero-load) |

Base standard: the open Agent Skills spec ([agentskills.io](https://agentskills.io)). `disable-model-invocation` is an enhancement beyond the spec, shared by Claude Code and Pi; Pi's semantics are the default — `formatSkillsForPrompt` strips flagged skills from the system-prompt XML entirely: no description, no tokens, no attention, reachable only via `/skill:name`. Claude's gating is selection-only (description stays listed). So on Pi, `explicit-only` is the correct way to remove a skill from model context — never add a pointer to it from an always-loaded doc.

### Description Budget

Every description is a machine-readable trigger and a permanent context-load footprint within a **300-character hard gate**. Follow the tripartite formula — what it is (front-loaded in the first 50 chars), what it does (third-person verbs), when to use (**required** `Use when...` clause) — plus symptom keywords (fundamental standard: users report *flaky tests*, *drift*, *crash*, not solutions), an opt-in negative boundary for adjacent-skill collisions, and no `TRIGGER:` pseudo-syntax. `validate-deps.py context-check` enforces the hard gates and warns on contract misses; semantic quality is enforced by `skill-authoring` methodology.

Canonical `SKILL.md` frontmatter is the single source: `validate-deps.py sync` regenerates `agents/openai.yaml`, and Pi applies invocation-class filtering at prompt build.

Reference: [Context-load policy contract](references/context-load-policy.md)

---

## Model Routing

| Model Tier | Use For                                               | Avoid                                     |
| ---------- | ----------------------------------------------------- | ----------------------------------------- |
| Fast/Cheap | Classification, boilerplate, narrow edits             | Complex reasoning, architecture decisions |
| Balanced   | Implementation, refactors, multi-file work            | Root-cause analysis, subtle invariants    |
| Strong     | Architecture, root-cause analysis, complex invariants | Simple tasks (wasteful)                   |

Escalate tier only when lower tier fails with a clear reasoning gap.

---

## Skill Infrastructure

The canonical tool for skill management is in the `skill-authoring` sub-skill.

```bash
# Validate all skill dependencies
uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py check

# Check inbound/outbound dependencies for a skill
uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py related <skill_name>

# Lint all skills for quality and conventions
uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py lint

# Generate platform-specific artifacts from canonical metadata
uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py sync

# Enforce context-load policy (hard gates + soft warnings)
uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py context-check
```

---

## High-Fidelity Handoffs

**The Handoff is the Mission Bridge**. Multi-agent systems and long-running tasks require reliable handoffs. The handoff document distills Goals, Reasoning, and Intent from a sprawling session into a single source of truth.

| Requirement          | Description                                                            |
| -------------------- | ---------------------------------------------------------------------- |
| **Intent First**     | Preserve the "Why" and the "Goal" over just the "What"                 |
| **Artifact Trail**   | Absolute pointers to all durable artifacts (Design, ADRs, Code, Evals) |
| **Success Criteria** | Define exactly what "done" looks like for the next agent               |
| **Context Recovery** | The next phase starts by reading the handoff to initialize state       |

### Subagent Response Contract

Every subagent MUST return the canonical structured response ([resp-format.md](references/resp-format.md)):

| Field        | Purpose                                                        |
| ------------ | -------------------------------------------------------------- |
| **Summary**  | Approach and reasoning, ≤100 words — not a play-by-play log    |
| **Artifacts**| Absolute file paths to generated plans, code, or reviews       |
| **Evidence** | Deterministic check results (`name`: PASS/FAIL + command)      |
| **Route**    | `continue`, `remediate`, or `blocked`                          |
| **Issues**   | Discovered risks, each with severity, `file:line`, remediation |

### Pointer Continuity

Use the handoff document as the index for durable artifacts (`design.md`, `lineage.md`, etc.). Subsequent agents start by reading the handoff to initialize state, displacing (ignoring) the original full conversation history.

### Anti-Patterns

- **History Hoarding** -- Expecting the next agent to re-read the entire chat history
- **Embedded Bloat** -- Pasting 500-line specs into the handoff instead of passing pointers
- **Prose-Only Handoff** -- Vague summaries without concrete artifact trails or success criteria

---

## Subagent-First Execution

> [!IMPORTANT] Universal Mandate Across All Coding Agents
> Subagent-First Execution is a **Universal Mandate across all coding agents**, regardless of underlying engine (`pi`, `claude`, `agy`, `cursor`, `cline`, `codex`, `gemini`, etc.).
>
> Any coding agent handling tasks with high noise (e.g. broad codebase exploration, recursive symbol searches, multi-file bulk editing, verbose build/test traces, adversarial crux review) or where only the final conclusion/artifact is needed **MUST delegate to ephemeral subagents**. This guarantees:
> 1. **Context Isolation**: High-entropy intermediate output (hundreds of lines of file dumps, compile errors, stack traces) stays trapped in disposable subagent contexts.
> 2. **Parallel Execution**: Independent investigations or reviews execute concurrently across separate context budgets.
> 3. **Compaction Prevention**: The primary agent's working memory remains lean and focused, avoiding compaction degradation, instruction amnesia, and lost constraints.
>
> **The orchestrator never does implementation work**. Implementers never do heavy exploration, bulk refactoring, or verbose test triage directly in the host pane.

The primary agent routes, dispatches with structured prompts, monitors, synthesizes summaries, and passes pointers between phases. It never writes code, edits files, runs verbose tests in the host pane, or reads full artifact contents into context.

### Execution Profile Boundary
- **Heavy Mutation & Implementation**: Subagent-first is mandatory. Keeps primary agent context clean and isolates trial-and-error churn.
- **Diagnostic & Audit Pipelines**: Standalone retrospective audits (`harness-audit`) may run as in-process linear pipelines in scratch directories. Dispatch **mid-session diagnostics** (such as trigger failures) to a subagent with forked context. This prevents diagnostic meta-chatter from bloating the parent session's working memory.

### Dispatch Pattern

Always use structured dispatch templates. Every dispatch MUST specify the expected response format.

```markdown
Agent tool (<subagent_type>):
description: "<short task summary>"
prompt: |
<context and requirements>
<execution instructions>

    Return format per skills/ai-engineering-expert/references/resp-format.md:
    ## Summary
    ## Artifacts
    ## Evidence
    ## Route (if applicable)
    ## Issues
```

### Pointer-Based State Passing

Subagents exchange state through **file paths**, not content. The orchestrator passes pointers. Subagents read and write artifacts at those paths. Preserves orchestrator context budget and supports large artifacts.

Reference: [Subagent-first execution](references/subagent-first-execution.md) — full DOES/NEVER tables, dispatch examples, summary style, anti-patterns.

---

## Artifact Hygiene

Every modification must preserve or improve organization. Additive changes without consolidation create bloat. Scattered knowledge creates discovery failures.

**Before any update:** audit the target, identify redundancy, find the right home.

**During updates:** consolidate don't accumulate, one concept one location, reorganize when needed, group by topic.

**Red flags:** files over size limits, duplicated concepts, copy-pasted content, catch-all sections, unclear ordering.

**After every structural change** (renames, moves, metadata edits, dependency changes): run the deterministic gate. Binary pass/fail — no ambiguity.

```bash
uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py check  # dependency graph
uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py lint   # frontmatter conformance
```

**Gotchas:**

- Windows-style paths -- always use forward slashes
- Additive-only updates -- every new section should prompt "is there old content this replaces?"
- Copy-paste across skills -- reference the canonical source instead
- Size blindness -- check line counts periodically

---

## Trade-Offs

Design decisions the architecture makes intentionally:

- **Latency vs Context Efficiency** -- On-demand skill loading adds a small runtime penalty (model must call `Skill` tool to retrieve deep knowledge). This keeps the base context window focused on the user's immediate request. Load only what is needed for the current sub-task.
- **Hero-Mode Prevention** -- Generic agents are prone to ignoring delegation instructions. Skills that dispatch agents SHOULD use explicit execution schemas. Stable Agent dispatch templates force the model into orchestration mode.
- **Tooling Preference** -- For shell search, prefer `rg` for content search and `fd` for file discovery. Avoid `grep`, `find`, and built-in search tools. Reserve `ls` and `tree` for structural inspection.

---

## Skill Refinement Pattern

When workflow steps are plain shell that the model rewrites each time, they add variance. Tighten by packing.

- **Pack plain steps into scripts**. Put repeated `git`, `wt`, `gh`, `npm` lines into `scripts/`. Use shell for file and branch work. Use Python for checks that read `json`. The guide then calls `scripts/<name> <args>`. The guide is the router, scripts hold the steps. A step is done when the script exits `0`. Each packed fix removes the inline lines it replaces; otherwise the guide grows.
- **Use plain words.** Keep prompts as `branch, copy, merge, conflict, fix, test, check, file, folder`. Plain words travel reliably and keep the guide short.

## Sub-Skill Dispatch

This skill manages five domain-specific sub-skills. Dispatch on task-match OR explicit `domain` argument — never wait for the user to name the domain. When the task writes or edits any agent-consumed document (SKILL.md, AGENTS.md, CLAUDE.md, pointer docs), also load `writing-for-agents` — even when the primary domain is `skill-authoring`.

| Domain                 | Sub-Skill                                            | Covers                                                                                                                                                                                                    |
| ---------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `skill-authoring`      | `$SKILL_DIR/subskills/skill-authoring/SKILL.md`      | Skill design, descriptions, invocation classes, description budgets, platform sync, rules-vs-skills boundary, progressive disclosure, parent-skill pattern, authoring checklists                          |
| `subagent-engineering` | `$SKILL_DIR/subskills/subagent-engineering/SKILL.md` | Action space design, observation design, error recovery, parallel execution, orchestration constraints, agent frontmatter                                                                                 |
| `verification`         | `$SKILL_DIR/subskills/verification/SKILL.md`         | EDD, deterministic vs semantic verification, AI regression patterns, test-to-reprove, eval-first loop, runtime trace fixtures                                                                             |
| `writing-for-agents`   | `$SKILL_DIR/subskills/writing-for-agents/SKILL.md`   | Agent-document writing — context pointers, hierarchy, progressive disclosure, completion criteria, leading words, pruning; use for any SKILL.md/AGENTS.md/CLAUDE.md or narrative rigor in skill-authoring |
| `writing-for-humans`   | `$SKILL_DIR/subskills/writing-for-humans/SKILL.md`   | Human-facing proposal writing — problem-first framing, evidence grounding, scannability, explicit asks, non-goals; use for GitHub issues, RFCs, and proposals a maintainer triages |

**Dispatch:** Read the matching sub-skill file and follow its instructions. With no matching domain or task, only the philosophy above is loaded.
