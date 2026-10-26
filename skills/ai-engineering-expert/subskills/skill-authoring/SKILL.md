---
name: skill-authoring
description: >-
  Methodology and structural standards for authoring LSZ skills — progressive disclosure, frontmatter schemas, trigger calibration, dependency metadata, and verification gates. Use when creating, modifying, auditing, or refactoring skills.
metadata:
  managed-by: ai-engineering-expert
---

# Skill Authoring

Structural methodology for authoring, curating, and verifying skills.

## Philosophy & Foundation

Skills encode persistent meta-behavior for autonomous agents.
A skill exists to wrangle determinism out of stochastic models.
Its root virtue is **Predictability**.
Meta-behavior is load-bearing.
A flawed skill corrupts every future session where it triggers.
Authoring therefore requires mutual curation before execution.
Never guess user intent.
Never improvise architecture.

### Dual Taxonomy

| Class | Shape | Budget |
| --- | --- | --- |
| Workflow | Philosophy first, then ordered phases | ≤150 lines per phase, ≤500 total |
| Knowledge | Mental model first, then patterns and gotchas | ≤500 lines total |

Orchestration is a workflow pattern, not a third class.
The `manage` and `managed-by` fields are context routing, not a taxonomy.

### Rules vs Skills

| Attribute | Rules | Skills |
| --- | --- | --- |
| Context tax | Always loaded | Loaded on demand |
| Content | Defaults and invariants | Procedures, patterns, scripts |
| Expression | State the rule directly | Explain with examples |

Use rules for universal preferences.
Use skills for specialized workflows and deep reference material.
Deep mechanics live in [references/skill-authoring.md](references/skill-authoring.md).

## Sibling Boundaries

| Sibling | Use for |
| --- | --- |
| `grilling` (when installed) | Intent probing and decision-tree dialogue |
| `scaffold` | Interactive CLI generators with single-question dialogs |
| `subagent-engineering` | Dispatch topology, contracts, and model routing |
| `verification` | Gate synthesis, EDD anchors, and test design |
| `plain-language` | Sentence grammar and STE-100 vocabulary |
| `ste100.py` | Deterministic sentence-length and prose linting |
| `context-load-policy` | Description budgets, invocation classes, and platform sync |
| `writing-for-agents` | Pointers, hierarchy, completion criteria, and pruning |

Load `writing-for-agents` before drafting any agent-consumed document.
This holds even when the primary domain is `skill-authoring`.

## Operational Workflow

Workflow: Phase 1 → Phase 2 → Phase 3.

### Phase 1: Settle Intent Contract

Discover workspace facts first.
Inspect files, dependencies, linters, and git history before asking.
Query the decision frontier in numbered rounds.
Recommend one default per question.
Wait for user confirmation before drafting.

| Question | Intent Contract field |
| --- | --- |
| Goal and scope | Problem, plus explicit non-goals |
| Taxonomy class | Non-negotiable constraint |
| Verification anchors | Proposed outcome |
| Behavioral scenarios | Proposed outcome |
| Context footprint | Affected seams |

Lock these four fields before advancing:

- **Problem**: concrete deficiency, friction, or regression.
- **Proposed Outcome**: observable behavior, plus Given/When/Then cases and verification anchors.
- **Affected Seams**: skill boundaries, trigger collisions, and parent-subskill wiring.
- **Non-Negotiable Constraints**: taxonomy class, token budget, platform support, and explicit non-goals.

The user confirmation gate locks the contract. The orchestrator owns this phase.
Interactive CLI generators use single-question dialogs instead.
See `scaffold`.

### Phase 2: Draft & Structure Contract

Resolve your role before editing:

- If you are the orchestrator, then dispatch an implementer subagent.
- Pass the locked Intent Contract as a durable artifact path.
- If you are the implementer, then execute these steps directly.
- Do not dispatch another implementer from an implementer.
- If no subagent facility exists, then execute inline and record the deviation.

Load `writing-for-agents` before drafting the body.

#### Step 1: Scaffold and Layout

Run the canonical lifecycle tool:

```bash
uv run $SKILL_DIR/scripts/skill.py add <name>
uv run $SKILL_DIR/scripts/skill.py add <name> --parent <parent> --description "<text>"
```

