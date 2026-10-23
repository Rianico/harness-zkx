---
name: writing-for-agents
description: >-
  Writing reference for agent-consumed docs — philosophy, contracts, context pointers, hierarchy, completion criteria, and pruning under STE-100. Use when drafting or editing SKILL.md, AGENTS.md, or CLAUDE.md, fixing prompt bloat, pruning no-ops, or clarifying agent instructions.
metadata:
  managed-by: ai-engineering-expert
---

# Writing for Agents

Managed sub-skill of `ai-engineering-expert`.
Load when `$domain` is `writing-for-agents`.
Also load when an `ai-engineering-expert` task writes or edits an agent-consumed document.
Sub-skills stay hidden from automatic discovery.
The parent dispatches by reading this file directly.

This skill teaches how to shape documents so future agent runs follow them reliably.
You are the designer.
A future agent is the reader.
The same levers apply to a skill, `AGENTS.md`, `CLAUDE.md`, or pointer documents.

**Sibling boundaries:**
- Sentence-level plain language rules live in [plain-language.md](../../references/plain-language.md).
- Human-facing issues, RFCs, and proposals belong to [writing-for-humans](../writing-for-humans/SKILL.md).
- Context-load and description-budget policies live in the parent [context-load policy](../../references/context-load-policy.md).

## Part I: Philosophy

### 1. Predictability as the Root Virtue

A skill exists to wrangle determinism out of a stochastic model.
**Predictability** is the root virtue of agent engineering.
Ensure the agent takes the same process on every run, rather than expecting identical token output.
Every structural lever in this skill serves predictable execution.

### 2. Goal-Driven Development: Intent and Scoping

Derive a one-sentence **goal** from user intent and repository state before drafting.
Let that goal govern what the document keeps, trims, and orders:
- **The goal is the review bar:** Audit every section against the goal sentence. If deleting a section leaves the goal intact, delete the section.
- **Name the consumer, then the exclusion:** The reader sets what must not appear. Exclude restated environment details from a skill. Exclude implementation secrets from public instructions.
- **State non-goals explicitly:** Explicit boundaries prevent model improvisation and scope creep.

### 3. Behavior-Driven Development: Concrete Contracts

Pin every rule and execution branch with a concrete, falsifiable example.
The example serves as the behavioral contract:
- **Avoid abstract prose explanations:** Ground rules in before-after pairs or Given-When-Then cases.
- **Turn guessing into translation:** A future agent must map each example to a concrete file and line without ambiguity.
- **Insulate technical tokens:** Wrap code tokens, file paths, tool names, and flags in backticks (`token`).

### 4. Environmental Truth and Honest Reporting

Environmental truth is supreme authority.
Trust only what tools, compilers, linters, and tests observe, never what the model claims.

**Report what ran:**
Every factual claim must name something that ran, or state plainly that it did not.
Never write intent as though it were a result.

| Situation | What the text says |
| --- | --- |
| Nothing ran | Say so, and name the command a reader would run. |
| CI produced the result | Name the run. Never describe it as local. |
| Checks added, not run | Say they are skipped, and that the skip was deliberate. |
| You could not run it | Name what it needs. Never let a skip look like a pass. |
| Someone else recorded it | Attribute it by name. |

_Check:_ grep the draft for `fully tested|no regressions|comprehensive|robust|properly|should work`.
Every hit needs evidence or deletion.

### 5. The Reading Bottleneck and Controlled Language (ASD-STE100)

Reading is the primary bottleneck in agent systems.
Language models generate tokens quickly, but long context windows dilute attention and increase latency.
Verbose instructions cause model hesitation, hallucinations, and premature completion.

Address this reading tax with controlled technical English.
Aim for the 80% ASD-STE100 standard:
- **Active voice and imperative mood:** Instruct the reader directly (`Validate once at admission`). Avoid passive phrasing (`Validation should be performed`).
- **Short sentences:** Keep procedural instructions to 20 words or fewer. Keep descriptive sentences to 25 words or fewer.
- **One action per sentence:** Never combine multiple sequential commands with coordinating conjunctions. Compound sentences tempt the model into premature completion or partial step execution.
- **Front-loaded guards:** Place the condition before the action: `If <condition>, then <action>`. A trailing condition lets the model emit tool calls before it evaluates the guard.
- **Single meaning per term:** Assign one specific meaning to each word. Avoid decorative synonyms or metaphors.
- **Budget emphasis:** Bold a term at its first definition only. Every bold mark spends attention on every re-read.
- **Zero filler:** Strip out conversational padding, qualifiers, and unsupported assertions.

Follow the representation ladder for high-density communication:
1. **Controlled text:** Concise STE-100 sentences for sequential steps.
2. **Tables and structured data:** Use tables for mappings or rules (`2p:5 / 3p:5 / 4p:4`). A table provides a single lookup. Prose requires parsing.
3. **Focused visual diagrams:** Use call trees or Mermaid diagrams when relationships exceed four sentences.
4. **Interactive artifacts:** Use self-contained files when human parameters require inspection.

