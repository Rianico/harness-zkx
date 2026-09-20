---
paths:
  - '**/*.md'
---

# Markdown Flavour — Standard links, Obsidian where safe

Use standard markdown links `[text](path)` for cross-references in repo documents (skill files, agent docs, ADRs, changelogs). Do **not** write Obsidian wikilinks `[[Note]]` there: a wikilink names a vault-relative note, so a model or renderer without that vault cannot locate the target. Resolve the real path first, then link it.

Other Obsidian syntax is fine when it stays readable outside a vault: callouts `> [!type]`, `==highlight==`, tags `#tag`/`#nested/tag`. Wikilinks are correct only inside a real Obsidian vault — use the `obsidian-markdown` skill there.

- Properties (`title`, `tags`, `date`, `aliases`, `cssclasses`) — only personal/task notes, never skill files or structured artifacts.
- Exceptions: scraped/external docs → standard markdown; SKILL.md frontmatter → `skill-conventions.md`.
- Deep syntax → `obsidian-markdown` skill.
