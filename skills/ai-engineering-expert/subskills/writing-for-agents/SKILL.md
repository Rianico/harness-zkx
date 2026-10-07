---
name: writing-for-agents
description: >-
  Writing reference for agent and human-facing docs — context pointers, hierarchy, completion criteria, leading words, pruning, plain-language rules. Use when drafting SKILL.md, AGENTS.md, CLAUDE.md, PR bodies, changelogs, or reports, fixing narrative bloat, or preventing agent confusion.
metadata:
  managed-by: ai-engineering-expert
---

# Writing for Agents

Managed sub-skill of `ai-engineering-expert`. Load when `$domain` is `writing-for-agents` or when any `ai-engineering-expert` task writes or edits an agent-consumed document. Sub-skills stay hidden from automatic discovery — the parent dispatches by reading this file directly.

This skill teaches how to **shape a document so a later model run follows it reliably**. You are the designer. A future agent is the reader. The same levers apply to a skill, `AGENTS.md`, `CLAUDE.md`, or a doc reached by a pointer. The goal is the same _process_ every run, not identical output.

**Sibling boundary.** Sentence-level rules for all prose live in [plain-language.md](../../references/plain-language.md). Machine-Targeted STE structure (single actions, front-loaded guards, token insulation) lives in [agent-command-grammar.md](references/agent-command-grammar.md). Issues, RFCs, and proposals a maintainer triages belong to [writing-for-humans](../writing-for-humans/SKILL.md). When the document is a skill, read [skill-mechanics.md](references/skill-mechanics.md) for frontmatter, invocation choice, and router skills. Context-load, invocation-class, and description-budget rules live only in the parent's [context-load policy](../../references/context-load-policy.md).

## Start from intent, name the goal

Derive a one-sentence **goal** from the user's intent, artifacts, and prior chat. Let that goal decide what the document keeps, trims, and orders. Every section earns its keep against that goal.

