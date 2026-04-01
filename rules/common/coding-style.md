# Coding Style

## Immutability (CRITICAL)

ALWAYS create new objects, NEVER mutate existing ones:

```
// Pseudocode
WRONG:  modify(original, field, value) → changes original in-place
CORRECT: update(original, field, value) → returns new copy with change
```

Rationale: Immutable data prevents hidden side effects, makes debugging easier, and enables safe concurrency.

## File Organization

MANY SMALL FILES > FEW LARGE FILES:
- High cohesion, low coupling
- 200-400 lines typical, 800 max
- Extract utilities from large modules
- Organize by feature/domain, not by type

## Error Handling

ALWAYS handle errors comprehensively:
- Handle errors explicitly at every level
- Provide user-friendly error messages in UI-facing code
- Log detailed error context on the server side
- Never silently swallow errors

## Input Validation

ALWAYS validate at system boundaries:
- Validate all user input before processing
- Use schema-based validation where available
- Fail fast with clear error messages
- Never trust external data (API responses, user input, file content)

## Code Quality Principles

### 1. Readability First
Code is read more than written
Clear variable and function names
Self-documenting code preferred over comments
Consistent formatting

### 2. KISS (Keep It Simple, Stupid)
Simplest solution that works
Avoid over-engineering
No premature optimization
Easy to understand > clever code

### 3. DRY (Don't Repeat Yourself When The Same Logic Exists More Than 3 Times)
Extract common logic into functions
Create reusable components
Share utilities across modules
Avoid copy-paste programming

### 4. YAGNI (You Aren't Gonna Need It)
Don't build features before they're needed
Avoid speculative generality
Add complexity only when required
Start simple, refactor when needed

## Code Quality Checklist

Before marking work complete:
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling
- [ ] No hardcoded values (use constants or config)
- [ ] No mutation (immutable patterns used)
