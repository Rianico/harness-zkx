---
name: continuous-learning
description: Manages the continuous learning system that observes sessions, detects patterns, and creates learned behaviors (instincts). Provides commands for status, analysis, evolution, and promotion of instincts.
arguments: command
argument-hint: |
  <status|analyze|evolve|promote|projects> -- subcommand
  [--project <id>] -- filter by project
  [--scope <project|global>] -- filter by scope
  [--domain <name>] -- filter by domain
  [--json] -- output as JSON
---

# Continuous Learning Skill

A skill for managing the continuous learning system that observes Claude Code sessions, detects patterns, and evolves learned behaviors.

## Commands

### status

Display all instincts with their confidence scores, domains, and triggers.

```bash
/continuous-learning status [--project <id>] [--scope <project|global>] [--domain <name>] [--json]
```

**Options:**
- `--project <id>`: Filter by project ID
- `--scope <project|global>`: Filter by scope
- `--domain <name>`: Filter by domain
- `--json`: Output as JSON

### analyze

Trigger immediate observation analysis. Reads unprocessed observations, spawns the observer agent, and updates the cursor.

```bash
/continuous-learning analyze [--project <id>] [--all-projects] [--batch-size <n>] [--dry-run] [--json]
```

**Options:**
- `--project <id>`: Analyze specific project
- `--all-projects`: Analyze all projects
- `--batch-size <n>`: Maximum observations to process
- `--dry-run`: Show what would happen without processing
- `--json`: Output as JSON

### evolve

Cluster related instincts and propose draft skills. Requires user approval to create actual skills.

```bash
/continuous-learning evolve [--min-size <n>] [--domain <name>] [--output-dir <path>] [--approve] [--dry-run] [--json]
```

**Options:**
- `--min-size <n>`: Minimum cluster size (default: 2)
- `--domain <name>`: Filter by domain
- `--output-dir <path>`: Output directory for draft skills
- `--approve`: Auto-approve proposals (use with caution)
- `--dry-run`: Show proposals without creating files
- `--json`: Output as JSON

### promote

Promote a project-scoped instinct to global scope. Validates promotion criteria before proceeding.

```bash
/continuous-learning promote <instinct-id> [--force] [--reason <text>] [--dry-run] [--json]
```

**Arguments:**
- `<instinct-id>`: The ID of the instinct to promote

**Options:**
- `--force`: Bypass promotion criteria checks
- `--reason <text>`: Reason for promotion
- `--dry-run`: Show what would happen without promoting
- `--json`: Output as JSON

### projects

List all known projects in the system.

```bash
/continuous-learning projects [--json]
```

### config

View or update configuration settings.

```bash
/continuous-learning config [key[=value]]
```

## Data Storage

All data is stored under `~/.claude/lsz/homunculus/`:

```
~/.claude/lsz/homunculus/
├── instincts/
│   ├── personal/     # Global auto-learned instincts
│   └── inherited/    # Global imported instincts
└── projects/
    └── <project-hash>/
        ├── observations.jsonl  # Project-scoped observations
        ├── .observer-cursor    # Processing cursor
        └── instincts/
            └── personal/       # Project-scoped instincts
```

## Instinct Lifecycle

1. **Creation**: Observer agent detects patterns from observations
2. **Accumulation**: Evidence builds over time, confidence increases
3. **Promotion**: High-confidence instincts across multiple projects become global
4. **Evolution**: Related instincts can be clustered into skills

## Related Components

- **Hooks**: `hooks/observe/` - Observation capture and daemon
- **Agent**: `agents/observer.md` - Pattern detection agent
- **Modules**: `hooks/observe/instinct_manager.py` - Instinct management
