# Eval Command

Manage eval-driven development workflow.

## Usage

`/eval [define|check|report|list] [feature-name]`

## Define Evals

`/eval define feature-name [source-of-truth]`

Create a new eval definition. This command accepts any approved source-of-truth artifact: design document, product spec, issue, ADR, execution plan, bug report, or explicit user-provided requirements. When invoked from an orchestrated workflow, the orchestrator should pass the artifact that owns the requirements for that workflow, such as `design.md` after brainstorming.

1. Read the source-of-truth pointer passed by the user or orchestration. Use supporting artifacts, such as ADRs or plans, only to clarify implementation constraints; they must not override the source-of-truth requirements unless the user explicitly approves the change.
2. Extract eval criteria without weakening or omitting requirements:
   - Capability requirements
   - Regression requirements
   - Negative requirements, including things the output must not contain
   - Golden examples or concrete expected outputs
   - Edge cases and externally visible error behavior
   - Non-functional requirements that can be checked locally
3. Create `.claude/evals/feature-name.md` with template:

```markdown
## EVAL: feature-name
Created: $(date)
Source of truth: [absolute or repo-relative source pointer]
Supporting artifacts:
- [ADR pointer, if any]
- [Plan pointer, if any]

### Capability Evals
- [ ] [Concrete observable behavior from the source of truth]
- [ ] [Concrete observable behavior from the source of truth]

### Format / Contract Evals
- [ ] [Required output shape, field, CLI flag, API contract, or schema behavior]
- [ ] [Required golden example match or invariant]

### Negative Evals
- [ ] [Forbidden behavior or output must not occur]
- [ ] [Rejected alternative remains absent]

### Regression Evals
- [ ] [Existing behavior 1 still works]
- [ ] [Existing behavior 2 still works]

### Success Criteria
- Capability evals: all required criteria pass, with retries recorded when applicable
- Regression evals: all required regression criteria pass
- Contract evals: all externally visible formats or modes named in the source of truth are covered
```

4. Present the eval definition to the user for review.
5. Do not proceed to TDD or implementation until the user explicitly approves the eval definition.
6. If the user points out a missing criterion, update the eval definition and ask for approval again.

## Check Evals

`/eval check feature-name`

Run evals for a feature:

1. Read eval definition from `.claude/evals/feature-name.md`
2. For each capability eval:
   - Attempt to verify criterion
   - Record PASS/FAIL
   - Log attempt in `.claude/evals/feature-name.log`
3. For each format, contract, or negative eval:
   - Verify the observable output or behavior directly
   - Record missing fields, forbidden fields, mismatched examples, or contract drift as FAIL
4. For each regression eval:
   - Run relevant tests
   - Compare against baseline
   - Record PASS/FAIL
5. Report current status:

```
EVAL CHECK: feature-name
========================
Capability: X/Y passing
Contract: X/Y passing
Negative: X/Y passing
Regression: X/Y passing
Status: IN PROGRESS / READY / FAILED
```

## Report Evals

`/eval report feature-name`

Generate comprehensive eval report:

```
EVAL REPORT: feature-name
=========================
Generated: $(date)

CAPABILITY EVALS
----------------
[eval-1]: PASS (pass@1)
[eval-2]: PASS (pass@2) - required retry
[eval-3]: FAIL - see notes

REGRESSION EVALS
----------------
[test-1]: PASS
[test-2]: PASS
[test-3]: PASS

METRICS
-------
Capability pass@1: 67%
Capability pass@3: 100%
Regression pass^3: 100%

NOTES
-----
[Any issues, edge cases, or observations]

RECOMMENDATION
--------------
[SHIP / NEEDS WORK / BLOCKED]
```

## List Evals

`/eval list`

Show all eval definitions:

```
EVAL DEFINITIONS
================
feature-auth      [3/5 passing] IN PROGRESS
feature-search    [5/5 passing] READY
feature-export    [0/4 passing] NOT STARTED
```

## Arguments

$ARGUMENTS:
- `define <name>` - Create new eval definition
- `check <name>` - Run and check evals
- `report <name>` - Generate full report
- `list` - Show all evals
- `clean` - Remove old eval logs (keeps last 10 runs)
