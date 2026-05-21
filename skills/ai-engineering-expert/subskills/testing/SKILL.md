---
name: testing
description: >-
  AI regression testing patterns, sandbox/production mismatch detection, error state leakage tests, and optimistic update rollback verification for the LSZ architecture.
metadata:
  managed-by: ai-engineering-expert
---

# Testing

Testing patterns specific to AI-generated code and AI engineering workflows.

## The Core Problem

When the same AI writes and reviews code, it carries the same assumptions into both steps. Systematic blind spots emerge that only automated tests catch.

## Top Regression Patterns

1. Sandbox/production path mismatch
2. SELECT clause omission
3. Error state leakage
4. Optimistic update without rollback

## Test Strategy

Write tests for bugs that were found, not for code that works. AI tends to make the same category of mistakes repeatedly -- once tested, that regression cannot happen again.

## Reference

[Full details: sandbox-testing-patterns.md](references/sandbox-testing-patterns.md)
