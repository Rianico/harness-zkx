# Skill Authoring Reference

Complete reference for authoring skills. Documents both the Agent Skills specification and Claude Code extensions.

**Default behavior: Claude Code spec.** Use official Agent Skills format only when portability is explicitly required.

## Skill Taxonomy

All LSZ skills are one of four primary types. Classification determines structure, dispatch pattern, and resource needs.

### Orchestration Skills

Use for multi-phase, multi-party, or fan-out/fan-in workflows.

- May invoke multiple skills and agents
- May define branching, checkpoints, and approval points
- Own workflow sequencing and complex state transitions
- Must not do implementation work directly

**Structure:** Dispatch table mapping phases to subagent templates. No implementation logic in the skill body.

**Example:** `orchestrating` -- dispatches architect, developer, code-reviewer, eval-gate across plan/implement/review cycles.

### Complex Workflow Skills

Use for a substantial single-purpose workflow with multiple phases.

- May invoke agents
- May generate artifacts and enforce phase transitions
- Should prefer structured, schema-like execution instructions when dispatching agents

**Structure:** Phase definitions with state transitions, artifact contracts, and phase-specific dispatch templates.

**Example:** `tdd-cycle` -- RED/GREEN/REFACTOR phases with test-first enforcement and phase gates.

### Domain Knowledge Skills

Use for guides, patterns, expert methodology, and reusable domain constraints.

- Provide retrieval-time expertise
- Do not generally own orchestration
- Designed to be loaded just-in-time by agents or higher-level skills

**Structure:** Organized by topic. Patterns with examples. Gotchas for non-obvious pitfalls. No dispatch templates.

**Example:** `ai-engineering-expert` -- loaded when designing skills/agents/workflows; provides methodology, not execution.

### Action Skills

Use for narrow, simple workflows and direct task execution.

- Best fit for small, low-ambiguity tasks
- Should usually be invoked directly as skills rather than exposed through command wrappers
- Should remain simple and compact

**Structure:** Compact, focused. Minimal sections. No subagent dispatch.

**Example:** `skill-stocktake` -- audits skill inventory and reports status. Single pass, no phases.

### When to Embed Logic Directly in an Agent

Only embed workflow logic directly into an Agent's system prompt if the workflow is:

1. **Atomic** -- Does one specific thing without loops
2. **Universal** -- Does not change based on language/framework
3. **Short** -- Under 300 words

Example: The `planner` agent -- takes a task, produces a plan, done. No branching, no framework-specific behavior, fits in a short prompt.

If the workflow violates any of these constraints, it belongs in a skill.

## Required Fields

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | **Required** | 1-64 chars, lowercase alphanumeric + hyphens, no leading/trailing hyphens, no `--`, must match directory name. |
| `description` | **Required** | 1-1024 chars, third-person, what + when, trigger vocabulary. Truncated at 1,536 chars in skill listing. |

### `name` Constraints (All Rules)

1. Must be 1-64 characters
2. Lowercase letters (`a-z`), numbers, and hyphens only
3. Must not start or end with a hyphen (`-`)
4. Must not contain consecutive hyphens (`--`)
5. Must match the parent directory name

**Valid:**
```yaml
name: pdf-processing
name: data-analysis
name: code-review
```

**Invalid:**
```yaml
name: PDF-Processing  # uppercase not allowed
name: -pdf            # cannot start with hyphen
name: pdf--processing # consecutive hyphens not allowed
name: my-skill        # if directory is named "other-skill"
```

### `description` Requirements

**This field is mandatory.** A skill without a proper description cannot be discovered or triggered.

- Write in **third person** (injected into system prompt; first-person causes discovery failures)
- Include **both** what the skill does AND when to use it
- Lead with the key use case (truncated at 1,536 chars in skill listing)
- Include trigger vocabulary: verbs, artifact names, domains, topic words
- Maximum 1024 characters

**Good:**
```yaml
description: "Extracts text and tables from PDF files, fills PDF forms, merges documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."
```

**Poor:**
```yaml
description: "Helps with documents"  # too vague
description: "I can help you process PDFs"  # wrong POV
```

