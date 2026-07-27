---
name: brainstorming
description: >-
  Design ideation and validation for features, architecture, or behavior. Transforms vague ideas into validated designs through disciplined reasoning. Maintains CONTEXT.md glossary inline. Use --peer-review for high-impact designs needing multi-agent validation.
argument-hint: |-
  [--peer-review]
metadata:
  depends-on: [handoff]
---

# Brainstorming Ideas Into Designs

## Purpose

Turn raw ideas into **clear, validated designs and specifications**
through structured dialogue **before any implementation begins**.

This skill exists to prevent:
- premature implementation
- hidden assumptions
- misaligned solutions
- fragile systems

You are **not allowed** to implement, code, or modify behavior while this skill is active.

---

## Operating Mode

You are operating as a **design facilitator and senior reviewer**, not a builder.

- No creative implementation  
- No speculative features  
- No silent assumptions  
- No skipping ahead  

Your job is to **slow the process down just enough to get it right**.

---

## The Process

### 1. Understand the Current Context (Mandatory First Step)

Before asking any questions:

- Review the current project state (if available):
  - files
  - documentation
  - plans
  - prior decisions
- Read `CONTEXT.md` (or `CONTEXT-MAP.md` if it exists) to extract canonical domain terminology
- Read relevant ADRs from `docs/adr/` that touch the area being designed
- Identify what already exists vs. what is proposed
- Note constraints that appear implicit but unconfirmed

If the user's language drifts from the glossary, flag it immediately: "Your glossary defines X as Y, but you seem to mean Z — which is it?"

**Do not design yet.**

---

### 2. Understanding the Idea (One Question at a Time)

Your goal here is **shared clarity**, not speed.

**Dialog Contract (present as plain text):**

```yaml
Dialog:
  header: "<investigation topic>"
  question: "<single focused question?>"
  multipleChoice: false
  options:
    - label: "<option A>"
      description: "<implication of A>"
    - label: "<option B>"
      description: "<implication of B>"
    - label: "Other"
      description: "Provide custom input"
```

**Rules:**

- One question per dialog
- 2-4 options max (plus "Other" for custom input)
- Set `multipleChoice: true` only when options are truly independent
- Provide clear descriptions explaining tradeoffs
- Use open-ended questions only when options cannot be anticipated

Focus on understanding:

- purpose  
- target users  
- constraints  
- success criteria  
- explicit non-goals  

---

### 3. Non-Functional Requirements (Mandatory)

You MUST explicitly clarify or propose assumptions for:

- Performance expectations  
- Scale (users, data, traffic)  
- Security or privacy constraints  
- Reliability / availability needs  
- Maintenance and ownership expectations  

If the user is unsure:

- Propose reasonable defaults  
- Clearly mark them as **assumptions**

---

### 4. Understanding Lock (Hard Gate)

Before proposing **any design**, you MUST pause and do the following:

#### Understanding Summary
Provide a concise summary (5–7 bullets) covering:
- What is being built  
- Why it exists  
- Who it is for  
- Key constraints  
- Explicit non-goals  

#### Assumptions
List all assumptions explicitly.

#### Open Questions
List unresolved questions, if any.

#### Domain Terminology
Surface the canonical terms from `CONTEXT.md` that are relevant to this design. If the user has used terms that conflict with or are absent from the glossary, call it out here. If new terms were introduced during the interview, note them for glossary update.

Then ask for confirmation:

```yaml
Dialog:
  header: "Understanding Lock"
  question: "Does this accurately reflect your intent? Please confirm or correct before we move to design."
  multipleChoice: false
  options:
    - label: "Confirmed"
      description: "Proceed to design exploration"
    - label: "Needs revision"
      description: "Clarify or correct specific items"
    - label: "Other"
      description: "Provide detailed feedback"
```

**Do NOT proceed until explicit confirmation is given.**

---

### 5. Explore Design Approaches

Once understanding is confirmed:

- Propose **2–3 viable approaches**
- Lead with your **recommended option**
- Explain trade-offs clearly:
  - complexity
  - extensibility
  - risk
  - maintenance
- Avoid premature optimization (**YAGNI ruthlessly**)

**Dialog Contract for approach selection:**

