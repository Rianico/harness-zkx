# Plain Language for Human-Facing Artifacts

A human-facing artifact is anything a human evaluates to make a judgment. Examples include PR descriptions, changelogs, issues, RFCs, proposals, ADRs, and review comments.

In Computer Science, we never use the rigid ~900-word aerospace dictionary from literal ASD-STE100. Doing so would break software engineering by banning fundamental terms like `parse`, `serialize`, `cache`, `timeout`, `spawn`, `dispatch`, and `mutex`.

Instead, both modes in this harness are **STE Flavors** adapted for computing, separated across two dials:
- **Lexical Dial (Vocabulary):** Rich technical vocabulary and verbatim code tokens are always permitted. We only ban subjective marketing adjectives (`robust`, `seamless`, `cutting-edge`) and ambiguous soft phrasal verbs (`spin up`, `touch base`).
- **Structural Dial (Grammar):**
  - **Human-Targeted STE Flavor** (this file): Used for human-judged decision artifacts. Employs active voice with named actors, sentence length ≤25 words, nominalization removal, 60-second scannability, and evidence over adjectives.
  - **Machine-Targeted STE Flavor**: Used for tool/function descriptions, error messages, system prompts, inter-agent instructions (`herdr`), and procedural runbooks (`SKILL.md`, `AGENTS.md`). Employs terse second-person imperative, 1 action per sentence, front-loaded guards, and sentence length ≤20 words. See [../../writing-for-agents/references/agent-command-grammar.md](../../writing-for-agents/references/agent-command-grammar.md).

Adapted from `warpdotdev/common-skills@b811c24` (MIT, © Denver Technologies, Inc.): `write-pr-description/references/plain-language.md` + `write-feature-docs` style rules.

> [!note] Authoritative Provenance: ASD-STE100 Issue 9 (published January 15, 2025).
> - **Adopted Structural Rules:**
>   - Rule 1.1: plain words.
>   - Rule 2.1: multi-word nouns ≤3 words.
>   - Rule 3.7: smothered verbs and nominalizations.
>   - Rule 5.1: procedural sentences ≤20 words.
>   - Section 6: descriptive sentences ≤25 words.
>   - Rule 8.1: semicolon ban.
> - **Intentional CS Adaptations / Deviations:**
>   1. **Dictionary Decoupling:** Replaced Part 2 aerospace dictionary with CS Ubiquitous Language and insulated code tokens.
>   2. **Epistemic Modality:** Preserved `MUST`, `SHOULD`, `MAY`, and `could` for system certainty and confidence bounds. Issue 9 Rule 3.4 bans auxiliary verbs, but computing requires them.
>   3. **Marketing Fluff Extension:** Added empirical replacements for ungrounded superlatives (`robust`, `seamless`).

## Which part of this file you need

