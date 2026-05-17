---
name: click-path-audit
description: Find state cancellation bugs in event handlers that runtime tests won't catch. Detects sequential undo bugs, stale closures, and event handler conflicts. TRIGGER on UI bugs, broken buttons, click not working, state not updating, event handler bugs.
arguments: scope
argument-hint: |
  <scope> -- component, page, or feature to audit (e.g., "form page", "checkout flow")
metadata:
  managed-by: ux-testing
---

# Click Path Audit

Find state cancellation bugs in event handlers that runtime tests won't catch deterministically.

## What This Detects

- **Sequential undo bugs** — State not reverting correctly on repeated undo
- **Stale closures** — Event handlers capturing outdated state
- **Handler conflicts** — Multiple handlers interfering with each other
- **Race conditions** — Async state updates causing inconsistent UI

## Process

1. Identify click paths in the specified scope
2. Trace event handler dependencies
3. Analyze state mutation sequences
4. Report potential bugs with reproduction steps

## Output

For each bug found:
- Location (file:line)
- Bug type (stale closure, handler conflict, race condition)
- Reproduction steps
- Fix suggestion
