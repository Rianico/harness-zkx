---
name: ai-engineering-expert
description: >-
  AI engineering methodology spine for LSZ harness — context-load, skill/agent design, writing for agents, testing, subagent-first execution. Use when designing skills, agents, rules, or agent docs (SKILL.md, AGENTS.md, CLAUDE.md). TRIGGER: skill design, writing for agents, context-load policy
arguments: domain
argument-hint: |-
  skill-authoring -- loads skill design methodology: taxonomy, frontmatter, descriptions, invocation classes, description budgets, progressive disclosure, rules-vs-skills boundary, platform sync, parent/sub-skill layout, and authoring checklists
  subagent-engineering -- loads subagent methodology: action space design, observation formats, error recovery, parallel execution, orchestration constraints, and agent frontmatter
  verification -- loads verification methodology: EDD, deterministic vs semantic verification, AI regression patterns, runtime trace fixtures, and eval-first loops
  writing -- loads agent-document writing: context pointers, hierarchy, disclosure, completion criteria, leading words, pruning; use when writing/editing SKILL.md, AGENTS.md, CLAUDE.md or any agent-consumed doc
  omitted -- loads only the core AI engineering philosophy and the sub-skill dispatch registry
metadata:
  manage: [skill-authoring, subagent-engineering, verification, writing]
---

# AI Engineering Expert

Core principles for building robust AI systems in the LSZ harness. This file holds the 20% that solves 80% of problems; deep methodology lives in subskills and their references.

## The Foundation: GDD (Goal-Driven Development)

The ultimate goal of AI Engineering is to achieve **Human Goals**. Because LLMs are fundamentally **Probabilistic Machines** trying to operate in a **Deterministic World**, we use **GDD** to bridge this gap through three non-negotiable pillars:

1. **BDD (Behavior-Driven Development) for Intent Alignment:** We bridge the Intent-Code gap by forcing a **Shared Contract**. BDD (Given/When/Then scenarios) transforms a creative guessing task into a structured translation task.
2. **EDD (Eval-Driven Development) for Empirical Truth:** We never trust what the model *says* it did; we only trust what the *environment says* it did. **Environmental Truth is the Supreme Authority.**
3. **Semantic vs. Deterministic Split:** Hard reality and qualitative alignment are distinct domains. Deterministic work is measured by non-LLM tools (compilers, linters, property tests). Semantic work is verified by Adversarial Orchestration (a "Skeptic" agent).

## Information Boundary Design

- Tool owns what it can deterministically verify; model owns intent. Never require the model to supply verification data or to re-read just to keep a check honest.
- Expose minimal anchors/handles for the model to reference; hide verbose content and persistence details behind the tool. The model copies the handle, the tool resolves and verifies.
- Grade the boundary by determinism: hard checks (content, type, existence) → tool; qualitative choices (what to change, wording) → model.

> Reference: [Information boundary pattern](references/information-boundary.md)

---

## Core Mental Model

AI system quality is constrained by eight factors:

1. **Action space quality** -- Can the agent express the right operations?
2. **Observation quality** -- Does the agent see what it needs to decide?
3. **Recovery quality** -- Can the agent handle errors gracefully?
4. **Tool feedback quality** -- Are automated signals (LSP, linters, compilers) treated as authoritative blockers?
5. **Context budget quality** -- Is guidance loaded when needed, not before? Are descriptions within budget and invocation classes declared correctly?
6. **Artifact hygiene** -- Are files organized, deduplicated, and free of bloat?
7. **Subagent-first execution** -- Is all implementation work delegated to subagents?
8. **Handoff quality** -- Is state captured such that a fresh agent can resume with full fidelity?

---

## Expert Role Placement

When assigning a specialist role (architect, TDD expert, refactoring expert, etc.), place it according to scope rather than stuffing it into one layer.

| Layer | Scope | What Goes Here |
|-------|-------|----------------|
| **Agents** | Stable baseline identity | Short, durable role framing that applies in nearly every use of that agent |
| **Skills** | Deep reusable methodology | Checklists, heuristics, trade-off frameworks, discipline-specific guidance |
| **Orchestration / Workflows** | Workflow-specific overlay | Phase-local emphasis, suppressions, artifact-specific instructions |
| **Rules** | Lightweight cross-cutting constraints | Conventions, tool preferences, artifact locations, global guardrails |

**Default decision rule:**
- Almost everywhere for that agent → agent definition
- Deep and reusable across workflows → skill
- Specific to one workflow, phase, or artifact contract → orchestration skill
- Broad repository-wide constraint → rules

