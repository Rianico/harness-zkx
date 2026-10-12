# Subagent Response Format

Canonical response contract for all subagents, skills, and dynamic workflow nodes.

Regardless of whether output is rendered as Markdown text or passed as JSON parameters to `structured_output`, it must convey the identical structured information.

---

## 1. Dual-Mode Representation

### Mode A: Markdown Prose Format
Used in interactive sessions, `/goal`, and CLI subagent dispatches:

```markdown
## Summary
<Carmack-style delivery: technical approach, architectural rationale, state tradeoffs, ≤100 words>

## Artifacts
- <absolute/path/to/file> (<spec | diff | report | eval | pr>)

## Evidence
- <check_name>: PASS | FAIL (`<command>`) [tail ≤20 lines on failure]

## Route
continue | remediate | blocked

## Issues
- [P1|P2|P3] <file>:<line> — <Invariant / Contract>: <Defect description>. Remediation: <Concrete fix>

## Suggestions (Optional)
- [Tooling|Environment|Spec|Workflow] <observation>. Workaround: <workaround>. Suggestion: <suggestion>
```

### Mode B: Structured JSON Schema Format
Used in dynamic workflows via `agent(prompt, { schema })` and the `structured_output` tool:

```json
{
  "summary": "Technical approach and tradeoffs (≤100 words)",
  "status": "COMPLETED | BLOCKED | REJECTED",
  "route": "continue | remediate | blocked",
  "artifacts": [
    { "path": "/absolute/path/to/file", "kind": "spec | diff | report | eval | pr" }
  ],
  "checks": [
    { "name": "pytest", "command": "uv run pytest", "ok": true, "exitCode": 0, "tail": "..." }
  ],
  "issues": [
    {
      "id": "ISSUE-1",
      "severity": "P1 | P2 | P3",
      "file": "src/core/router.py",
      "line": 42,
      "invariant": "Domain State Safety",
      "defect": "Race condition on concurrent refresh",
      "remediation": "Add async lock guard before refresh invocation"
    }
  ],
  "suggestions": [
    {
      "category": "Tooling | Environment | Spec | Workflow",
      "observation": "Direct oxfmt binary failed in subshell; needed package manager exec",
      "impact": "Unnecessary gate format failure",
      "workaround": "Invoked via pnpm exec oxfmt",
      "suggestion": "Prefix format commands with package manager exec in gate scripts"
    }
  ]
}
```

---

## 2. Isomorphic Field Mapping

| Prose Section | JSON Key | Type | Description |
|---|---|---|---|
| `## Summary` | `summary` | `string` | Approach, reasoning, and tradeoffs. Not a play-by-play status log. |
| (Implicit from Route) | `status` | `string` | `"COMPLETED"`, `"BLOCKED"`, or `"REJECTED"`. |
| `## Route` | `route` | `string` | `"continue"`, `"remediate"`, or `"blocked"`. |
| `## Artifacts` | `artifacts` | `array` | Absolute paths to touched/created files with `kind`. Never paste file bodies. |
| `## Evidence` | `checks` | `array` | Deterministic verification command results (`name`, `command`, `ok`, `tail`). |
| `## Issues` | `issues` | `array` | Actionable defects with severity, file:line, invariant, defect, remediation. Empty array / "None" if clean. |
| `## Suggestions` | `suggestions` | `array` | Optional non-blocking observations on environment/tooling friction (`category`, `observation`, `impact`, `workaround`, `suggestion`). |

---

## 3. Route & Severity Semantics

### Route Decision Matrix
| Route | Condition | Caller / Workflow Action |
|---|---|---|
| `continue` | 0 P1/P2 issues AND all deterministic checks green | Proceed to next stage or merge |
| `remediate` | P1 or P2 issues exist, attempts remain | Route back to developer with issue list |
| `blocked` | Contradictory spec, impossible invariant, or fatal conflict | Abort loop; escalate to human |

### Issue Severity Taxonomy
- **`P1` (Correctness / Contract / Security):** Broken invariants, fake tests/mock tautologies, security vulnerabilities, regression bugs.
- **`P2` (Architecture / State Safety):** Boundary leaks, mutable state escapes, domain drift, unhandled failure modes.
- **`P3` (Hygiene / Non-blocking):** Dead code, missing edge-case negative test, documentation drift.

---

## 4. Invariants

- **Formatting is never an issue:** Linters and formatters own whitespace and style deterministically. Never flag formatting as a semantic issue.
- **Paths, not contents:** Never paste file bodies into summary or issues. Downstream nodes read files via absolute paths.
- **Zero nitpicks:** An issue without `<file>:<line>`, violated invariant, defect, and concrete remediation is invalid.
- **Non-interfering suggestions:** `suggestions` are strictly non-blocking. They never fail a gate (`route: continue` remains valid) and do not delay primary delivery. Budget-capped at ≤ 2 items per turn.

