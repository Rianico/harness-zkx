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

The ultimate purpose of AI Engineering is to translate **Human Intent** into verifiable reality. LLMs are fundamentally **Probabilistic Engines** operating within a **Deterministic World**. We bridge this gap by establishing **IDD** as the upstream teleological root and **GDD** as the derived operational spine:

### 1. IDD (Intent-Driven Development): Source of Authority
Answers *"Why are we changing reality?"* Intent anchors teleological purpose and boundary invariants before any code or goals are authored. It is defined by the **4-part Intent Formula**:
- **Problem**: Concrete deficiency, friction, or behavioral regression in the current world state.
- **Proposed Outcome**: Observable change in behavior, capability, or invariant once resolved.
- **Affected Seams**: Architectural boundaries, module interfaces, or protocols touched.
- **Non-Negotiable Constraints**: Invariants, backwards compatibility, performance ceilings, or forbidden patterns.

### 2. GDD (Goal-Driven Development): Derived Operational Spine
Derives verifiable milestone world states and operational targets from Intent. Answers *"What world state confirms the intent was realized?"*

### 3. The Derivation Chain
$$\text{Intent (IDD)} \longrightarrow \text{Derived Goals (GDD)} \longrightarrow \text{BDD Contracts (Given/When/Then)} \longrightarrow \text{EDD Verification (Environmental Truth)}$$

1. **Intent (IDD)** establishes the human purpose and boundary invariants.
2. **Derived Goals (GDD)** operationalize intent into discrete, ordered milestone states.
3. **BDD Contracts** define behavioral specifications via Given/When/Then acceptance criteria.
4. **EDD Verification** executes deterministic environment checks (`test`, `lint`, `typecheck`) to prove environmental truth.