## Optional Fields

### Official Agent Skills Spec Fields

These fields are part of the Agent Skills specification and provide portability across compliant agents.

| Field | Required | Constraints | Purpose |
|-------|----------|-------------|---------|
| `license` | Optional | License name or reference | Specifies skill license |
| `compatibility` | Optional | Max 500 chars | Environment requirements |
| `metadata` | Optional | Key-value mapping | Arbitrary additional properties |

**Examples:**
```yaml
license: Apache-2.0
compatibility: Requires git, docker, jq, and access to the internet
metadata:
  author: example-org
  version: "1.0"
```

### Metadata Conventions

The `metadata` field supports project-specific structural declarations. The LSZ architecture defines these conventions:

| Key | Type | Purpose |
|-----|------|---------|
| `manage` | list | Parent skill: names of sub-skills this parent manages |
| `managed-by` | string | Sub-skill: name of the parent skill |
| `depends-on` | list | Hard dependencies on other skills (must exist in `skills/` or `skills-lock.json`) |
| `author` | string | Attribution for third-party skills |
| `version` | string | Version for third-party skills |

**`depends-on` rules:**
- Hard dependencies only -- list skills whose absence breaks this skill's behavior
- Simple list of skill names, no arguments
- Sub-skills declare their own `depends-on` independently
- Add `depends-on` when this skill must load or invoke another skill, read its scripts/references, consume its artifacts, or rely on its output contract
- Keep optional alternatives, related reading, examples, and background context in prose, not `depends-on`
- Before renaming, moving, merging, or deleting a skill, run `uv run $SKILL_DIR/scripts/validate-deps.py callers <skill-name>`, then update listed dependent skills or remove stale dependency entries
- Validation: `uv run $SKILL_DIR/scripts/validate-deps.py` from project root after dependency edits
- Caller scan: `uv run $SKILL_DIR/scripts/validate-deps.py callers <skill-name>` before renames, moves, merges, or removals
- Interactive repair: `uv run $SKILL_DIR/scripts/validate-deps.py --fix` after renames or removals

### Claude Code Extension Fields

These fields extend the Agent Skills spec for Claude Code specifically.

| Field | Required | Type | Purpose |
|-------|----------|------|---------|
| `argument-hint` | Optional | string | Autocomplete hint for arguments |
| `arguments` | Optional | string or array | Named positional arguments for `$name` substitution |
| `allowed-tools` | Optional | string or array | Tools allowed without permission prompts |
| `disable-model-invocation` | Optional | boolean | Prevent automatic skill loading (default: false) |
| `user-invocable` | Optional | boolean | Show in `/` menu (default: true) |
| `model` | Optional | string | Override model (`opus`, `sonnet`, `haiku`, `inherit`) |
| `effort` | Optional | string | Thinking level (`low`, `medium`, `high`, `xhigh`, `max`) |
| `context` | Optional | string | Set to `fork` for subagent isolation |
| `agent` | Optional | string | Subagent type when `context: fork` |
| `hooks` | Optional | object | Skill-scoped lifecycle hooks |
| `paths` | Optional | string or array | Glob patterns limiting skill activation |
| `shell` | Optional | string | Shell for inline commands (`bash` default, `powershell`) |

#### `arguments`

Named positional arguments substituted via `$name` in skill body. Names should reflect the skill's function — use semantic names that describe what the argument means, not just syntax.

```yaml
arguments: feature mode
# or
arguments:
  - feature
  - mode
```

**Good semantic names:**
- `content_type` not `arg1` — describes what kind of content
- `platform` not `target` — specifies where to publish
- `scope` not `area` — defines audit boundary
- `feature` not `thing` — what's being tested

#### `argument-hint`

One line per hint. Use bash conventions: `<arg>` required, `[arg]` optional, `[a|b|c]` options, `[--flag]` flags. Show defaults with `[arg=default]` and a comment. Descriptions should explain what the argument does in the skill's context.

```yaml
argument-hint: |
  [blog|essay|guide|tutorial|newsletter] -- content type to write (default: blog)
  <topic> -- subject or prompt for the article
```

