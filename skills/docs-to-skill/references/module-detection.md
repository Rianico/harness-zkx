# Module Detection Methodology

How to analyze documentation structure and propose logical module groupings.

## Detection Strategy

### Primary: Directory-Based

Map source directories to skill modules:

```
doc-dir/
├── crate_init/         → basics module
├── crate_backend/      → basics module
├── core_layout/        → layout module
├── core_style/         → styling module
├── widgets_block/      → widgets module
└── widgets_list/       → widgets module
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

| Library Type | Typical Modules |
|--------------|-----------------|
| UI Framework | basics, layout, widgets, styling |
| Data Library | basics, query, transformation, serialization |
| CLI Tool | basics, commands, configuration |
| Web Framework | basics, routing, middleware, database |
| Async Runtime | basics, tasks, channels, synchronization |

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
