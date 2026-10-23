---
name: writing-for-humans
description: >-
  Writing reference for human-judged GitHub issues, discussions, RFCs, and proposals — problem-first framing, evidence grounding, scannability, explicit asks. Use when drafting or reviewing an issue, RFC, or proposal, fixing vague or over-long drafts, triage fatigue, or stalled proposals.
metadata:
  managed-by: ai-engineering-expert
---

# Writing for Humans

Authoritative guide for documents a human maintainer triages: RFCs, GitHub issues, discussions, proposals, and PR descriptions.

**Completion criterion:** a reviewer answers yes, no, or later after one pass, with no re-reading.

## Sibling Boundaries

- Sentence-level grammar, STE-100 vocabulary, and banned fluff live in [plain-language.md](../../references/plain-language.md).
- Agent-consumed runbooks and skills belong to [writing-for-agents](../writing-for-agents/SKILL.md).

## 1. The Reading Bottleneck

Reading is the bottleneck. Long prose defers decisions and hides warnings. Climb one rung for each added relationship:

1. **Prose:** Write controlled technical English at 80% ASD-STE100 strength. Use active voice and direct verbs.
2. **Tables:** Compare three or more items: trade-offs, schemas, parameters.
3. **Visual shapes:** Switch when the prose explaining one relationship exceeds four sentences. Pick the smallest shape that answers the question:
   - Algorithm → pseudocode.
   - Control flow → call tree.
   - UI boundaries → component tree.
   - Refactor → shallow file tree.
   - Interaction or data flow → Mermaid sequence diagram.
   - Exact mutation → targeted unified diff.
   Show a change by diffing the shape itself. Diff a call tree, component tree, file tree, or state as you diff code:

   ```diff
   submitForm
     createSession
       persistPrompt
   +    expandSkillMention
       launchAgent
   ```

   Show the whole shape when most of it is new. Show it when omitted context hides ownership or order, or when the reviewer needs a copyable target.
4. **Interactive HTML:** Use this when the reviewer must explore multi-variable states. Match the product's colors, type, spacing, and components. Use real labels and data. Support desktop and mobile. Open the file for the reviewer.

Place each visual next to the short text it supports. Keep only the calls, files, props, states, and boundaries the decision needs. Use one shape, sometimes several, rarely all.

Replace the prose that a visual covers. Do not restate a diagram in sentences.

## 2. Decision-First Framing

Name the requested decision in one sentence before drafting. Delete every sentence that does not advance it.

- **Ask twice:** Open with the decision. Close with the decision.
- **Prior art first:** Cite existing solutions, or state why each one fails. Maintainers reject what already exists.
- **Cheapest test first:** Bound the proposal with non-goals. Scope the cheapest-to-test failure mode first.
- **Request, do not presume:** Offer a minimal pilot PR. Never assume unassigned ownership.
- **Demonstrated capabilities only:** Rely on interfaces the codebase already has. Flag novel hooks as open questions with a recommended default.

## 3. Evidence and Honesty

- **Observed versus conjectured:** Tag every claim. Back observed facts with run counts, logs, or links.
- **One label per concept:** Tag unconfirmed assumptions `[UNVERIFIED]`. Do not also call them hypotheses.
- **Isolate root causes:** Split independent failure modes into separate proposals.
- **Inflation costs the whole post:** One caught exaggeration discounts every other claim.

## 4. Proposal Anatomy

1. **Title and Summary:** Name the concrete proposal (`RFC: <Actionable Title>`). Summarize problem, scope, and decision requested.
2. **Problem and Evidence:** Lead with observed friction. Use reproduction commands or log snippets.
3. **Scoped Visual Solution:** Pair short text with the smallest clarifying artifact.
4. **Non-Goals:** List excluded paths.
5. **Call to Action:** State the exact decision or feedback required.

## 5. Ship Gate

Revise until all four checks pass:

1. A reviewer reaches the decision in one pass.
2. Prior art appears, or the draft explains why it does not apply.
3. Distinct failure modes are separate proposals, cheapest test first.
4. The prose passes [plain-language.md](../../references/plain-language.md).

## 6. Failure Modes

- **Solution-first jump** → establish the friction first.
- **Multi-problem mush** → split the mechanisms.
- **Ghost evidence** → cite a verified run, or drop the claim.
- **Architectural presumption** → use demonstrated APIs only.
- **Triage dump** → recommend a concrete default for each open question.

## Harness Wiring

- Deterministic: `uv run $SKILL_DIR/../skill-authoring/scripts/ste100.py <file>` gates sentence length and banned words.
- Semantic: dispatch a Skeptic subagent to find unverified claims, presumed architecture, and missing non-goals.
