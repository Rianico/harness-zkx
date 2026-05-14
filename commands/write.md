---
name: write
description: Single entry point for the content creation cluster. Routes to the appropriate skill based on intent.
argument-hint: "[article|publish] [--publish]"
allowed-tools: [Read, Edit, Write, Bash, Agent, Skill]
---

# Write Command

Single entry point for content creation and distribution.

## Routing

| Argument | Skill | Purpose |
|----------|-------|---------|
| `article` | write-article | Long-form writing craft (voice capture, structure, anti-patterns) |
| `publish` | write-publish | Platform-native content creation and multi-platform distribution |
| `article --publish` | write-article then write-publish | Create article then adapt and distribute |

## Instructions

### `/write article`

Invoke the `write-article` skill. Use for crafting long-form content with voice capture, structural guidance, and anti-pattern avoidance.

### `/write publish`

Invoke the `write-publish` skill. Use for creating platform-native social content and distributing it across platforms (X, LinkedIn, newsletters, TikTok, YouTube).

### `/write article --publish`

1. Invoke `write-article` to craft the long-form content
2. Then invoke `write-publish` to adapt and distribute it across platforms

### No argument provided

If `$ARGUMENTS` is empty, ask the user which mode they need:

1. **article** — "I need to write a long-form piece"
2. **publish** — "I need to create and distribute platform-native content"
3. **article --publish** — "I need to write an article and then distribute it"
