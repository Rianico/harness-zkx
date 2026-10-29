---
name: lua-expert
description: >-
  Lua development guidelines covering tables, metatables, error handling, game development, and performance optimization. Use when writing Lua modules or Love2D game code.
metadata:
  managed-by: programming-expert
---

# Lua Expert Skill

Checklists and constraints for Lua engineering: tables, metatables, game loops, and performance.

## Mental Model

- Lua is dynamically typed. Explicit nil handling and consistent structure carry the clarity.
- Tables are the single data structure. Arrays, records, namespaces, and objects are all tables.
- Indexing is 1-based. Apply it consistently across every module.
- Modules are tables loaded through `require()`. Group related functions into modules. Keep module-private code in local functions.

## Naming Conventions

- snake_case for variables and functions.
- PascalCase for classes/modules.
- UPPERCASE for constants.
- Underscore prefix for private functions/variables.

## Error Handling

- Wrap fallible calls in `pcall`. Use `xpcall` with a handler when you need the traceback.
- Handle nil values explicitly.
- Use `assert()` for preconditions.
- Write informative error messages. Propagate errors deliberately.

## Metatables and OOP

- Use metatables for object-oriented patterns.
- Implement `__index` for inheritance and read-through.
- Use `__newindex` to validate or guard property writes.
- Reach for metamethods (`__add`, `__eq`, `__tostring`) when operator or conversion syntax fits.

## Performance and Memory

- Prefer local variables over globals. Every global access is a table lookup. Cache frequently accessed values in locals.
- Minimize table creation inside loops. Pre-allocate tables when the size is known.
- Reuse tables where practical.
- Use weak tables (`__mode = "k"` or `"v"`) for caches, so entries collect.

## Game Development

- Structure the game loop explicitly: `love.load` → `love.update(dt)` → `love.draw`.
- Cull collisions with a broad phase (grid or quadtree) before narrow-phase tests.
- Manage game state as an explicit state machine or stack. Scattered flags hide transitions.
- Batch input processing once per frame.
- Isolate engine callbacks from game logic, so Love2D or Corona integration stays swappable.
