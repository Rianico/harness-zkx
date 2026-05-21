---
name: skill-authoring
description: >-
  Skill design, authoring process (Gather-Draft-Review), taxonomy classification, frontmatter, descriptions, progressive disclosure, parent-skill pattern, and authoring checklists for the LSZ architecture. TRIGGER when creating, writing, or building a new skill; designing skill structure, frontmatter, or descriptions; classifying skill type (orchestration, complex workflow, domain knowledge, action); or improving an existing skill's structure.
metadata:
  managed-by: ai-engineering-expert
---

# Skill Authoring

Designing and building skills in the LSZ architecture.

## Skill Taxonomy

Every LSZ skill falls into one of four types:

| Type | When to Use | Key Trait |
|------|-------------|-----------|
| **Orchestration** | Multi-phase, multi-party, fan-out/fan-in workflows | Owns sequencing, branching, checkpoints; delegates all implementation |
| **Complex Workflow** | Substantial single-purpose workflow with multiple phases | May invoke agents; owns phase transitions and artifact generation |
| **Domain Knowledge** | Guides, patterns, expert methodology, reusable constraints | Retrieval-time expertise; does not own orchestration |
| **Action** | Narrow, simple workflows and direct task execution | Low-ambiguity; compact and self-contained |

**When to embed logic directly in an Agent** instead of creating a skill: only when the workflow is Atomic (one specific thing, no loops), Universal (doesn't vary by language/framework), and Short (< 300 words). Example: the `planner` agent.

**Full definitions:** See [skill-authoring.md](references/skill-authoring.md) for detailed descriptions of each type, including when to use each and common pitfalls.

## Authoring Process

### Phase 1: Gather

Ask the user about:

1. **Task and domain** -- What does the skill do? What specific use cases must it handle?
2. **Taxonomy classification** -- Which of the four types above fits? If unsure, ask: "Does this need multiple phases or parties?" (orchestration), "Is there a single multi-step workflow?" (complex workflow), "Is this expertise to load on demand?" (domain knowledge), or "Is this a narrow, self-contained task?" (action).
3. **Skill identity** -- What `name` fits the directory? What `description` triggers cover the use cases?
4. **Resources needed** -- Does it need executable scripts (deterministic operations), reference files (deep content beyond 500 lines), or just instructions?
5. **Dependencies** -- Does it depend on other skills? If so, declare `metadata.depends-on`.
6. **Parent-skill relationship** -- Is this part of a cluster? Should it be a sub-skill under a parent, or a standalone skill?

### Phase 2: Draft

Create the skill following LSZ conventions:

1. **Directory structure** -- `skills/<name>/SKILL.md` plus `references/` and `scripts/` as needed
2. **Frontmatter** -- `name` (matches directory), `description` (third-person, what + when, trigger vocabulary), `arguments` + `argument-hint` if the skill accepts params, `metadata` for relationships and dependencies.
   - **CRITICAL: YAML Formatting** -- Always use YAML block scalars (`>-` or `|`) for `description` and `argument-hint` to prevent parsing errors caused by unquoted colons, special characters, or multi-line text.
     ```yaml
     description: >-
       Expert methodology for X. TRIGGER when...
     ```
3. **SKILL.md body** -- Under 500 lines. Progressive disclosure: high-level guidance in the body, deep content in `references/`
4. **Resource paths** -- Use `$SKILL_DIR/` prefix in prose, relative paths in markdown links
5. **Scripts** -- Use `uv run` with inline script metadata. Place in `scripts/`. Handle errors internally, don't punt to the LLM
6. **Taxonomy-specific structure:**
   - Orchestration: dispatch table + subagent templates, no implementation logic
   - Complex workflow: phase definitions with state transitions, artifact contracts
   - Domain knowledge: organized by topic, patterns with examples, gotchas
   - Action: compact, focused, minimal structure

### Phase 3: Review

Validate the draft before presenting to the user:

**First-Pass Review Checklist:**
- [ ] Taxonomy type is correct and structure matches that type
- [ ] Description is third-person, includes what + when, covers trigger patterns
- [ ] Frontmatter complete: `name`, `description`, `arguments`/`argument-hint` if needed, `metadata` for relationships
- [ ] References are one level deep from SKILL.md
- [ ] Scripts handle errors internally and use `uv run $SKILL_DIR/scripts/` invocation
- [ ] No content that belongs in rules (always-on preferences) or other skills

Then ask the user:
- Does this cover your use cases?
- Anything missing or unclear?
- Should any section be more or less detailed?

**Before publishing**, run the full [Skill Authoring Checklist](#skill-authoring-checklist) below.

## Required Frontmatter

- `name`: **Required** -- must match directory name (lowercase, hyphens, max 64 chars)
- `description`: **Required** -- what + when, third-person, trigger vocabulary. Use `>-` block scalar.

**CRITICAL: Description Triggers Discovery**
The `description` field is the **only way Claude discovers skills**. A skill that cannot be found cannot be used. Every time you add a new capability (hooks, MCP servers, testing patterns), you MUST update the description with:
- The domain term in the expertise list
- Trigger scenarios in the TRIGGER clause
- Example user questions that should invoke the skill

If it's not in the description, the skill will not trigger.

**Key Optional Fields**
- `arguments` + `argument-hint` (pair): `arguments` declares semantic named params for `$name` substitution; `argument-hint` documents them for autocomplete. Names should reflect skill function (`content_type`, `platform`, `scope` not `arg1`, `arg2`). Place `arguments` first. Format `argument-hint` as multi-line YAML with one hint per line using the `|` or `>-` block scalar: `<required>` / `[optional]` / `[opt=a|b]` / `[--flag]`, each with `-- description (default: value)`.
- `allowed-tools`: Tool allowlist without permission prompts
- `user-invocable`: Show in `/` menu (default: `true`). Set `false` for internal skills accessed only through routing commands.
- `disable-model-invocation`: Prevents the `Skill` tool from invoking the skill entirely (default: `false`). Do NOT use for skills accessed through routing commands -- it blocks both automatic loading AND explicit invocation.
- `model`: Override model (`opus`, `sonnet`, `haiku`, `inherit`)
- `effort`: Thinking level (`low`, `medium`, `high`, `xhigh`, `max`)

**Structure**
- SKILL.md under 500 lines
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
- Each coding agent maps to its native tool (Claude Code: AskUserQuestion, OpenCode: diag)

**References:**
- [skill-authoring.md](references/skill-authoring.md) -- Complete skill authoring reference (frontmatter, descriptions, triggers, string substitutions, calibration)
- [skill-structure.md](references/skill-structure.md) -- Directory layout, progressive disclosure, scripts
- [dialog-contract.md](references/dialog-contract.md) -- Standard pattern for user interactions

## Skill Authoring Checklist

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
- [ ] No redundant sections -- each concept lives in one place

**Structure**
- [ ] Frontmatter includes `name` and `description` (both required)
- [ ] `description` and `argument-hint` use YAML block scalars (`>-` or `|`)
- [ ] `argument-hint` present if skill accepts arguments
- [ ] `user-invocable: false` set for internal skills accessed only through routing commands (do NOT use `disable-model-invocation` -- it blocks the `Skill` tool)
- [ ] All `depends-on` entries validated via `uv run $SKILL_DIR/scripts/validate-deps.py check`
- [ ] Gotchas section for non-obvious environment facts
- [ ] Templates/checklists for multi-step workflows
- [ ] Validation loops for quality-critical tasks

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
  version: "1.0"
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

**Reference:**
- [skill-authoring.md](references/skill-authoring.md) -- Full "Parent Skill with Sub-Skills Pattern" section with structure, metadata, registry format, dispatch mechanism, and migration guide

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
