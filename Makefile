# Validate-deps convenience targets
# See skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py

VALIDATE_DEPS = uv run skills/ai-engineering-expert/subskills/skill-authoring/scripts/validate-deps.py
PROJECT_ROOT ?= .

.PHONY: validate-deps validate-deps-lint validate-deps-fix

validate-deps:
	$(VALIDATE_DEPS) --project-root $(PROJECT_ROOT) check

validate-deps-lint:
	$(VALIDATE_DEPS) --project-root $(PROJECT_ROOT) lint

validate-deps-fix:
	$(VALIDATE_DEPS) --project-root $(PROJECT_ROOT) fix $(if $(APPLY),,--dry-run)
