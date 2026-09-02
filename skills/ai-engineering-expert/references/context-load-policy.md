# Context-Load Policy Reference

Full policy contract and enforcement details. The parent spine holds the 20% summary; this file holds the deep 80%.

## Invocation Classes

Every skill declares one of two invocation classes via the canonical `disable-model-invocation` field in `SKILL.md` frontmatter:

| Declaration                      | Class              | Claude Code                                                                  | Codex                              | Pi ≥0.84.4                                                                                |
| -------------------------------- | ------------------ | ---------------------------------------------------------------------------- | ---------------------------------- | ----------------------------------------------------------------------------------------- |
| Omit (default `false`)           | `implicit-allowed` | Model can invoke autonomously                                                | `allow_implicit_invocation: true`  | Listed in `<available_skills>` XML — normal load                                          |
| `disable-model-invocation: true` | `explicit-only`    | Only user or `$skill` can invoke (description still listed — selection-only) | `allow_implicit_invocation: false` | **Removed from `<available_skills>` XML** — true zero-load; only `/skill:name` reaches it |

**Origin:** Claude Code. **Pi ≥0.84.4 advances it** — `formatSkillsForPrompt` filters `disableModelInvocation=true` and omits the entry from the system-prompt XML entirely. Claude's gating is selection-only (description stays, model instructed not to pick it); Pi strips it from context (no tokens, no attention).

**The field is canonical.** It controls Claude Code behavior, the generated `agents/openai.yaml`, and — on Pi — prompt inclusion. No separate platform-specific field exists in `SKILL.md` — the sync script maps this single field to each platform's mechanism; Pi applies the filter at prompt-build time.

## Selection vs Metadata Cost — Platform Divergence

**Claude Code (origin):** The invocation class controls _selection_ — whether the model can autonomously pick the skill. It does NOT control _metadata presence_ — the `description` stays in the initial skill-list metadata, visible to the harness on every turn. An explicit-only skill still pays context load for its description. It is not zero-load. This selection≠metadata separation is the single most surprising fact about the original policy and the primary reason it was recorded as an ADR.

**Pi ≥0.84.4 (advanced):** `disable-model-invocation: true` **does** control metadata presence. Skills with the flag are filtered by `formatSkillsForPrompt` (`skills.filter(s => !s.disableModelInvocation)`) and **removed from the `<available_skills>` XML** injected into the system prompt. They pay **zero context/metadata cost** — the model never learns their name until the human invokes `/skill:name`. Design consequence: on Pi, `explicit-only` is the correct tool to remove a skill from skill context; do not add a pointer to it from any always-loaded doc (see `writing-for-agents` — independent surfaces).

## Description Budget Rationale

Codex budgets 8,000 characters for the global initial skill list. It shortens descriptions before omitting skills. At 300 characters per skill, ~25 skills fit without shortening.

The 300-character limit is intentionally conservative — it forces description discipline (front-load triggers, collapse synonyms) and leaves headroom for skill growth.

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

### Soft Warnings (pass CI)

1. Description does not match trigger vocabulary pattern (`trigger|use when|when the user`)

### Semantic Quality (not in CI)

The following are enforced by `skill-authoring` methodology during authoring:

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
# Enforce policy on all skills
uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py context-check

# Single skill
uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py context-check <name>

# JSON output for CI
uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py context-check --json
```