```yaml
argument-hint: |
  [x|linkedin|threads|bluesky|tiktok|youtube] -- target platform
  <source> -- content to adapt (article, notes, url, or description)
```

```yaml
argument-hint: |
  <scope> -- component, page, or store to audit (e.g., "email page", "userStore")
```

**Field ordering convention:** Place `arguments` before `argument-hint`. `argument-hint` serves as inline docs for each argument.

**Principle:** Arguments and hints are documentation. A user reading only the `argument-hint` should understand what inputs the skill expects and what each input means.

#### `allowed-tools`

Accepts **both formats**:
```yaml
# Space-separated string
allowed-tools: Bash(git *) Read Write

# YAML array
allowed-tools:
  - Agent
  - Bash
  - Read
```

#### `model` Override
```yaml
model: opus      # Force Claude Opus
model: sonnet    # Force Claude Sonnet
model: haiku     # Force Claude Haiku
model: inherit   # Keep current model (default)
```

#### `effort` Levels

| Level | Use Case |
|-------|----------|
| `low` | Quick, simple tasks |
| `medium` | Standard complexity |
| `high` | Complex reasoning |
| `xhigh` | Very complex analysis |
| `max` | Maximum effort for critical tasks |

#### `context: fork` Isolation
```yaml
context: fork
agent: developer
```

#### `paths` Activation Limiting
```yaml
paths:
  - "src/**/*.ts"
  - "tests/**/*.ts"
```

## String Substitutions

Skills support string substitution for dynamic values in the skill content:

| Variable | Description |
|----------|-------------|
| `$ARGUMENTS` | All arguments passed when invoking the skill |
| `$ARGUMENTS[N]` | Access specific argument by 0-based index |
| `$N` | Shorthand for `$ARGUMENTS[N]` (e.g., `$0`, `$1`) |
| `$name` | Named argument declared in `arguments` frontmatter |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_EFFORT}` | Current effort level |
| `$SKILL_DIR` | Skill directory path (for referencing bundled files). **Official substitution:** `${CLAUDE_SKILL_DIR}` |

### `$SKILL_DIR` Path Convention

`$SKILL_DIR` is the universal path anchor for **prose references** to skill-owned resources — scripts, references, raw docs, config files, anything bundled with the skill. Use `$SKILL_DIR/` in prose text; use relative paths in markdown links.

**Also works in commands:** `$SKILL_DIR` resolves in command files too, pointing to the command's directory. Use `$SKILL_DIR/../skills/` to reference skills from a routing command.

**Why:** Prose references like `Read $SKILL_DIR/references/layout.md` are consumed by an LLM whose cwd is unknown — relative paths would resolve against the wrong directory. Markdown links like `[layout](references/layout.md)` follow the standard relative-to-file convention and work correctly.

**Applies to:**
| Resource | Prose Path | Markdown Link |
|----------|-----------|---------------|
| Scripts | `$SKILL_DIR/scripts/<name>.py` | — |
| References | `$SKILL_DIR/references/<module>.md` | `[text](references/<module>.md)` |
| Raw docs | `$SKILL_DIR/references/<skill-name>-raw/` | `[text](references/<skill-name>-raw/<file>.md)` |
| Config | `$SKILL_DIR/config/<file>` | — |

**Anti-patterns:**
- `../../references/<module>/<file>.md` in prose — brittle, breaks on file moves
- `./references/<file>.md` in prose — assumes cwd is the skill directory
- Absolute paths like `/Users/x/skills/my-skill/references/` — not portable
- `$SKILL_DIR/references/<file>.md` in markdown links — unnecessary, relative-to-file is standard

**Example:**
```yaml
---
name: session-logger
description: Log activity for this session
arguments: message
---

Log the following to logs/${CLAUDE_SESSION_ID}.log:
$message

Run the bundled script:
uv run $SKILL_DIR/scripts/helper.py

