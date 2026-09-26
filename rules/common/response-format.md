# Subagent & Task Delivery Contract

Subagents, lane workers, and autonomous tasks must format output using standard headings:

- **`## Summary`**: Carmack-style technical approach, architectural rationale, state tradeoffs (≤100 words).
- **`## Artifacts`**: Absolute paths to touched/created files (`<path> (<spec|diff|report|eval|pr>)`). Never paste file bodies.
- **`## Evidence`**: Deterministic verification command results (`<check_name>: PASS|FAIL (<cmd>)`).
- **`## Route`**: `continue` | `remediate` | `blocked`.
- **`## Issues`**: `[P1|P2|P3] <file>:<line> — <Invariant>: <Defect>. Remediation: <Fix>`. (Empty or "None" if clean).
- **`## Suggestions`**: Non-blocking observations on tooling/environment friction (≤2 items, optional).

Deep reference, JSON schema, and severity taxonomy: `skills/ai-engineering-expert/references/resp-format.md`.