## Part II: Workflow Pattern

### 6. The Two Loads Budgeting

Every document and pointer spends one of two budgets:
- **Context load:** The cost of always-loaded material on the agent window. Skill descriptions and `AGENTS.md` lines sit in context on every turn. They consume tokens and attention whether used or not.
- **Cognitive load:** The cost on human operators to remember documents and when to invoke each one. The human acts as the index. Spend cognitive load where human judgment matters. Eliminate it elsewhere.

Material reached through a pointer avoids context load at the price of the pointer line.
Material without a pointer relies entirely on cognitive load.
A router skill indexes user-invoked skills without registering them into root context.
See [skill-authoring](../skill-authoring/SKILL.md).

### 7. Crafting Context Pointers

A **context pointer** is an in-context reference that points to external material and specifies when to read it.
A skill description or an `AGENTS.md` entry is a context pointer.
The wording of the pointer dictates how reliably an agent reaches the material.
Weak wording causes variance bugs.
Sharpen the trigger wording first.
Inline the material only if sharpening fails.

A context pointer states what the document does and lists the triggering branches.
Every word in an always-loaded pointer costs tokens on every turn.
Prune pointers with extreme care:
- **Front-load the leading word:** Place primary retrieval keywords at the beginning of the pointer.
- **One trigger per branch:** Avoid listing synonyms for a single scenario. Synonyms duplicate a single branch. Keep only genuinely distinct cases.
- **Follow the tripartite formula:** State what the skill is, what it does, and when to use it (`Use when...`).
- **Cut identity already in the body:** Remove internal section names or redundant metadata.
- **Never point to invisible surfaces:** Avoid pointing to commands marked with `disable-model-invocation: true`. Such pointers consume context tokens without aiding autonomous model retrieval.

### 8. Structuring the Information Hierarchy

A document contains two types of content:
- **Steps:** Ordered actions the agent performs sequentially.
- **Reference:** Definitions, rules, and facts consulted on demand.

Place each item on the **information hierarchy** ladder based on immediacy of need:
1. **In-file step:** The primary tier. Specifies sequential actions in order.
2. **In-file reference:** Consulted on demand. Flat peer sets (such as lint rules) belong on this rung.
3. **Disclosed reference:** Pushed into a separate file and reached via a context pointer. Loaded only when the pointer fires.

Push too little down, and the top-level document bloats.
Push too much down, and you hide essential instructions.
Balancing this tension is the central design choice.

#### Progressive Disclosure

**Progressive disclosure** moves reference material out of the main document and behind a pointer.
This move keeps the operational spine clear.
Use branching as the disclosure test:
- Inline material that every branch needs.
- Disclose material behind a pointer if only specific branches require it.

Disclose reference files with self-routing navigation.
When a reference file exceeds roughly 150 lines, open with a short navigation table.

#### Co-Location

**Co-location** governs what sits beside a concept within a file.
Keep a concept's definition, execution rules, and edge cases under a single heading.
Do not scatter related rules across different sections.
Grouped material ensures reading one rule loads adjacent caveats automatically.

### 9. Steps and Completion Criteria

Every procedural step must conclude with a **completion criterion**.
The criterion tells the agent when the task is finished.
Two properties determine criterion effectiveness:

- **Clarity:** Can the agent distinguish done from not-done?
  Vague boundaries invite **premature completion**.
  Visible upcoming steps pull attention toward being done before the current step finishes.
  Defend against premature completion in order:
  1. Sharpen the completion boundary first. Make it falsifiable and local.
  2. If the agent continues rushing, split the sequence across a context boundary (such as a subagent dispatch).
- **Demand:** How much thoroughness the criterion requires.
  Demanding criteria drive **legwork** (the investigation latent in the task).
  Phrasing such as "account for every modified file" forces deeper work than "review changes".
  Demanding criteria bind flat reference rules as firmly as sequential steps.

Construct criteria that are both checkable and exhaustive.

### 10. When to Split

Dividing documents incurs cognitive or context overhead.
Split a document only when the boundary earns its cost:

- **By sequence:** Split a series of steps when future steps cause the agent to rush.
  Hiding later steps behind a subagent dispatch or handoff forces complete legwork on the immediate step.
- **By invocation:** Split off an independent skill when a distinct leading word warrants dedicated autonomous triggering.
  An independent model-invoked skill adds context load through its description.
  Ensure that independent discovery justifies the token cost.

### 11. Leading Words and Positive Steering

A **leading word** is a compact concept from model pretraining that anchors agent behavior (`tight`, `red`, `tracer bullets`).
A leading word recruits existing model priors to govern behavior in few tokens.
Prefer established terms over coined words.
A coined word costs definition tokens, while a pretrained word recruits existing priors without cost.

Leading words anchor behavior at two sites:
- **In execution (the body):** The model repeats the target behavior whenever the token appears. In reference text, the word focuses attention on specific patterns.
- **In invocation (pointers):** Shared vocabulary across prompts, documentation, and codebase helps the model activate the skill reliably.

