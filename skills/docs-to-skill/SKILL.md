---
name: docs-to-skill
description: |
  Transform scraped documentation into practical, actionable skills with modular structure.
  TRIGGER when: converting docs to skills, creating skill from documentation, generating skill from API docs,
  building skill from scraped docs, "make a skill from these docs", "create skill from documentation",
  "transform docs into skill", documentation to skill conversion.
argument-hint: "<doc-dir> [--name <skill-name>] [--supplementary <paths-or-urls>]"
---

# Docs-to-Skill Meta Skill

Transform scraped documentation into a layered skill architecture. This skill is a **pure orchestrator** - all implementation work is delegated to subagents.

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

**Why no LLM-processed wiki:**

LLM processing risks information loss. For edge cases where LLM knowledge gaps matter most, you need:
- **Every detail** - obscure parameters, edge case behaviors
- **Original context** - how the expert author explained it
- **No information loss** - processing always risks stripping "unimportant" details that become critical

Raw docs are copied into the skill at `references/<skill-name>-raw/` so the skill is fully self-contained.

## Input

| Input | Type | Required | Description |
|-------|------|----------|-------------|
| `<doc-dir>` | Directory | Yes | Scraped documentation directory with markdown files |
| `--name` | String | No | Skill name (defaults to directory name) |
| `--supplementary` | Paths/URLs | No | Tutorial docs, getting-started guides, FAQs |

## Output Structure

Flat skill with curated references merged by module and raw docs self-contained:

```
skills/<skill-name>/
├── SKILL.md                  # Essential patterns, API tables, quick starts
└── references/               # Layer 1 + Layer 2 combined
    ├── <module>.md           # Merged curated + key raw doc content per module (up to 2000 lines)
    └── <skill-name>-raw/     # Complete raw docs (copied from source)
```

**Key design decisions:**
- No sub-skills — SKILL.md contains all essential info, references contain detailed patterns
- References merged by module dimension — one file per module, not one file per topic
- `$SKILL_DIR/references/<module>.md` path pattern — like scripts, not relative paths
- Raw docs copied into skill — self-contained, no external dependencies
- Reference files up to 2000 lines — allows substantial raw doc inclusion

## Artifact Storage Convention

- **Topic root:** `.lsz/{date}/{topic_creation_time}_docs-to-skill/`
- **Drafts:** `{topic_root}/draft/`
- **Learning log:** `{topic_root}/learning-log.md`
- **Generated skill:** `skills/<skill-name>/`

## Workflow (Subagent Dispatch)

### Phase 0: Supplementary Docs (Optional)

Ask user with Dialog Contract before proceeding.

**Dialog Contract:**
```yaml
Dialog:
  header: "Extra Docs"
  question: "Do you have supplementary documentation to enhance the skill?"
  options:
    - label: "No, skip"
      description: "Use only scraped API docs"
    - label: "Local files"
      description: "Provide local file paths (tutorials, guides, FAQs)"
    - label: "Online docs"
      description: "Provide URLs to fetch (official tutorials, getting-started pages)"
```

If user provides supplementary docs, fetch and store at `{topic_root}/supplementary/`.

---

### Phase 1: Structure Analysis

**Dispatch:**
```markdown
Agent tool (Explore):
  description: "Analyze documentation structure"
  prompt: |
    Read reference: {SKILL_DIR}/references/module-detection.md

    Analyze the documentation directory: {DOC_DIR}

    Output a structure report to: {TOPIC_ROOT}/draft/structure-report.json

    Include:
    - File count and token estimates
    - Directory hierarchy
    - API surface summary (types, functions)
    - Issues (empty files, missing indices)

    Return: Summary (≤100 words) + path to structure report.
```

**Script validation:**
```bash
uv run {SKILL_DIR}/scripts/validate-structure.py {DOC_DIR} --output {TOPIC_ROOT}/draft/structure-report.json
```

---

### Phase 2: Module Detection

**Dispatch:**
```markdown
Agent tool (architect):
  description: "Propose module structure"
  prompt: |
    Read reference: {SKILL_DIR}/references/module-detection.md

    Analyze structure report: {TOPIC_ROOT}/draft/structure-report.json

    Propose module groupings based on directory structure and API surface.

    Output modules to: {TOPIC_ROOT}/draft/modules.yaml

    Format per reference file. Consider:
    - Functional groupings
    - Token distribution
    - User mental model

    Return: Summary (≤150 words, star rules format) + path to modules.yaml.
```

