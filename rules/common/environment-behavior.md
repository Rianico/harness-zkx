# Environment & Behavior

## 1. Tool Preferences & File Discovery

### Tools Preferences

- **File discovery:** Prefer `fd` for file searching. Example: `fd --glob "*.md" skills`.
- **Content search (text):** Use `rg` for text matching. Example: `rg -n "pattern" skills commands rules`.
- **Structural overview:** Use `eza -T -L 3 .` for directory TOC.
- **Targeted reading:** Prefer agent's `read` tool if files need modification rather than `cat`/`bat` (they may dump entire files and bloat context).
- **File paths:** Always use absolute paths, never relative — cwd resets between bash calls in subagent threads.
- Use tools specializing in AST(Abstract Syntax Tree), Treesitter for code overview and navigation.
- Use lsp tools(if provided) when need to operate on code across a wide range, such as rename a variable across the calling chain. These types of operation is fledged in LSP(Language Server Protocol) ecosystem.
