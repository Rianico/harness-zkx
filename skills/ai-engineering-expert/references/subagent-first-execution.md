# Subagent-First Execution

Full methodology for the subagent-first execution philosophy in LSZ architecture.

## Core Philosophy

**The orchestrator never does implementation work.** All code writing, file editing, test execution, doc updates, and review work happens in subagents. The main agent is a pure router: dispatch, monitor, receive results.

This is not a context optimization—it is a fundamental architectural constraint that ensures:
- Clean separation between orchestration logic and execution logic
- Predictable context budgets (orchestrator sees summaries, not full artifacts)
- Parallelizable work (multiple subagents can run concurrently)
- Isolated failure domains (subagent errors don't corrupt orchestrator state)

## Orchestrator vs Subagent Responsibilities

### Orchestrator DOES

- Route tasks to appropriate subagents
- Dispatch with structured prompts
- Monitor for completion/failure
- Receive and synthesize summaries
- Handle user interaction and approvals
- Pass pointers between phases

### Orchestrator NEVER DOES

- Write code directly
- Edit files directly
- Run tests directly
- Read full artifact contents into context
- Execute shell commands for implementation
- Re-process subagent outputs

## Dispatch Pattern

Always use structured dispatch templates with clear input/output contracts.

### Basic Template

```markdown
Agent tool (<subagent_type>):
  description: "<short task summary>"
  prompt: |
    <context and requirements>
    
    <execution instructions>
    
    Return: <expected output format>
```

### Example: Feature Implementation

```markdown
Agent tool (developer):
  description: "Implement auth refresh token rotation"
  prompt: |
    Plan file: /Users/.../plan/plan_v1.md
    
    Implement the refresh token rotation feature as described.
    Follow the architecture decisions in the plan.
    
    Return: Summary (approach + reasoning) + paths to modified files.
```

### Example: Code Review

```markdown
Agent tool (code-reviewer):
  description: "Review auth module changes"
  prompt: |
    Changed files:
    - src/auth/tokens.py
    - tests/test_tokens.py
    
    Review for quality, security, and maintainability.
    
    Return: Summary (key findings + recommendations) + paths to any issues.
```

## Pointer-Based State Passing

Subagents exchange state through **file paths**, not content. The orchestrator passes pointers; subagents read/write artifacts at those paths.

### Why Pointers

- Preserves orchestrator context budget
- Enables phase-to-phase continuity without orchestrator re-reading
- Supports large artifacts (plans, reports, code diffs)
- Allows downstream phases to access full context on demand

### Pattern

```markdown
Agent tool (developer):
  prompt: |
    Plan file: /path/to/.lsz/.../plan/plan_v1.md
    
    Implement the feature described in the plan.
    
    Return: Summary (≤100 words) + paths to modified files.
```

### Topic Root Convention

For multi-phase workflows, establish a shared topic root:

```
.lsz/{date}/{topic_creation_time}_{short_topic}/
├── plan/
│   └── plan_v1.md
├── implementation/
│   └── summary.md
├── review/
│   └── review_v1.md
└── evals/
    └── results.md
```

Orchestrator creates topic root once, passes it to each phase. Phases write to their subdirectory.

### Anti-Patterns

- Orchestrator reads plan, then passes plan content to subagent
- Subagent returns full artifact content instead of path
- Creating fresh topic roots for each phase instead of reusing one
- Orchestrator re-processing subagent outputs (summarizing summaries)

## Subagent Summary Contract

Every subagent MUST return a brief, structured summary. The orchestrator's context depends on it.

### Summary Style: BurntSushi's PR Approach

Summaries are complete, coherent, reviewable units:
- State approach and reasoning, not just "what was done"
- Deliver a position that can be critiqued
- Not "let me try something and see what you think"
- But "here's my approach, here's the reasoning, tell me where I'm wrong"

### Summary Format

```markdown
## Summary
<approach taken, reasoning behind key decisions, and outcome>

## Artifacts
- <path to primary output>
- <path to secondary outputs if any>

## Trade-offs (optional)
- <key trade-off or constraint for next phase>
```

### Size Constraints

- Status-only reports: ≤100 words, bullet list
- Decision/constraint reports: ≤150 words, star rules format
- Never return full artifact contents in the summary

### Example (Good)

```markdown
## Summary
Added retry logic to the database connector with exponential backoff (max 3 retries, 2s base delay). Chose this over circuit breaker because the failure mode is transient connection drops, not sustained outages. Tests cover happy path and all retry scenarios.

## Artifacts
- src/db/connector.py
- tests/test_db_connector.py
```

### Example (Bad - Just "What Was Done")

```markdown
## Summary
Added retry logic to the database connector. Tests pass.

## Artifacts
- src/db/connector.py
```

The good example delivers a reviewable position: here's the approach, here's why, here's what's covered. The bad example is a status update that forces the reviewer to read the code to understand the reasoning.

## Subagent Type Selection

| Task | Subagent Type | Why |
|------|---------------|-----|
| Write/modify code | `developer` | Implementation specialist |
| Review code for quality | `code-reviewer` | Quality/maintainability focus |
| Security analysis | `security-reviewer` | Security vulnerability expertise |
| Database schema work | `database-reviewer` | PostgreSQL/Supabase expertise |
| Research/explore codebase | `Explore` | Fast read-only search |
| General multi-step tasks | `general-purpose` | Flexible execution |
| Architecture design | `architect` | System design specialist |

## Parallel Execution

When tasks are independent, dispatch multiple subagents concurrently:

```markdown
# Single tool call with multiple Agent invocations
Agent tool (code-reviewer):
  description: "Review frontend changes"
  prompt: |
    Files: src/components/Auth.tsx, src/hooks/useAuth.ts
    Review for quality and patterns.

Agent tool (security-reviewer):
  description: "Security review of auth flow"
  prompt: |
    Files: src/auth/, src/api/auth.ts
    Review for OWASP Top 10 and auth vulnerabilities.
```

The orchestrator receives both results in parallel, maintaining context efficiency.

## Anti-Patterns

### Hero Mode Orchestrator

```markdown
# WRONG: Orchestrator doing implementation
Let me just write this quick fix directly...

# RIGHT: Dispatch to subagent
Agent tool (developer):
  description: "Fix null pointer in auth flow"
  prompt: |
    Issue: Null pointer when user session expires during token refresh.
    File: src/auth/refresh.py
    
    Fix the issue and add regression test.
```

### Context Hoarding

```markdown
# WRONG: Reading full file into orchestrator context
Let me read the plan file to understand the requirements...

# RIGHT: Pass pointer to subagent
Agent tool (developer):
  prompt: |
    Plan file: /path/to/plan_v1.md
    Implement the feature.
```

### Sequential When Parallel Is Possible

```markdown
# WRONG: Running reviews sequentially
1. Run code-reviewer
2. Wait for result
3. Run security-reviewer

# RIGHT: Dispatch both concurrently
Agent tool (code-reviewer): ...
Agent tool (security-reviewer): ...
```

### Orchestrator as Reviewer

```markdown
# WRONG: Main agent reviewing code
Let me review these changes for quality...

# RIGHT: Dispatch to specialist
Agent tool (code-reviewer):
  description: "Review feature changes"
  prompt: |
    Files: [list of changed files]
    Review for quality, security, and maintainability.
```

## Enforcement

Skills that orchestrate work MUST:

1. Define dispatch templates for each phase
2. Use pointer-based state passing (file paths, not content)
3. Require structured summaries from subagents
4. Avoid any direct implementation work in orchestrator
5. Run independent subagents in parallel

The orchestrator's job is routing and synthesis. Everything else is delegation.
