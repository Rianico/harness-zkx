---
name: ai-engineering-expert
description: >-
  AI engineering expertise for designing skills, agents, rules, workflows, MCP servers, hooks, evals, and regression tests in the LSZ architecture. TRIGGER when designing, refining, iterating, or redesigning a skill, rule, workflow, agent, command, hook, or MCP server; creating, writing, or building a new skill; classifying skill type (orchestration, complex workflow, domain knowledge, action); skill taxonomy or what type of skill; structuring agent orchestration; defining tool boundaries, action spaces, observation formats, or error recovery contracts; implementing MCP tools, resources, or prompts; choosing bash vs python for hook scripts; choosing stdio vs HTTP transport; hook output format with systemMessage vs additionalContext; eval-first execution, model routing, AI regression testing, bug-check workflows, sandbox/production mismatch tests, SELECT clause omission tests, error state leakage tests, or optimistic update rollback tests; reorganizing or consolidating skill/rule content to reduce redundancy and bloat; deciding when to delegate to subagents; designing subagent dispatch patterns; context window too small or too many tokens; skill doesn't trigger or triggers incorrectly; hook too slow or too frequent; agent keeps doing the wrong thing; which model tier for this task; how do I test AI-generated code; this skill is too bloated; consolidate these rules; organize this skill; should I delegate this task; when to use subagents; should this be a rule or skill; is this the right granularity; how should I structure this workflow; what's the right action space; how do I make this trigger reliably; add this to rules/skills; update this to xxx rule/skill; move this to rules; put this in the skill.
arguments: domain
argument-hint: |
  skill-authoring -- loads skill design methodology: taxonomy, frontmatter, descriptions, arguments, dependencies, progressive disclosure, parent/sub-skill layout, and authoring checklists
  rules-development -- loads rules methodology: rules vs skills boundaries, concise always-on constraints, routing conventions, and rule quality checks
  agent-harness -- loads agent methodology: lean persona design, tool/action-space boundaries, observation formats, context budgeting, and error recovery contracts
  extension-dev -- loads extension methodology: MCP servers, hooks, lifecycle scripts, transport choices, hook output formats, and extension boundaries
  testing -- loads AI testing methodology: evals, regression tests, sandbox/production mismatch checks, error-state leakage tests, and behavior-specific cases
  process-arch -- loads process architecture methodology: eval-first loops, model routing, session strategy, and team operating model design
  omitted -- loads only the core AI engineering philosophy and the sub-skill dispatch registry
metadata:
  manage: [skill-authoring, rules-development, agent-harness, extension-dev, testing, process-arch]
---

# AI Engineering Expert

Core principles for building robust AI systems. Use this skill when designing or refining skills, agents, workflows, and orchestration patterns.

## Core Mental Model

AI system quality is constrained by six factors:

1. **Action space quality** -- Can the agent express the right operations?
2. **Observation quality** -- Does the agent see what it needs to decide?
3. **Recovery quality** -- Can the agent handle errors gracefully?
4. **Context budget quality** -- Is guidance loaded when needed, not before?
5. **Artifact hygiene** -- Are files organized, deduplicated, and free of bloat?
6. **Subagent-first execution** -- Is all implementation work delegated to subagents?
7. **Handoff quality (Intent preservation)** -- Is state captured such that a fresh agent can resume with full fidelity?

Skills that violate these constraints produce fragile agents that fail silently, exhaust context on irrelevant details, or accumulate technical debt through disorganized artifacts.

---

## Respect Tool Feedback

Agents MUST treat feedback from automated tools — LSP diagnostics, type checkers, linters, test failures — as authoritative signals. Ignoring tool feedback is a systemic failure, not a style choice.

### LSP Diagnostics Are Blockers

After writing or editing code, the agent MUST check and resolve all diagnostics before declaring done.

