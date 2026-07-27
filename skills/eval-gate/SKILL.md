---
name: eval-gate
description: >-
  Eval-driven gate for pass/fail quality decisions. Defines criteria
  from specs/plans/ADRs, runs capability/contract/negative/regression
  evals with pass@k and model graders. Covers pre-PR gates (build,
  type check, lint, coverage). TRIGGER: validate implementation,
  acceptance gate.
argument-hint: >-
  [define|check|quick|report|list|clean] [feature-name] [source-of-truth] [topic_root=<path>|artifact_dir=<path>]
tools:
  - Agent
  - Bash
---

# Eval Gate (EDD)

Run **EDD (Eval-Driven Development)** gates while keeping substantive work out of the main context. The primary agent acts as an **Executioner**, orchestrating the **Deterministic Gate** via scripts and environmental truth.

## Core Loop (GDD)

```
Define (Intent -> Spec)  →  Execute Implementation
                           ↓
Deterministic Gate  ←  Re-run evals  ←  Implementation complete
```

**Baseline capture** happens inside `define`: the subagent writes scripts, runs them, and writes `baseline.json`. This anchors expectations and prevents "it works because I wrote tests after." The orchestrator never needs to run eval scripts directly.

## Command Modes

| Mode | Purpose |
|------|---------|
| `define <feature> [source]` | Create acceptance criteria from source-of-truth, verify scripts, capture baseline |
| `check <feature>` | Run criteria against current implementation |
| `quick` | Run 6 standard quality phases without formal definition (Build, Types, Lint, Tests, Security, Diff) |
| `report <feature>` | Produce comprehensive report with metrics |
| `list` | Show all eval definitions and statuses |
| `clean` | Remove old logs, keep last 10 runs per feature |

**Source docs**: Pass any combination of design.md, ADR, plan, or other requirements. Eval criteria are derived from whatever sources are provided.

## Quick Mode

`eval-gate quick` runs 6 standard quality phases without requiring a formal eval definition. Use for fast pre-PR quality gates or periodic verification during long sessions.

### Six Phases

| Phase | Checks | Commands |
|-------|--------|----------|
| **Build** | Project compiles | `npm run build` / `pnpm build` |
| **Types** | No type errors | `tsc --noEmit` / `basedpyright .` |
| **Lint** | Style compliance | `npm run lint` / `ruff check .` |
| **Tests** | Suite passes + coverage | `npm run test -- --coverage` |
| **Security** | No secrets, no leaks | `rg "sk-" .` / `rg "api_key" .` |
| **Diff** | Review changed files | `git diff --stat` |

### Quick Mode Output

```
EVAL QUICK CHECK
================
Build:     PASS
Types:     PASS (0 errors)
Lint:      PASS (2 warnings)
Tests:     PASS (42/42, 87% coverage)
Security:  FAIL (1 hardcoded API key in src/config.ts:12)
Diff:      3 files changed

Overall:   NOT READY for PR
Route:     remediate
Issues:
- hardcoded API key in src/config.ts:12
```

**Routing Decision:**
- `Overall: READY` + `Route: continue` → Proceed to PR
- `Overall: NOT READY` + `Route: remediate` → Fix issues before PR

### Continuous Mode Guidance

For long development sessions, run `eval-gate quick` every 15 minutes or after major changes:
- After completing each function or component
- Before moving to the next task
- Before creating a PR

## Four Eval Types

| Type | Checks | Example |
|------|--------|---------|
| **Capability** | New behavior the feature enables | "User can filter by date range" |
| **Contract** | Externally visible shapes and interfaces | "API returns `{ status, data, error }`" |
| **Negative** | Forbidden behavior must not occur | "No PII in logs" |
| **Regression** | Existing behavior still works | "Old filter still works" |

### Capability Evals

Test new behavior. Observable through code execution, tests, CLI commands, APIs, or environmental side effects.

**CRITICAL: No Paper Tigers.** 
Capability evals MUST be **Executable Assertions**. You are strictly forbidden from writing "Source Grep" evals that only check for substrings in the source code (e.g., `if 'logic' in file.read()`). An eval must prove that the goal was *achieved in the environment*, not just *promised in the code text*.

**Threshold**: `pass@3 >= 0.90` (success within 3 attempts)

### Contract Evals

Test externally visible shapes: fields, flags, schemas, status codes, file formats.

**Threshold**: `pass@1 = 1.00` (must pass first try — contract is binary)

### Negative Evals

Test forbidden behavior: security leaks, weakened requirements, unsupported paths.

**Threshold**: `pass@1 = 1.00` (must not occur)

### Regression Evals

Test existing behavior remains intact. Prefer narrow deterministic checks over full suites.

**Threshold**: `pass^3 = 1.00` for release-critical paths (3 consecutive passes)

## Artifact Storage

