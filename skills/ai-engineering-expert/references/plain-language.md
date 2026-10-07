# Plain Language (Shared STE Rules)

Sentence-level rules shared by `writing-for-agents` and `writing-for-humans`. Every rule here applies to all prose the harness writes. The reader sets the structural strictness:

- **Human-Targeted STE Flavor** (Narrative Mode): human-judged artifacts. Examples include PR descriptions, CHANGELOGs, issues, RFCs, proposals, ADRs, and review comments. Apply this file.
- **Machine-Targeted STE Flavor** (Strict Structure): model-primary artifacts. Apply this file, then the stricter structure in [agent-command-grammar.md](../subskills/writing-for-agents/references/agent-command-grammar.md).

Adapted from `warpdotdev/common-skills@b811c24` (MIT, © Denver Technologies, Inc.): `write-pr-description/references/plain-language.md` + `write-feature-docs` style rules.

> [!note] Authoritative Provenance: ASD-STE100 Issue 9 (published January 15, 2025).
> - **Adopted Structural Rules:**
>   - Rule 1.1: plain words.
>   - Rule 2.1: multi-word nouns ≤3 words.
>   - Rule 3.7: smothered verbs and nominalizations.
>   - Rule 5.1: procedural sentences ≤20 words.
>   - Section 6: descriptive sentences ≤25 words.
>   - Rule 8.1: semicolon ban.
>   - Rule 8.5-8.7: count parentheticals, elements, and hyphenated words as one word.
> - **Enforcement status:** `ste100.py` enforces Rules 3.7, 5.1, and 8.1, plus the lexical bans, deterministically. Rule 2.1 (multi-word nouns) and the Section 6 descriptive rules stay review judgment calls. No reliable deterministic check exists for noun chains.
> - **Intentional CS Adaptations / Deviations:**
>   1. **Dictionary Decoupling:** Replaced Part 2 aerospace dictionary with CS Ubiquitous Language and insulated code tokens.
>   2. **Epistemic Modality:** Preserved `MUST`, `SHOULD`, `MAY`, and `could` for system certainty and confidence bounds. Issue 9 Rule 3.4 bans auxiliary verbs, but computing requires them.
>   3. **Marketing Fluff Extension:** Added empirical replacements for ungrounded superlatives (`robust`, `seamless`).

## Which part of this file you need

