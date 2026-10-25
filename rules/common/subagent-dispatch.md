# Subagent Dispatch

Evaluate every task against these gates before execution. Keep implementation work, high-churn research, and adversarial review in subagents; keep trivial and user-facing work in-band.

## Dispatch a Subagent When

- **High churn:** You expect over 3,000 raw output tokens from research, scans, or log triage.
- **Speculative drafting:** Candidate implementations and prototypes stay in the scratchpad.
- **Adversarial review:** The reviewer needs a clean room and diff-only context.
- **Parallel seams:** Independent tasks touch separate architectural seams.
- **Least privilege:** The task needs a restricted action space.

## Keep In-Band When

- **Trivial work:** The task touches under 100 lines or runs single commands.
- **User alignment:** Probing intent stays with you. Subagents never interrogate the user.
- **Shared mutable state:** Concurrent edits without clean seams break invariants.
- **Depth limit:** You are already inside a subagent. Depth stays at 1.

## Configuration

- **Fresh context by default:** Pass a brief and absolute file pointers. Never resume a stale subagent to iterate on rejected work.
- **Scope the action space:** Grant researchers and reviewers inspection and search only. Grant implementers mutation, patch, and verification tools. Strip subagent dispatch tools.
- **Require the return envelope:** Subagents answer through `response-format.md`.

Deep methodology: `skills/ai-engineering-expert/subskills/subagent-engineering/SKILL.md`.
