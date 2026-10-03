---
name: writing-for-agents
description: >-
  Writing reference for agent and human-facing docs — context pointers, hierarchy, completion criteria, leading words, pruning, plain-language rules. Use when drafting SKILL.md, AGENTS.md, CLAUDE.md, PR bodies, changelogs, or reports, fixing narrative bloat, or preventing agent confusion.
metadata:
  managed-by: ai-engineering-expert
---

# Writing for Agents

Managed sub-skill of `ai-engineering-expert`. Load when `$domain` is `writing-for-agents` or when any `ai-engineering-expert` task writes or edits an agent-consumed document. For skill files, also read [$SKILL_DIR/references/skill-mechanics.md](references/skill-mechanics.md).

This skill teaches how to **shape a document so a later model run follows it reliably**. It does not teach how to run a workflow yourself. You are the designer. A future agent is the reader. Every choice below serves that handoff.

Use this reference when writing any document an agent consumes. Examples include a skill, `AGENTS.md`, `CLAUDE.md`, or a doc reached by a pointer. Packaging differs, but writing does not. The same levers make each document predictable. The agent takes the same _process_ every run, rather than producing identical output.

For an artifact a **human** judges, read [../writing-for-humans/references/plain-language.md](../writing-for-humans/references/plain-language.md) for Human-Targeted STE Flavor (active voice, scannability, narrative flow). Examples include a PR body, CHANGELOG entry, report, ADR, or published docs page. For Machine-Targeted STE Flavor (strict structural grammar, rich technical vocabulary, single actions, front-loaded guards), see [references/agent-command-grammar.md](references/agent-command-grammar.md).

When the document you write is a skill, read [`references/skill-mechanics.md`](references/skill-mechanics.md) for frontmatter, invocation choice, and router skills. For harness context-load, invocation-class, and description-budget rules, see the parent Context-Load Policy (`$SKILL_DIR/../..`). That policy is the single source of truth, not duplicated here.

## Start from intent, name the goal

Derive a one-sentence **goal** from the user's intent, artifacts, and prior chat. Let that goal decide what the document keeps, trims, and orders. This is the first and highest-leverage move. Everything below earns its keep against that goal.

- **Name it before you draft**. Write the goal down in one sentence (as `handoff` does with its Primary Goal) before choosing headings. If you delete a section and the goal still holds intact, delete it.
- **Use the goal as the review bar**. A reviewer must be able to point to the goal sentence and audit each section. The reviewer asks whether each section serves the goal or mere exposition.
- **Name the consumer, then the exclusion**. The reader determines what must not appear. Examples of readers include an agent mid-task, a reviewer, or a maintainer. Exclude implementation details from a product spec. Exclude confidential internals from a published page. Exclude restated environment details from a skill. Exclude another repository configuration from a template. Write the exclusion beside the goal. A document that leaks the wrong layer misleads the reader.
- **Pin each behavior with a concrete example**. For every branch or rule, give a concrete example. Use a before/after format or a given/when/then structure. The example is the contract. A new agent must map each example to a file and line without guessing.
- **Differentiate phrase pins and example pins**. A phrase pin is a prose constraint (e.g., case-sensitive test assertion), while an example pin is a behavioral contract. Follow three rules when rewriting pinned text:
  1. Prefer an example pin over a phrase pin.
  2. Keep pinned phrases verbatim as fixed islands inside STE prose.
  3. Move a pin in the same change that rewrites its sentence.
  Use `ste100.py --preserve <string>` to guard against dropping pinned substrings during rewrites.
- **Verify with fresh signals, not assertions**. Lints, type checks, and automated tests are the supreme authority. For qualitative fit, use a skeptic second read. Never trust an unverified claim. Trust the tool output that turns red if a claim is false.

Keep the whole skill body inline when teaching a writer. The writer needs the full picture in one read. Splitting core guidance behind extra pointers adds round-trips and variance. Reserve disclosure for branch-conditional depth, not for moves needed on every run. See [philosophy](references/philosophy.md) for the builder-facing mapping of these moves to their prior labels.

## Context pointers

A **context pointer** references out-of-context material from within the agent context window. It encodes the condition for reaching that target material. A skill description is one example. A pointer line in `AGENTS.md` is another example. The wording of a pointer decides when the agent reaches the material. It also decides how reliably that happens. A target behind a weakly worded pointer causes variance bugs. Sharpen the pointer wording first. Inline the material only if sharpening fails.

A pointer states what the material is and does. It lists the **branches** (`Use when...`) that trigger reaching the target. A branch is a distinct case handled by the document. Different runs follow different paths through branches. For skill descriptions, follow the tripartite formula: what it is, what it does, and when to use (`Use when...`). Every word of an always-loaded pointer costs tokens on every turn. Therefore, prune pointers aggressively:

