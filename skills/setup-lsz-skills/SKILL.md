---
name: setup-lsz-skills
description: >-
  Scaffold and migrate repo configuration for engineering skills — issue tracker, triage labels, GLOSSARY.md layout, CLI toolchain, and .lsz runtime. Use when initializing a repo, updating toolchain, or migrating CONTEXT.md.
disable-model-invocation: true
metadata:
  credits:
    source: https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/SKILL.md
    author: mattpocock
    version: main
    note: Adapted from setup-matt-pocock-skills
---

# Setup LSZ Skills

Scaffold a repo for the engineering skills. One deterministic script drives every
step. `CONTEXT.md` is deprecated; `GLOSSARY.md` is canonical.

Run from this harness repo root (its uv env carries the script's deps) and point
`--cwd` at the target checkout (default: the current directory):

```bash
uv run skills/setup-lsz-skills/scripts/setup_detect.py --cwd /path/to/target <command>
```

## Steps

### 1. Detect the environment

Run detection and write the config snapshot.

```bash
uv run skills/setup-lsz-skills/scripts/setup_detect.py detect
uv run skills/setup-lsz-skills/scripts/setup_detect.py detect --write-env
```

Detection inspects the CLI toolchain, git provider, and steering file.
`detect --write-env` writes compact YAML to `docs/agents/env.yaml` recording
`project`, `provider`, `remote_url`, `steering_file`, `domain_layout` (glossary
paths and deprecated `stale_files`), `runtime.tmp`, `toolchain`, and an `rtk`
section (installed, version). Review that
file before migrating.

### 2. Migrate deprecated files

Preview, then run the `CONTEXT.md` -> `GLOSSARY.md` rename.

```bash
uv run skills/setup-lsz-skills/scripts/setup_detect.py migrate --dry-run
uv run skills/setup-lsz-skills/scripts/setup_detect.py migrate
```

The migration renames `CONTEXT.md` to `GLOSSARY.md` and `CONTEXT-MAP.md` to
`GLOSSARY-MAP.md`. It creates `docs/adr/` when missing.

When both `CONTEXT.md` and `GLOSSARY.md` exist, the script stages a copy of
`CONTEXT.md` under `.lsz/tmp/CONTEXT.md.pending-merge` and lists it as
`merge required`; the original `CONTEXT.md` stays in place untouched. Merge the
two glossaries by hand: keep each unique term, resolve conflicting definitions,
then delete both the staged file and the legacy `CONTEXT.md`.

Set up the workspace temp directory once, idempotently.

```bash
uv run skills/setup-lsz-skills/scripts/setup_detect.py workspace
```

This creates `.lsz/tmp/` and adds `.lsz/*` and `!.lsz/config.yaml` to `.gitignore`.

### 3. Confirm tracker and triage choices

Read the provider in `docs/agents/env.yaml`. Confirm the issue tracker matches
the provider: GitHub uses `gh`, GitLab uses `glab`, local uses files under
`issues/`. Confirm the five canonical triage labels: `needs-triage`, `needs-info`,
`ready-for-agent`, `ready-for-human`, `wontfix`. Ask the user before changing
either choice.

### 4. Evaluate RTK integration

RTK (`rtk`) proxies shell commands and compresses their output. It changes host
state, so the agent asks the user before applying anything.

```bash
uv run skills/setup-lsz-skills/scripts/setup_detect.py rtk --check
uv run skills/setup-lsz-skills/scripts/setup_detect.py rtk --check --agent pi
```

`--check` is read-only. It probes the `rtk` version, the calling agent's hook
file, and the six canonical exclude patterns in `config.toml`. Exit `0` means clean; exit `1` means apply is
needed. The script resolves the agent from `PI_SESSION_ID`,
`ANTIGRAVITY_AGENT`, `CLAUDECODE`, or `CODEX_HOME`. A plain terminal shell
exports none of those, so it exits `2` and asks for `--agent`.

**Agent duty: confirm before applying.** `setup_detect.py` never prompts and
never reads stdin. The calling agent must:

1. Show the `--check` output to the user.
2. Ask whether to install the hook and merge the exclude patterns.
3. Run `--apply` only after an explicit yes.

```bash
uv run skills/setup-lsz-skills/scripts/setup_detect.py rtk --apply --agent pi --dry-run
uv run skills/setup-lsz-skills/scripts/setup_detect.py rtk --apply --agent pi
```

`--apply` runs `rtk init` for the agent (`pi`, `agy`, `claude`, or `codex`),
then merges the canonical exclude patterns into `[hooks] exclude_commands`.
No other config line changes. `--project` installs a project hook instead of a
global one. `--dry-run` prints the plan and writes nothing.

### 5. Render docs and update pointers

Render the `.j2` templates into `docs/agents/`.

```bash
uv run skills/setup-lsz-skills/scripts/setup_detect.py render
```

Rendering writes `domain.md`, `toolchain.md`, `issue-tracker.md`, and
`triage-labels.md` from `templates/`. Then add minimal navigation pointers to
`AGENTS.md`. Keep `CLAUDE.md` as a symlink to `AGENTS.md`; if it is a regular file, mirror the pointers there. Point at `GLOSSARY.md`, `docs/agents/env.yaml`, and the rendered docs. Keep pointers only; no inline specs.

## Templates

Templates live in `skills/setup-lsz-skills/templates/` and render with the Jinja
3.1 environment `trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True,
undefined=StrictUndefined`. Edit a template, not the rendered output.
