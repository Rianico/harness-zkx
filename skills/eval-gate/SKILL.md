---
name: eval-gate
description: Eval-driven development gate for pass/fail decisions on implementation quality. Use for eval define, check, report, list, and clean; for creating acceptance criteria from specs, plans, ADRs, or requirements; for running capability, contract, negative, and regression evals; for pass@k metrics, model graders, and compact subagent-run reports. Always use this when validating implementation against approved requirements or running acceptance gates.
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

## Orchestration Contract

1. **No Hero Mode**: Do not read implementation, run checks, or write artifacts in main context
2. **Subagent Execution**: Dispatch one eval subagent per mode
3. **Pointer Passing**: Pass artifact paths, not contents
4. **No Agent-ception**: Subagent must not launch further agents
5. **Compact Handoff**: ≤150 words plus paths

## Dispatch Template

```text
Agent tool (general-purpose):
  description: "Run eval-gate workflow"
  prompt: |
    You are the eval execution agent.

    Invocation: eval-gate $ARGUMENTS
    Eval directory: [eval_dir]

    Execute entirely inside this subagent. Do not launch subagents.

    Modes:
    - `define <feature> [source]`: Read source-of-truth, extract observable criteria, write definition. Do not implement.
    - `check <feature>`: Verify each criterion, append results to log, return status.
    - `report <feature>`: Read definition and log, write report, return recommendation.
    - `list`: Summarize definitions and statuses.
    - `clean`: Remove old logs, keep last 10 runs.

    Handoff: ≤150 words plus paths. Never paste full artifacts.
```

## Definition Template

```markdown
## EVAL: feature-name
Created: $(date)
Source of truth: [pointer]
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
Definition: [path]
Log: [path]
```

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
