---
name: e2e-workflow
description: >-
  Build maintainable E2E test infrastructure with Page Object Model, locator strategies, and flakiness quarantine. TRIGGER on E2E testing, Playwright setup, test infrastructure, POM, locator strategy, flaky tests.
arguments: feature
argument-hint: |-
  <feature> -- feature or page to build E2E tests for (e.g., "login flow", "checkout")
metadata:
  managed-by: ux-testing
---

# E2E Workflow

Build maintainable E2E test infrastructure with Page Object Model and flakiness prevention.

## Components

- **Page Object Model** — Encapsulate page structure and actions
- **Locator strategies** — Resilient selectors that survive UI changes
- **Flakiness quarantine** — Isolate and fix flaky tests

## Process

1. Identify test scenarios for the feature
2. Create Page Object classes
3. Implement test cases with robust locators
4. Set up flakiness detection and quarantine

## Output

- `tests/e2e/pages/` — Page Object classes
- `tests/e2e/specs/` — Test specifications
- `tests/e2e/quarantine/` — Isolated flaky tests
- Test configuration updates