### Examples

- `developer` agent in TDD: keep agent generic; load `tdd-expert` skill for methodology; inject scope boundaries in the TDD workflow prompt
- `onboarding` agent: load `onboarding` skill for codebase-specific context
- `code-reviewer` agent: keep it generally reusable; inject "do not replay TDD verification" only in the code-review workflow

---

## 80/20 Principle

The 20% of knowledge that solves 80% of problems lives in SKILL.md files. The deep 80% lives in reference files behind context pointers. This applies recursively at every level -- parent spine, subskills, and subskill references.

Every line in a SKILL.md earns its place by passing the test: does this solve 80% of problems? If it's deep methodology, edge-case patterns, or platform-specific detail, disclose it behind a pointer. If the pointer fires unreliably on must-have material, sharpen its wording first; pull it inline only if that fails.

---

## Context-Load Policy

Context load is a first-class architectural constraint. Every skill's `description` sits in the initial skill-list metadata on every turn, spending tokens and attention regardless of invocation class.

### Invocation Classes

Every skill declares one of two classes via the canonical `disable-model-invocation` field:

| Declaration | Class | Behavior |
|-------------|-------|-----------|
| Omit (default `false`) | `implicit-allowed` | Model can invoke autonomously; description triggers discovery |
| `disable-model-invocation: true` | `explicit-only` | Only user or `$skill` can invoke |

**Selection ≠ metadata cost.** The `description` is always present in the initial skill list -- invocation class only controls *selection*, not *presence*. Explicit-only is not zero-load.

### Description Budget

- Description must be present and non-empty
- Maximum 300 characters
- Should contain trigger vocabulary ("use when", "when the user", "trigger")

### Platform Sync

Claude Code `SKILL.md` is the canonical format. Scripts generate platform-specific artifacts:

`SKILL.md` (canonical) → `validate-deps.py sync` → `agents/openai.yaml` (generated)

| Canonical field | Generated field |
|----------------|-----------------|
| `name` | `interface.display_name` |
| `description` | `interface.short_description` |
| `disable-model-invocation: true` | `policy.allow_implicit_invocation: false` |
| `disable-model-invocation: false` | `policy.allow_implicit_invocation: true` |

Sync always regenerates output from canonical source. No drift detection needed.

### Enforcement

`validate-deps.py context-check` enforces hard gates (fail CI) and soft warnings (pass CI):
- Missing/empty description → hard fail
- Description over 300 chars → hard fail
- No trigger vocabulary → soft warning

Semantic quality rules (third-person voice, front-loaded leading word, deduplication) are enforced by `skill-authoring` methodology during authoring, not by CI.

Reference: [Context-load policy contract](references/context-load-policy.md)

---

## Model Routing

| Model Tier | Use For | Avoid |
|------------|---------|-------|
| Fast/Cheap | Classification, boilerplate, narrow edits | Complex reasoning, architecture decisions |
| Balanced | Implementation, refactors, multi-file work | Root-cause analysis, subtle invariants |
| Strong | Architecture, root-cause analysis, complex invariants | Simple tasks (wasteful) |

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

**The Handoff is the Mission Bridge.** In complex multi-agent systems or long-running tasks, the handoff document distills Goals, Reasoning, and Intent from a sprawling session into a single source of truth.

| Requirement | Description |
|-------------|-------------|
| **Intent First** | Preserve the "Why" and the "Goal" over just the "What" |
| **Artifact Trail** | Absolute pointers to all durable artifacts (Design, ADRs, Code, Evals) |
| **Success Criteria** | Define exactly what "done" looks like for the next agent |
| **Context Recovery** | The next phase starts by reading the handoff to initialize state |

### Subagent Response Contract

Every subagent MUST return a structured response:

| Field | Purpose |
|-------|---------|
| **Summary** | Concise bullet list of work completed |
| **Artifact Pointers** | Absolute file paths to generated plans, code, or reviews |
| **Route/Status** | Explicit signal: `COMPLETED`, `REJECTED`, `BLOCKED` |
| **Issues** | List of discovered risks or required follow-ups |

### Pointer Continuity

Use the handoff document as the index for durable artifacts (`design.md`, `lineage.md`, etc.). Subsequent agents start by reading the handoff to initialize state, displacing (ignoring) the original full conversation history.

### Anti-Patterns

- **History Hoarding** -- Expecting the next agent to re-read the entire chat history
- **Embedded Bloat** -- Pasting 500-line specs into the handoff instead of passing pointers
- **Prose-Only Handoff** -- Vague summaries without concrete artifact trails or success criteria