```yaml
Dialog:
  header: "Design Approach"
  question: "Which approach should we pursue?"
  multipleChoice: false
  options:
    - label: "<Approach A> (Recommended)"
      description: "<tradeoffs and implications>"
    - label: "<Approach B>"
      description: "<tradeoffs and implications>"
    - label: "Hybrid/Other"
      description: "Combine elements or propose alternative"
```

This is still **not** final design.

---

### 6. Present the Design (Incrementally)

When presenting the design:

- Break it into sections of **200–300 words max**
- After each section, ask for checkpoint confirmation:

```yaml
Dialog:
  header: "Design Checkpoint"
  question: "Does this section look right so far?"
  multipleChoice: false
  options:
    - label: "Continue"
      description: "Proceed to next section"
    - label: "Revise"
      description: "Something needs adjustment"
    - label: "Other"
      description: "Provide specific feedback"
```

Cover, as relevant:

- Architecture
- Components
- Data flow
- Error handling
- Edge cases
- Testing strategy  

---

### 7. Decision Log (Mandatory)

Maintain a running **Decision Log** throughout the design discussion.

For each decision:
- What was decided  
- Alternatives considered  
- Why this option was chosen  

This log should be preserved for documentation.

---
### 8. Behavioral Specification (BDD) (Mandatory Before Documentation)

Before finalizing any design, you MUST present **concrete behavioral specifications** using BDD (Behavior-Driven Development) syntax. This ensures the design is validated through human-readable scenarios that clarify intent better than raw code or abstract diagrams.

#### Required Scenario Types

Present at least **2-3 scenarios** using the **Given / When / Then** format, covering:

1. **Happy Path** - The primary use case working as intended.
2. **Edge Case** - Boundary conditions, unusual inputs, or scale limits.
3. **Error Scenario** - How the system behaves when things go wrong.

#### BDD Format

Each scenario MUST include:

```markdown
**Scenario: <descriptive name>**

**Given** <the initial state of the system and context>
**When** <the user or system performs a specific action>
**Then** <the observable behavior or result that should occur>

**Rationale:** <briefly explain which design decisions this validates>
```

#### Confirmation Dialog

After presenting BDD scenarios, ask for explicit confirmation:

```yaml
Dialog:
  header: "BDD Validation"
  question: "Do these behavioral scenarios accurately capture the intended design?"
  multipleChoice: false
  options:
    - label: "Confirmed"
      description: "Scenarios align with intent, proceed to documentation"
    - label: "Needs adjustment"
      description: "Scenarios don't match expected behavior"
    - label: "Add more scenarios"
      description: "Need additional behaviors covered"
    - label: "Other"
      description: "Provide specific feedback"
```

**Do NOT proceed to documentation until BDD scenarios are confirmed.**

If scenarios reveal design gaps:
- Return to step 5 (Explore Design Approaches) or step 6 (Present the Design)
- Update the design to address gaps
- Re-present scenarios with fixes

---

## After the Design

### Documentation

Once the design AND BDD scenarios are validated:

- Write the final design to a durable, shared format (e.g. `design.md`)
- Include:
  - Understanding summary
  - Assumptions
  - Decision log
  - Final design
  - Behavioral Specification (BDD)

Persist the document according to the project's standard workflow.


---

### Glossary Maintenance (Mandatory)

If the design introduced, resolved, or clarified domain terms:

- Update `CONTEXT.md` **inline** — don't batch term changes
- Use the format defined in `$SKILL_DIR/references/context-format.md`
- Be opinionated: pick the canonical term, list synonyms to avoid
- Keep definitions tight: what it IS, not what it does
- If `CONTEXT.md` doesn't exist yet, create it lazily with the first resolved term

---

### Implementation Handoff (Optional)

Only after documentation is complete, ask:

```yaml
Dialog:
  header: "Implementation Handoff"
  question: "Ready to set up for implementation?"
  multipleChoice: false
  options:
    - label: "Yes, proceed"
      description: "Invoke the handoff skill to prepare for implementation"
    - label: "Not yet"
      description: "Need more design refinement or review"
    - label: "Other"
      description: "Provide specific requirements"
```

If yes:
1. **Handoff Intent**: Invoke the `handoff` skill with `artifacts=[topic_root]/design.md` to distill the decisions, designs, and user intent.
2. **Handoff Document**: Provide the path to the `handoff.md` artifact. This document acts as the high-signal bridge, potentially displacing the need for the next agent to immediately re-read the full `design.md`.
3. **Transition**: Suggest the next implementation step (e.g., `tdd-cycle`) using the handoff pointer.


