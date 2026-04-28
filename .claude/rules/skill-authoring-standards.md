# Skill Authoring Standards

## Purpose
Comprehensive standards for creating, structuring, and maintaining skills in the LSZ architecture. Ensures discoverability, context efficiency, and maintainability across LLM platforms.

---

## Skill Location

**All skills MUST be placed under `<project_root>/skills/`.**

```
<project_root>/
└── skills/
    └── <skill-name>/
        └── ...
```

---

## Directory Layout

```
skills/
└── <skill-name>/
    ├── SKILL.md          # Required: skill definition
    ├── references/       # Optional: reference materials, examples, templates
    └── scripts/          # Optional: executable scripts for the skill
```

### Directory Purposes

| Directory | Required | Purpose |
|-----------|----------|---------|
| `/` (root) | Yes | Contains `SKILL.md` |
| `references/` | No | Docs loaded into context as needed |
| `scripts/` | No | Executable code for deterministic/repetitive tasks |

### Additional Optional Files

- `prompts/` — Template prompts
- `README.md` — Extended documentation

---

## Required YAML Frontmatter

All skills MUST include in YAML frontmatter:

```yaml
---
name: <skill-name>
description: <description optimized for trigger recall>
argument-hint: "<usage syntax>"  # Required if skill accepts arguments
---
```

### Name Requirements

- Maximum 64 characters
- Lowercase letters, numbers, and hyphens only
- No XML tags
- Prefer **gerund form** (verb + -ing): `processing-pdfs`, `analyzing-spreadsheets`
- Acceptable alternatives: noun phrases (`pdf-processing`), action-oriented (`process-pdfs`)
- Avoid: vague names (`helper`, `utils`), overly generic (`documents`, `data`)

### Description Requirements (CRITICAL)

Descriptions are the **primary trigger surface** for skill discovery. Write for recall first, elegance second.

**MUST:**
- Write in **third person** (injected into system prompt; inconsistent POV causes discovery failures)
- Include **both** what the skill does AND when to use it
- Lead with a one-line identity sentence
- Include trigger vocabulary: verbs, artifact names, domains, topic words
- Signal scope and depth explicitly (name phases, coverage breadth, or narrow purpose)
- Mention key integrations when they affect execution
- Maximum 1024 characters

**GOOD:**
```yaml
description: "Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction."
```

```yaml
description: "Execute a compact TDD workflow for feature work and bug fixes. Use this when the task needs strict RED, GREEN, and REFACTOR discipline, failing tests first, minimal passing changes, and implementation-focused verification."
```

**BAD (too vague):**
```yaml
description: "Helps with documents"
```

**BAD (wrong POV):**
```yaml
description: "I can help you process Excel files"  # First person - will fail discovery
```

### Trigger Pattern Coverage (Methodology Skills)

For **domain-knowledge** and **methodology** skills (e.g., `architecture-expert`, `tdd-expert`, `python-expert`), descriptions MUST cover all natural trigger patterns users employ:

| Pattern | Example Phrases | Why It Matters |
|---------|-----------------|----------------|
| **Direct domain** | "design the architecture", "implement authentication", "build a cache layer" | Explicit request for the domain |
| **Problem framing** | "this code is a mess", "need to scale", "too many bugs", "slow queries" | User describes symptom, not domain |
| **Decision language** | "should we use X or Y", "which approach", "trade-off between", "is this the right pattern" | User needs guidance, not action |

**Rationale:** LLMs often miss methodology skills when users describe problems or decisions rather than explicitly naming the domain. Without problem-framing vocabulary, the skill won't trigger for "this code is a mess" — only for "review the architecture."

**Pattern: Use explicit TRIGGER clause**

```yaml
description: "Architecture expertise for system design, refactoring, service boundaries, and trade-offs. TRIGGER when: designing architecture, defining boundaries, evaluating approaches; OR user mentions scaling problems, messy code, coupling issues, tech debt, performance bottleneck; OR user asks 'should we', 'which approach', 'trade-off between', 'is this the right pattern'."
```

**ANTI-PATTERN (missing problem framing):**
```yaml
description: "Architecture expertise for system design. Use for design critique and refactoring strategy."
# ↑ Won't trigger when user says "this code is a mess"
```

