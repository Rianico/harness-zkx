---
name: ai-engineering-expert
description: >-
  AI engineering philosophy and routing spine for the LSZ harness. Covers skill design principles, description budgets, invocation classes, context-load policy, agent action spaces, rules-vs-skills boundaries, eval-first testing, and model routing. Use when designing or refining skills/agents/rules/workflows; creating new skills; classifying skill type or granularity; setting invocation class, description budget, or platform-sync contracts; designing agent tool boundaries, observation formats, or context budgets; planning eval-first workflows, regression tests, or runtime trace fixtures; reducing skill/rule bloat; or deciding when to delegate to subagents.
arguments: domain
argument-hint: |
  skill-authoring -- loads skill design methodology: taxonomy, frontmatter, descriptions, invocation classes, description budgets, progressive disclosure, rules-vs-skills boundary, platform sync, parent/sub-skill layout, and authoring checklists
  agent-harness -- loads agent methodology: lean persona design, tool/action-space boundaries, observation formats, context budgeting, and error recovery contracts
  testing -- loads testing methodology: EDD, eval-first loops, model routing, AI regression tests, sandbox/production mismatch checks, runtime trace fixtures, and error-state leakage tests
  omitted -- loads only the core AI engineering philosophy and the sub-skill dispatch registry
metadata:
  manage: [skill-authoring, agent-harness, testing]
---

# AI Engineering Expert

Core principles for building robust AI systems in the LSZ harness. This file holds the 20% that solves 80% of problems; deep methodology lives in subskills and their references.

## The Foundation: GDD (Goal-Driven Development)

The ultimate goal of AI Engineering is to achieve **Human Goals**. Because LLMs are fundamentally **Probabilistic Machines** trying to operate in a **Deterministic World**, we use **GDD** to bridge this gap through three non-negotiable pillars:

1. **BDD (Behavior-Driven Development) for Intent Alignment:** We bridge the Intent-Code gap by forcing a **Shared Contract**. BDD (Given/When/Then scenarios) transforms a creative guessing task into a structured translation task.
2. **EDD (Eval-Driven Development) for Empirical Truth:** We never trust what the model *says* it did; we only trust what the *environment says* it did. **Environmental Truth is the Supreme Authority.**
3. **Semantic vs. Deterministic Split:** Hard reality and qualitative alignment are distinct domains. Deterministic work is measured by non-LLM tools (compilers, linters, property tests). Semantic work is verified by Adversarial Orchestration (a "Skeptic" agent).

---

## Core Mental Model

AI system quality is constrained by five factors:

1. **Action space quality** -- Can the agent express the right operations?
2. **Observation quality** -- Does the agent see what it needs to decide?
3. **Recovery quality** -- Can the agent handle errors gracefully?
4. **Context budget quality** -- Is guidance loaded when needed, not before? Are descriptions within budget and invocation classes declared correctly?
5. **Artifact hygiene** -- Are files organized, deduplicated, and free of bloat?
6. **Subagent-first execution** -- Is all implementation work delegated to subagents?
7. **Handoff quality** -- Is state captured such that a fresh agent can resume with full fidelity?

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

**Selection ≠ metadata cost.** The `description` is always present in the initial skill list -- invocation class only controls _selection_, not _presence_. Explicit-only is not zero-load.

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

**Gotchas:**
- Windows-style paths -- always use forward slashes
- Additive-only updates -- every new section should prompt "is there old content this replaces?"
- Copy-paste across skills -- reference the canonical source instead
- Size blindness -- check line counts periodically

---

## Sub-Skill Dispatch

This skill manages three domain-specific sub-skills. Read the appropriate sub-skill based on the `domain` argument.

| Domain | Sub-Skill | Covers |
|--------|-----------|--------|
| `skill-authoring` | `$SKILL_DIR/subskills/skill-authoring/SKILL.md` | Skill design, descriptions, invocation classes, description budgets, platform sync, rules-vs-skills boundary, progressive disclosure, parent-skill pattern, authoring checklists |
| `agent-harness` | `$SKILL_DIR/subskills/agent-harness/SKILL.md` | Action space design, observation design, error recovery, context budgeting |
| `testing` | `$SKILL_DIR/subskills/testing/SKILL.md` | EDD, eval-first loops, model routing, AI regression tests, runtime trace fixtures, sandbox mismatch |

**Dispatch:** When `$domain` is provided, read the matching sub-skill file and follow its instructions. When no domain is specified, only the philosophy above is loaded.
