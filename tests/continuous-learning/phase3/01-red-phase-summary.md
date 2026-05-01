# Phase 3 RED: Observer Agent Tests

## Summary

Created failing tests for Phase 3 (Observer Agent) of the continuous learning system. Tests verify pattern detection capabilities and structured output schema compliance.

## Test Results

```
19 failed, 20 passed in 0.24s
```

**Passing tests**: Schema validation (20 tests) - Pydantic models correctly defined
**Failing tests**: Pattern detection (19 tests) - `analyze_session()` returns `None` stub

## Created Files

### Test Fixtures

| Path | Purpose |
|------|---------|
| `fixtures/expected_outputs/user_correction.json` | Expected instinct for rejection pattern |
| `fixtures/expected_outputs/repeated_workflow.json` | Expected instinct for workflow pattern |
| `fixtures/expected_outputs/error_resolution.json` | Expected instinct for resolution pattern |
| `fixtures/expected_outputs/README.md` | Fixture documentation |

### Test Files

| Path | Tests | Eval Criteria |
|------|-------|---------------|
| `phase3/test_pattern_correction.py` | 7 tests | Eval 3.1: User correction detection |
| `phase3/test_pattern_workflow.py` | 6 tests | Eval 3.2: Repeated workflow detection |
| `phase3/test_pattern_resolution.py` | 8 tests | Eval 3.3: Error resolution detection |
| `phase3/test_structured_output.py` | 18 tests | Eval 3.4: Structured output validation |

### Implementation Stub

| Path | Purpose |
|------|---------|
| `hooks/observe/agent_runner.py` | Agent runner stub with Pydantic schemas |

## Pass Criteria (from eval-criteria.md)

### Eval 3.1: Pattern Detection - User Correction
- [ ] Correction pattern detected
- [ ] Instinct created with appropriate trigger
- [ ] Confidence in range [0.3, 0.9]
- [ ] Evidence recorded

### Eval 3.2: Pattern Detection - Repeated Workflow
- [ ] Workflow sequence detected
- [ ] Minimum 3 repetitions required
- [ ] Confidence starts at 0.7

### Eval 3.3: Pattern Detection - Error Resolution
- [ ] Error pattern detected
- [ ] Resolution strategy captured
- [ ] Confidence starts at 0.6

### Eval 3.4: Structured Output
- [x] Output is valid JSON
- [x] Schema validation passes
- [x] No extra fields
- [x] Required fields present

## Next Steps (GREEN Phase)

1. Implement `analyze_session()` in `agent_runner.py` to detect:
   - User correction patterns (Edit rejected -> Read -> Edit success)
   - Repeated workflow patterns (same sequence 3+ times)
   - Error resolution patterns (error -> modified approach -> success)

2. Implement `run()` to aggregate session analyses into `AgentResult`

3. Pattern detection logic should:
   - Parse event sequences
   - Identify trigger conditions
   - Generate appropriate confidence values
   - Record evidence with session IDs
