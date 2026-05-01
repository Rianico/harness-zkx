# Phase 4: Instinct Management - RED Phase Summary

## Status: RED Phase Complete

## Tests Created

### Fixtures
- `tests/continuous-learning/fixtures/instincts/existing_instinct.yaml` - Sample instinct for update tests
- `tests/continuous-learning/fixtures/agent_results/creation_result.json` - Agent result with new instinct
- `tests/continuous-learning/fixtures/agent_results/update_result.json` - Agent result updating existing instinct
- `tests/continuous-learning/fixtures/agent_results/promotion_result.json` - Agent result with promotion

### Test Files
1. `tests/continuous-learning/phase4/test_instinct_creation.py` (8 tests)
2. `tests/continuous-learning/phase4/test_instinct_update.py` (9 tests)
3. `tests/continuous-learning/phase4/test_instinct_promotion.py` (13 tests)

### Stub Module
- `hooks/observe/instinct_manager.py` - Stub implementation returning None/empty

## Test Results

```
collected 30 items
26 failed, 4 passed in 0.35s
```

Tests fail because `InstinctManager` methods return `None` instead of implementing the logic.

## Eval Coverage

### Eval 4.1: Instinct Creation
- [x] File created at `instincts/personal/<id>.yaml`
- [x] YAML frontmatter valid
- [x] Content matches agent result
- [x] Timestamps set correctly

### Eval 4.2: Instinct Update
- [x] Confidence score updated
- [x] Evidence list extended
- [x] updated_at timestamp refreshed
- [x] No duplicate evidence

### Eval 4.3: Instinct Promotion
- [x] Instinct moved/linked to global directory
- [x] scope changed to "global"
- [x] project_id set to "global"
- [x] Promotion reason logged

## Next Steps (GREEN Phase)
1. Implement `InstinctManager.create_instinct()` - Create YAML files from InstinctCreated
2. Implement `InstinctManager.update_instinct()` - Update confidence and append evidence
3. Implement `InstinctManager.promote_instinct()` - Move to global scope with eligibility check
4. Implement `InstinctManager.process_result()` - Process AgentResult for all operations
