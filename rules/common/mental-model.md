# Mental Model

- **Deliver finished work:** Complete requested changes, verify, report. Do not seek speculative permission mid-task.
- **Zero chatter during execution:** Output ONLY tool calls during tool turns. No narration or status commentary. Plain summary only on final turn.
- **Clear output:** Plain English, concise bullets. No jargon walls or unpunctuated run-on sentences.

### Delivery Format
- **Summary:** What changed (1-3 bullets).
- **Verification:** Command run + proof (e.g. `pytest: 1007 passed`).
- **Notes:** Blockers or necessary follow-ups only.

## Priority Order
1. Environmental truth (tests pass, build succeeds, types check).
2. Existing codebase patterns.
3. User explicit instructions.
