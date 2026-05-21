---
name: ux-testing
description: >-
  |
  UX testing cluster for verifying user-facing experience. Routes to click-path-audit for state cancellation bugs (sequential undo, stale closures, handler conflicts), e2e-workflow for E2E test infrastructure (POM, locators, flakiness quarantine), or browser-qa for ad-hoc QA and post-deploy monitoring.
  TRIGGER on UI bugs, broken buttons, E2E testing, browser testing, state interaction bugs, test infrastructure, or post-deploy verification.
arguments: mode options
argument-hint: |
  audit -- find state cancellation bugs (sequential undo, stale closures)
  build -- set up E2E test infrastructure (POM, locators, flakiness quarantine)
  check [--once|--watch] -- ad-hoc QA or sustained monitoring
  [--compare <staging> <prod>] -- diff mode comparing environments
metadata:
  manage: [click-path-audit, e2e-workflow, browser-qa]
---

# UX Testing

Single entry point for verifying that the user-facing experience works as intended.

## Sub-Skill Registry

```yaml
subskills:
  click-path-audit: $SKILL_DIR/subskills/click-path-audit/SKILL.md
  e2e-workflow: $SKILL_DIR/subskills/e2e-workflow/SKILL.md
  browser-qa: $SKILL_DIR/subskills/browser-qa/SKILL.md
```

## Dispatch

Parse `$ARGUMENTS` to determine mode:

| First Arg | Action |
|-----------|--------|
| `audit` | Read `$SKILL_DIR/subskills/click-path-audit/SKILL.md` and follow its instructions |
| `build` | Read `$SKILL_DIR/subskills/e2e-workflow/SKILL.md` and follow its instructions |
| `check` | Read `$SKILL_DIR/subskills/browser-qa/SKILL.md` and follow its instructions |

### `/ux-testing audit`

Read `$SKILL_DIR/subskills/click-path-audit/SKILL.md` and follow its instructions. Use for finding state cancellation bugs that runtime tests won't catch deterministically (sequential undo, stale closures, event handler conflicts).

### `/ux-testing build`

Read `$SKILL_DIR/subskills/e2e-workflow/SKILL.md` and follow its instructions. Use for building maintainable E2E test infrastructure with Page Object Model, locator strategies, and flakiness quarantine.

### `/ux-testing check [--once|--watch] [--interval 5m] [--duration 2h] [--compare <staging> <prod>]`

Read `$SKILL_DIR/subskills/browser-qa/SKILL.md` and follow its instructions with the appropriate flags:

- `--once` (default): Single-pass ad-hoc QA check
- `--watch`: Sustained post-deploy monitoring with alert thresholds
- `--compare`: Diff mode comparing staging vs production

### No argument provided

If `$ARGUMENTS` is empty, ask the user which mode they need:

1. **audit** — "I need to find state bugs in event handlers"
2. **build** — "I need to set up E2E test infrastructure"
3. **check** — "I need to verify the UI works right now"
