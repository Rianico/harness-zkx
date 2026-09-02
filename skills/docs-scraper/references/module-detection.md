# Module Detection Methodology

How to analyze documentation structure and propose logical module groupings.

## Detection Strategy

### Primary: Directory-Based

Map source directories to skill modules:

```
doc-dir/
├── getting_started/    → basics module
├── core/               → basics module
├── layout/             → layout module
├── style/              → styling module
├── widgets/            → widgets module
└── advanced/           → advanced module
```

**Process:**
1. List all top-level directories
2. Group by functional area (init, layout, style, widgets, etc.)
3. Estimate token count per group
4. Check for cross-cutting concerns (theming, errors, etc.)

### Secondary: Content Clustering

When directory structure is flat or uninformative:

1. Scan file content for type signatures
2. Cluster by import relationships
3. Identify cohesive feature sets
4. Propose modules based on clusters

## Module Proposal Format

```yaml
proposed_modules:
  - name: <module>
    source_dirs: [<dir1>, <dir2>]
    topics: [<topic1>, <topic2>]
    estimated_tokens: <count>
```

## Module Naming Conventions

| Source Pattern | Module Name |
|----------------|-------------|
| init, setup, config | `basics` |
| layout, constraint, rect | `layout` |
| style, color, text | `styling` |
| widgets/* | `widgets` |
| theming, theme | `theming` (separate from styling if color palettes exist) |
| errors, validation | `error-handling` |
| testing, test | `testing` |

## Token Thresholds

| Size | Action |
|------|--------|
| < 10k tokens | Single module, no sub-skills |
| 10k - 50k tokens | 2-4 modules recommended |
| > 50k tokens | 4-6 modules, consider references/ |

## Common Patterns by Library Type

| Library Type | Typical Modules | Detection Signals |
|--------------|-----------------|-------------------|
| UI Framework | basics, layout, widgets, styling, theming | Widgets, rendering, event handling |
| Data Library | basics, query, transformation, serialization | Query builders, data structures |
| CLI Tool | basics, commands, configuration, plugins | Command handlers, argument parsing |
| Network Library | basics, client, server, middleware | Request/response, protocols |
| Web Framework | basics, routing, middleware, database | HTTP methods, route definitions |
| Async Runtime | basics, tasks, channels, synchronization | Spawn, join, channel primitives |
| Testing Framework | basics, assertions, mocking, fixtures | Test runners, matchers |

## Module Grouping Rules

**Separate Styling from Theming:**
- When UI framework has both style attributes and named color schemes
- Split: `styling` for style/color primitives, `theming` for palettes/themes

**Group by User Mental Model:**
- When directory structure doesn't match how users think about the library
- Group by task (e.g., "building forms" vs "form components")

**Keep "Basics" Small:**
- When basics module exceeds 8000 tokens
- Move initialization to `getting-started`, keep lifecycle in basics

## Module Merging Heuristics

Merge modules when:
- Combined tokens < 15k
- High conceptual overlap (e.g., style + theming if no color system)
- User feedback indicates confusion

## Module Splitting Heuristics

Split modules when:
- Single module > 20k tokens
- Distinct sub-communities (e.g., list widgets vs chart widgets)
- State management differs (stateless vs stateful widgets)
