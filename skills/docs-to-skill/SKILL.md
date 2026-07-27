---
name: docs-to-skill
description: >-
  Documentation-to-skill conversion: transforms scraped docs into modular, actionable skills. TRIGGER: converting docs to skills, creating skill from documentation/API docs/scraped docs.
argument-hint: |-
  <doc-dir> [--name <skill-name>] [--supplementary <paths-or-urls>]
metadata:
  depends-on: [ai-engineering-expert]
---

# Docs-to-Skill Meta Skill

Transform scraped documentation into a layered skill architecture. This skill is a **pure orchestrator** - all implementation work is delegated to subagents.

## Two-Layer Documentation Model

```
Layer 1: Curated References (LLM-optimized)
├── SKILL.md with essential patterns, triggers, API tables
├── references/<module>.md — extracted per schema, source-linked
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
| `<doc-dir>` | Directory or URL | Yes | Scraped documentation directory with markdown files, or a URL to scrape via docs-scraper skill |
| `--name` | String | No | Skill name (defaults to directory name) |
| `--supplementary` | Paths/URLs | No | Tutorial docs, getting-started guides, FAQs |

## Output Structure

Flat skill with curated references merged by module and raw docs self-contained:

```
skills/<skill-name>/
├── SKILL.md                  # Essential patterns, API tables, quick starts
└── references/               # Layer 1 + Layer 2 combined
    ├── <module>.md           # Curated per schema (see extraction-rules.md)
    └── <skill-name>-raw/     # Complete raw docs (copied from source)
```

**Key design decisions:**
- No sub-skills — SKILL.md contains all essential info, references contain detailed patterns
- References extracted per schema — one file per module using template schemas from extraction-rules.md
- `$SKILL_DIR/references/<module>.md` in prose, relative paths in markdown links — `$SKILL_DIR` when cwd is ambiguous, `[text](references/<file>.md)` for standard relative-to-file links
- Raw docs copied into skill — self-contained, no external dependencies
- Quality governed by extraction rules, not line counts — atomic data, source linking, schema-first

## Artifact Storage Convention

- **Topic root:** `.lsz/{date}/{topic_creation_time}_docs-to-skill/`
- **Drafts:** `{topic_root}/draft/`
- **Learning log:** `{topic_root}/learning-log.md`
- **Generated skill:** `skills/<skill-name>/`

## Workflow (Subagent Dispatch)

### Phase 0: Doc Acquisition

**If `<doc-dir>` is a URL:** Invoke the `docs-scraper` skill (not the script directly):

```markdown
Skill tool:
  skill: "docs-scraper"
  args: "site --base-url {URL} --output-dir {TOPIC_ROOT}/draft/skills/{SKILL_NAME}/references/{SKILL_NAME}-raw/"
