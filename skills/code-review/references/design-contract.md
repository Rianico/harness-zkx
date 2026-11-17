# Design Contract: Multi-Agent Code Review Gate

This document defines the architectural contract for the multi-agent code review gate.

---

## 1. Meta-Governor: Evidence State (`coding-protocol`[^coding-protocol])

All review subagents operate strictly under `coding-protocol` Evidence state.
The orchestrator and subagents hold **judgment authority** only, never **mutation authority**.
No subagent may edit files, implement fixes, or mutate Git state.
Reviewers scale effort by risk and blast radius.
Reviewers ignore whitespace, formatting, syntax, and style issues covered by linters.
Reviewers report only actionable architectural, security, quality, and intent defects.

---

## 2. Review Package Ingestion (`review_package.py`[^superpowers])

Subagents do not explore Git history through manual tool calls.
The orchestrator runs `review_package.py` before dispatching subagents.
This script produces a single consolidated review bundle containing:
- Commit log across the change range.
- Diffstat showing changed files and line modifications.
- Extended context unified diff (`git diff -U10`).
- Target HEAD SHA and diff SHA256 digest.
- Specification or intent contract when provided.

Subagents read the entire bundle in a single tool call.
This eliminates multi-step Git exploration and prevents context drift.

---

## 3. Subagent 1: Spec & Intent Alignment (`spec-intent`)[^mattpocock]

### Mandate
Validates that the change satisfies the requested intent without omissions or scope bloat.
Focuses on behavioral commitments, product requirements, and technical specifications.

### Source of Truth (SOT) Hierarchy
Subagents resolve conflicting intent using this strict precedence order:
1. **Pinned Technical Specification**: PR spec, RFC, ticket specification, or `design.md`.
2. **Issue Tracker Metadata**: Issue description, acceptance criteria, and user story requirements.
3. **Commit Messages**: Explanatory commit headers and body text.

### Degraded Mode (`INCONCLUSIVE`)
When no spec, issue, or clear commit exists, the subagent enters degraded mode.
It infers provisional intent from existing test cases and commit summaries.
Confidence is marked as `LOW`.
The subagent caps the workflow route at `remediate`.
It emits a `[HIGH]` finding: `intent-unverifiable`.
The author must supply an explicit specification before merge.

### Core Checks
- **Missing Requirements**: Mandated behaviors or failure paths omitted from the diff.
- **Scope Creep**: Unrequested architectural refactorings or speculative scaffolding.
- **Incorrect Behavior**: Logic diverging from stated business requirements.

---

## 4. Subagent 2: Code Quality & Structural Boundaries (`quality-boundaries`)[^addy-quality][^addy-simplify][^keel][^programming-expert]

### Mandate
Evaluates implementation quality, test refutability, structural seams, and complexity reduction.
Integrates code simplification while preserving exact runtime behavior.

### Intra-File Quality & Refutability (VDD)
- **Test Refutability**: Every test must fail when underlying behavior breaks.
- **Paper Tiger Rejection**: Reject tests that mock the unit under test (SUT) or assert only `mock.called`.
- **Tautological Assertions**: Reject assertions that evaluate constant truth or mirror inputs directly.
- **Negative Paths**: Verify error handling, timeouts, malformed inputs, and recovery logic.
- **Language Idioms**: Enforce clean idioms, typing constraints, and resource management.

### Inter-Module Structural Seams (`keel`[^keel] Judgment Mode)
- **Dependency Direction**: Enforce Clean Architecture inward dependencies. Domain entities must never import delivery mechanisms.
- **Seam Isolation**: Expose narrow interfaces and data transfer objects across boundary seams.
- **Deep Interfaces (Ousterhout)**: Prefer deep modules with simple interfaces over shallow classes. Avoid "classitis".
- **Behavior Preservation**: Code simplification must preserve exact observable behavior.