Read the reference:
$SKILL_DIR/references/format-spec.md
```

## Trigger Pattern Coverage

For methodology and domain-knowledge skills, descriptions MUST cover all natural trigger patterns:

| Pattern | Example Phrases | Why It Matters |
|---------|-----------------|----------------|
| **Direct domain** | "design the architecture", "implement authentication" | Explicit request for the domain |
| **Problem framing** | "this code is a mess", "need to scale", "too many bugs" | User describes symptom, not domain |
| **Decision language** | "should we use X or Y", "which approach", "trade-off between" | User needs guidance, not action |

### TRIGGER Clause Pattern

For methodology skills, use an explicit TRIGGER clause:
```yaml
description: "Architecture expertise for system design. TRIGGER when: designing architecture, defining boundaries, evaluating approaches; OR user mentions scaling problems, messy code, coupling issues; OR user asks 'should we', 'which approach', 'is this the right pattern'."
```

## Calibration: Freedom vs Prescriptiveness

Match specificity to task fragility.

### High Freedom (Text-based instructions)
Use when: multiple approaches valid, decisions depend on context.
```markdown
## Code review process
1. Analyze the code structure
2. Check for potential bugs
3. Suggest improvements
```

### Low Freedom (Specific scripts)
Use when: operations are fragile, consistency is critical.
```markdown
## Database migration
Run exactly:
\`\`\`bash
python scripts/migrate.py --verify --backup
\`\`\`
Do not modify or add flags.
```

### Provide Defaults, Not Menus

**Good:**
```markdown
Use pdfplumber for text extraction. For scanned PDFs, use pdf2image with pytesseract.
```

**Bad:**
```markdown
You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image...
```

## Rules vs Skills Boundary

Rules and skills serve fundamentally different purposes in the architecture. Understanding this boundary is critical for designing a maintainable, context-efficient system.

### The Core Distinction

| Dimension | Rules | Skills |
|-----------|-------|--------|
| **Loading** | Always-on | On-demand |
| **Token cost** | Every conversation | Only when invoked |
| **Purpose** | Defaults & consistency | Deep expertise |
| **Content** | WHAT to use | HOW to implement |
| **Knowledge type** | Personal taste, baseline | Non-obvious, experiential |

### Rules Design Principles

Rules are **always loaded** into context. Every token competes with conversation history and other context. This constraint shapes everything.

**1. Conciseness is Mandatory**

Rules must justify their token cost every conversation.

```markdown
# GOOD: One line, high value
- **`pytest`**: Run with `uv run pytest -q`

# BAD: Verbose explanation
- **`pytest`**: You should use pytest for testing because it has great fixture support and a rich plugin ecosystem. Run it with `uv run pytest -q` to keep output quiet unless you need verbose mode...
```

**2. STATE, Don't EXPLAIN**

Rules declare preferences. They don't justify them.

```markdown
# GOOD: Just the preference
Use FastAPI for new APIs.

# BAD: Explaining why
Use FastAPI for new APIs because it provides automatic OpenAPI documentation, async support out of the box, and type safety through Pydantic integration...
```

The LLM already knows FastAPI's benefits. The rule sets YOUR default.

**3. Baseline Knowledge Only**

Rules capture what the LLM already knows but might forget or choose differently.

| LLM Knows | Rule Purpose |
|-----------|--------------|
| "Use pytest" | "Use pytest, not unittest" (preference) |
| "Type hints are good" | "Type hints on all signatures" (consistency) |
| "PEP 8 exists" | "PEP 8, snake_case" (reminder) |

Rules don't teach. They crystallize defaults.

**4. Personal Style & Taste**

Rules encode decisions you don't want to revisit.

```markdown
# Tool choices
- `uv` over `pip`
- `ruff` over `black`
- `basedpyright` over `pyright`

# Style choices
- `pytest -q` by default
- File-level suppressions, never global
```

These aren't "right answers" — they're YOUR answers. Rules eliminate trivial decisions.

**5. Stability Over Recency**

Rules should rarely change. They represent settled decisions.

- "Use FastAPI" → stable preference
- "Use FastAPI 0.115+ for new X feature" → too specific, belongs in skill

### Skills Design Principles

Skills are **loaded on-demand**. They can be longer, include examples, and explain reasoning.

**1. Non-Obvious Knowledge**

Skills contain what the LLM might NOT know or might get WRONG.

