# Skill Composition via skill.sh — Workflow Wiring

> Phases **B/C are LLM responsibilities** under `ai-engineering-expert` guidance.
> This doc wires the workflow; it does not deterministically merge skills.

## When to Use

- You have **complementary skills** (multiple skill.sh/GitHub sources) and want **one** new skill.
- Single skill needs **reorganization** under `ai-engineering-expert` rigor.
- Staging lives under `.lsz/tmp/skill-compose` (default), multi-run via `--run`. Delegates to `npx skills` mature client (no raw GitHub API).

## Prerequisites

- Load `ai-engineering-expert` subskills **before** composing:
  - `skill-authoring` — description budget (≤300 chars), trigger vocab, invocation class, platform sync, rules-vs-skills boundary.
  - `writing` — Obsidian-flavored body, progressive disclosure, pruning, source hygiene.
- Source material is already staged by `SkillsScraper` (Phase A deterministic).

## Inputs — Staged Layout

After `scrape.py skills ...`:

```
.lsz/tmp/skill-compose/              # --staging (default)
├── <run>/                           # --run slug (omitted => single run at root)
│   ├── README.md                    # staging index + manifest pointer
│   ├── manifest.json                # machine-readable inputs + staged list
│   ├── stage/<owner>/<repo>/<skill>/
│   │   ├── SKILL.md                 # raw frontmatter + body
│   │   ├── references/*.md          # as in source repo
│   │   └── scripts/*                # as in source repo
│   └── out/<new-skill>/             # LLM write target (you create)
│       ├── SKILL.md
│       ├── references/
│       ├── scripts/
│       └── sources/            # raw originals (copied inside skill)
└── .cache/skills/                   # shared fetch cache (reused across runs)
```

Each `stage/<repo>/<skill>/` preserves origin attribution and file layout (drop-in installable). Read `README.md` + `manifest.json` for inventory before composing.

## CLI — Phase A (Deterministic)

```bash
# Single skill — fetch + stage (even single goes through LLM reorganization)
uv run $SKILL_DIR/scripts/scrape.py skills https://www.skills.sh/sickn33/agentic-awesome-skills/typescript-expert

# Complementary skills — multi-input, named run
uv run $SKILL_DIR/scripts/scrape.py skills \
  https://www.skills.sh/sickn33/agentic-awesome-skills/typescript-expert \
  https://www.skills.sh/sickn33/agentic-awesome-skills/nodejs-best-practices \
  sickn33/agentic-awesome-skills/clean-code \
  --run ts-quality

# GitHub repo as input (whole repo)
uv run $SKILL_DIR/scripts/scrape.py skills https://github.com/sickn33/agentic-awesome-skills --run full-collection

# Bare triple (no scheme)
uv run $SKILL_DIR/scripts/scrape.py skills sickn33/agentic-awesome-skills/browser-automation --run browser

# Force re-fetch, choose method
uv run $SKILL_DIR/scripts/scrape.py skills <inputs> --run my-run --method raw --force
uv run $SKILL_DIR/scripts/scrape.py skills <inputs> --run big-run --method clone  # bulk via git clone
# npx is opt-in: prints manual command, does not stage
uv run $SKILL_DIR/scripts/scrape.py skills <inputs> --method npx
```

`--method auto` (default) maps to `npx`; `raw`/`clone` are deprecated aliases that map to `npx`. Clone cache is handled by npx (XDG), staging is reused across runs.

## Compose — Phases B/C (LLM under ai-engineering-expert)

> Do not script the merge. The LLM decides composition; the doc below is the checklist it follows.

### 1. Read staged sources

- `stage/<repo>/<skill>/SKILL.md` — extract frontmatter `name`, `description`, invocation triggers, risk/category.
- `references/` + `scripts/` inventory — note overlap/dedup candidates (e.g., same-named scripts, duplicated reference topics).
- `manifest.json` — authoritative list, not filesystem walk (handles nested `references/`). Its `inputs[].skillsh_url` / `source` fields are copied verbatim into frontmatter `meta.sources`.

