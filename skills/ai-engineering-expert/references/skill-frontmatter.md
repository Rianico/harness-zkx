# Skill Frontmatter Reference

All available frontmatter fields for Claude Code skills.

## Required Fields

| Field | Description |
|-------|-------------|
| `name` | Display name for the skill; if omitted, uses the directory name |
| `description` | What the skill does and when to use it; Claude uses this to decide when to apply the skill |

## Optional Fields

| Field | Description |
|-------|-------------|
| `when_to_use` | Additional context for when Claude should invoke the skill, such as trigger phrases or example requests |
| `argument-hint` | Hint shown during autocomplete to indicate expected arguments, like `[issue-number]` or `[filename] [format]` |
| `arguments` | Named positional arguments for `$name` substitution in the skill content; accepts a space-separated string or a YAML list |
| `disable-model-invocation` | Set to `true` to prevent Claude from automatically loading this skill; default is `false` |
| `user-invocable` | Set to `false` to hide from the `/` menu; default is `true` |
| `allowed-tools` | Tools Claude can use without asking permission when this skill is active; accepts a space-separated string or a YAML list |
| `model` | Model to use when this skill is active; accepts the same values as `/model`, or `inherit` to keep the active model |
| `effort` | Effort level when this skill is active; options include `low`, `medium`, `high`, `xhigh`, `max` |
| `context` | Set to `fork` to run in a forked subagent context |
| `agent` | Which subagent type to use when `context: fork` is set |
| `hooks` | Hooks scoped to this skill's lifecycle |
| `paths` | Glob patterns that limit when this skill is activated; accepts a comma-separated string or a YAML list |
| `shell` | Shell to use for inline shell commands; accepts `bash` (default) or `powershell` |

## Example Frontmatter

### Minimal (Required Only)

```yaml
---
name: my-skill
description: Does something useful when you need X.
---
```

### Full Example

```yaml
---
name: tdd-cycle
description: Execute a compact TDD workflow with strict RED, GREEN, and REFACTOR discipline.
when_to_use: Use for test-first implementation, bug fixes, regression tests.
argument-hint: "<feature or module> [--incremental|--suite] [--coverage 80]"
arguments:
  - feature
  - mode
disable-model-invocation: false
user-invocable: true
allowed-tools:
  - Agent
  - Bash
  - Read
  - Write
  - Edit
model: inherit
effort: high
context: fork
agent: developer
hooks:
  PreToolUse: echo "Starting tool use"
paths:
  - "src/**/*.ts"
  - "tests/**/*.ts"
shell: bash
---
```

## Field Details

### `name`

- Maximum 64 characters
- Lowercase letters, numbers, and hyphens only
- No XML tags
- Prefer gerund form (verb + -ing): `processing-pdfs`, `analyzing-spreadsheets`
- Acceptable alternatives: noun phrases (`pdf-processing`), action-oriented (`process-pdfs`)
- Avoid: vague names (`helper`, `utils`), overly generic (`documents`, `data`)

### `description`

- Write in **third person** (injected into system prompt; inconsistent POV causes discovery failures)
- Include **both** what the skill does AND when to use it
- Lead with a one-line identity sentence
- Include trigger vocabulary: verbs, artifact names, domains, topic words
- Signal scope and depth explicitly
- Maximum 1024 characters

### `when_to_use`

Supplements `description` with specific trigger patterns:
- Trigger phrases the user might say
- Example requests that should invoke this skill
- Context conditions that make this skill relevant

### `argument-hint`

- Use square brackets for optional parts: `[optional]`
- Use angle brackets for required parts: `<required>`
- Include common flags after the main arguments

```yaml
argument-hint: "[balanced|uncle-bob|fowler|evans] <topic>"
```

### `arguments`

Named positional arguments that get substituted in the skill content via `$name`:

```yaml
arguments: feature mode
# or
arguments:
  - feature
  - mode
```

Used in skill body as `$feature`, `$mode`.

### `allowed-tools`

Restricts which tools Claude can use without permission prompts:

```yaml
allowed-tools: Agent Bash Read Write Edit
# or
allowed-tools:
  - Agent
  - Bash
  - Read
  - Write
  - Edit
```

### `model`

Override the model for this skill:

```yaml
model: opus      # Force Claude Opus
model: sonnet    # Force Claude Sonnet
model: haiku     # Force Claude Haiku
model: inherit   # Keep current model (default behavior)
```

### `effort`

Control thinking/effort level:

| Level | Use Case |
|-------|----------|
| `low` | Quick, simple tasks |
| `medium` | Standard complexity |
| `high` | Complex reasoning |
| `xhigh` | Very complex analysis |
| `max` | Maximum effort for critical tasks |

### `context: fork`

Run the skill in a forked subagent context for isolation:

```yaml
context: fork
agent: developer
```

Combined with `agent` field to specify which subagent type handles the forked execution.

### `paths`

Limit skill activation to specific file patterns:

```yaml
paths: "src/**/*.ts, tests/**/*.ts"
# or
paths:
  - "src/**/*.ts"
  - "tests/**/*.ts"
```

### `hooks`

Skill-scoped hooks that fire during the skill's lifecycle:

```yaml
hooks:
  PreToolUse: /path/to/hook.sh
  PostToolUse: /path/to/cleanup.sh
```
