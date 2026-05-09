# Subagent Response Format

Default structured output format for all subagent and skill invocations.

## Format

```markdown
## Summary
<what was done, why those choices, what tradeoffs were made>

## Artifacts
- <path to primary output>

## Route (when applicable)
continue | remediate | blocked
Issues:
- <specific issue 1>
- <specific issue 2>
```

## How to Write It

**Summary is not a status report.** It's a delivery — approach, reasoning, tradeoffs — that the caller can review, critique, and act on without re-reading your artifacts.

Good: "Moved serialization to IPC layer per ADR-0024. Chose public accessor methods over property to hide cache implementation. Tradeoff: 3 more methods on LSPClient, but isolates daemon.py from cache internals."

Bad: "Refactored daemon.py. Tests pass."

**The difference:** Good delivers a position ("here's what I did and why"). Bad delivers a status update that forces the reviewer to read the code.

## Rules

- **Status + issues** — Always include pass/fail status and enumerate issues when failing
- **Route recommendation** — When the output determines next steps, include `Route:` with a recommendation; the caller decides what to do with it
- **No exit code reliance** — Scripts output JSON; callers parse output, not exit codes
- **Skill owns output, caller owns routing** — Skills produce status and issues; callers translate "remediate" into the right action for their workflow
- **Never return full artifact contents** — Return paths, not content
- **Size** — ≤100 words for status-only, ≤150 words for decisions/constraints

## Customization

Skills and dispatch prompts may add domain-specific fields (e.g., `## Test Results`, `## Diagnostics`) or omit `## Route` when the subagent has no routing decision to make. `## Summary` and `## Artifacts` are always required.

## Route Semantics

| Route | Meaning | Caller Action |
|-------|---------|---------------|
| `continue` | All checks passed | Proceed to next phase |
| `remediate` | Issues found, fixable | Dispatch fix agent with issue list |
| `blocked` | Cannot proceed without user input | Stop and surface to user |
