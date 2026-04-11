---
name: e2e-workflow
description: Language-agnostic End-to-End Testing methodology. Enforces Page Object Model (POM), stable locator strategies, auto-waiting, artifact capture, and flaky test quarantine.

---

# End-to-End (E2E) Testing Workflow

This skill defines the behavioral methodology and architecture for writing stable, maintainable End-to-End (E2E) tests. It focuses on the *what* and *when* of browser testing. 

For the *how* (syntax, frameworks, configurations), this skill relies on the chosen automation tool for the project (e.g., `agent-browser`, `playwright`).

## Core Testing Philosophy

E2E tests are expensive to write, slow to run, and prone to flakiness. They must be treated as the last line of defense for critical user journeys.

1. **Test Journeys, Not Details:** E2E tests should verify complete user flows (e.g., "User can sign up, log in, and create a project"). Do not use E2E to test granular UI states or complex business logic algorithms (use unit/integration tests for those).
2. **Fail Fast, Fail Loud:** Every key interaction must have a corresponding assertion. If a step fails, the test must halt immediately and capture the exact state (screenshots, DOM snapshots).
3. **Zero Flakiness Tolerance:** A flaky test is worse than no test. If a test fails 1 out of 10 times in CI, it must be quarantined immediately until the root cause (usually a race condition) is fixed.

## Architectural Requirements

### 1. The Page Object Model (POM)
You must strictly separate test logic from page interaction logic. Tests should never contain raw CSS selectors or API URLs.

*   **Pages:** Create a class/object for each logical page or major component.
*   **Locators:** Define all element selectors as properties of the page object.
*   **Actions:** Define user interactions (e.g., `login(user, pass)`, `search(query)`) as methods on the page object.

### 2. Resilient Locator Strategy
Never use brittle selectors that are subject to styling changes.
*   **BEST:** User-facing text (`text="Submit"`), accessible roles (`role="button" name="Submit"`), or explicit test IDs (`data-testid="submit-btn"`).
*   **POOR:** CSS classes (`.btn-primary`), long XPath chains, DOM hierarchy paths (`div > ul > li:nth-child(3)`).

### 3. Asynchronous Stability (Auto-Waiting)
The web is asynchronous. Your tests must account for network latency, animations, and rendering cycles.
*   **NEVER** use arbitrary timeouts (e.g., `sleep(5000)`).
*   **ALWAYS** wait for specific state changes:
    *   Wait for an element to become visible/hidden.
    *   Wait for a specific API response to complete.
    *   Wait for the network state to reach 'idle'.

## Execution State Machine

When operating as the `e2e-runner` agent, you must progress through these states in order. 

### State 1: PLAN (Identify the Journey)
1. Read the user's request and identify the *critical user journey*.
2. Define the start state, the sequence of actions, and the expected end state.
3. Identify the necessary Page Objects.

### State 2: SCAFFOLD (Build the POM)
1. Create or update the relevant Page Object files.
2. Define resilient locators for all required elements.
3. Define the interaction methods (e.g., `fillForm()`, `submit()`).

### State 3: WRITE (Create the Test)
1. Write the test specification file.
2. Import the Page Objects.
3. Write the test sequence using the Page Object methods.
4. Add assertions at key validation points.

### State 4: EXECUTE & CAPTURE (Run the Test)
1. Run the test using the project's specific automation CLI.
2. If the test fails:
    *   Analyze the captured artifacts (screenshots, traces, error logs).
    *   Identify if the failure is a genuine bug or a flaky test implementation (e.g., a race condition).
    *   Return to State 2 or 3 to fix the implementation.
3. If the test passes, run it repeatedly (e.g., 3-5 times) locally to ensure stability.

### State 5: QUARANTINE (Handle Flakiness)
If a test cannot be immediately stabilized, it must be marked as skipped or "fixme" in the test suite so it does not block the CI pipeline, with a clear comment explaining the flakiness.

## Tooling Fallback Hierarchy

The `e2e-runner` must detect the correct execution tool based on the project environment:

### Primary: Agent Browser (`agent-browser`)
Use `agent-browser` when semantic, AI-optimized execution is possible. It handles auto-waiting and semantic selection dynamically.

**Core Workflow:**
```bash
# Setup
npm install -g agent-browser && agent-browser install

# Execution Loop
agent-browser open https://example.com
agent-browser snapshot -i          # Get elements with refs [ref=e1]
agent-browser click @e1            # Click by ref
agent-browser fill @e2 "text"      # Fill input by ref
agent-browser wait visible @e5     # Explicitly wait for element state
agent-browser screenshot result.png
```

### Fallback: Playwright (`npx playwright`)
When `agent-browser` is not applicable or you are generating persistent test files for a CI pipeline, use Playwright.

**Core Workflow:**
```bash
npx playwright test                        # Run all E2E tests
npx playwright test tests/auth.spec.ts     # Run specific file
npx playwright test --headed               # Run with UI visible
npx playwright test --debug                # Debug with inspector
npx playwright test --trace on             # Run with trace capture
npx playwright test --repeat-each=5        # Check for flakiness
npx playwright show-report                 # View HTML report
```
