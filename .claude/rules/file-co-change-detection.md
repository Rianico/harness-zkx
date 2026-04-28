# File Co-Change Detection

## Purpose
Ensure related files are updated together when making changes, reducing the risk of inconsistent or incomplete modifications.

## Co-Change Patterns

### Command-Skill Pairs
When modifying `commands/<name>.md`, check if `skills/<name>-workflow/SKILL.md` or related skills need updates.

### Command-Agent Pairs
When modifying `commands/<name>.md`, verify the corresponding `agents/<name>.md` reflects any changes to orchestration behavior or tool requirements.

### Expert Skills Cluster
Changes to one `skills/*-expert/SKILL.md` often require reviewing other expert skills for consistency in methodology structure.


> NOTE: You can use `rg` or `fd` to identify related files in a quick way.

### Hook Changes
When modifying `hooks/<family>/`, verify:
- `tests/test_hook_install_smoke.py` covers the change
- `hooks/<family>/install.py` is updated if installation logic changed
- `hooks/<family>/README.md` reflects any behavioral changes

### Rules Cluster
When modifying `rules/common/*.md`, consider impact on other rules files for consistency.

## Enforcement
- Pre-commit or PR review should flag when one file in a co-change group is modified without others
- Use as a mental checklist during development, not a hard block

## Exceptions
- Documentation-only changes to one file
- Bug fixes that are isolated to a single component
