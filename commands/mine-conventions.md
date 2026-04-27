---
description: Interactive local convention mining. Analyzes git history and interact with user to extract coding patterns.
argument-hint: "<optional_flags>"
---

# Mine Conventions

Analyzes your repository's git history to extract coding patterns and generate rule files interactively.

**How it works:**
Delegates to the `convention-miner` agent, which scans your `git log`, identifies conventions (like commit prefixes or file co-changes), and interact with user to let you select which patterns to formalize into rules.

**Execution Instruction:**
To execute this workflow, you MUST invoke the Agent tool.

Use the Agent tool with these parameters:
- `subagent_type`: "convention-miner"
- `description`: "Mine conventions from git"
- `prompt`: "[Include user constraints. Explicitly instruct the agent to run its git analysis and present options to the user for selecting which patterns to formalize into rules.]"

**Usage:**
```bash
/mine-conventions
```