### 2. Design the new skill (ai-engineering-expert)

- **Single responsibility:** one concept per output skill; if sources span distinct responsibilities, split or choose narrowest surface that satisfies actual use (graded surfaces).
- **Description budget:** ≤300 chars, front-loaded leading word, trigger vocab (`use when…`, `when the user…`), third-person. CI gates this (`context-check`).
- **Invocation class:** declare `disable-model-invocation` explicitly; skill list metadata always costs context.
- **Progressive disclosure:** 20% in `SKILL.md` (solves 80%), deep detail behind `references/` pointers. No 500-line spec paste in body.
- **Frontmatter attribution:** every composed `SKILL.md` must include `meta: sources:` in frontmatter (list of original skill.sh URLs) as authoritative attribution. Body `> [!tip] Attribution` callout is supplementary and must point to `sources/` inside the skill (not `.lsz/tmp/.../stage/`). Copy URLs from `manifest.json` inputs (`skillsh_url` / `source`). Example:
  ```yaml
  ---
  name: my-composed-skill
  description: >-
    ... TRIGGER: ...
  meta:
    sources:
      - https://www.skills.sh/github/awesome-copilot/javascript-typescript-jest
      - https://www.skills.sh/wshobson/agents/typescript-advanced-types
  ---
  Raw originals must be copied inside the composed skill at `sources/<owner>/<repo>/<skill>/` (not left only in `.lsz/tmp/.../stage/`).
  ```
- **One concept one location:** consolidate, don't accumulate. Deduplicate scripts (rename on clash: `<origin>-<name>`), deduplicate reference topics.

### 3. Write `out/<new-skill>/`

```
out/<new-skill>/
├── SKILL.md            # new frontmatter (name, description ≤300, disable-model-invocation, meta.sources: [skill.sh URLs])
├── references/
│   ├── <topic>.md      # merged, deduped
│   └── skillsh-compose.md  # optional: keep if composition notes are durable
└── scripts/
    └── <tool>.py       # merged, tests added if needed
├── sources/            # raw originals copied inside skill (not tmp)
│   └── <owner>/<repo>/<skill>/SKILL.md, references/, scripts/
```

- Body uses Obsidian-flavored markdown by default (wikilinks `[[Note]]`, callouts `> [!type]`, `==highlight==`).
- SKILL.md frontmatter follows `skill-conventions.md` rules (no Obsidian properties there). Must include `meta.sources` list (see above) for attribution; body callout supplements but frontmatter is source of truth.
- Validate after write: `uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py context-check` (hard fail if description budget/trigger vocab missing).

### 4. Verify

- Single skill reorganized: check that new `SKILL.md` is strictly better organized than source (clearer triggers, pruned bloat).
- Multi-skill merged: no duplicated `references/` sections, no script name collisions, installable at `skills/<new-skill>/`.
- Multiple runs coexist: previous `.lsz/tmp/skill-compose/<other-run>/` untouched.

## Multi-Run Notes

- `--run <slug>` isolates runs; omit ⇒ single run at `staging_base` (not nested).
- Re-running with same `--run` overwrites that run's `stage/` (to update sources). Different slugs coexist.
- Cache is shared; re-staging same skill in another run hits cache, no re-download unless `--force`.

## Troubleshooting

- **npx timeout / clone:** large repos (e.g., agentic-awesome-skills ~1.9k skills) may time out. Raise `SKILLS_CLONE_TIMEOUT_MS=600000` (10m) or clone manually and pass local path to `skills add`.
- **No skills discovered (`--list` empty):** parser may miss names if CLI output format changes. Run `npx -y skills add <repo> --list` manually to verify; scraper will still attempt `npx add <repo> -y` (install all) as fallback.
- **Private repo:** ensure git auth: `ssh-add -l` (SSH) or `gh auth status` (HTTPS). npx clones via https/ssh with `GIT_SSH_COMMAND` support.
- **Staging location:** npx installs to isolated work dir under `run/_npx/` then copied to `stage/<owner>/<repo>/<skill>/`; check `manifest.json` for `error` entries if staging empty.
