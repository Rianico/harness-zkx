---
name: ai-engineering-expert
description: AI engineering expertise for designing skills, agents, rules, workflows, MCP servers, hooks, evals, and regression tests in the LSZ architecture. TRIGGER when designing, refining, iterating, or redesigning a skill, rule, workflow, agent, command, hook, or MCP server; structuring agent orchestration; defining tool boundaries, action spaces, observation formats, or error recovery contracts; implementing MCP tools, resources, or prompts; choosing bash vs python for hook scripts; choosing stdio vs HTTP transport; hook output format with systemMessage vs additionalContext; eval-first execution, model routing, AI regression testing, bug-check workflows, sandbox/production mismatch tests, SELECT clause omission tests, error state leakage tests, or optimistic update rollback tests; reorganizing or consolidating skill/rule content to reduce redundancy and bloat; deciding when to delegate to subagents; designing subagent dispatch patterns; OR user says 'add this to rules/skills', 'update this to xxx rule/skill', 'move this to rules', 'put this in the skill', 'should this be a rule or skill', 'is this the right granularity', 'how should I structure this workflow', 'what's the right action space', 'how do I make this trigger reliably', 'which model tier for this task', 'how do I test AI-generated code', 'bash or python for this hook', 'systemMessage vs additionalContext', 'this skill is too bloated', 'consolidate these rules', 'organize this skill', 'should I delegate this task', 'when to use subagents'.
---

# AI Engineering Expert

Core principles for building robust AI systems. Use this skill when designing or refining skills, agents, workflows, and orchestration patterns.

## Core Mental Model

AI system quality is constrained by six factors:

1. **Action space quality** — Can the agent express the right operations?
2. **Observation quality** — Does the agent see what it needs to decide?
3. **Recovery quality** — Can the agent handle errors gracefully?
4. **Context budget quality** — Is guidance loaded when needed, not before?
5. **Artifact hygiene** — Are files organized, deduplicated, and free of bloat?
6. **Subagent-first execution** — Is all implementation work delegated to subagents?

Skills that violate these constraints produce fragile agents that fail silently, exhaust context on irrelevant details, or accumulate technical debt through disorganized artifacts.

---

## Subagent-First Execution

### Core Principle

**The orchestrator never does implementation work.** All code writing, file editing, test execution, doc updates, and review work happens in subagents. The main agent is a pure router: dispatch, monitor, receive results.

This is not a context optimization—it is a fundamental architectural constraint that ensures:
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
- Orchestrator parses output to decide next action — needs structured fields, not prose
- Route + Issues enable automated remediation loops without user intervention
- Without explicit format, subagents return unstructured text that the orchestrator cannot reliably parse

**When to customize the format:**
- Add domain-specific fields (e.g., `## Test Results` for test runners)
- Omit `## Route` when the subagent has no routing decision to make
- Never remove `## Summary` or `## Artifacts` — these are always required

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
    
    Return: Summary (≤100 words) + paths to modified files.
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
Skill B → structured output (status + route + issues)
     ↓
Skill A → parses output, makes routing decision
     ↓
Next action (remediate, continue, block)
```

- **Skill B:** produce status, enumerate issues, recommend route. NOT assume what "remediate" means in caller's context.
- **Skill A:** parse output, translate route into the right action for its workflow.

**Why this boundary matters:** Skills remain composable — eval-gate works with orchestrating, brainstorming, or standalone. No upstream coupling. Orchestrator retains control.

**Example:**
```text
# eval-gate outputs:
Route: remediate
Issues: CAP-01: 3 warnings, NEG-01: suppressions in commands/lsp.py

