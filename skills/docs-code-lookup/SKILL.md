---
name: docs-code-lookup
description: |
  Fetch current library documentation and code examples. TRIGGER when: user asks how to use a library, framework, or API; needs setup guide, configuration help, or code examples; asks about React, Next.js, Prisma, Supabase, Tailwind, Express, Vue, Django, or any library.
argument-hint: "<library> <question>"
---

# Docs Code Lookup

Fetch up-to-date documentation and working code examples for libraries and frameworks.

## Purpose

Training data becomes stale. This skill fetches current docs via Context7 MCP to provide accurate, copy-pasteable answers.

## When to Use

- Setup or configuration questions ("How do I configure Next.js middleware?")
- API usage questions ("What are the Supabase auth methods?")
- Code that depends on a library ("Write a Prisma query for...")
- Any question about a specific library or framework

## Workflow

Invoke the `docs-lookup` agent with a structured prompt:

```text
Agent tool (docs-lookup):
  description: "Fetch docs for <library>"
  prompt: |
    Look up documentation for: <library>

    Question: <user's specific question>

    Requirements:
    1. Return working code examples, not just explanations
    2. Cite the library version if available
    3. If the question is ambiguous, ask for clarification before querying
```

## Agent Output

The agent returns:
- **Direct answer** — Short, focused on the question
- **Code examples** — Copy-pasteable snippets
- **Source citation** — e.g., "From the official Next.js docs..."

## Prompt Guidelines

When invoking the agent:

1. **Be specific** — Pass the exact library name and user's question
2. **Demand code** — Explicitly request code examples
3. **Redact secrets** — Never pass API keys, passwords, or tokens

## Limitations

- Only covers libraries in Context7's database
- For bulk doc downloads, use the `scraper` skill instead
- For building local skill references, use `docs-to-skill` skill

## Example Invocation

**User:** "How do I set up Next.js middleware?"

**Skill action:**
```text
Agent tool (docs-lookup):
  description: "Fetch Next.js middleware docs"
  prompt: |
    Look up documentation for: Next.js

    Question: How do I configure middleware in Next.js?

    Requirements:
    1. Return the exact code snippet for a basic middleware.ts file
    2. Explain where it should be placed in the project structure
    3. Include any configuration options
```