**Checkpoint:**
```yaml
Dialog:
  header: "Modules"
  question: "Are these module groupings correct?"
  options:
    - label: "Yes, proceed"
      description: "Use detected modules"
    - label: "Merge some modules"
      description: "Combine related modules"
    - label: "Split some modules"
      description: "Break down large modules"
    - label: "Custom grouping"
      description: "Provide custom module structure"
```

Record user adjustments to `{TOPIC_ROOT}/learning-log.md`.

---

### Phase 3: Trigger Extraction

**Dispatch:**
```markdown
Agent tool (Explore):
  description: "Extract trigger keywords"
  prompt: |
    Read reference: {SKILL_DIR}/references/trigger-extraction.md

    Extract triggers from:
    - Structure report: {TOPIC_ROOT}/draft/structure-report.json
    - Supplementary docs: {TOPIC_ROOT}/supplementary/ (if exists)
    - Source documentation: {DOC_DIR}

    Output triggers to: {TOPIC_ROOT}/draft/triggers.yaml

    Extract:
    - Type names from API surface
    - Function names from API surface
    - Query phrases from headings/FAQ
    - Problem-framing keywords from troubleshooting

    Return: Summary (≤100 words) + path to triggers.yaml.
```

**Script validation:**
```bash
uv run {SKILL_DIR}/scripts/compile.py validate-triggers {TOPIC_ROOT}/draft/triggers.yaml
```

**Checkpoint:**
```yaml
Dialog:
  header: "Triggers"
  question: "Are these triggers complete?"
  options:
    - label: "Yes, proceed"
      description: "Use extracted triggers"
    - label: "Add triggers"
      description: "Specify additional trigger keywords"
    - label: "Remove triggers"
      description: "Remove some triggers"
```

---

### Phase 4: Pattern Extraction

**Dispatch:**
```markdown
Agent tool (Explore):
  description: "Extract code patterns"
  prompt: |
    Read reference: {SKILL_DIR}/references/pattern-extraction.md

    Extract patterns from:
    - Supplementary docs: {TOPIC_ROOT}/supplementary/ (if exists, prioritize)
    - Source documentation: {DOC_DIR}
    - FAQ sections

    Output patterns to: {TOPIC_ROOT}/draft/patterns.yaml

    Extract by category:
    - Initialization patterns
    - Common usage patterns
    - Stateful patterns
    - Error handling patterns
    - Integration patterns

    Return: Summary (≤100 words) + path to patterns.yaml.
```

---

### Phase 5: Skill Generation

**Dispatch:**
```markdown
Agent tool (developer):
  description: "Generate curated skill files"
  prompt: |
    Read references:
    - {SKILL_DIR}/references/skill-template.md
    - {SKILL_DIR}/references/compilation-contract.md

    Generate skill from drafts:
    - Modules: {TOPIC_ROOT}/draft/modules.yaml
    - Triggers: {TOPIC_ROOT}/draft/triggers.yaml
    - Patterns: {TOPIC_ROOT}/draft/patterns.yaml
    - Raw docs location: {DOC_DIR}

    Output to: {TOPIC_ROOT}/draft/skills/{SKILL_NAME}/

    Generate this FLAT structure (no sub-skills):
    ```
    {SKILL_NAME}/
    ├── SKILL.md                  # Essential patterns, API tables, quick starts
    └── references/               # Merged by module + raw docs
        ├── <module>.md           # Curated + key raw doc content (up to 2000 lines)
        └── raw/                  # Complete raw docs (copied from {DOC_DIR})
    ```

    SKILL.md MUST include:
    - Essential patterns for all modules (consolidated)
    - API reference tables for all modules
    - Quick start guide
    - References table using `$SKILL_DIR/references/<module>.md` path pattern
    - "When to use raw docs" guidance pointing to `$SKILL_DIR/references/<skill-name>-raw/`

    Each reference file MUST include:
    - Key patterns from the module (from patterns.yaml)
    - Curated reference content merged into single file
    - Key raw doc excerpts for that module (API signatures, important details)
    - Up to 2000 lines per file

    Copy raw docs into references/<skill-name>-raw/ preserving source structure.

    Return: Summary (≤150 words) + paths to generated files.
```

