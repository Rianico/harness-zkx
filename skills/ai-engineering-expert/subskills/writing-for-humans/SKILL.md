---
name: writing-for-humans
description: >-
  Writing reference for human-judged GitHub issues, discussions, RFCs, and proposals — problem-first framing, evidence grounding, scannability, explicit asks. Use when drafting or reviewing an issue, RFC, or proposal, fixing vague or over-long drafts, triage fatigue, or stalled proposals.
metadata:
  managed-by: ai-engineering-expert
---

# Writing for Humans

Managed sub-skill of `ai-engineering-expert`. Load when `$domain` is `writing-for-humans` or when any
`ai-engineering-expert` task drafts, reviews, or revises a document a human maintainer triages — a GitHub
issue, discussion post, RFC, or proposal. This is the sibling of `writing-for-agents`: same discipline of
goal-first structure, inverted voice — you are persuading a busy volunteer, not instructing a runtime.
For sentence-level plain language rules (STE-100, sentence length, active voice), see sibling reference
[`writing-for-agents/references/human-facing-prose.md`](../writing-for-agents/references/human-facing-prose.md).

This skill teaches how to **shape a proposal so a maintainer can decide on it in one read** — not how to
run the project yourself. You are the proposer; a maintainer with fragmented attention is the reader.
Every choice below serves that handoff.

## Start from the decision, not the idea

Derive one sentence naming **the decision you want** before drafting — e.g. "maintainer agrees stale-read
recovery is worth addressing" — then let that sentence decide what the document keeps and trims.
Everything below only earns its keep against that decision.

- **Name it before you draft.** Write the decision down first. If a section doesn't move the maintainer
  toward it, delete the section.
- **State the ask twice.** Once in the title or TL;DR (what kind of response: directional feedback, a
  yes/no, a review), once at the end (the explicit decision or next step requested). Never mention what the
  proposer does next unless the user clearly intended to volunteer implementation.
- **Separate what you verified from what you suspect.** Mark every claim as observed (with run counts,
  logs, links) or conjectured. A maintainer who catches one inflated claim discounts the whole post.

## Principles

1. **Problem before mechanism.** Establish the friction is real and worth fixing before describing any
   implementation. No maintainer can evaluate a solution to an unagreed problem.
2. **Evidence over adjectives.** Replace "very common", "arguably the worst", "clearly" with counts, logs,
   or links. A single concrete transcript snippet carries more evidentiary weight than paragraphs of assertion.
3. **Isolate distinct root causes.** Split separate failure modes into distinct proposals. Blending external
   concurrency with self-inflicted tool errors inflates perceived complexity and stalls review on the hardest piece.
