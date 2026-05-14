---
name: write
description: Content creation and distribution cluster. Routes to write-article for long-form writing (articles, blog posts, guides, tutorials, newsletters, voice matching) or write-publish for platform-native content and multi-platform distribution (X, LinkedIn, Threads, Bluesky, TikTok, YouTube, newsletters). TRIGGER on article writing, blog drafting, newsletter creation, social posts, crossposting, content repurposing, or voice-consistent writing.
arguments: mode content_type platform
argument-hint: |
  article [blog|essay|guide|tutorial|newsletter] -- long-form writing with voice capture
  publish [x|linkedin|threads|bluesky|tiktok|youtube|newsletter] -- platform-native content
  article --publish [platforms...] -- write article then adapt and distribute
allowed-tools: [Read, Edit, Write, Bash, Agent]
---

# Write Command

Single entry point for content creation and distribution.

## Routing

| Argument | Skill file | Purpose |
|----------|------------|---------|
| `article` | `$SKILL_DIR/../skills/write-article/SKILL.md` | Long-form: blog, essay, guide, tutorial, newsletter |
| `publish` | `$SKILL_DIR/../skills/write-publish/SKILL.md` | Platform-native: X, LinkedIn, Threads, Bluesky, TikTok, YouTube |
| `article --publish` | both skills sequentially | Create article then adapt and distribute |

## Instructions

### `/write article [blog|essay|guide|tutorial|newsletter]`

Read `$SKILL_DIR/../skills/write-article/SKILL.md` and follow its instructions. Use for crafting long-form content with voice capture, structural guidance, and anti-pattern avoidance.

### `/write publish [x|linkedin|threads|bluesky|tiktok|youtube|newsletter]`

Read `$SKILL_DIR/../skills/write-publish/SKILL.md` and follow its instructions. Use for creating platform-native social content and distributing it across platforms.

### `/write article --publish [platforms...]`

1. Read `$SKILL_DIR/../skills/write-article/SKILL.md` and craft the long-form content
2. Then read `$SKILL_DIR/../skills/write-publish/SKILL.md` and adapt/distribute across platforms

### No argument provided

If `$ARGUMENTS` is empty, ask the user which mode they need:

1. **article** — "I need to write a long-form piece (blog, essay, guide, tutorial, newsletter)"
2. **publish** — "I need to create and distribute platform-native content (X, LinkedIn, Threads, Bluesky, TikTok, YouTube)"
3. **article --publish** — "I need to write an article and then distribute it"
