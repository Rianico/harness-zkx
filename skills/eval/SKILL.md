---
name: eval
description: Eval-driven development workflow for Claude Code. Use this for eval define, eval check, eval report, eval list, and eval clean; for creating acceptance eval definitions from specs, plans, ADRs, issues, or requirements; for running capability, contract, negative, and regression evals; for pass/fail gates, pass@k metrics, model graders, and compact subagent-run eval reports. Always use this when the user asks about evals, EDD, acceptance criteria gates, or validating implementation against approved requirements.
argument-hint: "[define|check|report|list|clean] [feature-name] [source-of-truth] [topic_root=<path>]"
tools: Agent, AskUserQuestion, Bash
---

# Eval Skill

Run eval-driven development workflows while keeping substantive eval work out of the main context. The primary agent orchestrates; a subagent reads artifacts, writes eval files, runs checks, and returns compact status plus pointers.

## Command modes

- `define <feature-name> [source-of-truth] [topic_root=<path>]`: create or revise an eval definition before implementation.
- `check <feature-name> [topic_root=<path>]`: run the approved eval definition against the current implementation.
- `report <feature-name> [topic_root=<path>]`: produce a comprehensive eval report from definition and logs.
- `list [topic_root=<path>]`: summarize available eval definitions and status.
- `clean [topic_root=<path>]`: remove old eval run logs while keeping the last 10 runs per feature.

## Artifact root selection

Use one eval artifact directory for the whole workflow:

1. If orchestration provides `[topic_root]` or an argument like `topic_root=<path>`, use `[topic_root]/eval/`.
2. Otherwise capture a standalone topic root once as `.lsz/$(date +%Y%m%d)/$(date +%H%M%S)_eval/`, store it as `[topic_root]`, then use `[topic_root]/eval/`.
3. Create the selected eval directory with `Bash`: `mkdir -p [eval_dir]`.
4. Pass `[eval_dir]` to every eval subagent. Downstream eval phases for the same topic reuse the same directory instead of minting a new timestamp.

Recommended files:

```text
[eval_dir]/<feature>.md          # eval definition
[eval_dir]/<feature>.log         # append-only check log
[eval_dir]/<feature>-report.md   # report artifact
[eval_dir]/baseline.json         # optional regression baseline
```

## Primary-agent orchestration contract

1. **No Hero Mode:** Do not read implementation files, run eval checks, or write eval artifacts in the main context.
2. **Subagent Execution:** For each mode, dispatch exactly one eval execution subagent unless a `define` approval checkpoint requires a revision pass.
3. **Pointer Passing:** Pass artifact paths and approved upstream pointers to subagents. Do not paste large artifact contents into the main prompt.
4. **No Agent-ception:** The eval execution subagent must not launch further agents. It should use direct reads, edits, and commands only.
5. **Compact Handoff:** Require ≤150 words plus artifact paths. Keep criteria, grader notes, command output, retries, and report bodies in files.
6. **Failure Handling:** If the subagent reports a blocker or ambiguous requirements, surface the blocker and stop.

## Dispatch template

After selecting `[eval_dir]`, call the `Agent` tool:

```text
Agent tool (general-purpose):
  description: "Run eval workflow"
  prompt: |
    You are the eval execution agent for this repository.

    User invocation: eval $ARGUMENTS
    Eval artifact directory: [eval_dir]

    Execute the requested eval mode entirely inside this subagent context. Do not launch subagents.

    Mode behavior:
    - `define <feature-name> [source-of-truth]`: read only the source-of-truth and necessary supporting pointers. Extract concrete observable criteria without weakening requirements. Write `[eval_dir]/<feature-name>.md`. Do not implement code.
    - `check <feature-name>`: read `[eval_dir]/<feature-name>.md`, verify each criterion with the smallest necessary reads or commands, append results to `[eval_dir]/<feature-name>.log`, and return aggregate status.
    - `report <feature-name>`: read the definition and log, write `[eval_dir]/<feature-name>-report.md`, and return recommendation plus report path.
    - `list`: list eval definitions and statuses under `[eval_dir]` without dumping full artifacts.
    - `clean`: remove old eval log entries or rotated logs while keeping the last 10 runs per feature; return what changed.

    Handoff format: ≤150 words plus paths. Never paste full definitions, logs, reports, or command output into the final response unless no artifact exists.
```

