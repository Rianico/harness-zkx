# Glossary — Skill Authoring

The domain model for what makes a skill great, extended with LSZ context-load policy terms. A skill exists to wrangle determinism out of a stochastic system; the root virtue is **Predictability**.

Terms are grouped by axis: **Invocation**, **Information Hierarchy**, **Steering**, **Pruning**, and **Context-Load Policy**.

## Predictability

The degree to which a skill makes the agent behave the same _way_ on every run — the same process, not the same output. The root virtue every other term serves.
_Avoid_: Consistency, reliability, robustness, output-determinism.

## Invocation

### Model-Invoked

A skill that keeps its `description` field and omits `disable-model-invocation`, so the agent can see it and fire it autonomously. Model-invocation always _includes_ user reach — the human can still type its name. Pays a permanent **context load** on every turn.
_Avoid_: Ability, tool, capability.

### User-Invoked

A skill with `disable-model-invocation: true` — invisible to the agent's autonomous selection and reachable only by the human typing its name or another skill invoking `$skill`. Still pays **context load** for its description in the initial metadata list (the description is always present regardless of invocation class).
_Avoid_: Procedure, workflow, command.

### Description

The skill's machine-readable trigger. Its mere presence _is_ the invocation axis: omit `disable-model-invocation` and the skill is model-invoked; set it to `true` and the skill is user-invoked. The source of a model-invoked skill's context load, and always present in the initial skill-list metadata.
_Avoid_: Frontmatter, summary.

### Description Budget

The adopted character limit (300 chars) for a skill `description`, enforced by `validate-deps.py context-check`. Rationale: Codex budgets 8,000 chars for the global initial list, shortening descriptions before omitting skills.
_Avoid_: Description length, char limit.

### Context Pointer

A reference held in the agent's context that names out-of-context material and encodes the condition for reaching it. The description is the top-level context pointer (context window → skill); pointers to disclosed files are the same object one level down.
_Avoid_: Link, reference, import.

### Context Load

The permanent token and attention cost a skill's `description` imposes on every turn by sitting in the initial skill-list metadata. Paid regardless of invocation class — even user-invoked skills contribute their description to the initial list.
_Avoid_: Token cost, context bloat.

### Cognitive Load

The cost a user-invoked skill imposes on the human — what they must hold in their head: which skills exist and when to reach for each. What model-invocation removes by being agent-discoverable. Not a cost to minimise: it is the price of human agency.
_Avoid_: Human index, burden, overhead.

### Router Skill

A user-invoked skill whose job is to point at other user-invoked skills — naming each and when to reach for it — so the human has one skill to remember instead of many.
_Avoid_: Dispatcher, menu, registry, index.

### Granularity

How finely you divide skills. Finer division spends one of two loads: more model-invoked skills spend context load; more user-invoked skills spend cognitive load.
_Avoid_: Chunking, modularity.

### Invocation Class

Whether a skill is reachable by model inference (`implicit-allowed`) or only by explicit name (`explicit-only`). Declared via the canonical `disable-model-invocation` field. Controls selection, not metadata presence.
_Avoid_: Invocation mode, trigger mode.

### Selection Mode

How the runtime decides to load a skill: autonomously (description match) or by name (user types `$skill` or another skill invokes it). Distinct from metadata cost.
_Avoid_: Discovery mode, pick mode.

### Metadata Cost

The context consumed by a skill's name and description being listed in the initial available-skills inventory. Paid even when implicit invocation is disabled. The key principle: selection ≠ metadata cost.
_Avoid_: Listing cost, inventory cost.

## Information Hierarchy

### Information Hierarchy

A skill's content ranked by how immediately the agent needs it. The rungs: steps (in-file, primary), reference (in-file, secondary), reference (disclosed, behind a context pointer). The 80/20 principle governs placement.
_Avoid_: Structure, organization, layout.

### Steps

The ordered actions the agent performs — when a skill has them, the primary tier of its content. Every step ends on a completion criterion.
_Avoid_: Workflow, instructions, choreography.

### Reference

Material the agent refers to on demand — definitions, facts, parameters, examples. When a skill has steps it is secondary to them; when a skill has none it is the entire content.
_Avoid_: Supporting material, docs, background.

### External Reference

Reference that lives outside the skill system — a plain file, no description, no steps — that any skill can point at. The home for shared reference that needn't fire on its own.
_Avoid_: Doc, resource, knowledge base.

### Progressive Disclosure

Moving reference down the ladder — out of SKILL.md and behind a context pointer — so the top stays legible. Licensed by branching: disclose what only some branches need, inline what every path needs.
_Avoid_: Lazy loading, chunking.

