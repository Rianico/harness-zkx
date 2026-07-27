---
name: improve-codebase-architecture
description: >-
  Surface architectural friction and propose deepening opportunities -- refactors turning shallow modules into deep ones. Uses subagent exploration, structured MD reporting, and interactive grilling. TRIGGER: architecture improvement, refactoring candidates, tightly-coupled modules, testability.
argument-hint: |-
  [topic] [artifact_dir=<path>]
metadata:
  depends-on: [md-to-html]
---

# Improve Codebase Architecture

You are the Orchestrator. Your job is to dispatch a subagent for exploration and report generation, then run an interactive grilling loop with the user. You never explore code or write report content yourself.

## CRITICAL BEHAVIORAL RULES

1. **No Hero Mode:** You are strictly forbidden from exploring code, writing report content, or editing files directly. Dispatch subagents for all implementation work.
2. **Pointer Passing:** Pass file paths (pointers) between phases. Do not read subagent outputs into your context unless you need to make a routing decision from the `## Summary` and `## Route` fields.
3. **Strict Order:** Execute phases in exact order. Phase 2 requires user interaction — wait for the user to pick a candidate before proceeding.
4. **Halt on Blocked:** If an agent returns `Route: blocked`, stop and surface issues to the user. Do not attempt recovery yourself.
5. **Never enter plan mode autonomously:** This file IS your execution plan.

---

## Glossary

Use these terms exactly in every suggestion. Consistent language is the point — don't drift into "component," "service," "API," or "boundary." Full definitions in [LANGUAGE.md](references/LANGUAGE.md).

- **Module** — anything with an interface and an implementation (function, class, package, slice)
- **Interface** — everything a caller must know to use the module: types, invariants, error modes, ordering, config
- **Implementation** — the code inside
- **Depth** — leverage at the interface: a lot of behaviour behind a small interface. **Deep** = high leverage. **Shallow** = interface nearly as complex as the implementation
- **Seam** — where an interface lives; a place behaviour can be altered without editing in place (use this, not "boundary")
- **Adapter** — a concrete thing satisfying an interface at a seam
- **Leverage** — what callers get from depth
- **Locality** — what maintainers get from depth: change, bugs, knowledge concentrated in one place

Key principles (see [LANGUAGE.md](references/LANGUAGE.md) for the full list):

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
   - `[report_md_pointer]` = `[base_dir]/architecture-review-{date}.md`
   - `[report_html_pointer]` = `[base_dir]/architecture-review-{date}.html`

**Initialize manifest** (write to `[manifest_pointer]`):

```json
{
  "topic": "<topic>",
  "created_at": "<ISO-8601>",
  "phases": {
    "explore_and_present": { "status": "pending", "started_at": null, "finished_at": null },
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

## PHASE 1: EXPLORE & PRESENT

**Action:** Dispatch a single subagent to explore the codebase, identify deepening candidates, write the structured MD report, render it to HTML, and open it. One agent has full context — no handoff tax.

**Payload Template:**

```text
Agent tool (general-purpose):
  description: "Explore codebase and produce architecture review report"
  prompt: |
    You are the Phase 1 agent for an architecture review. Your job is end-to-end: explore the codebase, identify deepening candidates, produce the final report, and open it.

    Topic focus: [topic]

    ## Step 1: Explore

    Read the project's domain glossary (CONTEXT.md) and any ADRs (docs/adr/) in the area first. These define the domain language and record decisions you should not re-litigate.

    Walk the codebase organically. Don't follow rigid heuristics — note where you experience friction:

    - Where does understanding one concept require bouncing between many small modules?
    - Where are modules **shallow** — interface nearly as complex as the implementation?
    - Where have pure functions been extracted just for testability, but the real bugs hide in how they're called (no **locality**)?
    - Where do tightly-coupled modules leak across their seams?
    - Which parts of the codebase are untested, or hard to test through their current interface?

    Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate complexity, or just move it? "Yes, concentrates" is the signal you want.

    ## Architecture Vocabulary

    Use these terms exactly when describing findings. Full definitions: [SKILL_DIR]/references/LANGUAGE.md

    - **Module** — anything with an interface and an implementation
    - **Interface** — everything a caller must know to use the module
    - **Depth** — leverage at the interface. Deep = lots of behaviour behind a small interface
    - **Seam** — where an interface lives; a place behaviour can be altered without editing in place
    - **Adapter** — a concrete thing satisfying an interface at a seam
    - **Leakage** — dependency that crosses a seam in the wrong direction
    - **Leverage** — what callers get from depth
    - **Locality** — what maintainers get from depth

    For each candidate identified, capture:
    1. **Title** — short, names the deepening (e.g. "Domain-Infrastructure Boundary")
    2. **Strength** — `Strong`, `Worth exploring`, or `Speculative`
    3. **Category** — `in-process`, `local-substitutable`, `ports & adapters`, or `mock` (see [SKILL_DIR]/references/DEEPENING.md)
    4. **Files** — paths to involved modules
    5. **Legend terms** — which glossary terms apply (e.g. leakage, seam, shallow_module, locality, leverage)
    6. **Problem** — one sentence on what hurts
    7. **Solution** — one sentence on what changes
    8. **Benefits** — gains explained in terms of locality and leverage, and how tests would improve
    9. **Before/After sketch** — rough Mermaid diagram ideas to polish in the report
    10. **ADR conflicts** — if any (mark: "contradicts ADR-00XX — worth reopening because...")

    Order candidates by strength (Strong first, Speculative last).

    ## Step 2: Write the MD Report

    Write the structured markdown report to: [report_md_pointer]

    The report MUST follow the contract in [SKILL_DIR]/references/MD-REPORT.md. Key requirements:

    1. **Frontmatter** — review metadata (repository, branch, reviewed, files_scanned, model), glossary, legend, strength_enum, category_enum, statistics
    2. **Overview table** — 6-column markdown table (`#`, `Strength`, `Candidate`, `Files`, `Lines`, `Category`) summarizing all candidates
    3. **Detailed cards** — each candidate as `## N. Title` with callouts in strict order:
       - `> [!badge]` — strength and category (e.g. `**Strong** · ports & adapters`)
       - `> [!files]` — bullet list of involved file paths
       - `> [!legend]` — glossary term tags separated by `·`
       - `> [!problem]` — problem statement
       - `**Solution:**` — what changes (plain bold paragraph)
       - `**Wins:**` — gains in glossary terms (plain bold paragraph with bullet list)
       - Before/After Mermaid diagrams
    4. **Top Recommendation** — which candidate to tackle first and why
    5. **All diagrams MUST use Mermaid blocks** — ` ```mermaid ``` ` with `graph TD` for dependency graphs. Before/after pairs use blockquote headers.

    ## Repository Metadata

    Detect and populate:
    - `repository`: from `git remote get-url origin` (extract org/repo)
    - `branch`: from `git branch --show-current`
    - `reviewed`: current ISO-8601 datetime with timezone
    - `files_scanned`: count of files read during exploration
    - `model`: "Claude Sonnet 4.6"

    ## Step 3: Render HTML and Open

    Invoke the `md-to-html` skill to convert the MD report to HTML:

    ```
    Skill tool (md-to-html):
      args: "[report_md_pointer] -o [report_html_pointer] -f kami"
    ```

    The md-to-html skill knows its own script path — never hardcode it. After the skill renders the HTML, open it:

    ```bash
    open [report_html_pointer]
    ```

    Return format per rules/templates/resp-format.md:
    ## Summary
    <candidate count, files scanned, key themes, exploration approach, tradeoffs>

    ## Artifacts
    - [report_md_pointer]
    - [report_html_pointer]
    - [manifest_pointer] (populated: files_scanned, candidates, phase timestamps)

    ## Route
    continue | blocked
    Issues:
    - <specific blocker if blocked>