### Argument Hint Format

- Use square brackets for optional parts: `[optional]`
- Use angle brackets for required parts: `<required>`
- Include common flags after the main arguments

```yaml
argument-hint: "[balanced|uncle-bob|fowler|evans] <topic>"
```

---

## Token Budgets & Progressive Disclosure

Skills share the context window with conversation history, system prompts, and other skills. Every token competes for attention.

### Hard Limits

| Metric | Limit | Rationale |
|--------|-------|-----------|
| SKILL.md body | **500 lines** / **5,000 tokens** | Optimal performance threshold |
| Reference depth | **One level** from SKILL.md | LLMs may partially read nested refs |

### Three-Level Loading

| Level | Content | When Loaded |
|-------|---------|-------------|
| 1. Metadata | `name` + `description` | Always (~100 words) |
| 2. SKILL.md body | Full skill instructions | When triggered |
| 3. Bundled resources | `references/`, `scripts/` | As needed (unlimited) |

### Progressive Disclosure Patterns

**Pattern 1: High-level guide with references**
```markdown
## Advanced features

**Form filling**: See [FORMS.md](FORMS.md) for complete guide
**API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
```

**Pattern 2: Conditional details**
```markdown
## Creating documents

Use docx-js for new documents.

**For tracked changes**: See [REDLINING.md](REDLINING.md)
```

**ANTI-PATTERN (too deep):**
```markdown
# SKILL.md
See [advanced.md](advanced.md)...

# advanced.md
See [details.md](details.md)...  # ← LLM may only partially read this
```

---

## Skill Body Structure

1. **Purpose statement** — What the skill does (1-2 sentences)
2. **When to use** — Explicit trigger conditions (optional if covered in description)
3. **Execution contract** — How to invoke, arguments, expected behavior
4. **Workflow phases** — Ordered steps if applicable
5. **Output format** — Expected artifacts or responses

---

## Calibration: Freedom vs. Prescriptiveness

Match specificity to task fragility. Not all parts of a skill need the same level of detail.

### High Freedom (Text-based instructions)
Use when: multiple approaches valid, decisions depend on context, heuristics guide approach.

```markdown
## Code review process

1. Analyze the code structure and organization
2. Check for potential bugs or edge cases
3. Suggest improvements for readability
```

### Low Freedom (Specific scripts, no parameters)
Use when: operations are fragile, consistency is critical, specific sequence required.

```markdown
## Database migration

Run exactly this script:

```bash
python scripts/migrate.py --verify --backup
```

Do not modify the command or add additional flags.
```

### Provide Defaults, Not Menus

When multiple tools/approaches could work, pick a default and mention alternatives briefly.

**GOOD:**
```markdown
Use pdfplumber for text extraction:

```python
import pdfplumber
```

For scanned PDFs requiring OCR, use pdf2image with pytesseract instead.
```

**BAD:**
```markdown
You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image...
```

---

## High-Value Patterns

### Gotchas Sections

Highest-value content: environment-specific facts that defy reasonable assumptions.

```markdown
## Gotchas

- The `users` table uses soft deletes. Queries MUST include
  `WHERE deleted_at IS NULL` or results will include deactivated accounts.
- The user ID is `user_id` in the database, `uid` in the auth service,
  and `accountId` in the billing API. All three refer to the same value.
```

**Add to gotchas when an LLM makes a mistake you correct.**

### Templates for Output Format

Concrete templates outperform prose descriptions.

```markdown
## Report structure

```markdown
# [Analysis Title]

## Executive summary
[One-paragraph overview]

## Key findings
- Finding 1 with supporting data

## Recommendations
1. Specific actionable recommendation
```
```

### Checklists for Multi-Step Workflows

```markdown
## Form processing workflow

Progress:
- [ ] Step 1: Analyze the form (run `scripts/analyze_form.py`)
- [ ] Step 2: Create field mapping (edit `fields.json`)
- [ ] Step 3: Validate mapping (run `scripts/validate_fields.py`)
- [ ] Step 4: Fill the form (run `scripts/fill_form.py`)
```

### Validation Loops

Run validator → fix errors → repeat until pass.

