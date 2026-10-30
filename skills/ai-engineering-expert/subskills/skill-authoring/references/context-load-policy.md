# Context-Load Policy Reference

Full policy contract and enforcement details. `skill-authoring` holds the summary. This file holds the deep 80%.

## Invocation Classes

Every skill declares one of two invocation classes via the canonical `disable-model-invocation` field in `SKILL.md` frontmatter:

| Declaration                      | Class              | Claude Code                                                                  | Codex                              | Pi ≥0.84.4                                                                                |
| -------------------------------- | ------------------ | ---------------------------------------------------------------------------- | ---------------------------------- | ----------------------------------------------------------------------------------------- |
| Omit (default `false`)           | `implicit-allowed` | Model can invoke autonomously                                                | `allow_implicit_invocation: true`  | Listed in `<available_skills>` XML — normal load                                          |
| `disable-model-invocation: true` | `explicit-only`    | Only user or `$skill` can invoke (description still listed — selection-only) | `allow_implicit_invocation: false` | **Removed from `<available_skills>` XML** — true zero-load; only `/skill:name` reaches it |

**Base standard:** the open Agent Skills spec ([agentskills.io](https://agentskills.io)) — `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. `disable-model-invocation` is an enhancement beyond that spec, shared by Claude Code and Pi. **Pi ≥0.84.4 semantics are the default enhancement** — `formatSkillsForPrompt` filters `disableModelInvocation=true` and omits the entry from the system-prompt XML entirely. Claude's gating is selection-only (description stays, model instructed not to pick it). Pi strips it from context (no tokens, no attention).

**The field is the single switch.** It controls Claude Code behavior, the generated `agents/openai.yaml`, and prompt inclusion on Pi. No separate platform-specific field exists in `SKILL.md`. The sync script maps this field to each platform. Pi applies the filter at prompt-build time.

## Selection vs Metadata Cost — Platform Divergence

**Claude Code (origin):** The invocation class controls _selection_ — whether the model can autonomously pick the skill. It does NOT control _metadata presence_. The `description` stays in the initial skill-list metadata, visible on every turn. An explicit-only skill still pays context load for its description. It is not zero-load. This selection-versus-metadata separation is surprising, and it is the primary reason this policy became an ADR.

**Pi ≥0.84.4 (advanced):** `disable-model-invocation: true` **does** control metadata presence. Skills with the flag are filtered by `formatSkillsForPrompt` (`skills.filter(s => !s.disableModelInvocation)`) and **removed from the `<available_skills>` XML** injected into the system prompt. They pay **zero context/metadata cost** — the model never learns their name until the human invokes `/skill:name`. Design consequence: on Pi, `explicit-only` removes a skill from context. Keep always-loaded docs free of pointers to it.

## Description Budget Rationale

Codex budgets 8,000 characters for the global initial skill list. It shortens descriptions before omitting skills. At 300 characters per skill, ~25 skills fit without shortening.

The 300-character limit is intentionally conservative. It forces description discipline and leaves headroom for skill growth. Every description must fit the **Tripartite Formula**:
1. **What it is:** Category noun or role anchor. Identity in the first 50 characters.
2. **What it does:** Concrete third-person action verbs defining capabilities and outputs.
3. **When to use:** Required decision boundary with `Use when...` or `when the user...`. Embed symptom keywords here.
4. **Negative boundary (optional):** Exclusion clause such as `Do not use for...` or `defer to...` to prevent collisions.

Three parts are required. The negative boundary is an optional lever.

### Subskill Router Budget

Subskills managed by router skills (`metadata.managed-by`) enter system prompts when prompt-building extensions fold their descriptions into router blocks. Subskill descriptions target **≤205 characters** (with the same 300-character hard limit) and must adhere to the Tripartite Formula with concrete symptom keywords.

## Platform Sync Details

### Mapping Table

| `SKILL.md` (canonical)                      | `agents/openai.yaml` (generated)          | Pi ≥0.84.4 (`<available_skills>` XML) |
| ------------------------------------------- | ----------------------------------------- | ------------------------------------- |
| `name`                                      | `interface.display_name`                  | `<name>` when visible                 |
| `description`                               | `interface.short_description`             | `<description>` when visible          |
| `disable-model-invocation: true`            | `policy.allow_implicit_invocation: false` | **Omitted from XML** — zero-load      |
| `disable-model-invocation: false` (default) | `policy.allow_implicit_invocation: true`  | Listed in XML — normal load           |

### Deliberately Omitted

- `interface.default_prompt` — AI-generated, non-deterministic. Users who want it run Codex-native tooling.
- `interface.icon_small`, `icon_large`, `brand_color` — only when explicitly provided.
- `dependencies.tools` — MCP tool declarations, out of scope for initial sync.

### Regeneration Contract

`sync` always regenerates from canonical source. There is no incremental edit mode. There is no drift detection — the output is always fresh. This simplifies the contract: the generated file is disposable.

## Enforcement Contract

### Hard Gates (fail CI)

1. `description` field missing from `SKILL.md` frontmatter
2. `description` value is empty string
3. `description` length exceeds 300 characters

### Script Checks & Warnings (pass CI)

1. **Required `Use when...`:** Description must match `\buse\s+(?:[a-z_\-]+\s+)?when\b`.
2. **Symptom keywords standard:** Description must contain problem signals or symptom keywords.
3. **Deprecated `TRIGGER:` tag:** Flags legacy `TRIGGER:` pseudo-syntax for removal.
4. **Negative boundary detection:** Recognizes opt-in exclusion clauses (`do not use`, `not for`, `defer to`).

### Semantic Quality (not in CI)

The following are enforced by `skill-authoring` methodology during authoring:

- Tripartite formula compliance (What it is + What it does + When to use via `Use when...`)
- Third-person voice (no "I can help you...")
- Front-loaded leading word (first sentence distinguishes from other skills)
- No trigger duplication with another skill's description
- Concrete, specific scope boundaries

## Scope

- **Enforced on:** all skills under `skills/` directory
- **Not enforced on:** third-party skills in `skills-lock.json`
- **No exemption mechanism** — all owned skills comply. The policy is a contract, not guidance.

## Verification

```bash
# Enforce policy across the whole skill tree
uv run $SKILL_DIR/scripts/validate-deps.py context-check

# JSON output for CI
uv run $SKILL_DIR/scripts/validate-deps.py context-check --json
```

`context-check` scans the whole tree. It has no working single-skill mode.
