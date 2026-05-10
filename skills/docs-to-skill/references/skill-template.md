# Skill Template

Template for generating flat skills (no sub-skills) from documentation.

## Two-Layer Documentation Model

```
Layer 1: Curated References (LLM-optimized)
├── SKILL.md with essential patterns, triggers, API tables
├── references/<module>.md merged by module (up to 2000 lines)
├── Covers 80% of queries from memory
└── Fast retrieval, minimal file reads

Layer 2: Raw Docs (complete API surface, self-contained)
├── references/<skill-name>-raw/ — copied from source into skill
├── Covers edge cases, obscure APIs, tricky scenarios
└── Skill is fully self-contained, no external dependencies
```

## Skill Structure

```
<skill-name>/
├── SKILL.md                  # Essential patterns, API tables, quick starts
└── references/               # Layer 1 + Layer 2 combined
    ├── <module>.md           # Merged curated + key raw doc content (up to 2000 lines)
    └── raw/                  # Complete raw docs (copied from source)
        └── <source-structure>/
```

## YAML Frontmatter

```yaml
---
name: <skill-name>
description: |
  <what the skill does>. TRIGGER when: <trigger scenarios>
argument-hint: "[topic]"
---
```

**Requirements:**
- `name`: Lowercase, alphanumeric + hyphens, matches directory name
- `description`: Third-person, includes WHAT and WHEN, <=1024 chars
- `argument-hint`: Optional, provides autocomplete hint

## SKILL.md Template

```markdown
---
name: <skill-name>
description: |
  <what>. TRIGGER when: <triggers>
argument-hint: "[topic]"
---

# <Skill Name>

> **Version:** <version> | **Last Updated:** <date>
>
> Check for updates: <package-url>

<one-sentence purpose>

## Code Generation Rules

1. <language/framework specific rules>
2. <version requirements>

## Quick Start

<simplest working example>

## Core Concepts

1. **Concept 1** - <description>
2. **Concept 2** - <description>

## <Key Pattern Category 1>

<patterns with code examples>

## <Key Pattern Category 2>

<patterns with code examples>

## API Reference Table

| Function/Type | Description | Example |
|---------------|-------------|---------|
| `<api>` | <description> | `<example>` |

## References

For detailed patterns and complete API documentation, read:

| Module | File | Topics |
|--------|------|--------|
| <module1> | `$SKILL_DIR/references/<module1>.md` | <topics> |
| <module2> | `$SKILL_DIR/references/<module2>.md` | <topics> |

For edge cases and complete API surface, read `$SKILL_DIR/references/<skill-name>-raw/`.

## When Writing Code

1. <guideline>
2. <guideline>

## When Answering Questions

1. Answer from patterns and tables above first
2. If the question involves deeper details, read `$SKILL_DIR/references/<module>.md`
3. For edge cases, read `$SKILL_DIR/references/<skill-name>-raw/`
4. If still insufficient, inform user and answer from built-in knowledge
```

## Reference File Template

Each `references/<module>.md` contains:

```markdown
# <Skill Name> <Module>

> <one-line description>

## Key Patterns
(most important patterns from this module)

## API Reference
(API table for this module)

## <Topic 1>
(curated + key raw doc content)

## <Topic 2>
(curated + key raw doc content)

## Complete API: <Key Type>
(relevant sections from raw docs — API signatures, method docs)
```

## Template Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `<skill-name>` | User input | Skill name |
| `<version>` | User input or docs | Library version |
| `<date>` | Generation time | Last updated date |
| `<triggers>` | Phase 3 output | Trigger keywords |
| `<patterns>` | Phase 4 output | Extracted patterns |
| `<api>` | Phase 1 output | API surface |

## Size Constraints

- SKILL.md body: <=500 lines
- Reference files: <=2000 lines each
- API Reference Table: <=20 rows per table

## Path Convention

- Use `$SKILL_DIR/references/<module>.md` — not relative paths like `../../references/`
- Raw docs: `$SKILL_DIR/references/<skill-name>-raw/` — self-contained within skill
