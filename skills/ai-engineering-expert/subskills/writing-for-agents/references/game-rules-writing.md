# Game Rules Writing → Agent Docs (first-principles transfer)

Source: game-rule writing tips (Sedjtroll, 2015) — https://sedjtroll.blogspot.com/2015/03/tips-for-rules-writing.html — different audience (human learner) vs LLM with context window, same tension: **correct + approachable + referenceable or unplayed/unfollowed**. Read through keel + writing lens; not literal.

## Transfer table

| Game tip | Agent-doc transfer | LSZ location |
|---|---|---|
| **Correct but approachable > terse VCR manual** | Rules = `STATE, don't explain`; Skills = `HOW with examples`. Old `development-patterns.md` VCR style (131 lines, 6-level ladder fully spelled) → 71-line spine with falsifiable `_Check:` + imperative bullets. | `writing/SKILL.md` — Correct, complete, and teach in order |
| **2nd-person "On your turn, choose…" vs "Each player takes…"** | Imperative 2nd-person present: `Validate once at admission`, `Create topic branch`, not passive `Validation should be performed`. Model follows imperative shortest; passive adds indirection. Negation alone fails — pair ban with positive. | `## Leading words — Voice` |
| **Terminology consistency — one term = one thing** | One leading word = one meaning; define once, use everywhere. `==tight worktree==` token, not `worktree/work-tree/git worktree` synonyms. Ladder collapsed to single line to stop drift. | `Leading words` + `Pruning — single source of truth` |
| **Don't capitalize/bold every term** | Budget emphasis like context load: bold/caps only on first definition, then plain leading word. Every bold spends attention on every re-read. | `Pruning — Budget emphasis` |
| **Images → charts/examples** | No images in LLM window, but **table/chart/example > prose** for mappings/counts/variants. `2p:5 / 3p:5 / 4p:4` is one lookup; `Deal 5 cards for 2 or 3 players…` is a parse. Put example next to rule. | `Pruning — Prefer chart/example` |
| **Organization Theme→Components+Setup→Overview→Turn→End; combine Components+Setup** | **Information hierarchy** in play order: theme → components+setup co-located → overview → steps → end. Keep definition + setup rule under one heading (co-location) rather than scattered. Our `git-convention` single file (§1-5 daily + §6-7 reference) is the same co-location; `git-workflow` daily default stays unconditional, changelog/docs remain reference at the bottom without a second file. | `## Information hierarchy` + `Correct, complete…` |

| **3 audiences: learner / lookup / rules-lawyer** | `Progressive disclosure` serves all three: learner = every-run spine (46-71 lines unconditional), lookup = second read / `paths` conditional, lawyer = disclosed edge cases / `skills:` pointer. Boxed sidebar → frontmatter `paths:` disclosure. | `## Information hierarchy — Progressive disclosure` (three readers) |
| **Cover every edge case, even untested** | Undefined edge = model improvisation. Close every decision the agent can hit, classify `reversible/compensable/irreversible` (keel #5). Suppressions `shrink-only` ladder is explicit no-loophole. | `writing — Correct, complete` + `keel.md #5` |
| **Proofreading + read backwards** | `Verification closes loop` + fresh-state re-run + deterministic `validate-deps.py lint/context-check` + Skeptic subagent as second reader. Reading backwards = reading the doc out of narrative order to catch copy drift. | `## Harness Wiring — Verification` |

## Not transferable

- Literal `Images, images, images` politics, gendered-example advice — less load-bearing for agent; 2nd-person imperative already solves the underlying discoverability problem.

## Two follow-up tweaks this lens suggests (deferred)

1. Add 3-line **terminology glossary** pointer atop `development-patterns.md` (`admission = input boundary`, `emission = output boundary`) to lock `Any/object/dict.get` synonym drift.
2. Use one **chart** for Suppression Ladder as intermediate-reader sidebar behind `paths: ['**/.pyright*', '**/pyproject.toml']` rather than inline single line — purer disclosure; deferred until Ladder triggers often enough to pay its pointer cost.
