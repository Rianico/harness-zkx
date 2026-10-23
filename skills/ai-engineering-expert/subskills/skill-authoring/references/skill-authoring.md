# Skill Authoring Reference

Complete reference for authoring skills in the LSZ harness.

**Default standard: the open Agent Skills spec ([agentskills.io](https://agentskills.io)). The root steering file is `AGENTS.md` ([agents.md](https://agents.md)).** Claude Code and Pi frontmatter attributes are enhancements layered on that base. Where enhancements diverge, Pi's semantics are the default (Pi implements the spec, warns on unknown fields, and strips `disable-model-invocation: true` skills from model context entirely).

---

## Part I: Authoring Philosophy

### 1. Rules vs Skills Boundary (The Context Tax)

Rules and skills serve fundamentally different purposes in the agent harness. Understanding this boundary is critical for designing a maintainable, context-efficient system.

| Dimension | Rules | Skills |
|---|---|---|
| **Loading** | Always-on (injected every prompt) | On-demand (loaded only when triggered) |
| **Token Cost** | Deducted from every conversation | Consumed only when invoked |
| **Purpose** | Universal preferences & defaults | Specialized workflows & deep domain expertise |
| **Content** | WHAT to choose (concise directives) | HOW to execute (procedures, gotchas, examples) |
| **Knowledge Type** | Personal taste, baseline reminders | Non-obvious, experiential, framework-specific |

#### Rules Design Principles

Rules are **always loaded** into context. Every rule token competes for attention with conversation history and code:

1. **Conciseness is Mandatory:** Rules must justify their token tax on every single turn.
   - *Good:* `- **pytest**: Run with 'uv run pytest -q'`
   - *Bad:* Long paragraphs explaining why pytest is preferable to unittest.
2. **State Defaults, Do Not Explain:** Rules declare settled decisions. They do not teach or justify.
   - *Good:* `Use FastAPI for new REST services.`
   - *Bad:* Three sentences explaining OpenAPI generation, async performance, and Pydantic integration.
3. **Encode Settled Taste:** Rules capture decisions you never want to debate:
   - Tool choices: `uv` over `pip`, `ruff` over `black`, `basedpyright` over `pyright`.
   - Coding preferences: `pytest -q` by default, file-level lint suppressions over global ignores.

#### Skills Design Principles

Skills are **loaded on-demand**. They can provide deep procedural steps, worked code examples, and trade-off analyses:

1. **Non-Obvious Experiential Knowledge:** Skills teach what the LLM might forget, misunderstand, or execute poorly.
   - *Example:* Demonstrating why blocking I/O inside `async def` freezes the asyncio event loop.
2. **Patterns with Code Shapes:** Skills show concrete execution shapes rather than abstract advice.
   - *Example:* Auditing Django N+1 queries using `select_related` and `prefetch_related`.
3. **Framework Gotchas & Invariants:** Skills capture non-obvious failure modes (e.g., PyTorch `optimizer.zero_grad()` placement).
4. **Architectural Seams:** Skills explain trade-offs and structural constraints.

#### Boundary Identification Checklist

| Evaluation Question | Rule | Skill |
|---|---|---|
| Should this instruction apply to EVERY turn in every conversation? | Yes | No |
| Is it a one-line tool or styling preference? | Yes | No |
| Does the model already understand the concepts perfectly? | Yes | No |
| Does the procedure require code examples, scripts, or templates? | No | Yes |
| Is it framework-specific or domain-specific? | No | Yes |
| Might the model make subtle, catastrophic assumptions without it? | No | Yes |

#### The Expertise Routing Pattern

Rules can delegate to skills for complex scenarios:

```markdown
## Expertise Routing

For complex patterns and domain gotchas, invoke the expert skill:
/python-expert [async|testing|django|pytorch]
```

This keeps rules lean while ensuring deep knowledge is available when needed.

---

### 2. Dual Taxonomy of Skills

All skills in LSZ belong to one of two structural categories. Classification determines execution shape and budget:

```
                  ┌───────────────────────────────┐
                  │        SKILL TAXONOMY         │
                  └───────────────┬───────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     WORKFLOW SKILLS (Action)    │       │   KNOWLEDGE SKILLS (Reference)  │
├─────────────────────────────────┤       ├─────────────────────────────────┤
│ • Procedural execution steps    │       │ • Domain expertise & gotchas    │
│ • State transitions & phases    │       │ • Methodology & best practices  │
│ • Artifact generation contracts │       │ • No state machine transitions  │
│ • Budget: ≤150 lines per phase  │       │ • Budget: ≤500 lines total      │
└─────────────────────────────────┘       └─────────────────────────────────┘
```

#### Workflow Skills (Procedural)

Use for multi-phase tasks with concrete input/output contracts.
- **Structural Signature:** **Philosophy First, Then Workflow**. Anchor the mental model and invariants before describing state transitions and commands.
- **1-Phase Workflow:** Focused, self-contained task with low ambiguity (e.g., `handoff`, `skill-stocktake`). Budget: ≤150 lines.
- **N-Phase Workflow:** Manages state transitions, gates, and sequential execution (e.g., `tdd-cycle` with RED/GREEN/REFACTOR). Budget: ≤150 lines per phase, capped at 500 lines.

#### Knowledge Skills (Reference)

Use for guides, domain invariants, architectural patterns, and specialized constraints.
- **Structural Signature:** **Mental Model & Invariants First, Then Reference Patterns & Gotchas**.
- **No Artificial Workflows:** Never force a procedural workflow onto reference knowledge. Structure the body by domain topics, concrete code shapes, anti-patterns, and framework gotchas.
- Loaded just-in-time when entering a specific domain.
- Examples: `ai-engineering-expert`, `python-expert`, `codebase-design`. Budget: ≤500 lines.

#### Context Routers (`manage` / `managed-by`)

Parent skill clusters (e.g., `write` managing `write-article` and `write-publish`, or `scaffold` managing its language subskills) are **information-architecture context routers**, not an intrinsic taxonomy type.
- The parent acts as an index to avoid polluting the root catalog.
- The parent dispatches subskills via `Read`, hiding subskills from root auto-discovery.

#### When to Embed Logic Directly in an Agent Prompt

Only embed workflow logic directly into an Agent's system prompt if the workflow is:
1. **Atomic:** Does one specific task without loops or retries.
2. **Universal:** Does not vary across languages or frameworks.
3. **Short:** Under 300 words.

If a workflow violates any of these three constraints, author it as a skill.

---

### 3. Progressive Disclosure & Token Economics

Skills share the context window with conversation history, system prompts, and tools. Every token competes for attention:

- **Level 1 (Metadata):** `name` and `description` are loaded on every turn (~100 words). Must stay concise.
- **Level 2 (Skill Body):** `SKILL.md` is loaded only when triggered. Hard budget: ≤500 lines (5,000 tokens).
- **Level 3 (Bundled Resources):** `references/` and `scripts/` are loaded only on demand (unlimited).

#### The 80/20 Pointer-First Rule

Keep 20% of essential decision logic in `SKILL.md`. Place the remaining 80% of deep reference details behind markdown pointers in `references/`:
- Keep file references **one level deep** from `SKILL.md`.
- Never create nested reference chains (`SKILL.md` → `ref1.md` → `ref2.md`), as LLMs may fail to traverse secondary links.

---

### 4. Calibration: Freedom vs Prescriptiveness

Calibrate instruction specificity to task fragility:

- **High Freedom (Text Guidelines):** Use when multiple valid approaches exist and contextual judgment is required (e.g., qualitative code review, architecture trade-offs).
- **Low Freedom (Specific Scripts):** Use when operations are fragile, consistency is critical, or syntax errors cause cascading failures (e.g., database migrations, crypto operations, release tagging).
- **Provide Defaults, Not Menus:** Never give the model an open-ended menu of equivalent choices. Recommend a concrete default with an option to diverge.

---

### 5. Content Integrity & Model Competence

- **Assume Baseline Competence:** Do not explain basic programming concepts (e.g., "JSON is a key-value format" or "git commit saves changes"). Jump directly to project conventions, non-obvious gotchas, and procedural order.
- **Avoid Time-Sensitive Sediment:** Avoid prose like "If before August 2025, use API v1". State the current standard directly, or place legacy migrations in collapsible HTML sections.

---

## Part II: Operational Authoring Workflow

```
┌─────────────────────────────────┐
│ Phase 1: Intent Curation        │ Query design tree frontier with recommended defaults
└────────────────┬────────────────┘
                 ▼
┌─────────────────────────────────┐
│ Phase 2: Schema & Frontmatter   │ Apply tripartite formula, block scalars, ≤300 chars
└────────────────┬────────────────┘
                 ▼
┌─────────────────────────────────┐
│ Phase 3: Parent-Subskill Layout │ Configure manage/managed-by, dispatch via Read
└────────────────┬────────────────┘
                 ▼
┌─────────────────────────────────┐
│ Phase 4: Verification & Gates   │ Pass lint, context-check, STE-100, and pytest
└─────────────────────────────────┘
```

---

### Phase 1: Intent Curation (Grilling Pattern)

Because skills encode persistent agent behaviors, agents must never assume requirements silently. We use the **Grilling Pattern**:

1. **Discover Facts First:** Inspect the workspace, existing skills, dependencies, and test commands before asking questions.
2. **Identify the Decision Frontier:** Map open architectural choices as a tree.
3. **Ask in Numbered Rounds:** Query open choices with recommended defaults:
   - **Scope & Non-Goals:** What problem does this solve? What is explicitly out of scope?
   - **Classification:** Is this a procedural Workflow or reference Knowledge?
   - **Verification Anchors:** Which outputs are verified deterministically, and which semantically?
   - **Behavioral Scenarios:** What BDD cases must hold?
4. **Lock Shared Understanding:** Secure user confirmation before creating files.

Interactive CLI generators use single-question dialogs instead. See `scaffold`.

---

### Phase 2: Schema & Frontmatter Mechanics

#### Naming Conventions

The `name` field must satisfy these hard constraints:
1. 1–64 characters, lowercase alphanumeric and hyphens only (`^[a-z0-9-]+$`).
2. Must not start or end with a hyphen (`-`).
3. Must not contain consecutive hyphens (`--`).
4. Must match the skill's directory name exactly.

**Taxonomy-Based Naming Patterns:**
- **Knowledge (Methodology/Spine):** Standardize on `[topic]-expert` (e.g., `python-expert`, `tdd-expert`).
- **Knowledge (Facts/Reference):** Use bare nouns or plural concepts (e.g., `adr`, `triage-labels`, `design-system`).
- **Workflows:** Use action verbs or prepositional phrases (e.g., `handoff`, `update-docs`, `tdd-cycle`).

#### Description Requirements (The Tripartite Formula)

The `description` field is mandatory and must satisfy the **Tripartite Formula**:
1. **What it is (Anchor Noun):** Category noun defining nature and domain in the first 50 characters (e.g., *"Architecture decision record manager..."*, *"Adversarial code review gate..."*).
2. **What it does (Active Capabilities):** Concrete third-person present tense action verbs (e.g., *"initiates, links, and supersedes ADRs"*).
3. **When to use (Activation Trigger):** Explicit trigger condition starting with `Use when...`, embedded with concrete symptom keywords (e.g., *flaky tests*, *drift*, *errors*, *debugging*).
4. **Negative Boundary (Optional Lever):** Add `Do not use for X; defer to Y` when adjacent skills collide.

**Frontmatter Scalar Convention:**
- Always format `description` with YAML folded block scalar `>-` (strip trailing newlines).
- Format `argument-hint` with literal block scalar `|-`.
- Enforce the **≤ 300 characters** hard budget in the LSZ harness.

**Worked Description Examples:**

*Good Workflow Description (279 chars):*
```yaml
description: >-
  ADR lifecycle manager via `adr` CLI. Initiates, links, supersedes, and verifies architecture decision records. Use when documenting architectural decisions, evaluating technical trade-offs, or diagnosing ADR drift. Defer to git for commit management.
```

*Good Knowledge Description (288 chars):*
```yaml
description: >-
  Adversarial crux code review gate auditing test refutability, domain state invariants, failure resiliency, and Clean Architecture boundaries. Evaluates semantic soundness beyond test passes. Use when reviewing code changes, auditing PRs, checking invariants, or verifying goal attainment.
```

#### Base Fields (Agent Skills Spec)

| Field | Required | Type | Purpose |
|---|---|---|---|
| `name` | **Required** | string | Skill identifier (1–64 chars, matches directory) |
| `description` | **Required** | string | Tripartite routing text (≤300 chars, `>-` scalar) |
| `compatibility` | Optional | string | Environment requirements (max 500 chars) |
| `allowed-tools` | Optional | string or list | Pre-approved tools (e.g., `Bash(git:*) Read Write`) |
| `metadata` | Optional | mapping | Structural declarations (see below) |

#### Metadata Conventions

The `metadata` mapping supports structural relationships:

```yaml
metadata:
  manage: [git, python, rust]        # Parent skill: managed subskill names
  managed-by: scaffold               # Subskill: parent skill name
  depends-on: [eval-gate, code-review] # Hard dependencies required for execution
  credits:                           # Upstream provenance for ported skills
    source: https://github.com/org/repo/blob/main/skills/upstream/SKILL.md
    author: upstream-author
    version: main
    note: Adapted for LSZ harness
```

**`depends-on` Rules:**
- List hard dependencies only: skills whose absence breaks execution.
- Add `depends-on` when this skill invokes another skill, reads its scripts, or relies on its output contract.
- Keep optional alternatives and reading references in markdown prose.
- Run `uv run $SKILL_DIR/scripts/validate-deps.py related <skill-name>` before renaming or removing a skill.

#### Platform Enhancement Fields

Claude Code and Pi extend the base spec with enhancement attributes. Pi's semantics are the default:

| Field | Platform | Type | Purpose |
|---|---|---|---|
| `disable-model-invocation` | Claude / Pi | boolean | When `true`, removes skill from model context entirely; callable only via user slash command |
| `argument-hint` | Claude Code | string | Autocomplete syntax hint for arguments (`\|-` scalar) |
| `arguments` | Claude Code | string or list | Named positional arguments substituted via `$name` |
| `user-invocable` | Claude Code | boolean | Controls appearance in user slash menu (default: `true`) |
| `model` | Claude Code | string | Override model (`opus`, `sonnet`, `haiku`, `inherit`) |
| `effort` | Claude Code | string | Thinking effort level (`low`, `medium`, `high`, `xhigh`, `max`) |
| `context` | Claude Code | string | Set to `fork` for subagent isolation |
| `paths` | Claude Code | list | Glob patterns limiting activation |

#### Path & Variable Substitutions

Use `$SKILL_DIR` as the universal path anchor in **prose**:
- Scripts: `uv run $SKILL_DIR/scripts/<name>.py`
- References: `$SKILL_DIR/references/<name>.md`
- Markdown Links: Use standard relative-to-file links: `[name](references/<name>.md)`.

---

### Phase 3: Parent-Subskill Architecture

When multiple related capabilities share a domain, organize them under a parent cluster to prevent root catalog bloat:

```
skills/<parent-name>/
├── SKILL.md              # Parent router with manage metadata + dispatch table
├── subskills/
│   ├── <subskill-1>/
│   │   ├── SKILL.md      # Full skill with managed-by: <parent-name>
│   │   ├── references/
│   │   └── scripts/
│   └── <subskill-2>/
│       └── SKILL.md
```

#### Invariants

1. **Subskill Name Collision Rule:** A subskill name must NOT collide with any top-level skill name. Tooling indexes skills by name. Duplicates cause silent collision.
2. **Dispatch via `Read`, Never `Skill` Tool:** Nested subskills under `subskills/` are deliberately hidden from model root discovery. The parent must dispatch them using `Read`:

```markdown
## Dispatch Table

| Subskill | Action |
|---|---|
| `article` | Read `$SKILL_DIR/subskills/article/SKILL.md` and execute its instructions |
| `publish` | Read `$SKILL_DIR/subskills/publish/SKILL.md` and execute its instructions |
```

---

### Phase 4: Deterministic Verification & Static Gates

Before publishing or committing any skill, execute the 5 verification gates:

```bash
# Gate 1 & 2: Frontmatter syntax, scalar conventions, and name collisions
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py lint

# Gate 3: Description budget (≤300 chars) and tripartite formula
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py context-check

# Gate 4: Plain English and STE-100 deterministic linting
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/ste100.py skills/<skill-name>/SKILL.md

# Gate 5: Unit test integrity
uv run pytest tests/ai-engineering-expert
```

All 5 gates must return **PASS** with zero errors.