---

## Context Management (Compaction)

Brainstorming sessions are often turn-intensive. If you notice the conversation history becoming large or the model becoming slow:

- **Artifact Finalization**: Ensure the `design.md` and `handoff.md` are fully written to disk. These are your state recovery artifacts.
- **Compaction Recommendation**: Suggest the user run the `/compact` command to reset the context window.
- **State Recovery**: Inform the user that they can resume from the current state by pointing a fresh agent to the generated artifacts (specifically `handoff.md` and `design.md`).

---

## Exit Criteria (Hard Stop Conditions)

You may exit brainstorming mode **only when all of the following are true**:

- Understanding Lock has been confirmed  
- At least one design approach is explicitly accepted  
- Design examples have been presented AND confirmed  
- Major assumptions are documented  
- Key risks are acknowledged  
- Decision Log is complete  

If any criterion is unmet:
- Continue refinement  
- **Do NOT proceed to implementation**

---

## 9. Complexity Classification (Mandatory Output)

After the design is validated, you MUST classify the task complexity for orchestration routing.

### Output Locations

1. **Design.md frontmatter** - Add `complexity` field:
   ```markdown
   ---
   complexity: lightweight | heavy
   ---
   ```

2. **Return value** - Include classification in your handoff response:
   ```
   Design: [path]
   Complexity: lightweight | heavy
   Rationale: <brief reason>
   ```

### Classification Heuristics

**Lightweight if ALL are true:**
- Single module/function scope
- No cross-module dependencies
- No interface/contract changes (or trivial additions only)
- Easy to verify with tests
- No security/performance implications

**Heavy if ANY is true:**
- Multi-module impact
- Interface/contract changes to existing APIs
- Data model/schema changes
- Security or performance implications
- Hard-to-verify behavior (async, distributed, non-deterministic)

### Complexity Transformation

Complexity can change during brainstorming:
- **Simple to Complex**: Discovery of hidden dependencies, security implications, or architectural impact
- **Complex to Simple**: Discovery of elegant solution that reduces scope

When complexity changes, re-evaluate and update classification before finalizing.

### Default Behavior

When uncertain, classify as **heavy**. The cost of extra architecture review is lower than the cost of skipping it when needed.

---

## Peer Review Escalation (--peer-review)

For high-impact, high-risk, or elevated-confidence designs, escalate to **peer review mode**.

### When to Escalate

Escalate to `--peer-review` when:
- Design has significant architectural impact
- Failure would be costly (revenue, safety, user trust)
- Security or compliance implications exist
- Multiple non-functional constraints are in tension
- Stakeholder alignment is critical

### Peer Review Process (3 Phases)

**Phase 1: Single-Agent Design**
- Complete the standard brainstorming process (Steps 1-9)
- Understanding Lock confirmed
- Initial design produced
- Decision Log started

**Phase 2: Structured Review Loop**
- Reviewers invoked sequentially: Skeptic, Constraint Guardian, User Advocate
- Each reviewer provides scoped feedback
- Primary Designer responds to objections and revises

**Phase 3: Integration & Arbitration**
- Arbiter reviews design, Decision Log, and unresolved objections
- Arbiter accepts/rejects objections with rationale
- Design declared complete or returned for revision

### Detailed Roles and Process

See `$SKILL_DIR/references/peer-review-roles.md` for:
- Full role definitions (Primary Designer, Skeptic, Constraint Guardian, User Advocate, Arbiter)
- May/May NOT mandates for each role
- Phase 2 and Phase 3 process details
- Decision Log requirements

### Peer Review Exit Criteria

You may exit peer review mode **only when all are true**:

- Understanding Lock was completed
- All reviewer agents have been invoked
- All objections are resolved or explicitly rejected
- Decision Log is complete
- Arbiter has declared the design acceptable

If invoked by orchestration, report disposition: **APPROVED**, **REVISE**, or **REJECT** with rationale.

---

## Key Principles (Non-Negotiable)

- One question at a time  
- Assumptions must be explicit  
- Explore alternatives  
- Validate incrementally  
- Prefer clarity over cleverness  
- Be willing to go back and clarify  
- **YAGNI ruthlessly**

---

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.
