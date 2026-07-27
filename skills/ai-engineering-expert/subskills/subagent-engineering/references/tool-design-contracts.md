# Harness Design

Designing agent action spaces, tool definitions, and observation formatting for reliable completion.

## Core Quality Model

Agent output quality is constrained by:

1. **Action space quality** — Can the agent express the right operations?
2. **Observation quality** — Does the agent see what it needs to decide?
3. **Recovery quality** — Can the agent handle errors gracefully?
4. **Context budget quality** — Is guidance loaded when needed, not before?

## Action Space Design

### Rules

1. **Use stable, explicit tool names**
   - Prefer `create_user` over `user_management` with mode parameter
   - Names should describe what happens, not what domain

2. **Keep inputs schema-first and narrow**
   - Required fields explicit, optional fields minimal
   - Avoid polymorphic inputs (same field accepts string or object)

3. **Return deterministic output shapes**
   - Same inputs → same structure, even on error
   - Agents pattern-match on output; variance breaks reasoning

4. **Avoid catch-all tools unless isolation is impossible**
   - Generic `run_command` is necessary sometimes
   - Prefer specific `deploy_service`, `run_tests`, `validate_config`

### Granularity Rules

| Size | Use Case | Example |
|------|----------|---------|
| Micro | High-risk operations | `deploy_production`, `migrate_database`, `grant_admin_access` |
| Medium | Common edit/read/search loops | `read_file`, `edit_file`, `grep_search` |
| Macro | Round-trip overhead dominates | `process_pdf_batch` (when each file needs 10+ operations) |

When in doubt, start medium. Micro for safety, macro for latency.

## Observation Design

Every tool response should include:

```
status:       success | warning | error
summary:      one-line result (what happened)
next_actions: list of actionable follow-ups
artifacts:    file paths, IDs, URLs produced
```

### Example

```yaml
status: success
summary: "Created 3 database migrations for user schema changes"
next_actions:
  - "Run `npm run migrate:verify` to check migration validity"
  - "Review generated files in `migrations/20241201_*.sql`"
artifacts:
  - migrations/20241201_add_user_profile.sql
  - migrations/20241201_add_user_preferences.sql
  - migrations/20241201_create_user_indexes.sql
```

### Anti-Patterns

- Empty success with no artifacts
- Error-only response with no recovery hint
- Wall of text summary (should be one line)
- Missing next_actions when agent could continue

## Error Recovery Contract

For every error path, include:

1. **Root cause hint** — What went wrong, not just that it failed
2. **Safe retry instruction** — What to change before retrying
3. **Explicit stop condition** — When to escalate to human

### Example

```yaml
status: error
summary: "Migration failed: column 'email' already exists"
root_cause: "The migration assumes a fresh schema, but this database has prior migrations"
retry_instruction: "Run with --force to recreate schema, or remove conflicting migrations"
stop_condition: "If --force fails or data loss risk, escalate to DBA"
```

## Context Budgeting

1. **Keep system prompt minimal and invariant**
   - Don't stuff with domain knowledge that changes per task

2. **Move large guidance into skills loaded on demand**
   - Progressive disclosure: metadata always, body on trigger, references as needed

3. **Prefer references to files over inlining long documents**
   - "See [patterns.md](patterns.md) for detailed guidance" vs 200 lines inline

4. **Compact at phase boundaries, not arbitrary token thresholds**
   - After completing a feature, compact history
   - Don't compact mid-debugging (loses context)

## Architecture Pattern Guidance

| Pattern | Best For | Avoid |
|---------|----------|-------|
| ReAct | Exploratory tasks with uncertain path | Deterministic workflows |
| Function-calling | Structured, predictable flows | Open-ended research |
| Hybrid (recommended) | ReAct planning + typed tool execution | — |

## Benchmarking

Track:
- **Completion rate** — % of tasks finishing successfully
- **Retries per task** — Efficiency metric
- **pass@1 and pass@3** — Success without vs with retries
- **Cost per successful task** — Economic efficiency

## Anti-Patterns

- **Too many tools with overlapping semantics** — Agent wastes time choosing
- **Opaque tool output with no recovery hints** — Agent gets stuck
- **Error-only output without next steps** — Dead end
- **Context overloading with irrelevant references** — Token waste, distraction

## Summary Checklist

Designing a new tool or harness:
- [ ] Action name is stable and explicit
- [ ] Input schema is narrow and typed
- [ ] Output shape is deterministic
- [ ] Errors include root cause, retry hint, stop condition
- [ ] Success includes summary, next_actions, artifacts
- [ ] Granularity matches risk (micro for dangerous, macro for efficient)
- [ ] Not duplicating existing tools
