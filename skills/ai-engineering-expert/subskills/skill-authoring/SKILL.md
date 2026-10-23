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

### Router Skills for Invocation Management

When user-invoked skills (`disable-model-invocation: true`) multiply past human memory, cognitive load accumulates.
Resolve this using a **router skill**:
- Create a single user-invoked skill that indexes related specialized skills.
- Detail when to reach for each managed skill without registering them into root context.
- Keep the router itself user-invoked to avoid always-on context load.

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

### Authoring Anti-Patterns (Gotchas)

Avoid these core failure modes when conceiving and authoring skills:
- **Vague descriptions**: "Helps with code" fails routing. Always embed concrete symptom keywords.
- **Wrong POV**: First-person ("I can help") causes discovery failures. Always write in third-person.
- **Hero-mode execution**: The orchestrator doing direct edits instead of delegating to subagents. Always dispatch.
- **Overloading `SKILL.md`**: Keep under 500 lines. Move deep details to `references/`.
- **Deep nesting**: References must be exactly one level from `SKILL.md`.
- **Missing validation loops**: Destructive edits without verification gates produce silent regressions.
- **Interrogating the user**: Asking questions for facts already in the workspace. Always inspect first.

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

Execute the four drafting steps in order. Deep frontmatter schemas and edge cases live in [references/skill-authoring.md](references/skill-authoring.md).

#### Step 1: Initialize Directory & Layout
Create `skills/<skill-name>/` matching `name` (1-64 chars, lowercase alphanumeric, hyphens):
- `SKILL.md`: Main entry point (strictly under 500 lines).
- `references/`: Optional domain guides and specs (one level deep).
- `scripts/`: Optional deterministic helpers and gates.

#### Step 2: Draft & Calibrate Frontmatter
Scaffold minimal YAML frontmatter using folded block scalar `>-`:
```yaml
---
name: skill-name
description: >-
  Category noun defining role. Active verbs articulating capabilities. Use when concrete symptoms, pain points, or triggers arise.
---
```
- **Tripartite Formula**: 1. What it is (Role anchor noun in first 50 chars), 2. What it does (third-person present action verbs), 3. When to use (`Use when...` with symptom keywords).
- **Hard Budget**: Strictly ≤ 300 characters.
- **Optional Attributes**: Add `argument-hint` (`|-`), `disable-model-invocation: true` (user-only), or `metadata` (`manage`, `managed-by`, `depends-on`).

#### Step 3: Author Body by Structural Signature
Structure the markdown body according to its taxonomy class:
- **Workflow Skills (Philosophy First, Then Workflow)**:
  1. *Philosophy & Foundation*: Core mental model, invariants, design constraints.
  2. *Operational Workflow*: Ordered execution phases, scripts, and deterministic completion criteria.
- **Knowledge Skills (Mental Model & Invariants First, Then Reference)**:
  1. *Core Mental Model*: Domain invariants, architectural trade-offs, and rules.
  2. *Topical Guidance & Gotchas*: Worked code shapes, anti-patterns, framework gotchas. Never invent artificial operational workflows for reference material.

#### Step 4: Wire Resources & Paths
- Anchor prose paths with `$SKILL_DIR`: `$SKILL_DIR/scripts/<cmd>.py` or `$SKILL_DIR/references/<ref>.md`.
- Use relative markdown links for reading: `[text](references/<module>.md)`.
- Make scripts self-contained via `uv run` with PEP 723 inline dependencies. Handle errors internally.

### Phase 3: Verify & Deterministic Gate

Run automated scripts first, then perform qualitative semantic checks:

#### 1. Deterministic Verification Gate (Formal Substrate)
Execute the native verification suite from the project root:

```bash
# Gate 1 & 2: Frontmatter syntax, scalar conventions, and name collisions
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py lint

# Gate 3: Description budget (≤300 chars) and tripartite formula
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py context-check

# Gate 4: Plain English and STE-100 deterministic linting
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/ste100.py skills/<name>/SKILL.md

# Gate 5: Dependency resolution and manage/managed-by wiring
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py check

# Gate 6: Unit test integrity
uv run pytest tests/<name>  # or tests/ai-engineering-expert
```

All deterministic checks must pass with zero errors before moving to semantic review.

#### 2. Semantic Verification Gate (Semantic Reasoner)
Dispatch an adversarial Skeptic subagent to verify qualitative alignment:
- [ ] **EDD Anchors**: Does each deterministic goal have an evaluation script under `scripts/` or a test?
- [ ] **Symptom Grounding**: Does `Use when...` contain natural user problem terms rather than academic jargon?
- [ ] **BDD Scenario Coverage**: Do Given/When/Then scenarios cover the happy path, edge cases, and failure modes?
- [ ] **Default Selection**: Does the skill provide clear defaults rather than open menus?
- [ ] **Context Cleanliness**: Are environment-specific paths and setup noise kept out of the skill body?

---

## References

- [skill-authoring.md](references/skill-authoring.md) -- Full reference: frontmatter schemas, worked description examples, credits schema, compression rules, string substitutions, calibration.
- [skill-diagnosis.md](references/skill-diagnosis.md) -- Trigger misses, collisions, execution loops, dead skills, and the evidential trigger ledger.
- [skill-structure.md](references/skill-structure.md) -- Directory layout, progressive disclosure, scripts.
- [glossary.md](references/glossary.md) -- Skill authoring terminology: predictability, invocation classes, information hierarchy, steering, and pruning.
- [writing-for-agents](../writing-for-agents/SKILL.md) -- Agent-document writing: hierarchy, pointers, leading words, pruning.
- [context-load-policy.md](references/context-load-policy.md) -- Enforcement contract: hard CI gates, description budgets, platform sync mapping, regeneration. Use when a load-cost rule must be audited.