```
[eval_dir]/
├── run-[N]/
│   ├── <feature>.md          # Definition
│   ├── <feature>.log         # Append-only check log
│   ├── <feature>-report.md   # Report artifact
│   └── baseline.json         # Pre-implementation baseline
```

**Directory selection:**
1. `artifact_dir=<path>` → use exactly (orchestrator should pass `eval/run-[N]`)
2. `topic_root=<path>` → use `[topic_root]/eval/run-1/`
3. Default → `.lsz/{date}/{timestamp}_{topic}/eval/run-1/`

## Dispatch Template

```text
Agent tool (general-purpose):
  description: "Run eval-gate workflow"
  prompt: |
    You are the eval execution agent.

    Mode: $MODE
    Feature: $FEATURE
    Source docs: $SOURCE_DOCS
    Eval directory: $EVAL_DIR

    Execute entirely inside this subagent. Do not launch subagents.

    Modes:
    - `define`: Read source docs, extract observable criteria. Write a single, consolidated evaluation script (e.g., `run_evals.py` or `run_evals.sh`) that executes all criteria checks in one pass and outputs a unified LLM-friendly JSON report. Verify the script runs and capture baseline state for all criteria.
    - `check`: Execute the consolidated evaluation script directly (execute once, get all checked items). Parse the unified JSON output, append results to log, return status with routing.
    - `quick`: Run 6 standard quality phases (Build, Types, Lint, Tests, Security, Diff) without formal definition. Return compact PASS/FAIL per phase.
    - `report`: Read definition and log, write report, return recommendation. If this is the final report for the phase, invoke the `handoff` skill with `artifacts=[report_path]` to distill the readiness status and any residual issues.
    - `list`: Summarize definitions and statuses.
    - `clean`: Remove old logs, keep last 10 runs.

    **CRITICAL for `quick` mode:**
    1. Run each phase in sequence: Build, Type Check, Lint, Test Suite, Security Scan, Diff Review
    2. For each phase, determine PASS/FAIL based on command output
    3. Report errors/warnings counts, test results, coverage, and security issues
    4. Output format:
       ```
       EVAL QUICK CHECK
       ================
       Build:     PASS | FAIL
       Types:     PASS | FAIL (X errors)
       Lint:      PASS | FAIL (X warnings)
       Tests:     PASS | FAIL (X/Y passed, Z% coverage)
       Security:  PASS | FAIL (X issues)
       Diff:      X files changed

       Overall:   READY | NOT READY for PR
       Route:     continue | remediate
       Issues:
       - [brief issue 1, ≤10 words each]
       - [brief issue 2]
       ```
    5. If any phase fails, `Overall: NOT READY` and `Route: remediate`
    6. List specific issues found for remediation

    **CRITICAL for `define` mode:**
    1. Write the evaluation definition and a single, consolidated execution script.
    2. Verify the consolidated script is executable and produces valid, unified JSON output.
    3. Run the consolidated script once to capture baseline state for all criteria.
    4. Write `baseline.json` to the eval dir with structure:
       ```json
       {"captured": "<ISO timestamp>", "criteria": {"<id>": {"status": "pass|fail", "summary": "..."}}}
       ```
    5. Return a compact baseline summary table — do NOT paste full script output into your return

    **CRITICAL for `check` mode:**
    1. Execute the consolidated evaluation script directly. Do NOT execute commands one by one.
    2. The script's output MUST be a clear, concise, LLM-friendly report (JSON) including failed tests, desired vs actual, and enumerated issues.
    3. Parse the unified JSON output: `{"status": "pass|fail", "summary": "...", "criteria": {"<id>": {"status": "pass|fail", "summary": "...", "issues": [...]}}, "issues": [...]}`
    4. NEVER rely on exit code — parse the output.
    5. If ANY criterion has `status: "fail"`, the eval fails.
    6. Enumerate all issues from the unified `issues` array for remediation.
    7. Do NOT interpret results with LLM — use script output directly.
    8. If any eval fails, write enumerated issues to `[eval_dir]/issues.md` (one issue per line, no formatting).
    9. Include routing decision, brief issue summary, and issues path in output:
       - `Route: continue` if all pass
       - `Route: remediate` if any fail (with brief summary + issues file path)
       - `Route: blocked` if cannot proceed (e.g., missing dependencies)

    **Required Output Format for `check` mode:**
    ```
    EVAL CHECK: feature-name
    Capability: X/Y passing (pass@3: N%)
    Contract: X/Y passing
    Negative: X/Y passing
    Regression: X/Y passing (pass^3: N%)
    Status: READY | FAILED
    Definition: [path]
    Log: [path]
    ```

    **Standard Return Format (Mandatory):**
    ```markdown
    ## Summary
    <technical summary of eval results and baseline comparisons>

    ## Artifacts
    - [eval_dir]/<feature>.md
    - [eval_dir]/<feature>.log
    - [eval_dir]/issues.md (if remediate)

    ## Route
    continue | remediate | blocked
    Issues:
    - [brief issue 1, ≤10 words]
    - [brief issue 2]
    ```
```

