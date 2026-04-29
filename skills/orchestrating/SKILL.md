---
name: orchestrating
description: Orchestrate multi-step LSZ workflows for feature development, refactors, bug fixes, and documentation updates. Defines the skill sequence across brainstorming, architect, plan, eval, TDD, build-fix, update-docs, and code-review, with approval checkpoints, shared topic roots, remediation loops, final review behavior, and pointer-based state passing.
argument-hint: "[feature|refactor|bugfix|docs]"
---

# Orchestration

You have invoked the Orchestration Workflow Skill. This skill defines the strict sequence of LSZ skills you must execute to complete complex software engineering tasks.

## Orchestration Rules
1. **Skill Execution, Not Bare Agents:** You MUST NOT invoke the `Agent` tool directly unless instructed by a specific skill's execution rules. Instead, load the phase skill via the `Skill` tool, then execute its workflow exactly as written.
2. **Sequential Execution:** You must execute the skills in the exact order specified by the pipeline.
3. **Pointer-Based State Passing:** Pass approved artifact pointers between skills instead of restating prior artifacts in prose. Each downstream phase should receive only the upstream pointers it is expected to consume.
4. **Interactive Approval Propagation:** By executing skills rather than bare agents, you naturally inherit their interactive approval loops. You MUST honor these user interaction prompts and handle user feedback exactly as defined in the skill's instructions before proceeding to the next step in the pipeline.
5. **Shared Topic Root:** For a multi-phase workflow on the same topic, create `[topic_root] = .lsz/$(date +%Y%m%d)/$(date +%H%M%S)_[short_topic]` once at the start of the workflow, then pass it downstream as an explicit `topic_root=<path>` override. Downstream workflow skills own their standalone defaults and MUST treat the orchestrated topic root as a caller override.
6. **Strict Phase Ownership:** Preserve distinct responsibilities across phases. Architect defines decisions and boundaries. Plan defines execution order and scope. TDD defines tests and implementation validation. Code review defines repository-level review and readiness.
7. **No Redundant Re-encoding:** Do not ask a downstream phase to recreate an upstream artifact as a rewritten checklist, summary, or review unless that transformation is the explicit purpose of the phase.
8. **Topic-Root Source of Truth Exception:** `design.md` may live directly at `[topic_root]/design.md` because it is the mission-level source of truth, not a workflow-specific artifact directory. Workflow phase artifacts still belong under `[topic_root]/{workflow_kind}/` unless `artifact_dir=<path>` overrides them.
9. **Domain Context Injection:** When a phase skill's execution instructions require launching an agent or passing state, prepend concise domain context to the task prompt, then pass only approved upstream pointers relevant to that phase.
10. **Eval Gate Remediation:** If `eval check` is not READY, return to `tdd-cycle` remediation with pointers to the source of truth, eval definition, eval log, and implementation artifacts. Do not proceed to `code-review` until required evals pass or the workflow explicitly stops as blocked.
11. **Final Review Remediation:** When `code-review` is the final phase, invoke it with `orchestrated_final_review=true`. Safe `medium`, `low`, or `minor` findings should be delegated for remediation without asking the user first. Ask for approval only when findings are `blocking`, `high`, security-critical, destructive, risky to fix, or require a product or architecture decision.

Use this prompt shape when injecting domain context:

```text
**[DOMAIN CONTEXT]**
Language/Domain: [e.g., Rust]
Root File: [e.g., Cargo.toml]

**[APPROVED UPSTREAM POINTERS]**
[Include only absolute file path pointers the next phase is expected to consume]

**[TASK]**
[Task summary and user requirements]
```

## Phase Ownership Contract
- `brainstorming` owns requirement discovery: source-of-truth design capture, examples, negative requirements, acceptance criteria, assumptions, and open questions.
- `architect` owns decisions: problem framing, boundaries, invariants, interfaces, trade-offs, risks, and rejected alternatives.
- `plan` owns execution: ordered steps, dependency sequencing, touched modules, checkpoints, risks, and explicit out-of-scope items.
- `eval define` owns acceptance checks: converting the approved source of truth into reviewed capability, contract, negative, and regression evals.
- `tdd-cycle` owns implementation validation: tests, implementation progress, and implementation-level verification needed to complete the change.
- `eval check` owns spec-compliance verification: checking the implementation against the approved eval definition and producing pass/fail logs.
- `code-review` owns repository-level review: security, maintainability, correctness gaps not covered by TDD/evals, and overall readiness.

## Standard Pipelines

To execute a step, load the corresponding Skill (e.g., `skill="architect"`) and follow its execution contract.