### Co-location

Keeping the material an agent needs at once in one place — a concept's definition, rules, and caveats under a single heading — so reading one part brings its neighbours with it.
_Avoid_: Grouping, clustering, cohesion.

### 80/20 Principle

A recursive content-architecture rule: a SKILL.md holds the 20% of knowledge that solves 80% of problems; references hold the deep 80%. Applied at every level — parent spine, subskills, and subskill references.
_Avoid_: Pareto content, essential-first.

### Sprawl

_Failure mode._ A skill that is simply too long — even an all-live, all-unique skill can sprawl. The cure is the information hierarchy: push reference down behind pointers, split by branch or sequence.
_Avoid_: Bloat, length, size, verbosity.

## Steering

### Branch

A distinct way a skill can be invoked — a case the skill handles — so different runs take different paths through it.
_Avoid_: Path, case, fork.

### Leading Word

A compact concept already living in the model's pretraining that the agent thinks with while running the skill. It encodes a behavioural principle in the fewest possible tokens by invoking priors the model already holds (e.g. _lesson_, _tracer bullets_). Serves predictability twice: in the body it anchors execution; in the description it anchors invocation.
_Avoid_: Keyword, term, motif.

### Completion Criterion

The condition that tells the agent a unit of work is done. Two properties: clarity (can the agent tell done from not-done?) and demand (how much legwork does it require?).
_Avoid_: Done condition, exit condition, stopping rule.

### Legwork

The work an agent does behind the scenes within a single step — reading files, exploring the codebase, digging up what it needs rather than offloading to the user.
_Avoid_: Scope, effort, diligence, coverage.

### Post-Completion Steps

The steps that follow the current step. Visible, they pull the agent forward into premature completion; the defence is to hide them by splitting.
_Avoid_: Horizon, fog of war, lookahead.

### Premature Completion

_Failure mode._ Ending the current step before it is genuinely done, because the agent's attention slips to being done rather than to the work. A tug-of-war between visible post-completion steps and the completion criterion's clarity.
_Avoid_: Premature closure, the rush, rushing, shortcutting.

### Negation

_Failure mode._ Steering by prohibition — telling the agent what _not_ to do — which drags the forbidden behaviour into context and makes it _more_ available. Cure: prompt the positive.
_Avoid_: Ironic rebound, don't-prompting, the pink elephant.

## Pruning

### Single Source of Truth

The desired state where each meaning lives in exactly one authoritative place, so a change to the skill's behaviour is a change in one place.
_Avoid_: Home, canonical location.

### Duplication

_Failure mode._ The same meaning given more than one single source of truth. Costs maintenance, tokens, and inflates prominence past its real rank.
_Avoid_: Repetition, redundancy.

### Relevance

Whether a line still bears on what the skill does — the lens for what to keep. Distinct from no-op: relevance asks whether a line bears on the task, not whether it changes behaviour.
_Avoid_: Load-bearing, staleness, freshness.

### Sediment

_Failure mode._ Layers of old content that settle in a skill and are never cleared, because adding feels safe and removing feels risky. The default fate of any skill without a pruning discipline.
_Avoid_: Accretion, bloat, cruft, rot.

### No-Op

_Failure mode._ An instruction that changes nothing because the model already does it by default — you pay load to tell the agent what it would do anyway. The test: does a line change behaviour versus the default?
_Avoid_: Redundant instruction, restating the obvious, belaboring.

## Context-Load Policy

### Static Guard

A CI-time script (`validate-deps.py context-check`) that parses every `SKILL.md` and enforces hard gates (description presence, budget) and soft warnings (trigger vocabulary). Deterministic — no AI needed.
_Avoid_: Linter, validator.

### Runtime Trace

A recorded invocation log from a Codex surface proving that explicit-only skills are not implicitly loaded but remain explicitly reachable via `$skill`. Manual validation, not automated in CI.
_Avoid_: Invocation receipt, trace log.

### Platform Adapter

A script-generated mapping from Claude Code canonical frontmatter to a target platform's mechanism (e.g., `disable-model-invocation: true` → `allow_implicit_invocation: false` in `agents/openai.yaml`). Always regenerated from canonical source.
_Avoid_: Sync layer, shim.

### Compatibility Field

A frontmatter key recognized by one platform (e.g., `disable-model-invocation` for Claude Code) that has no defined semantics in another target runtime. Must be paired with the supported platform mechanism via sync.
_Avoid_: Legacy field, foreign key.
