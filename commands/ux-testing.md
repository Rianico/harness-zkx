---
name: ux-testing
description: Single entry point for the UX testing cluster. Routes to the appropriate skill based on intent.
argument-hint: "[audit|build|check] [--once|--watch]"
allowed-tools: [Read, Edit, Write, Bash, Agent, Skill]
---

# UX Testing Command

Single entry point for verifying that the user-facing experience works as intended.

## Routing

| Argument | Skill | Purpose |
|----------|-------|---------|
| `audit` | click-path-audit | Static code analysis of handler state interactions |
| `build` | e2e-workflow | Build persistent E2E test suite with POM and locators |
| `check` | browser-qa | Ad-hoc runtime verification or sustained post-deploy monitoring |

## Instructions

### `/ux-testing audit`

Invoke the `click-path-audit` skill. Use for finding state cancellation bugs that runtime tests won't catch deterministically (sequential undo, stale closures, event handler conflicts).

### `/ux-testing build`

Invoke the `e2e-workflow` skill. Use for building maintainable E2E test infrastructure with Page Object Model, locator strategies, and flakiness quarantine.

### `/ux-testing check [--once|--watch] [--interval 5m] [--duration 2h] [--compare <staging> <prod>]`

Invoke the `browser-qa` skill with the appropriate flags:

- `--once` (default): Single-pass ad-hoc QA check
- `--watch`: Sustained post-deploy monitoring with alert thresholds
- `--compare`: Diff mode comparing staging vs production

### No argument provided

If `$ARGUMENTS` is empty, ask the user which mode they need:

1. **audit** — "I need to find state bugs in event handlers"
2. **build** — "I need to set up E2E test infrastructure"
3. **check** — "I need to verify the UI works right now"
