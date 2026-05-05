---
name: ai-engineering-expert
description: AI engineering expertise for designing skills, agents, rules, workflows, MCP servers, hooks, evals, and regression tests in the LSZ architecture. TRIGGER when designing, refining, iterating, or redesigning a skill, rule, workflow, agent, command, hook, or MCP server; structuring agent orchestration; defining tool boundaries, action spaces, observation formats, or error recovery contracts; implementing MCP tools, resources, or prompts; choosing bash vs python for hook scripts; choosing stdio vs HTTP transport; hook output format with systemMessage vs additionalContext; eval-first execution, model routing, AI regression testing, bug-check workflows, sandbox/production mismatch tests, SELECT clause omission tests, error state leakage tests, or optimistic update rollback tests; OR user says 'add this to rules/skills', 'update this to xxx rule/skill', 'move this to rules', 'put this in the skill', 'should this be a rule or skill', 'is this the right granularity', 'how should I structure this workflow', 'what's the right action space', 'how do I make this trigger reliably', 'which model tier for this task', 'how do I test AI-generated code', 'bash or python for this hook', 'systemMessage vs additionalContext'.
---

# AI Engineering Expert

Core principles for building robust AI systems. Use this skill when designing or refining skills, agents, workflows, and orchestration patterns.

## Core Mental Model

AI system quality is constrained by four factors:

1. **Action space quality** — Can the agent express the right operations?
2. **Observation quality** — Does the agent see what it needs to decide?
3. **Recovery quality** — Can the agent handle errors gracefully?
4. **Context budget quality** — Is guidance loaded when needed, not before?

Skills that violate these constraints produce fragile agents that fail silently or exhaust context on irrelevant details.

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
- `argument-hint`: Autocomplete hint like `[mode] <topic>`
- `allowed-tools`: Tool allowlist without permission prompts
- `model`: Override model (`opus`, `sonnet`, `haiku`, `inherit`)
- `effort`: Thinking level (`low`, `medium`, `high`, `xhigh`, `max`)

**Structure**
- SKILL.md under 500 lines
- Deep content in `references/` (one level deep)
- Executable logic in `scripts/`

**Script Conventions**
- Run scripts from any directory: `uv run $SKILL_DIR/scripts/xxx.py`
- Avoid `cd` prefixes — the script should handle paths internally
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

**Structure**
- [ ] Frontmatter includes `name` and `description` (both required)
- [ ] `argument-hint` present if skill accepts arguments
- [ ] Gotchas section for non-obvious environment facts
- [ ] Templates/checklists for multi-step workflows
- [ ] Validation loops for quality-critical tasks

### Skill Gotchas

- **Vague descriptions** — "Helps with documents" won't trigger. Use explicit trigger vocabulary.
- **Wrong POV** — "I can help you..." fails discovery. Always third-person.
- **Missing problem framing** — Description covers "design architecture" but misses "this code is a mess".
- **Overloading SKILL.md** — Keep under 500 lines. Move depth to references/.
- **Deep nesting** — References should be one level from SKILL.md. Nested references get partially read.
- **No validation loops** — Skills that do destructive work without self-checking produce silent failures.
- **Orchestration logic in skills** — Skills should not contain workflow orchestration. Use orchestration skills or commands instead.
- **Content duplication across skills** — Each piece of knowledge should live in one place. Reference other skills rather than copying.

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

## Cross-Cutting Gotchas

- **Windows-style paths** — Always use forward slashes (`skills/my-skill/` not `skills\my-skill\`). Cross-platform compatibility matters.