```markdown
# SKILL: python-expert

## Async & Concurrency

**Blocking the Event Loop:**
Never put blocking I/O inside `async def`. It blocks the entire event loop.
```python
# BAD
async def fetch():
    response = requests.get(url)  # Blocks!
```

The LLM knows `requests` is blocking, but might not realize the severity in async context. This is experiential knowledge.

**2. Patterns with Examples**

Skills show HOW, not just WHAT.

```markdown
# SKILL: django-expert

**N+1 Query Audit:**
```python
# BAD: N+1 queries
for post in Post.objects.all():
    print(post.author.name)  # Query per post

# GOOD: Join
for post in Post.objects.select_related('author'):
    print(post.author.name)
```
```

This requires code to understand. It's not a one-liner rule.

**3. Framework/Domain Gotchas**

Skills capture pitfalls and edge cases.

```markdown
# SKILL: pytorch-expert

**Memory Management:**
```python
optimizer.zero_grad()  # Before backprop

with torch.no_grad():  # Evaluation
    outputs = model(inputs)
```
```

The LLM might forget `zero_grad()` or use `no_grad()` incorrectly. This is about correctness, not preference.

**4. Architectural Decisions**

Skills explain trade-offs and constraints.

```markdown
# SKILL: django-expert

**Fat Models, Skinny Views:**
Views handle HTTP routing and permissions. Business logic belongs in models or service layer.
```

This is a design philosophy, not a syntax rule. It requires understanding WHY.

### Boundary Identification Checklist

Ask these questions to determine placement:

| Question | Rule | Skill |
|----------|------|-------|
| Should this apply EVERY conversation? | ✓ | ✗ |
| Is it a one-liner preference? | ✓ | ✗ |
| Does the LLM already know this? | ✓ | ✗ |
| Does it need code examples? | ✗ | ✓ |
| Is it framework/domain-specific? | ✗ | ✓ |
| Might the LLM get this WRONG? | ✗ | ✓ |
| Does it explain WHY? | ✗ | ✓ |

### The Routing Pattern

Rules can delegate to skills for complex scenarios:

```markdown
## Expertise Routing

For complex patterns and domain gotchas, invoke the expert skill:
```
Skill(skill="python-expert", args="[async|testing|django|pytorch]")
```
```

This keeps rules lean while ensuring deep knowledge is available when needed.

### Anti-Patterns

**Bad Rules (verbose, explanation-heavy):**
```markdown
# BAD: Explaining WHY
Use pytest because it has fixture support and a plugin ecosystem. Fixtures are better than setUp/tearDown because they provide better isolation and composability...

# BAD: Domain-specific knowledge always loaded
Django models should use select_related for foreign keys to avoid N+1 queries. This is critical for performance because...
```

**Bad Skills (obvious, preference-only):**
```markdown
# BAD: Just a preference
Use pytest for testing.

# BAD: Generic advice
Write clean code and add comments.
```

### Layered Example: Python Testing

**Rule (always-on, preference):**
```markdown
- **`pytest`**: Run with `uv run pytest -q` (quiet by default)
- Default to pytest, not unittest
```

**Skill (on-demand, deep knowledge):**
```markdown
## Testing Strategy

**Pytest over unittest:**
- Fixtures over `setUp`/`tearDown`
- `pytest-asyncio` for async tests

**Mock Philosophy:**
Minimize `unittest.mock`. Prefer:
- Containerized dependencies (test databases)
- `responses` or VCR for HTTP
- Real implementations when fast enough
```

The rule sets the default. The skill guides complex scenarios.

## Subagent Delegation

**Core Philosophy: Subagent-First Execution**

The orchestrator NEVER does implementation work directly. All code writing, file editing, test execution, doc updates, and review work happens in subagents. This is a fundamental architectural constraint, not a context optimization.

### Orchestrator Role

| Orchestrator DOES | Orchestrator NEVER DOES |
|-------------------|------------------------|
| Route tasks to appropriate subagents | Write code directly |
| Dispatch with structured prompts | Edit files directly |
| Monitor for completion/failure | Run tests directly |
| Receive and synthesize summaries | Read full artifact contents into context |
| Handle user interaction and approvals | Execute shell commands for implementation |
| Pass pointers between phases | Re-process subagent outputs |

### Pointer-Based State Passing

Subagents exchange state through **file paths**, not content. The orchestrator passes pointers; subagents read/write artifacts at those paths.

```markdown
Agent tool (developer):
  prompt: |
    Plan file: /path/to/.lsz/.../plan/plan_v1.md
    
    Implement the feature described in the plan.
    
    Return: Summary (≤100 words) + paths to modified files.
