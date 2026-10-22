---
name: skill-authoring
description: >-
  Methodology and structural standards for authoring LSZ skills — progressive disclosure, frontmatter schemas, trigger calibration, dependency metadata, and verification gates. Use when creating, modifying, auditing, or refactoring skills.
metadata:
  managed-by: ai-engineering-expert
---

# Skill Authoring

Structural methodology for authoring, curating, and verifying skills.

## Philosophy & Core Mental Model

### The Nature of Skills

Skills establish persistent meta-behavior for autonomous agents. A skill exists to wrangle determinism out of stochastic models. Its root virtue is **Predictability**.

Meta-behavior is load-bearing. A flawed skill corrupts every future session where it triggers. Therefore, authoring a skill requires rigorous mutual curation before execution. Never guess user intent or improvise architecture.

### The Dual Taxonomy

Every skill falls into one of two operational categories:

1. **Workflow Skills (Procedural)**: Step-by-step procedures to produce artifacts or change system state. Follows **Philosophy First, Then Workflow**. Anchor the core mental model and invariants before detailing sequential execution phases.
2. **Knowledge Skills (Reference)**: Mental models, domain constraints, heuristics, and expert patterns loaded just-in-time. Follows **Mental Model & Invariants First, Then Reference Patterns & Gotchas**. Never invent artificial procedural workflows for reference material.

> **Note on Orchestration & Management**: Orchestration is a multi-agent workflow pattern, not a distinct taxonomy type. The `manage` and `managed-by` metadata declarations provide structural context routing (hiding subskills under `subskills/` to eliminate root context load), rather than an intrinsic skill class.

### Rules vs Skills Boundary (Context Economics)

Rules and skills serve different context-cost economics:

| Attribute | Rules (`rules/`) | Skills (`skills/`) |
| :--- | :--- | :--- |
| **Context Tax** | Always loaded into root prompt; permanent token cost. | Loaded on demand; zero token cost until triggered. |
| **Content** | Tool defaults, styling preferences, invariant constraints. | Procedural steps, reference patterns, executable scripts. |
| **Expression** | State the rule directly; do not explain rationale. | Explain how to implement with concrete examples. |

Use rules for universal preferences that apply unconditionally. Use skills for specialized workflows, domain gotchas, and progressive reference material.

### The Grilling Principle

Because skills encode persistent agent behaviors, agents must never assume requirements silently. We use the **Grilling Pattern**, documented in the `grilling` skill where installed. Map the design space as a tree. Query the frontier of open decisions with recommended answers. Establish shared understanding before generating files.

---

## Operational Workflow

```
Phase 1: Grill & Curate Intent
               │
               ▼
Phase 2: Draft & Structure Contract
               │
               ▼
Phase 3: Verify & Deterministic Gate
```

### Phase 1: Grill & Curate Intent

Interview the user systematically to settle the **design tree** before drafting:

1. **Discover Environment Facts First**: Finding facts is the agent's job, never the user's. Inspect workspace files, dependencies, linters, and git history before asking questions.
2. **Identify the Decision Frontier**: The frontier comprises decisions whose prerequisites are already settled.
3. **Ask in Numbered Rounds**: Present open frontier decisions clearly with a recommended answer for each:
   - **Goal & Scope**: What problem does this skill solve? What are the concrete non-goals?
   - **Category**: Is this an executable Workflow or domain Knowledge?
   - **Verification Anchors (GDD/EDD)**: Which outputs are measurable with deterministic scripts, and which remain semantic?
   - **Behavioral Scenarios (BDD)**: What Given/When/Then cases must hold?
   - **Context Footprint**: Does this belong in a parent-subskill cluster (`manage`) or standalone?
4. **Lock Shared Understanding**: Wait for user confirmation before advancing to file generation.

Interactive CLI generators use single-question dialogs instead. See the `scaffold` skill.

### Phase 2: Draft & Structure Contract

#### Directory Layout & Budget

```
skills/<skill-name>/
├── SKILL.md          # Primary entry point (under 500 lines)
├── references/       # Deep reference docs (one level deep)
└── scripts/          # Deterministic executable scripts (uv run)
```

- Keep `SKILL.md` under 500 lines. Place deep reference material in `references/`.
- Progressive disclosure: Level 1 metadata (frontmatter) -> Level 2 body (`SKILL.md`) -> Level 3 deep assets (`references/`, `scripts/`).

#### Body Structural Signatures

Structure the body based on the skill's taxonomy type:

- **Workflow Skills (Philosophy First, Then Workflow):**
  1. *Philosophy & Foundation:* Core mental model, invariants, design constraints, anti-patterns.
  2. *Operational Workflow:* Sequential phases, commands, scripts, deterministic gates.
- **Knowledge Skills (Mental Model & Invariants First, Then Reference):**
  1. *Core Mental Model:* Domain invariants, architectural trade-offs, conceptual foundations.
  2. *Topical Patterns & Gotchas:* Worked code shapes, anti-patterns, framework-specific edge cases.

#### Required Frontmatter

