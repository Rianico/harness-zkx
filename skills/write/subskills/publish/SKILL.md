---
name: write-publish
description: >-
  Platform-native content creation and multi-platform distribution across X, LinkedIn, Threads, Bluesky, TikTok, YouTube, newsletters. TRIGGER: social posts, threads, scripts, content calendars, crossposting, platform-specific adaptation.
arguments: platform source
argument-hint: |-
  [x|linkedin|threads|bluesky|tiktok|youtube|newsletter] -- target platform
  <source> -- content to adapt (article, notes, url, or description)
metadata:
  managed-by: write
---

# Write & Publish

Turn one idea into platform-native content, then distribute with platform-specific adaptation.

## When to Activate

- Writing X posts, threads, or LinkedIn posts
- Scripting short-form video or YouTube explainers
- Crossposting or distributing content across multiple platforms
- Repurposing articles, podcasts, demos, or docs into social content
- Building a content plan around a launch, milestone, or theme

## First Questions

Clarify:
- **source asset:** what are we adapting from
- **audience:** builders, investors, customers, operators, or general audience
- **platform(s):** X, LinkedIn, TikTok, YouTube, newsletter, or multi-platform
- **goal:** awareness, conversion, recruiting, authority, launch support, or engagement

---

## Section 1: Content Craft

Core rules for creating strong, platform-native content.

### Core Craft Rules

1. **One idea per post.** If the source content has multiple ideas, split across posts.
2. **Hooks matter more than summaries.** Open with something that interrupts attention.
3. **Adapt for the platform.** Never cross-post identical copy.
4. **Use specifics over slogans.** Concrete details beat generic hype.
5. **Keep the ask small and clear.** Match CTA to content and audience.

### Platform-Specific Craft

**X**
- Open fast with a hook, not a summary
- One idea per post or per tweet in a thread
- Keep links out of the main body unless necessary
- Avoid hashtag spam (1-2 max)

**LinkedIn**
- Strong first line (visible before "see more")
- Short paragraphs with line breaks
- Frame around lessons, results, and professional takeaways
- More explicit context than X (LinkedIn audience needs framing)
- 3-5 relevant hashtags

**TikTok / Short Video**
- First 3 seconds must interrupt attention
- Script around visuals, not just narration
- One demo, one claim, one CTA

**YouTube**
- Show the result early
- Structure by chapter
- Refresh the visual every 20-30 seconds

**Newsletter**
- Deliver one clear lens, not a bundle of unrelated items
- Make section titles skimmable
- Keep the opening paragraph doing real work

**Threads**
- Conversational, casual tone
- Shorter than LinkedIn, less compressed than X
- Visual-first if possible

**Bluesky**
- Direct and concise (300 char limit)
- Community-oriented tone
- Use feeds/lists for topic targeting instead of hashtags

### Repurposing Flow

Default cascade:
1. Anchor asset: article, video, demo, memo, or launch doc
2. Extract 3-7 atomic ideas
3. Write platform-native variants
4. Trim repetition across outputs
5. Align CTAs with platform intent

---

## Section 2: Publish & Distribute

Distribute content across platforms with platform-native adaptation.

### Distribution Rules

1. **Primary platform first.** Post to the main platform, then adapt for others.
2. **Respect platform conventions.** Length limits, formatting, link handling all differ.
3. **Stagger timing.** Not all at once — 30-60 min gaps between platforms.
4. **Attribution matters.** If crossposting someone else's content, credit the source.

### Platform Specifications

| Platform | Max Length | Link Handling | Hashtags | Media |
|----------|-----------|---------------|----------|-------|
| X | 280 chars (4000 for Premium) | Counted in length | Minimal (1-2 max) | Images, video, GIFs |
| LinkedIn | 3000 chars | Not counted in length | 3-5 relevant | Images, video, docs, carousels |
| Threads | 500 chars | Separate link attachment | None typical | Images, video |
| Bluesky | 300 chars | Via facets (rich text) | None (use feeds) | Images |

### Workflow

**Step 1: Create Source Content**
- Identify the single core message
- Determine the primary platform (where the audience is biggest)
- Draft the primary platform version first

**Step 2: Identify Target Platforms**
Ask the user or determine from context:
- Which platforms to target
- Priority order (primary gets the best version)
- Any platform-specific requirements

**Step 3: Adapt Per Platform**

For each target platform, transform the content using platform-specific craft rules above.

**Step 4: Post Primary Platform**
Post to the primary platform first:
- Use `x-api` skill for X
- Use platform-specific APIs or tools for others
- Capture the post URL for cross-referencing

**Step 5: Post to Secondary Platforms**
Post adapted versions to remaining platforms:
- Stagger timing (30-60 min gaps)
- Include cross-platform references where appropriate

### Content Adaptation Examples

**Source: Product Launch**

X version:
```
We just shipped [feature].

[One specific thing it does that's impressive]

[Link]
```

LinkedIn version:
```
Excited to share: we just launched [feature] at [Company].

Here's why it matters:

[2-3 short paragraphs with context]

[Takeaway for the audience]

[Link]
```

Threads version:
```
just shipped something cool — [feature]

[casual explanation of what it does]

link in bio
```

**Source: Technical Insight**

X version:
```
TIL: [specific technical insight]

[Why it matters in one sentence]
```

LinkedIn version:
```
A pattern I've been using that's made a real difference:

[Technical insight with professional framing]

[How it applies to teams/orgs]

#relevantHashtag
```

### API Integration

**Batch Crossposting Service (Example Pattern)**
If using a crossposting service (e.g., Postbridge, Buffer, or custom API):

```python
import os
import requests

resp = requests.post(
    "https://your-crosspost-service.example/api/posts",
    headers={"Authorization": f"Bearer {os.environ['POSTBRIDGE_API_KEY']}"},
    json={
        "platforms": ["twitter", "linkedin", "threads"],
        "content": {
            "twitter": {"text": x_version},
            "linkedin": {"text": linkedin_version},
            "threads": {"text": threads_version}
        }
    },
    timeout=30,
)
resp.raise_for_status()
```

**Manual Posting**
Without a crossposting service, post to each platform using its native API:
- X: Use `x-api` skill patterns
- LinkedIn: LinkedIn API v2 with OAuth 2.0
- Threads: Threads API (Meta)
- Bluesky: AT Protocol API

---

## Deliverables

When asked for a campaign, return:
- The core angle
- Platform-specific drafts
- Optional posting order
- Optional CTA variants
- Any missing inputs needed before publishing

## Quality Gate

Before delivering or posting:
- [ ] Each draft reads natively for its platform
- [ ] Hooks are strong and specific
- [ ] One idea per post (split if multiple)
- [ ] No generic hype language
- [ ] No identical content across platforms
- [ ] Length limits respected
- [ ] Links work and are placed appropriately
- [ ] Tone matches platform conventions
- [ ] Media is sized correctly for each platform
- [ ] CTA matches content and audience

## Related Skills

- `write-article` — Long-form content creation for articles and guides
