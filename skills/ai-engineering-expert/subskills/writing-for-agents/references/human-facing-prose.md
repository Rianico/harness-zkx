# Plain prose for human-facing artifacts

A human-facing artifact is anything a person reads to make a judgement: PR body, CHANGELOG entry, report or readout, ADR, README section, review comment. Baseline for all of them: **ASD-STE100** (Simplified Technical English) — a controlled language for prose that is read fast, under load, by someone who did not write the thing. Use it as a baseline, not a compliance target: the goal is prose the reader parses correctly on the first pass.

Agent-facing docs (SKILL.md, AGENTS.md, CLAUDE.md) invert these rules — terse, 2nd-person imperative, tables over sentences. Apply those in [../SKILL.md](../SKILL.md); apply this file to artifacts a human judges.

Adapted from `warpdotdev/common-skills@b811c24` (MIT, © Denver Technologies, Inc.): `write-pr-description/references/plain-language.md` + `write-feature-docs` style rules.

## Which part of this file you need

- Drafting a PR body, CHANGELOG entry, report, or ADR: [The rules](#the-rules).
- Wondering whether an identifier may be paraphrased: [What is exempt](#what-is-exempt).
- Tightening a draft that reads flat or vague: [Two rewrites](#two-rewrites).
- Cutting padding: [Words that add nothing](#words-that-add-nothing).
- Writing a published docs page: [Shape rules for published docs](#shape-rules-for-published-docs).

## The rules

| Rule                                    | Failure it prevents                                                              |
| --------------------------------------- | -------------------------------------------------------------------------------- |
| Active voice, name the actor            | Passive hides who acts — the one thing a permissions/validation reader needs     |
| One topic per sentence                  | A fact + consequence + caveat in one sentence becomes three clamped together     |
| Sentence ≤ ~25 words                    | Long sentences are almost always two facts joined by a comma                     |
| Simple tenses                           | "had been rejecting" hides which state the reader is looking at                  |
| Keep articles and connecting words      | "Fix for case where config is nil" reads as a telegram and forces a reparse      |
| One term per concept, artifact-wide     | Renaming tenant → organization → account makes the reader hunt for a distinction |
| ≤ 3 stacked nouns                       | "consumer retry backoff configuration override" forces bracketing guesses        |
| Vertical list at 3+ conditions or steps | Prose carrying several conditions hides at least one                             |
| Prefer the specific verb                | "handles/supports/manages/processes" are placeholders for an unchosen verb       |
| Paragraph ≤ ~6 sentences                | Past that, either split it or make it a list                                     |

## What is exempt

Technical names stay verbatim. Do not paraphrase an identifier to satisfy a word rule — `nil` is `nil`, not "an empty value":

- Code identifiers, type/field names, paths: `FactoryConfig`, `spawn_server_impl`, `logic/factories.go`.
- Command lines and flags, exactly as run.
- Established repository and domain jargon: merge queue, feature flag, migration, presubmit, one-way door.
- Product and service names.

## Two rewrites

**Passive and vague**

> The cache layer was updated so that stale entries can be handled appropriately.

**Active and specific**

> Each cache entry now records the version of the pricing table it was built from. The lookup compares that version against the current one and rebuilds the entry when they differ.

**Intent stated as result**

> Added tests to make sure the migration is safe to roll back.

**Result stated as result**

> `migrate down` drops the index and leaves no other residue. The integration test asserts this against a local PostgreSQL instance.

## Words that add nothing

Cut unless they carry weight: comprehensive, robust, cleanly, properly, simply, just, basically, essentially, in order to, it should be noted that, a number of.

"Simply" and "just" are worth singling out: they tell the reader the following material is easy, which is redundant, occasionally wrong, and reads as dismissive. Same family as [grading your own work](../SKILL.md#report-what-ran).

## Shape rules for published docs

- **Headings:** sentence case; proper feature names keep their capitalization — `## Agent Mode settings`, not `## Agent mode settings`.
- **Lists:** `**Term** - Description`. Never a colon after the bold term.
- **UI elements:** bold buttons, links, and menu items — `Click **Save**`; bold every segment of a settings path, leave `>` plain — `**Settings** > **AI** > **Knowledge**`.
- **Tense:** present for how things work, imperative for instructions.
- **Description field:** a standalone snippet — user benefit first, then the feature name and key terms. `Environments ensure your cloud agents run with a consistent toolchain. Learn when to use them and how to configure them.` — not `This page describes environments.`
- **Unverified leftovers:** mark them (`[UNVERIFIED]`, `[TODO: <owner> — …]`) instead of smoothing them into confident prose. A placeholder the reader can see beats a sentence they will trust and act on.