**Script validation:**
```bash
uv run {SKILL_DIR}/scripts/compile.py validate-skill {TOPIC_ROOT}/draft/skills/{SKILL_NAME}/
```

---

### Phase 6: Quality Evaluation

**Dispatch:**
```markdown
Agent tool (code-reviewer):
  description: "Evaluate skill quality"
  prompt: |
    Read reference: {SKILL_DIR}/references/quality-metrics.md

    Evaluate generated skill at: {TOPIC_ROOT}/draft/skills/{SKILL_NAME}/

    Score against criteria:
    - Trigger Coverage (20%)
    - Pattern Usefulness (20%)
    - Beginner Friendliness (15%)
    - Documentation Completeness (15%)
    - Navigation Clarity (15%)
    - Graceful Degradation (15%)

    Also verify:
    - Each sub-skill has raw docs fallback pointers
    - Layer 1 → Layer 2 escalation path is clear
    - Output structure matches official skill format

    Output quality report to: {TOPIC_ROOT}/draft/quality-report.yaml

    Return: Summary with overall score (≤100 words) + path to quality report.
```

**Checkpoint:**
```yaml
Dialog:
  header: "Review"
  question: "Quality score: {SCORE}. Accept generated skill?"
  options:
    - label: "Accept and install"
      description: "Copy skill to skills/{SKILL_NAME}/"
    - label: "Keep as draft"
      description: "Keep in .lsz/ for manual review"
    - label: "Regenerate with feedback"
      description: "Provide feedback for improvement"
```

---

### Phase 7: Install (if accepted)

Copy generated skill from `{TOPIC_ROOT}/draft/skills/{SKILL_NAME}/` to `skills/{SKILL_NAME}/`.

## Reference Files

Subagents load these for methodology:

- `references/module-detection.md` - Module detection methodology
- `references/trigger-extraction.md` - Trigger extraction patterns
- `references/pattern-extraction.md` - Pattern extraction methodology
- `references/skill-template.md` - Template for generated SKILL.md
- `references/quality-metrics.md` - Quality evaluation criteria
- `references/compilation-contract.md` - Script/LLM interface contract
- `references/learning-patterns.md` - Patterns from user corrections

## Scripts

Deterministic validation scripts:

- `scripts/validate-structure.py` - Structure analysis
- `scripts/compile.py` - Validation and curation

## Learning Mechanism

After each user correction, append to `{TOPIC_ROOT}/learning-log.md`:

```markdown
## {Phase Name}
**LLM Proposed:** {original}
**User Adjusted:** {corrected}
**Lesson:** {extracted pattern}
```

Aggregate lessons into `references/learning-patterns.md` periodically.

## Design Rationale

### Why No Wiki Layer

The original design included an LLM-processed wiki as an intermediate layer. This was removed because:

1. **Information loss risk**: LLM processing (flattening, chrome removal, summarization) risks stripping details that become critical in edge cases
2. **No unique value**: A processed wiki sits between curated references and raw docs without clear advantages — it's neither optimized for common cases (like references) nor complete (like raw docs)
3. **Simpler is better**: Two layers (curated + raw) are sufficient and easier to maintain
4. **Source of truth**: Raw docs preserved in their original form remain the authoritative fallback for tricky scenarios

For edge cases where LLM knowledge gaps are most painful, you need 100% of the information, not 95% after processing.

### Why Flat Structure (No Sub-Skills)

The original design used `skills/<module>/SKILL.md` sub-skills for each module. This was changed to a flat structure because:

1. **Simpler navigation**: One SKILL.md with essential info + references table, no indirection through sub-skills
2. **`$SKILL_DIR` paths**: Use path patterns like scripts (`$SKILL_DIR/references/<module>.md`) instead of brittle relative paths
3. **Merged references**: Per-module reference files (up to 2000 lines) combine curated patterns + key raw doc content, avoiding the need for sub-skill SKILL.md files
4. **Self-contained**: Raw docs are copied into `references/<skill-name>-raw/` so the skill works without external dependencies
