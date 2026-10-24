# Subagent & Task Delivery Contract

> [!IMPORTANT]
> **Model-Exclusive IPC Contract**: This format is strictly for headless subagents and autonomous tasks. Never emit these headings (`## Route`, `## Issues`, `## Artifacts`) to the human user.

Subagents, lane workers, and autonomous tasks must format output using standard headings:

- **`## Summary`**: Carmack-style delivery of the technical approach, architectural rationale, and state tradeoffs in 100 words or fewer.
- **`## Artifacts`**: List absolute paths for modified or created files (`<path> (<spec|diff|report|eval|pr>)`). Never paste full file contents.
- **`## Evidence`**: Report deterministic verification commands and outcomes (`<check_name>: PASS|FAIL (<cmd>)`).
- **`## Route`**: Specify next action: `continue`, `remediate`, or `blocked`.
- **`## Issues`**: Report issues as `[P1|P2|P3] <file>:<line> — <Invariant>: <Defect>. Remediation: <Fix>`. State `None` if clean.
- **`## Suggestions`**: Share optional non-blocking observations on tooling or environment friction (at most two items).

Deep reference, JSON schema, and severity taxonomy: `skills/ai-engineering-expert/subskills/subagent-engineering/references/inter-agent-message-contract.md`.
