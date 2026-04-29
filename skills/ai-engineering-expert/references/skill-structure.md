# Skill Structure Reference

Directory layout, file organization, and progressive disclosure patterns for LSZ skills.

## Skill Location

**All skills MUST be placed under `<project_root>/skills/`.**

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

**Form filling**: See [FORMS.md](references/FORMS.md) for complete guide
**API reference**: See [REFERENCE.md](references/REFERENCE.md) for all methods
```

**Pattern 2: Conditional details**
```markdown
## Creating documents

Use docx-js for new documents.

**For tracked changes**: See [REDLINING.md](references/REDLINING.md)
```

**ANTI-PATTERN (too deep):**
```markdown
# SKILL.md
See [advanced.md](references/advanced.md)...

# references/advanced.md
See [details.md](details.md)...  # ← LLM may only partially read this
```

## Skill Body Structure

1. **Purpose statement** — What the skill does (1-2 sentences)
2. **When to use** — Explicit trigger conditions (optional if covered in description)
3. **Execution contract** — How to invoke, arguments, expected behavior
4. **Workflow phases** — Ordered steps if applicable
5. **Output format** — Expected artifacts or responses

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
