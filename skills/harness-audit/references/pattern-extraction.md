# Pattern Extraction — Cross-Skill Audit Methodology

Deep reference for the `audit_skill_patterns.py` workload. The deterministic half lives in the script; the extraction bar, verdict vocabulary, and treatment discipline live in [criteria.yaml](../data/criteria.yaml). Evolve criteria there, never in this file or in `SKILL.md`.

## When to Run

- Monthly, after installing new skills, or when skills feel duplicated.
- Invocation: `/harness-audit skill_patterns` or `uv run $SKILL_DIR/scripts/audit_skill_patterns.py [--paths <dir> ...] [--json] [--batch-size N]`.

## The Loop

1. **Inventory (deterministic).** Run the script. It resolves the corpus (default `~/.agents/skills`, or `--paths`), follows symlinks, parses frontmatter, reports staleness, and renders the criteria plus the subagent prompt template. The starting batches are alphabetical; regroup them thematically before dispatch.
2. **Batch (model).** Group skills by description themes. Aim for batches of 8–15. Merge tiny themes; split giant ones.
3. **Cross-read (subagents).** Dispatch one fresh subagent per batch with the rendered prompt. Pass the full `SKILL.md` text of each batch skill plus the full `rules/common/*.md` text (small enough to inline). Load deep `references/` bodies only on a second pass, when a candidate needs them.
4. **Merge (model).** Deduplicate candidates across batches. Re-check the promotion bar with evidence from **all** batches combined: a principle found in one skill per batch but two or more skills total is valid.
5. **Verdicts (model proposes, you decide).** Present each candidate with evidence links, verdict, target, and confidence. You approve by number.
6. **Resolve (in-session).** Approved items execute through the repo gates: edits to `rules/` or `skills/`, `scripts/check.sh`, changelog entry, conventional commit. Nothing is persisted. Git history is the record of everything approved; rejected candidates may resurface in later runs, and a resurfaced rejection costs one "skip".

## Input Contract

- Per batch: full `SKILL.md` bodies plus the full `rules/common` text.
- Third-party skills (listed in `skills-lock.json`) are evidence sources only. Promote their patterns into rules; never edit or merge the skills themselves.

## Verdict Schema

Each subagent returns JSON only:

```json
{
  "candidates": [
    {
      "pattern": "1-2 sentences in do-X form",
      "evidence": ["skill-name: §Section", "skill-name: §Section"],
      "violation_risk": "1 sentence",
      "verdict": "promote_to_rule | refactor_skill | merge_skills | already_covered | too_specific",
      "target": "rules/common/<file> §Section, skills/<name>, or the covering artifact",
      "confidence": "high | medium | low"
    }
  ]
}
```

## Treatment Discipline

- A mechanical violation earns a deterministic check — a linter rule, a hook, or a CI step. Never a prose rule.
- One concept keeps one canonical home. Reference it by name; never copy it.
- A pattern the base model follows by default is a no-op. Do not promote it.
- Full statements live in [criteria.yaml](../data/criteria.yaml); the script renders them into every cross-read prompt so doc and prompt cannot drift.

## Completion Criteria

Done when every candidate carries a verdict with evidence and target, you have chosen approve or skip for each, approved items landed through the gates (`scripts/check.sh` green, changelog updated), and the cross-batch merge re-checked the promotion bar against combined evidence.
