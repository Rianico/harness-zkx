---
paths:
  - "CMakeLists.txt"
  - "Makefile"
  - "**/*.cpp"
  - "**/*.hpp"
  - "**/*.h"
  - "**/*.c"
---

# C++ Rules

You are operating in a C++ codebase.

## Core C++ Standards (80% Base)

- **Memory safety:** raw `new`/`delete` is banned except inside a low-level memory allocator. Use `std::unique_ptr` by default.
- **Const correctness:** variables, pointers, and methods are `const` whenever they do not mutate state.
- **Header files:** always use `#pragma once` in headers. Include what you use.
- **Modern dialect:** assume C++17 or higher unless specified otherwise. Use structured bindings, `std::optional`, and `std::variant`.

## Expertise Routing (Use `Read` tool)

`cpp-expert` is a managed subskill of the `programming-expert` router. Subskills are hidden from discovery (`managed-by`) — do not invoke them through the `Skill` tool. Read the file directly:

- `skills/programming-expert/subskills/cpp-expert/SKILL.md` — build/linker resolution, modern C++ standards, GoogleTest/Catch2 testing
- `skills/programming-expert/subskills/cpp-expert/references/` — coding standards (`F.*`/`C.*` rules, resource management), testing workflow

**CRITICAL:** Do not attempt complex C++ macro debugging or template metaprogramming fixes without reading the expert documentation first.