- Drafting an issue, RFC, PR, or ADR: [The rules](#the-rules).
- Mode selection: [Timing arbitration table](#timing-arbitration-table).
- Identifying the responsible actor: [Active voice with named actors](#active-voice-with-named-actors).
- Removing smothered verbs: [Nominalization removal](#nominalization-removal).
- Grounding claims in verification: [Evidence over adjectives](#evidence-over-adjectives).
- Preserving normative standards: [RFC keyword preservation](#rfc-keyword-preservation).
- Designing for maintainer triage: [60-second scannability](#60-second-scannability).
- Verbatim technical terms: [What is exempt](#what-is-exempt).
- Tightening vague drafts: [Two rewrites](#two-rewrites).
- Cutting padding and fluff: [Words that add nothing](#words-that-add-nothing).
- Writing published docs: [Shape rules for published docs](#shape-rules-for-published-docs).

## Timing arbitration table

| Mode / Dimension | Scope / Artifacts | Key Rules & Sentence Length |
| --- | --- | --- |
| **Machine-Targeted STE Flavor** (Strict Structure) | Tool/function descriptions, error messages, system prompts, inter-agent instructions (`herdr`), procedural runbooks (`SKILL.md` body, `AGENTS.md`) | ≤20 words/instruction, 1 action/sentence, imperative, front-loaded guards, zero synonym rotation, token insulation |
| **Human-Targeted STE Flavor** (Narrative Mode) | Human-primary decision artifacts (PR descriptions, ADRs, RFCs, GitHub issues, CHANGELOGs, review comments) | ≤25 words/sentence, active voice with named actors, nominalization removal, evidence over adjectives, 60s scannability |
| **Hybrid / Gray Areas** | Architecture reviews, complex diagnostics, proposals with embedded action blocks | Human-Targeted STE for exposition/rationale; Machine-Targeted STE for normative contracts, invariants, action blocks |
| **Lexical vs. Structural Split** | Vocabulary rules vs. Grammar rules | Vocabulary: Rich CS terms allowed; fluff and soft phrasals banned (never use aerospace ~900-word dictionary). Grammar: ≤20 words for procedural instructions vs. ≤25 words for descriptive prose |

## Active voice with named actors

Passive voice conceals who acts. In engineering prose, callers, runtimes, permissions, and validation boundaries require explicit actors:

- **Bad:** `The configuration file is validated before workers are initialized.`
- **Good:** `The CLI validates the configuration file before the supervisor spawns workers.`
- **Bad:** `Stale sessions were dropped.`
- **Good:** `The session manager drops expired sessions after 15 minutes of inactivity.`

Name the component, function, process, or user that takes the action.

## Nominalization removal

Nominalizations (smothered verbs) replace direct verbs with abstract nouns coupled with generic verbs (`perform`, `conduct`, `carry out`, `make`):

| Smothered Verb | Direct Verb |
| -------------- | ----------- |
| `perform a validation` | `validate` |
| `conduct an assessment` | `assess` |
| `carry out the deployment` | `deploy` |
| `perform an inspection` | `inspect` |
| `make a determination` | `determine` |
| `conduct a verification` | `verify` |
| `carry out a migration` | `migrate` |

Direct verbs make sentences shorter, clearer, and faster to parse.

## Evidence over adjectives

Cut marketing adjectives and subjective intensifiers (`robust`, `seamless`, `cutting-edge`, `blazing-fast`, `state-of-the-art`, `game-changing`, `effortless`). Replace them with measurable data, outputs, or concrete guarantees:

- **Bad:** `The service provides a robust and seamless failover mechanism.`
- **Good:** `When the primary replica fails health checks for 3 consecutive intervals, the router switches traffic to the standby replica within 500ms.`
- **Bad:** `Our cutting-edge parser is blazing-fast.`
- **Good:** `The SIMD-accelerated parser processes 1.2 GB/s on an M2 Max core.`

A single verified command output, test count, or log snippet carries more weight than subjective praise.

## RFC keyword preservation

Preserve standard RFC 2119 and RFC 8174 keywords: `MUST`, `MUST NOT`, `REQUIRED`, `SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`, `RECOMMENDED`, `MAY`, `OPTIONAL`.

- Write normative keywords in uppercase to distinguish requirements from informal advice.
- Do not soften `MUST` to `should` or "please make sure to".
- Do not inflate `MAY` to `MUST`. Keep optional capabilities precise.

## 60-second scannability

Maintainers triage under high context-switching pressure. Structure prose so a maintainer understands problem, evidence, scope, and requested decision in 60 seconds:

- **Front-load the core point:** State the observed problem and proposed decision in the first paragraph.
- **Short sentences:** Keep sentences to ≤25 words. Long sentences usually join two distinct ideas with a comma.
- **Short paragraphs:** Limit paragraphs to ≤5-6 sentences. Split longer blocks into vertical lists.
- **Scannable formatting:** Use bold anchors, tables for multi-attribute comparisons, and fenced blocks for commands.

## The rules

| Rule | Failure it prevents |
| ---- | ------------------- |
| Active voice, name the actor | Passive hides who acts — the critical detail in security, validation, and concurrency |
| One topic per sentence | Clamping fact, consequence, and caveat into one sentence causes misinterpretation |
| Sentence ≤ ~25 words | Long sentences force re-reading and conceal edge cases |
| Remove nominalizations | Smothered verbs add syllable drag and weaken actionable clarity |
| Evidence over adjectives | Subjective intensifiers destroy credibility; concrete metrics provide proof |
| Simple tenses | Complex tenses (`had been rejecting`) obscure current versus historical state |
| Keep articles and connecting words | Telegram style (`Fix case where config nil`) causes syntax parsing errors |
| One term per concept | Synonym rotation (`tenant` → `account` → `workspace`) makes readers search for phantom differences |
| ≤ 3 stacked nouns | Multi-noun chains (`retry backoff configuration override`) force syntactic guesswork |
| Vertical list at 3+ conditions or steps | Multi-condition prose hides failure branches |
| Prefer the specific verb | `handles`, `manages`, `supports` conceal the actual operational mechanism |
| Paragraph ≤ ~6 sentences | Dense walls of text get skimmed and critical warnings get skipped |

## What is exempt

Technical names stay verbatim. Never paraphrase an identifier to satisfy a word rule — `nil` is `nil`, not "an empty value":

- Code identifiers, type and field names, file paths: `FactoryConfig`, `spawn_server_impl`, `logic/factories.go`.
- Command lines, flags, and arguments: `uv run pytest -k test_ste100`.
- Established repository and domain terms: merge queue, feature flag, migration, presubmit, one-way door.
- Product, protocol, and service names: `PostgreSQL`, `HTTP/2`, `Docker`.

## Two rewrites

**Passive, smothered, and vague**

> `An update was conducted on the cache layer so that stale entries can be handled in a robust and seamless manner.`

**Active, direct, and specific**

> Each cache entry records the version of the pricing table used during build. The lookup compares that version against the current schema version and invalidates the entry when versions differ.

**Intent stated as result**

> `Added tests to make sure rollback is effortless.`

**Result stated as result**

> `migrate down` drops the index and removes all schema residue. The integration test verifies this against a local PostgreSQL 16 container.

## Words that add nothing

Cut filler terms unless backed by concrete data:

- **Banned adjectives:** `comprehensive`, `robust`, `properly`, `various`, `seamless`, `cutting-edge`, `effortless`, `blazing-fast`, `state-of-the-art`, `game-changing`.
- **Banned soft phrasal verbs:** `spin up`, `kick off`, `dive into`, `reach out`, `circle back`, `touch base`.
- **Conversational padding:** `basically`, `essentially`, `in order to`, `it should be noted that`, `a number of`, `should work`.
- **Diminishing qualifiers:** `simply`, `just`. They mislead readers about difficulty and sound dismissive.

## Shape rules for published docs

- **Headings:** sentence case. Proper feature names keep their capitalization — `## Agent Mode settings`, not `## Agent mode settings`.
- **Lists:** `**Term** - Description`. Never a colon after the bold term.
- **UI elements:** bold buttons, links, and menu items — `Click **Save**`. Bold every segment of a settings path, leave `>` plain — `**Settings** > **AI** > **Knowledge**`.
- **Tense:** present for how things work, imperative for instructions.
- **Description field:** a standalone snippet — user benefit first, then the feature name and key terms. `Environments ensure your cloud agents run with a consistent toolchain. Learn when to use them and how to configure them.` — not `This page describes environments.`
- **Unverified leftovers:** mark them (`[UNVERIFIED]`, `[TODO: <owner> — …]`) instead of smoothing them into confident prose. A placeholder the reader can see beats a sentence they will trust and act on.