# orchestrating decides: dispatch developer agent (not full tdd-cycle)
```

**Anti-patterns:**
- Subagent returns prose without structure → orchestrator cannot reliably parse
- Subagent assumes caller's workflow → eval-gate references tdd-cycle internals
- Subagent returns full artifact content → wastes orchestrator context

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

- **Hero mode orchestrator** — "Let me just write this quick fix directly"
- **Context hoarding** — Reading full artifact contents instead of dispatching a subagent
- **Sequential when parallel is possible** — Running review agents one after another instead of concurrently
- **Orchestrator as reviewer** — Main agent reviewing code instead of dispatching `code-reviewer`
- **Unstructured subagent output** — Prose without Summary/Artifacts/Route fields

### Workflow Phase Design

**Consolidate stages that share sources.** When multiple stages are independent and derive from the same source files, merge into one stage.

**Checklist:**
1. Do all stages read from the same source?
2. Are there dependencies forcing sequential execution?
3. Is combined task size manageable?

If (1) yes, (2) and (3) no → consolidate.

**Why:** Each stage incurs orchestration overhead (dispatch, context loading, summary). Merging eliminates redundant reads.

**Example:** docs-to-skill had 4 separate stages (structure, modules, triggers, patterns) all reading the same docs. Consolidated to 1 stage, reducing 8 phases to 5.

### Reference

[Full details: subagent-first-execution.md](references/subagent-first-execution.md)

---

## Skill Development

### Quick Reference: Skill Authoring

**Required Frontmatter**
- `name`: **Required** — must match directory name (lowercase, hyphens, max 64 chars)
- `description`: **Required** — what + when, third-person, trigger vocabulary

**CRITICAL: Description Triggers Discovery**
The `description` field is the **only way Claude discovers skills**. A skill that cannot be found cannot be used. Every time you add a new capability (hooks, MCP servers, testing patterns), you MUST update the description with:
- The domain term in the expertise list
- Trigger scenarios in the TRIGGER clause
- Example user questions that should invoke the skill

If it's not in the description, the skill will not trigger.

**Key Optional Fields**
- `arguments` + `argument-hint` (pair): `arguments` declares semantic named params for `$name` substitution; `argument-hint` documents them for autocomplete. Names should reflect skill function (`content_type`, `platform`, `scope` not `arg1`, `arg2`). Place `arguments` first. Format `argument-hint` as multi-line YAML with one hint per line: `<required>` / `[optional]` / `[opt=a|b]` / `[--flag]`, each with `-- description (default: value)`.
- `allowed-tools`: Tool allowlist without permission prompts
- `user-invocable`: Show in `/` menu (default: `true`). Set `false` for internal skills accessed only through routing commands.
- `disable-model-invocation`: Prevents the `Skill` tool from invoking the skill entirely (default: `false`). Do NOT use for skills accessed through routing commands — it blocks both automatic loading AND explicit invocation.
- `model`: Override model (`opus`, `sonnet`, `haiku`, `inherit`)
- `effort`: Thinking level (`low`, `medium`, `high`, `xhigh`, `max`)

**Structure**
- SKILL.md under 500 lines
- Deep content in `references/` (one level deep)
- Executable logic in `scripts/`

**Resource Path Convention**
- `$SKILL_DIR` is the path anchor for ALL skill-owned resources (scripts, references, raw docs, config)
- **Prose text:** Always `$SKILL_DIR/references/<module>.md` — cwd is unknown to the reader
- **Markdown links:** Always relative like `[text](references/<module>.md)` — standard relative-to-file convention
- Scripts: `uv run $SKILL_DIR/scripts/xxx.py` — runs from any directory
- Raw docs: `$SKILL_DIR/references/<skill-name>-raw/` in prose — self-contained within skill
- Avoid `cd` prefixes — scripts should handle paths internally
- Use `~/.claude/lsz/$SKILL_DIR/` for runtime artifacts (results, temp files)
- Scripts are invoked via `uv run` with inline script metadata for dependencies

**User Interaction**
- Use Dialog Contract pattern for all user questions (tool-agnostic structural spec)
- One question per dialog, 2-4 options plus "Other"
- Always include clear descriptions explaining tradeoffs
- Each coding agent maps to its native tool (Claude Code: AskUserQuestion, OpenCode: diag)

**References:**
- [skill-authoring.md](references/skill-authoring.md) — Complete skill authoring reference (frontmatter, descriptions, triggers)
- [skill-structure.md](references/skill-structure.md) — Directory layout, progressive disclosure
- [dialog-contract.md](references/dialog-contract.md) — Standard pattern for user interactions

### Skill Authoring Checklist

Before publishing a skill:

**Core Quality**
- [ ] Description is third-person, specific, includes trigger terms
- [ ] Description includes both what AND when to use
- [ ] Description updated for any new capability added (hooks, MCP, testing patterns)
- [ ] Methodology skills: Description covers all three trigger patterns (direct domain, problem framing, decision language)
- [ ] SKILL.md body under 500 lines / 5,000 tokens
- [ ] Reference files are one level deep from SKILL.md
- [ ] No time-sensitive information (or in "old patterns" section)
- [ ] Consistent terminology throughout
- [ ] Examples are concrete, not abstract
- [ ] No redundant sections — each concept lives in one place

**Structure**
- [ ] Frontmatter includes `name` and `description` (both required)
- [ ] `argument-hint` present if skill accepts arguments
- [ ] `user-invocable: false` set for internal skills accessed only through routing commands (do NOT use `disable-model-invocation` — it blocks the `Skill` tool)
- [ ] Gotchas section for non-obvious environment facts
- [ ] Templates/checklists for multi-step workflows
- [ ] Validation loops for quality-critical tasks

### Parent Skill with Sub-Skills

When a skill manages multiple related capabilities, use the parent-skill-with-sub-skills pattern instead of routing commands.

**Structure:**
```
skills/write/
  SKILL.md              # Parent: registry + dispatch
  subskills/
    article/SKILL.md    # Sub-skill: long-form content
    publish/SKILL.md    # Sub-skill: platform distribution
