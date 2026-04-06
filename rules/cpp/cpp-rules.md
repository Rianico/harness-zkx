---
paths:
  - "CMakeLists.txt"
  - "Makefile"
  - "**/*.cpp"
  - "**/*.hpp"
  - "**/*.h"
  - "**/*.c"
  - "CMakeLists.txt"
---

# C++ Rules

You are operating in a C++ codebase. Before proceeding with your task, review and apply these rules.

## Core C++ Standards (80% Base)
- **Memory Safety:** NEVER use raw `new`/`delete` unless writing a low-level memory allocator. Use `std::unique_ptr` by default.
- **Const Correctness:** Variables, pointers, and methods must be `const` whenever they do not mutate state.
- **Header Files:** Always use `#pragma once` in headers. Include what you use.
- **Modern Dialect:** Assume C++17 or higher unless specified otherwise. Use modern features like structured bindings, `std::optional`, and `std::variant`.

## Expertise Routing (Use `Skill` tool)
If your task requires resolving complex linker errors, CMake issues, or structural reviews, you MUST pause and invoke the `Skill` tool for `cpp-expert` to retrieve the deep methodology:

- **Build Resolution:** If fixing CMake or linker errors, invoke `Skill(skill="cpp-expert", args="build")`.
- **Code Review:** If performing a PR or code review, invoke `Skill(skill="cpp-expert", args="review")`.
- **Testing:** If writing comprehensive tests, invoke `Skill(skill="cpp-expert", args="testing")`.

**CRITICAL INSTRUCTION:** Do not attempt complex C++ macro debugging or template metaprogramming fixes without invoking the expert skill methodology first.
