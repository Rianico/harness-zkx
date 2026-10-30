---
name: cpp-expert
description: >-
  Modern C++ guide across C++11-23: RAII, smart pointers, templates, CMake, and GoogleTest/Catch2. Use when implementing C++, debugging memory/linker errors, resolving build failures, or refactoring code.
argument-hint: |-
  [build|review|testing]
metadata:
  managed-by: programming-expert
---

# C++ Expert Skill

Checklists and constraints for C++ engineering tasks.

## Quick Actions & Checklists

### Build & Linker Resolution (CMake)

- **Undefined references:** trace to a missing `target_link_libraries` or an uncompiled `.cpp` file. Check `CMakeLists.txt`.
- **Header guards:** ensure `#pragma once` or standard `#ifndef` guards are present.
- **Includes:** prefer forward declarations in headers to cut compilation time. Include what you use.

### Coding Standards (Modern C++)

- **Memory management:** use `std::unique_ptr` and `std::shared_ptr`. Avoid raw `new` and `delete`.
- **Initialization:** use uniform brace initialization `{}`.
- **Const correctness:** apply `const` liberally to methods, parameters, and variables.
- **Auto:** use `auto` when the type is obvious or overly complex. Prefer explicit types when the type is ambiguous.

> Deep dive: [cpp-coding-standards.md](references/cpp-coding-standards.md) — cross-cutting principles, function and class rules (`F.*`, `C.*`), resource management.

### Testing & Verification (GoogleTest/Catch2)

- **Test structure:** use `TEST_F` for fixtures. Keep setup logic in the fixture constructor or `SetUp()`.
- **Mocks:** use GoogleMock (`MOCK_METHOD`) for dependency injection.

> Deep dive: [cpp-testing.md](references/cpp-testing.md) — TDD workflow, GoogleTest/Catch2 examples, running tests, debugging failures.
