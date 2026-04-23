---
description: Universal TDD entrypoint. Routes your request to the `tdd-guide` agent and automatically loads the correct language testing skill based on the project context.
---

# Universal TDD Command (`/tdd`)

This command invokes the **tdd-guide** agent to enforce a rigorous Test-Driven Development (TDD) methodology across any supported language.

## What This Command Does

It acts as the smart routing layer for TDD:
1. **Invokes the `tdd-guide` Agent**: The strict execution engine that manages the Red-Green-Refactor state machine.
2. **Injects Methodology**: Automatically ensures the agent follows the language-agnostic `tdd-workflow` skill.
3. **Injects Syntax**: Instructs the agent to dynamically load the framework-specific testing skill for your current language (e.g., `python-testing`, `golang-testing`, `rust-testing`).

## When to Use

Use `/tdd` for almost all coding tasks where reliability is paramount:
- Implementing new features.
- Fixing bugs (you must write a failing test that reproduces the bug first).
- Refactoring complex logic safely.

## Example Usage

You do not need to specify the language. The command relies on the agent to detect the context or you can pass it explicitly.

```
User: /tdd I need a function to calculate market liquidity score

Agent (tdd-guide):
[STATE: RED]
I'll scaffold the interface and write a failing test. Let me check the testing framework for this project...
...
```

```
User: /tdd Create an endpoint for user registration.
```

## How It Replaces Legacy Commands

This command supersedes language-specific commands (like `/go-test` or `/python-test`). By centralizing the logic, the TDD methodology remains perfectly consistent across languages, while only the syntax changes.

**Note for Agents:**
When triggered via this command, the `tdd-guide` agent MUST proactively use the `Skill` tool to read the relevant language testing skill if it is unsure of the project's testing framework or mocking idioms.
