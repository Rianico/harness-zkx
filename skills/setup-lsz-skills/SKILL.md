name: setup-lsz-skills
description: Sets up an `## Agent skills` block in AGENTS.md/CLAUDE.md and `docs/agents/` so the engineering skills know this repo's issue tracker, triage labels, and domain doc layout. Also initializes the ADR CLI (`adr init docs/adr`).
disable-model-invocation: true
---

# Setup LSZ Skills

Scaffold the per-repo configuration that the LSZ engineering skills assume:

- **ADR CLI** — initialize the ADR directory (`docs/adr`)
- **Issue tracker** — where issues live (GitHub, GitLab, or local markdown)
- **Triage labels** — the strings used for the five canonical triage roles
- **Domain docs** — where `CONTEXT.md` and ADRs live, and the consumer rules for reading them

This is a prompt-driven skill, not a deterministic script. Explore, present what you found, confirm with the user, then write.

## Process

### 1. ADR CLI Initialization (MANDATORY)

Before configuring other skills, initialize the ADR directory to ensure all architectural decisions are tracked in the correct location.

**Action:** Run the following command via `Bash`:
```bash
adr init docs/adr
```

### 2. Explore

Look at the current repo to understand its starting state. Read whatever exists; don't assume:

- `git remote -v` and `.git/config` — is this a GitHub/GitLab repo?
- `AGENTS.md` and `CLAUDE.md` at the repo root — does either exist? Is there already an `## Agent skills` section?
- `CONTEXT.md` and `CONTEXT-MAP.md` at the repo root
- `docs/adr/` and any `src/*/docs/adr/` directories
- `docs/agents/` — does this skill's prior output already exist?
- `.scratch/` — sign that a local-markdown issue tracker convention is already in use

### 3. Present findings and ask

Summarise what's present and what's missing. Then walk the user through the decisions **one at a time** — present a section, get the user's answer, then move to the next.

**Section A — Issue tracker.**
- **GitHub** — issues live in the repo's GitHub Issues (uses the `gh` CLI)
- **GitLab** — issues live in the repo's GitLab Issues (uses the `glab` CLI)
- **Local markdown** — issues live as files under `.scratch/<feature>/`
- **Other** (Jira, Linear, etc.) — freeform prose description

**Section B — Triage label vocabulary.**
Canonical roles: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`.

**Section C — Domain docs.**
- **Single-context** — one `CONTEXT.md` + `docs/adr/` at root.
- **Multi-context** — `CONTEXT-MAP.md` pointing to per-context `CONTEXT.md` files.

### 4. Confirm and edit

Show the user a draft of:
- The `## Agent skills` block to add to `CLAUDE.md` or `AGENTS.md`.
- The contents of `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, `docs/agents/domain.md`.

### 5. Write

**Pick the file to edit:**
- If `CLAUDE.md` exists, edit it.
- Else if `AGENTS.md` exists, edit it.
- If neither exists, ask the user which one to create.

The block:
```markdown
## Agent skills

### Issue tracker
[one-line summary]. See `docs/agents/issue-tracker.md`.

### Triage labels
[one-line summary]. See `docs/agents/triage-labels.md`.

### Domain docs
[one-line summary]. See `docs/agents/domain.md`.
```

Then write the three docs files using the seed templates in the skill folder:
- `issue-tracker-github.md`
- `issue-tracker-gitlab.md`
- `issue-tracker-local.md`
- `triage-labels.md`
- `domain.md`

### 6. Done

Tell the user the setup is complete and which engineering skills (`to-issues`, `tdd`, `diagnose`, etc.) will now read from these files.
