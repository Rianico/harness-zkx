# Agent Command Grammar

In Computer Science, we never use the rigid ~900-word aerospace dictionary from literal ASD-STE100. Doing so would break software engineering by banning fundamental terms like `parse`, `serialize`, `cache`, `timeout`, `spawn`, `dispatch`, and `mutex`.

Instead, both modes in this harness are **STE Flavors** adapted for computing. They are governed by two independent dials:

1. **The Lexical (Vocabulary) Dial:** Rich technical vocabulary and verbatim code tokens are always permitted. We only ban subjective marketing adjectives (`robust`, `seamless`, `cutting-edge`) and ambiguous soft phrasal verbs (`spin up`, `touch base`).
2. **The Structural (Grammar) Dial:** Dictates sentence structure and rigidity based on target audience:
   - **Machine-Targeted STE Flavor** (formerly Strict Structural Mode): Designed for machine-parsed and model-primary artifacts. These include tool/function descriptions, error messages, system prompts, inter-agent instructions (`herdr`), and procedural runbooks (`SKILL.md` body, `AGENTS.md`). It imposes strict structural rules. Requirements include 1 action per sentence, second-person imperative, and front-loaded guards (`If X, then Y`). It limits instructions to ≤20 words, requires zero synonym rotation, and enforces backticked token insulation.
   - **Human-Targeted STE Flavor** (Narrative Mode): Designed for human-judged decision artifacts. These include PR descriptions, ADRs, RFCs, GitHub issues, CHANGELOGs, and review comments. It employs active voice with named actors, ≤25 words per sentence, 60-second scannability, nominalization removal, and evidence over adjectives. See [../../writing-for-humans/references/plain-language.md](../../writing-for-humans/references/plain-language.md).

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

