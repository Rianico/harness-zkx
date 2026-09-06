---
paths:
  - "**/*.go"
  - "go.mod"
  - "go.sum"
---

# Go Rules

You are operating in a Go (Golang) codebase. Before proceeding with your task, review and apply these rules.

## Core Go Standards (80% Base)
- **Formatting:** Enforce `gofmt` or `goimports`. Code must adhere to standard Go formatting.
- **Error Handling:** Always handle errors gracefully with `if err != nil { return err }`.
- **Visibility:** Exported names (functions, structs, fields) must start with a capital letter. Unexported names start with a lowercase letter.
- **Concurrency:** Don't communicate by sharing memory; share memory by communicating (use channels).

## Expertise Routing (Use `Skill` tool)
If your task requires resolving complex build/module errors, concurrency review, or comprehensive testing, you MUST pause and invoke the `Skill` tool for `programming-expert` (`go-expert`) to retrieve the deep methodology:

- **Build Resolution:** If fixing compiler or `go mod` errors, invoke `Skill(skill="programming-expert", args="go-expert build")`.
- **Code Review:** If performing a PR or code review, invoke `Skill(skill="programming-expert", args="go-expert review")`.
- **Testing:** If writing comprehensive tests, invoke `Skill(skill="programming-expert", args="go-expert testing")`.

**CRITICAL INSTRUCTION:** Do not randomly guess `go.mod` fixes without retrieving the expert skill methodology.
