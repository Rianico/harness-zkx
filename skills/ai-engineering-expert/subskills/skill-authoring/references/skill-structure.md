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

**Source of truth: `<project_root>/skills/<skill-name>/`.** Agents discover skills through the `.agents/skills/` convention. Expose each skill by mirroring or symlinking it into `~/.agents/skills/<name>` or project `.agents/skills/<name>`.

The project `.agents/` path is gitignored. It is a mixed install target. Repo skills can be symlinked into `.agents/skills/<name>`. Standalone or vendored skills can be real directories. `~/.agents/skills/` is the user-global mirror. It can also contain non-repo skills.

```
<project_root>/
├── skills/              # Source of truth (tracked)
│   └── <skill-name>/
│       └── ...
└── .agents/skills/      # Local install target (gitignored, mixed)
    ├── <skill-name> -> ../../skills/<skill-name>
    └── <vendored-skill>/   # Real directory
```

`validate-deps.py` scans `skills/` only. It does not scan `.agents/skills/`. Author every owned skill under `skills/`.

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

Structure the skill body according to its taxonomy type:

#### 1. Workflow Skills: Philosophy First, Then Workflow

Workflow skills own procedures and state transitions. They must anchor mental models before listing execution steps:
1. **Philosophy & Foundation**: Core mental model, invariants, design constraints, and non-goals.
2. **Operational Workflow**: Ordered phases, deterministic commands, error handling, and completion criteria.
3. **Execution Contract**: How to invoke the skill, arguments, and expected response format.

#### 2. Knowledge Skills: Mental Model & Invariants First, Then Reference

Knowledge skills provide on-demand domain expertise. They do not own execution pipelines:
1. **Core Mental Model**: Architectural trade-offs, foundational invariants, and domain rules.
2. **Topical Guidance & Gotchas**: Practical patterns with code shapes, anti-patterns, and framework failure modes.
3. **Pointers to Deep Assets**: Markdown links to one-level-deep reference materials. Never invent artificial procedural workflows for reference material.

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
uv run <skill-dir>/scripts/helper.py --input data.json
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
uv run <skill-dir>/scripts/helper.py
```

**Never `cd` into the skill directory:**
```bash
# BAD: stateful cwd mutation
cd ~/.claude/skills/my-skill && uv run scripts/helper.py

# GOOD: stateless invocation
uv run <skill-dir>/scripts/helper.py
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
