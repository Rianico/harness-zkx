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

Checklists and constraints for Go engineering tasks.

## Quick Actions & Checklists

### Build & Compilation Resolution

- **Modules:** run `go mod tidy` to fix missing dependencies.
- **Imports:** break import cycles by extracting shared interfaces into a separate package.
- **Generics:** use Go 1.18+ generics (`[T any]`) instead of `interface{}` when type safety is needed.

### Idiomatic Go (Code Review)

- **Error handling:** check errors explicitly (`if err != nil`). Never use `panic` for expected error conditions.
- **Concurrency:** prefer channels for passing data. Use `sync.Mutex` or `sync.RWMutex` only when protecting shared state. Start goroutines safely and ensure they can exit to avoid leaks.
- **Interfaces:** define interfaces where they are *used*, not where they are implemented. Keep them small (1-2 methods).
- **Deep packages:** a package should be deep (Ousterhout) — minimal exported surface (`UpperCamelCase`), rich absorbed complexity. Avoid shallow `util` packages or multi-layer DTO/mapper shuffles.
- **Design deepening vs. scope creep:** internal package decomposition (e.g. inside `internal/`) to cure God files is permitted design deepening. Never expand public exported symbols without mandate.
- **Naming:** use MixedCaps. Keep package names short, lowercase, and single-word.

> Deep dive: [golang-patterns.md](references/golang-patterns.md) — error handling patterns, concurrency patterns, interface design, package organization.

### Testing & Verification

- **Test structure & oracles:** use table-driven tests (`[]struct`) as minimal input-output oracles. Cover state transitions and edge cases.
- **Subtests:** run subtests with `t.Run()` for isolation and naming.
- **Mocks:** generate mocks with `gomock`, or implement simple mock structs directly in the test file.
- **Counterexample refutation:** when claiming an algorithmic defect, supply a concrete minimal table entry (`input -> expected vs observed`) proving the failure.

> Deep dive: [golang-testing.md](references/golang-testing.md) — table-driven tests, subtests and benchmarks, test helpers, golden files.
