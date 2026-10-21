---
name: writing-for-humans
description: >-
  Writing reference for human-judged GitHub issues, discussions, RFCs, and proposals — problem-first framing, evidence grounding, scannability, explicit asks. Use when drafting or reviewing an issue, RFC, or proposal, fixing vague or over-long drafts, triage fatigue, or stalled proposals.
metadata:
  managed-by: ai-engineering-expert
---

# Writing for Humans

Managed sub-skill of `ai-engineering-expert`. Load when `$domain` is `writing-for-humans`. Also load when an `ai-engineering-expert` task drafts, reviews, or revises a document a human maintainer triages. Examples are a GitHub issue, discussion post, RFC, or proposal.

This skill teaches how to **shape a proposal so a maintainer can decide on it in one read**. You are the proposer. A busy maintainer with fragmented attention is the reader: you persuade, you do not instruct.

**Sibling boundary.** Sentence-level rules live in [plain-language.md](../../references/plain-language.md). Agent-consumed instructions (`SKILL.md`, `AGENTS.md`) belong to [writing-for-agents](../writing-for-agents/SKILL.md).

## Start from the decision, not the idea

Derive one sentence naming **the decision you want** before drafting. If a section does not move the maintainer toward that decision, delete it.

- **State the ask twice.** Once in the title or summary, and once at the end. Name the exact decision or next step requested.
- **Request a decision without presuming ownership.** Mention proposer-led next steps only if the user clearly intended to volunteer implementation. State the offer concretely as a minimal pilot PR or repro script.
- **Separate what you verified from what you suspect.** Mark every claim as observed (run counts, logs, links) or conjectured. A maintainer who catches one inflated claim discounts the whole post.
- **Isolate distinct root causes.** Split separate failure modes into distinct proposals. Blending external concurrency with tool errors inflates perceived complexity and stalls review.
- **Propose within demonstrated capabilities.** Specify only hooks, interfaces, or observability the project demonstrably has. Flag the rest as open questions.

## Visual-First Proposal Anatomy

Structure proposals so a maintainer grasps the decision in one quick read. Follow visual-first principles: skip preamble and pick the smallest view that makes the point clear.

1. **Title & Summary**: Name the concrete proposal in the title (`RFC: <Actionable Title>`). Open with a brief summary of the observed problem, proposed scope, and exact decision requested.
2. **Problem & Evidence**: Establish the friction before any mechanism. No maintainer can evaluate a solution to an unagreed problem. Back it with run logs, reproduction traces, or failure rates.
3. **Scoped Visual Solution**: Pair short text with the smallest visual artifact that makes the mechanism clear:
   - File responsibility or refactor: shallow file tree
   - Runtime control flow: concise call tree
   - Component or data interactions: focused Mermaid sequence diagram
   - Code mutations: targeted unified diff
4. **Explicit Non-Goals**: List what is out of scope. Explicit non-goals relieve maintainer fears of unbounded scope or brittle maintenance.
5. **Call to Action**: End with the explicit decision or feedback requested.

## Pre-submit checklist

A single "no" means revise before filing.

1. Does the title name the concrete proposal or problem, not just a topic area?
2. Does the problem appear, with evidence, before any mechanism?
3. Does the proposal use a visual diagram or diff where prose explanations exceed four sentences?
4. Is every factual claim marked observed (count, log, link) or conjectured?
5. Are distinct failure modes separated, with the cheapest-to-test one scoped first?
6. Does the proposal assume only project internals that demonstrably exist?
7. Are non-goals stated explicitly?
8. Is the ask stated in both the summary and the closing?
9. Is proposer-led follow-up absent, unless the user clearly intended to volunteer it?
10. Can a maintainer grasp problem, scope, and ask in a single pass?
11. Does the prose pass [plain-language.md](../../references/plain-language.md)?

## Anti-patterns

- **Solution-first jump.** Opening with mechanics before establishing the blind spot. Establish the concrete friction first.
- **Multi-problem mush.** Combining multiple unrelated failure mechanisms into one complaint. Isolate the mechanisms into separate proposals.
- **Ghost evidence.** Making sweeping claims without verified data. Cite verified runs or omit the claim.
- **Architectural presumption.** Assuming unsupported internal hooks or interception capabilities. Propose within demonstrated APIs.
- **Triage dump.** Closing with open questions that transfer design labor onto maintainers. Recommend a concrete default for each question.

## Harness Wiring

- **Verification:** Validate frontmatter deterministically with `uv run $SKILL_DIR/../skill-authoring/scripts/validate-deps.py context-check`. Review drafts semantically via a Skeptic subagent checking for unverified assertions, presumed architecture, and missing non-goals.

## Further reading

- Simon Tatham, "How to Report Bugs Effectively" — ground reports in verified fact.
- Nolan Lawson, "What it feels like to be an open-source maintainer" — triage fatigue deprioritizes unfocused proposals.
- Brett Cannon, "Setting expectations for open source participation" — state intent and own the work.
- GitHub Open Source Guides, "How to Contribute" — align with repo workflow.
- Phil Calçado, "A Structured RFC Process" — decouple problem from solution with explicit non-goals.
