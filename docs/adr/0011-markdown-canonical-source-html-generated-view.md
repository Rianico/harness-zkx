# Use Markdown as Canonical Source and HTML as Generated View

AI workflow artifacts use Markdown as the canonical source for LLM-facing prose because it is token-efficient, maintainable, diffable, and easy for agents to parse. HTML is treated as a generated human-facing view, analogous to a database view: it may improve layout, visual hierarchy, interactivity, and style, but it must not modify or replace the Markdown source.

Generated HTML views are written beside their Markdown source by default, include provenance linking them to the source and flavor snapshot, and may be refreshed only when provenance shows they were generated from the same source. View flavors are applied through stable structural hooks and explicit role annotations, with Open Design MCP/CLI integrations normalized through flavor adapters before rendering.
