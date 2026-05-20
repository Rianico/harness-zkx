# Skill Conventions

Mandatory requirements for all skills in this project.

## Mandatory Requirements

- All skills MUST be placed under `<project_root>/skills/`
- All skills MUST include `name` and `description` in YAML frontmatter
- Descriptions MUST be third-person (not "I can help you...")
- SKILL.md MUST stay under 500 lines
- Reference files MUST be one level deep from SKILL.md (no nested references)
- All skill-internal resource paths MUST use `$SKILL_DIR/` prefix, not relative paths

## Prohibited Patterns

- Orchestration logic in skills — use orchestration skills or commands instead
- Content duplication across skills
- Windows-style paths — always use forward slashes
- Relative paths like `../../references/` — use `$SKILL_DIR/references/` instead
- Vague descriptions like "Helps with documents"

## Reference

Full methodology: invoke the `ai-engineering-expert` skill with the appropriate domain argument:
- `ai-engineering-expert skill-authoring` -- skill design, frontmatter, descriptions, progressive disclosure
- `ai-engineering-expert rules-development` -- rules vs skills boundary, rules design principles
- `ai-engineering-expert agent-harness` -- action space design, observation, error recovery
- `ai-engineering-expert extension-dev` -- MCP servers, hooks, language selection
- `ai-engineering-expert testing` -- AI regression testing patterns
- `ai-engineering-expert process-arch` -- eval-first loop, model routing, session strategy
