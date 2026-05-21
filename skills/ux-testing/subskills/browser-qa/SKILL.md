---
name: browser-qa
description: >-
  Ad-hoc QA and post-deploy monitoring for UI verification. Supports single-pass checks, sustained monitoring, and environment comparison. TRIGGER on browser testing, UI verification, post-deploy check, staging vs prod, ad-hoc QA.
arguments: mode options
argument-hint: >-
  |
  --once -- single-pass ad-hoc QA check
  --watch --interval 5m --duration 2h -- sustained monitoring
  --compare <staging> <prod> -- diff mode comparing environments
metadata:
  managed-by: ux-testing
---

# Browser QA

Ad-hoc QA and post-deploy monitoring for verifying user-facing experience.

## Modes

### `--once` (default)

Single-pass ad-hoc QA check. Visits key pages, checks for errors, reports findings.

### `--watch --interval 5m --duration 2h`

Sustained post-deploy monitoring. Periodically checks UI health with alert thresholds.

### `--compare <staging> <prod>`

Diff mode. Compares staging and production environments for discrepancies.

## What It Checks

- Page load success
- Console errors
- Broken links
- Missing assets
- Layout issues
- Functional flows

## Output

- QA report with findings
- Screenshots of issues
- Environment diff summary (if compare mode)
