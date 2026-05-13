# Compilation Contract

Interface contract between LLM generation and script compilation.

## Overview

The compilation pipeline produces a flat, self-contained skill:

```
<skill-name>/
├── SKILL.md                  # Essential patterns, API tables, quick starts
└── references/               # Layer 1 + Layer 2 combined
    ├── <module>.md           # Curated per schema (see extraction-rules.md)
    └── <skill-name>-raw/     # Complete raw docs (copied from source)
```

Stages:

```
LLM Generation → Script Compiler → LLM Evaluator → User Review
```

## Official Skill Structure

Generated skills must match the flat structure defined in SKILL.md's "Output Structure" section.

## Stage 1: LLM Generation

**Input:**
- Structure report (JSON from `validate-structure.py`)
- Supplementary docs (optional, fetched if URLs)
- Raw docs path (for Layer 2 pointers)

**Output:** Draft artifacts in `.lsz/{topic}/draft/`
```
draft/
├── modules.yaml      # Proposed module structure
├── triggers.yaml     # Extracted triggers
├── patterns.yaml     # Extracted patterns
└── skills/
    └── {skill-name}/
        ├── SKILL.md
        └── references/
            ├── <module>.md
            └── <skill-name>-raw/
```

**Error Handling:**
- If structure report missing, fail with error
- If supplementary docs fail to fetch, warn and continue

## Stage 2: Script Compiler

**Input:** Draft artifacts from Stage 1

**Commands:**
```bash
# Validate triggers
uv run scripts/compile.py validate-triggers .lsz/{topic}/draft/triggers.yaml

# Validate skill structure
uv run scripts/compile.py validate-skill .lsz/{topic}/draft/skills/{name}/
```

**Output:**
```json
{
  "valid": true,
  "structure": {
    "main_skill": true,
    "sub_skills": 5,
    "references_count": 15
  },
  "issues": [],
  "warnings": []
}
```

**Deterministic Checks:**

| Check | Error Level | Description |
|-------|-------------|-------------|
| YAML syntax | Error | Valid YAML format |
| Name match | Error | `name` matches directory |
| Description length | Error | <=1024 chars |
| SKILL.md line count | Warning | <=500 lines recommended |
| Reference file metadata | Error | Must have version, date, source, author, brief header |
| Reference file schema | Warning | Must follow a template schema from extraction-rules.md |
| Source linking | Warning | Key claims link to raw docs |
| `$SKILL_DIR` paths | Warning | References use `$SKILL_DIR/` not relative paths |
| No sub-skills | Error | No `skills/` directory in output |
| Raw docs present | Warning | `references/<skill-name>-raw/` should exist |
| Link existence | Warning | Internal links exist |
| Trigger duplicates | Warning | No duplicates across modules |
| Trigger format | Error | No regex/special chars |

## Stage 3: LLM Evaluator

**Input:**
- Validated draft from Stage 2
- Compilation report

**Output:** Quality report
```yaml
quality_report:
  overall_score: 0.85
  scores:
    trigger_coverage: 0.90
    pattern_usefulness: 0.80
    beginner_friendliness: 0.75
    documentation_completeness: 0.85
    navigation_clarity: 0.90
    graceful_degradation: 0.80
  suggestions:
    - "Add pattern for 'how to handle resize events'"
```

**Quality Criteria:** See `quality-metrics.md`

## Stage 4: User Review

**Input:**
- Quality report from Stage 3
- Generated skill files

**Interactions:**
1. Show quality report
2. Present suggestions as options
3. Allow user to:
   - Accept as-is
   - Request specific improvements
   - Manually edit files

**Output:** Approved skill in `skills/<skill-name>/`

## File Format Contracts

### modules.yaml

```yaml
proposed_modules:
  - name: <string>
    source_dirs: [<string>, ...]
    topics: [<string>, ...]
    estimated_tokens: <int>
```

### triggers.yaml

```yaml
triggers:
  <module>:
    types: [<string>, ...]
    functions: [<string>, ...]
    queries: [<string>, ...]
    problems: [<string>, ...]
```

### patterns.yaml

```yaml
patterns:
  <module>:
    - name: <string>
      code: <multiline string>
      complexity: simple | medium | complex
      category: initialization | common_usage | stateful | error_handling | integration
```

### quality_report.yaml

```yaml
quality_report:
  overall_score: <float 0-1>
  scores:
    <criterion>: <float 0-1>
  suggestions: [<string>, ...]
```

## Error Handling

| Error Type | Stage | Action |
|------------|-------|--------|
| Invalid YAML | Script | Fail with line number |
| Missing file | Script | Fail with path |
| Duplicate triggers | Script | Warn with duplicates list |
| Low quality score | LLM Evaluator | Show suggestions, allow proceed |
| User rejection | User Review | Return to relevant phase |

## Learning Record Format

Saved after user corrections:

```yaml
learning_record:
  phase: <phase name>
  llm_proposed: <original value>
  user_adjusted: <corrected value>
  lesson: <extracted pattern>
```

## Design Decision: No Wiki Layer

The original design included an LLM-processed wiki layer between curated references and raw docs. This was removed because:

1. **Information loss risk**: Processing (flattening, chrome removal) risks stripping details critical for edge cases
2. **No clear value**: Wiki would be neither optimized (like references) nor complete (like raw docs)
3. **Simpler architecture**: Two layers sufficient for 80% + edge case coverage
4. **Source of truth**: Raw docs remain authoritative for tricky scenarios

## Design Decision: Flat Structure (No Sub-Skills)

The original design used `skills/<module>/SKILL.md` sub-skills. This was changed to a flat structure:

1. **Simpler navigation**: One SKILL.md with essential info, references for deep dives
2. **`$SKILL_DIR` paths**: Stable path pattern like scripts, no brittle relative paths
3. **Schema-driven references**: Per-module files follow template schemas from extraction-rules.md
4. **Self-contained**: Raw docs copied into `references/<skill-name>-raw/`, no external dependencies
