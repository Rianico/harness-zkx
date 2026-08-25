# 12. Router Skill Argument-Hint Injection via Global Extension

Date: 2026-08-25

## Status

Accepted

Implements [Context Load](../..//CONTEXT.md#context-load) and [Platform Adapter](../..//CONTEXT.md#platform-adapter)

## Context

Pi's `Skill` type strips `arguments`/`argument-hint` (`SkillFrontmatter [key: string]: unknown`, `formatSkillsForPrompt` only `name`+`description` per `agentskills.io`), so `ai-engineering-expert` router's domain ledger (`skill-authoring | writing | verification | subagent-engineering`) is invisible despite LSZ `Description Budget` 300c / Codex 8000c global needing it. Flat catalog `N×300c` vs router `1×280c` forces hierarchical hidden subskills (`manage`/`managed-by` hidden via `Read` not `Skill`), but without hint the model cannot trigger leaves without manual `/skill`.

Alternative `router: true|false` frontmatter flag was considered to mark routers for injection. However `metadata.manage` already marks routers canonically; adding a second flag would duplicate source of truth (Pruning violation) and require synchronization. Per-leaf injection would re-create `N` cost, conditional injection on prompt match adds variance bug, enlarging description blows 300c.

Decision must be reversible only globally (extension affects all projects), is surprising (future reader expects `arguments` ignored per `dist/core/skills.d.ts`), and involves genuine trade-off between context cost vs discoverability.

## Decision

We will inject `argument-hint` for router skills via a **global** Pi extension `~/.pi/agent/extensions/skill-router-injector.ts` that hooks `before_agent_start`:

- **Filter:** `metadata.manage` exists and `argument-hint` present — parsed from `SKILL.md` frontmatter (yaml-tolerant manual parse handling `|-`/`|`/`>-`/`>`), not from `systemPromptOptions.skills` object (stripped). No new `router:true` field.
- **Inject:** parent `argument-hint` block only (one line per domain, already compressed Category>Verbs, slashes, `TRIGGER:` tail). Leaves with `managed-by` stay dark (0 Metadata Cost).
- **When/Scope:** always inject per **loaded** router (`systemPromptOptions.skills` for this `cwd`), not all on disk. Enables per-project filtering. Fail-soft on read/parse error (warn, don't block turn). Cap at 5 routers with truncation note to keep context lean.
- **Content:** `## Skill Router Arguments (injected)` with `**Router: <name>** (metadata.manage: [...])` + hint lines as ``- `skill-authoring -- ...` `` and footer `→ Load via Read $SKILL_DIR/subskills/<domain>/SKILL.md`.

This mirrors `claude-rules.ts` (scan on `session_start`, append on `before_agent_start`) and `prompt-customizer.ts` (`systemPromptOptions` inspection) patterns.

### Considered Options

- **Rejected: `router: true` flag** — duplicate of `manage`, violates single source, needs sync.
- **Rejected: per-leaf injection** — re-creates `N×` cost, breaks hidden-leaf promise.
- **Rejected: conditional injection on prompt match** — variance bug (weak pointer hides must-have), adds `event.prompt` coupling.
- **Rejected: enlarge description to list leaves** — violates 300c, blows 8000c global.

## Consequences

- Scales to dozens: add domain as `argument-hint` line (outside 300c) + `subskills/<new>/SKILL.md` with `managed-by`, parent stays ~280c (`292c PASS`).
- Keeps `validate-deps.py context-check` gate green; `synced` `agents/openai.yaml` unchanged.
- Adds per-turn ~250c for each loaded router (still cheaper than `N×300c`), hidden leaves remain 0.
- Cross-harness compat: Codex uses hint natively, Pi via extension injection.
- Requires yaml-tolerant parsing (block scalar variance) and global trust (`~/.pi/agent/extensions/` always active).
- Future split of router only when distinct leading word worth its own `300c` permanent load.
