# Skill Structure Convention

## Purpose
Ensure all skills follow a consistent directory layout and frontmatter format for discoverability and maintainability.

## Skill Location

**All skills in this project MUST be placed under `<project_root>/skills/`.**

```
<project_root>/
└── skills/
    └── <skill-name>/
        └── ...
```

Do NOT place skills in `.claude/skills/` or other locations.

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

## Required Frontmatter

All skills MUST include in YAML frontmatter:

```yaml
---
name: <skill-name>
description: <one-line description optimized for trigger recall>
argument-hint: "<usage syntax>"  # If skill accepts arguments
---
```

### Description Requirements
- Lead with a one-line identity sentence
- Include trigger vocabulary (verbs, artifact names, domains)
- Signal scope and depth explicitly
- Mention key integrations when they affect execution

### Argument Hint Format
- Use square brackets for optional parts: `[optional]`
- Use angle brackets for required parts: `<required>`
- Include common flags after the main arguments

## Progressive Disclosure

Skills use a three-level loading system to optimize context usage:

| Level | Content | When Loaded |
|-------|---------|-------------|
| 1. Metadata | `name` + `description` from frontmatter | Always in context (~100 words) |
| 2. SKILL.md body | Full skill instructions | When skill triggers (<500 lines ideal) |
| 3. Bundled resources | `references/`, `scripts/` | As needed (unlimited) |

**Guidelines:**
- Keep `SKILL.md` under 500 lines
- Put deep methodology in `references/`
- Put executable scripts in `scripts/`
- Reference files clearly from `SKILL.md` with guidance on when to read them

## Skill Body Structure

1. **Purpose statement** — What the skill does
2. **Execution contract** — How to invoke the skill
3. **Workflow phases** — Ordered steps if applicable
4. **Output format** — Expected artifacts or responses

## Prohibited Patterns
- Skills should NOT contain orchestration logic (use orchestration-like skills)
- Skills should NOT duplicate content from other skills

## Example: Complete Skill Structure

```
skills/
└── my-skill/
    ├── SKILL.md                    # Skill definition
    ├── references/
    │   ├── patterns.md             # Domain patterns
    │   └── examples.md             # Usage examples
    └── scripts/
        ├── helper.py               # Python helper script
        └── process.sh              # Shell script
```

**SKILL.md references scripts:**

```markdown
## Usage

Run the helper script:

\`\`\`bash
./scripts/helper.py --input data.json
\`\`\`
```