```

**Transition Rules (Post-Execution):**

1. Parse subagent response, extract pointers from `## Artifacts`.
2. If `Route: blocked`, stop and surface issues to user.
3. Update manifest: set `phases.explore_and_present.status = "completed"`, `phases.explore_and_present.finished_at`.
4. Report to user:
   ```
   Found N deepening candidates across M files.

   MD report: [report_md_pointer]
   HTML report: [report_html_pointer]
   ```
5. Ask: **"Which of these would you like to explore?"**
6. Wait for user response before proceeding to Phase 2.

---

## PHASE 2: GRILLING LOOP

**This phase is interactive and stays with the orchestrator.** The user has picked a candidate — now walk the design tree with them.

Once the user picks a candidate, drop into a grilling conversation. Walk the design tree with them — constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

### Grilling Flow

1. **Restate the candidate** — problem, proposed solution, benefits (from the report)
2. **Walk constraints** — what dependencies does this candidate have? Which category (in-process, local-substitutable, ports & adapters, mock)?
3. **Design the deepened module** — where does the seam go? What's the interface? What sits behind it?
4. **Test strategy** — what tests survive? What new tests are needed? Apply: *the interface is the test surface*
5. **Explore alternatives** — if the user wants to compare designs, invoke [INTERFACE-DESIGN.md](references/INTERFACE-DESIGN.md)

### Side Effects (inline as decisions crystallize)

- **Naming a deepened module after a concept not in `CONTEXT.md`?** Add the term to `CONTEXT.md`. Create the file lazily if it doesn't exist.
- **Sharpening a fuzzy term during the conversation?** Update `CONTEXT.md` right there.
- **User rejects the candidate with a load-bearing reason?** Offer an ADR: *"Want me to record this as an ADR so future architecture reviews don't re-suggest it?"* Only offer when the reason would be needed by a future explorer to avoid re-suggesting the same thing — skip ephemeral reasons ("not worth it right now") and self-evident ones.
- **Want to explore alternative interfaces for the deepened module?** See [INTERFACE-DESIGN.md](references/INTERFACE-DESIGN.md).

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
MD Report: [report_md_pointer]
HTML Report: [report_html_pointer]
```

---

## Reference Files

| File | Role |
|------|------|
| [LANGUAGE.md](references/LANGUAGE.md) | Architecture vocabulary — terms, principles, relationships |
| [DEEPENING.md](references/DEEPENING.md) | How to deepen modules — dependency categories, seam discipline, test strategy |
| [INTERFACE-DESIGN.md](references/INTERFACE-DESIGN.md) | Parallel sub-agent pattern for exploring alternative interfaces |
| [MD-REPORT.md](references/MD-REPORT.md) | Structured markdown report contract — frontmatter schema, body structure, validation rules |
