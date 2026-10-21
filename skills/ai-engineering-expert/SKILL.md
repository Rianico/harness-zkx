---
name: ai-engineering-expert
description: >-
  AI engineering methodology spine for LSZ harness — context-load, skill authoring, agent design, agent-doc writing, testing, subagent-first execution. Use when creating or editing skills, agents, rules, or agent docs (SKILL.md, AGENTS.md, CLAUDE.md), or diagnosing context bloat or discovery failure.
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

## The Foundation: IDD & GDD

AI engineering turns human intent into verified artifacts. **IDD** owns intent. **GDD** derives goals from intent.

Two owners split the work:

- **Formal Substrate**: Compilers, linters, typecheckers, databases, and tests return pass/fail. It owns environmental truth. The model never supplies verification data and never echoes text to prove honesty.
- **Semantic Reasoner**: The model navigates ambiguity, resolves conflicts, and proposes integrations when the substrate reports an impasse.

> Reference: [Information boundary pattern](references/information-boundary.md)

### 1. IDD (Intent-Driven Development): Source of Authority

Answers *Why change reality?* Anchors purpose and boundary invariants before anyone writes code or goals. Defined by the **4-part Intent Formula**:

- **Problem**: Concrete deficiency, friction, or regression in the current state.
- **Proposed Outcome**: Observable change in behavior, capability, or invariant once resolved.
- **Affected Seams**: Architectural boundaries, module interfaces, or protocols touched.
- **Non-Negotiable Constraints**: Invariants, backward compatibility, performance ceilings, or forbidden patterns.

### 2. GDD (Goal-Driven Development): Derived Operational Spine

Derives verifiable milestone world states from intent. Answers *What world state confirms the intent was realized?*

### 3. The Derivation Chain

1. **Intent (IDD)**: Establishes human purpose and boundary invariants.
2. **Derived Goals (GDD)**: Converts intent into discrete, ordered milestone states.
3. **BDD Contracts**: Defines behavior as Given/When/Then acceptance criteria. Turns guessing into structured translation.
4. **EDD Verification**: Runs `test`, `lint`, and `typecheck`. Never trust what the model says it did. **Environmental Truth is the Supreme Authority.**

Both ends are mandatory:

