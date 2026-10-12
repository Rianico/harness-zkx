---
name: setup-lsz-skills
description: >-
  Scaffold and migrate repo configuration for engineering skills — issue tracker, triage labels, GLOSSARY.md layout, CLI toolchain, and .lsz runtime. Use when initializing a repo, updating toolchain, or migrating CONTEXT.md.
disable-model-invocation: true
---

# Setup LSZ Skills

Scaffold a repo for the engineering skills. One deterministic script drives every
step. `CONTEXT.md` is deprecated; `GLOSSARY.md` is canonical.

Run the script from the repo root with `uv run`:

```bash
uv run skills/setup-lsz-skills/scripts/setup_detect.py --cwd . <command>
```

## Steps

### 1. Detect the environment

Run detection and write the config snapshot.

```bash
uv run skills/setup-lsz-skills/scripts/setup_detect.py detect
uv run skills/setup-lsz-skills/scripts/setup_detect.py detect --write-env
```

Detection inspects the CLI toolchain, git provider, and steering file.
`detect --write-env` writes compact YAML to `docs/agents/env.yaml`. Review that
file; it records the detected toolchain and the deprecated `CONTEXT.md` files.

### 2. Migrate deprecated files

Preview, then run the `CONTEXT.md` -> `GLOSSARY.md` rename.

```bash
uv run skills/setup-lsz-skills/scripts/setup_detect.py migrate --dry-run
uv run skills/setup-lsz-skills/scripts/setup_detect.py migrate
```

The migration renames `CONTEXT.md` to `GLOSSARY.md` and `CONTEXT-MAP.md` to
`GLOSSARY-MAP.md`. It creates `docs/adr/` when missing.

When both `CONTEXT.md` and `GLOSSARY.md` exist, the script stages `CONTEXT.md`
under `.lsz/tmp/CONTEXT.md.pending-merge` and lists it as `merge required`. Do
not clobber. Merge the two glossaries by hand: keep each unique term, resolve
conflicting definitions, then delete the staged file.

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

### 4. Render docs and update pointers

Render the `.j2` templates into `docs/agents/`.

```bash
uv run skills/setup-lsz-skills/scripts/setup_detect.py render
```

Rendering writes `domain.md`, `toolchain.md`, `issue-tracker.md`, and
`triage-labels.md` from `templates/`. Then add minimal navigation pointers to
`AGENTS.md` and mirror them into `CLAUDE.md`. Point at `GLOSSARY.md`,
`docs/agents/env.yaml`, and the rendered docs. Keep pointers only; no inline specs.

## Templates

Templates live in `skills/setup-lsz-skills/templates/` and render with the Jinja
3.1 environment `trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True,
undefined=StrictUndefined`. Edit a template, not the rendered output.
