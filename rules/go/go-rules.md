---
paths:
  - "**/*.go"
  - "go.mod"
  - "go.sum"
---

# Go Rules

You are operating in a Go (Golang) codebase.

## Core Go Standards (80% Base)

- **Formatting:** enforce `gofmt` or `goimports`. Code must adhere to standard Go formatting.
- **Error handling:** always handle errors explicitly with `if err != nil { return err }`. `panic` is for programmer errors, not expected conditions.
- **Visibility:** exported names (functions, structs, fields) start with a capital letter. Unexported names start lowercase.
- **Concurrency:** don't communicate by sharing memory. Share memory by communicating (use channels).

## Expertise Routing (Use `Read` tool)

`go-expert` is a managed subskill of the `programming-expert` router. Subskills are hidden from discovery (`managed-by`) — do not invoke them through the `Skill` tool. Read the file directly:

- `skills/programming-expert/subskills/go-expert/SKILL.md` — build resolution, idiomatic review checklists, testing
- `skills/programming-expert/subskills/go-expert/references/` — Go patterns (error handling, concurrency, interfaces, packages), table-driven testing

**CRITICAL:** Do not guess `go.mod` fixes. Read the expert methodology first.
