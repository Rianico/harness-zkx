# Skill Authoring Reference

Complete reference for authoring skills. Documents both the Agent Skills specification and Claude Code extensions.

**Default behavior: Claude Code spec.** Use official Agent Skills format only when portability is explicitly required.

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

#### `argument-hint`

Use square brackets for optional parts, angle brackets for required:
```yaml
argument-hint: "[balanced|uncle-bob|fowler|evans] <topic>"
```

#### `arguments`

Named positional arguments substituted via `$name` in skill body:
```yaml
arguments: feature mode
# or
arguments:
  - feature
  - mode
```

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

`$SKILL_DIR` is the universal path anchor for **all** skill-owned resources — scripts, references, raw docs, config files, anything bundled with the skill. Always use `$SKILL_DIR/` paths instead of relative paths like `../../references/`.

**Why:** Relative paths break when the referencing file moves (e.g., sub-skill to main skill, reference to another reference). `$SKILL_DIR` resolves correctly from any file in the skill regardless of nesting depth.

**Applies to:**
| Resource | Path Pattern | Example |
|----------|-------------|---------|
| Scripts | `$SKILL_DIR/scripts/<name>.py` | `uv run $SKILL_DIR/scripts/compile.py` |
| References | `$SKILL_DIR/references/<module>.md` | `Read $SKILL_DIR/references/layout.md` |
| Raw docs | `$SKILL_DIR/references/raw/` | `Read $SKILL_DIR/references/raw/ratatui/` |
| Config | `$SKILL_DIR/config/<file>` | `source $SKILL_DIR/config/defaults.sh` |

**Anti-patterns:**
- `../../references/<module>/<file>.md` — brittle, breaks on file moves
- `./references/<file>.md` — assumes cwd is the skill directory
- Absolute paths like `/Users/x/skills/my-skill/references/` — not portable

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
