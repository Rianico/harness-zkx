# Dialog Contract Pattern

Structural specification for user interactions in coding agent workflows. Tool-agnostic — each agent maps to its native questioning tool.

## Purpose

Ensure consistent, structured user dialogs that work across different coding agents (Claude Code, OpenCode, etc.).

## Contract Structure

```yaml
Dialog:
  header: "<topic or brief summary>"
  question: "<single focused question?>"
  multipleChoice: false
  options:
    - label: "<option A>"
      description: "<implication or tradeoff>"
    - label: "<option B>"
      description: "<implication or tradeoff>"
    - label: "Other"
      description: "Provide custom input"
```

## Field Definitions

| Field | Required | Type | Purpose |
|-------|----------|------|---------|
| `header` | Yes | string | Brief topic/context (≤20 chars) |
| `question` | Yes | string | Single focused question |
| `multipleChoice` | Yes | boolean | `true` if multiple selections allowed |
| `options` | Yes | array | 2-4 options plus "Other" |
| `label` | Yes | string | Short option label |
| `description` | Yes | string | What happens if selected |

## Rules

1. **One question per dialog** — Split complex decisions into multiple sequential dialogs
2. **2-4 options max** — Plus "Other" for custom input
3. **Clear descriptions** — Explain tradeoffs, not just labels
4. **`multipleChoice: true`** — Only when options are truly independent
5. **"Other" always included** — Users can provide custom input
6. **Header is context** — Brief topic for quick recognition

## Tool Mappings by Agent

Different coding agents map this contract to their native tools:

### Claude Code → AskUserQuestion

```yaml
Dialog:                           AskUserQuestion:
  header: "Topic"           →      questions[0].header
  question: "What?"         →      questions[0].question
  multipleChoice: false     →      questions[0].multiSelect
  options: [...]            →      questions[0].options
```

### OpenCode → diag

```yaml
Dialog:                           diag tool:
  header: "Topic"           →      title
  question: "What?"         →      message
  multipleChoice: false     →      (single select mode)
  options: [...]            →      choices array
```

### Other Agents

Map to the agent's native user-interaction tool. The structural contract remains the same.

## Examples

### Single Selection

```yaml
Dialog:
  header: "Design Approach"
  question: "Which approach should we pursue?"
  multipleChoice: false
  options:
    - label: "Monolith (Recommended)"
      description: "Simpler deployment, single codebase"
    - label: "Microservices"
      description: "Independent scaling, higher complexity"
    - label: "Other"
      description: "Propose alternative approach"
```

### Multiple Selection

```yaml
Dialog:
  header: "Review Scope"
  question: "Which areas should the review cover?"
  multipleChoice: true
  options:
    - label: "Security"
      description: "Vulnerabilities, auth, secrets"
    - label: "Performance"
      description: "Latency, memory, throughput"
    - label: "Maintainability"
      description: "Code quality, documentation"
    - label: "Other"
      description: "Specify additional areas"
```

### Confirmation Gate

```yaml
Dialog:
  header: "Understanding Lock"
  question: "Does this accurately reflect your intent?"
  multipleChoice: false
  options:
    - label: "Confirmed"
      description: "Proceed to next phase"
    - label: "Needs revision"
      description: "Clarify or correct items"
    - label: "Other"
      description: "Provide detailed feedback"
```

## Anti-Patterns

❌ **Multiple questions in one dialog:**
```yaml
Dialog:
  question: "What framework and which version?"  # WRONG: two questions
```

❌ **Missing "Other" option:**
```yaml
Dialog:
  options:
    - label: "A"
    - label: "B"  # WRONG: no escape hatch for custom input
```

❌ **Vague descriptions:**
```yaml
Dialog:
  options:
    - label: "Option A"
      description: "Select this"  # WRONG: doesn't explain tradeoff
```

❌ **Too many options:**
```yaml
Dialog:
  options:
    - label: "A"
    - label: "B"
    - label: "C"
    - label: "D"
    - label: "E"  # WRONG: too many, split into multiple dialogs
```

## Integration

Skills define dialogs using the structural YAML format. Each coding agent's runtime maps the Dialog contract to its native tool:

1. Parse the `Dialog:` block
2. Map to agent's native questioning tool
3. Present options to user
4. Process selection
5. Continue workflow or spawn follow-up dialog