- Choosing a flavor: [Mode selection](#mode-selection).
- Drafting any artifact: [The rules](#the-rules).
- Identifying the responsible actor: [Active voice with named actors](#active-voice-with-named-actors).
- Removing smothered verbs: [Nominalization removal](#nominalization-removal).
- Grounding claims: [Evidence over adjectives](#evidence-over-adjectives).
- Domain consistency: [One term per concept](#one-term-per-concept).
- Requirement strength: [Normative keyword preservation](#normative-keyword-preservation).
- Designing for triage: [60-second scannability](#60-second-scannability).
- Verbatim technical terms: [What is exempt](#what-is-exempt).
- Preserving test assertions: [Rewriting pinned text](#rewriting-pinned-text).
- Tightening a vague draft: [A rewrite](#a-rewrite).
- Cutting padding and fluff: [Words that add nothing](#words-that-add-nothing).
- Writing published docs: [Shape rules for published docs](#shape-rules-for-published-docs).

## Mode selection

| Mode | Scope / Artifacts | Structural rules |
| --- | --- | --- |
| **Machine-Targeted STE Flavor** | Tool/function descriptions, error messages, system prompts, inter-agent instructions (`herdr`), procedural runbooks (`AGENTS.md`, procedural `SKILL.md` bodies) | This file, plus ≤20 words/instruction, 1 action/sentence, imperative, front-loaded guards, token insulation |
| **Human-Targeted STE Flavor** | PR descriptions, ADRs, RFCs, GitHub issues, CHANGELOGs, review comments, human-facing guidelines (such as `subskills/writing-for-humans`) | This file: ≤25 words/sentence, 60s scannability |
| **Hybrid / Gray Areas** | Architecture reviews, complex diagnostics, proposals with embedded action blocks | Human-Targeted STE for exposition and rationale. Machine-Targeted STE for normative contracts, invariants, and action blocks |

Both flavors share one **lexical dial**. Rich CS vocabulary and verbatim code tokens are always permitted. Never use the ~900-word aerospace dictionary from literal ASD-STE100. It bans fundamental terms like `parse`, `serialize`, `cache`, `timeout`, `spawn`, `dispatch`, and `mutex`. Ban only the fluff in [Words that add nothing](#words-that-add-nothing).

## The rules

| Rule | Failure it prevents |
| ---- | ------------------- |
| Active voice, name the actor | Passive hides who acts — the critical detail in security, validation, and concurrency |
| One topic per sentence | Clamping fact, consequence, and caveat into one sentence causes misinterpretation |
| Sentence ≤ ~25 words | Long sentences force re-reading and conceal edge cases. They usually join two ideas with a comma |
| Remove nominalizations | Smothered verbs add syllable drag and weaken actionable clarity |
| Evidence over adjectives | Subjective intensifiers destroy credibility; concrete metrics provide proof |
| Simple tenses | Complex tenses (`had been rejecting`) obscure current versus historical state |
| Keep articles and connecting words | Telegram style (`Fix case where config nil`) causes syntax parsing errors |
| One term per concept | Synonym rotation makes readers search for phantom differences |
| ≤ 3 stacked nouns | Multi-noun chains (`retry backoff configuration override`) force syntactic guesswork |
| Vertical list at 3+ conditions or steps | Multi-condition prose hides failure branches |
| Prefer the specific verb | `handles`, `manages`, `supports` conceal the actual operational mechanism |
| Paragraph ≤ ~6 sentences | Dense walls of text get skimmed and critical warnings get skipped |

## Active voice with named actors

Passive voice conceals who acts. Callers, runtimes, permissions, and validation boundaries need explicit actors. Name the component, function, process, or user that takes the action.

- **Bad:** `The configuration file is validated before workers are initialized.`
- **Good:** `The CLI validates the configuration file before the supervisor spawns workers.`
- **Bad:** `Stale sessions were dropped.`
- **Good:** `The session manager drops expired sessions after 15 minutes of inactivity.`

## Nominalization removal

Nominalizations (smothered verbs) pair an abstract noun with a generic verb (`perform`, `conduct`, `carry out`, `make`). Use the direct verb:

| Smothered Verb | Direct Verb |
| -------------- | ----------- |
| `perform a validation` | `validate` |
| `conduct an assessment` | `assess` |
| `carry out the deployment` | `deploy` |
| `perform an inspection` | `inspect` |
| `make a determination` | `determine` |
| `conduct a verification` | `verify` |
| `carry out a migration` | `migrate` |

## Evidence over adjectives

Replace marketing adjectives and intensifiers with measurable data, outputs, or concrete guarantees. One verified command output, test count, or log snippet outweighs paragraphs of assertion.

- **Bad:** `The service provides a robust and seamless failover mechanism.`
- **Good:** `When the primary replica fails health checks for 3 consecutive intervals, the router switches traffic to the standby replica within 500ms.`
- **Bad:** `Our cutting-edge parser is blazing-fast.`
- **Good:** `The SIMD-accelerated parser processes 1.2 GB/s on an M2 Max core.`

## One term per concept

Bind exactly one term to each domain concept across the whole document. Use the ubiquitous language from the project's domain model. Human readers search for phantom differences between rotated synonyms. Models do the same: they hunt for latent distinctions between `tenant`, `account`, and `organization`.

- **Bad:** `Initialize the repository. Inspect files in the codebase. Commit updates to the project.`
- **Good:** `Initialize the repository. Inspect files in the repository. Commit updates to the repository.`

## Normative keyword preservation

Preserve RFC 2119 and RFC 8174 keywords in uppercase. They separate requirements from informal advice and carry confidence bounds.

| Keyword | Role | Reader behavior |
| ------- | ---- | --------------- |
| `MUST`, `MUST NOT`, `REQUIRED`, `SHALL`, `SHALL NOT` | Hard invariant | Never violate. If compliance is impossible, halt and report |
| `SHOULD`, `SHOULD NOT`, `RECOMMENDED` | Strong default | Follow unless a specific, documented exception applies |
| `MAY`, `OPTIONAL`, `could` | Permitted choice or confidence bound | Explore when appropriate. Never treat as mandatory |

- Keep `MUST` at full strength. Softening it to `should` or "please make sure to" causes silent validation bypasses.
- Keep `MAY` optional. Inflating it to `MUST` forces brittle dead-ends at edge cases.
- Keep probabilistic qualifiers (`may fail under high concurrency`) so the reader plans for the uncertainty.

## 60-second scannability

A maintainer triaging under context-switching pressure must grasp problem, evidence, scope, and requested decision in 60 seconds:

- **Front-load the core point:** State the observed problem and proposed decision in the first paragraph.
- **Short paragraphs:** Split blocks longer than ~6 sentences into vertical lists.
- **Scannable formatting:** Use bold anchors, tables for multi-attribute comparisons, and fenced blocks for commands.

## What is exempt

Technical names stay verbatim. Never paraphrase an identifier to satisfy a word rule — `nil` is `nil`, not "an empty value":

- Code identifiers, type and field names, file paths: `FactoryConfig`, `spawn_server_impl`, `logic/factories.go`.
- Command lines, flags, and arguments: `uv run pytest -k test_ste100`.
- Established repository and domain terms: merge queue, feature flag, migration, presubmit, one-way door.
- Product, protocol, and service names: `PostgreSQL`, `HTTP/2`, `Docker`.

## Rewriting pinned text

A phrase pin is a prose constraint (e.g., a case-sensitive test assertion). An example pin is a behavioral contract. An STE rewrite can silently break a phrase pin. Follow three rules:

1. Prefer an example pin over a phrase pin.
2. Keep pinned phrases verbatim as fixed islands inside STE prose.
3. Move a pin in the same change that rewrites its sentence.

Pass `--preserve <string>` to `ste100.py` to fail when a rewrite drops a pinned substring. Repeat the flag to check several pins.

```bash
python3 skills/ai-engineering-expert/subskills/skill-authoring/scripts/ste100.py <path> --preserve <string>
```

## A rewrite

**Passive, smothered, and vague**

> `An update was conducted on the cache layer so that stale entries can be handled in a robust and seamless manner.`

**Active, direct, and specific**

> Each cache entry records the version of the pricing table used during build. The lookup compares that version against the current schema version and invalidates the entry when versions differ.

## Words that add nothing

Cut these terms unless concrete data backs them:

- **Banned adjectives and self-grades:** `comprehensive`, `robust`, `properly`, `various`, `seamless`, `cutting-edge`, `effortless`, `blazing-fast`, `state-of-the-art`, `game-changing`, `clean`, `fully tested`, `no regressions`.
- **Banned soft phrasal verbs:** `spin up`, `kick off`, `dive into`, `reach out`, `circle back`, `touch base`.
- **Conversational padding:** `basically`, `essentially`, `in order to`, `it should be noted that`, `a number of`, `should work`, `clearly`, `very common`.
- **Diminishing qualifiers:** `simply`, `just`. They mislead readers about difficulty and sound dismissive.

## Shape rules for published docs

- **Headings:** sentence case. Proper feature names keep their capitalization — `## Agent Mode settings`, not `## Agent mode settings`.
- **Lists:** `**Term** - Description`. Never a colon after the bold term.
- **UI elements:** bold buttons, links, and menu items — `Click **Save**`. Bold every segment of a settings path, leave `>` plain — `**Settings** > **AI** > **Knowledge**`.
- **Tense:** present for how things work, imperative for instructions.
- **Description field:** a standalone snippet — user benefit first, then the feature name and key terms. `Environments ensure your cloud agents run with a consistent toolchain. Learn when to use them and how to configure them.` — not `This page describes environments.`
- **Unverified leftovers:** mark them (`[UNVERIFIED]`, `[TODO: <owner> — …]`) instead of smoothing them into confident prose. A placeholder the reader can see beats a sentence they will trust and act on.