- **Goal without intent** causes **Specification Gaming** (Goodhart's Law). The agent optimizes the metric itself: mock tautologies, stubbed checks, deleted assertions, broken cross-cutting invariants. It defeats the human purpose.
- **Intent without goal** causes **Semantic Drift**: unbounded refactors of unrelated files that never converge on verifiable completion.

### 4. Root-Cause Archetypes for Agent Failure

Build checks over writing rules. Classify each failure by cause:

- **Mechanical Violation** (syntax, argument types, banned APIs, file paths, dump sizes) → Add a deterministic tool to the Formal Substrate (compilers, linters, property tests, pre-commit hooks). Never patch via prose.
- **Semantic Ambiguity** (model interpreted guidance plausibly but diverged from intent) → Refine the prompt contract (tripartite formula, negative boundary, concrete input/output specs, STE-100 terminology).
- **Semantic Disregard / No-Op** (rule is clear, model ignored it under context pressure) → Enforce via Context Pressure Asymmetry (move it to the Skeptic reviewer) or a hard tool gate. Prune ignored prose.
- **Route Friction** (model bypassed the rule because compliance was manual or multi-step) → Pack the steps into `scripts/<cmd>`. Make the governed path the cheapest path.

---

## Expert Knowledge Activation

Name the canonical work for a mental model. Invoke the installed skill for a checklist.

### 1. Parametric Anchoring

Name the canonical source. A canonical name activates structured prior knowledge at low token cost.

- **Module design**: when a task places a seam, use Ousterhout's terms: deep module, information hiding, narrow interface.
- **Test-first work**: when a test must fail first, use Kent Beck's red-green-refactor loop and name the failing assertion.
- **Refactoring**: when a change touches existing code, name the smell (divergent change, shotgun surgery) before the mechanics.
- **Interface contracts**: when narrowing an interface, state the Liskov case — which caller expectation must still hold.

Parametric recall supplies shape, not proof. Confirm specifics against a skill or a check before you rely on them.

### 2. Context Skill Activation

Invoke the installed skill instead of inlining its methodology into a prompt:

- **Deep module and seam design**: invoke the `Skill` tool for `codebase-design` where installed, else use the APoSD terms above.
- **Language idioms**: invoke `Skill(skill="programming-expert", args="<language>")`.
- **Strict red-green-refactor**: invoke `tdd-expert` where installed. Otherwise state the loop in the prompt.
- **Pass/fail acceptance**: invoke `Skill(skill="eval-gate", args="define")`, then `args="check"` to verify.

Place each role by scope: agent for identity, skill for methodology, phase prompt for one step, rule for repo-wide constraints.

### 3. Context Pressure Asymmetry

Split implementation from review. Each side carries a different context load:

- **Implementer**: give it the full budget — exploration, drafts, failing output. Keep standards and style out of its prompt.
- **Reviewer**: give it the diff only, with zero exploration. Load standards, invariants, and skepticism there.

---

## Progressive Disclosure & Context Load

Context load is a primary architectural constraint. Attention degrades and costs rise as context grows. Load guidance only when a task needs it.

- **The 80/20 Rule**: The 20% of knowledge that solves 80% of problems lives in `SKILL.md`. The deep 80% lives in reference files behind context pointers. This applies recursively: parent spine, subskills, and subskill references.
- **Root Steering via `AGENTS.md`**: the open standard ([agents.md](https://agents.md)). Closest file wins. Nested files are supported. `CLAUDE.md` and other agent variants are compatibility mirrors. Keep to navigation pointers, never inline specs.
- **Prune No-Ops**: Delete steering instructions that do not measurably alter agent decisions.
- **Dispatch on Demand**: Isolate specialized workflows into sub-skills. Load them by handle, never by pasting their bodies.

For invocation classes, description budgets, and platform prompt filtering, read the [context-load policy](references/context-load-policy.md). For authoring a new skill, load `skill-authoring`.

---

## Skill Creation

Creating, editing, or debugging a skill? Read `subskills/skill-authoring/SKILL.md` before you write anything. It holds the taxonomy, the three phases (Gather, Draft, Review), the frontmatter contract, and the checklist.

The spine holds only the decision:

- **Embed, don't create**: an Atomic, Universal workflow under 300 words belongs in the agent, not in a skill.
- **Pick one of three types**: Orchestration sequences phases and parties. Workflow owns phases and artifacts. Domain Knowledge supplies retrieval-time expertise.

Gates: `validate-deps.py lint` for conventions, `validate-deps.py context-check` for the context-load budget. The `check`, `related`, and `sync` subcommands live in `skill-authoring`.

---

## High-Fidelity Handoffs

A handoff transfers intent and pointers, never duplicated technical detail ([ADR-0009](../../docs/adr/0009-behavioral-evals-and-manifest-indexed-handoffs.md)). Subsequent agents initialize state from the handoff and referenced artifacts, displacing prior conversation history.

- **Intent First**: Capture the "Why" and explicit user constraints.
- **Artifact Trail**: Pass absolute pointers to durable artifacts (`design.md`, `mission_manifest.json`, diffs).
- **Zero Duplication**: Never repeat technical decisions, file lists, or test results already present in artifacts.
- **Suggested Skills**: Name the next directive and specific skills to invoke.

To generate a phase handoff, invoke the `handoff` skill.

---

## Model Routing

| Model Tier | Use For                                               | Avoid                                     |
| ---------- | ----------------------------------------------------- | ----------------------------------------- |
| Fast/Cheap | Classification, boilerplate, narrow edits             | Complex reasoning, architecture decisions |
| Balanced   | Implementation, refactors, multi-file work            | Root-cause analysis, subtle invariants    |
| Strong     | Architecture, root-cause analysis, complex invariants | Simple tasks (wasteful)                   |

Escalate tier only when lower tier fails with a clear reasoning gap.

---

## Subagent-First Execution

> [!IMPORTANT] Universal Mandate Across All Coding Agents
> Subagent-First Execution is a **Universal Mandate across all coding agents** (`pi`, `claude`, `agy`, `cursor`, `cline`, `codex`, `gemini`, and others).
>
> Any coding agent handling high-noise tasks **MUST delegate to ephemeral subagents**. This covers broad exploration, recursive symbol searches, bulk editing, verbose build traces, and adversarial crux review. The same rule applies when only the final conclusion or artifact is needed. This guarantees:
> 1. **Context Isolation**: High-entropy intermediate output (hundreds of lines of file dumps, compile errors, stack traces) stays trapped in disposable subagent contexts.
> 2. **Parallel Execution**: Independent investigations or reviews execute concurrently across separate context budgets.
> 3. **Compaction Prevention**: The primary agent's working memory remains lean and focused, avoiding compaction degradation, instruction amnesia, and lost constraints.
>
> **The orchestrator never does implementation work**. Implementers never do heavy exploration, bulk refactoring, or verbose test triage directly in the host pane.

The primary agent routes, dispatches with structured prompts, monitors, synthesizes summaries, and passes pointers between phases. It never writes code, edits files, runs verbose tests in the host pane, or reads full artifact contents into context.

### Subagent Response Contract

Every subagent MUST return the canonical structured response ([resp-format.md](references/resp-format.md), [lane-coordination.md](../herdr/references/lane-coordination.md)):

| Field        | Purpose                                                        |
| ------------ | -------------------------------------------------------------- |
| **Summary**  | Approach and reasoning, ≤100 words — not a play-by-play log    |
| **Artifacts**| Absolute file paths to generated plans, code, or reviews       |
| **Evidence** | Deterministic check results (`name`: PASS/FAIL + command)      |
| **Route**    | `continue`, `remediate`, or `blocked`                          |
| **Issues**   | Discovered risks, each with severity, `file:line`, remediation |

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
