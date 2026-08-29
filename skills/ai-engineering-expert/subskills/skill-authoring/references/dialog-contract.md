# Dialog Contract Pattern

Structural specification for user interactions in coding agent workflows. Present questions as plain text — structured, readable, and tool-free.

## Purpose

Ensure consistent, structured user dialogs. Use plain text to present questions — no special tools required.

## Contract Structure

```yaml
Dialog:
  header: '<topic or brief summary>'
  question: '<single focused question?>'
  multipleChoice: false
  options:
    - label: '<option A>'
      description: '<implication or tradeoff>'
    - label: '<option B>'
      description: '<implication or tradeoff>'
    - label: 'Other'
      description: 'Provide custom input'
```

## Field Definitions

| Field            | Required | Type    | Purpose                               |
| ---------------- | -------- | ------- | ------------------------------------- |
| `header`         | Yes      | string  | Brief topic/context (≤20 chars)       |
| `question`       | Yes      | string  | Single focused question               |
| `multipleChoice` | Yes      | boolean | `true` if multiple selections allowed |
| `options`        | Yes      | array   | 2-4 options plus "Other"              |
| `label`          | Yes      | string  | Short option label                    |
| `description`    | Yes      | string  | What happens if selected              |

## Rules

1. **One question per dialog** — Split complex decisions into multiple sequential dialogs
2. **2-4 options max** — Plus "Other" for custom input
3. **Clear descriptions** — Explain tradeoffs, not just labels
4. **`multipleChoice: true`** — Only when options are truly independent
5. **"Other" always included** — Users can provide custom input
6. **Header is context** — Brief topic for quick recognition

## Chaining & Conditional Dialogs

Chain one question per dialog; branch only on the prior answer. Typical spine: `Q1 Project Shape (flavor) → Q2 Verification Gate (multipleChoice, defaults per Q1) → Q3 Coverage (conditional — only if Tests ∈ Q2, else skip) → Q4 CI Release`. Omitted grilling defaults to `Tests=on, Coverage=off, CI=Yes, threshold 80` — direct dispatch still byte-identical. Keep sequential — never ask parallel questions. Scaffold example: `Project Shape → Verification Gate (Formatter/Linter/Type/Tests) → Coverage (No/80%/90%/Other) → CI Release (Yes/No/Other)`; `--with-coverage` is leaf that changes bytes, skipping a gate only skips its `verify` step.

## Rendering as Plain Text

Present the contract as a clear, structured block of plain text:

```
**<header>**

<question>

1. <option A> — <description>
2. <option B> — <description>
3. Other — <provide custom input>
```

The YAML contract is the design artifact. The plain-text rendering is how it reaches the user. Keep the same structure: one question per dialog, 2-4 options plus "Other", clear descriptions explaining tradeoffs.

## Examples

### Single Selection

```yaml
Dialog:
  header: 'Design Approach'
  question: 'Which approach should we pursue?'
  multipleChoice: false
  options:
    - label: 'Monolith (Recommended)'
      description: 'Simpler deployment, single codebase'
    - label: 'Microservices'
      description: 'Independent scaling, higher complexity'
    - label: 'Other'
      description: 'Propose alternative approach'
```

### Multiple Selection

```yaml
Dialog:
  header: 'Review Scope'
  question: 'Which areas should the review cover?'
  multipleChoice: true
  options:
    - label: 'Security'
      description: 'Vulnerabilities, auth, secrets'
    - label: 'Performance'
      description: 'Latency, memory, throughput'
    - label: 'Maintainability'
      description: 'Code quality, documentation'
    - label: 'Other'
      description: 'Specify additional areas'
```

### Confirmation Gate

```yaml
Dialog:
  header: 'Understanding Lock'
  question: 'Does this accurately reflect your intent?'
  multipleChoice: false
  options:
    - label: 'Confirmed'
      description: 'Proceed to next phase'
    - label: 'Needs revision'
      description: 'Clarify or correct items'
    - label: 'Other'
      description: 'Provide detailed feedback'
```

## Anti-Patterns

❌ **Multiple questions in one dialog:**

```yaml
Dialog:
  question: 'What framework and which version?' # WRONG: two questions
```

❌ **Missing "Other" option:**

```yaml
Dialog:
  options:
    - label: 'A'
    - label: 'B' # WRONG: no escape hatch for custom input
```

❌ **Vague descriptions:**

```yaml
Dialog:
  options:
    - label: 'Option A'
      description: 'Select this' # WRONG: doesn't explain tradeoff
```

❌ **Too many options:**

```yaml
Dialog:
  options:
    - label: 'A'
    - label: 'B'
    - label: 'C'
    - label: 'D'
    - label: 'E' # WRONG: too many, split into multiple dialogs
```

## Integration

Skills define dialogs using the structural YAML format. Each coding agent's runtime maps the Dialog contract to its native tool:

1. Parse the `Dialog:` block
2. Map to agent's native questioning tool
3. Present options to user
4. Process selection
5. Continue workflow or spawn follow-up dialog
