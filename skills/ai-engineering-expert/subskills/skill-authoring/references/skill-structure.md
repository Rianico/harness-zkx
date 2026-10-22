# Skill Structure Reference

Directory layout, file organization, and progressive disclosure patterns for LSZ skills.

## Progressive Disclosure & Context Economics

Skills share the context window with conversation history, system prompts, and other skills. Every token competes for attention.

### Hard Limits

| Metric | Limit | Rationale |
|---|---|---|
| SKILL.md body | **500 lines** / **5,000 tokens** | Optimal performance threshold |
| Reference depth | **One level** from SKILL.md | LLMs may partially read nested refs |

### Three-Level Loading Hierarchy

| Level | Content | When Loaded |
|---|---|---|
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

**Anti-Pattern (Nested references):**
```markdown
# SKILL.md
See [advanced.md](references/advanced.md)...

# references/advanced.md
See [details.md](details.md)...  # Nested links risk partial reads
```

## Directory Organization & Layout

### Source of Truth and Discovery Mirror

**Source of truth: `<project_root>/skills/<skill-name>/`.** Agents discover skills through the `.agents/skills/` convention (the Agent Skills / Pi discovery path). Expose each skill by mirroring or symlinking it into `~/.agents/skills/<name>` or project `.agents/skills/<name>`. This repo symlinks `skills/<name>` into `.agents/skills/<name>`.

```
<project_root>/
├── skills/              # Source of truth
│   └── <skill-name>/
│       └── ...
└── .agents/skills/      # Discovery mirror (symlinks), per the Agent Skills convention
    └── <skill-name> -> ../../skills/<skill-name>
```

Do NOT author skills in `.claude/skills/` or other runtime-specific locations. Those are generated or synced, never the source.

### Standard Directory Anatomy

```
skills/
└── <skill-name>/
    ├── SKILL.md          # Required: skill definition (<500 lines)
    ├── references/       # Optional: deep reference materials, examples, specs (1 level deep)
    └── scripts/          # Optional: executable scripts for deterministic execution (uv run)
```

| Component | Required | Purpose |
|---|---|---|
| `SKILL.md` | Yes | Entry contract and operational instructions |
| `references/` | No | Deep domain docs loaded into context only when needed |
| `scripts/` | No | Deterministic code for repetitive tasks, linters, or gates |

Optional folders:
- `prompts/` -- Template prompts
- `README.md` -- Extended documentation

### Skill Body Structure

1. **Purpose statement** -- What the skill does (1-2 sentences)
2. **When to use** -- Explicit trigger conditions (matches `Use when...`)
3. **Execution contract** -- How to invoke, arguments, expected behavior
4. **Workflow phases** -- Ordered steps if procedural
5. **Output format** -- Expected artifacts or response contract

### Complete Worked Example

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

**Referencing bundled resources:**

```markdown
## Usage

Run the helper script:

```bash
uv run $SKILL_DIR/scripts/helper.py --input data.json
```

Read the domain reference:
See [patterns](references/patterns.md) for architectural trade-offs.
```

## Scripts in Skills

### When to Bundle Scripts

Bundle scripts when the LLM repeatedly reinvents logic: parsing data, calculating statistics, or running multi-step verification.

### Script Execution Intent

Make clear whether the LLM should:
- **Execute the script** (most common): "Run `analyze_form.py` to extract fields"
- **Read as reference**: "See `analyze_form.py` for the extraction algorithm"

### Handle Errors, Don't Punt

Handle failure modes natively inside the script rather than dumping raw stack traces for the LLM to interpret:

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
    return open(path).read()  # Punts raw exception to LLM
```

### Script Invocation Conventions

**Direct execution from any directory:**
```bash
uv run $SKILL_DIR/scripts/helper.py
```

**Never `cd` into the skill directory:**
```bash
# BAD: stateful cwd mutation
cd ~/.claude/skills/my-skill && uv run scripts/helper.py

# GOOD: stateless invocation
uv run $SKILL_DIR/scripts/helper.py
```

**Runtime artifacts location:**
Store temporary artifacts in the workspace topic root (e.g. `.lsz/` or temporary build paths). Never commit runtime artifacts into the skill directory.

**Inline script metadata (PEP 723):**
```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["rich>=13.0.0"]
# ///
```
This enables `uv run` to manage dependencies hermetically without a dedicated `pyproject.toml`.