1. **Read every diagnostic** — never skip, never dismiss as "just a warning"
2. **Fix or suppress** each one — both are valid; silent ignore is not
3. **Errors first, then warnings** — but all must be triaged
4. **Suppressions require justification** — use the most precise scope available

### Common Diagnostic Categories

| Category | Examples | Resolution |
|----------|----------|------------|
| Unused code | unused imports, variables, parameters | Remove, or prefix with `_` |
| Missing types | implicit `any`, missing type arguments | Add proper types; suppress only at external boundaries |
| Type errors | incompatible types, missing properties | Fix the code; suppress when type system can't express the pattern |
| Dead code | unreachable code, unused assignments | Remove or restructure control flow |

### When Type Looseness Is Acceptable

- Interfacing with untyped external APIs (HTTP responses, JSON parsing)
- Dynamic dispatch where type narrowing is impossible
- Third-party libraries without type stubs

Even in these cases, **add a suppression comment** explaining why — never silently pass.

### Verification Pattern

```bash
# After any code change, check diagnostics
llm-lsp-cli lsp diagnostics <file>
llm-lsp-cli lsp workspace-diagnostics
```

This principle applies to all languages and all tool types. Domain-specific exceptions (e.g., exploratory notebooks, prototype scripts) must be explicitly scoped by the user.

---

## High-Fidelity Handoffs

### Core Principle

**The Handoff is the Mission Bridge.** In complex multi-agent systems or long-running tasks, the handoff document (`handoff.md`) acts as a **Context Aggregator** that distills Goals, Reasoning, and Intent from a sprawling session into a single, high-signal source of truth.

This pattern enables:
- **Multi-Agent Continuity**: Subagent A can hand off a mission to Subagent B (or even a different model/platform) with 100% fidelity.
- **Context Displacement**: The handoff document is high-signal enough to stand in for full specifications or deep chat history, keeping the next session's context window pristine.
- **Session Compaction**: Instead of re-reading 1,000 lines of history, the agent reads a 50-line distilled handoff.

### The Handoff Contract

Every major phase transition (e.g., Design -> Implement, Implement -> Verify) MUST conclude with a handoff aggregation.

| Requirement | Description |
|-------------|-------------|
| **Intent First** | Preserve the "Why" (Reasoning) and the "Goal" (User Intent) over just the "What" (Code). |
| **Artifact Trail** | Provide absolute pointers to all durable artifacts (Design, ADRs, Code, Evals). |
| **Success Criteria** | Define exactly what "done" looks like for the next agent. |
| **Context Recovery** | The next phase starts by reading the handoff to initialize its state. |

### Multi-Agent Interaction

The Handoff pattern is the primary mechanism for **Cross-Agent Collaboration**:
- **Subagent-to-Subagent**: Direct state passing via pointers in the handoff.
- **Cross-Model Portability**: A handoff generated by Claude can be consumed by Pi or GPT, as it relies on durable markdown artifacts rather than internal model state.
- **System Stability**: Missions can survive complete context resets if the handoff document is persisted in the repository (`.lsz/`).

### Anti-Patterns

- **History Hoarding**: Expecting the next agent to re-read the entire chat history.
- **Embedded Bloat**: Pasting 500-line specs into the handoff instead of passing pointers.
- **Prose-Only Handoff**: Vague summaries without concrete artifact trails or success criteria.
- **Hero-Mode Resumption**: Starting a new phase without reading the previous handoff.

---

## Subagent-First Execution

### Core Principle

**The orchestrator never does implementation work.** All code writing, file editing, test execution, doc updates, and review work happens in subagents. The main agent is a pure router: dispatch, monitor, receive results.

