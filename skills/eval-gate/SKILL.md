---
name: eval-gate
description: Eval-driven development gate for pass/fail decisions on implementation quality. Use for eval define, check, report, list, and clean; for creating acceptance criteria from specs, plans, ADRs, or requirements; for running capability, contract, negative, and regression evals; for pass@k metrics, model graders, and compact subagent-run reports. TRIGGER when validating implementation against approved requirements, running acceptance gates, defining verification scripts, or checking deterministic criteria. Always use this when validating implementation against approved requirements or running acceptance gates.
argument-hint: "[define|check|report|list|clean] [feature-name] [source-of-truth] [topic_root=<path>|artifact_dir=<path>]"
tools:
  - Agent
  - Bash
---

# Eval Gate

Run eval-driven development gates while keeping substantive work out of the main context. The primary agent orchestrates; a subagent reads artifacts, runs checks, and returns compact status plus pointers.

## Core Loop

```
Define criteria  →  Capture baseline  →  Execute implementation
                                              ↓
Compare deltas  ←  Re-run evals  ←  Implementation complete
```

**Baseline capture**: Before implementation, run `check` to capture what fails. This anchors expectations and prevents "it works because I wrote tests after."

## Command Modes

| Mode | Purpose |
|------|---------|
| `define <feature> [source]` | Create acceptance criteria from source-of-truth |
| `check <feature>` | Run criteria against current implementation |
| `report <feature>` | Produce comprehensive report with metrics |
| `list` | Show all eval definitions and statuses |
| `clean` | Remove old logs, keep last 10 runs per feature |

**Source docs**: Pass any combination of design.md, ADR, plan, or other requirements. Eval criteria are derived from whatever sources are provided.

## Four Eval Types

| Type | Checks | Example |
|------|--------|---------|
| **Capability** | New behavior the feature enables | "User can filter by date range" |
| **Contract** | Externally visible shapes and interfaces | "API returns `{ status, data, error }`" |
| **Negative** | Forbidden behavior must not occur | "No PII in logs" |
| **Regression** | Existing behavior still works | "Old filter still works" |

### Capability Evals

Test new behavior. Observable through code, tests, CLI, API, UI, or artifacts.

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
├── <feature>.md          # Definition
├── <feature>.log         # Append-only check log
├── <feature>-report.md   # Report artifact
└── baseline.json         # Pre-implementation baseline
```

**Directory selection:**
1. `artifact_dir=<path>` → use exactly
2. `topic_root=<path>` → use `[topic_root]/eval/`
3. Default → `.lsz/{date}/{timestamp}_{topic}/eval/`

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
    - `define`: Read source docs, extract observable criteria, write definition with scripts for each criterion.
    - `check`: Run each criterion's script, parse JSON output, append results to log, return status with routing.
    - `report`: Read definition and log, write report, return recommendation.
    - `list`: Summarize definitions and statuses.
    - `clean`: Remove old logs, keep last 10 runs.

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
    Route: continue | remediate | blocked
    Issues:
    - [brief issue 1 summary, ≤10 words each]
    - [brief issue 2 summary]
    Issues File: [path to issues.md if remediate, omitted otherwise]
    Definition: [path]
    Log: [path]
    ```

    Return: Brief summary (≤100 words) of what was done, followed by artifact paths.
    Never paste full artifacts.
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
2. **Capture baseline** — Run check before implementation to know what fails
3. **Prefer deterministic graders** — Model graders introduce variance
4. **Keep fast** — Evals should run repeatedly without cost anxiety
5. **Gate on thresholds** — Ship only when all thresholds met
6. **Mark human review** — Security signoff never fully automated

## Script-Based Verification

**Core Principle:** All deterministic checks MUST use scripts that output structured, parseable results. The orchestrator parses script output to determine pass/fail — never rely on exit codes alone.

### Script Requirements

1. **Structured output** — JSON for complex data, single-line text for simple pass/fail
2. **Fail-fast on issues** — If any issues remain, output them clearly for remediation
3. **No exit code reliance** — Scripts may have bugs; parse output to detect actual state
4. **Issue enumeration** — When failing, list each issue so remediation can target them

### Script Output Formats

**JSON format (preferred for complex checks):**
```json
{
  "status": "pass|fail",
  "summary": "0 errors, 0 warnings",
  "issues": [],
  "details": {}
}
```

**Text format (for simple checks):**
```
PASS: <description>
```
or
```
FAIL: <description>
ISSUES:
- issue 1
- issue 2
```

### Anti-Patterns

| Wrong | Right |
|-------|-------|
| Exit code 0 = pass | Parse output JSON, check `status: "pass"` |
| `basedpyright && echo "pass"` | `basedpyright --outputjson \| jq '{status: if .errorCount > 0 then "fail" else "pass" end, issues: ...}'` |
| `grep -q pattern && exit 0` | `grep pattern \| jq -R -s '{status: if . == "" then "pass" else "fail" end, issues: split("\n")}'` |
| LLM interprets test output | Script parses own output, returns structured result |

### Example: Type Checking Script

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
import subprocess
import json
import sys

result = subprocess.run(
    ["basedpyright", "--outputjson"],
    capture_output=True,
    text=True
)

try:
    data = json.loads(result.stdout)
except json.JSONDecodeError:
    print(json.dumps({"status": "fail", "summary": "Failed to parse basedpyright output", "issues": [result.stderr]}))
    sys.exit(0)  # Exit 0 — we output status ourselves

errors = data.get("generalDiagnostics", [])
issues = [
    f"{e['file']}:{e['range']['start']['line']+1}: {e['message']}"
    for e in errors
]

output = {
    "status": "pass" if len(issues) == 0 else "fail",
    "summary": f"{len(issues)} issues found",
    "issues": issues
}
print(json.dumps(output))
# Always exit 0 — status is in output
```

### Example: Pattern Check Script (Bash)

```bash
#!/usr/bin/env bash
# Check for suppressions outside designated zones

DESIGNATED="lsp/transport.py|ipc/"
ISSUES=$(rg "# pyright:" src/ --type py | grep -Ev "$DESIGNATED" || true)

if [ -z "$ISSUES" ]; then
    echo '{"status": "pass", "summary": "No suppressions outside designated zones", "issues": []}'
else
    echo "{\"status\": \"fail\", \"summary\": \"Suppressions found outside designated zones\", \"issues\": $(echo "$ISSUES" | jq -R -s 'split("\n") | map(select(length > 0))')}"
fi
# Always exit 0 — status is in output
```

---

## Grader Selection: Determinism vs Semantics

| Check Type | Grader | Why |
|------------|--------|-----|
| Type errors, test pass/fail | Code/Script | Deterministic, repeatable |
| Pattern matching (regex, grep) | Rule | Exact match, no variance |
| Code style, behavior quality | Model | Requires semantic understanding |
| Security, architecture decisions | Human | Judgment required |

**Key principles:**
- Use scripts for deterministic checks (pass/fail is stable)
- Use LLM for semantic analysis where judgment is needed
- Never rely on LLM output for binary gate decisions — model responses are not stable
- Never rely on exit codes — scripts may have bugs; parse the output

**Reference:** [script-templates.md](references/script-templates.md) — Reusable script templates for type checking, pattern matching, test running, and LSP diagnostics.
