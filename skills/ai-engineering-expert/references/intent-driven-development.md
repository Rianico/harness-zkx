# Intent-Driven Development

Method for turning an ambiguous request into settled intent: read this before the harness implements.

## The Axiom

Intent is an output of collaborative discovery, not a passive input. The user holds a partial picture. The harness holds an inference. Belief about what the user wants is thinner than it feels.

A harness that reads a request as a finished specification mistakes its own inference for the user's intent. The code then satisfies the text and misses the purpose. The user rejects work that met the written request.

Treat the request as evidence. Probe it until the user confirms the intent behind it.

## The Unknown Unknowns Gap

Four gaps separate a request from its intent. Each gap hides work the user did not name.

- **Solution bias**: The user names the mechanism they already pictured, not the friction. Ask what pain the mechanism should remove. The answer often redirects the work.
- **Unexamined blast radius**: The request omits downstream callers, stored state, and other consumers. Inspect the seams before you accept the scope.
- **Latent trade-offs**: Two goals conflict, and the request states only one. Surface both goals and force the priority choice.
- **Specification gaming**: A measurable goal invites optimizing the metric over the purpose. Pair each metric with the outcome it should represent.

## Core Operating Rules

- **Look Before You Ask**: Investigate the environment (code, git history, dependencies) first. Facts belong to the harness. Decisions belong to the user.
- **Excavate Unknown Unknowns**: Match ambiguity to the probing pattern (root-cause drilling, approaches matrix, decision frontiers).
- **Say Defaults Out Loud**: Never leave implicit architectural assumptions unvoiced. A default the user never heard is one they could not reject.
- **The Confirmation Gate**: Settle the **Intent Contract** with explicit human alignment before entering GDD.
- **No Ambiguity Escape Hatch**: The harness MUST probe before proceeding if any ambiguity exists. A task with zero ambiguity proceeds directly.

## The 5 Probing Patterns

Each pattern answers a different shape of ambiguity. Pick the pattern that matches the gap.

### Symptom Inversion and Root-Cause Drilling

Fires when the request names a solution instead of a problem. The harness asks what breaks without the solution, then drills to the structural cause. It proposes the fix against that cause.

Example: "Add a retry" becomes "which failure loses data?" The answer names the real defect.

### Approaches and Trade-Off Matrix

Fires when the ambiguity is broad and several designs could work. The harness presents two or three mutually exclusive approaches. Each option names cost, risk, and fit.

Example: "Cache it" becomes "local cache, shared cache, or no cache?" Each option carries its own cost.

### Decision Frontier and Phased Rounds

Fires when many choices depend on each other. The harness maps them as a tree and asks only the current frontier. Each round is numbered, and each question carries a recommended default.

Example: Round 1 asks the storage choice. Round 2 asks only what that choice unlocks.

### Seam and Invariant Stress-Testing

Fires when the change touches a shared boundary. The harness inspects callers, stored data, and published contracts. It then forces the compatibility choice into the open.

Example: "Rename the field" becomes "do old readers need it?" The answer sets the migration path.

### Negative Scoping and Non-Goals

Fires when scope could grow without limit. The harness names what it will not touch, so the boundary is visible before work starts. The user confirms each exclusion.

Example: "Improve the parser" becomes "not the lexer, not the formatter, not the CLI."

## The Intent Contract

The contract records four parts:

- **Problem**: The concrete deficiency, friction, or regression.
- **Proposed Outcome**: The observable change once the work lands.
- **Affected Seams**: The boundaries, interfaces, and protocols the change touches.
- **Non-Negotiable Constraints**: The invariants, compatibility promises, forbidden patterns, and explicit **Non-Goals**.

Explicit **Non-Goals** name what stays out of scope. The contract is settled when the human has rejected or accepted each default and each non-goal. Then the Confirmation Gate opens.

## Canonical Patterns and References

- `obra/superpowers/brainstorming`: `https://skills.sh/obra/superpowers/brainstorming`. The source pattern asks one question at a time and follows each answer.
- Decision-tree frontier mapping: map dependent choices as a tree, then ask only the frontier. Choices above the frontier are settled. Choices below it wait for their parent.
