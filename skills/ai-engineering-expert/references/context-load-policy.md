# Context-Load Policy Reference

Full policy contract and enforcement details. The parent spine holds the 20% summary; this file holds the deep 80%.

## Invocation Classes

Every skill declares one of two invocation classes via the canonical `disable-model-invocation` field in `SKILL.md` frontmatter:

| Declaration | Class | Claude Code | Codex |
|-------------|-------|-------------|-------|
| Omit (default `false`) | `implicit-allowed` | Model can invoke autonomously | `allow_implicit_invocation: true` |
| `disable-model-invocation: true` | `explicit-only` | Only user or `$skill` can invoke | `allow_implicit_invocation: false` |

**The field is canonical.** It controls both Claude Code behavior and the generated `agents/openai.yaml`. No separate platform-specific field exists in `SKILL.md` — the sync script maps this single field to each platform's mechanism.

## Selection ≠ Metadata Cost

The invocation class controls _selection_ — whether the model can autonomously pick the skill. It does NOT control _metadata presence_ — the `description` is always in the initial skill-list metadata, visible to the harness on every turn.

An explicit-only skill still pays context load for its description. It is not zero-load. This is the single most surprising fact about the policy and the primary reason it is recorded as an ADR.

## Description Budget Rationale

Codex budgets 8,000 characters for the global initial skill list. It shortens descriptions before omitting skills. At 300 characters per skill, ~25 skills fit without shortening.

The 300-character limit is intentionally conservative — it forces description discipline (front-load triggers, collapse synonyms) and leaves headroom for skill growth.

## Platform Sync Details

### Mapping Table

| `SKILL.md` (canonical) | `agents/openai.yaml` (generated) |
|------------------------|----------------------------------|
| `name` | `interface.display_name` |
| `description` | `interface.short_description` |
| `disable-model-invocation: true` | `policy.allow_implicit_invocation: false` |
| `disable-model-invocation: false` (default) | `policy.allow_implicit_invocation: true` |

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
