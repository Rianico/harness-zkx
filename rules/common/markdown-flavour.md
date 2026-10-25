---
paths:
  - '**/*.md'
---

# Markdown Flavour — Standard links, Obsidian where safe

Use standard markdown links `[text](path)` for cross-references in repository documents. These include skill files, agent docs, ADRs, and changelogs. A wikilink `[[Note]]` targets a vault-relative note. A model or renderer without that vault cannot resolve the target. Resolve the real path first, then link it.

Use other Obsidian syntax when it stays readable outside a vault. Supported elements include callouts `> [!type]`, `==highlight==`, and tags `#tag` or `#nested/tag`. Use wikilinks only inside a true Obsidian vault with the `obsidian-markdown` skill.

- Keep properties (`title`, `tags`, `date`, `aliases`, `cssclasses`) in personal notes. Never place properties in skill files or structured artifacts.
- Use standard markdown links for scraped or external documentation.
- For SKILL.md frontmatter, follow the `skill-authoring` reference (`skills/ai-engineering-expert/subskills/skill-authoring/references/skill-authoring.md`).
- For advanced vault features, load the `obsidian-markdown` skill.
