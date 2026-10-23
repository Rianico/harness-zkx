# Eval-First Development

Verification practice for AI-assisted development: define the eval, decompose the work, then compare deltas.

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
