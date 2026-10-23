---
name: writing-for-agents
description: >-
  Writing reference for agent-consumed docs — pointers, hierarchy, completion criteria, and pruning. Use when drafting or editing SKILL.md, AGENTS.md, or CLAUDE.md, fixing prompt bloat, pruning no-ops, or clarifying agent instructions.
metadata:
  managed-by: ai-engineering-expert
---

# Writing for Agents

Authoritative guide for structuring documents that agents consume (`SKILL.md`, `AGENTS.md`, `CLAUDE.md`, or pointer targets).

Ensure the agent follows the same reliable process on every run. Do not expect identical token output.

## Sibling Boundaries

- Sentence-level grammar, STE-100 vocabulary, and banned fluff live in [plain-language.md](../../references/plain-language.md).
- Human proposals, RFCs, and issues belong to [writing-for-humans](../writing-for-humans/SKILL.md).
- Skill frontmatter, invocation classes, and router patterns live in [skill-authoring](../skill-authoring/SKILL.md).

## 1. The Reading Bottleneck & Controlled Language

Generation is fast. Reading and comprehension is the primary bottleneck. Sprawling prose dilutes attention, which causes hallucinations and skipped steps.

Address this bottleneck with controlled technical English (80% ASD-STE100):
- **Imperative mood:** Direct the reader with active commands (`Validate inputs at admission`).
- **Short sentences:** Keep procedural instructions to 20 words or fewer. Keep descriptive sentences to 25 words or fewer.
- **One action per sentence:** Never combine sequential steps with conjunctions.
- **Front-loaded guards:** Place conditions before actions: `If <condition>, then <action>`. Trailing conditions cause speculative execution before the model checks guards.
- **Structured lookups:** Use tables or key-value pairs for mappings. Structured formats provide immediate random access without parsing ambiguity.

## 2. Context Pointers & The Two Loads

Every instruction spends one of two budgets:
- **Context Load:** Tokens sitting in context on every turn (`AGENTS.md`, skill descriptions). Prune ruthlessly.
- **Cognitive Load:** Memory load on the human operator. Router skills index workflows without loading details into agent context.

A **context pointer** references external material and defines its activation trigger:
- **Formula:** State what it does, followed by when to use it (`Use when...`).
- **Front-load leading words:** Put retrieval keywords at the start of the pointer.
- **One trigger per branch:** Collapse synonyms. List only distinct operational branches.
- **Denotation sentence:** Add a concise description when the model cannot deduce artifact contents from context. Describe what the file contains.
- **Zero technical duplication:** Point to artifacts by path. Never copy their contents into the pointer.

## 3. Information Hierarchy & Progressive Disclosure

Structure content across three tiers:
1. **In-file step:** Ordered procedural actions the agent must execute.
2. **In-file reference:** Rules and tables consulted on demand. Flat peer sets belong here.
3. **Disclosed reference:** Material pushed to a separate file behind a pointer, loaded only when a branch triggers.

**The Disclosure Test:** Inline what every execution branch requires. Disclose behind a pointer what only specific branches reach.

**Co-Location:** Keep a concept's definition, execution rules, and edge cases under a single heading. Never scatter related constraints across distant sections.

## 4. Completion Criteria & Sequence Splitting

Every procedural step must conclude with a checkable, falsifiable **completion criterion**.

- **Resist premature completion:** Visible upcoming steps pull attention toward concluding early. Sharpen completion boundaries with observable states (such as exit codes or assertion passes).
- **Split by sequence:** If an agent rushes exploratory work, hide subsequent steps behind a subagent dispatch or handoff. A context boundary eliminates premature completion.

## 5. Leading Words & Positive Steering

- **Recruit pretraining priors:** Use established, compact domain concepts (`tight`, `red`, `tracer bullets`, `idempotent`). Never coin custom jargon when standard software engineering terms already activate pre-trained behaviors.
- **Prompt positive target behavior:** Negation ("Do not write multi-line comments") primes the forbidden tokens. Direct the positive action ("Write single-line comments").

## 6. Pruning Discipline

- **Single source of truth:** Define each rule in exactly one place.
- **Environment as authority:** Never copy directory layouts, CLI help, or package scripts into prose. Prose is a cache. Cache only unwritten rationale or non-obvious invariants.
- **Sentence-level no-op hunting:** Delete any instruction that the base model follows by default.
- **Model gotchas & retirable constraints:** Isolate empirical model quirks under a dedicated gotcha block. Pair each gotcha with a positive recovery action. Delete entries as frontier models advance.