4. **No presumed machinery.** Never specify hooks, interfaces, or observability the project may not have
   (e.g. intercepting an agent's individual tool calls when adapters treat CLIs as black boxes). Propose
   within demonstrated capabilities; flag the rest as open questions, not assumptions.
5. **Bound with non-goals.** Name what is explicitly out of scope (e.g. no asynchronous timing, no new infrastructure).
   Non-goals relieve the maintainer's fear of unbounded maintenance and flaky tests.
6. **Scope the ask without presuming ownership.** State clearly what decision, feedback, or review is needed
   from maintainers. Never commit the proposer to implementation or mention what the proposer does next unless
   the user clearly intended to volunteer it. If the user explicitly intends to build it, state that offer
   concretely (e.g. a minimal pilot PR or repro script).
7. **Design for rapid scanning (the 60-second heuristic).** Put the proposal in the title, summarize problem,
   scope, and ask in the TL;DR, write descriptive section headers, and collapse long traces behind details folds.
   Maintainers triage in bursts; scannability decides acted-upon vs deferred.

## Proposal anatomy (the 5-part shape)

Structure every proposal, RFC, or issue so a maintainer can evaluate it progressively:

1. **Title & TL;DR (0–15s):** State the concrete proposal in the title (`RFC: <Actionable Title>`). Open with a
   2–3 sentence summary covering the observed problem, proposed scope, and the exact decision requested.
2. **Problem & evidence (15–30s):** Name the friction before any solution. Back claims with observed run logs,
   failure rates, or reproduction traces.
3. **Scoped proposal (30–45s):** Propose the minimal viable increment (e.g. a pilot task family or narrow prototype)
   rather than an open-ended framework.
4. **Explicit non-goals:** List what is deliberately out of scope to preempt maintainer maintenance anxiety.
5. **Call to action & requested decision (45–60s):** End with the explicit decision or feedback requested from
   maintainers (e.g. roadmap alignment, directional go/no-go). Only state proposer-led next steps if the user
   clearly intended to volunteer implementation.

## Pre-submit checklist

Answer every question honestly; a single "no" means revise before filing.

1. Does the title name the concrete proposal or problem, not just a topic area?
2. Is the problem stated and justified before any mechanism appears?
3. Is each factual claim backed by a count, log, or link — with zero intensifiers doing the work of evidence?
4. Are distinct failure modes separated, with the cheapest-to-test one scoped first?
5. Does the proposal avoid assuming project internals that may not exist?
6. Are non-goals stated explicitly?
7. Is the call to action unambiguous about the requested decision or feedback?
8. Does the draft avoid mentioning what the proposer does next unless the user clearly intended to volunteer it?
9. Can a maintainer grasp problem, scope, and ask in a rapid skim (~60 seconds)?

## Anti-patterns (illustrative pairs)

- **Solution-first jump.** Bad (illustrative): opening with hook mechanics ("a seeded hook mutates the file after the
  first read…") before establishing the blind spot. Good (illustrative): one paragraph on what current tasks cannot
  measure, then the proposed mechanism.
- **Multi-problem mush.** Bad (illustrative): "two agents share a tree, a formatter runs, and the agent's own `sed`
  invalidates its reads" as one undifferentiated complaint. Good (illustrative): isolate the mechanisms separately and
  scope the proposal to the single one testable without new infrastructure.
- **Ghost evidence.** Bad (illustrative): "agents very commonly clobber their own changes." Good (illustrative): "across
  4 observation runs on 226 tasks, 14% of edit failures traced to shell-invalidated offsets (links to run logs)" — cite
  verified runs, or omit the claim if unmeasured.
- **Architectural presumption.** Bad (illustrative): "the hook appends lines after the agent's first read" (assumes
  unsupported per-tool-call interception). Good (illustrative): "a fixture-level prompt step that shifts lines before
  the edit — no harness instrumentation required."
- **Triage dump.** Bad (illustrative): closing with open questions that transfer design labor onto maintainers ("which
  hook fits best?", "warn or stay silent?"). Good (illustrative): recommend concrete defaults for each question, state
  the exact maintainer decision needed ("Maintainers: does this dimension belong on the roadmap?"), and never commit
  the proposer to implementation unless the user clearly intended to volunteer.

## Harness Wiring

- **When to load:** `ai-engineering-expert` loads this sub-skill when `$domain` is `writing-for-humans` or when any
  workflow drafts, reviews, or revises human-facing issues, RFCs, or discussion posts.
- **Sibling boundary:** Use `writing-for-agents` for agent-consumed instructions (`SKILL.md`, `AGENTS.md`). For
  sentence-level plain language rules (STE-100, sentence length, active voice), consult
  [`writing-for-agents/references/human-facing-prose.md`](../writing-for-agents/references/human-facing-prose.md).
- **Verification:** Validate frontmatter deterministically with
  `uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py context-check`. Review drafts semantically via a
  Skeptic subagent checking for unverified assertions, presumed architecture, and missing non-goals.

## Further reading

- Simon Tatham, "How to Report Bugs Effectively" — ground reports in verified fact, kill back-and-forth ambiguity.
- Nolan Lawson, "What it feels like to be an open-source maintainer" — triage fatigue; unfocused proposals get deprioritized.
- Brett Cannon, "Setting expectations for open source participation" — state intent, own the work.
- GitHub Open Source Guides, "How to Contribute" — context before specifics, align with repo workflow.
- Phil Calçado, "A Structured RFC Process" — decouple problem from solution, explicit non-goals, one owner.
