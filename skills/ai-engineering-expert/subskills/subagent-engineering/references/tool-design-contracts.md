# Tool Design Contracts

Designing agent action spaces, tool definitions, and observation formatting for reliable subagent execution.

## Core Quality Model

Agent output quality depends on four core properties:

1. **Action space quality:** Can the agent express the intended operations unambiguously?
2. **Observation quality:** Does the agent receive clean environmental truth to guide decisions?
3. **Recovery quality:** Can the agent handle errors gracefully without human intervention?
4. **Context budget quality:** Is guidance loaded when needed, not before? (governed by [context-load-policy.md](../../../references/context-load-policy.md)).

---

## Action Space Design

### Core Principles

1. **Use stable, explicit tool names**
   - Prefer `create_user` over `user_management` with an action parameter.
   - Names describe what happens, not the broad domain.

2. **Keep inputs schema-first and narrow**
   - Make required fields explicit and keep optional fields minimal.
   - Avoid polymorphic inputs where one field accepts multiple types.

3. **Return deterministic output shapes**
   - Return the same structural schema for identical operations, even on error.
   - Agents pattern-match on output. Variance degrades reasoning.

4. **Avoid catch-all tools unless isolation is impossible**
   - Generic `run_command` is sometimes necessary.
   - Prefer domain tools like `deploy_service`, `run_tests`, or `validate_config`.

### Tool Granularity Matrix

| Size | Use Case | Latency vs Risk | Example |
|---|---|---|---|
| **Micro** | Dangerous or destructive operations | High safety, higher round-trip overhead | `deploy_production`, `migrate_database` |
| **Medium** | Common read, edit, or search loops | Balanced safety and throughput | `read_file`, `edit_file`, `grep_search` |
| **Macro** | Batch operations with high round-trip overhead | Fast throughput, lower intermediate visibility | `process_pdf_batch`, `scrape_site_corpus` |

Start medium by default. Use micro for destructive operations and macro for high-volume pipelines.

---

## Observation Design Contracts

Observation design depends on the tool runtime:

### 1. Passive Runtime Truth (Shell & CLI Commands)

Standard terminal commands return native execution truth:
- Stream stdout, stderr, and exit codes directly.
- Never wrap standard shell outputs in artificial JSON envelopes.
- Capture output passively using pipes or log streams instead of polling with blind query loops.

### 2. Structured Return Contracts (RPC & MCP Endpoints)

Specialized RPC or Model Context Protocol (MCP) endpoints must return structured envelopes:

```yaml
status: success | warning | error
summary: one-line result describing the outcome
next_actions: list of actionable next steps
artifacts: list of file paths, identifiers, or links produced
```

#### Structured Success Example

```yaml
status: success
summary: "Created 3 database migrations for user schema changes"
next_actions:
  - "Run npm run migrate:verify to check migration validity"
  - "Review generated files in migrations/20241201_*.sql"
artifacts:
  - migrations/20241201_add_user_profile.sql
  - migrations/20241201_add_user_preferences.sql
  - migrations/20241201_create_user_indexes.sql
```

---

## Error Recovery Contracts

Every tool error path must return actionable diagnostic metadata:

1. **Root cause hint:** State the concrete failure condition, not just that execution failed.
2. **Safe retry instruction:** State what parameter or environment state to modify before retrying.
3. **Explicit stop condition:** State when the subagent must stop and escalate to the orchestrator.

### Error Recovery Example

```yaml
status: error
summary: "Migration failed: column email already exists"
root_cause: "The migration assumes an empty schema, but the database holds prior tables"
retry_instruction: "Run with --force to rebuild schema, or drop conflicting columns manually"
stop_condition: "If --force fails or data loss risk exists, escalate to user"
```

---

## Tool Design Anti-Patterns

- **Polymorphic parameters:** A single argument accepting either a string or an object confuses the model.
- **Forced JSON on shell tools:** Wrapping raw compiler output in JSON envelopes wastes tokens and breaks diff parsers.
- **Opaque error strings:** Returning generic error codes with no root cause or retry guidance creates infinite retry loops.
- **Overlapping tool semantics:** Providing multiple tools that perform similar operations forces the agent to guess.
- **Unbounded toolsets:** Injecting dozens of tools into a subagent dilutes tool selection accuracy.

---

## Tool Authoring Checklist

- [ ] Tool name is explicit, stable, and active-voice.
- [ ] Input schema is narrow, strictly typed, and non-polymorphic.
- [ ] Output schema returns deterministic shapes.
- [ ] Shell tools return native stdout and stderr streams.
- [ ] RPC and MCP tools return structured envelopes with summary and artifacts.
- [ ] Error paths return root cause, retry instruction, and stop condition.
- [ ] Granularity matches operation risk (micro for destructive, macro for batch).
- [ ] Tool does not duplicate existing action space capabilities.