### Size Triage Trigger
Line count alone is **never** sufficient for a review finding.
A 200-line cohesive module with a deep interface is superior to ten shallow classes.
Functions exceeding 60 lines or files exceeding 400 lines trigger structural triage.
The reviewer inspects large units for single-responsibility violations, state leakage, and hidden coupling.
Reviewers flag structural defects only when substantive coupling or state issues exist.

---

## 5. Subagent 3: Security & Hardening (`security-hardening`)[^addy-security]

### Mandate
Applies threat modeling and vulnerability scanning across trust boundaries.
Ensures systems fail closed and protect sensitive data.

### Threat Modeling (STRIDE)
- **Spoofing**: Validate caller identity across process and network boundaries.
- **Tampering**: Validate payload signatures, checksums, and immutable state.
- **Repudiation**: Ensure audit logs record security-critical events.
- **Information Disclosure**: Prevent secret leaks, debug dumps, and over-permissive API returns.
- **Denial of Service**: Verify timeouts, resource limits, unbounded memory allocations, and backpressure.
- **Elevation of Privilege**: Check authorization, permission checks, and token scopes.

### Critical Security Invariants
- **Input Validation**: Validate untrusted inputs at boundary entry before passing inward.
- **Injection Defense**: Enforce parameterized queries, sanitized shell executions, and safe templates.
- **Fail-Closed Concurrency**: Rate limits, quotas, and authorization checks must fail closed during outages.
- **LLM Safety**: Sanitize prompts, guard tool invocations, and validate generated outputs before execution.

---

## 6. Synthesis, Deduplication, and Tie-Break Protocol

### Parallel Execution & Side-by-Side Reporting
The orchestrator dispatches all three subagents in parallel.
Each subagent produces findings under its distinct heading.
Findings from one axis cannot mask or offset findings from another axis.

### Deduplication
The orchestrator deduplicates overlapping findings targeting identical `file:line` locations.
When findings share a location and invariant, the higher severity survives.

### Tie-Break Precedence
When competing priorities conflict, the orchestrator applies strict precedence:
1. **Spec & Intent Alignment** (highest priority: solving the wrong problem invalidates all code).
2. **Security & Hardening** (system compromise overrides structural elegance).
3. **Structural Boundaries & Seams** (architectural rot compromises long-term health).
4. **Code Quality & Standards** (local idiom improvements yield to higher-order concerns).

---

## 7. Severity Taxonomy & Routing Rules

### Severity Levels
- **`[BLOCKING]` (P1)**: Critical defect causing gate failure. Includes contract breaks, fake mocks, security holes, and spec contradictions.
- **`[HIGH]` (P2)**: Must-fix issue. Includes architectural leaks, design drift, state corruption risk, and unverified intent in degraded mode.
- **`[INFO]` (P3)**: Advisory observation. Includes ratchet improvements or benign cleanup opportunities. Does not block merge.

### Route Classification
- `Route: continue`: Quality score $\ge 8$, zero `BLOCKING` or `HIGH` issues, intent verified, SOT in sync.
- `Route: remediate`: Quality score $< 8$, any `BLOCKING` or `HIGH` defect, or material intent drift.
- `Route: blocked`: Low quality score ($\le 4$) with multiple blocking flaws or irrecoverable specification contradictions.

---

## Footnote References

[^mattpocock]: https://github.com/mattpocock/skills/blob/main/skills/engineering/code-review/SKILL.md
[^addy-quality]: https://github.com/addyosmani/agent-skills/tree/main/skills/code-review-and-quality
[^addy-simplify]: https://github.com/addyosmani/agent-skills/tree/main/skills/code-simplification
[^addy-security]: https://github.com/addyosmani/agent-skills/tree/main/skills/security-and-hardening
[^superpowers]: https://github.com/obra/superpowers/tree/main/skills/subagent-driven-development/scripts/review-package
[^keel]: skills/keel/SKILL.md
[^coding-protocol]: skills/coding-protocol/SKILL.md
[^programming-expert]: skills/programming-expert/SKILL.md
