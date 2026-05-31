---
name: eval-gate
description: >-
  Eval-driven development gate for pass/fail decisions on implementation quality. Use for eval define, check, report, list, and clean; for creating acceptance criteria from specs, plans, ADRs, or requirements; for running capability, contract, negative, and regression evals; for pass@k metrics, model graders, and compact subagent-run reports. TRIGGER when validating implementation against approved requirements, running acceptance gates, defining verification scripts, or checking deterministic criteria. Also use for quick quality gates: build verification, type checking, lint, test coverage, security scans, and diff review before PRs. Always use this when validating implementation against approved requirements, running acceptance gates, or running pre-PR quality checks.
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
    - `define`: Read source docs, extract observable criteria, write definition with scripts for each criterion. Then verify scripts run and capture baseline by running each script. Write `baseline.json` to eval dir. Return baseline summary table.
    - `check`: Run each criterion's script, parse JSON output, append results to log, return status with routing.
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
    1. Write the eval definition and scripts
    2. Verify each script is executable and produces valid JSON output
    3. Run each script to capture baseline state
    4. Write `baseline.json` to the eval dir with structure:
       ```json
       {"captured": "<ISO timestamp>", "criteria": {"<id>": {"status": "pass|fail", "summary": "..."}}}
       ```
    5. Return a compact baseline summary table — do NOT paste full script output into your return

    **CRITICAL for `check` mode:**
    1. Run the script defined for each criterion
    2. Parse the JSON output: `{"status": "pass|fail", "summary": "...", "issues": [...]}`
    3. NEVER rely on exit code — parse the output
    4. If ANY criterion has `status: "fail"`, the eval fails
    5. Enumerate all issues from `issues` array for remediation
    6. Do NOT interpret results with LLM — use script output directly
    7. If any eval fails, write enumerated issues to `[eval_dir]/issues.md` (one issue per line, no formatting)
    8. Include routing decision, brief issue summary, and issues path in output:
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

```markdown
### [ID]: [Title]

**Description:** What this criterion checks.

**Grader:** code | rule | model | human

**Script:** (for code/rule graders)
```bash
# Script that outputs JSON: {"status": "pass|fail", "summary": "...", "issues": [...]}
```

**Pass Condition:** Script output has `status: "pass"`

**Fail Condition:** Script output has `status: "fail"` with enumerated issues
```

**Critical:** Scripts MUST output JSON with `status`, `summary`, and `issues` fields. The orchestrator parses this output — never rely on exit code.

## Grader Types

| Grader | Use For | Example |
|--------|---------|---------|
| **Code** | Deterministic checks | Tests, CLI commands, scripts |
| **Rule** | Structural assertions | Regex, schema, snapshot |
| **Model** | Open-ended outputs | LLM-as-judge rubric |
| **Human** | Subjective or security-critical | Manual review flag |

**Model routing for graders:**
- Simple contract/rule → fast model
- Complex behavior judgment → balanced model
- Security/signoff → human (never fully automate)

## Metrics

| Metric | Definition | Use When |
|--------|------------|----------|
| `pass@1` | First-attempt success | Contract, negative evals |
| `pass@3` | Success within 3 attempts | Capability evals |
| `pass^3` | 3 consecutive passes | Release-critical regression |

## Check Output

```
EVAL CHECK: feature-name
Capability: X/Y passing (pass@3: N%)
Contract: X/Y passing
Negative: X/Y passing
Regression: X/Y passing (pass^3: N%)
Status: IN PROGRESS | READY | FAILED
Route: continue | remediate | blocked
Issues:
- [brief issue 1 summary, ≤10 words each]
- [brief issue 2 summary]
Issues File: [path to issues.md if remediate, omitted otherwise]
Definition: [path]
Log: [path]
```

**Routing Decision:**
- `Status: READY` + `Route: continue` → Proceed to next phase
- `Status: FAILED` + `Route: remediate` → Invoke `tdd-cycle --lightweight issues=[path]` with issues file
- `Status: IN PROGRESS` + `Route: blocked` → Stop, requires user decision

**Why both Issues and Issues File:**
- `Issues:` provides brief context for orchestrator awareness (≤10 words each)
- `Issues File:` contains full details for tdd-cycle remediation

## Report Output

```
EVAL REPORT: feature-name
Capability pass@1: N%
Capability pass@3: N%
Regression pass^3: N%
Gate Status: SHIP | NEEDS WORK | BLOCKED
Report: [path]
```

## Best Practices

1. **Define before coding** — Criteria anchor to approved requirements, not post-hoc justification
2. **Baseline inside define** — The define subagent verifies scripts and captures baseline; the orchestrator never runs eval scripts directly
3. **Prefer deterministic graders** — Model graders introduce variance
4. **Keep fast** — Evals should run repeatedly without cost anxiety
5. **Gate on thresholds** — Ship only when all thresholds met
6. **Mark human review** — Security signoff never fully automated

## Script-Based Verification & Remediation

**Core Principle:** All deterministic checks MUST use scripts that output structured, parseable results. The orchestrator parses script output to determine pass/fail — never rely on exit codes alone.

### Avoiding "Prose" Scripts

When `defining` evals, you MUST NOT write vague or non-executable descriptions of checks. Every "Code" or "Rule" grader MUST correspond to a concrete, executable script (Python or Bash) located in the eval artifact directory. 

- **Use Templates:** Strictly follow the templates in `$SKILL_DIR/references/script-templates.md`.
- **No Manual Grep:** Do not instruct the next agent to "run grep and see if it looks okay." The script MUST do the work and output JSON.
- **Enumerated Issues:** If a script fails, it MUST populate the `issues` array in the JSON output with specific, actionable failure locations (file:line:message).

### The Remediation Loop (EDD -> TDD)

The `check` mode is the trigger for the **Remediation Loop**. 

1. **Failure Detection**: `eval-gate check` detects a `status: "fail"` in a script's JSON output.
2. **Issue Aggregation**: The orchestrator or eval agent extracts all strings from the `issues` array and writes them to `[eval_dir]/issues.md` (one per line).
3. **Route: remediate**: The orchestrator receives the `remediate` route and the path to `issues.md`.
4. **TDD Resumption**: The orchestrator invokes `tdd-cycle --lightweight issues=[eval_dir]/issues.md topic_root=[topic_root]`.
5. **Deterministic Fix**: The `tdd-cycle` skill treats each line in `issues.md` as a **Work Unit** to be resolved.
6. **Re-Verification**: Once `tdd-cycle` completes, control returns to the orchestrator, which MUST re-run `eval-gate check` to verify the fix.

### Anti-Patterns

| Wrong | Right |
|-------|-------|
| Description: "Check if types are okay" | Script: `scripts/check-types.py` (executable) |
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
