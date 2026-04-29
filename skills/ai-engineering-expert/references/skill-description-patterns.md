# Skill Description Patterns

How to write skill descriptions that trigger reliably. Descriptions are the primary trigger surface for skill discovery.

## Core Requirements

- Write in **third person** (injected into system prompt; inconsistent POV causes discovery failures)
- Include **both** what the skill does AND when to use it
- Lead with a one-line identity sentence
- Include trigger vocabulary: verbs, artifact names, domains, topic words
- Signal scope and depth explicitly
- Maximum 1024 characters

## Good vs Bad Examples

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

## Trigger Pattern Coverage (Methodology Skills)

For domain-knowledge and methodology skills (e.g., `architecture-expert`, `tdd-expert`, `python-expert`), descriptions MUST cover all natural trigger patterns users employ:

| Pattern | Example Phrases | Why It Matters |
|---------|-----------------|----------------|
| **Direct domain** | "design the architecture", "implement authentication", "build a cache layer" | Explicit request for the domain |
| **Problem framing** | "this code is a mess", "need to scale", "too many bugs", "slow queries" | User describes symptom, not domain |
| **Decision language** | "should we use X or Y", "which approach", "trade-off between", "is this the right pattern" | User needs guidance, not action |

**Rationale:** LLMs often miss methodology skills when users describe problems or decisions rather than explicitly naming the domain. Without problem-framing vocabulary, the skill won't trigger for "this code is a mess" — only for "review the architecture."

## Explicit TRIGGER Clause Pattern

For methodology skills, use an explicit TRIGGER clause:

```yaml
description: "Architecture expertise for system design, refactoring, service boundaries, and trade-offs. TRIGGER when: designing architecture, defining boundaries, evaluating approaches; OR user mentions scaling problems, messy code, coupling issues, tech debt, performance bottleneck; OR user asks 'should we', 'which approach', 'trade-off between', 'is this the right pattern'."
```

**ANTI-PATTERN (missing problem framing):**
```yaml
description: "Architecture expertise for system design. Use for design critique and refactoring strategy."
# ↑ Won't trigger when user says "this code is a mess"
```

## Name Requirements

- Maximum 64 characters
- Lowercase letters, numbers, and hyphens only
- No XML tags
- Prefer **gerund form** (verb + -ing): `processing-pdfs`, `analyzing-spreadsheets`
- Acceptable alternatives: noun phrases (`pdf-processing`), action-oriented (`process-pdfs`)
- Avoid: vague names (`helper`, `utils`), overly generic (`documents`, `data`)

## Argument Hint Format

- Use square brackets for optional parts: `[optional]`
- Use angle brackets for required parts: `<required>`
- Include common flags after the main arguments

```yaml
argument-hint: "[balanced|uncle-bob|fowler|evans] <topic>"
```

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

\`\`\`bash
python scripts/migrate.py --verify --backup
\`\`\`

Do not modify the command or add additional flags.
```

### Provide Defaults, Not Menus

When multiple tools/approaches could work, pick a default and mention alternatives briefly.

**GOOD:**
```markdown
Use pdfplumber for text extraction:

\`\`\`python
import pdfplumber
\`\`\`

For scanned PDFs requiring OCR, use pdf2image with pytesseract instead.
```

**BAD:**
```markdown
You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image...
```

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
