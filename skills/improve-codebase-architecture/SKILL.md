---
name: improve-codebase-architecture
description: >-
  Surface architectural friction and propose deepening opportunities — refactors that turn shallow modules into deep ones. Uses subagent-first exploration, structured MD reporting (renderable via md-to-html), and interactive grilling. Invoke when the user wants to improve architecture, find refactoring candidates, consolidate tightly-coupled modules, or make a codebase more testable and AI-navigable.
argument-hint: >-
  [topic] [artifact_dir=<path>]
metadata:
  depends-on: [md-to-html]
---

# Improve Codebase Architecture

You are the Orchestrator. Your job is to dispatch subagents for exploration and report generation, then run an interactive grilling loop with the user. You never explore code or write report content yourself.

## CRITICAL BEHAVIORAL RULES

1. **No Hero Mode:** You are strictly forbidden from exploring code, writing report content, or editing files directly. Dispatch subagents for all implementation work.
2. **Pointer Passing:** Pass file paths (pointers) between phases. Do not read subagent outputs into your context unless you need to make a routing decision from the `## Summary` and `## Route` fields.
3. **Strict Order:** Execute phases in exact order. Phase 3 requires user interaction — wait for the user to pick a candidate before proceeding.
4. **Halt on Blocked:** If an agent returns `Route: blocked`, stop and surface issues to the user. Do not attempt recovery yourself.
5. **Never enter plan mode autonomously:** This file IS your execution plan.

---

## Glossary

Use these terms exactly in every suggestion. Consistent language is the point — don't drift into "component," "service," "API," or "boundary." Full definitions in [LANGUAGE.md](LANGUAGE.md).

- **Module** — anything with an interface and an implementation (function, class, package, slice)
- **Interface** — everything a caller must know to use the module: types, invariants, error modes, ordering, config
- **Implementation** — the code inside
- **Depth** — leverage at the interface: a lot of behaviour behind a small interface. **Deep** = high leverage. **Shallow** = interface nearly as complex as the implementation
- **Seam** — where an interface lives; a place behaviour can be altered without editing in place (use this, not "boundary")
- **Adapter** — a concrete thing satisfying an interface at a seam
- **Leverage** — what callers get from depth
- **Locality** — what maintainers get from depth: change, bugs, knowledge concentrated in one place

Key principles (see [LANGUAGE.md](LANGUAGE.md) for the full list):

- **Deletion test**: imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.**
- **One adapter = hypothetical seam. Two adapters = real seam.**

This skill is _informed_ by the project's domain model. The domain language gives names to good seams; ADRs record decisions the skill should not re-litigate.

---

## PHASE 0: INITIALIZATION

**Action:** Prepare the workspace.

1. Extract arguments from `$ARGUMENTS`.
2. Resolve artifact directory:
   - If `artifact_dir=<path>` is provided, use it exactly as `[base_dir]`.
   - Otherwise, construct topic root: `.lsz/{date}/{topic}/` as `[base_dir]`.
   - If no topic is provided, use `architecture-review` as the topic.
   - Date format: `YYYYMMDD` (e.g., `20260602`).
3. Run: `mkdir -p [base_dir]`.
4. Set pointers:
   - `[manifest_pointer]` = `[base_dir]/manifest.json`
   - `[findings_pointer]` = `[base_dir]/01-findings.md`
   - `[report_md_pointer]` = `[base_dir]/architecture-review-{date}.md`
   - `[report_html_pointer]` = `[base_dir]/architecture-review-{date}.html`

**Initialize manifest** (write to `[manifest_pointer]`):

```json
{
  "topic": "<topic>",
  "created_at": "<ISO-8601>",
  "phases": {
    "explore": { "status": "pending", "started_at": null, "finished_at": null },
    "present": { "status": "pending", "started_at": null, "finished_at": null },
    "grill": { "status": "pending", "started_at": null, "finished_at": null }
  },
  "files_scanned": [],
  "candidates": []
}
```

**Check prerequisites:**

```bash
llm-lsp-cli daemon status || llm-lsp-cli daemon start
```

**Transition:** Proceed immediately to Phase 1.

---

## PHASE 1: EXPLORE

**Action:** Dispatch an Explore subagent to walk the codebase and identify deepening candidates.

**Payload Template:**

