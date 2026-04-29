# Skill Conventions

Mandatory requirements for all skills in this project.

## Mandatory Requirements

- All skills MUST be placed under `<project_root>/skills/`
- All skills MUST include `name` and `description` in YAML frontmatter
- Descriptions MUST be third-person (not "I can help you...")
- SKILL.md MUST stay under 500 lines
- Reference files MUST be one level deep from SKILL.md (no nested references)

## Prohibited Patterns

- Orchestration logic in skills — use orchestration skills or commands instead
- Content duplication across skills
- Windows-style paths — always use forward slashes
- Vague descriptions like "Helps with documents"

## Reference

Full methodology: invoke the `ai-engineering-expert` skill.

Normative specs:
- Frontmatter: `skills/ai-engineering-expert/references/skill-frontmatter.md`
- Structure: `skills/ai-engineering-expert/references/skill-structure.md`
- Descriptions: `skills/ai-engineering-expert/references/skill-description-patterns.md`
