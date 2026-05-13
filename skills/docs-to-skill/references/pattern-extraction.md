# Pattern Extraction Methodology

How to extract practical code patterns from documentation.

## Pattern Categories

### 1. Initialization Patterns

First code users need to run:

```
# Example: Hello world / basic setup
initialize_library()
run_minimal_app()
```

**Sources:**
- "Getting Started" sections
- "Quick Start" guides
- README examples
- Supplementary tutorial first examples

### 2. Common Usage Patterns

Operations users do frequently:

```
# Example: Basic layout configuration
layout = create_vertical([fixed(3), fill(1), fixed(1)])
header, body, footer = layout.split(area)
```

**Sources:**
- Documentation examples
- Tutorial code blocks
- Common recipes

### 3. Stateful Patterns

Components with external state:

```
# Example: List with selection state
state = ListState()
state.select(0)
render_with_state(list, area, state)
```

**Indicators:**
- Types with `State` suffix
- Render calls that accept mutable state references
- State initialization and update patterns

### 4. Error Handling Patterns

Common pitfalls and solutions:

```
# Example: Proper resource cleanup
resource = acquire_resource()
try:
    run_app(resource)
finally:
    release_resource()  # Always release!
```

**Sources:**
- "Troubleshooting" sections
- FAQ error scenarios
- Common mistakes documentation

### 5. Integration Patterns

Combining multiple features:

```
# Example: Nested layout with components
header, body, footer = vertical_layout.split(area)
sidebar, main_content = horizontal_layout.split(body)
# Render components in each region
```

**Sources:**
- Advanced tutorials
- Example applications
- Integration guides

## Extraction Priority

1. **Supplementary docs** (tutorials, guides) - best for beginner-friendly patterns
2. **Primary docs** code blocks - authoritative examples
3. **FAQ sections** - problem-solution pairs

## Pattern Selection Criteria

| Criterion | Include | Skip |
|-----------|---------|------|
| Complexity | Simple to medium | Complex edge cases |
| Generality | Reusable template | Example-specific |
| Frequency | Common operation | Rare use case |
| Clarity | Self-contained | Requires external context |

### Target Distribution

Aim for this complexity split across modules:

| Complexity | Percentage | Purpose |
|------------|------------|---------|
| Simple | 40% | Quick wins, common tasks |
| Medium | 40% | Typical usage, best practices |
| Complex | 20% | Advanced scenarios, edge cases |

### Selection Lessons

- **Prefer generalizable patterns:** Example-specific code confuses users. Patterns should work with any input, not just tutorial data.
- **Include state management patterns:** Users struggle with stateful components. Cover state initialization, updates, and synchronization.
- **Show error recovery:** Users don't know how to handle failures. Include try-catch patterns and fallback behaviors.

## Pattern Complexity Levels

| Level | Lines | Description |
|-------|-------|-------------|
| Simple | 5-15 | Single concept, minimal setup |
| Medium | 15-40 | Multiple concepts, some setup |
| Complex | 40+ | Full example, significant setup |

**Rule:** Include 1-2 simple, 2-3 medium per module. Complex patterns go to references/.

## Pattern Template

```yaml
- name: "<Descriptive Name>"
  code: |
    <code block>
  complexity: simple | medium | complex
  category: initialization | common_usage | stateful | error_handling | integration
  source: "<raw-doc-filename>#<section>"
```

**Source linking:** Every pattern MUST include a `source` field linking to the raw doc where it was found. This satisfies the Golden Source rule from extraction-rules.md.

## Anti-Patterns to Avoid

- Patterns with placeholder values that need explanation
- Code that imports from example-specific modules
- Patterns that depend on external state not shown
- Incomplete snippets missing key context

## Pattern Count Guidelines

| Module Size | Patterns in SKILL.md | Patterns in References |
|-------------|---------------------|------------------------|
| Small (< 5k tokens) | 3-5 | 0 |
| Medium (5-15k tokens) | 5-8 | 5-10 |
| Large (> 15k tokens) | 5-8 | 10-20 |