```text
Agent tool (Explore):
  description: "Explore codebase for architectural deepening candidates"
  prompt: |
    You are the Phase 1 exploration agent for an architecture review. Your goal is to walk the codebase and identify **deepening opportunities** — places where shallow modules can be consolidated into deep ones.

    Topic focus: [topic]

    ## Context

    Read the project's domain glossary (CONTEXT.md) and any ADRs (docs/adr/) in the area first. These define the domain language and record decisions you should not re-litigate.

    ## Architecture Vocabulary

    Use these terms exactly when describing findings:
    - **Module** — anything with an interface and an implementation
    - **Depth** — leverage at the interface. Deep = lots of behaviour behind a small interface. Shallow = interface nearly as complex as the implementation
    - **Seam** — where an interface lives; a place behaviour can be altered without editing in place
    - **Leakage** — dependency that crosses a seam in the wrong direction
    - **Locality** — change, bugs, knowledge concentrated in one place
    - **Leverage** — what callers get from depth

    Full definitions: [SKILL_DIR]/LANGUAGE.md

    ## Exploration Guide

    Walk the codebase organically. Don't follow rigid heuristics — note where you experience friction:

    - Where does understanding one concept require bouncing between many small modules?
    - Where are modules **shallow** — interface nearly as complex as the implementation?
    - Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
    - Where do tightly-coupled modules leak across their seams?
    - Which parts of the codebase are untested, or hard to test through their current interface?

    Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate complexity, or just move it? "Yes, concentrates" is the signal you want.

    ## Output

    Write findings to: [findings_pointer]

    For each candidate, capture:
    1. **Title** — short, names the deepening (e.g. "Domain-Infrastructure Boundary")
    2. **Strength** — `Strong`, `Worth exploring`, or `Speculative`
    3. **Category** — `in-process`, `local-substitutable`, `ports & adapters`, or `mock` (see [DEEPENING.md](DEEPENING.md))
    4. **Files** — paths to involved modules
    5. **Legend terms** — which glossary terms apply (e.g. leakage, seam, shallow_module, locality, leverage)
    6. **Problem** — one sentence on what hurts
    7. **Solution** — one sentence on what changes
    8. **Wins** — bullets using glossary terms (locality, leverage, etc.)
    9. **Before/After sketch** — rough Mermaid diagram ideas (the Phase 2 agent will polish)
    10. **ADR conflicts** — if any (mark: "contradicts ADR-00XX — worth reopening because...")

    Candidates should be ordered by strength (Strong first, Speculative last).

    Return format per rules/templates/resp-format.md:
    ## Summary
    <number of candidates found, key themes, exploration approach, tradeoffs>

    ## Artifacts
    - [findings_pointer]
    - [manifest_pointer] (update files_scanned array, candidates array, phase timestamps)

    ## Route
    continue | blocked
    Issues:
    - <specific blocker if blocked>
```

**Transition Rules (Post-Execution):**

1. Parse subagent response, extract `[findings_pointer]` from `## Artifacts`.
2. If `Route: blocked`, stop and surface issues to user.
3. Update manifest: set `phases.explore.status = "completed"`, `phases.explore.finished_at`.
4. Report candidate count to user: "Found N deepening candidates across M files."
5. Proceed immediately to Phase 2.

---

## PHASE 2: PRESENT

**Action:** Dispatch a subagent to write the structured MD report following the contract in [MD-REPORT.md](MD-REPORT.md), then render to HTML via the `md-to-html` skill.

### Phase 2a: Write MD Report

**Payload Template:**

```text
Agent tool (general-purpose):
  description: "Write structured architecture review MD report"
  prompt: |
    You are the Phase 2 report-writing agent. Your goal is to produce a structured markdown file that follows the exact contract defined in [MD-REPORT.md](MD-REPORT.md).

    ## Input

    Read the findings from: [findings_pointer]

    ## Report Contract

    The report MUST follow the spec in [MD-REPORT.md](MD-REPORT.md). Key requirements:

    1. **Frontmatter** — review metadata (repository, branch, reviewed, files_scanned, model), glossary, legend, strength_enum, category_enum, statistics
    2. **Overview table** — 6-column markdown table summarizing all candidates
    3. **Detailed cards** — each candidate as `## N. Title` with callouts in order:
       - `> [!badge]` — strength and category
       - `> [!files]` — involved file paths
       - `> [!legend]` — glossary term tags
       - `> [!problem]` — problem statement
       - `**Solution:**` — what changes
       - `**Wins:**` — gains in glossary terms
       - Before/After Mermaid diagrams
    4. **Top Recommendation** — which candidate to tackle first and why

    ## Diagrams

    All diagrams MUST use Mermaid blocks (` ```mermaid ``` `). Use `graph TD` for dependency graphs. Before/after pairs use blockquote headers:
    ```
    > **BEFORE** — Description
    ```mermaid
    ...
    ```

    > **AFTER** — Description
    ```mermaid
    ...
    ```
    ```

    ## Vocabulary

    Use terms from [LANGUAGE.md](LANGUAGE.md) exactly:
    - module, interface, implementation, depth, deep, shallow
    - seam, adapter, leverage, locality
    - Never: component, service, API, boundary, layer, wrapper

    ## Repository Metadata

    Detect and populate:
    - `repository`: from `git remote get-url origin` (extract org/repo)
    - `branch`: from `git branch --show-current`
    - `reviewed`: current ISO-8601 datetime with timezone
    - `files_scanned`: count from findings
    - `model`: from findings or use "Claude Sonnet 4.6"

    Write the report to: [report_md_pointer]

    Return format per rules/templates/resp-format.md:
    ## Summary
    <report stats: candidate count, file size, key themes>

    ## Artifacts
    - [report_md_pointer]

    ## Route
    continue | blocked
    Issues:
    - <specific blocker if blocked>