### 4. Why Both Are Strictly Required
- **Goal without Intent causes Specification Gaming (Goodhart's Law)**: An agent given a goal without understanding the underlying intent optimizes for the metric or test directly (e.g. mock tautologies, stubbing out checks, deleting assertions, or breaking cross-cutting invariants) while defeating the human purpose.
- **Intent without Goal causes Semantic Drift & Unbounded Refactors**: An agent given pure intent without crisp milestone goals and verification gates wanders aimlessly, refactoring unrelated files, over-engineering architectures, and never converging on verifiable completion.

### 5. Execution Pillars
1. **BDD (Behavior-Driven Development) for Intent Alignment:** We bridge the Intent-Code gap by forcing a **Shared Contract**. BDD (Given/When/Then scenarios) transforms a creative guessing task into a structured translation task.
2. **EDD (Eval-Driven Development) for Empirical Truth:** We never trust what the model _says_ it did. We only trust what the _environment says_ it did. **Environmental Truth is the Supreme Authority.**
3. **Semantic vs. Deterministic Split:** Hard reality and qualitative alignment are distinct domains. Default to building checks over writing rules. When an agent fails, classify root cause into four distinct archetypes:
   - **Mechanical Violation** (syntax, argument types, banned APIs, file paths, dump sizes) → deterministic tools (compilers, linters, property tests, pre-commit hooks). Never patch via prose.
   - **Semantic Ambiguity** (model interpreted guidance plausibly but diverged from intent) → refine prompt contracts (tripartite formula, negative boundary, concrete input/output specs, STE-100 terminology).
   - **Semantic Disregard / No-Op** (rule is clear, model ignored it under context pressure) → enforce via Context Pressure Asymmetry (move to Skeptic reviewer) or build a hard tool gate. Prune ignored prose.
   - **Route Friction** (model bypassed rule because compliance was too manual or multi-step) → pack steps into a script (`scripts/<cmd>`). Make the governed path the cheapest path.
4. **Unified Message Format:** All inter-agent dispatches and completion replies adhere to an isomorphic dual-mode contract (Markdown prose and structured JSON schema) covering Summary (Carmack-style), Artifacts, Evidence, Route, and Issues. (See [Subagent Response Format](references/resp-format.md) and [Lane Coordination](../herdr/references/lane-coordination.md)).

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

- **Root steering files (`AGENTS.md`, `CLAUDE.md`):** Keep minimal. Use strictly for **navigation pointers**, never inline specs.
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

Origin: Claude Code `disable-model-invocation`. Pi ≥0.84.4 advances this design. `formatSkillsForPrompt` filters `disableModelInvocation=true` skills. It **removes them from the `<available_skills>` XML** injected into the system prompt, paying **zero context/metadata cost**. Claude's original gating is selection-only (description stays listed, model instructed not to pick it). Pi strips it from context entirely — no description, no tokens, no attention. It is reachable only via explicit `/skill:name`.

### Description Principles & Budget

Every skill's `description` is its top-level machine-readable trigger and permanent context-load footprint. Grounded in empirical function-calling benchmarks, descriptions reject pseudo-syntax annotations (`TRIGGER:`). They use natural language conditionals and symptom hooks within a strict 300-character budget:

1. **What it is (Role/Identity Anchor):** Category noun defining nature and domain (e.g., *Methodology spine...*, *Verification gate...*, *CLI reference...*). Front-load in first 50 chars.
2. **What it does (Active Capabilities & Outputs):** Third-person present tense verbs defining concrete operations and deliverables (e.g., *audits test refutability and invariants...*, *synthesizes multi-stack test runners...*).
3. **When to use (Activation Boundary via `Use when...`):** **Required.** Explicit condition starting with `Use when...` (or `when the user...`). Benchmarks show natural language conditionals activate model routing policy heads far more reliably than passive topic summaries.
4. **Symptom Keywords Standard:** **Fundamental standard.** Users describe problems and symptoms, not solutions. Must include concrete failure states, bug indicators, debugging signals, and pain phrases (e.g., *flaky tests*, *drift*, *messy code*, *memory leak*, *crash*, *slow*).
5. **Negative Boundary:** **Opt-in.** Clause specifying when NOT to use the skill (e.g., *Do not use for unit testing -- defer to Y for Z*). Proven highest-leverage lever to eliminate false-positive collisions between adjacent skills.

**Enforcement Rules:**
- Must be present, non-empty, and written with YAML block scalar `>-`
- Maximum 300 characters (hard gate)
- Must contain explicit `Use when...` clause (contract check)
- Strict third-person perspective (never first/second person: "I can...", "You can...")
- No legacy `TRIGGER:` tags (script flags as deprecated)

### Platform Sync

Claude Code `SKILL.md` is the canonical format. Scripts generate platform-specific artifacts. Pi handles the field natively at prompt build:

`SKILL.md` (canonical) → `validate-deps.py sync` → `agents/openai.yaml` (generated) · Pi ≥0.84.4 `formatSkillsForPrompt` → strip from `<available_skills>` XML

| Canonical field                                                                  | Generated field (OpenAI)                  | Pi ≥0.84.4 runtime                            |
| -------------------------------------------------------------------------------- | ----------------------------------------- | --------------------------------------------- |
| `name`                                                                           | `interface.display_name`                  | `<name>` in `<available_skills>` when visible |
| `description`                                                                    | `interface.short_description`             | `<description>` when visible                  |
| `disable-model-invocation: true`                                                 | `policy.allow_implicit_invocation: false` | **Removed from XML** — zero-load              |
| `disable-model-invocation: false`                                                | `policy.allow_implicit_invocation: true`  | Listed in XML — normal load                   |
| Sync always regenerates output from canonical source. No drift detection needed. |

### Enforcement

`validate-deps.py context-check` deterministically enforces:

- **Hard Gates (fail CI):** Missing/empty description, or description over 300 chars.
- **Contract Warnings (pass CI, flagged for remediation):**
  - Missing required `Use when...` trigger clause.
  - Missing symptom keywords / problem-framing signals.
  - Presence of deprecated `TRIGGER:` tags.
- **Opt-in Detection:** Records presence of negative boundary clauses (`Do not use for...`, `defer to...`).

Semantic quality rules (tripartite structure, third-person voice, front-loaded leading words, deduplication) are enforced by `skill-authoring` methodology during authoring.

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

Every subagent MUST return a structured response:

| Field                 | Purpose                                                  |
| --------------------- | -------------------------------------------------------- |
| **Summary**           | Concise bullet list of work completed                    |
| **Artifact Pointers** | Absolute file paths to generated plans, code, or reviews |
| **Route/Status**      | Explicit signal: `COMPLETED`, `REJECTED`, `BLOCKED`      |
| **Issues**            | List of discovered risks or required follow-ups          |

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

| Primary Agent DOES                   | Primary Agent NEVER DOES                 |
| ------------------------------------ | ---------------------------------------- |
| Route tasks to appropriate subagents | Write code directly in orchestrator role |
| Dispatch with structured prompts     | Edit files directly without scoping      |
| Monitor for completion/failure       | Run verbose tests directly in host pane  |
| Receive and synthesize summaries     | Read full artifact contents into context |
| Pass pointers between phases         | Re-process raw subagent observation logs |

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
    ## Route (if applicable)
```

### Pointer-Based State Passing

Subagents exchange state through **file paths**, not content. The orchestrator passes pointers. Subagents read and write artifacts at those paths. Preserves orchestrator context budget and supports large artifacts.

### Anti-Patterns

- **Hero mode orchestrator** -- "Let me just write this quick fix directly"
- **Context hoarding** -- Reading full artifact contents instead of dispatching a subagent
- **Sequential when parallel is possible** -- Running review agents one after another instead of concurrently
- **Unstructured subagent output** -- Prose without Summary/Artifacts/Route fields

Reference: [Subagent-first execution](references/subagent-first-execution.md)

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

- **Pack plain steps into scripts**. Put repeated `git`, `wt`, `gh`, `npm` lines into `scripts/`. Use shell for file and branch work. Use Python for checks that read `json`. The guide then calls `scripts/<name> <args>`. The guide is the router, scripts hold the steps. A step is done when the script exits `0`.
- **Fix inside the copy**. If a merge shows a conflict, the main flow does not edit files. A separate worker opens that copy's folder and checks `git status`. The worker fixes each file (`git rm` for delete vs change, `git add` after). It runs `npm run typecheck && npm test`, executes `GIT_EDITOR=true git rebase --continue`, and retries the merge.
- **Use plain words.** Keep prompts as `branch, copy, merge, conflict, fix, test, check, file, folder`. Plain words travel reliably and keep the guide short.
  Each fix must remove the inline lines it replaces. Otherwise the guide grows.

## Sub-Skill Dispatch

This skill manages five domain-specific sub-skills. Read the appropriate sub-skill based on the `domain` argument. When the task writes or edits any agent-consumed document (SKILL.md, AGENTS.md, CLAUDE.md, pointer docs), also load `writing-for-agents` — even when primary domain is `skill-authoring`.

| Domain                 | Sub-Skill                                            | Covers                                                                                                                                                                                                    |
| ---------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `skill-authoring`      | `$SKILL_DIR/subskills/skill-authoring/SKILL.md`      | Skill design, descriptions, invocation classes, description budgets, platform sync, rules-vs-skills boundary, progressive disclosure, parent-skill pattern, authoring checklists                          |
| `subagent-engineering` | `$SKILL_DIR/subskills/subagent-engineering/SKILL.md` | Action space design, observation design, error recovery, parallel execution, orchestration constraints, agent frontmatter                                                                                 |
| `verification`         | `$SKILL_DIR/subskills/verification/SKILL.md`         | EDD, deterministic vs semantic verification, AI regression patterns, test-to-reprove, eval-first loop, runtime trace fixtures                                                                             |
| `writing-for-agents`   | `$SKILL_DIR/subskills/writing-for-agents/SKILL.md`   | Agent-document writing — context pointers, hierarchy, progressive disclosure, completion criteria, leading words, pruning; use for any SKILL.md/AGENTS.md/CLAUDE.md or narrative rigor in skill-authoring |
| `writing-for-humans`   | `$SKILL_DIR/subskills/writing-for-humans/SKILL.md`   | Human-facing proposal writing — problem-first framing, evidence grounding, scannability, explicit asks, non-goals; use for GitHub issues, RFCs, and proposals a maintainer triages |

**Dispatch:** When `$domain` is provided, read the matching sub-skill file and follow its instructions. When no domain is specified, only the philosophy above is loaded.
