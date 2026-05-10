# Learning Patterns

Patterns extracted from user corrections during skill generation.

## Purpose

The docs-to-skill meta skill learns from user adjustments to improve future skill generation. This document aggregates lessons learned and provides heuristics for better autonomous decisions.

## Module Detection Patterns

### Library Type Heuristics

| Library Type | Typical Modules | Detection Signals |
|--------------|-----------------|-------------------|
| UI Framework | basics, layout, widgets, styling, theming | Widgets, rendering, event handling |
| Data Library | basics, query, transformation, serialization | Query builders, data structures |
| CLI Tool | basics, commands, configuration, plugins | Command handlers, argument parsing |
| Network Library | basics, client, server, middleware | Request/response, protocols |
| Testing Framework | basics, assertions, mocking, fixtures | Test runners, matchers |

### Module Grouping Rules

**Rule 1: Separate Styling from Theming**
- **When:** UI framework has both style attributes and named color schemes
- **Split:** `styling` module for Style/Color/Modifier, `theming` module for palettes/themes
- **Example:** ratatui has `Style` types and `palette::material`/`palette::tailwind`

**Rule 2: Group by User Mental Model**
- **When:** Directory structure doesn't match how users think about the library
- **Adjust:** Group by task (e.g., "building forms" vs "form components")
- **Example:** Group `input`, `select`, `checkbox` under `form-widgets` if tutorials teach forms

**Rule 3: Keep "Basics" Small**
- **When:** Basics module exceeds 8000 tokens
- **Split:** Move initialization to `getting-started`, keep terminal/lifecycle in basics
- **Reason:** Users want quick setup, not comprehensive basics

## Trigger Extraction Patterns

### Problem-Framing Keywords by Domain

| Domain | Common Problem Framings |
|--------|------------------------|
| Layout | "center", "resize", "responsive", "split", "divide", "align" |
| Forms | "validate", "submit", "error handling", "required field" |
| Lists | "scrollable", "selectable", "filter", "search", "paginate" |
| Tables | "sort", "filter", "select row", "column width" |
| Styling | "change color", "bold", "theme", "dark mode" |
| Events | "handle key", "on click", "event loop", "input" |

### Trigger Extraction Lessons

**Lesson 1: Include "How to" Phrases**
- **Context:** LLM often misses natural language queries
- **Add:** Phrases like "how to center", "how to create", "how to handle"
- **Source:** FAQ sections and tutorial headings

**Lesson 2: Include Error Messages as Triggers**
- **Context:** Users search for error text
- **Add:** Common error messages or panic conditions
- **Example:** "terminal not restored", "buffer overflow"

**Lesson 3: Add Localized Triggers**
- **Context:** Non-English documentation users
- **Add:** Chinese/Japanese keywords if docs have translations
- **Example:** `组件` (widget), `布局` (layout), `样式` (style)

## Pattern Selection Patterns

### Pattern Complexity Distribution

| Complexity | Percentage | Purpose |
|------------|------------|---------|
| Simple | 40% | Quick wins, common tasks |
| Medium | 40% | Typical usage, best practices |
| Complex | 20% | Advanced scenarios, edge cases |

### Pattern Selection Lessons

**Lesson 1: Prefer Generalizable Patterns**
- **Context:** Example-specific code confuses users
- **Avoid:** Patterns that only work with specific data
- **Prefer:** Patterns that work with any input

**Lesson 2: Include State Management Patterns**
- **Context:** Users struggle with stateful widgets
- **Add:** State initialization, state updates, state synchronization
- **Example:** List with selection, Table with scrolling

**Lesson 3: Show Error Recovery**
- **Context:** Users don't know how to handle failures
- **Add:** Try-catch patterns, fallback behaviors
- **Example:** "What happens when terminal resize fails?"

## Reference Curation Patterns

### Reference Size Guidelines

| Reference Type | Target Size | Max Size |
|---------------|-------------|----------|
| API reference | 200-400 lines | 600 lines |
| Pattern guide | 100-200 lines | 400 lines |
| Quick reference | 50-100 lines | 200 lines |

### Reference Organization Lessons

**Lesson 1: Keep Code Examples Intact**
- **Context:** Truncated code is unusable
- **Rule:** Never split code blocks across files
- **Check:** All code blocks compile/run

**Lesson 2: Add Context for API Docs**
- **Context:** Raw API docs lack usage context
- **Add:** "When to use" and "Common patterns" sections
- **Source:** Tutorial sections that use the API

## Quality Threshold Patterns

### Minimum Quality for Acceptance

| Criterion | Minimum | Reason |
|-----------|---------|--------|
| Trigger Coverage | 0.6 | Skills need discoverability |
| Pattern Usefulness | 0.5 | Skills need practical value |
| Beginner Friendliness | 0.5 | Attract new users |
| Graceful Degradation | 0.7 | Skills must work offline |

### When to Request User Review

- Overall score < 0.7
- Any criterion < 0.5
- Generated patterns > 10 per module (overwhelming)
- Generated patterns < 3 per module (insufficient)
- Triggers > 40 per module (too many)
- Triggers < 8 per module (too few)

## Continuous Improvement

### Learning Record Format

```yaml
learning_record:
  timestamp: "2026-05-08T10:30:00Z"
  library: ratatui
  phase: module_detection
  llm_proposed: [basics, layout, widgets, styling]
  user_adjusted: [basics, layout, widgets, styling, theming]
  lesson: "For UI frameworks, separate styling from theming when color palettes exist"
  applied_to: [uikit, gtk-rs, iced]
```

### Aggregation Process

1. Collect learning records from all sessions
2. Cluster by phase and library type
3. Extract common patterns
4. Update this document
5. Apply to future generations
