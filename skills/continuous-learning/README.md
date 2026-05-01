# Continuous Learning System

A system that observes Claude Code sessions, detects patterns, and creates learned behaviors ("instincts") that evolve over time.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CONTINUOUS LEARNING SYSTEM                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐                                                │
│  │ observe.sh      │  PreToolUse/PostToolUse hook                  │
│  │ (shell)         │  - Captures tool events                        │
│  │                 │  - Writes to observations.jsonl               │
│  │                 │  - Signals daemon every N observations        │
│  └────────┬────────┘                                                │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                                │
│  │ observer_daemon │  Python daemon with uv inline deps            │
│  │ (Python)        │  - Sleeps, wakes on SIGUSR1 or interval       │
│  │                 │  - Reads & groups observations                │
│  │                 │  - Spawns observer agent with structured data │
│  │                 │  - Processes agent result (transactional)     │
│  └────────┬────────┘                                                │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                                │
│  │ observer agent  │  Native Claude agent (haiku)                  │
│  │ (haiku)         │  - Receives grouped observations               │
│  │                 │  - Detects patterns                            │
│  │                 │  - Returns structured JSON result              │
│  └────────┬────────┘                                                │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────┐                                                │
│  │ instincts/*.yaml│  Learned behaviors with confidence            │
│  └─────────────────┘                                                │
│                                                                     │
│  ┌─────────────────┐                                                │
│  │ Skill           │  User-facing commands                         │
│  │ (thin)          │  /continuous-learning status|analyze|...      │
│  └─────────────────┘                                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Observation Hook (`hooks/observe/`)

| File | Purpose |
|------|---------|
| `observe.sh` | PreToolUse/PostToolUse hook that captures tool events |
| `detect-project.sh` | Derives PROJECT_ID from git remote URL hash |
| `observer_daemon.py` | Python daemon that prepares data and spawns agent |
| `install.py` | Family installer following project hook pattern |
| `config.py` | Configuration loader with auto-generation |

### 2. Bundled Config (`skills/continuous-learning/scripts/`)

| File | Purpose |
|------|---------|
| `config.properties` | Default configuration (bundled with skill) |

### 3. Observer Agent (`agents/observer.md`)

Fat agent containing pattern detection logic:
- Receives structured JSON payload with grouped observations
- Detects patterns: user corrections, repeated workflows, error resolutions
- Returns structured JSON result with instincts to create/update

### 4. Skill (`skills/continuous-learning/`)

Thin dispatcher with subcommands:
- `status` - Show all instincts with confidence scores
- `analyze` - Trigger immediate observation analysis
- `evolve` - Cluster instincts into draft skills/commands
- `promote` - Promote project instincts to global scope
- `projects` - List all known projects
- `config` - View/update configuration

## Data Storage

```
~/.claude/lsz/homunculus/
├── .observer.pid              # PID of running daemon
├── .observer.lock             # Lock file for startup race prevention
├── config.properties          # Runtime config
├── projects.json              # Project registry
├── observations.jsonl         # Global fallback
├── instincts/
│   ├── personal/              # Global auto-learned instincts
│   └── inherited/             # Global imported instincts
└── projects/
    └── <project-hash>/
        ├── project.json       # Project metadata
        ├── observations.jsonl # Project-scoped observations
        ├── .observer-cursor   # {"line": 1234, "updated_at": "..."}
        └── instincts/
            └── personal/      # Project-scoped instincts
```

## Observation Schema

```json
{
  "timestamp": "2026-04-30T10:00:00Z",
  "event": "tool_start" | "tool_complete",
  "tool": "Read" | "Edit" | "Bash" | "Write" | "...",
  "input": "{...truncated to 5000 chars...}",
  "output": "{...truncated to 5000 chars...}",
  "session": "session-uuid",
  "project_id": "a1b2c3d4e5f6",
  "project_name": "my-react-app",
  "tool_use_id": "toolu_abc123"
}
```

## Instinct Schema

```yaml
---
id: read-before-edit
trigger: "when editing unfamiliar files"
confidence: 0.7
domain: "workflow"
scope: "project"
project_id: "a1b2c3d4e5f6"
created_at: "2026-04-30T10:00:00Z"
updated_at: "2026-04-30T10:05:00Z"
evidence_count: 5
---

# Read Before Edit

## Action
Use Read tool to verify file exists and understand context before editing.

## Evidence
- Session abc123: Edit failed (file not found), then Read succeeded
- Session def456: Similar pattern observed
```

## Configuration

`config.properties`:

```properties
# How many observations before signaling the daemon
signal_every_n=20

# Minimum new observations needed before spawning agent
min_observations_to_analyze=50

# Fallback interval (minutes) if no signal received
run_interval_minutes=5

# Observation retention in days
retention_days=30

# Max file size in MB before archiving
max_file_size_mb=10

# Model for observer agent
observer_model=haiku
```

## Data Flow

### Observation Capture

```
Tool Use (Read, Edit, Bash, etc.)
       │
       ▼
observe.sh hook (PreToolUse/PostToolUse)
       │
       ├─► Write to observations.jsonl
       │
       └─► Every N observations: kill -USR1 $DAEMON_PID
```

### Pattern Detection

```
observer_daemon.py (on SIGUSR1 or interval)
       │
       ├─► Read .observer-cursor for each project
       ├─► Load new observations from cursor position
       ├─► Group by session_id using pandas
       ├─► Build structured JSON payload
       │
       └─► Spawn: claude --agent observer --model haiku -p '{...}'
              │
              ▼
       observer agent processes and returns:
              │
              {
                "instincts_created": [...],
                "instincts_updated": [...],
                "promotions": [...],
                "processed_count": 150,
                "cursor_position": 1234
              }
              │
              ▼
       daemon writes instincts, updates cursor
```

## PID Management

- **PID file**: `~/.claude/lsz/homunculus/.observer.pid`
- **Lock file**: `~/.claude/lsz/homunculus/.observer.lock`

### Singleton Daemon Prevention

1. `observe.sh` checks if daemon is running before lazy-start
2. Uses `flock` (Linux) or `mkdir` (macOS) for atomic check-then-start
3. `observer_daemon.py` validates PID on startup

## Instinct Evolution

### Pattern Types

| Pattern Type | Detection Signal | Confidence |
|--------------|------------------|------------|
| User Correction | Rejected suggestion → different action | 0.5 → 0.7 |
| Repeated Workflow | Same tool sequence 3+ times | 0.7 |
| Error Resolution | Tool failed → succeeded with different approach | 0.6 → 0.8 |

### Promotion Criteria

- Same instinct_id in 2+ projects
- Average confidence >= 0.8
- User approval required

## Development

Tests are in `tests/continuous-learning/` with 198 tests covering all components.

## Decision Log

| # | Decision | Alternatives | Rationale |
|---|----------|--------------|-----------|
| 1 | Hooks as `hooks/observe/` family | Skill-bundled | Follows project pattern |
| 2 | Data under `~/.claude/lsz/homunculus/` | ECC's path | LSZ namespace |
| 3 | Single global daemon | Per-project | Simpler management |
| 4 | Python daemon + uv inline deps | Shell/pyproject.toml | Better data handling |
| 5 | config.properties format | JSON/YAML | Supports comments |
| 6 | Transactional daemon → agent | Agent direct writes | Script controls state |
| 7 | Agent returns structured JSON | Agent writes files | Atomic updates |
| 8 | Haiku model for observer | Sonnet | Cost-efficient |
| 9 | Evolution with approval | Automatic | User control |
| 10 | Single skill with subcommands | Multiple skills | Unified interface |