## Define approval checkpoint

After `define` returns an eval definition pointer, stop and ask for approval with `AskUserQuestion`:

```json
{
  "questions": [{
    "question": "Eval definition is ready. Please review the file at [eval_definition_pointer].",
    "header": "Eval",
    "multiSelect": false,
    "options": [
      { "label": "Approve", "description": "Accept this eval definition as the gate for implementation." },
      { "label": "Revise", "description": "Provide changes or missing criteria for a new subagent revision pass." },
      { "label": "Reject", "description": "Stop without using this eval definition." }
    ]
  }]
}
```

If approved, return the eval definition pointer and `[eval_dir]`, then terminate. If revision is requested, ask for the requested changes, then launch a new subagent with the prior definition pointer, `[eval_dir]`, and the user's feedback. Do not resume the old subagent.

## Eval definition template

```markdown
## EVAL: feature-name
Created: $(date)
Source of truth: [absolute or repo-relative source pointer]
Eval directory: [eval_dir]
Supporting artifacts:
- [ADR pointer, if any]
- [Plan pointer, if any]

### Capability Evals
- [ ] [Concrete observable behavior from the source of truth]

### Format / Contract Evals
- [ ] [Required output shape, field, CLI flag, API contract, or schema behavior]

### Negative Evals
- [ ] [Forbidden behavior or output must not occur]

### Regression Evals
- [ ] [Existing behavior still works]

### Success Criteria
- Capability evals: all required criteria pass, with retries recorded when applicable
- Regression evals: all required regression criteria pass
- Contract evals: all externally visible formats or modes named in the source of truth are covered
```

## Eval types

### Capability evals

Check new behavior the work must make possible. Criteria should be observable through code, tests, CLI output, API response, UI behavior, or generated artifact content.

### Format / contract evals

Check externally visible shapes: fields, flags, schemas, modes, status codes, file names, markdown sections, or golden examples.

### Negative evals

Check forbidden behavior: unsupported alternatives, leaked sensitive data, weakened requirements, unexpected output, or regressions the source of truth explicitly rejects.

### Regression evals

Check existing behavior that must remain intact. Prefer deterministic tests or focused commands over broad, slow suites when a narrower command proves the criterion.

## Grader types

- **Code grader:** deterministic local command or script.
- **Rule grader:** regex, schema, snapshot, or structural assertion.
- **Model grader:** LLM-as-judge rubric for open-ended outputs; record the prompt and rationale in the log.
- **Human grader:** flag manual adjudication when behavior cannot be safely automated, especially for security-sensitive or subjective outcomes.

## Metrics

- `pass@1`: first-attempt success rate.
- `pass@3`: success within three controlled attempts; useful for capability reliability.
- `pass^3`: three consecutive successes; use for release-critical regression stability.

Recommended thresholds:

- Capability evals: `pass@3 >= 0.90`.
- Regression evals: `pass^3 = 1.00` for release-critical paths.

## Check output format

The subagent should write details to the log and return:

```text
EVAL CHECK: feature-name
Capability: X/Y passing
Contract: X/Y passing
Negative: X/Y passing
Regression: X/Y passing
Status: IN PROGRESS / READY / FAILED
Definition: [eval_dir]/feature-name.md
Log: [eval_dir]/feature-name.log
```

## Report output format

The subagent should write a report artifact and return:

```text
EVAL REPORT: feature-name
Capability pass@1: N%
Capability pass@3: N%
Regression pass^3: N%
Recommendation: SHIP / NEEDS WORK / BLOCKED
Report: [eval_dir]/feature-name-report.md
```

## Best practices

1. Define evals before coding so success criteria stay anchored to approved requirements.
2. Use source-of-truth artifacts for requirements; supporting ADRs or plans clarify constraints but do not override requirements unless the user approves the change.
3. Prefer deterministic graders when possible.
4. Keep evals fast enough to run repeatedly.
5. Version eval artifacts with the workflow output, not in ad hoc root files.
6. Do not fully automate security signoff; mark human review where appropriate.
