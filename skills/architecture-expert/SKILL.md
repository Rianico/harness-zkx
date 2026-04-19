---
name: architecture-expert
description: Deep architecture methodology for software and system design. Use whenever architectural trade-offs, system boundaries, clean architecture, domain modeling, architectural styles, view-based design, or microservice decomposition are central to the task. Supports lenses such as balanced, uncle-bob, fowler, evans, shaw-garlan, kruchten, and newman.
argument-hint: "[balanced|uncle-bob|fowler|evans|shaw-garlan|kruchten|newman]"
---

# Architecture Expert Skill

You have invoked the Architecture Expert Skill. This skill provides reusable architectural reasoning lenses. It is meant to shape how an agent reasons about architecture, not to own orchestration or artifact storage.

## Default Usage

If no lens is specified, use `balanced`.

- `balanced` — mixed architecture reasoning across boundaries, trade-offs, domain modeling, communication, and operational concerns
- `uncle-bob` — clean architecture, dependency rule, boundary purity, SOLID, testability, separation of policy from detail
- `fowler` — refactoring pressure, enterprise patterns, pragmatism, evolutionary design, avoiding accidental complexity
- `evans` — domain language, bounded contexts, aggregate discipline, domain model integrity
- `shaw-garlan` — architectural styles, components and connectors, explicit structural reasoning
- `kruchten` — 4+1 views, stakeholder communication, view-based description of complex systems
- `newman` — service boundaries, independent deployability, operability, distributed systems trade-offs

## Core Architectural Questions

Regardless of lens, reason through these questions when relevant:

- What responsibilities belong in the core domain versus the edges?
- What boundaries must remain stable as the system evolves?
- What must be transactional together, and what can be asynchronous?
- What coupling is being introduced, and is it acceptable?
- What operational burden does this decision create?
- What becomes easier, and what becomes harder, after this decision?

## Lens Guidance

### balanced
Use this when the task needs broad architectural reasoning without a strong ideological bias.

Emphasize:
- clear system boundaries
- maintainable module decomposition
- explicit trade-offs
- stakeholder readability
- operational realism

### uncle-bob
Use this when the main problem is dependency direction, policy/detail separation, or maintainability through boundaries.

Emphasize:
- dependency rule
- ports and adapters
- isolation of business rules from frameworks
- SOLID as a design pressure, not ceremony
- testability through decoupling

Ask:
- Which code is policy and which is detail?
- Are inner layers protected from frameworks and I/O concerns?
- Is any abstraction serving a real boundary instead of speculative purity?

### fowler
Use this when the task involves reshaping existing systems, enterprise application structure, or making a design more evolvable over time.

Emphasize:
- refactoring as architecture improvement
- practical enterprise patterns
- evolutionary design
- avoiding accidental complexity and speculative abstraction

Ask:
- What design pressure is the code currently signaling?
- What should be improved now versus deferred?
- Which abstractions are pulling their weight?

### evans
Use this when domain complexity, terminology, or service boundaries are central.

Emphasize:
- ubiquitous language
- bounded contexts
- aggregate boundaries
- alignment between code structure and domain concepts

Ask:
- What is the actual domain language here?
- Are we mixing multiple contexts into one model?
- What invariants belong within one aggregate boundary?

### shaw-garlan
Use this when the task benefits from explicit discussion of architectural style or component/connector structure.

Emphasize:
- architectural style selection
- explicit structural relationships
- component and connector roles
- clarity about system form, not just local code structure

Ask:
- What architectural style best matches the problem?
- What are the primary components and connectors?
- Where does data, control, or event flow actually move?

### kruchten
Use this when architecture must be communicated clearly to multiple stakeholders or described from several perspectives.

Emphasize:
- logical view
- development view
- process/runtime view
- physical/deployment view
- use-case/scenario validation

Ask:
- Which stakeholders need which view of the system?
- Is the design understandable from runtime, deployment, and code organization perspectives?
- Which use cases validate the architecture?

### newman
Use this when distributed systems, service decomposition, or microservices are central.

Emphasize:
- service boundaries aligned to business capability
- independent deployability
- operability and observability
- failure isolation
- avoiding premature microservice decomposition

Ask:
- Should this even be a separate service?
- What data ownership boundary exists?
- What happens under timeout, retry, duplication, and partial failure?
- What operational overhead does this split introduce?

## Output Shaping Guidance

When used by an architecture workflow:
- keep the reasoning decision-oriented
- surface trade-offs explicitly
- make rejected alternatives concrete
- tie lens-specific concerns back to system boundaries, invariants, and risks

This skill should NOT:
- replace ADR-writing methodology already owned by `architecture-decision-records`
- define workflow sequencing
- define artifact locations
- turn architecture work into a style imitation exercise
