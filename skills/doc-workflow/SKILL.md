---
name: doc-workflow
description: Consolidated workflow for generating project documentation and architectural codemaps. Includes interactive prompts for user alignment.
allowed-tools: Read Grep Glob Bash
---

# Documentation Workflow Skill

You have invoked the Documentation Workflow Skill. This skill defines the process for syncing human-readable project documentation and generating token-lean architectural codemaps.

## PHASE 1: USER ALIGNMENT (INTERACTIVE)
If the user did not explicitly provide arguments specifying what to update, you MUST ask them what they want to do.

---
**Docs Target**

What documentation should be updated? (You may select multiple)

1. **Project Docs** — Sync CONTRIBUTING.md, RUNBOOK.md, and ENV variables from source files.
2. **Architecture Codemaps** — Perform a deep codebase scan and generate token-lean maps in docs/CODEMAPS/.
---

Wait for the user's response before proceeding.

## PHASE 2: EXECUTION

### If "Project Docs" is selected:
1. **Identify Sources:** Look for `package.json`, `Cargo.toml`, `.env.example`, `Makefile`.
2. **Sync Scripts:** Extract all scripts/commands and update the reference table in `docs/CONTRIBUTING.md`.
3. **Sync Environment:** Extract variables from `.env.example` and update the environment documentation.
4. **Staleness Check:** Identify documentation files not modified in 90+ days and flag them for review.

### If "Architecture Codemaps" is selected:
1. **Scan Project:** Identify entry points, routing layers, and database repos.
2. **Generate Maps:** Create/update files in `docs/CODEMAPS/` (e.g., `architecture.md`, `backend.md`, `frontend.md`).
3. **Constraint:** Codemaps MUST be token-lean. Use file paths and function signatures. Do not paste full code blocks.
4. **Metadata:** Add a freshness header to each codemap: `<!-- Generated: YYYY-MM-DD | Files scanned: X -->`.

## PHASE 3: REPORT
Print a summary to the console of exactly what files were updated, skipped, or flagged as stale.
