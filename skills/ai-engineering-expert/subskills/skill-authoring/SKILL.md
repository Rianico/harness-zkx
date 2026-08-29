---
name: skill-authoring
description: >-
  Skill design, authoring process (Gather-Draft-Review), taxonomy classification, frontmatter, descriptions, progressive disclosure, and authoring checklists. TRIGGER when creating, writing, or improving a skill; classifying skill type; or designing skill structure.
metadata:
  managed-by: ai-engineering-expert
---

# Skill Authoring

Designing and building skills in the LSZ architecture.

## Skill Taxonomy

Every LSZ skill falls into one of three types:

| Type                 | When to Use                                                                                                                                                           | Key Trait                                                                                                                                                                                                                        |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Orchestration**    | Multi-phase, multi-party, fan-out/fan-in, router-projection pattern                                                                                                   | Owns sequencing, branching, checkpoints across heterogeneous subskills; delegates all implementation via Read + managed-by; never writes artifacts itself. Scaffold router (`manage: [git,python,rust,ci]`) is canonical example |
| **Workflow**         | One or more phases with artifact contract; 1-phase = formerly Action (compact, self-contained), N-phase = formerly Complex (owns transitions, may dispatch subagents) | Owns phase transitions and artifact generation within single flow; `phases==1` is compact Action, `phases>1` is Complex                                                                                                          |
| **Domain Knowledge** | Guides, patterns, expert methodology, reusable constraints                                                                                                            | Retrieval-time expertise; does not own orchestration                                                                                                                                                                             |

> Former `Action` → `Workflow (phases==1)`. Router-Projection pattern: parent dispatches via `Read`, not `Skill` tool, hidden `subskills/` — see `scaffold`.