This is not a context optimization -- it is a fundamental architectural constraint that ensures:
- Clean separation between orchestration logic and execution logic
- Predictable context budgets (orchestrator sees summaries, not full artifacts)
- Parallelizable work (multiple subagents can run concurrently)
- Isolated failure domains (subagent errors don't corrupt orchestrator state)

### The Orchestrator Role

| Orchestrator DOES | Orchestrator NEVER DOES |
|-------------------|------------------------|
| Route tasks to appropriate subagents | Write code directly |
| Dispatch with structured prompts | Edit files directly |
| Monitor for completion/failure | Run tests directly |
| Receive and synthesize summaries | Read full artifact contents into context |
| Handle user interaction and approvals | Execute shell commands for implementation |
| Pass pointers between phases | Re-process subagent outputs |

### Dispatch Pattern

Always use structured dispatch templates. Every dispatch MUST specify the expected response format (default: `rules/templates/resp-format.md`) so the orchestrator can make routing decisions.

**Standard dispatch template:**

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

**Why the response format matters:**
- Orchestrator parses output to decide next action -- needs structured fields, not prose
- Route + Issues enable automated remediation loops without user intervention
- Without explicit format, subagents return unstructured text that the orchestrator cannot reliably parse

**When to customize the format:**
- Add domain-specific fields (e.g., `## Test Results` for test runners)
- Omit `## Route` when the subagent has no routing decision to make
- Never remove `## Summary` or `## Artifacts` -- these are always required

### Pointer-Based State Passing

Subagents exchange state through **file paths**, not content. The orchestrator passes pointers; subagents read/write artifacts at those paths.

**Why pointers:**
- Preserves orchestrator context budget
- Enables phase-to-phase continuity without orchestrator re-reading
- Supports large artifacts (plans, reports, code diffs)

**Pattern:**

```markdown
Agent tool (developer):
  prompt: |
    Plan file: /path/to/.lsz/.../plan/plan_v1.md

    Implement the feature described in the plan.

    Return: Summary (<=100 words) + paths to modified files.
```

**Anti-patterns:**
- Orchestrator reads plan, then passes plan content to subagent
- Subagent returns full artifact content instead of path
- Creating fresh topic roots for each phase instead of reusing one

### Subagent Response Contract

Every subagent and skill invocation MUST return structured output per `rules/templates/resp-format.md`. This section adds skill-to-skill routing semantics on top of that default.

**Key addition: route-based handoff.**

When Skill A invokes Skill B:
```
Skill B -> structured output (status + route + issues)
     |
Skill A -> parses output, makes routing decision
     |
Next action (remediate, continue, block)
```

- **Skill B:** produce status, enumerate issues, recommend route. NOT assume what "remediate" means in caller's context.
- **Skill A:** parse output, translate route into the right action for its workflow.

**Why this boundary matters:** Skills remain composable -- eval-gate works with orchestrating, brainstorming, or standalone. No upstream coupling. Orchestrator retains control.

**Example:**
```text
# eval-gate outputs:
Route: remediate
Issues: CAP-01: 3 warnings, NEG-01: suppressions in commands/lsp.py

# orchestrating decides: dispatch developer agent (not full tdd-cycle)
```

**Anti-patterns:**
- Subagent returns prose without structure -> orchestrator cannot reliably parse
- Subagent assumes caller's workflow -> eval-gate references tdd-cycle internals
- Subagent returns full artifact content -> wastes orchestrator context

### When to Use Which Subagent

| Task | Subagent Type |
|------|---------------|
| Write/modify code | `developer` |
| Review code for quality | `code-reviewer` |
| Security analysis | `security-reviewer` |
| Database schema work | `database-reviewer` |
| Research/explore codebase | `Explore` |
| General multi-step tasks | `general-purpose` |
| Architecture design | `architect` |

### Anti-Patterns

- **Hero mode orchestrator** -- "Let me just write this quick fix directly"
- **Context hoarding** -- Reading full artifact contents instead of dispatching a subagent
- **Sequential when parallel is possible** -- Running review agents one after another instead of concurrently
- **Orchestrator as reviewer** -- Main agent reviewing code instead of dispatching `code-reviewer`
- **Unstructured subagent output** -- Prose without Summary/Artifacts/Route fields

### Workflow Phase Design

**Consolidate stages that share sources.** When multiple stages are independent and derive from the same source files, merge into one stage.

**Checklist:**
1. Do all stages read from the same source?
2. Are there dependencies forcing sequential execution?
3. Is combined task size manageable?

If (1) yes, (2) and (3) no -> consolidate.

**Why:** Each stage incurs orchestration overhead (dispatch, context loading, summary). Merging eliminates redundant reads.

**Example:** docs-to-skill had 4 separate stages (structure, modules, triggers, patterns) all reading the same docs. Consolidated to 1 stage, reducing 8 phases to 5.

### Reference

[Full details: subagent-first-execution.md](references/subagent-first-execution.md)

---

## Artifact Hygiene

### Core Principle

Every modification to skills, rules, workflows, agents, or hooks must preserve or improve organization. Additive changes without consolidation create bloat; scattered knowledge creates discovery failures.

### Before Any Update

1. **Audit the target** -- Read the file structure, understand existing organization
2. **Identify redundancy** -- Check if new content duplicates existing knowledge elsewhere
3. **Find the right home** -- Determine if content belongs in this file or should be a reference/linked elsewhere

### During Updates

- **Consolidate, don't accumulate** -- Merge related sections, remove superseded content
- **One concept, one location** -- Reference other files rather than copying
- **Reorganize when needed** -- If a file has grown unclear, restructure before adding
- **Group by topic by default** -- Comprehensive rules or broad information files must be organized by topic (e.g., Code Quality, Git Workflow, Testing). Topic-based grouping improves discoverability and enables readers to scan by concern.

### Red Flags

- File exceeds size limits (SKILL.md > 500 lines, reference files bloating)
- Multiple sections explaining the same concept
- Copy-pasted content across files
- "Misc" or "Other" catch-all sections
- Unclear section ordering or naming

### Enforcement

- When adding new capability: update description, check for duplicates, consolidate if found
- When refining existing content: remove obsolete parts, not just add new ones
- When file feels disorganized: fix organization first, then add new content

---

## Cross-Cutting Gotchas

- **Windows-style paths** -- Always use forward slashes (`skills/my-skill/` not `skills\my-skill\`). Cross-platform compatibility matters.
- **Additive-only updates** -- Adding without removing creates bloat. Every new section should prompt: "Is there old content this replaces?"
- **Copy-paste across skills** -- Duplicated methodology rots independently. Reference the canonical source instead.
- **Catch-all sections** -- "Miscellaneous", "Other Notes", "Tips" sections are organization debt. Every item should have a clear category.
- **Size blindness** -- Files grow silently. Check line counts periodically; split or consolidate when over limits.

---

## Sub-Skill Dispatch

This skill manages six domain-specific sub-skills. Read the appropriate sub-skill based on the `domain` argument.

| Domain | Sub-Skill | Covers |
|--------|-----------|--------|
| `skill-authoring` | `$SKILL_DIR/subskills/skill-authoring/SKILL.md` | Skill design, frontmatter, descriptions, progressive disclosure, parent-skill pattern, checklists |
| `rules-development` | `$SKILL_DIR/subskills/rules-development/SKILL.md` | Rules vs skills boundary, rules design principles, when to use rules vs skills |
| `agent-harness` | `$SKILL_DIR/subskills/agent-harness/SKILL.md` | Action space design, observation design, error recovery, context budgeting |
| `extension-dev` | `$SKILL_DIR/subskills/extension-dev/SKILL.md` | MCP server patterns, hook development, language selection, output format |
| `testing` | `$SKILL_DIR/subskills/testing/SKILL.md` | AI regression testing, sandbox/production mismatch, error state leakage, optimistic update rollback |
| `process-arch` | `$SKILL_DIR/subskills/process-arch/SKILL.md` | Eval-first loop, model routing, session strategy, team operating model |

**Dispatch:** When `$domain` is provided, read the matching sub-skill file and follow its instructions. When no domain is specified, only the philosophy above is loaded.