- **Front-load the leading word**. The pointer is where the leading word triggers retrieval.
- **One trigger per branch**. Synonyms that rename a single branch duplicate that branch. Collapse synonyms and keep only genuinely distinct branches.
- **Cut identity the body already carries**.
- **Never point to an independent surface**. Prompt Templates (`/release`) and `disable-model-invocation: true` skills have zero model-visible metadata cost on Pi. Pi removes disabled skills from `<available_skills>` XML via `formatSkillsForPrompt`. The model never learns the skill name until a human enters `/skill:name`. An always-loaded pointer to an independent surface never fires. It adds context load with zero retrieval benefit. Discovery is human-driven through slash menus and autocomplete. Keep the command description as the sole index. Claude Code gating is selection-only, whereas Pi strips disabled skills from context.

## The two loads

Every document and pointer you add spends one of two budgets:

- **Context load**. This is the cost of always-loaded material on the agent window. Examples include `AGENTS.md` lines and skill descriptions. This material spends tokens and attention on every turn, even when unused.
- **Cognitive load**. This is the cost on the human to track which documents exist and when to reach for each. The human acts as the index. Do not treat cognitive load as a cost to minimize blindly. It represents the price of human agency. Spend it where human judgment matters. Remove it where human judgment does not matter.

Material reached only through a pointer avoids context load at the price of the pointer line. Material without any pointer relies entirely on cognitive load.

## Information hierarchy

A document contains two content types: **steps** and **reference**. Steps describe ordered actions. Reference material covers definitions, rules, and facts consulted on demand. Content types mix freely in recipes, review rules, or hybrid guides. The **information hierarchy** ranks where each piece sits by immediacy of need:

1. **In-file step**. The primary tier: what the agent does, in order.
2. **In-file reference**. Consulted on demand. Flat peer-sets (e.g., review rules on one rung) are valid structures.
3. **Disclosed reference**. Pushed into a separate file and reached by a context pointer. Loaded only when the pointer fires. This reference spans sibling files in the same folder to fully external references.

Push too little down, and the top bloats. Push too much down, and you hide material the agent needs. Managing that tension is the core decision.

**Progressive disclosure** moves detail down the ladder and behind pointers to keep the top legible. This protection of hierarchy matters more than raw token savings. Branching provides the cleanest disclosure test. Inline what every branch needs. Push behind a pointer what only specific branches reach. When a document has steps, buried in-file reference causes variance. The agent might miss critical steps. Design for three readers simultaneously: the first-time learner, the reference lookup, and the rules completist. The ladder serves all three. The learner reads only the spine, while other readers follow pointers.

**Make disclosed references self-routing**. Disclosure is otherwise all-or-nothing. When a pointer fires for one rule, the reader pays for the whole file. A reference over roughly 150 lines must open with a navigation map. Use a `## Which part of this file you need` map with anchor links. See [references/agent-command-grammar.md](references/agent-command-grammar.md) for the shape.

**Co-location** is the within-file companion to disclosure. While the ladder decides how far down a piece sits, co-location decides what sits beside it. Keep a concept definition, rules, and caveats together under one heading. Reading one part then brings its context with it. The document should read like documentation written for the agent. Grouped material reads clearly, whereas scattered material confuses the agent. Note that scattering fragments one meaning across many places, while duplication repeats one meaning in multiple places.

**Sprawl** is the primary failure mode. A sprawling document is too long, even when every line is live and unique. Agent attention thins across excess text. The cure is the ladder. Disclose reference behind pointers. Split by branch or sequence so each path carries only necessary text.

## Steps and completion criteria

Every step ends on a **completion criterion**. This condition informs the agent that the work is finished. Two properties make completion criteria effective:

- **Clarity**. Can the agent distinguish done from not-done? A vague bound invites **premature completion**. In premature completion, the agent stops before the step finishes because attention drifts to being done. Visible subsequent steps supply the pull toward premature completion. Criterion clarity supplies the necessary resistance. Defend in order: **sharpen the bound first**. Sharpening the bound is local and cheap. If the bound remains fuzzy and the agent rushes, hide later steps by splitting the sequence. Hiding steps requires a real context boundary, such as a handoff or subagent dispatch. Inline calls leave subsequent steps visible in context.
- **Demand**. This property measures how much work the criterion requires. Requiring every modified model accounted for forces rigorous effort. Vague goals like producing a change list permit superficial checks. Demand drives **legwork**, which is the unwritten investigation latent in the requirement. Demand applies to both steps and flat reference. Requiring every rule applied binds flat reference, establishing an exhaustiveness bar.

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

Multiple situations can apply at once. State each fact once. Repeating unrun disclaimers across three sections reads as hedging and obscures commands to run instead.

Avoid **grading your own work**: `comprehensive`, `robust`, `clean`, `properly`, and `fully tested` destroy credibility and describe nothing. Audit drafts for those terms and for `should work`. Each instance must quote tool output or face removal.