- The two dials: [Lexical vs. Structural dials](#the-two-dials-lexical-vs-structural).
- Action structure: [Imperative mood and single action](#imperative-mood-and-single-action).
- Conditional execution: [Front-loaded branching guards](#front-loaded-branching-guards).
- Protecting code and paths: [Technical token insulation](#technical-token-insulation).
- Domain consistency: [Zero synonym rotation](#zero-synonym-rotation).
- Preserving uncertainty and confidence bounds: [Modality preservation](#modality-preservation).
- Side-by-side patterns: [Comparative grammar table](#comparative-grammar-table).
- Mode selection: [Timing arbitration table](#timing-arbitration-table).

## The two dials: Lexical vs. Structural

| Dial | Scope | Rule in Computer Science |
| --- | --- | --- |
| **Lexical (Vocabulary)** | Word choice, terminology, identifiers | **Rich domain vocabulary allowed.** Never use the ~900-word aerospace dictionary. Use exact CS terms (`serialize`, `mutex`, `cache`). Ban only subjective marketing fluff and soft phrasals. |
| **Structural (Grammar)** | Sentence syntax, clause count, branching | **Audience-dependent constraints.** Machine-targeted: ≤20 words, 1 action/sentence, front-loaded guards. Human-targeted: ≤25 words, active voice, 60s scannability. |

## Imperative mood and single action

Instruct the agent in the second-person imperative mood (`Run`, `Verify`, `Parse`, `Output`). 

- Limit each sentence to exactly **one action**.
- Never join consecutive actions with `and then`, semicolons, or comma splices.
- Compound sentences tempt the model into premature completion or partial step execution.

**Bad:**
> Read the configuration file and then extract the database credentials, verifying they are non-empty.

**Good:**
> Read the configuration file. Extract the database credentials. Verify the credentials are non-empty.

## Front-loaded branching guards

Place conditional checks and guards **before** the action: `If <condition>, then <action>`.

- Trailing conditions (`<action> if <condition>`) cause agents to begin generating tool calls before attending to the guard.
- Front-loading forces the attention head to evaluate the prerequisite state before emitting the command.

**Bad:**
> Roll back the migration if any integration test fails.

**Good:**
> If any integration test fails, roll back the migration.

**Bad:**
> Dispatch worker tasks once the queue size exceeds 100 items.

**Good:**
> When the queue size exceeds 100 items, dispatch worker tasks.

## Technical token insulation

Wrap every code symbol, CLI command, parameter, file path, and HTTP method in backticks (`` `...` ``):

- Backticking shields tokens from natural language tokenization ambiguity.
- Insulation prevents the agent from paraphrasing or translating identifiers (e.g. converting `nil` to "empty").
- Deterministic linters exclude inline code spans from prose word count calculations.

**Bad:**
> Run uv run pytest on tests/unit/test_auth.py with the verbose flag.

**Good:**
> Run `uv run pytest -v` on `tests/unit/test_auth.py`.

## Zero synonym rotation

Bind exactly one term to each domain concept across the entire document.

- Human writers rotate synonyms to avoid repetitive phrasing. For agents, synonym rotation is an ambiguity bug: the model searches for latent distinctions between `tenant`, `account`, and `organization`.
- Adhere strictly to the ubiquitous language defined in the project's domain model.

**Bad:**
> Initialize the repository. Inspect files in the codebase. Commit updates to the project.

**Good:**
> Initialize the repository. Inspect files in the repository. Commit updates to the repository.

## Modality preservation

Preserve epistemic modalities to accurately communicate system confidence and constraint levels:

| Modal | Semantic Role | Agent Behavior |
| ----- | ------------- | -------------- |
| `MUST` | Hard invariant | Never violate; halt and report error if impossible |
| `SHOULD` | Strong default | Follow unless a specific, documented exception applies |
| `MAY` / `could` | Permissible choice / Confidence bound | Explore when appropriate; do not treat as mandatory |

- **Do not collapse `MAY` into `MUST`:** Over-constraining forces the agent into brittle dead-ends when encountering edge cases.
- **Do not soften `MUST` into `SHOULD`:** Weakening invariants leads to silent validation bypasses.
- Preserve probabilistic confidence indicators (`may fail under high concurrency`) so the agent factors uncertainty into error handling.

## Comparative grammar table

| Dimension | Trailing / Permissive (Fragile) | Front-Loaded / Structural (Reliable) |
| --------- | -------------------------------- | ------------------------------------- |
| **Action count** | `Compile the binary and run tests.` | `Compile the binary. Run the tests.` |
| **Branch guard** | `Retry the request if timeout occurs.` | `If a timeout occurs, retry the request.` |
| **Token insulation** | `Call getUserById in api/users.ts.` | `Call \`getUserById\` in \`api/users.ts\`.` |
| **Ubiquitous language** | `Fetch ticket, then close issue.` | `Fetch issue, then close issue.` |
| **Modality precision** | `You should always check errors.` | `You MUST check errors.` |

## Timing arbitration table

| Mode / Dimension | Scope / Artifacts | Key Rules & Sentence Length |
| --- | --- | --- |
| **Machine-Targeted STE Flavor** (Strict Structure) | Tool/function descriptions, error messages, system prompts, inter-agent instructions (`herdr`), procedural runbooks (`SKILL.md` body, `AGENTS.md`) | ≤20 words/instruction, 1 action/sentence, imperative, front-loaded guards, zero synonym rotation, token insulation |
| **Human-Targeted STE Flavor** (Narrative Mode) | Human-primary decision artifacts (PR descriptions, ADRs, RFCs, GitHub issues, CHANGELOGs, review comments) | ≤25 words/sentence, active voice with named actors, nominalization removal, evidence over adjectives, 60s scannability |
| **Hybrid / Gray Areas** | Architecture reviews, complex diagnostics, proposals with embedded action blocks | Human-Targeted STE for exposition/rationale; Machine-Targeted STE for normative contracts, invariants, action blocks |
| **Lexical vs. Structural Split** | Vocabulary rules vs. Grammar rules | Vocabulary: Rich CS terms allowed; fluff and soft phrasals banned (never use aerospace ~900-word dictionary). Grammar: ≤20 words for procedural instructions vs. ≤25 words for descriptive prose |