---

## Subagent-First Execution

**The orchestrator never does implementation work.** All code writing, file editing, test execution, doc updates, and review work happens in subagents.

| Orchestrator DOES | Orchestrator NEVER DOES |
|-------------------|------------------------|
| Route tasks to appropriate subagents | Write code directly |
| Dispatch with structured prompts | Edit files directly |
| Monitor for completion/failure | Run tests directly |
| Receive and synthesize summaries | Read full artifact contents into context |
| Pass pointers between phases | Re-process subagent outputs |

### Dispatch Pattern

Always use structured dispatch templates. Every dispatch MUST specify the expected response format.

```markdown
Agent tool (<subagent_type>):
  description: "<short task summary>"
  prompt: |
    <context and requirements>
    <execution instructions>

    Return format per rules/templates/resp-format.md:
    ## Summary
    ## Artifacts
    ## Route (if applicable)
```

### Pointer-Based State Passing

Subagents exchange state through **file paths**, not content. The orchestrator passes pointers; subagents read/write artifacts at those paths. Preserves orchestrator context budget and supports large artifacts.

### Anti-Patterns

- **Hero mode orchestrator** -- "Let me just write this quick fix directly"
- **Context hoarding** -- Reading full artifact contents instead of dispatching a subagent
- **Sequential when parallel is possible** -- Running review agents one after another instead of concurrently
- **Unstructured subagent output** -- Prose without Summary/Artifacts/Route fields

Reference: [Subagent-first execution](references/subagent-first-execution.md)

---

## Artifact Hygiene

Every modification must preserve or improve organization. Additive changes without consolidation create bloat; scattered knowledge creates discovery failures.

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
- **Hero-Mode Prevention** -- Generic agents are prone to ignoring delegation instructions. Orchestration skills and complex workflow skills that dispatch agents SHOULD use explicit execution schemas with stable Agent dispatch templates to force the model into orchestration mode.
- **Tooling Preference** -- When using shell-based search, prefer `rg` for content search and `fd` for file discovery over `grep`, `find`, and agent built-in search tools. Reserve `ls` and `tree` for structural inspection.

---

## Skill Refinement Pattern
When workflow steps are plain shell that the model rewrites each time, they add variance. Tighten by packing.
- **Pack plain steps into scripts.** Put repeated `git`, `wt`, `gh`, `npm` lines into `scripts/` — shell for file and branch work, Python for checks that read `json`. The guide then calls `scripts/<name> <args>`. The guide is the router, scripts hold the steps. A step is done when the script exits `0`.
- **Fix inside the copy.** If a merge shows a conflict, the main flow does not edit files. A separate worker opens that copy's folder, checks `git status`, fixes each file (`git rm` for delete vs change, `git add` after), runs `npm run typecheck && npm test`, then `GIT_EDITOR=true git rebase --continue` and tries the merge again.
- **Use plain words.** Keep prompts as `branch, copy, merge, conflict, fix, test, check, file, folder`. Plain words travel reliably and keep the guide short.
Each fix must remove the inline lines it replaces. Otherwise the guide grows.



## Sub-Skill Dispatch

This skill manages four domain-specific sub-skills. Read the appropriate sub-skill based on the `domain` argument. When the task writes or edits any agent-consumed document (SKILL.md, AGENTS.md, CLAUDE.md, pointer docs), also load `writing` — even when primary domain is `skill-authoring`.

| Domain | Sub-Skill | Covers |
|--------|-----------|--------|
| `skill-authoring` | `$SKILL_DIR/subskills/skill-authoring/SKILL.md` | Skill design, descriptions, invocation classes, description budgets, platform sync, rules-vs-skills boundary, progressive disclosure, parent-skill pattern, authoring checklists |
| `subagent-engineering` | `$SKILL_DIR/subskills/subagent-engineering/SKILL.md` | Action space design, observation design, error recovery, parallel execution, orchestration constraints, agent frontmatter |
| `verification` | `$SKILL_DIR/subskills/verification/SKILL.md` | EDD, deterministic vs semantic verification, AI regression patterns, test-to-reprove, eval-first loop, runtime trace fixtures |
| `writing` | `$SKILL_DIR/subskills/writing/SKILL.md` | Agent-document writing — context pointers, hierarchy, progressive disclosure, completion criteria, leading words, pruning; use for any SKILL.md/AGENTS.md/CLAUDE.md or narrative rigor in skill-authoring |

**Dispatch:** When `$domain` is provided, read the matching sub-skill file and follow its instructions. When no domain is specified, only the philosophy above is loaded.
