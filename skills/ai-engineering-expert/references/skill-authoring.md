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
