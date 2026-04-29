# Architecture and Process

Operating models for teams and individuals doing AI-assisted development.

## Team Operating Model

### Process Shifts

1. **Planning quality matters more than typing speed**
   - AI generates code fast; correctness comes from specification clarity
   - Invest in decomposition and acceptance criteria upfront

2. **Eval coverage matters more than anecdotal confidence**
   - "It works on my machine" is insufficient
   - Automated evaluations catch regressions that manual review misses

3. **Review focus shifts from syntax to system behavior**
   - Style is enforced by automation (formatters, linters)
   - Human review focuses on invariants, edge cases, security assumptions

### Architecture Requirements

Prefer architectures that are agent-friendly:

| Quality | Rationale |
|---------|-----------|
| Explicit boundaries | Agents reason about contracts, not implicit conventions |
| Stable contracts | Reduces churn when implementation changes |
| Typed interfaces | Failures surface at boundaries, not deep in logic |
| Deterministic tests | AI-generated code needs regression detection |

Avoid implicit behavior spread across hidden conventions — agents struggle to discover and follow invisible rules.

### Code Review in AI-First Teams

Prioritize:
- Invariants and edge cases
- Security and auth assumptions
- Data integrity guarantees
- Failure handling completeness
- Rollout safety

Minimize time on style issues already covered by automation.

### Hiring and Evaluation Signals

Strong AI-first engineers demonstrate:
- Clean decomposition of ambiguous work
- Measurable acceptance criteria
- High-signal prompts and evals
- Risk controls under delivery pressure

---

## Individual Practices

### Eval-First Loop

```
Define capability eval  →  Run baseline  →  Capture failures
                                               ↓
Compare deltas  ←  Re-run evals  ←  Execute implementation
```

**Capability eval:** Tests that the feature works correctly  
**Regression eval:** Tests that existing behavior still works

### Task Decomposition

Apply the **15-minute unit rule**:
- Each unit independently verifiable
- Each unit has a single dominant risk
- Each unit has a clear done condition

### Model Routing

| Model Tier | Use For | Avoid |
|------------|---------|-------|
| Fast/Cheap | Classification, boilerplate transforms, narrow edits | Complex reasoning, architecture decisions |
| Balanced | Implementation, refactors, multi-file coordination | Root-cause analysis, subtle invariants |
| Strong | Architecture, root-cause analysis, complex invariants | Simple tasks (wasteful) |

Escalate tier only when lower tier fails with a clear reasoning gap.

### Session Strategy

- **Continue session** for closely-coupled units
- **Fresh session** after major phase transitions (clear context, avoid drift)
- **Compact** at milestone completion, not during active debugging

### Cost Discipline

Track per task:
- Model tier used
- Token estimate
- Retry count
- Wall-clock time
- Success/failure outcome

Review patterns: Are you using strong models for tasks that cheaper models handle? Are retries indicating unclear specifications?

### Testing Standard

Raise the testing bar for generated code:
- Required regression coverage for touched domains
- Explicit edge-case assertions
- Integration checks for interface boundaries

---

## Summary Checklist

Before shipping AI-assisted work:
- [ ] Eval defined and baseline captured
- [ ] Task decomposed into 15-minute units
- [ ] Model tier appropriate to complexity
- [ ] Regression tests written for bug fixes
- [ ] Review focused on invariants, not style
- [ ] Architecture constraints documented (boundaries, contracts)
