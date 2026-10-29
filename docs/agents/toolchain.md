# Toolchain

Detected CLI toolchain for `harness-zkx`. Missing tools fall back to the listed alternative.

| Tool | Status | Fallback |
| ---- | ------ | -------- |
| `adr` | found | manual directory + template |
| `fd` | found | find |
| `rg` | found | grep |
| `eza` | found | ls / tree |
| `wt` | found | git worktree |
| `uv` | found | pip / python -m venv |
| `oxlint` | missing | ruff / eslint |
| `oxfmt` | missing | prettier |
| `basedpyright` | found | pyright / mypy |
| `rtk` | found | direct command execution |

Prefer the found tool. When a tool is missing, use its fallback and note the gap
rather than silently changing the workflow.

## RTK (Token Killer)

RTK (`rtk`) proxies shell commands: each agent's hook calls `rtk rewrite` to
compress output before the agent reads it. Current state:

| Field | Value |
| ----- | ----- |
| Installed | yes |
| Version | 0.48.0 |
| Active agent | pi |
| Hook | installed |

The hook is per agent: `pi` reads `~/.pi/agent/extensions/rtk.ts`, Antigravity
reads `.agents/rules/antigravity-rtk-rules.md`, Claude Code patches
`~/.claude/settings.json`, and Codex reads `~/.codex/RTK.md`. Install it with
`setup_detect.py rtk --apply --agent <name>` after the user confirms.

### Native exclude list

RTK must not rewrite `cat`, `head`, `tail`, `grep`, `rg`, or `wc`. Those commands
already print compact output, so compression saves few tokens and risks
truncating lines the agent parses byte-exactly. Apply merges the six canonical
patterns into `[hooks] exclude_commands` and leaves every other config section
untouched.

### Output ceilings and `cat`

The bash tool returns at most 2,000 lines or 50 KB, whichever comes first; the
rest lands in a temp file. Page through long output instead of assuming it
arrived whole. macOS ships BSD `cat`, which has no `cat -A`; use `cat -vet` to
show tabs and line endings.