```

### Subagent Summary Contract

Every subagent MUST return a brief summary following BurntSushi's PR style:
- Complete, coherent, reviewable unit
- State approach and reasoning, not just "what was done"
- Deliver a position that can be critiqued

**Format:**

```markdown
## Summary
<approach taken, reasoning behind key decisions, and outcome>

## Artifacts
- <path to primary output>

## Trade-offs (optional)
- <key trade-off or constraint for next phase>
```

### Skill Dispatch Template

Skills at any taxonomy level may delegate to subagents. Complex workflow skills MUST define their dispatch pattern internally:

```markdown
Agent tool (<subagent_type>):
  description: "<short task summary>"
  prompt: |
    Mode: $MODE
    Feature: $FEATURE
    Source docs: $SOURCE_DOCS
    
    [execution instructions...]
    
    Return: Summary (approach + reasoning) + artifact paths.
```

The caller injects parameters (`$MODE`, `$FEATURE`), the skill owns the dispatch shape.

### Skill Dispatch Template

Complex workflow skills MUST define their dispatch pattern internally:

```markdown
## Dispatch Template

Agent tool (general-purpose):
  description: "Run feature validation"
  prompt: |
    Mode: $MODE
    Feature: $FEATURE
    Source docs: $SOURCE_DOCS
    
    [execution instructions...]
```

The caller injects parameters (`$MODE`, `$FEATURE`), the skill owns the dispatch shape.

## Content Guidelines

### Assume Baseline Competence

Only add context the LLM wouldn't already know:
- Project-specific conventions
- Domain-specific procedures
- Non-obvious edge cases

**Bad (explaining common knowledge):**
```markdown
PDF files are a common format that contains text and images...
```

**Good (jumps to specifics):**
```markdown
Use pdfplumber for text extraction. For scanned documents, fall back to pdf2image.
```

### Avoid Time-Sensitive Information

**Bad:**
```markdown
If you're doing this before August 2025, use the old API.
```

**Good:**
```markdown
## Current method
Use the v2 API endpoint.

## Old patterns
<details>
<summary>Legacy v1 API (deprecated 2025-08)</summary>
The v1 API is no longer supported.
</details>
```

## Structure Guidelines

- Keep `SKILL.md` **under 500 lines**
- Move detailed reference material to separate files in `references/`
- Keep file references **one level deep** from `SKILL.md`
- Reference supporting files from `SKILL.md` so Claude knows what each contains

## Parent Skill with Sub-Skills Pattern

When a skill manages multiple related capabilities, use the **parent skill with sub-skills** pattern instead of routing commands. This pattern provides better discoverability, explicit relationships, and maintainability.

### When to Use

Use this pattern when:
- Multiple related skills share a common domain (e.g., `write-article` and `write-publish` under `write`)
- You want discoverability: sub-skills are visibly nested under their parent
- You need explicit relationships: metadata fields express parent-child connections
- Each sub-skill may have its own references, scripts, or resources

**Do NOT use for:**
- Single-purpose skills (no sub-skills needed)
- Skills with no shared domain or relationship
- Cases where a single skill file is sufficient

### Structure

```
skills/<parent-name>/
  SKILL.md              # Parent skill with registry + dispatch logic
  subskills/
    <subskill-1>/
      SKILL.md          # Full skill with frontmatter, references, scripts
      references/
      scripts/
    <subskill-2>/
      SKILL.md
      references/
      scripts/
```

**Example:**
```
skills/write/
  SKILL.md              # Parent: routes to article or publish
  subskills/
    article/
      SKILL.md          # Long-form content writing
    publish/
      SKILL.md          # Platform distribution
