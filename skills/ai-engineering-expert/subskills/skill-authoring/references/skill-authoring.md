# Skill Authoring Reference

Deep reference for authoring skills in the LSZ harness.

**Default standard: the open Agent Skills spec ([agentskills.io](https://agentskills.io)). The root steering file is `AGENTS.md` ([agents.md](https://agents.md)).** Claude Code and Pi frontmatter attributes are enhancements layered on that base. Where enhancements diverge, Pi's semantics are the default. Pi implements the spec, warns on unknown fields, and strips `disable-model-invocation: true` skills from model context entirely.

The entrypoint `SKILL.md` carries the 20% operational spine. This file carries the deep 80%.

---

## Part I: Authoring Philosophy

### 1. Rules vs Skills Boundary

Rules and skills spend different context budgets. Rules are always loaded. Skills are loaded on demand.

Use this boundary test:

| Question | Rule | Skill |
| --- | --- | --- |
| Does this apply to every turn in every conversation? | Yes | No |
| Is it a one-line tool or styling preference? | Yes | No |
| Does the model already understand the concept? | Yes | No |
| Does the procedure need code examples, scripts, or templates? | No | Yes |
| Is it framework-specific or domain-specific? | No | Yes |
| Could a subtle, catastrophic assumption appear without it? | No | Yes |

#### Rules Design Principles

1. **Conciseness is mandatory.** Every rule token competes for attention on every turn.
   - Good: `- **pytest**: Run with 'uv run pytest -q'`
   - Bad: A long paragraph explaining why pytest beats unittest.
2. **State defaults. Do not explain.** Rules declare settled decisions.
   - Good: `Use FastAPI for new REST services.`
   - Bad: Three sentences about OpenAPI, async performance, and Pydantic.
3. **Encode settled taste.** Capture decisions you never want to debate.
   - Tools: `uv` over `pip`, `ruff` over `black`, `basedpyright` over `pyright`.
   - Style: `pytest -q` by default, file-level suppressions over global ignores.

#### Skills Design Principles

1. **Non-obvious experiential knowledge.** Teach what the model might forget or execute poorly.
2. **Patterns with code shapes.** Show concrete execution shapes, not abstract advice.
3. **Framework gotchas and invariants.** Capture non-obvious failure modes.
4. **Architectural seams.** Explain trade-offs and structural constraints.

The entrypoint holds the short comparison table. Keep the full design rationale here only.

### 2. Dual Taxonomy

Every skill is either a Workflow skill or a Knowledge skill. The class determines the body signature and the budget.

#### Workflow Skills (Procedural)

Use for multi-phase tasks with concrete input and output contracts.

- **Structural signature:** philosophy first, then workflow.
- Anchor the mental model and invariants before state transitions and commands.
- **1-phase workflow:** focused, self-contained task. Budget: ≤150 lines.
- **N-phase workflow:** manages state transitions, gates, and sequence. Budget: ≤150 lines per phase, ≤500 lines total.

#### Knowledge Skills (Reference)

Use for guides, domain invariants, architectural patterns, and specialized constraints.

- **Structural signature:** mental model and invariants first, then reference patterns and gotchas.
- **No artificial workflows.** Never force a procedure onto reference knowledge.
- Structure by domain topics, code shapes, anti-patterns, and framework gotchas.
- Examples: `ai-engineering-expert`, `python-expert`, `codebase-design`. Budget: ≤500 lines.

#### Context Routers (`manage` / `managed-by`)

Parent clusters are information-architecture routers, not a third taxonomy.

- The parent indexes subskills to avoid polluting the root catalog.
- The parent dispatches subskills by reading their `SKILL.md`.
- Subskills use `metadata.managed-by: <parent>`.
- Parents use `metadata.manage: [<subskill>, ...]`.

### 3. Progressive Disclosure and Token Economics

Skills share the context window with conversation history, system prompts, and tools.

- **Level 1 (Metadata):** `name` and `description` load on every turn. Keep them short.
- **Level 2 (Skill Body):** `SKILL.md` loads when the skill triggers. Budget: ≤500 lines.
- **Level 3 (Bundled Resources):** `references/` and `scripts/` load on demand.

#### The 80/20 Pointer-First Rule

Keep 20% of essential decision logic in `SKILL.md`. Place the deep 80% behind markdown pointers.

- Keep file references one level deep from `SKILL.md`.
- Never create nested reference chains. Models may fail to traverse secondary links.
- One concept, one canonical home. Cross-link instead of copying.

### 4. Calibration: Freedom vs Prescriptiveness

Match instruction specificity to task fragility.

- **High freedom (text guidelines):** multiple valid approaches and contextual judgment. Use for qualitative review and architecture trade-offs.
- **Low freedom (specific scripts):** fragile operations, consistency demands, or cascading syntax failures. Use for migrations, crypto operations, and release tagging.
- **Provide defaults, not menus.** Recommend one concrete default with an option to diverge.

### 5. Content Integrity and Model Competence

- **Assume baseline competence.** Do not explain basic programming concepts.
- Jump to project conventions, non-obvious gotchas, and procedural order.
- **Avoid time-sensitive sediment.** State the current standard directly. Put legacy migrations in collapsible sections.

---

## Part II: Operational Authoring Workflow

The workflow has three phases. The entrypoint carries the same phases. Do not maintain a second phase model here.

### Phase 1: Settle Intent Contract

Skills encode persistent behavior. Never assume requirements silently.

1. **Discover facts first.** Inspect the workspace, existing skills, dependencies, and test commands.
2. **Identify the decision frontier.** Map open choices as a tree. A choice is open only when its prerequisites are settled.
3. **Ask in numbered rounds.** Recommend one default per question.
4. **Lock the Intent Contract.** Require explicit user confirmation before creating files.

The four contract fields:

- **Problem:** concrete deficiency, friction, or regression.
- **Proposed Outcome:** observable behavior, plus Given/When/Then cases and verification anchors.
- **Affected Seams:** skill boundaries, trigger collisions, and parent-subskill wiring.
- **Non-Negotiable Constraints:** taxonomy class, token budget, platform support, and explicit non-goals.

Interactive CLI generators use single-question dialogs. See `scaffold`.

### Phase 2: Draft and Structure Contract

Resolve the role before editing:

- The orchestrator dispatches an implementer with the contract artifact path.
- The implementer executes the steps below.
- An implementer never dispatches another implementer.
- Without a subagent facility, execute inline and record the deviation.

Load `writing-for-agents` before drafting the body.

#### 2.1 Scaffold and Layout with `skill.py`

`skill.py` is the canonical lifecycle tool. It owns deterministic file moves and frontmatter wiring. The model supplies intent: names, relationships, and descriptions.

```bash
# Create a top-level skill
uv run $SKILL_DIR/scripts/skill.py add <name> --description "<description>"

# Create a subskill under a parent
uv run $SKILL_DIR/scripts/skill.py add <name> --parent <parent> --description "<description>"

# Wire dependencies and hierarchy
uv run $SKILL_DIR/scripts/skill.py depend <skill> <dependency>
uv run $SKILL_DIR/scripts/skill.py manage <parent> <child>

# Rename or remove with cascade
uv run $SKILL_DIR/scripts/skill.py rename <old> <new> [--parent <parent>]
uv run $SKILL_DIR/scripts/skill.py remove <name> [--parent <parent>]
```

Rules:

- Use `skill.py` for scaffolding and wiring. Do not create directories by hand.
- `validate-deps.py rename` duplicates this tool. Prefer `skill.py`.
- `skill.py add` creates `skills/<name>/SKILL.md` for a top-level skill.
- It creates `skills/<parent>/subskills/<name>/SKILL.md` for a subskill.
- It wires `metadata.manage` on the parent and `managed-by` on a subskill.
- The basic directory anatomy lives in [skill-structure.md](skill-structure.md).

#### 2.2 Parent-Subskill Architecture

Use a parent cluster when related capabilities share a domain. This prevents root catalog bloat.

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

Invariants:

1. **Subskill name collision rule.** A subskill name must not collide with a top-level skill name. Tooling indexes skills by name. Duplicates cause silent collisions.
2. **Dispatch via `Read`, not the `Skill` tool.** Nested subskills are hidden from root discovery. The parent must read the subskill file.

```markdown
## Dispatch Table

| Subskill | Action |
| --- | --- |
| `article` | Read `$SKILL_DIR/subskills/article/SKILL.md` and execute its instructions |
| `publish` | Read `$SKILL_DIR/subskills/publish/SKILL.md` and execute its instructions |
```

#### 2.3 Naming Conventions

The `name` field must satisfy these constraints:

1. 1–64 characters, lowercase alphanumeric and hyphens only (`^[a-z0-9-]+$`).
2. Must not start or end with a hyphen.
3. Must not contain consecutive hyphens.
4. Must match the skill directory name exactly.

No script enforces these rules today. Treat them as reviewer checks.

Taxonomy-based naming patterns:

- **Knowledge (methodology or spine):** `[topic]-expert`, such as `python-expert`.
- **Knowledge (facts or reference):** bare nouns or plural concepts, such as `adr` or `design-system`.
- **Workflows:** action verbs or prepositional phrases, such as `handoff` or `update-docs`.

#### 2.4 Description Requirements (Tripartite Formula)

The `description` field is mandatory. It has three required parts and one optional lever.

1. **What it is (anchor noun).** A category noun in the first 50 characters. Example: "Architecture decision record manager..."
2. **What it does (active capabilities).** Concrete third-person present action verbs. Example: "initiates, links, and supersedes ADRs."
3. **When to use (activation trigger).** An explicit `Use when...` clause with concrete symptom keywords.
4. **Negative boundary (optional).** `Do not use for X. Defer to Y.` Use it when adjacent skills collide.

Frontmatter scalar convention:

- Use the folded block scalar `>-` for `description`.
- Use the literal block scalar `|-` for `argument-hint`.
- Enforce the 300-character budget.

Worked examples:

*Good workflow description (279 chars):*

```yaml
description: >-
  ADR lifecycle manager via `adr` CLI. Initiates, links, supersedes, and verifies architecture decision records. Use when documenting architectural decisions, evaluating technical trade-offs, or diagnosing ADR drift. Defer to git for commit management.
```

*Good knowledge description (288 chars):*

```yaml
description: >-
  Adversarial crux code review gate auditing test refutability, domain state invariants, failure resiliency, and Clean Architecture boundaries. Evaluates semantic soundness beyond test passes. Use when reviewing code changes, auditing PRs, checking invariants, or verifying goal attainment.
```

#### 2.5 Base Fields (Agent Skills Spec)

| Field | Required | Type | Purpose |
| --- | --- | --- | --- |
| `name` | Required | string | Skill identifier. 1–64 chars. Must match the directory. |
| `description` | Required | string | Tripartite routing text. ≤300 chars. Use `>-`. |
| `compatibility` | Optional | string | Environment requirements. Max 500 chars. |
| `allowed-tools` | Optional | string or list | Pre-approved tools, such as `Bash(git:*) Read Write`. |
| `metadata` | Optional | mapping | Structural declarations. See below. |

#### 2.6 Metadata Conventions

```yaml
metadata:
  manage: [git, python, rust]           # Parent skill: managed subskill names
  managed-by: scaffold                  # Subskill: parent skill name
  depends-on: [eval-gate, code-review]  # Hard dependencies required for execution
  credits:                              # Upstream provenance for ported skills
    source: https://github.com/org/repo/blob/main/skills/upstream/SKILL.md
    author: upstream-author
    version: main
    note: Adapted for LSZ harness
```

`depends-on` rules:

- List hard dependencies only. Their absence breaks execution.
- Add `depends-on` when this skill invokes another skill, reads its scripts, or relies on its output contract.
- Keep optional alternatives and reading references in prose.
- Run `uv run $SKILL_DIR/scripts/validate-deps.py related <skill-name>` before a rename or removal.

`check` validates `depends-on` only. It does not validate `manage` or `managed-by` wiring. Use `skill.py manage` and `skill.py unmanage` for those changes.

#### 2.7 Platform Enhancement Fields

Claude Code and Pi extend the base spec. Pi's semantics are the default.

| Field | Platform | Type | Purpose |
| --- | --- | --- | --- |
| `disable-model-invocation` | Claude / Pi | boolean | `true` removes the skill from model context. User-only invocation. |
| `argument-hint` | Claude Code | string | Autocomplete hint for arguments. Use `\|-`. |
| `arguments` | Claude Code | string or list | Named positional arguments substituted via `$name`. |
| `user-invocable` | Claude Code | boolean | Controls appearance in the user slash menu. |
| `model` | Claude Code | string | Overrides the model: `opus`, `sonnet`, `haiku`, or `inherit`. |
| `effort` | Claude Code | string | Thinking effort: `low`, `medium`, `high`, `xhigh`, or `max`. |
| `context` | Claude Code | string | Set to `fork` for subagent isolation. |
| `paths` | Claude Code | list | Glob patterns that limit activation. |

#### 2.8 Path and Variable Substitutions

Use `$SKILL_DIR` as the path anchor in prose:

- Scripts: `uv run $SKILL_DIR/scripts/<name>.py`
- References: `$SKILL_DIR/references/<name>.md`
- Markdown links: standard relative links, such as `[name](references/<name>.md)`.

Use forward slashes in every path.

**Anchor:** `$SKILL_DIR` expands to the directory of the `SKILL.md` that owns the referencing document. The package root is the outermost `skills/<name>/` above it.

**Scope:** a `$SKILL_DIR` path must resolve inside the package root. A path that escapes it is an Out-of-Package Reference.

Three reference kinds:

| Kind | Required form |
| --- | --- |
| Intra-package pointer | Relative link or `$SKILL_DIR` path. |
| Cross-package pointer | Symbolic skill name plus a `metadata.depends-on` entry. Never a `$SKILL_DIR/../..` path. |
| Exterior capability | Guarded Reference: front-loaded condition per `writing-for-agents` §1, plus the degraded branch. |

**Guard trigger:** guard a target that is not co-distributed (a different repository or `skills-lock.json` source), or absent from the declared install set. A co-distributed sibling needs no guard.

#### 2.9 Body Signatures

**Workflow skills:**

1. *Philosophy and foundation:* mental model, invariants, design constraints, and non-goals.
2. *Operational workflow:* ordered phases, deterministic commands, error handling, and completion criteria.
3. *Execution contract:* invocation, arguments, and expected response format.

**Knowledge skills:**

1. *Core mental model:* architectural trade-offs, invariants, and domain rules.
2. *Topical guidance and gotchas:* code shapes, anti-patterns, and failure modes.
3. *Pointers to deep assets:* one-level-deep links. Never invent a workflow for reference material.

Every procedural step ends with a checkable, falsifiable completion criterion. Prefer an exit code, an assertion, or a file existence test.

### Phase 3: Verify and Gate Execution

Run the native verification suite from the project root. These commands are repo-wide unless noted.

```bash
# Frontmatter syntax, scalar conventions, and name collisions
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py lint

# Description budget (≤300 chars)
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py context-check

# Plain English and STE-100 linting (per file)
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/ste100.py skills/<skill-name>/SKILL.md
```

Conditional gates:

```bash
# After a dependency, move, or rename change. Validates depends-on only.
uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py check

# Only when targeted tests exist
uv run pytest tests/ai-engineering-expert tests/test_validate_deps.py
uv run pytest tests/<skill-name>
```

Full local gate:

```bash
bash scripts/check.sh
```

`scripts/check.sh` runs 8 gates: ruff check, ruff format, basedpyright, `lint`, `check`, `context-check`, STE-100 on 7 named files, and pytest.

Gate facts:

- `context-check` scans the whole tree. It has no working single-skill mode.
- `context-check` hard-fails only on missing, empty, or over-budget descriptions. `Use when` and symptom checks are warnings. They are skipped for `managed-by` subskills.
- `ste100.py` enforces 20 words for every sentence. It does not split procedural and descriptive limits.
- CI STE-100 covers 7 named files, not every `SKILL.md` or reference.
- `uv run $SKILL_DIR/scripts/validate-deps.py refs` resolves every Markdown link and `$SKILL_DIR` target. Gate 5 (`validate-deps.py check`) runs it too.

#### Semantic Verification Gate (Skeptic)

Dispatch an adversarial Skeptic subagent. The Skeptic reads the diff only, with zero exploration.

- **EDD anchors:** each deterministic goal has a script or test.
- **Symptom grounding:** `Use when...` uses natural user problem terms.
- **BDD coverage:** Given/When/Then covers the happy path, edge cases, and failure modes.
- **Default selection:** one clear default, not an open menu.
- **Context cleanliness:** no environment-specific paths or setup noise.
- **Link integrity:** every markdown reference resolves.
- **Path anchoring:** prose uses `$SKILL_DIR`.
- **Taxonomy fit:** the body signature matches Workflow or Knowledge.

A failure routes back to the implementer. The orchestrator keeps the verdict and the artifact pointers.

---

## Canonical Homes

- **Layout and directory anatomy:** [skill-structure.md](skill-structure.md)
- **Failure archetypes and diagnosis:** [skill-diagnosis.md](skill-diagnosis.md)
- **Description budgets and invocation classes:** [context-load-policy.md](context-load-policy.md)
- **Terminology:** [glossary.md](glossary.md)
- **Agent-document craft:** [writing-for-agents](../../writing-for-agents/SKILL.md)
- **STE-100 grammar:** [plain-language.md](../../../references/plain-language.md)