```markdown
## Editing workflow

1. Make your edits
2. Run validation: `python scripts/validate.py output/`
3. If validation fails:
   - Review the error message
   - Fix the issues
   - Run validation again
4. Only proceed when validation passes
```

---

## Content Guidelines

### Assume Baseline Competence

Only add context the LLM wouldn't already know:
- Project-specific conventions
- Domain-specific procedures
- Non-obvious edge cases
- Particular tools or APIs to use

**BAD (explaining common knowledge):**
```markdown
PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library...
```

**GOOD (jumps to what the LLM wouldn't know):**
```markdown
Use pdfplumber for text extraction. For scanned documents, fall back to
pdf2image with pytesseract.
```

### Avoid Time-Sensitive Information

**BAD:**
```markdown
If you're doing this before August 2025, use the old API.
After August 2025, use the new API.
```

**GOOD:**
```markdown
## Current method

Use the v2 API endpoint: `api.example.com/v2/messages`

## Old patterns

<details>
<summary>Legacy v1 API (deprecated 2025-08)</summary>

The v1 API is no longer supported.
</details>
```

### Use Consistent Terminology

Pick one term and use it throughout. Don't mix "API endpoint", "URL", "API route", "path".

---

## Scripts in Skills

### When to Bundle Scripts

Bundle scripts when you notice the LLM independently reinventing the same logic each run: building charts, parsing a format, validating output.

### Script Execution Intent

Make clear whether the LLM should:
- **Execute the script** (most common): "Run `analyze_form.py` to extract fields"
- **Read as reference**: "See `analyze_form.py` for the extraction algorithm"

### Handle Errors, Don't Punt

**GOOD:**
```python
def process_file(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        print(f"File {path} not found, creating default")
        with open(path, "w") as f:
            f.write("")
        return ""
```

**BAD:**
```python
def process_file(path):
    return open(path).read()  # Punt to LLM to handle errors
```

---

## External Tool References

If a skill uses platform-specific tools (MCP, custom integrations, etc.), use fully qualified names where required by the platform.

**Example (MCP-style):**
```markdown
Use BigQuery:bigquery_schema to retrieve table schemas.
Use GitHub:create_issue to create issues.
```

Adapt naming conventions to your specific platform's requirements.

---

## Prohibited Patterns

- **Orchestration in skills** — Skills should NOT orchestrate other agents (use orchestration skills or commands)
- **Content duplication** — Skills should NOT duplicate content from other skills
- **Windows-style paths** — Always use forward slashes: `scripts/helper.py`, not `scripts\helper.py`
- **Vague descriptions** — "Helps with documents" is unacceptable
- **First-person POV** — "I can help you..." will fail discovery

---

## Evaluation-First Development

For complex skills, create evaluations BEFORE writing extensive documentation.

**Process:**
1. Identify gaps: Run the LLM on representative tasks without a skill
2. Create 3+ scenarios that test these gaps
3. Establish baseline: Measure performance without the skill
4. Write minimal instructions to address gaps
5. Iterate: Execute evaluations, compare against baseline, refine

---

## Checklist for Skill Review

Before publishing a skill:

### Core Quality
- [ ] Description is third-person, specific, includes trigger terms
- [ ] Description includes both what AND when to use
- [ ] **Methodology skills**: Description covers all three trigger patterns (direct domain, problem framing, decision language)
- [ ] SKILL.md body under 500 lines / 5,000 tokens
- [ ] Reference files are one level deep from SKILL.md
- [ ] No time-sensitive information (or in "old patterns" section)
- [ ] Consistent terminology throughout
- [ ] Examples are concrete, not abstract

### Structure
- [ ] Frontmatter includes `name` and `description` (required)
- [ ] `argument-hint` present if skill accepts arguments
- [ ] Gotchas section for non-obvious environment facts
- [ ] Templates/checklists for multi-step workflows
- [ ] Validation loops for quality-critical tasks

### Scripts (if applicable)
- [ ] Scripts solve problems rather than punt to the LLM
- [ ] Error handling is explicit and helpful
- [ ] No "voodoo constants" (all values justified)
- [ ] Required packages listed
- [ ] Forward slashes in all paths
