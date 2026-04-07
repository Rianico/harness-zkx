---
name: architecture-expert
description: Deep expertise in software architecture, clean architecture, microservices, Event-Driven Architecture (EDA), Domain-Driven Design (DDD), and structural integrity.
argument-hint: "[clean-arch|microservices|eda|ddd|resilience]"
---

# Architecture Expert Skill

You have invoked the Architecture Expert Skill. This skill contains high-level patterns and checklists for designing and reviewing software architectures.

## Quick Actions & Checklists

### Clean & Layered Architecture
- **Dependency Rule:** Inner layers (domain/entities) MUST NOT depend on outer layers (UI/Database). Use dependency inversion (interfaces) to cross boundaries.
- **Hexagonal Architecture:** Define clear Ports (interfaces) and Adapters (implementations) to isolate core business logic from frameworks.

### Domain-Driven Design (DDD)
- **Bounded Contexts:** Ensure clear boundaries between sub-domains. Do not share database tables across bounded contexts.
- **Ubiquitous Language:** Class and variable names must perfectly match the terminology used by domain experts.
- **Aggregates:** Transaction boundaries must align with Aggregate Roots. Never modify two aggregates in a single transaction.

### Distributed Systems & Microservices
- **Event-Driven Architecture (EDA):** Use events (e.g., via Kafka, RabbitMQ) to decouple services. Ensure idempotency for all event handlers.
- **Data Patterns:** Prefer Saga or Outbox patterns for distributed transactions. Avoid two-phase commits (2PC).
- **Resilience:** Always implement Circuit Breakers, Bulkheads, and Timeouts when calling external services.

## Instructions for the Agent
1. Apply these architectural constraints to the code or design plan you are reviewing.
2. If the user's request violates these principles, propose a refactored design that aligns with them.
3. If you need deeper knowledge on a specific pattern, instruct the user to provide it or research it.
