# Subagent Communication

- **Paths:** Always absolute, never relative (cwd resets between bash calls)
- **Code snippets:** Only when load-bearing (bugs, function signatures) — do not recap code merely read
- **Emojis:** Avoid — clear communication requires plain text
- **Tool calls:** No colon prefix — "Let me read the file." not "Let me read the file:"

Example:

```markdown
# Good
Let me read the file.
[tool call]

Relevant paths:
- /Users/zhengxk/stowfiles/claude-skills/harness/everything-claude-code/skills/ai-engineering-expert/SKILL.md

# Bad
Let me read the file:
[tool call]

Here's the code:
[full file content recap]

Check out 📁 skills/ai-engineering-expert/ 🎯
```
