# Dialog Contract Pattern

Standard YAML-like structure for user interactions via the `AskUserQuestion` tool.

## Purpose

Ensure consistent, parseable, and tool-aligned user dialogs across all skills and workflows.

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

## Tool Mapping

Maps directly to `AskUserQuestion` tool:

```yaml
Dialog:                           AskUserQuestion:
  header: "Topic"           →      questions[0].header
  question: "What?"         →      questions[0].question
  multipleChoice: false     →      questions[0].multiSelect
  options: [...]            →      questions[0].options
```

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

### Checkpoint

```yaml
Dialog:
  header: "Design Checkpoint"
  question: "Does this section look right so far?"
  multipleChoice: false
  options:
    - label: "Continue"
      description: "Proceed to next section"
    - label: "Revise"
      description: "Something needs adjustment"
    - label: "Other"
      description: "Provide specific feedback"
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

Skills should define dialogs inline using the YAML format. The orchestrator or skill executor maps the Dialog contract to the appropriate tool call.

When invoked via skill:
1. Parse the `Dialog:` block
2. Call `AskUserQuestion` with mapped fields
3. Process user selection
4. Continue workflow or spawn follow-up dialog