The tool creates `skills/<name>/SKILL.md` for a top-level skill.
For a subskill, it creates `skills/<parent>/subskills/<name>/SKILL.md`.
It wires `metadata.manage` on the parent and writes `managed-by` for a subskill.
Use `skill.py` for `depend`, `manage`, `rename`, and `remove` changes.
Do not create the directory by hand or duplicate wiring with `validate-deps.py rename`.
**Completion criterion:** `test -f` exits 0 on the created path.

#### Step 2: Calibrate Frontmatter

Use the folded block scalar `>-`.
Apply the tripartite formula:

1. **What it is**: role anchor noun in the first 50 characters.
2. **What it does**: third-person present action verbs.
3. **When to use**: `Use when...` plus concrete symptom keywords.

Add an optional negative boundary.
Write `Do not use for X. Defer to Y.`
Keep the description at or below 300 characters.
Add `argument-hint`, `disable-model-invocation`, or `metadata` only when needed.
**Completion criterion:** `validate-deps.py lint` exits 0.
Also run `validate-deps.py context-check`.
Require exit 0 and a PASS row for the skill.
Treat warnings as advisory, not proof.

#### Step 3: Author the Body

Match the body to the taxonomy signature:

- **Workflow**: philosophy and invariants first, then ordered phases.
- **Knowledge**: mental model and invariants first, then patterns and gotchas.
- Never invent a workflow for reference material.

Keep each procedural sentence at or below 25 words.
End every step with an observable completion criterion.
**Completion criterion:** `rg -n '^## ' skills/<name>/SKILL.md` lists the signature headings.

#### Step 4: Wire Resources

Anchor prose paths with `$SKILL_DIR`.
Use relative markdown links for reading.
Keep references one level deep from `SKILL.md`.
Make scripts self-contained with `uv run` and PEP 723 metadata.
**Completion criterion:** a reviewer confirms every link resolves and prose paths use `$SKILL_DIR`.
No link checker exists today, so this check is reviewer-only.

### Phase 3: Verify & Gate Execution

Run the native verification suite from the project root:

```bash
# Frontmatter syntax, scalar conventions, and name collisions
uv run $SKILL_DIR/scripts/validate-deps.py lint

# Description budget (≤300 chars)
uv run $SKILL_DIR/scripts/validate-deps.py context-check

# Plain English and STE-100 linting (per file)
uv run $SKILL_DIR/scripts/ste100.py skills/<name>/SKILL.md
```

Run these gates when their condition holds:

```bash
# After a dependency, move, or rename change. Validates depends-on only.
uv run $SKILL_DIR/scripts/validate-deps.py check

# Only when targeted tests exist
uv run pytest tests/ai-engineering-expert tests/test_validate_deps.py
uv run pytest tests/<name>
```

Run the full repo gate before handoff:

```bash
bash scripts/check.sh
```

- `check` validates `depends-on` only. It does not validate `manage` wiring.
- `context-check` scans the whole tree. It has no working single-skill mode.
- `ste100.py` enforces 25 words for every sentence.
- CI lints 7 named files, not the whole skill tree.

#### Semantic Gate

Dispatch an adversarial Skeptic subagent.
Review these checks:

- **EDD anchors**: each deterministic goal has a script or test.
- **Symptom grounding**: `Use when...` uses user problem terms.
- **BDD coverage**: happy path, edge cases, and failure modes.
- **Default selection**: one clear default, not an open menu.
- **Context cleanliness**: no environment-specific noise.
- **Link integrity**: every markdown reference resolves.
- **Path anchoring**: prose uses `$SKILL_DIR`.

## References

- [skill-authoring.md](references/skill-authoring.md) -- Deep mechanics: frontmatter schemas, worked examples, lifecycle tooling, and gate details.
- [skill-diagnosis.md](references/skill-diagnosis.md) -- Failure archetypes, trigger misses, collisions, and the evidential ledger.
- [skill-structure.md](references/skill-structure.md) -- Directory layout, progressive disclosure, and scripts.
- [context-load-policy.md](references/context-load-policy.md) -- Description budgets, invocation classes, and platform sync.
- [glossary.md](references/glossary.md) -- Skill authoring terminology.
- [writing-for-agents](../writing-for-agents/SKILL.md) -- Agent-document hierarchy, pointers, and pruning.