- **Name it before you draft**. Write the goal in one sentence (as `handoff` does with its Primary Goal) before choosing headings. If you delete a section and the goal still holds, delete it.
- **Use the goal as the review bar**. A reviewer must audit each section against the goal sentence: does it serve the goal or mere exposition?
- **Name the consumer, then the exclusion**. The reader (an agent mid-task, a reviewer, a maintainer) determines what must not appear. Exclude implementation details from a product spec. Exclude confidential internals from a published page. Exclude restated environment details from a skill. Exclude another repository's configuration from a template. Write the exclusion beside the goal. A document that leaks the wrong layer misleads the reader.
- **Pin each behavior with a concrete example**. For every branch or rule, give a before/after or given/when/then example. The example is the contract. A new agent must map each example to a file and line without guessing. When rewriting pinned text, follow [Rewriting pinned text](../../references/plain-language.md#rewriting-pinned-text).
- **Verify with fresh signals, not assertions**. Lints, type checks, and automated tests are the supreme authority. For qualitative fit, use a skeptic second read. Trust the tool output that turns red if a claim is false.

Keep the whole skill body inline when teaching a writer. Splitting core guidance behind extra pointers adds round-trips and variance. Reserve disclosure for branch-conditional depth. See [philosophy](references/philosophy.md) for the builder-facing mapping of these moves to their prior labels.

## Context pointers

A **context pointer** references out-of-context material from inside the agent context window and encodes the condition for reaching it. Skill descriptions and `AGENTS.md` pointer lines are examples. Pointer wording decides when, and how reliably, the agent reaches the material. A weakly worded pointer causes variance bugs. Sharpen the wording first. Inline the material only if sharpening fails.

A pointer states what the material is and does, and lists the **branches** (`Use when...`) that trigger it. A branch is a distinct case the document handles. For skill descriptions, follow the tripartite formula: what it is, what it does, and when to use (`Use when...`). Every word of an always-loaded pointer costs tokens on every turn:

- **Front-load the leading word**. The pointer is where the leading word triggers retrieval.
- **One trigger per branch**. Synonyms that rename one branch duplicate it. Keep only genuinely distinct branches.
- **Cut identity the body already carries**.
- **Never point to an independent surface**. Prompt Templates (`/release`) and `disable-model-invocation: true` skills are invisible to the model until a human enters them, so an always-loaded pointer to them never fires and adds context load with zero retrieval benefit. Keep the command description as the sole index. Mechanics: parent context-load policy.

## The two loads

Every document and pointer you add spends one of two budgets:

- **Context load**. The cost of always-loaded material (`AGENTS.md` lines, skill descriptions) on the agent window, paid every turn even when unused.
- **Cognitive load**. The cost on the human of tracking which documents exist and when to reach for each. The human acts as the index. Cognitive load is the price of human agency. Spend it where human judgment matters. Remove it elsewhere.

Material behind a pointer avoids context load at the price of the pointer line. Material without any pointer relies entirely on cognitive load.

## Information hierarchy

A document holds **steps** (ordered actions) and **reference** (definitions, rules, facts consulted on demand). The **information hierarchy** ranks where each piece sits by immediacy of need:

1. **In-file step**. The primary tier: what the agent does, in order.
2. **In-file reference**. Consulted on demand. Flat peer-sets (e.g., review rules on one rung) are valid.
3. **Disclosed reference**. A separate file reached by a context pointer, loaded only when the pointer fires.

Push too little down, and the top bloats. Push too much down, and you hide material the agent needs. Managing that tension is the core decision.

**Progressive disclosure** moves detail down the ladder to keep the top legible. Branching is the cleanest test: inline what every branch needs, and disclose what only specific branches reach. Buried in-file reference makes the agent miss steps. The ladder serves three readers. The first-time learner reads the spine. The reference lookup and the rules completist follow pointers.

**Make disclosed references self-routing**. When a pointer fires for one rule, the reader pays for the whole file. A reference over roughly 150 lines must open with a `## Which part of this file you need` map with anchor links. See [plain-language.md](../../references/plain-language.md) for the shape.

**Co-location** decides what sits beside a piece. Keep a concept's definition, rules, and caveats under one heading so reading one part brings its context.

## Steps and completion criteria

Every step ends on a **completion criterion** that tells the agent the work is finished. Two properties make it effective:

- **Clarity**. Can the agent distinguish done from not-done? A vague bound invites **premature completion**: the agent stops early because visible later steps pull attention toward being done. Defend in order. Sharpen the bound first, because it is local and cheap. If the agent still rushes, hide later steps by splitting the sequence. Hiding needs a real context boundary, such as a handoff or subagent dispatch. Inline calls leave later steps visible.
- **Demand**. How much work the criterion requires. "Every modified model accounted for" forces rigor. "Produce a change list" permits a skim. Demand drives **legwork**, the unwritten investigation latent in the requirement. "Every rule applied" sets the same exhaustiveness bar for flat reference.

The strongest criteria are checkable and exhaustive.

## Report what ran

Every claim about work must describe something that ran, or state plainly that it did not. **Never write intent as though it were a result**. The reader cannot tell the difference. A report that overstates results is worse than a silent report.

| Situation                | What to write                                                                                                                                                          |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nothing ran              | Say so, and name the command the reader or CI should run.                                                                                                              |
| CI produces the result   | Name the job and mark the outcome as an expectation ("expect one destroy and one create"), never as an observation.                                                    |
| Checks added but not run | Say the checks are added and unrun, so nobody reads a list of tests as evidence they passed.                                                                           |
| You could not run it     | Name what it needs (device, credentials, environment) and the check you are asking the reader to make. Never cover a skip this way — if you could have run it, run it. |
| Someone else recorded it | Attribute it, or leave it out. Never restate it as your own observation.                                                                                               |

Multiple situations can apply at once. State each fact once. Repeating unrun disclaimers across sections reads as hedging and buries the commands to run.

Avoid **grading your own work**. Self-grades describe nothing and destroy credibility. The banned list lives in [Words that add nothing](../../references/plain-language.md#words-that-add-nothing).

_Check:_ grep the draft for `fully tested|no regressions|comprehensive|robust|properly|should work` — zero hits, or every hit backed by output you can point at.

## When to split

Splitting one document into two spends both loads. Split only when the separation pays:

- **By sequence**. Split a run of steps where later steps tempt the agent to rush the current one. Hidden later steps drive more legwork now.
- **By invocation**. Skill-specific: see [`references/skill-mechanics.md`](references/skill-mechanics.md).

## Leading words

A **leading word** is a compact concept from model pretraining that the agent uses during execution (e.g., _lesson_, _fog of war_, _tracer bullets_). Repeated as a token, it accumulates a distributed definition and anchors behavior in few tokens. A coined word works with a clear definition, but you pay definition tokens for what a pretrained word provides free. Reach for an existing word first.

A leading word anchors at two sites:

- In the body, for **execution**. The agent repeats the same behavior wherever the word appears. In flat reference, it directs attention toward a class of issues.
- In a pointer, for **invocation**. The word recurs across prompts, docs, and code. The agent links that shared language and reaches the material more reliably.

Refactor sprawling triads and verbose sentences into single tokens:

- "fast, deterministic, low-overhead" → _tight_ (a _tight_ loop).
- "a loop you believe in" → _red_ — a fuzzy gate becomes a binary observable state (the loop goes _red_ on the bug, or it doesn't).

Assume every document carries restatements that leading words can retire.

**Negation** is this lever's failure mode. Steering by prohibition drags the forbidden behavior into context. In _do not think of an elephant_, the elephant dominates and overruns the weak negation. Prompt the **positive** target instead, e.g. "write one-line comments", so the banned behavior stays unstated. Keep a prohibition only as a guardrail where positive framing fails, and pair it with a positive target.

**Voice: second-person imperative**. Instruct the reader as a player on their turn: `Validate once at admission`, `Create a topic branch`. Passive and third-person phrasing (`Validation should be performed`, `Each player takes a branch`) add indirection and hedging.

## Pruning

- Keep each meaning in a **single source of truth**, so changing behavior takes one edit. **Duplication** costs maintenance and tokens, and inflates a concept beyond its real rank. (Duplication is the accidental inverse of a leading word, which repeats tokens on purpose.)
- **Budget emphasis like context load**. Bold or uppercase only on first definition. Every bold term claims attention on every read, and bolding everything makes nothing stand out.
- **Prefer chart or example over paragraph**. A table (`2p:5 / 3p:5 / 4p:4`) is one lookup. Prose (`Deal 5 cards for 2 or 3 players, 4 for 4 players`) needs a parse. An example beside a rule teaches faster than explanation.
- The **environment** is also a source of truth: `package.json` scripts, config files, directory structures, `--help` text. A document restating them is a **cache**. Cache only what inspection cannot reveal: unwritten conventions, reasons behind choices, subtle edge cases. Leave one-file and one-command lookups to the environment, so nothing goes stale.
- Check every line for **relevance**. Lines lose relevance by missing the task, omitting needed disclosure, or going stale. Without pruning, text decays into **sediment**: stale layers that pile up because adding feels safe and removing feels risky.
- Hunt **no-ops** sentence by sentence. An instruction the model already follows by default wastes context. The test is model-relative, settled by running the document rather than by debate. Delete a failing sentence whole. Weak leading words (_be thorough_) also fail the test. Replace them with stronger ones (_relentless_).
- **Template projection rule**. If reference content duplicates a template, delete the reference. Keep the single source in `templates/` or a generator script, and leave a one-line pointer to the generator (`uv run $SKILL_DIR/scripts/<name>.py --dry-run` previews the output). **Red flags**: duplicated template dumps and hand-copied `.releaserc.json` or `pyproject.toml` files in `references/`.
- **Cut in a pass, after drafting**. Draft thoroughly first. Then name the behavior each line alters or the branch it serves. Delete any line without one. Excess gathers in sections that feel obligatory: work inventories, duplicated facts, paraphrases of adjacent code.
- **Keep-list when cutting**. Never cut an invariant, a completion criterion, a branch trigger, or the reason behind a choice. Cut mechanisms and restatements first.
- **Do not manufacture**. When no alternative existed, state the decision plainly. Invented rejected options read like rationale while offering none.

## Failure modes

Name the mode when you cut. A named mode is easier to spot than a rule re-derived per draft.

| Mode                            | Looks like                                                           | Cure                                                                                    |
| ------------------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Sediment**                    | Stale layers nobody dares remove.                                    | Relevance-check each line; delete the sentence, not words from it.                      |
| **Sprawl**                      | Long although every line is live; attention thins across excess.     | Move reference down the ladder; split by branch or sequence.                            |
| **Duplication**                 | One meaning in two places.                                           | Single source of truth; point instead of restating.                                     |
| **Scattering**                  | One meaning fragmented across sections (duplication's inverse).      | Co-locate definition, rules, and caveats under one heading.                             |
| **No-op**                       | An instruction the model obeys by default.                           | Delete the sentence; if the point still fails to land, choose a stronger leading word.  |
| **Negation**                    | A prohibition that activates the banned behaviour.                   | Prompt the positive target; keep a guardrail only where the positive cannot be phrased. |
| **Narrating the doc's history** | "This section was moved…", "an earlier version said…".               | Describe the current state — the reader has one version, not your path to it.           |
| **Restating the environment**   | Script names, config values, or template bodies copied into prose.   | Point at the file or command; cache only what a lookup cannot show.                     |
| **Grading the document**        | "Covers everything you need", "comprehensive rules".                 | State what it does; let coverage show itself.                                           |
| **Lecturing the reader**        | "Be careful with edge cases", "make sure error handling is correct". | Point at the specific branch or decision; drop the generic advice.                      |

## Correct, complete, and teach in order

Rules must be _correct_ and _approachable_, or agents ignore them — the game-rules tension. Keep invariants exact (e.g., falsifiable `_Check:` blocks). Teach in the order the agent acts: theme, components, setup, overview, steps, and end. An undefined edge case causes improvisation, so close every decision the agent can meet, including untested branches. Proofread like playtesting: read backwards, run the instructions, and use a Skeptic subagent reviewer. See the transfer table in [game-rules-writing.md](references/game-rules-writing.md).

## Harness Wiring

- **Skill-authoring integration**. Apply hierarchy, pointer wording, completion criteria, leading words, and pruning when drafting `SKILL.md` files. Keep the skill body under 500 lines. Push deep methodology into `references/` behind a pointer (see [skill-mechanics](references/skill-mechanics.md)).
- **Verification**. Verify deterministically with `validate-deps.py lint` and `context-check`. They check frontmatter, description budgets, trigger vocabulary, and single sources of truth. Verify semantically with a Skeptic subagent comparing prose to intent. Sibling skill [verification](../verification/SKILL.md) covers fresh environment signals and skeptic reviews.
- **Prose evals**. [evals/evals.json](evals/evals.json) holds blind writing evals with fixtures and property assertions. Dispatch one fresh subagent per eval with only its prompt and fixture. Never show the subagent the assertions. Grade each assertion pass or fail against the returned artifact. Any fabricated claim about unrun work is an immediate hard fail.
