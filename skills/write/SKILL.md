---
name: write
description: Content creation and distribution cluster. Routes to article for long-form writing (articles, blog posts, guides, tutorials, newsletters) or publish for platform-native content and multi-platform distribution (X, LinkedIn, Threads, Bluesky, TikTok, YouTube, newsletters). TRIGGER on article writing, blog drafting, newsletter creation, social posts, crossposting, content repurposing, or voice-consistent writing.
arguments: mode content_type platform
argument-hint: |
  article [blog|essay|guide|tutorial|newsletter] -- long-form writing with voice capture
  publish [x|linkedin|threads|bluesky|tiktok|youtube|newsletter] -- platform-native content
  article --publish [platforms...] -- write article then adapt and distribute
metadata:
  manage: [article, publish]
---

# Write Skill

Single entry point for content creation and distribution.

## Sub-Skill Registry

```yaml
subskills:
  article: $SKILL_DIR/subskills/article/SKILL.md
  publish: $SKILL_DIR/subskills/publish/SKILL.md
```

## Dispatch

Parse `$ARGUMENTS` to determine mode:

| First Arg | Action |
|-----------|--------|
| `article` | Read `$SKILL_DIR/subskills/article/SKILL.md` and follow its instructions |
| `publish` | Read `$SKILL_DIR/subskills/publish/SKILL.md` and follow its instructions |
| `article --publish` | Read article skill first, then read publish skill for distribution |

### `/write article [blog|essay|guide|tutorial|newsletter]`

Read `$SKILL_DIR/subskills/article/SKILL.md` and follow its instructions. Use for crafting long-form content with voice capture, structural guidance, and anti-pattern avoidance.

### `/write publish [x|linkedin|threads|bluesky|tiktok|youtube|newsletter]`

Read `$SKILL_DIR/subskills/publish/SKILL.md` and follow its instructions. Use for creating platform-native social content and distributing it across platforms.

### `/write article --publish [platforms...]`

1. Read `$SKILL_DIR/subskills/article/SKILL.md` and craft the long-form content
2. Then read `$SKILL_DIR/subskills/publish/SKILL.md` and adapt/distribute across platforms

### No Argument

If `$ARGUMENTS` is empty, ask the user which mode they need:

1. **article** — "I need to write a long-form piece (blog, essay, guide, tutorial, newsletter)"
2. **publish** — "I need to create and distribute platform-native content (X, LinkedIn, Threads, Bluesky, TikTok, YouTube)"
3. **article --publish** — "I need to write an article and then distribute it"
