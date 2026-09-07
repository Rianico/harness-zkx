# Philosophy — Builder Mapping

Agent-facing prose never uses framework labels. This file is the builder-facing map so maintainers can trace the moves below to their prior names in `ai-engineering-expert` and git history. **Do not cite these labels in documents the model reads at run time** (SKILL.md, AGENTS.md, CLAUDE.md). Teach the move, not the name.

| Move the model does | Prior label | What it means in practice |
| --- | --- | --- |
| **Start from intent, name the goal** — derive a one-sentence goal from intent/artifacts/chat and let it decide what stays, what goes, and how the doc is ordered. | Previously **GDD** (Goal-Driven Development) | Goal is the review bar. If deleting a section leaves the goal intact, delete it. `handoff/SKILL.md` demonstrates by opening with Primary Goal before context. |
| **Pin behavior with concrete examples** — every branch/rule gets a before/after or given/when/then-shaped example; the example is the contract. | Previously **BDD** (Behavior-Driven Development) | Turns a creative guessing task into a translation task. A new agent can map each example to a file:line. |
| **Verify with fresh signals, not assertions** — lints, typechecks, tests, and other tool outputs are the authority; for qualitative fit use a skeptic second read. | Previously **EDD** (Eval-Driven / Environment-Driven Development) | Never trust "I did it" — trust the tool output that would go red if the claim were false. |

**How to use this file:** When you read older ADRs, issues, or parent `ai-engineering-expert/SKILL.md` that cite GDD/BDD/EDD, translate via this table. When you write new agent-facing prose, use the left column only.
