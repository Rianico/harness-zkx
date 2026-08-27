# Skill Composition from skill.sh Sources

Workflow for composing **one new agent skill** from complementary skills fetched
by the `skills` scraper. Fetching/staging (Phase A) is deterministic and done by
`scrape.py`; **all composition is LLM work** governed by the `ai-engineering-expert`
methodology (skill-authoring + writing sub-skills).

> [!info] Scope
> Use when the user wants to merge/reorganize skills into one (e.g. gather several
> complementary skills from skill.sh, then combine them). Single-source input means
> a reorganization pass, not a merge.

## 1. Load the methodology

- `ai-engineering-expert` → domains `skill-authoring` (design, frontmatter, description
  budget, progressive disclosure) + `writing` (agent-document writing) — **always both**.
- Follow the platform's skill conventions for the output (frontmatter rules, description
  ≤ 300 chars with trigger vocabulary).
- Body markdown: follow your project's default markdown flavour (e.g. Obsidian syntax).

## 2. Inventory the staged sources

Inputs live under `<staging_root>/<run>/`:

```
stage/SOURCES.md                         # index: origin repo + verbatim frontmatter
stage/<repo>/<skill>/SKILL.md            # the actual content the LLM composes from
stage/<repo>/<skill>/references/...      # deep reference / cheatsheets / configs
stage/<repo>/<skill>/scripts/...         # executable logic
```

1. Read `SOURCES.md` for the map (which repo, which frontmatter, where each skill sits).
2. Read every staged `SKILL.md` fully — the content, not just the index.
3. For each source note: **what it contributes** (its unique methodology), **what overlaps**
   (same tooling, scripts, reference topics, trigger phrases).

> [!tip] Deterministic-vs-semantic
> `stage/` is fetch output — never edit sources in place. Copy what you keep into
> `out/<new-skill>/`; discard the rest. The `out/` dir is the only place you write.

## 3. Choose the composition strategy

| Situation | Strategy |
|-----------|----------|
| Skills cover distinct phases of one workflow | **Merge** — one unified SKILL.md with shared references |
| Skills heavily overlap (near-duplicates) | **Reorganize** — keep the strongest, fold in gaps, delete redundancy |
| One strong source + minor helpers | **Absorb** — helpers become references/scripts of the main skill |
| Single source only | **Reorganize** — sharpen, unbundle, re-disclose |

## 4. Write `out/<new-skill>/`

```
out/<new-skill>/
├── SKILL.md
├── references/...        # deduped, one concept one location
└── scripts/...           # deduped, renamed to avoid clashes
```

**SKILL.md:**

- One coherent `name` (kebab-case) and a single `description` (≤ 300 chars, third person,
  trigger vocabulary — "use when …"). Pull these from the strongest source; reconcile
  conflicting descriptions instead of concatenating.
- 80/20 body: the top-20% cross-source methodology inline; deep detail behind
  `references/` pointers (progressive disclosure).
- Keep a short `## Origin`/attribution note listing the sources and repos you merged
  (honest lineage, per artifact trail).
- Keep frontmatter that the platform conventions require (e.g. category/risk if the
  source repo used them — reconcile, don't stack).

**Merging references/scripts (dedup):**

- Same-named reference across sources → keep one, consolidate unique content into it.
- Same-purpose scripts → keep the best impl, drop clones.
- Name clashes across sources → rename with a prefix rather than overwriting.
- Update all pointers inside the merged SKILL.md + references to the new layout.

## 5. Validate

- Frontmatter present, description non-empty and ≤ 300 chars, trigger vocabulary present
  (soft gate). If the `skill-authoring` validator is available:
  ```bash
  uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py context-check
  ```
- No orphan references: every `references/`/`scripts/` pointer from SKILL.md resolves to
  a file in `out/<new-skill>/`.
- No duplicate concepts: `rg` the merged tree for repeated headings/scripts before shipping.

## Completion criteria

- One `out/<new-skill>/SKILL.md` that reads as a single skill, not a stack of pasted skills.
- All kept content attributed in the `## Origin` note; nothing unowned.
- References/scripts deduped; no clash/overwrite; pointers resolve.

## Anti-patterns

- **Paste-stacking** — concatenating sources without dedup → duplicate concepts, bloat.
- **Editing stage/ sources** — keep fetch output pristine; write only under `out/`.
- **Silent loss** — dropping source methodology without noting it in `## Origin`.
- **Concatenated descriptions** — compress to one ≤300-char description.
