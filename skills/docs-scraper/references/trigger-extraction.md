# Trigger Extraction Patterns

Patterns for extracting trigger keywords from documentation.

## Purpose of Triggers

Triggers serve one purpose: help the LLM decide **when to invoke the skill**. They are NOT an API index — they match what users actually say, not the internal type surface.

**Good triggers:** domain terms, task phrases, problem descriptions that a user would type
**Bad triggers:** internal type names, method names, implementation details a user would never mention

## Trigger Categories

### 1. Domain Terms (Highest Priority)

The library name, framework category, and domain vocabulary:
- `<library-name>`, `<framework-category>`, `<domain-keywords>`
- These are the strongest signals — if someone mentions the domain, the skill is relevant

### 2. Task Phrases

What users ask to do:
- "<verb> <domain-object>", "<create/build> <thing>"
- "<action> <component>", "<configure> <setting>"

**Pattern:** Verb + domain object in natural language

### 3. Problem-Framing Keywords

How users describe problems:
- "<component> not <expected-behavior>", "<feature> not working"
- "<action> fails", "<behavior> broken", "how to <goal>"

**Pattern:** Problem or goal the user is trying to solve

### 4. Beginner Queries

Common entry-point phrases:
- "<library> hello world", "<library> tutorial", "getting started with <library>"
- These catch users who don't know the terminology yet

## Domain Problem-Framing Keywords

When extracting problem-framing triggers, use these domain patterns:

| Domain | Common Problem Framings |
|--------|------------------------|
| Layout | "center", "resize", "responsive", "split", "divide", "align" |
| Forms | "validate", "submit", "error handling", "required field" |
| Lists | "scrollable", "selectable", "filter", "search", "paginate" |
| Tables | "sort", "filter", "select row", "column width" |
| Styling | "change color", "bold", "theme", "dark mode" |
| Events | "handle key", "on click", "event loop", "input" |

## Trigger Enrichment Lessons

- **Include "how to" phrases:** LLMs often miss natural language queries. Add phrases like "how to center", "how to create", "how to handle". Source: FAQ sections and tutorial headings.
- **Include error messages:** Users search for error text. Add common error messages or panic conditions as triggers.
- **Include conceptual synonyms:** Users may describe the same concept using different vocabulary (e.g., "responsive layout" / "adaptive sizing" / "flexible constraints").

## What NOT to Include

| Skip | Why |
|------|-----|
| Internal type names (`Widget`, `Buffer`, `Area`) | Users don't say these; if they mention the library name, it already triggers |
| Method names (`render`, `split`, `draw`) | Too generic without context; "render" could be anything |
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

For a UI framework library:

```yaml
description: |
  <Language> <category> for building <domain> applications. TRIGGER when: user mentions <library-name>, <framework-category>; asks about building <domain> apps, <component> rendering, layout constraints; "<library> hello world", <domain> layout, <domain> widgets, custom widget.
```

**Not this:**
```yaml
# BAD: API surface dump, not user-facing triggers
description: |
  TRIGGER when: Widget, Container, Layout, Flex, Direction, Block, Paragraph, List, Table, Frame, Buffer, Span, Line, Text, render, split, areas, vertical, horizontal...
```
