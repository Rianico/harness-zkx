---
name: writing-for-humans
description: >-
  Writing reference for human-judged GitHub issues, discussions, RFCs, and proposals — problem-first framing, evidence grounding, scannability, explicit asks. Use when drafting or reviewing an issue, RFC, or proposal, fixing vague or over-long drafts, triage fatigue, or stalled proposals.
metadata:
  managed-by: ai-engineering-expert
---

# Writing for Humans

Managed sub-skill of `ai-engineering-expert`. Load when `$domain` is `writing-for-humans`. Also load when an
`ai-engineering-expert` task drafts, reviews, or revises a document a human maintainer triages. Examples are a
GitHub issue, discussion post, RFC, or proposal.

This skill teaches how to **shape a proposal so a maintainer can decide on it in one read**. You are the
proposer. A busy maintainer with fragmented attention is the reader: you persuade, you do not instruct.

**Sibling boundary.** Sentence-level rules (active voice, sentence length, banned words, scannability) live in
[plain-language.md](../../references/plain-language.md). Agent-consumed instructions (`SKILL.md`, `AGENTS.md`)
belong to [writing-for-agents](../writing-for-agents/SKILL.md).

## Start from the decision, not the idea

Derive one sentence naming **the decision you want** before drafting — e.g. "maintainer agrees stale-read
recovery is worth addressing". If a section does not move the maintainer toward that decision, delete it.

- **State the ask twice.** Once in the title or TL;DR (what kind of response: directional feedback, a yes/no,
  a review), once at the end (the explicit decision or next step requested).
- **Request a decision without presuming ownership.** Mention proposer-led next steps only if the user
  clearly intended to volunteer implementation. Then state the offer concretely (e.g. a minimal pilot PR or
  repro script).
- **Separate what you verified from what you suspect.** Mark every claim as observed (run counts, logs,
  links) or conjectured. A maintainer who catches one inflated claim discounts the whole post.
- **Isolate distinct root causes.** Split separate failure modes into distinct proposals. Blending external
  concurrency with self-inflicted tool errors inflates perceived complexity and stalls review on the hardest piece.
- **Propose within demonstrated capabilities.** Specify only hooks, interfaces, or observability the project
  has (e.g. adapters may treat CLIs as black boxes, so per-tool-call interception may not exist). Flag the
  rest as open questions.

## Proposal anatomy (the 5-part shape)

Structure every proposal, RFC, or issue so a maintainer can evaluate it progressively within 60 seconds:

1. **Title & TL;DR (0–15s):** Name the concrete proposal in the title (`RFC: <Actionable Title>`). Open with a
   2–3 sentence summary of the observed problem, proposed scope, and exact decision requested.
2. **Problem & evidence (15–30s):** Establish the friction before any mechanism. No maintainer can evaluate
   a solution to an unagreed problem. Back it with run logs, failure rates, or reproduction traces.
3. **Scoped proposal (30–45s):** Propose the minimal viable increment (e.g. a pilot task family or narrow
   prototype), not an open-ended framework.
4. **Explicit non-goals:** List what is out of scope (e.g. no asynchronous timing, no new infrastructure).
   Non-goals relieve the fear of unbounded maintenance and flaky tests.
5. **Call to action (45–60s):** End with the explicit decision or feedback requested (e.g. roadmap alignment,
   directional go/no-go).

## Pre-submit checklist

A single "no" means revise before filing.

1. Does the title name the concrete proposal or problem, not just a topic area?
2. Does the problem appear, with evidence, before any mechanism?
3. Is every factual claim marked observed (count, log, link) or conjectured?
4. Are distinct failure modes separated, with the cheapest-to-test one scoped first?
5. Does the proposal assume only project internals that demonstrably exist?
6. Are non-goals stated explicitly?
7. Is the ask stated in both the TL;DR and the closing, naming the requested decision?
8. Is proposer-led follow-up absent, unless the user clearly intended to volunteer it?
9. Can a maintainer grasp problem, scope, and ask in ~60 seconds?
10. Does the prose pass [plain-language.md](../../references/plain-language.md)?

## Anti-patterns

All pairs are illustrative.

- **Solution-first jump.** Bad: opening with hook mechanics ("a seeded hook mutates the file after the first
  read…") before establishing the blind spot. Good: one paragraph on what current tasks cannot measure, then
  the proposed mechanism.
- **Multi-problem mush.** Bad: `two agents share a tree, a formatter runs, and the agent's own sed invalidates
  its reads` as one complaint. Good: isolate the mechanisms. Scope the proposal to the one testable without new
  infrastructure.
- **Ghost evidence.** Bad: `agents very commonly clobber their own changes`. Good: `across 4 observation runs
  on 226 tasks, 14% of edit failures traced to shell-invalidated offsets` (with links to run logs). Cite
  verified runs, or omit the claim if unmeasured.
- **Architectural presumption.** Bad: "the hook appends lines after the agent's first read" (assumes
  unsupported per-tool-call interception). Good: "a fixture-level prompt step that shifts lines before the
  edit — no harness instrumentation required."
- **Triage dump.** Bad: closing with open questions that transfer design labor onto maintainers ("which hook
  fits best?", "warn or stay silent?"). Good: recommend a concrete default for each question and state the
  exact decision needed ("Maintainers: does this dimension belong on the roadmap?").

## Harness Wiring

- **Verification:** Validate frontmatter deterministically with
  `uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py context-check`. Review drafts semantically via a
  Skeptic subagent checking for unverified assertions, presumed architecture, and missing non-goals.

## Further reading

- Simon Tatham, "How to Report Bugs Effectively" — ground reports in verified fact, kill back-and-forth ambiguity.
- Nolan Lawson, "What it feels like to be an open-source maintainer" — triage fatigue makes maintainers deprioritize unfocused proposals.
- Brett Cannon, "Setting expectations for open source participation" — state intent, own the work.
- GitHub Open Source Guides, "How to Contribute" — context before specifics, align with repo workflow.
- Phil Calçado, "A Structured RFC Process" — decouple problem from solution, explicit non-goals, one owner.
