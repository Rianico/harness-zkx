# Phase 3 Test Fixtures - Expected Outputs

This directory contains expected outputs from the observer agent for each pattern type.

## Schema

All expected outputs follow the agent result schema:

```json
{
  "instincts_created": [
    {
      "id": "string",
      "trigger": "string",
      "confidence": 0.0-1.0,
      "domain": "workflow|debugging|...",
      "action": "string",
      "evidence": [
        {"session_id": "string", "description": "string"}
      ]
    }
  ],
  "instincts_updated": [
    {"id": "string", "new_confidence": 0.0-1.0}
  ],
  "promotions": [
    {"id": "string", "reason": "string"}
  ],
  "processed_count": 0,
  "cursor_position": 0
}
```

## Files

| File | Pattern Type | Initial Confidence |
|------|--------------|-------------------|
| user_correction.json | User rejects suggestion, takes different action | 0.5 |
| repeated_workflow.json | Same tool sequence repeated 3+ times | 0.7 |
| error_resolution.json | Tool fails, modified approach succeeds | 0.6 |