```

The skill handles tavily-powered discovery, llms.txt/sitemap fallback, fetching, markdown conversion, and README placeholder filling. Do NOT run `scrape.py` directly — the skill adds semantic intelligence (tavily discovery, README filling) that the script alone does not provide.

**If `<doc-dir>` is a local directory:** Copy raw docs into final location:

```bash
mkdir -p {TOPIC_ROOT}/draft/skills/{SKILL_NAME}/references/{SKILL_NAME}-raw/
cp -R {DOC_DIR}/* {TOPIC_ROOT}/draft/skills/{SKILL_NAME}/references/{SKILL_NAME}-raw/
```

**Supplementary docs (optional):** Ask user with Dialog Contract.

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

This places raw docs at their final path (`references/<skill-name>-raw/`) before any phase reads them. All subsequent phases reference the same stable location — no path shifts between analysis and generation.

---

### Phase 1: Documentation Analysis (Consolidated)

Single agent analyzes documentation and produces all planning artifacts.

**Dispatch:**
```markdown
Agent tool (architecture-scribe):
  description: "Analyze docs and extract skill components"
  prompt: |
    Read references:
    - {SKILL_DIR}/references/module-detection.md
    - {SKILL_DIR}/references/trigger-extraction.md
    - {SKILL_DIR}/references/pattern-extraction.md

    Analyze the documentation directory: {TOPIC_ROOT}/draft/skills/{SKILL_NAME}/references/{SKILL_NAME}-raw/

    Output analysis to: {TOPIC_ROOT}/draft/analysis.yaml

    Produce ALL of the following in one pass:
    1. **Structure**: File count, line counts, token estimates, directory hierarchy
    2. **Modules**: Functional groupings with source files, topics, rationale, estimated token weight
    3. **Triggers**: Domain terms, task phrases, problem-framing keywords, query-style English triggers only
    4. **Patterns**: Initialization, common usage, error handling, integration patterns, with complexity labels
    5. **Confidence notes**: Uncertainties, edge cases, and raw docs that should be checked during generation

    For modules, consider:
    - Functional groupings (commands, config, etc.)
    - Token distribution (aim for balanced modules)
    - User mental model (what would someone look up?)

    For triggers, extract what USERS would type, not internal API names:
    - Domain terms (library name, framework category)
    - Task phrases (verb + domain object)
    - Problem-framing keywords (troubleshooting scenarios)

    For patterns, prioritize practical examples:
    - Simple patterns for common operations
    - Medium patterns for workflows
    - Skip complex edge cases

    Return: Summary (≤150 words) with module proposal + path to analysis.yaml.
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

### Phase 2: Skill Generation

**Dispatch:**
```markdown
Agent tool (ai-engineering-designer):
  description: "Generate curated skill files"
  prompt: |
    Generate a domain knowledge skill from the analysis results.

    **Mandatory first step:** Invoke the ai-engineering-expert skill with `skill-authoring` argument to load skill design methodology.
    Apply its guidance on skill authoring (frontmatter, descriptions, triggers, structure, path convention).

    **Input files:**
    - Analysis: {TOPIC_ROOT}/draft/analysis.yaml
    - Raw docs (already in place): {TOPIC_ROOT}/draft/skills/{SKILL_NAME}/references/{SKILL_NAME}-raw/

    **Methodology references (read after ai-engineering-expert skill-authoring):**
    - {SKILL_DIR}/references/skill-template.md
    - {SKILL_DIR}/references/compilation-contract.md
    - {SKILL_DIR}/references/extraction-rules.md

    **Output to:** {TOPIC_ROOT}/draft/skills/{SKILL_NAME}/

    Generate this FLAT structure (no sub-skills):
    ```
    {SKILL_NAME}/
    ├── SKILL.md                  # Essential patterns, API tables, quick starts
    └── references/               # Curated by schema + raw docs
        ├── <module>.md           # Curated per schema (see extraction-rules.md)
        └── <skill-name>-raw/     # Already in place from Phase 0
    ```

    SKILL.md MUST include:
    - Essential patterns for all modules (consolidated)
    - API reference tables for all modules
    - Quick start guide
    - References table with source column using `$SKILL_DIR/references/<module>.md` path pattern
    - "When to use raw docs" section with escalation criteria (missing flag, complete API, conflict resolution)
    - "Path Convention" section: `$SKILL_DIR/` in prose (cwd unknown), relative paths in markdown links (relative-to-file)
    - Dedicated Triggers section with domain terms, task phrases, and problem phrases
    - Discouraged patterns / common pitfalls where applicable
    - Default values in configuration tables where available from source

    Each reference file MUST follow extraction-rules.md:
    - Mandatory metadata header (version, date, source, author, generated by, brief)
    - Choose appropriate schema (CLI Reference, Technical Docs, etc.)
    - Extract atomic data with source-to-row links
    - One idea per paragraph, sentences under 25 words
    - Link key claims back to raw docs

    Raw docs are already at references/<skill-name>-raw/ — do NOT move or copy them.

    Return: Summary (≤150 words) + paths to generated files.
```

**Script validation:**
```bash
uv run {SKILL_DIR}/scripts/compile.py validate-skill {TOPIC_ROOT}/draft/skills/{SKILL_NAME}/
```

**Remediation on failure:** If validation returns `valid: false`, re-dispatch a new developer agent with the issues list and the previous draft path. Do NOT resume the old agent — spawn fresh with feedback.

---

### Phase 3: Quality Evaluation

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
    - Each reference file has raw docs fallback pointers
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

### Phase 4: Install (if accepted)

Copy generated skill from `{TOPIC_ROOT}/draft/skills/{SKILL_NAME}/` to `skills/{SKILL_NAME}/`.

## Reference Files

Subagents load these for methodology:

- `references/module-detection.md` - Module detection methodology
- `references/trigger-extraction.md` - Trigger extraction patterns
- `references/pattern-extraction.md` - Pattern extraction methodology
- `references/extraction-rules.md` - Extraction, synthesis, and referencing rules with template schemas
- `references/skill-template.md` - Template for generated SKILL.md
- `references/quality-metrics.md` - Quality evaluation criteria
- `references/compilation-contract.md` - Script/LLM interface contract

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

Aggregate lessons into the relevant specialized reference file (module-detection, trigger-extraction, pattern-extraction, or quality-metrics).

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
3. **Schema-driven references**: Per-module files follow template schemas from extraction-rules.md, ensuring consistent quality
4. **Self-contained**: Raw docs are copied into `references/<skill-name>-raw/` so the skill works without external dependencies
