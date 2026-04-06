---
name: cpp-expert
description: Deep expertise in modern C++ (C++11/14/17/20), CMake build systems, memory safety, and testing. Invoke this skill when instructed by the C++ rules.
argument-hint: "[build|review|testing]"
---

# C++ Expert Skill

You have invoked the C++ Expert Skill. This skill contains actionable checklists and constraints for C++ software engineering tasks.

## Quick Actions & Checklists

### Build & Linker Resolution (CMake)
- **Undefined References:** Often caused by missing `target_link_libraries` or failing to compile a `.cpp` file. Check `CMakeLists.txt`.
- **Header Guards:** Ensure `#pragma once` or standard `#ifndef` guards are present.
- **Includes:** Prefer forward declarations in headers to reduce compilation time. Include what you use.

### Coding Standards (Modern C++)
- **Memory Management:** Use `std::unique_ptr` and `std::shared_ptr`. Avoid raw `new` and `delete`.
- **Initialization:** Use uniform initialization (brace initialization `{}`).
- **Const Correctness:** Apply `const` liberally to methods, parameters, and variables.
- **Auto:** Use `auto` when the type is obvious or overly complex, but prefer explicit types for readability if it's ambiguous.
> **Need Deep Knowledge?** Read `skills/cpp-expert/references/cpp-coding-standards.md`.

### Testing & Verification (GoogleTest/Catch2)
- **Test Structure:** Use `TEST_F` for fixtures. Keep setup logic in the fixture constructor or `SetUp()` method.
- **Mocks:** Use GoogleMock (`MOCK_METHOD`) for dependency injection.
> **Need Deep Knowledge?** Read `skills/cpp-expert/references/cpp-testing.md`.

## Instructions for the Agent
1. Based on the arguments provided (e.g., "build", "review", "testing"), apply the relevant checklist above.
2. If the task is architectural, use the `Read` tool to fetch the relevant reference document from `skills/cpp-expert/references/`.