_Check:_ grep the draft for `fully tested|no regressions|comprehensive|robust|properly|should work` — zero hits, or every hit backed by output you can point at.

## When to split

Splitting one document into two spends budget from the two loads. Split only when the separation justifies the cost:

- **By sequence**. Split a run of steps where post-completion steps tempt the agent to rush the current step. Keeping subsequent steps hidden drives more legwork on the current task. Merging sequences exposes later steps and invites premature completion.
- **By invocation**. Skill-specific: see [`references/skill-mechanics.md`](references/skill-mechanics.md).

## Leading words

A **leading word** is a compact concept existing in model pretraining. The agent uses it during execution (e.g., _lesson_, _fog of war_, _tracer bullets_). Repeated as a token, it accumulates a distributed definition. It anchors behavior in few tokens by activating pretrained priors. Coining your own word works with clear definitions, but made-up terms lack priors. You pay definition tokens for what a pretrained word provides free. Reach for an existing word first.

A leading word anchors at two sites:

- In the body, for **execution**. The agent executes the same behavior whenever the word appears. Inside flat reference, it directs attention toward specific classes of issues.
- In a pointer, for **invocation**. When the word appears across prompts, docs, and codebase, the agent links that shared language. The agent reaches the material more reliably.

Search for opportunities to refactor using leading words. Sprawling triads and verbose sentences can collapse into single tokens:

- "fast, deterministic, low-overhead" → _tight_ (a _tight_ loop).
- "a loop you believe in" → _red_ — a fuzzy gate becomes a binary observable state (the loop goes _red_ on the bug, or it doesn't).

This yields two advantages: fewer tokens, and a sharper mental hook. Assume every document carries restatements that leading words can retire.

**Negation** is the primary failure mode for this lever. Steering by prohibition drags forbidden behavior into context. That makes the forbidden behavior more prominent. In the phrase _do not think of an elephant_, the elephant dominates attention. The negation is a weak modifier that the strong concept overruns. As a result, bans often read like instructions. Prompt the **positive** target behavior instead. For example, write "write one-line comments" so the banned behavior remains unstated. Keep a prohibition only as an unyielding guardrail where positive framing fails. Even then, pair the prohibition with a positive target.

**Voice: second-person imperative**. Write as you instruct a player on their turn. Use `Validate once at admission` or `Create a topic branch`. Do not use `Validation should be performed` or `Each player takes a branch`. Active second-person imperative provides the shortest path to model action. Passive voice and third-person phrasing add indirection and hedging. For Machine-Targeted STE Flavor, see [references/agent-command-grammar.md](references/agent-command-grammar.md).

## Pruning

- Keep each meaning in a **single source of truth**. Store each fact in one authoritative place. This structure ensures changing behavior requires an edit in only one place. **Duplication** costs maintenance effort and tokens. It inflates a concept on the ladder beyond its real rank. (Duplication is the accidental inverse of a leading word, which repeats tokens intentionally.)
- **Budget emphasis like context load**. Use bold or uppercase text only on first definition. Keep subsequent mentions plain. Every bold term claims attention during every read. Capitalizing every term makes none stand out. Define once with emphasis, then let the leading word carry the concept.
- **Prefer chart or example over paragraph**. Use tables for mappings, counts, or variants. A table (`2p:5 / 3p:5 / 4p:4`) is one lookup. In contrast, prose (`Deal 5 cards for 2 or 3 players, 4 for 4 players`) requires a parse. An example next to a rule teaches faster than explanatory prose. If prose caches what a chart could show, replace the prose.
- The **environment** is also a source of truth. Examples include `package.json` scripts, config files, directory structures, and `--help` text. A document restating these details is a **cache**. A cache earns its load only when a lookup is expensive. Cache only what an agent cannot discover by inspecting the environment. Include unwritten conventions, reasons behind choices, and subtle edge cases. Leave one-file and one-command lookups to the environment. That prevents information from going stale.

- Check every line for **relevance**. Does the line still direct what the document accomplishes? Lines lose relevance by missing the task, omitting necessary disclosure, or going stale. Shorter documents remain easier to maintain. Without pruning discipline, text decays into **sediment**. Sediment forms stale layers because adding feels safe while removing feels risky. Eventually, engineers must dig through sediment to locate live rules.
- Hunt **no-ops** sentence by sentence. An instruction that the model already follows by default wastes context. The evaluation test is model-relative rather than reader-relative. Disagreements about defaults are settled by running the document rather than by debate. When a sentence fails this test, delete the entire sentence. The test also grades leading words. Weak words like _be thorough_ fail to shift default behavior. Replace them with stronger leading words like _relentless_.
- **Template projection rule**. If reference content duplicates a template, delete the reference. Keep the single source in `templates/` or a generator script. Replace the text with a one-line pointer (`See $SKILL_DIR/scripts/*.py + --dry-run` and `uv run … --dry-run` preview). Scaffold deleted `deterministic-artifacts.md`, `python-templates.md`, and `rust-templates.md`. It retained `runtime-matrix` as a policy table. **Red flags**: duplicated template dumps and hand-copied `.releaserc.json` or `pyproject.toml` files in `references/`.
- **Cut in a pass, after drafting**. Draft thoroughly first. Then evaluate each line to name the behavior it alters or the branch it serves. Delete any line where you cannot name a purpose. Excess gathers in sections that feel obligatory. Examples include work inventories, duplicated facts, and paraphrases of adjacent code. These sections are the cheapest to remove.
- **Keep-list when cutting**. Never cut an invariant, a completion criterion, a branch trigger, or the reason behind a choice. Cut mechanisms and restatements first.
- **Do not manufacture**. When no alternative existed, state the decision plainly. Do not invent rejected options to satisfy formatting habits. Invented reasoning reads like genuine rationale while offering none.

## Failure modes

Name the mode when you cut. A named mode is easier to spot than a rule re-derived per draft.

| Mode                            | Looks like                                                           | Cure                                                                                    |
| ------------------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| **Sediment**                    | Stale layers nobody dares remove.                                    | Relevance-check each line; delete the sentence, not words from it.                      |
| **Sprawl**                      | Long although every line is live.                                    | Move reference down the ladder; split by branch or sequence.                            |
| **Duplication**                 | One meaning in two places.                                           | Single source of truth; point instead of restating.                                     |
| **Scattering**                  | One meaning fragmented across sections (duplication's inverse).      | Co-locate definition, rules, and caveats under one heading.                             |
| **No-op**                       | An instruction the model obeys by default.                           | Delete the sentence; if the point still fails to land, choose a stronger leading word.  |
| **Negation**                    | A prohibition that activates the banned behaviour.                   | Prompt the positive target; keep a guardrail only where the positive cannot be phrased. |
| **Narrating the doc's history** | "This section was moved…", "an earlier version said…".               | Describe the current state — the reader has one version, not your path to it.           |
| **Restating the environment**   | Script names, config values, or template bodies copied into prose.   | Point at the file or command; cache only what a lookup cannot show.                     |
| **Grading the document**        | "Covers everything you need", "comprehensive rules".                 | State what it does; let coverage show itself.                                           |
| **Lecturing the reader**        | "Be careful with edge cases", "make sure error handling is correct". | Point at the specific branch or decision; drop the generic advice.                      |

## Correct, complete, and teach in order

Rules must be _correct_ and _approachable_ or agents ignore them. This balance represents the game-rules tension. Keep invariants exact (e.g., falsifiable `_Check:` blocks). Teach invariants in the order the agent acts: theme, components, setup, overview, steps, and end. An undefined edge case causes model improvisation. Close every decision the agent can encounter, including untested branches. Proofread documents like playtesting games: read backwards, run the instructions, and use a Skeptic subagent reviewer. See the complete transfer table in [game-rules-writing.md](references/game-rules-writing.md).

## Harness Wiring

- **When to load**. Load this sub-skill whenever an `ai-engineering-expert` task writes or edits an agent-consumed document. Read `$SKILL_DIR/subskills/writing-for-agents/SKILL.md` directly. Sub-skills remain hidden from automatic discovery.
- **Skill-authoring integration**. Apply hierarchy, pointer wording, completion criteria, leading words, and pruning when drafting `SKILL.md` files. Keep the skill body under 500 lines. Push deep methodology into `references/` behind a pointer (see [skill-mechanics](references/skill-mechanics.md)).
- **Verification**. Verify writing deterministically using `validate-deps.py lint` and `context-check`. These scripts check frontmatter, description budgets, trigger vocabulary, and single sources of truth. Verify semantically using a Skeptic subagent comparing prose to intent. Sibling skill [verification](../verification/SKILL.md) describes fresh environment signals and skeptic reviews. Never trust model self-evaluations. Trust fresh validation output.
- **Human-facing artifacts**. For PR bodies, changelogs, reports, ADRs, or docs pages, read [plain-language.md](../writing-for-humans/references/plain-language.md). Human-Targeted STE rules invert this file's imperative voice.
- **Agent command grammar**. For Machine-Targeted STE Flavor (strict structural grammar, rich vocabulary, front-loaded guards, token insulation), read [references/agent-command-grammar.md](references/agent-command-grammar.md).
- **Prose evals**. The file [evals/evals.json](evals/evals.json) holds blind writing evals with fixtures and property assertions. Dispatch one fresh subagent per eval with only its prompt and fixture. Never show the subagent the assertions. Grade each assertion pass or fail against the returned artifact. Any fabricated claim about unrun work triggers an immediate hard fail.