```

**Metadata:**
```yaml
# Parent
metadata:
  manage: [article, publish]

# Sub-skill
metadata:
  managed-by: write
```

**Key points:**
- Sub-skills are nested in `subskills/` directory (hidden from Claude Code discovery)
- Parent uses `Read` tool to dispatch (not `Skill` tool — nested paths not discoverable)
- Sub-skills are full skills with frontmatter, references, scripts

**Reference:**
- [skill-authoring.md](references/skill-authoring.md) — Full "Parent Skill with Sub-Skills Pattern" section with structure, metadata, registry format, dispatch mechanism, and migration guide

### Skill Gotchas

- **Vague descriptions** — "Helps with documents" won't trigger. Use explicit trigger vocabulary.
- **Wrong POV** — "I can help you..." fails discovery. Always third-person.
- **Missing problem framing** — Description covers "design architecture" but misses "this code is a mess".
- **Hero mode orchestrator** — Orchestrator doing implementation directly instead of delegating to subagents. Always dispatch.
- **Overloading SKILL.md** — Keep under 500 lines. Move depth to references/.
- **Deep nesting** — References should be one level from SKILL.md. Nested references get partially read.
- **No validation loops** — Skills that do destructive work without self-checking produce silent failures.
- **Orchestration logic in skills** — Skills should not contain workflow orchestration. Use orchestration skills or commands instead.
- **Content duplication across skills** — Each piece of knowledge should live in one place. Reference other skills rather than copying.
- **Updating without organizing** — Before adding content, audit existing structure. Consolidate redundant sections, remove obsolete material.

---

## Rules Development

### Quick Reference: Rules Design

**Core Principle**
Rules are always-on, skills are on-demand. Every token in a rule costs context every conversation.

**Rules vs Skills Boundary**
| Rules | Skills |
|-------|--------|
| Always loaded | Loaded on demand |
| WHAT to use | HOW to implement |
| Personal taste, defaults | Non-obvious patterns |
| STATE, don't explain | Show examples |
| One-liner preferences | Framework gotchas |

**Rules Checklist**
- [ ] Concise — one line per rule, no justification
- [ ] Baseline only — LLM already knows, you're setting YOUR default
- [ ] Stable — rarely changes, settled decisions
- [ ] STATE — declare preferences, don't explain why

**When to use rules:**
- Tool/lib selection (`uv` over `pip`)
- Style defaults (`pytest -q`)
- Baseline patterns (type hints on all signatures)
- Personal taste that should always apply

**When to use skills:**
- Non-obvious patterns (async event loop blocking)
- Framework gotchas (Django N+1 queries)
- Examples needed (PyTorch memory management)
- Architectural decisions (fat models, skinny views)

**Reference:**
- [skill-authoring.md](references/skill-authoring.md) — Full "Rules vs Skills Boundary" section with design principles, anti-patterns, and layered examples

---

## Agent & Harness Design

### Quick Reference: Harness Design

**Action Space Rules**
- Stable, explicit tool names
- Schema-first, narrow inputs
- Deterministic output shapes
- Avoid catch-all tools unless isolation impossible

**Observation Design**
Every tool response should include:
- `status`: success|warning|error
- `summary`: one-line result
- `next_actions`: actionable follow-ups
- `artifacts`: file paths / IDs

**Error Recovery**
Every error path needs:
- Root cause hint
- Safe retry instruction
- Explicit stop condition

[Full details: tool-design-contracts.md](references/tool-design-contracts.md)

---

## Process & Architecture

### Quick Reference: Architecture & Process

**Team Operating Model**
- Planning quality > typing speed
- Eval coverage > anecdotal confidence
- Review focus: behavior and invariants, not style

**Eval-First Loop**
1. Define capability eval and regression eval
2. Run baseline, capture failure signatures
3. Execute implementation
4. Re-run evals, compare deltas

**Model Routing**
- Fast/cheap: classification, boilerplate, narrow edits
- Balanced: implementation, refactors, multi-file work
- Strong: architecture, root-cause analysis, complex invariants

**Session Strategy**
- Continue for closely-coupled units
- Fresh session after major phase transitions
- Compact at milestones, not during debugging

[Full details: eval-first-development.md](references/eval-first-development.md)

---

## Extension Development

### Quick Reference: MCP Server Patterns

**Core Concepts**
- **Tools**: Actions the model can invoke (e.g., search, run command)
- **Resources**: Read-only data the model can fetch (e.g., file contents, API responses)
- **Prompts**: Reusable, parameterized prompt templates
- **Transport**: stdio (local clients) vs Streamable HTTP (remote/Cursor/cloud)

**Best Practices**
- Schema-first: Define input schemas for every tool
- Structured errors: Return messages the model can interpret
- Idempotency: Prefer idempotent tools for safe retries
- SDK versioning: Pin version, check release notes on upgrade

[Full details: mcp-server-patterns.md](references/mcp-server-patterns.md)

### Quick Reference: Hook Development

**Language Selection**
- **Bash**: High-frequency hooks (>10/session), simple I/O, no dependencies
- **Python**: Complex logic (>50 lines), external libs, stateful operations
- **Hybrid**: Bash entrypoint + Python helper when both matter

**Output Format**
- **`systemMessage`**: User-visible alert in transcript
- **`additionalContext`**: LLM-only context injection (silent to user)
- **`hookSpecificOutput.hookEventName`**: Required for event-specific fields

**Decision Drivers**
- Frequency: Python startup ~50-100ms; Bash ~5-10ms
- Complexity: Bash with `jq` matches Python for simple JSON transforms
- Dependencies: Python ecosystem justifies overhead when needed

[Full details: hook-language-selection.md](references/hook-language-selection.md)
[Output format: hook-output-format.md](references/hook-output-format.md)

---

## Testing

### Quick Reference: Testing Patterns

**The Core Problem**
When the same AI writes and reviews code, it carries the same assumptions into both steps. Systematic blind spots emerge that only automated tests catch.

**Top Regression Patterns**
1. Sandbox/production path mismatch
2. SELECT clause omission
3. Error state leakage
4. Optimistic update without rollback

**Test Strategy**
Write tests for bugs that were found, not for code that works. AI tends to make the same category of mistakes repeatedly — once tested, that regression cannot happen again.

[Full details: sandbox-testing-patterns.md](references/sandbox-testing-patterns.md)

---

## Artifact Hygiene

### Quick Reference: Organization & Clarity

**Core Principle**
Every modification to skills, rules, workflows, agents, or hooks must preserve or improve organization. Additive changes without consolidation create bloat; scattered knowledge creates discovery failures.

**Before Any Update**
1. **Audit the target** — Read the file structure, understand existing organization
2. **Identify redundancy** — Check if new content duplicates existing knowledge elsewhere
3. **Find the right home** — Determine if content belongs in this file or should be a reference/linked elsewhere

**During Updates**
- **Consolidate, don't accumulate** — Merge related sections, remove superseded content
- **One concept, one location** — Reference other files rather than copying
- **Reorganize when needed** — If a file has grown unclear, restructure before adding
- **Group by topic by default** — Comprehensive rules or broad information files must be organized by topic (e.g., Code Quality, Git Workflow, Testing). Topic-based grouping improves discoverability and enables readers to scan by concern.

**Red Flags**
- File exceeds size limits (SKILL.md > 500 lines, reference files bloating)
- Multiple sections explaining the same concept
- Copy-pasted content across files
- "Misc" or "Other" catch-all sections
- Unclear section ordering or naming

**Enforcement**
- When adding new capability: update description, check for duplicates, consolidate if found
- When refining existing content: remove obsolete parts, not just add new ones
- When file feels disorganized: fix organization first, then add new content

---

## Cross-Cutting Gotchas

- **Windows-style paths** — Always use forward slashes (`skills/my-skill/` not `skills\my-skill\`). Cross-platform compatibility matters.
- **Additive-only updates** — Adding without removing creates bloat. Every new section should prompt: "Is there old content this replaces?"
- **Copy-paste across skills** — Duplicated methodology rots independently. Reference the canonical source instead.
- **Catch-all sections** — "Miscellaneous", "Other Notes", "Tips" sections are organization debt. Every item should have a clear category.
- **Size blindness** — Files grow silently. Check line counts periodically; split or consolidate when over limits.