## Definition Template

```markdown
## EVAL: feature-name
Created: $(date)
Source of truth: [pointer(s)]
Eval directory: [eval_dir]

### Capability Evals
- [ ] [Observable behavior]

### Contract Evals
- [ ] [Interface/shape requirement]

### Negative Evals
- [ ] [Forbidden behavior]

### Regression Evals
- [ ] [Existing behavior preserved]

### Grader Assignment
- [ ] Capability: [code|model|human]
- [ ] Contract: [code|rule]
- [ ] Negative: [code|model|human]
- [ ] Regression: [code]

### Thresholds
- Capability: pass@3 >= 0.90
- Contract: pass@1 = 1.00
- Negative: pass@1 = 1.00
- Regression: pass^3 = 1.00
```

## Eval Criterion Template

For each criterion, define:

### [ID]: [Title]

**Description:** What this criterion checks.

**Grader:** code | rule | model | human

**Implementation:** All "code" or "rule" criteria MUST be implemented within the consolidated evaluation script (`run_evals.py` or similar). The script must perform the check for this ID and include it in the unified JSON report.

**Pass Condition:** Unified JSON report shows `status: "pass"` for this ID.

**Fail Condition:** Unified JSON report shows `status: "fail"` for this ID with enumerated issues.

**Critical:** The consolidated evaluation script MUST output a unified JSON report with a top-level `status` and `issues` array, and a `criteria` object mapping criterion IDs to their individual `status`, `summary`, and `issues`.

---

## Script-Based Verification & Remediation

**Core Principle:** All deterministic checks MUST use a single, consolidated evaluation script that outputs structured, parseable, and LLM-friendly results. The orchestrator executes this script once per check cycle — never execute commands or criterion-specific scripts one by one.

### Consolidated Reporting

When `defining` evals, you MUST create a single executable script (Python or Bash) in the eval artifact directory that serves as the "source of truth" for the implementation's quality.

- **Unified Output:** The script MUST output a single JSON blob containing all results.
- **LLM-Friendly:** The output should include clear failure details (desired vs actual), failed tests, and specific line-level issues.
- **Execute Once:** The agent should be able to run `python3 run_evals.py` (or similar) and receive the full state of the project.
- **Enumerated Issues:** If any check fails, the script MUST populate a global `issues` array with specific, actionable failure locations (file:line:message).

### The Remediation Loop (EDD -> TDD)

The `check` mode is the trigger for the **Remediation Loop**. 

1. **Failure Detection**: `eval-gate check` executes the consolidated script and detects a top-level `status: "fail"`.
2. **Issue Aggregation**: The orchestrator extracts all strings from the global `issues` array in the JSON output and writes them to `[eval_dir]/issues.md` (one per line).
3. **Route: remediate**: The orchestrator receives the `remediate` route and the path to `issues.md`.
4. **TDD Resumption**: The orchestrator invokes `tdd-cycle --lightweight issues=[eval_dir]/issues.md topic_root=[topic_root]`.
5. **Deterministic Fix**: The `tdd-cycle` skill treats each line in `issues.md` as a **Work Unit** to be resolved.
6. **Re-Verification**: Once `tdd-cycle` completes, control returns to the orchestrator, which MUST re-run `eval-gate check` to verify the fix.

### Anti-Patterns

| Wrong | Right |
|-------|-------|
| Running `check-types.py`, then `check-tests.py` | Running `run_evals.py` which calls both and aggregates |
| Description: "Check if types are okay" | Script: `scripts/run_evals.py` (executable) |
| Output: "It failed with some errors" | Output: `{"status": "fail", "issues": ["src/main.py:12: Type error..."]}` |
| Remediation: "Look at the logs and fix it" | Remediation: `tdd-cycle --lightweight issues=eval/issues.md` |
| Relying on exit code 0 | Parsing `status: "pass"` from JSON output |

---

## Metric Reference

| Check Type | Grader | Why |
|------------|--------|-----|
| Type errors, test pass/fail | Code/Script | Deterministic, repeatable |
| Pattern matching (regex) | Rule | Exact match, no variance |
| Code style, behavior quality | Model | Requires semantic understanding |
| Security, architecture decisions | Human | Judgment required |

**Key principles:**
- Use scripts for deterministic checks (pass/fail is stable)
- Use LLM for semantic analysis where judgment is needed
- Never rely on LLM output for binary gate decisions — model responses are not stable
- Never rely on exit codes — scripts may have bugs; parse the output

**Reference:** [script-templates.md](references/script-templates.md) — Reusable script templates for type checking, pattern matching, test running, and LSP diagnostics.
