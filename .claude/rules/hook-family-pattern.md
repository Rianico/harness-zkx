# Hook Family Pattern

## Purpose
Ensure hook capabilities follow a consistent family-based design for editability, installability, and maintainability.

## Family Directory Structure

```
hooks/
└── <family>/
    ├── install.py      # Required: family-specific installer
    ├── prompt.md       # Required: hook prompt/spec
    └── README.md       # Optional: family documentation
```

## Root Installer Contract

`install-hooks.py` at repository root:
- Is the user-facing management surface
- Dispatches to family-specific installers
- Supports `--family <name>` and `--all` flags

## Installer Requirements

Each `hooks/<family>/install.py` MUST:
1. Copy runtime hook scripts to `.claude/hooks/<family>/`
2. Register copied paths in `settings.json`
3. Be idempotent — running twice produces same result
4. Handle uninstall by removing only its own entries

## Runtime vs Source Separation

- **Source files** stay in `hooks/<family>/`
- **Runtime scripts** are copied to `.claude/hooks/<family>/`
- `settings.json` points to runtime scripts, NOT source files

## Settings Mutation Rules

- Install adds exact missing entry to `settings.json`
- Uninstall removes only exact matching entry
- Delete copied runtime scripts only when entry was removed
- Never modify entries owned by other hook families

## Failure Handling

Personal hooks MUST fail soft by default:
- Missing env vars → degrade gracefully
- Missing files → warn, don't block
- Parse issues → log error, continue
- Local command failures → non-blocking unless explicitly critical

## Documentation Requirements

Each hook family MUST document:
1. Purpose and behavior
2. Install/uninstall commands
3. Configuration inputs
4. Minimal usage example
