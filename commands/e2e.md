---
description: Universal E2E entrypoint. Routes your request to the `e2e-runner` agent and automatically loads the correct testing methodology based on the project context.
---

# Universal E2E Command (`/e2e`)

This command invokes the **e2e-runner** agent to enforce a rigorous End-to-End Testing methodology, whether using Playwright, Agent Browser, Cypress, or Selenium.

## What This Command Does

It acts as the smart routing layer for E2E testing:
1. **Invokes the `e2e-runner` Agent**: The strict execution engine that manages the Plan -> Scaffold -> Write -> Execute -> Quarantine state machine.
2. **Injects Methodology**: Automatically ensures the agent follows the language/framework-agnostic `e2e-workflow` skill.
3. **Injects Tooling**: Instructs the agent to dynamically load the framework-specific testing syntax (e.g., `playwright-testing` or `agent-browser` documentation) for your current project.

## When to Use

Use `/e2e` for testing critical user journeys where backend-frontend integration is key:
- Writing tests for user flows (login, trading, search, CRUD).
- Setting up cross-browser test suites.
- Resolving and quarantining flaky tests in CI.
- Generating artifacts (screenshots, traces, videos) for debugging failures.

## Example Usage

You do not need to specify the framework. The command relies on the agent to detect the context or you can pass it explicitly.

```
User: /e2e Test the market search and view flow

Agent (e2e-runner):
[STATE: PLAN]
I will formalize the critical user journey for this search flow. Let me check the testing framework for this project...
...
```

```
User: /e2e The auth tests are flaky in CI. Fix them.
```
