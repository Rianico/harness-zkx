---
name: setup-lsz-skills
description: >-
  Sets up an `## Agent skills` block in AGENTS.md/CLAUDE.md and `docs/agents/` so the engineering skills know this repo's issue tracker, triage labels, domain doc layout, and available CLI tools. Also initializes the ADR CLI (`adr init docs/adr`).
disable-model-invocation: true
---

# Setup LSZ Skills

Scaffold the per-repo configuration that the LSZ engineering skills assume:

- **ADR CLI** — initialize the ADR directory (`docs/adr`)
- **Issue tracker** — where issues live (GitHub, GitLab, or local markdown)
- **Triage labels** — the strings used for the five canonical triage roles
- **Domain docs** — where `CONTEXT.md` and ADRs live, and the consumer rules for reading them
- **Toolchain** — which preferred CLI tools are available in this environment

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

**Toolchain detection.** Run the following commands to determine which preferred CLI tools are available:

```bash
for cmd in adr fd rg eza llm-lsp-cli wt uv; do
  if command -v "$cmd" >/dev/null 2>&1; then
    printf "%-15s %s\n" "$cmd" "$(command -v "$cmd")"
  else
    printf "%-15s %s\n" "$cmd" "NOT FOUND"
  fi
done
```

Record which tools are present and which are missing. This determines whether the generated `toolchain.md` recommends the preferred tools or documents the fallback equivalents.

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

**Section D — Toolchain.**
Present the detection results from step 2. For each tool, show:

| Tool | Status | Preferred use | Fallback if missing |
|------|--------|---------------|---------------------|
| `adr` | FOUND / NOT FOUND | ADR CLI for architecture decision records | manual `mkdir` + template |
| `fd` | FOUND / NOT FOUND | File discovery | `find` |
| `rg` | FOUND / NOT FOUND | Content search | `grep` |
| `eza` | FOUND / NOT FOUND | Directory structure | `ls` / `tree` |
| `llm-lsp-cli` | FOUND / NOT FOUND | LSP code intelligence | (optional, no fallback) |
| `wt` | FOUND / NOT FOUND | Worktree management | `git worktree` |
| `uv` | FOUND / NOT FOUND | Python tooling | `pip` / `venv` |

Ask the user:
1. Are these the right tools to document, or should any be added/removed?
2. Should a `## Tool Preferences` section be added to `CLAUDE.md`/`AGENTS.md`? (Only needed if some preferred tools are missing and agents need to know the fallbacks.)

### 4. Confirm and edit

Show the user a draft of:
- The `## Agent skills` block to add to `CLAUDE.md` or `AGENTS.md`.
- The contents of `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, `docs/agents/domain.md`, `docs/agents/toolchain.md`.
- If applicable, the `## Tool Preferences` section for `CLAUDE.md`/`AGENTS.md`.

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

### Toolchain
[one-line summary]. See `docs/agents/toolchain.md`.
```

Then write the four docs files using the seed templates in the skill folder:
- `issue-tracker-github.md`
- `issue-tracker-gitlab.md`
- `issue-tracker-local.md`
- `triage-labels.md`
- `domain.md`
- `toolchain.md`

If the user agreed to add a `## Tool Preferences` section, append it to `CLAUDE.md`/`AGENTS.md`:
```markdown
## Tool Preferences

This environment has the following tool availability. Use the preferred tool when present; fall back to the alternative when it is not.

| Task | Preferred | Fallback |
|------|-----------|----------|
| ADR CLI | `adr` | manual `mkdir` + template |
| File discovery | `fd` | `find` |
| Content search | `rg` | `grep` |
| Directory structure | `eza` | `ls` / `tree` |
| LSP code intelligence | `llm-lsp-cli` | (optional) |
| Worktree management | `wt` | `git worktree` |
| Python tooling | `uv` | `pip` / `venv` |

See `docs/agents/toolchain.md` for the full detected tool landscape.
```

Only include rows where the preferred tool is **NOT FOUND** — if all preferred tools are available, the `## Tool Preferences` section is unnecessary and should be skipped.

### 6. Done

Tell the user the setup is complete and which engineering skills (`to-issues`, `tdd`, `diagnose`, etc.) will now read from these files.
