---
name: go-expert
description: >-
  Go/Golang domain expertise for modules, idiomatic package design, interfaces, error handling, goroutines/channels/concurrency, table-driven tests, gomock, build errors, and code review. For Go implementation, debugging, testing, build resolution, concurrency design, and refactoring.
argument-hint: |-
  [build|review|testing]
metadata:
  managed-by: programming-expert
---

# Go Expert Skill

You have invoked the Go Expert Skill. This skill contains actionable checklists and constraints for Go software engineering tasks.

## Quick Actions & Checklists

### Build & Compilation Resolution
- **Modules:** Always ensure `go mod tidy` is run to fix missing dependencies.
- **Imports:** Avoid cyclic dependencies by extracting shared interfaces into a separate package.
- **Generics:** Use Go 1.18+ generics (`[T any]`) instead of `interface{}` when type safety is needed.

### Idiomatic Go (Code Review)
- **Error Handling:** Check errors explicitly (`if err != nil`). Never use `panic` for expected error conditions.
- **Concurrency:** Prefer channels for passing data. Use `sync.Mutex` or `sync.RWMutex` only when protecting shared state. Start goroutines safely and ensure they can exit to avoid leaks.
- **Interfaces:** Define interfaces where they are *used*, not where they are implemented. Keep them small (1-2 methods).
- **Deep Packages:** A package should be deep (Ousterhout) — minimal exported surface (`UpperCamelCase`), rich absorbed complexity. Avoid shallow `util` packages or multi-layer DTO/mapper shuffles.
- **Design Deepening vs. Scope Creep:** Internal package decomposition (e.g. inside `internal/`) to cure God files is permitted design deepening. Never expand public exported symbols without mandate.
- **Naming:** Use MixedCaps. Keep package names short, lowercase, and single-word.
> **Need Deep Knowledge?** Read `$SKILL_DIR/references/golang-patterns.md`.

### Testing & Verification
- **Test Structure & Oracles:** Use Table-Driven Tests (`[]struct`) as minimal input-output oracles verifying state transitions and edge cases.
- **Subtests:** Run subtests using `t.Run()` for better isolation and naming.
- **Mocks:** Generate mocks using `gomock` or implement simple mock structs directly in the test file.
- **Counterexample Refutation:** When claiming an algorithmic defect, supply a concrete minimal table entry (`input -> expected vs observed`) proving the failure.
> **Need Deep Knowledge?** Read `$SKILL_DIR/references/golang-testing.md`.

## Instructions for the Agent
1. Based on the arguments provided (e.g., "build", "review", "testing"), apply the relevant checklist above.
2. For deeper idiomatic Go patterns or testing guidance, use the `Read` tool to fetch the relevant reference document from `$SKILL_DIR/references/`.