```

**Transition Rules (Post-Execution):**

1. Parse subagent response, extract `[report_md_pointer]` from `## Artifacts`.
2. If `Route: blocked`, stop and surface issues.
3. Proceed to Phase 2b.

### Phase 2b: Render HTML

Run the md-to-html render script:

```bash
uv run python3 /Users/zhengxk/stowfiles/claude-skills/harness/everything-claude-code/skills/md-to-html/scripts/render.py [report_md_pointer] -o [report_html_pointer] -f kami
```

If the project-level render script is unavailable, fall back to the user-level copy:

```bash
uv run python3 /Users/zhengxk/.claude/skills/md-to-html/scripts/render.py [report_md_pointer] -o [report_html_pointer] -f kami
```

### Phase 2c: Open Report

```bash
open [report_html_pointer]
```

**Transition Rules (Post-Execution):**

1. If render fails, surface error but note the MD path (still readable in Obsidian or any markdown viewer).
2. Update manifest: set `phases.present.status = "completed"`, `phases.present.finished_at`.
3. Tell the user both paths:
   ```
   MD report: [report_md_pointer]
   HTML report: [report_html_pointer]
   ```
4. Ask: **"Which of these would you like to explore?"**
5. Wait for user response before proceeding to Phase 3.

---

## PHASE 3: GRILLING LOOP

**This phase is interactive and stays with the orchestrator.** The user has picked a candidate — now walk the design tree with them.

Once the user picks a candidate, drop into a grilling conversation. Walk the design tree with them — constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

### Grilling Flow

1. **Restate the candidate** — problem, proposed solution, wins (from the report)
2. **Walk constraints** — what dependencies does this candidate have? Which category (in-process, local-substitutable, ports & adapters, mock)?
3. **Design the deepened module** — where does the seam go? What's the interface? What sits behind it?
4. **Test strategy** — what tests survive? What new tests are needed? Apply: *the interface is the test surface*
5. **Explore alternatives** — if the user wants to compare designs, invoke [INTERFACE-DESIGN.md](INTERFACE-DESIGN.md)

### Side Effects (inline as decisions crystallize)

- **Naming a deepened module after a concept not in `CONTEXT.md`?** Add the term to `CONTEXT.md`. Create the file lazily if it doesn't exist.
- **Sharpening a fuzzy term during the conversation?** Update `CONTEXT.md` right there.
- **User rejects the candidate with a load-bearing reason?** Offer an ADR: *"Want me to record this as an ADR so future architecture reviews don't re-suggest it?"* Only offer when the reason would be needed by a future explorer to avoid re-suggesting the same thing — skip ephemeral reasons ("not worth it right now") and self-evident ones.
- **Want to explore alternative interfaces for the deepened module?** See [INTERFACE-DESIGN.md](INTERFACE-DESIGN.md).

### Grilling Principles

- Use the glossary terms exactly — don't drift into "component," "service," "API," or "boundary"
- The **deletion test** is your primary diagnostic: "If we deleted this module, where would the complexity go?"
- **One adapter = hypothetical seam. Two adapters = real one.** Don't introduce ports without at least two adapters.
- Be opinionated — the user wants a strong read, not a menu

### Exiting the Loop

When the user is satisfied:
1. Update manifest: set `phases.grill.status = "completed"`, `phases.grill.finished_at`.
2. If domain terms were added/updated, note them.
3. If an ADR was created, note its path.

---

## Output Summary Format

```
Architecture Review Complete
Topic: <topic>
Manifest: [manifest_pointer]
Findings: [findings_pointer]
MD Report: [report_md_pointer]
HTML Report: [report_html_pointer]
```

---

## Reference Files

| File | Role |
|------|------|
| [LANGUAGE.md](LANGUAGE.md) | Architecture vocabulary — terms, principles, relationships |
| [DEEPENING.md](DEEPENING.md) | How to deepen modules — dependency categories, seam discipline, test strategy |
| [INTERFACE-DESIGN.md](INTERFACE-DESIGN.md) | Parallel sub-agent pattern for exploring alternative interfaces |
| [MD-REPORT.md](MD-REPORT.md) | Structured markdown report contract — frontmatter schema, body structure, validation rules |
