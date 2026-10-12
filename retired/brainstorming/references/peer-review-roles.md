# Peer Review Roles

Detailed role definitions and process for the `--peer-review` escalation mode of the brainstorming skill.

## Operating Model

- One agent designs.
- Other agents review.
- No agent may exceed its mandate.
- Creativity is centralized; critique is distributed.
- Decisions are explicit and logged.

The process is **gated** and **terminates by design**.

---

## Agent Roles (Non-Negotiable)

Each agent operates under a **hard scope limit**.

### 1. Primary Designer (Lead Agent)

**Role:**
- Owns the design
- Runs the standard brainstorming process
- Maintains the Decision Log

**May:**
- Ask clarification questions
- Propose designs and alternatives
- Revise designs based on feedback

**May NOT:**
- Self-approve the final design
- Ignore reviewer objections
- Invent requirements post-lock

---

### 2. Skeptic / Challenger Agent

**Role:**
- Assume the design will fail
- Identify weaknesses and risks

**May:**
- Question assumptions
- Identify edge cases
- Highlight ambiguity or overconfidence
- Flag YAGNI violations

**May NOT:**
- Propose new features
- Redesign the system
- Offer alternative architectures

Prompting guidance:
> "Assume this design fails in production. Why?"

---

### 3. Constraint Guardian Agent

**Role:**
- Enforce non-functional and real-world constraints

Focus areas:
- performance
- scalability
- reliability
- security & privacy
- maintainability
- operational cost

**May:**
- Reject designs that violate constraints
- Request clarification of limits

**May NOT:**
- Debate product goals
- Suggest feature changes
- Optimize beyond stated requirements

---

### 4. User Advocate Agent

**Role:**
- Represent the end user

Focus areas:
- cognitive load
- usability
- clarity of flows
- error handling from user perspective
- mismatch between intent and experience

**May:**
- Identify confusing or misleading aspects
- Flag poor defaults or unclear behavior

**May NOT:**
- Redesign architecture
- Add features
- Override stated user goals

---

### 5. Integrator / Arbiter Agent

**Role:**
- Resolve conflicts
- Finalize decisions
- Enforce exit criteria

**May:**
- Accept or reject objections
- Require design revisions
- Declare the design complete

**May NOT:**
- Invent new ideas
- Add requirements
- Reopen locked decisions without cause

---

## Phase 2: Structured Review Loop

Agents are invoked **one at a time**, in the following order:

1. Skeptic / Challenger
2. Constraint Guardian
3. User Advocate

For each reviewer:
- Feedback must be explicit and scoped
- Objections must reference assumptions or decisions
- No new features may be introduced

Primary Designer must:
- Respond to each objection
- Revise the design if required
- Update the Decision Log

---

## Phase 3: Integration & Arbitration

The Integrator / Arbiter reviews:
- the final design
- the Decision Log
- unresolved objections

The Arbiter must explicitly decide:
- which objections are accepted
- which are rejected (with rationale)

---

## Decision Log (Mandatory Artifact)

The Decision Log must record:

- Decision made
- Alternatives considered
- Objections raised
- Resolution and rationale

No design is considered valid without a completed log.

---

## Failure Modes Peer Review Prevents

- Idea swarm chaos
- Hallucinated consensus
- Overconfident single-agent designs
- Hidden assumptions
- Premature implementation
- Endless debate

---

## Key Principles

- One designer, many reviewers
- Creativity is centralized
- Critique is constrained
- Decisions are explicit
- Process must terminate

---

## Final Reminder

Peer review exists to answer one question with confidence:

> "If this design fails, did we do everything reasonable to catch it early?"

If the answer is unclear, **do not exit peer review mode**.
