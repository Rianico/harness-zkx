---
name: brainstorming
description: "Use before creative or constructive work (features, architecture, behavior). Transforms vague ideas into validated designs through disciplined reasoning and collaboration."
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

### 1️⃣ Understand the Current Context (Mandatory First Step)

Before asking any questions:

- Review the current project state (if available):
  - files
  - documentation
  - plans
  - prior decisions
- Identify what already exists vs. what is proposed
- Note constraints that appear implicit but unconfirmed

**Do not design yet.**

---

### 2️⃣ Understanding the Idea (One Question at a Time)

Your goal here is **shared clarity**, not speed.

**Dialog Contract (use AskUserQuestion tool):**

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

### 3️⃣ Non-Functional Requirements (Mandatory)

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

### 4️⃣ Understanding Lock (Hard Gate)

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

Then ask for confirmation:

```yaml
Dialog:
  header: “Understanding Lock”
  question: “Does this accurately reflect your intent? Please confirm or correct before we move to design.”
  multipleChoice: false
  options:
    - label: “Confirmed”
      description: “Proceed to design exploration”
    - label: “Needs revision”
      description: “Clarify or correct specific items”
    - label: “Other”
      description: “Provide detailed feedback”
```

**Do NOT proceed until explicit confirmation is given.**

---

### 5️⃣ Explore Design Approaches

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

### 6️⃣ Present the Design (Incrementally)

When presenting the design:

- Break it into sections of **200–300 words max**
- After each section, ask for checkpoint confirmation:

```yaml
Dialog:
  header: “Design Checkpoint”
  question: “Does this section look right so far?”
  multipleChoice: false
  options:
    - label: “Continue”
      description: “Proceed to next section”
    - label: “Revise”
      description: “Something needs adjustment”
    - label: “Other”
      description: “Provide specific feedback”
```

Cover, as relevant:

- Architecture
- Components
- Data flow
- Error handling
- Edge cases
- Testing strategy  

---

### 7️⃣ Decision Log (Mandatory)

Maintain a running **Decision Log** throughout the design discussion.

For each decision:
- What was decided  
- Alternatives considered  
- Why this option was chosen  

This log should be preserved for documentation.

---

## After the Design

### 📄 Documentation

Once the design is validated:

- Write the final design to a durable, shared format (e.g. Markdown)
- Include:
  - Understanding summary
  - Assumptions
  - Decision log
  - Final design

Persist the document according to the project’s standard workflow.

---

### 🛠️ Implementation Handoff (Optional)

Only after documentation is complete, ask:

```yaml
Dialog:
  header: “Implementation Handoff”
  question: “Ready to set up for implementation?”
  multipleChoice: false
  options:
    - label: “Yes, proceed”
      description: “Create implementation plan and begin”
    - label: “Not yet”
      description: “Need more design refinement or review”
    - label: “Other”
      description: “Provide specific requirements”
```

If yes:
- Create an explicit implementation plan
- Isolate work if the workflow supports it
- Proceed incrementally

---

## Exit Criteria (Hard Stop Conditions)

You may exit brainstorming mode **only when all of the following are true**:

- Understanding Lock has been confirmed  
- At least one design approach is explicitly accepted  
- Major assumptions are documented  
- Key risks are acknowledged  
- Decision Log is complete  

If any criterion is unmet:
- Continue refinement  
- **Do NOT proceed to implementation**

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
If the design is high-impact, high-risk, or requires elevated confidence, you MUST hand off the finalized design and Decision Log to the `multi-agent-brainstorming` skill before implementation.

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.
