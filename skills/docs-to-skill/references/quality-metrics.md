# Quality Metrics

Criteria for evaluating generated skill quality.

## Overall Score Calculation

```
overall_score = weighted_average(criterion_scores)
```

## Criteria

### 1. Trigger Coverage (20%)

**Check:** Do triggers cover all major API surfaces?

| Aspect | Points |
|--------|--------|
| All types have triggers | +0.4 |
| All major functions have triggers | +0.3 |
| Problem-framing triggers present | +0.2 |
| Query-style triggers present | +0.1 |

**Evaluation:**
```python
trigger_coverage = (
    0.4 * (types_covered / total_types) +
    0.3 * (functions_covered / total_functions) +
    0.2 * (1 if problem_triggers else 0) +
    0.1 * (1 if query_triggers else 0)
)
```

### 2. Pattern Usefulness (20%)

**Check:** Are patterns practical and common?

| Aspect | Points |
|--------|--------|
| Initialization pattern present | +0.25 |
| Common usage patterns (3+) | +0.25 |
| Stateful patterns if applicable | +0.25 |
| Error handling patterns | +0.25 |

**Evaluation:**
- Check pattern categories
- Verify code examples are runnable
- Assess if patterns solve common problems

### 3. Beginner Friendliness (15%)

**Check:** Are there simple getting-started patterns?

| Aspect | Points |
|--------|--------|
| "Hello world" pattern | +0.3 |
| Step-by-step tutorial style | +0.3 |
| Simple before complex examples | +0.2 |
| Clear explanations | +0.2 |

**Bonus:** +0.2 if supplementary docs were provided

### 4. Documentation Completeness (15%)

**Check:** Do curated references cover key features? Are extraction rules followed? Is raw docs fallback self-contained?

| Aspect | Points |
|--------|--------|
| All modules have curated reference files | +0.2 |
| Reference files have mandatory metadata header | +0.2 |
| Reference files follow template schemas | +0.2 |
| Reference files use `$SKILL_DIR` path pattern | +0.2 |
| Raw docs copied into `references/<skill-name>-raw/` | +0.2 |

**Note:** Skills must be self-contained. Raw docs are copied into `references/<skill-name>-raw/` within the skill. Reference quality is governed by extraction rules, not line counts.

### 5. Navigation Clarity (15%)

**Check:** Is the module table easy to understand?

| Aspect | Points |
|--------|--------|
| Module table present in SKILL.md | +0.3 |
| Topics listed for each module | +0.25 |
| Consistent naming | +0.25 |
| Clear separation of concerns | +0.2 |

### 6. Graceful Degradation (15%)

**Check:** Does the skill work without reference files? Is raw docs fallback clear?

| Aspect | Points |
|--------|--------|
| SKILL.md has key patterns inline | +0.3 |
| References table uses `$SKILL_DIR` paths | +0.3 |
| API reference table present | +0.2 |
| "When to use raw docs" guidance in SKILL.md | +0.2 |

## Scoring Thresholds

| Score | Rating | Action |
|-------|--------|--------|
| >= 0.9 | Excellent | Proceed |
| 0.7 - 0.9 | Good | Proceed with minor suggestions |
| 0.5 - 0.7 | Acceptable | Show suggestions, user choice |
| < 0.5 | Needs Work | Require improvements |

### Minimum Per-Criterion Scores

| Criterion | Minimum | Reason |
|-----------|---------|--------|
| Trigger Coverage | 0.6 | Skills need discoverability |
| Pattern Usefulness | 0.5 | Skills need practical value |
| Beginner Friendliness | 0.5 | Attract new users |
| Graceful Degradation | 0.7 | Skills must work offline |

## Suggestion Generation

Automatically generate suggestions for low-scoring criteria:

```python
def generate_suggestions(scores, patterns):
    suggestions = []
    
    if scores.trigger_coverage < 0.7:
        missing = find_missing_triggers()
        suggestions.append(f"Add triggers for: {missing}")
    
    if scores.beginner_friendliness < 0.7:
        if not has_hello_world(patterns):
            suggestions.append("Add a simple 'hello world' pattern for beginners")
    
    if scores.documentation_completeness < 0.7:
        suggestions.append("Ensure all modules have reference documentation")
    
    return suggestions
```

## Example Quality Report

```yaml
quality_report:
  overall_score: 0.85
  scores:
    trigger_coverage: 0.90
    pattern_usefulness: 0.80
    beginner_friendliness: 0.75
    documentation_completeness: 0.85
    navigation_clarity: 0.90
    graceful_degradation: 0.80
  suggestions:
    - "Add pattern for 'how to handle resize events'"
    - "Consider adding conceptual synonyms for broader trigger coverage"
    - "Add a simple 'hello world' pattern for beginners"
```

## Manual Review Triggers

Always flag for manual review if:
- Overall score < 0.7 or any criterion < 0.5
- Generated patterns > 10 per module (overwhelming) or < 3 per module (insufficient)
- Triggers > 40 per module (too many) or < 8 per module (too few)
- Empty patterns list or no triggers for a module
- SKILL.md exceeds 600 lines
- Reference files missing metadata headers
- No source links in curated references
