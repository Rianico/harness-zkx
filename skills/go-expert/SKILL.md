---
name: go-expert
description: Deep expertise in Go (Golang) patterns, idiomatic code, concurrency, testing, and build resolution. Invoke this skill when instructed by the Go rules.
argument-hint: "[build|review|testing]"
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
- **Naming:** Use MixedCaps. Keep package names short, lowercase, and single-word.
> **Need Deep Knowledge?** Read `skills/go-expert/references/golang-patterns.md`.

### Testing & Verification
- **Test Structure:** Use Table-Driven Tests (`[]struct`) for robust unit testing.
- **Subtests:** Run subtests using `t.Run()` for better isolation and naming.
- **Mocks:** Generate mocks using `gomock` or implement simple mock structs directly in the test file.
> **Need Deep Knowledge?** Read `skills/go-expert/references/golang-testing.md`.

## Instructions for the Agent
1. Based on the arguments provided (e.g., "build", "review", "testing"), apply the relevant checklist above.
2. If the task is architectural, use the `Read` tool to fetch the relevant reference document from `skills/go-expert/references/`.
