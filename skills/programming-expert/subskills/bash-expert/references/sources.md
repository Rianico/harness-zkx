# Bash-Expert Sources

Raw sources fetched via `docs-scraper` (`skills` scraper → `npx skills` stage). Curated in `SKILL.md`; raw retained in `.lsz/tmp/bash-fetch/` per `docs-scraper` → `ai-engineering-expert` pipeline. Keep this file as audit trail — `SKILL.md` points here, not inline.

## Fetched 2026-09-09 — 9 inputs via `scrape.py skills`

| #   | Skill                                | Repo                             | skill.sh URL                                                                               | Local clone                                                                                        |
| --- | ------------------------------------ | -------------------------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| 1   | `shell`                              | `pproenca/dot-skills`            | `https://www.skills.sh/pproenca/dot-skills/shell`                                          | `.lsz/tmp/bash-fetch/pproenca_dot-skills/skills/.experimental/shell/`                              |
| 2   | `bash-defensive-patterns` (wshobson) | `wshobson/agents`                | `https://www.skills.sh/wshobson/agents/bash-defensive-patterns`                            | `.lsz/tmp/bash-fetch/wshobson_agents/plugins/shell-scripting/skills/bash-defensive-patterns/`      |
| 3   | `bash-scripting`                     | `sickn33/agentic-awesome-skills` | `https://www.skills.sh/sickn33/agentic-awesome-skills/bash-scripting`                      | `.lsz/tmp/bash-fetch/sickn33_agentic-awesome-skills/skills/bash-scripting/`                        |
| 4   | `bash-pro`                           | `rmyndharis/antigravity-skills`  | `https://www.skills.sh/rmyndharis/antigravity-skills/bash-pro`                             | `.lsz/tmp/bash-fetch/rmyndharis_antigravity-skills/skills/bash-pro/`                               |
| 5   | `bash-linux`                         | `vudovn/ag-kit`                  | `https://www.skills.sh/vudovn/ag-kit/bash-linux`                                           | `.lsz/tmp/bash-fetch/vudovn_ag-kit/.agents/skills/bash-linux/`                                     |
| 6   | `linux-shell-scripting`              | `sickn33/agentic-awesome-skills` | `https://www.skills.sh/sickn33/agentic-awesome-skills/linux-shell-scripting`               | `.lsz/tmp/bash-fetch/sickn33_agentic-awesome-skills/skills/linux-shell-scripting/`                 |
| 7   | `error-handling-patterns`            | `wshobson/agents`                | `https://www.skills.sh/wshobson/agents/error-handling-patterns`                            | `.lsz/tmp/bash-fetch/wshobson_agents/plugins/developer-essentials/skills/error-handling-patterns/` |
| 8   | `bats-testing-patterns`              | `wshobson/agents`                | `https://www.skills.sh/wshobson/agents/bats-testing-patterns`                              | `.lsz/tmp/bash-fetch/wshobson_agents/plugins/shell-scripting/skills/bats-testing-patterns/`        |
| 9   | `os-scripting`                       | `sickn33/agentic-awesome-skills` | `https://github.com/sickn33/agentic-awesome-skills/blob/main/skills/os-scripting/SKILL.md` | `.lsz/tmp/bash-fetch/sickn33_agentic-awesome-skills/skills/os-scripting/`                          |

## Extra references consulted

- `sickn33/agentic-awesome-skills/skills/bash-defensive-patterns`, `bash-pro`, `bash-linux` (duplicates under `plugins/agentic-awesome-skills` — deduped)
- `sickn33/agentic-awesome-skills/skills/shellcheck-configuration` (via `bash-scripting` Phase 6)
- Local `pproenca/dot-skills` 49-rule taxonomy (`skills/.experimental/shell/references/*.md` — 9 categories)

## Scrape commands (repro)

```bash
uv run $SKILL_DIR/scripts/scrape.py skills --staging .lsz/tmp/bash-expert-raw --run raw \
  https://www.skills.sh/pproenca/dot-skills/shell \
  https://www.skills.sh/wshobson/agents/bash-defensive-patterns \
  https://www.skills.sh/sickn33/agentic-awesome-skills/bash-scripting \
  https://www.skills.sh/rmyndharis/antigravity-skills/bash-pro \
  https://www.skills.sh/vudovn/ag-kit/bash-linux \
  https://www.skills.sh/sickn33/agentic-awesome-skills/linux-shell-scripting \
  https://www.skills.sh/wshobson/agents/error-handling-patterns \
  https://www.skills.sh/wshobson/agents/bats-testing-patterns \
  https://github.com/sickn33/agentic-awesome-skills/blob/main/skills/os-scripting/SKILL.md

# clones for local read (fallback when npx stage empty)
for repo in pproenca/dot-skills sickn33/agentic-awesome-skills rmyndharis/antigravity-skills vudovn/ag-kit wshobson/agents; do
  gh repo clone $repo .lsz/tmp/bash-fetch/$(echo $repo | tr '/' '_') -- --depth 1
done
```

## How curated

`docs-scraper` Phase 0 → `.lsz/tmp` fetch, then `ai-engineering-expert/skill-authoring` Phase 1-4 → trigger/pattern extraction → `SKILL.md` (≤500 lines, 283-char description) + `references/{defensive-patterns,templates,tooling}.md`. See `skills/docs-scraper/references/skillsh-compose.md` for staging → `out/<skill>` contract.
