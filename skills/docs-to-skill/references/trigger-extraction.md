# Trigger Extraction Patterns

Patterns for extracting trigger keywords from documentation.

## Purpose of Triggers

Triggers serve one purpose: help the LLM decide **when to invoke the skill**. They are NOT an API index — they match what users actually say, not the internal type surface.

**Good triggers:** domain terms, task phrases, problem descriptions that a user would type
**Bad triggers:** internal type names, method names, implementation details a user would never mention

## Trigger Categories

### 1. Domain Terms (Highest Priority)

The library name, framework category, and domain vocabulary:
- `ratatui`, `TUI`, `terminal UI`, `terminal app`
- These are the strongest signals — if someone mentions the domain, the skill is relevant

### 2. Task Phrases

What users ask to do:
- "build terminal app", "create TUI", "event loop"
- "split area", "responsive layout", "terminal widgets"
- "style terminal text", "custom widget"

**Pattern:** Verb + domain object in natural language

### 3. Problem-Framing Keywords

How users describe problems:
- "widget not rendering", "layout not fitting", "text wrapping"
- "center widget", "handle resize", "scrollable list"

**Pattern:** Problem or goal the user is trying to solve

### 4. Beginner Queries

Common entry-point phrases:
- "ratatui hello world", "ratatui app structure", "getting started with TUI"
- These catch users who don't know the terminology yet

## What NOT to Include

| Skip | Why |
|------|-----|
| Internal type names (`Frame`, `Buffer`, `Rect`) | Users don't say these; if they mention the library name, it already triggers |
| Method names (`render_widget`, `split`) | Too generic without context; "render" could be anything |
| Enum variants (`Direction::Vertical`) | Implementation detail, not a user query |
| Every type in the API | Bloats description without improving discovery |

**Test:** Would a user ever type this phrase? If not, it's not a trigger.

## Extraction Process

```
1. Identify domain terms from library name and category
   ↓
2. Extract task phrases from tutorial headings and FAQ
   ↓
3. Identify problem-framing from troubleshooting sections
   ↓
4. Add beginner entry-point phrases
   ↓
5. Filter: remove anything a user wouldn't type
   ↓
6. Assign to skill description (not per-module — triggers live in the main SKILL.md)
```

## Output Format

Triggers go into the main SKILL.md `description` field, not a separate file:

```yaml
description: |
  <what the skill does>. TRIGGER when: <domain terms>; <task phrases>; <problem phrases>; <beginner queries>.
```

## Example

From ratatui documentation:

```yaml
description: |
  Rust TUI framework for building terminal user interfaces. TRIGGER when: user mentions ratatui, TUI, terminal UI/app/interface; asks about building terminal apps, event loops, widget rendering, layout constraints; "ratatui hello world", terminal layout, terminal widgets, custom widget.
```

**Not this:**
```yaml
# BAD: API surface dump, not user-facing triggers
description: |
  TRIGGER when: Layout, Constraint, Rect, Flex, Direction, Block, Paragraph, List, Table, Frame, Buffer, Span, Line, Text, render_widget, split, areas, vertical, horizontal...
```