```

### Metadata Fields

Express parent-child relationships via `metadata` frontmatter:

**Parent skill:**
```yaml
metadata:
  manage: [article, publish]
```

**Sub-skill:**
```yaml
metadata:
  managed-by: write
```

| Field | Location | Purpose |
|-------|----------|---------|
| `manage` | Parent | List of sub-skill names this parent manages |
| `managed-by` | Sub-skill | Back-reference to parent skill name |

**Why these fields:**
- Discoverable via grep/search
- Enables tooling to identify relationships
- Natural verb phrases (`manage`, `managed-by`)
- No `skill-kind` field needed (redundant with the pair)

### Registry Format

Parent skill includes a formal YAML registry:

```yaml
---
name: write
description: Content creation and distribution cluster...
arguments: mode content_type platform
metadata:
  manage: [article, publish]
---

# Write Skill

## Sub-Skill Registry

```yaml
subskills:
  article: $SKILL_DIR/subskills/article/SKILL.md
  publish: $SKILL_DIR/subskills/publish/SKILL.md
```

## Dispatch

Parse `$ARGUMENTS` to determine mode...
```

**Minimal registry:** Just paths. Sub-skill frontmatter already contains descriptions and arguments. Avoid duplication.

### Dispatch Mechanism

**CRITICAL:** Claude Code's skill discovery only finds `skills/*/SKILL.md` (top-level). Nested `skills/*/subskills/*/SKILL.md` are **NOT discoverable** via the `Skill` tool.

**Parent must use `Read` to dispatch:**

```markdown
## Dispatch

| First Arg | Action |
|-----------|--------|
| `article` | Read `$SKILL_DIR/subskills/article/SKILL.md` and follow its instructions |
| `publish` | Read `$SKILL_DIR/subskills/publish/SKILL.md` and follow its instructions |
```

**Anti-pattern:** Using `Skill` tool to invoke sub-skills — it returns "Unknown skill" for nested paths.

### Sub-Skill Identity

Sub-skills are **full skills**:
- Complete frontmatter (`name`, `description`, `arguments`, `argument-hint`)
- Can have `references/` and `scripts/`
- Are hidden from direct invocation (nested path, not discovered)

**No special frontmatter needed** beyond `managed-by: <parent>` in metadata.

### Migration from Routing Commands

**Old pattern (routing command):**
```
commands/write.md           → routing command (forwards to skills)
skills/write-article/SKILL.md  → hidden skill (user-invocable: false)
skills/write-publish/SKILL.md  → hidden skill (user-invocable: false)
```

**Problems:**
- Sub-skills have no back-reference to their manager
- Relationship only visible in command file, not skills
- Requires reading command to understand skill relationships

**Migration steps:**
1. Create `skills/<name>/` directory
2. Convert `commands/<name>.md` → `skills/<name>/SKILL.md`
   - Add frontmatter with `metadata.manage`
   - Add sub-skill registry section
   - Add dispatch logic using `Read`
3. Move sibling skills to `skills/<name>/subskills/<subskill>/`
4. Add `metadata.managed-by` to each sub-skill
5. Remove `user-invocable: false` and `disable-model-invocation: true` from sub-skills
6. Delete old command and standalone skill directories

### Benefits Over Routing Commands

| Aspect | Routing Command | Parent Skill with Sub-Skills |
|--------|-----------------|------------------------------|
| Discoverability | Sub-skills invisible in directory | Sub-skills visibly nested |
| Relationship | Only in command file | In metadata + directory structure |
| Maintenance | Scattered (command + skills) | Consolidated (one parent skill) |
| Resources | Sub-skills can't have scripts/references | Each sub-skill has full capabilities |

### Checklist

Before using this pattern:
- [ ] Multiple related capabilities share a domain
- [ ] Each sub-skill may need its own references or scripts
- [ ] Parent skill has clear dispatch logic
- [ ] Registry lists all sub-skills with `$SKILL_DIR/` paths
- [ ] Parent has `manage: [...]` in metadata
- [ ] Sub-skills have `managed-by: <parent>` in metadata
- [ ] Dispatch uses `Read`, not `Skill` tool
