# Obsidian Markdown Default

When generating `.md` files, use Obsidian-flavored markdown by default.

## Default Behavior
- Wikilinks (`[[Note]]`) for internal references
- Callouts (`> [!type]`) for admonitions
- `==highlight==` for emphasis
- Obsidian tags (`#tag`, `#nested/tag`)

## Properties (Frontmatter)
Obsidian properties (`title`, `tags`, `date`, `aliases`, `cssclasses`) apply only when writing personal notes or task notes. Do not use them for skill files, project docs, or other structured artifacts.

## Exceptions
- Scraped/external docs (docs-scraper output) — use standard markdown
- SKILL.md frontmatter — follow skill-conventions.md rules
  (body content of SKILL.md still uses Obsidian-flavored syntax)

## Deep Reference
For complex Obsidian syntax, invoke the obsidian markdown skill if available.