**When to embed logic directly in an Agent** instead of creating a skill: only when the workflow is Atomic (one specific thing, no loops), Universal (doesn't vary by language/framework), and Short (< 300 words). Example: the `planner` agent.

**Full definitions:** See [skill-authoring.md](references/skill-authoring.md) for detailed descriptions of each type, including when to use each and common pitfalls.

## Authoring Process

### Phase 1: Gather

Ask the user about:

1. **Task and domain** -- What does the skill do? What specific use cases must it handle?
2. **Success Criteria (GDD/EDD)** -- How do we know the goal is achieved? What are the measurable, deterministic outputs? What are the qualitative, semantic goals?
3. **Behavioral Scenarios (BDD)** -- What are the key Given/When/Then scenarios the skill must satisfy?
4. **Taxonomy classification** -- Which of the three types above fits? If unsure, ask: "Does this govern across skills / need multiple parties / fan-out or a router-projection?" (orchestration), "Is it one flow with 1-to-N phases and artifact contracts?" (workflow — `phases==1` compact formerly Action, `phases>1` formerly Complex), or "Is this expertise to load on demand?" (domain knowledge).
5. **Resources needed** -- Does it need executable scripts (deterministic operations), reference files (deep content beyond 500 lines), or just instructions?
6. **Dependencies** -- Does it depend on other skills? If so, declare `metadata.depends-on`.
7. **Parent-skill relationship** -- Is this part of a cluster? Should it be a sub-skill under a parent, or a standalone skill?

### Phase 2: Draft

Create the skill following LSZ conventions:

1. **Directory structure** -- `skills/<name>/SKILL.md` plus `references/` and `scripts/` as needed
2. **Verification Logic (EDD)** -- Include scripts in `scripts/` for deterministic verification. Define how semantic verification (e.g., via a Skeptic subagent) will be handled.
3. **Behavioral Spec (BDD)** -- Include a `references/bdd-scenarios.md` if the workflow is complex, or embed scenarios directly in the SKILL.md body.
4. **Frontmatter** -- `name` (matches directory), `description` (third-person, what + when, trigger vocabulary), `arguments` + `argument-hint` if the skill accepts params, `metadata` for relationships and dependencies.
   - **CRITICAL: YAML Formatting** -- Always use YAML block scalars (`>-` or `|`) for `description` and `argument-hint` to prevent parsing errors caused by unquoted colons, special characters, or multi-line text.
     ```yaml
     description: >-
       Expert methodology for X. TRIGGER when...
     ```
5. **SKILL.md body** -- Under 500 lines. Progressive disclosure: high-level guidance in the body, deep content in `references/`. Apply [writing sub-skill](../writing/SKILL.md) for information hierarchy, pointer wording, completion criteria, leading words, and pruning.
6. **Resource paths** -- Use `$SKILL_DIR/` prefix in prose, relative paths in markdown links
7. **Scripts** -- Use `uv run` with inline script metadata. Place in `scripts/`. Handle errors internally, don't punt to the LLM
8. **Taxonomy-specific structure:**
   - Orchestration: dispatch table + subagent templates, router-projection pattern (`Read` + `managed-by`, hidden `subskills/`), no implementation logic — budget ≤500 lines
   - Workflow (1-phase): compact, focused, minimal structure (formerly Action) — budget ≤150 lines
   - Workflow (N-phase): phase definitions with state transitions, artifact contracts (formerly Complex) — budget ≤150×phases capped 500; lint soft warning first (e.g., "Workflow with 2 phases is 340 lines but budget 300 — consider splitting")
   - Domain knowledge: organized by topic, patterns with examples, gotchas — budget ≤500 lines

### Phase 3: Review

Validate the draft before presenting to the user:

**First-Pass Review Checklist:**

- [ ] Taxonomy type is correct and structure matches that type
- [ ] BDD scenarios are defined (Given/When/Then)
- [ ] EDD verification path is clear (scripts for deterministic, skepticism for semantic)
- [ ] Description is third-person, includes what + when, covers trigger patterns
- [ ] Frontmatter complete: `name`, `description`, `arguments`/`argument-hint` if needed, `metadata` for relationships
- [ ] References are one level deep from SKILL.md
- [ ] Scripts handle errors internally and use `uv run $SKILL_DIR/scripts/` invocation
- [ ] No content that belongs in rules (always-on preferences) or other skills
- [ ] Writing rigor applied (hierarchy, pointers, completion criteria, leading words, pruning) via writing sub-skill; no-ops pruned

Then ask the user:

- Does this cover your use cases?
- Anything missing or unclear?
- Should any section be more or less detailed?

**Before publishing**, run the full [Skill Authoring Checklist](#skill-authoring-checklist) below.

## Required Frontmatter

- `name`: **Required** -- must match directory name (lowercase, hyphens, max 64 chars)
- `description`: **Required** -- what + when, third-person, trigger vocabulary. Use `>-` block scalar.

**Description Writing Principles**

The description is the skill's machine-readable trigger and permanent context-load footprint. Budget: 300 chars (hard gate). It must trigger model discovery, stay within budget, and remain human-legible — all at once.

**Structure (max 3 clauses):**

1. **What it is** — Category noun first: "Reference for..." "Protocol for..." "Expert methodology for..."
2. **When to use** — Category-level trigger scenarios, not verb enumeration: "managing ADRs" not "initializing, creating, linking, superseding, listing, and reading ADRs"
3. **Value proposition** — What makes this skill distinctive (optional, recommended): "Keeps ADR content compatible with adr-tools"

**Compression Rules (apply in order until within budget):**

1. **Categories over actions** — "ADR lifecycle management" not verb-by-verb enumeration
2. **Domain slashes** — "Spring Boot/JPA/Hibernate" not "Spring Boot, JPA, Hibernate, and JUnit"
3. **Parentheticals to body** — "(hard to reverse, surprising without context)" moves to SKILL.md body
4. **TRIGGER: tag for key terms** — End with `TRIGGER: term1, term2, ...` for explicit model matching
5. **Front-load distinctive terms** — First 50 chars must distinguish this skill from related skills
6. **Third-person, present tense** — "Manages ADRs" not "I can help you..." or "This skill manages..."

**Good (108 chars):**

```
Reference for writing and editing skills well — the vocabulary and principles that make a skill predictable.
```

**Good (237 chars):**

```
Methodology spine for LSZ harness AI engineering — context-load policy, skill design, agent action spaces, testing, and subagent-first execution. Use when designing skills/agents/rules/workflows, setting invocation classes or description budgets, or planning eval-first testing. TRIGGER: context-load policy, skill design, agent design, testing methodology.
```

**Bad (443 chars):** Verb enumeration instead of categories. Parenthetical detail belongs in body, not description. Missing TRIGGER tag. Exhaustive where it should be distinctive.

```
Manage architecture decision records with the `adr` CLI. Use for initializing an ADR repository, creating, linking, superseding, listing, and reading ADRs; for deciding whether a new decision relates to older ADRs; for evaluating whether a decision warrants an ADR (hard to reverse, surprising without context, genuine trade-off); and for keeping ADR content short, historical, and compatible with adr-tools templates and status/link behavior.
```

Reference: [glossary.md](references/glossary.md) for the full domain vocabulary (invocation classes, description budget, context load, progressive disclosure, and all skill-authoring terms).

**Key Optional Fields**

- `arguments` + `argument-hint` (pair): `arguments` declares semantic named params for `$name` substitution; `argument-hint` documents them for autocomplete. Names should reflect skill function (`content_type`, `platform`, `scope` not `arg1`, `arg2`). Place `arguments` first. Format `argument-hint` as multi-line YAML with one hint per line using the `|` or `>-` block scalar: `<required>` / `[optional]` / `[opt=a|b]` / `[--flag]`, each with `-- description (default: value)`.
- `allowed-tools`: Tool allowlist without permission prompts
- `user-invocable`: Show in `/` menu (default: `true`). Set `false` for internal skills accessed only through routing commands.
- `disable-model-invocation`: Prevents the `Skill` tool from invoking the skill entirely (default: `false`). Do NOT use for skills accessed through routing commands -- it blocks both automatic loading AND explicit invocation.
- `model`: Override model (`opus`, `sonnet`, `haiku`, `inherit`)
- `effort`: Thinking level (`low`, `medium`, `high`, `xhigh`, `max`)

**Structure**

- SKILL.md under 500 lines — practical usage guide (workflows, commands, examples)
- SKILL.md is env-agnostic — env/config/setup/state belongs in `references/` (progressive disclosure)
- Deep content in `references/` (one level deep)
- Executable logic in `scripts/`
  **Resource Path Convention**
- `$SKILL_DIR` is the path anchor for ALL skill-owned resources (scripts, references, raw docs, config)
- **Prose text:** Always `$SKILL_DIR/references/<module>.md` -- cwd is unknown to the reader
- **Markdown links:** Always relative like `[text](references/<module>.md)` -- standard relative-to-file convention
- Scripts: `uv run $SKILL_DIR/scripts/xxx.py` -- runs from any directory
- Raw docs: `$SKILL_DIR/references/<skill-name>-raw/` in prose -- self-contained within skill
- Avoid `cd` prefixes -- scripts should handle paths internally
- Use `~/.claude/lsz/$SKILL_DIR/` for runtime artifacts (results, temp files)
- Scripts are invoked via `uv run` with inline script metadata for dependencies

**User Interaction**

- Use Dialog Contract pattern for all user questions (tool-agnostic structural spec)
- One question per dialog, 2-4 options plus "Other"
- Always include clear descriptions explaining tradeoffs
- Present questions as plain text — structured but no special tool required

**Interaction Anti-Patterns:**

- Generating 5 files or a massive plan to disk, then asking "Is this okay?" via an unstructured follow-up
- Heavy orchestration and complex workflow skills MUST define explicit checkpoints and structured branching points when approval or divergence is required

**References:**

- [skill-authoring.md](references/skill-authoring.md) -- Complete skill authoring reference (frontmatter, descriptions, triggers, string substitutions, calibration)
- [skill-structure.md](references/skill-structure.md) -- Directory layout, progressive disclosure, scripts
- [dialog-contract.md](references/dialog-contract.md) -- Standard pattern for user interactions
- [glossary.md](references/glossary.md) -- Domain vocabulary: invocation classes, description budget, context load, progressive disclosure, and all skill-authoring terms
- [writing sub-skill](../writing/SKILL.md) -- Agent-document writing: context pointers, hierarchy, disclosure, completion criteria, leading words, pruning; load when drafting any SKILL.md/AGENTS.md/CLAUDE.md

## Skill Authoring Checklist

Before publishing a skill:

**Core Quality**

- [ ] BDD scenarios cover Happy Path, Edge Case, and Error Case
- [ ] Deterministic goals have corresponding evaluation scripts (EDD)
- [ ] Semantic goals have a verification plan (e.g., Adversarial Review)
- [ ] Description is third-person, specific, includes trigger terms
- [ ] Description includes both what AND when to use
- [ ] Description updated for any new capability added (hooks, MCP, testing patterns)
- [ ] Methodology skills: Description covers all three trigger patterns (direct domain, problem framing, decision language)
- [ ] SKILL.md body under 500 lines / 5,000 tokens
- [ ] Reference files are one level deep from SKILL.md
- [ ] No time-sensitive information (or in "old patterns" section)
- [ ] Consistent terminology throughout
- [ ] Examples are concrete, not abstract
- [ ] No redundant sections -- each concept lives in one place
- [ ] SKILL.md is practical usage guide; env/config/setup/state is in `references/`

**Structure**

- [ ] Frontmatter includes `name` and `description` (both required)
- [ ] `description` and `argument-hint` use YAML block scalars (`>-` or `|`)
- [ ] `argument-hint` present if skill accepts arguments
- [ ] `user-invocable: false` set for internal skills accessed only through routing commands (do NOT use `disable-model-invocation` -- it blocks the `Skill` tool)
- [ ] All `depends-on` entries validated via `uv run $SKILL_DIR/scripts/validate-deps.py check`
- [ ] Gotchas section for non-obvious environment facts
- [ ] Templates/checklists for multi-step workflows
- [ ] Validation loops for quality-critical tasks
- [ ] Env-agnostic SKILL.md — no env/config/setup/state inlined (see references/)

## Metadata Conventions

The `metadata` frontmatter field holds project conventions -- structural declarations with validation and documentation value.

### `manage` and `managed-by` (Parent-Child Relationship)

Declares parent-skill-with-sub-skills relationships. See "Parent Skill with Sub-Skills" section below.

### `depends-on` (Cross-Skill Dependencies)

Declares hard dependencies on other skills. A skill listed in `depends-on` must exist in `skills/` or `skills-lock.json`. If absent, the declaring skill produces incorrect or incomplete behavior.

```yaml
metadata:
  depends-on: [eval-gate, tdd-cycle, code-review]
```

**Rules:**

- Hard dependencies only -- only list skills whose absence breaks this skill's behavior
- Simple list of skill names, no arguments (argument details belong in the skill body)
- Sub-skills declare their own `depends-on` independently
- Add `depends-on` when a skill must load/invoke another skill, read its resources, consume its artifacts, or rely on its output contract
- Keep optional alternatives, related reading, examples, and background mentions in prose, not `depends-on`
- Before renaming, moving, merging, or deleting a skill, run `uv run $SKILL_DIR/scripts/validate-deps.py related <skill-name>` and update every listed dependent skill first
- After dependency edits or skill renames, run validation to catch stale references

**Validation:** Run `uv run $SKILL_DIR/scripts/validate-deps.py check` from the project root to check all `depends-on` entries against the skill registry. Use `uv run $SKILL_DIR/scripts/validate-deps.py related <skill-name>` to list both inbound and outbound dependencies before refactoring. Use `fix` to automatically resolve common frontmatter issues.

### `author` and `version` (Attribution)

Optional metadata for third-party skills. Not used by LSZ tooling.

```yaml
metadata:
  author: org-name
  version: '1.0'
```

## Parent Skill with Sub-Skills

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
- Parent uses `Read` tool to dispatch (not `Skill` tool -- nested paths not discoverable)
- Sub-skills are full skills with frontmatter, references, scripts

**Sub-skill names must not collide with top-level skill names** — see Name Collision Rule in the reference. Enforced by `validate-deps.py lint`.

**Reference:**

- [skill-authoring.md](references/skill-authoring.md) -- Full "Parent Skill with Sub-Skills Pattern" section with structure, metadata, registry format, dispatch mechanism, migration guide, and Name Collision Rule

## Rules vs Skills Boundary

Rules are always-on, skills are on-demand. Every token in a rule costs context every conversation.

| Rules                    | Skills               |
| ------------------------ | -------------------- |
| Always loaded            | Loaded on demand     |
| WHAT to use              | HOW to implement     |
| Personal taste, defaults | Non-obvious patterns |
| STATE, don't explain     | Show examples        |
| One-liner preferences    | Framework gotchas    |

**When to use rules:** tool/lib selection, style defaults, baseline patterns, personal taste that should always apply.

**When to use skills:** non-obvious patterns, framework gotchas, examples needed, architectural decisions.

## Skill Gotchas

- **Vague descriptions** -- "Helps with documents" won't trigger. Use explicit trigger vocabulary.
- **Wrong POV** -- "I can help you..." fails discovery. Always third-person.
- **Missing problem framing** -- Description covers "design architecture" but misses "this code is a mess".
- **Hero mode orchestrator** -- Orchestrator doing implementation directly instead of delegating to subagents. Always dispatch.
- **Overloading SKILL.md** -- Keep under 500 lines. Move depth to references/.
- **Deep nesting** -- References should be one level from SKILL.md. Nested references get partially read.
- **No validation loops** -- Skills that do destructive work without self-checking produce silent failures.
- **Orchestration logic in skills** -- Skills should not contain workflow orchestration. Use orchestration skills or commands instead.
- **Content duplication across skills** -- Each piece of knowledge should live in one place. Reference other skills rather than copying.
- **Updating without organizing** -- Before adding content, audit existing structure. Consolidate redundant sections, remove obsolete material.