### 0. Pre-implementation (Research & Reuse)
*Mandatory before any new implementation unless the task is a narrow bugfix with an already reproduced failure.*
- **GitHub code search first:** Run `gh search repos` and `gh search code` to find existing implementations, templates, and patterns.
- **Library docs second:** Use Context7 or vendor docs to confirm API behavior.
- **Search package registries:** npm, PyPI, crates.io, etc.
- **Tavity only when insufficient:** Use `websearch-tavity` skill for broader web research.
- Prefer adopting or porting a proven approach over writing net-new code.

### 1. Feature Pipeline (`args="feature|refactor"`)
- **Step 1:** `brainstorming` (Load skill: `brainstorming`) - *Create `[topic_root]` once for the topic. The phase MUST produce `[topic_root]/design.md` as the source of truth before implementation. The design must include understanding summary, assumptions, non-functional requirements, decision log, behavior specification, output examples or golden examples, negative requirements, acceptance criteria, and open questions.*
- **Step 2:** `architect` (Load skill: `architect`) - *Pass the approved `design.md` pointer and `topic_root=[topic_root]` override. This phase records the architecture decision for feature/refactor work as an ADR. It must preserve the design contract and record trade-offs, boundaries, invariants, and rejected alternatives only.*
- **Step 3:** `plan` (Load skill: `plan`) - *Pass the approved `design.md`, approved ADR pointer, and `topic_root=[topic_root]` override. This phase converts the design and ADR into an execution plan without weakening or reinterpreting acceptance criteria.*
- **Step 4:** `eval define` (Load skill: `eval`) - *Pass the approved `design.md`, ADR, execution plan, and `topic_root=[topic_root]` override. The eval definition must be derived from `design.md`, include concrete capability checks, regression checks, negative requirements, and golden examples where present, then stop for explicit user review and approval before implementation begins.*
- **Step 5:** `tdd-cycle` (Load skill: `tdd-cycle`) - *Pass the approved execution plan, approved eval definition, approved `design.md`, and `topic_root=[topic_root]` override into the TDD orchestrator. This phase owns tests, implementation, and implementation-level verification only.*
- **Step 6:** `eval check` (Load skill: `eval`) - *Run the approved eval definition against the implementation. If all required evals pass, continue to code review. If any eval fails, return to `tdd-cycle` with pointers to `design.md`, the eval definition, the eval failure log, and the current implementation summary. Retry remediation at most twice before stopping and surfacing the blocker.*
- **Step 7:** `code-review` (Load skill: `code-review`) - *Pass `topic_root=[topic_root]`, `orchestrated_final_review=true`, approved upstream artifact pointers, and eval pass log. This is the repository-level review gate for security, maintainability, broader correctness gaps, and overall readiness after implementation and eval verification. In this final orchestrated review, safe `medium`, `low`, or `minor` findings should be delegated for remediation without a user approval checkpoint; ask the user only for `blocking`, `high`, security-critical, destructive, risky, or decision-requiring findings.*

### 2. Bugfix Pipeline (`args="bugfix"`)
- **Step 1:** `tdd-cycle` (Load skill: `tdd-cycle`) - *Create `[topic_root]` once for the topic, then pass `topic_root=[topic_root]` and use incremental mode to write a failing test for the bug and fix it.*
- **Step 2:** `build-fix` (Load skill: `build-fix`) - *Execute ONLY IF the bug involves compilation/build failures that TDD couldn't resolve.*
- **Step 3:** `eval check` (Load skill: `eval`) - *Execute if an eval already exists for the affected behavior or if the bugfix changes an externally visible contract. A failing eval returns to `tdd-cycle` remediation with the eval failure log. Do not create a new ADR for ordinary bugfixes.*
- **Step 4:** `architect` escalation (Load skill: `architect`) - *Execute ONLY IF the bugfix changes architecture, public contracts, data models, policy, or long-lived behavior. In that case, pass `topic_root=[topic_root]` to create the ADR under the shared topic root, then update the plan/eval pointers before continuing.*
- **Step 5:** `code-review` (Load skill: `code-review`) - *Pass `topic_root=[topic_root]`, `orchestrated_final_review=true`, plus any test, build, eval, or ADR pointers created during the fix. In this final orchestrated review, safe `medium`, `low`, or `minor` findings should be delegated for remediation without a user approval checkpoint; ask the user only for `blocking`, `high`, security-critical, destructive, risky, or decision-requiring findings.*

### 3. Documentation Pipeline (`args="docs"`)
- **Step 1:** `update-docs` (Load skill: `update-docs`) - *Create `[topic_root]` once for the topic, then pass `topic_root=[topic_root]`.*
- **Step 2:** `code-review` (Load skill: `code-review`) - *Pass `topic_root=[topic_root]` and `orchestrated_final_review=true`. Document-only work normally does not require ADR or eval unless it changes a normative workflow contract. In this final orchestrated review, safe `medium`, `low`, or `minor` findings should be delegated for remediation without a user approval checkpoint; ask the user only for `blocking`, `high`, security-critical, destructive, risky, or decision-requiring findings.*
