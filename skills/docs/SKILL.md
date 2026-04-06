---
name: docs
description: Invoke the docs-lookup agent to fetch up-to-date library and framework docs instead of relying on training data. Activates for setup questions, API references, code examples, or when the user names a framework.
---

# Documentation Lookup

This skill invokes the `docs-lookup` agent to fetch up-to-date documentation.

When the user asks about libraries, frameworks, or APIs (e.g., React, Next.js, Prisma, Supabase), delegate the research task to the `docs-lookup` agent rather than performing MCP queries manually or relying on your training data.

## How it works

Use the Agent tool to launch the docs-lookup agent:
```json
{
  "subagent_type": "docs-lookup",
  "description": "{description}",
  "prompt": "{prompt}"
}
```

### Writing the Agent Prompt

To ensure the agent returns useful information instead of over-summarizing, your prompt to the agent must be specific and demand code examples:

1. **Be specific**: Pass along the exact library name, version (if applicable), and the user's detailed task.
2. **Demand code snippets**: Explicitly tell the agent to return the literal code examples required to implement the solution, not just high-level concepts.
3. **Redact sensitive data**: Do not pass API keys, passwords, tokens, or proprietary codebase secrets into the agent's prompt.

## When to use

Activate when the user:

- Asks setup or configuration questions (e.g. "How do I configure Next.js middleware?")
- Requests code that depends on a library ("Write a Prisma query for...")
- Needs API or reference information ("What are the Supabase auth methods?")
- Mentions specific frameworks or libraries (React, Vue, Svelte, Express, Tailwind, Prisma, Supabase, etc.)

## Examples

### Example: Next.js middleware

**User:** "How do I set up Next.js middleware?"
**Action:** Use the Agent tool to launch the docs-lookup agent:
```json
{
  "subagent_type": "docs-lookup",
  "description": "Find Next.js middleware setup",
  "prompt": "Look up how to configure middleware in Next.js. I need the exact code snippet for a basic middleware.ts file and instructions on where it should be placed in the project structure."
}
```

### Example: Prisma query

**User:** "How do I write a Prisma query to find a user and include their relations?"
**Action:** Use the Agent tool to launch the docs-lookup agent:
```json
{
  "subagent_type": "docs-lookup",
  "description": "Find Prisma relation queries",
  "prompt": "Find documentation on how to query with relations in Prisma. Please return the exact Prisma Client code patterns (e.g., using 'include' or 'select')."
}
```