Refactor wordy instructions into compact leading words:
- "Fast, deterministic, low-overhead" -> `tight` (a `tight` verification loop).
- "A check you trust" -> `red` (the test goes `red` on regression).

#### Avoid Negation

Steering by prohibition activates the forbidden behavior.
In *do not think of an elephant*, attention fixes upon the elephant.
Negation acts as a weak modifier that the model easily overruns.
Always prompt the **positive target behavior**:
- Instead of "Do not write multi-line comments", write "Write single-line comments".
- State what the model must do, rather than what it must avoid.
- Only a repeated failure earns a negative gotcha. See Section 12.

### 12. Model Gotchas and Retirable Constraints

Isolate empirical model quirks into an independent section.
Add a negative constraint only if a model repeatedly executes a forbidden action despite positive steering.

Maintain this independent section under strict lifecycle rules:
- **Isolate from core prose:** Keep model-specific workarounds in this dedicated section. Do not scatter negative rules across procedural workflows.
- **Pair with positive recovery:** For every recorded gotcha, specify both the forbidden failure and the required recovery action.
- **Retire as models advance:** Frontier model updates resolve older reasoning traps. An isolated section allows rapid auditing, iteration, and pruning without disrupting core instructions.

### 13. Pruning Discipline

Maintain strict pruning discipline to preserve model attention:

- **Single source of truth:** Keep each rule in one authoritative file. Duplication costs maintenance and token budget.
- **Environment as authority:** Configuration files, package scripts, directory trees, and `--help` text provide factual truth. Prose that copies them becomes stale. Cache only facts that direct inspection cannot reveal, such as unwritten conventions or rationale.
- **Relevance checks:** Inspect every sentence. Information loses relevance when external context shifts. Outdated instructions accumulate into **sediment**.
- **Sentence-by-sentence no-op hunting:** Test whether each sentence alters agent behavior beyond base model defaults. If an instruction states default model behavior, delete the sentence completely.
- **Template projection:** Never paste complete template files into reference prose. Keep authoritative templates in `templates/` or generator scripts, and point to them.
- **Cut in dedicated passes:** Draft content completely first. Then audit each sentence to verify what concrete behavior it changes. Delete sentences that provide only narrative filler or backstory.

### 14. Diagnosing Failure Modes

Identify and resolve these structural failure modes:

| Failure Mode | Symptoms | Remediation |
| --- | --- | --- |
| **Premature completion** | The agent finishes a step early because visible later steps draw attention away. | Sharpen the completion criterion first. If rushing persists, hide later steps via subagents. |
| **Duplication** | The same rule appears in multiple places. | Establish a single source of truth and reference it with a context pointer. |
| **Sediment** | Outdated procedural layers remain because authors hesitate to remove old text. | Review instructions against current workflows and delete stale sentences. |
| **Sprawl** | The document grows excessively long, thinning attention across unnecessary words. | Move reference material down the hierarchy ladder; split by branch or sequence. |
| **No-op** | The instruction directs the model to perform actions it already executes by default. | Delete the sentence; replace weak directives with distinct leading words. |
| **Negation** | Negative phrasing names banned behavior and causes the model to focus on it. | Restate the rule as a positive target behavior. |
| **Scattering** | Concept definitions, execution rules, and edge cases are divided across distant sections. | Co-locate definition, rules, and edge cases under a single heading. |
| **Restating the environment** | The document copies script names, tool arguments, or configuration schemas into prose. | Point to the underlying file or tool directly; cache only hidden rationale. |
| **Narrating history** | Prose discusses previous edits ("This section was moved...", "An earlier version said..."). | Describe current state only. The reader requires the current specification. |
| **Self-grading** | Prose uses vague praise without empirical proof. | Replace adjectives with measurable conditions and explicit verification commands. |
| **Lecturing** | Text offers generic advice without concrete guidance. | Point to specific edge cases or remove the lecture. |

### 15. Harness Wiring and Verification

Apply these integration patterns across the harness:

- **Skill authoring integration:** Apply ASD-STE100 rules, hierarchy ladders, pointer formulas, and pruning during skill creation. Keep skill bodies under 500 lines.
- **Proofreading and backwards reading:** Proofread backwards across sections to isolate individual statements from narrative momentum.
- **Deterministic verification:** Validate frontmatter and trigger budgets using `validate-deps.py lint` and `context-check`. Validate plain English constraints using `ste100.py`.
- **Semantic verification:** Dispatch a Skeptic reviewer subagent to evaluate prose against user intent. The reviewer audits for unstated assumptions, vague completion criteria, and narrative bloat.
- **Prose evaluation evals:** Run blind evaluations in `evals/evals.json` with assertions withheld from the worker agent. Grade output against strict criteria. Any fabricated claim regarding unrun commands constitutes a hard failure.

## References

- ASD-STE100 Issue 9 (2025): Simplified Technical English specification.
- Karpathy, A. (2026): On reading bottlenecks and controlled English in language models.
