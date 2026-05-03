# Domain Expert Consultation

## Purpose
Ensure domain expertise is leveraged before diving into problem-solving or implementation, reducing the risk of misaligned solutions.

## Consultation Requirement

**Before thinking through a question or executing a task, you MUST:**

1. **Identify relevant domain expertise** — Determine which domain knowledge applies to the task
2. **Invoke the appropriate expert skill** — Load domain-specific skills before proceeding
3. **Review expert methodology** — Read the expert's guidance, patterns, and constraints
4. **Apply expert framework** — Use the expert's structured approach for analysis and decisions

## Enforcement

- System prompt should remind at task start
- User can explicitly request expert bypass for simple tasks
- Expert invocation is mandatory for complex or unfamiliar domains

## Exceptions

- Trivial, single-step tasks with clear precedent
- Emergency fixes where delay introduces risk
- Tasks explicitly scoped by user to skip consultation

## Anti-Patterns

- Guessing at domain constraints without expert input
- Applying generic solutions to specialized domains
- Skipping expert methodology because "it seems simple"