Frontmatter follows the open Agent Skills spec ([agentskills.io](https://agentskills.io)):

```yaml
---
name: skill-name
description: >-
  Category noun defining role. Active verbs articulating capabilities. Use when concrete symptoms, pain points, or triggers arise.
---
```

- `name`: Required. Must match directory name (1-64 chars, lowercase alphanumeric and hyphens).
- `description`: Required. Machine-readable trigger. Enforce the **Tripartite Formula**:
  1. **What it is (Role Anchor)**: Front-load a category noun in the first 50 chars.
  2. **What it does (Active Capabilities)**: Third-person present tense verbs defining concrete outputs.
  3. **When to use (Activation Boundary)**: Mandatory condition starting with `Use when...`. Embed concrete symptom keywords (e.g. *flaky tests*, *drift*, *crash*, *slow*) to bridge the user-to-tool semantic gap.
- **Strict Budget**: Hard limit ≤ 300 characters.
- **YAML Scalar**: Always use `>-` block scalars for `description` and `argument-hint` to prevent character escaping errors.

#### Key Optional Frontmatter Fields

- `arguments` + `argument-hint`: Declares named parameters. Format `argument-hint` using YAML block scalar `|-` or `>-` with syntax `<required>`, `[optional]`, `[opt=a|b]`, or `[--flag]` -- description (default: value).
- `disable-model-invocation`: Set `true` for user-only workflows. On Pi, this strips the skill from model context entirely, paying zero tokens. Do not use it for routing-command targets. It blocks the `Skill` tool.
- `user-invocable`: Set `false` for internal router projections.

#### Resource Path Convention

- `$SKILL_DIR` is the path anchor for all skill-owned resources.
- Prose references: Always `$SKILL_DIR/references/<module>.md`.
- Markdown links: Always relative like `[text](references/<module>.md)`.
- Scripts: Place in `scripts/` and invoke via `uv run $SKILL_DIR/scripts/<script>.py`. Handle errors internally. Never punt error interpretation to the LLM.

#### Metadata Conventions & Routing

- `manage` and `managed-by`: Used for parent-subskill clusters. Subskills are hidden in `subskills/` and dispatched via `Read` tool. Dispatch on task match or explicit domain, never domain-only.
- `depends-on`: Declare hard dependencies on other skills. Add `depends-on` when a skill invokes or loads another skill, reads resources, consumes artifacts, or requires an output contract.
- `credits`: Attribution for ported skills (`source`, `author`, `version`, `note`). `validate-deps.py lint` checks the schema.

### Phase 3: Verify & Deterministic Gate

Run all deterministic gates before publishing:

1. **STE-100 Linting**:
   ```bash
   uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/ste100.py skills/<name>/SKILL.md
   ```
2. **Metadata & Dependency Check**:
   ```bash
   uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py lint
   uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py check
   ```
3. **Context Budget Verification**:
   ```bash
   uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py context-check
   ```

---

## Unified Skill Authoring Checklist

Validate the skill against these gates before publishing:

**Core Quality**
- [ ] BDD scenarios cover Happy Path, Edge Case, and Error Case
- [ ] Deterministic goals have corresponding evaluation scripts in `scripts/` (EDD)
- [ ] Semantic goals have an explicit verification plan (e.g. Adversarial Skeptic Review)
- [ ] Description follows the Tripartite Formula (What it is, What it does, When to use via `Use when...`)
- [ ] Description embeds symptom keywords and stays within the 300-character budget
- [ ] `SKILL.md` body is under 500 lines, with deep reference content in `references/`
- [ ] Environment facts, config, and setup details are kept out of `SKILL.md` body

**Structure & Mechanics**
- [ ] `name` matches directory name
- [ ] Block scalars (`>-` or `|-`) format `description` and `argument-hint`
- [ ] Resource links use relative markdown paths, while prose paths use `$SKILL_DIR`
- [ ] Scripts use `uv run` with inline dependencies and handle errors internally
- [ ] `depends-on` entries verified via `validate-deps.py check`
- [ ] Subskills in `subskills/` are wired with `manage` and `managed-by`
- [ ] All files pass `ste100.py` with 0 issues

---

## Skill Gotchas

- **Vague descriptions**: "Helps with code" fails routing. Use concrete symptom keywords.
- **Wrong POV**: First-person ("I can help...") causes discovery failures. Always write in third-person.
- **Hero-mode execution**: The orchestrator doing direct edits instead of delegating to subagents. Always dispatch.
- **Overloading `SKILL.md`**: Keep under 500 lines. Move depth to `references/`.
- **Deep nesting**: References must be exactly one level from `SKILL.md`.
- **Missing validation loops**: Destructive edits without verification gates produce silent failures.
- **Interrogating the user**: Asking questions for facts already present in the workspace. Always inspect first.

---

## References

- [skill-authoring.md](references/skill-authoring.md) -- Full reference: frontmatter schemas, worked description examples, credits schema, compression rules, string substitutions, calibration.
- [skill-diagnosis.md](references/skill-diagnosis.md) -- Trigger misses, collisions, execution loops, dead skills, and the evidential trigger ledger.
- [skill-structure.md](references/skill-structure.md) -- Directory layout, progressive disclosure, scripts.
- [glossary.md](references/glossary.md) -- Invocation classes, description budget, context load, progressive disclosure.
- [writing-for-agents](../writing-for-agents/SKILL.md) -- Agent-document writing: hierarchy, pointers, leading words, pruning.
