---
name: branch-worktree-pr
description: >-
  Orchestration for branch+worktree+PR workflow — ticket/spec → isolated worktrees → verify → squash merge. Use when creating a branch from a ticket/spec, dispatching parallel worktrees, merging via wt merge, or opening a PR that closes tickets. TRIGGER: branch, worktree, wt merge, squash, Closes
---

# branch-worktree-pr — ==tight worktree== orchestration

> **Type:** Orchestration — owns sequencing, checkpoints, and fan-out/fan-in. Delegates ==all== implementation to subagents. The orchestrator never writes code.

## When to use

- Creating a `feat/|fix/|doc/` or `map/` branch from a ticket/spec
- Fanning out parallel worktrees for independent write tickets
- Merging worktrees back into parent via `wt merge`
- Opening or landing a squash PR that closes tickets

## When not to use

- No ticket/spec yet → identifying and decomposing tasks first. This skill assumes tickets exist.
- Fork PR you can't push

> [!note] Tracker is pluggable
> The anchor is always the **ticket/spec**, not GitHub. Where issues live is defined by `docs/agents/issue-tracker.md` (GitHub `gh` by default; `.scratch/*.md` or Linear/Jira via freeform). `Closes #NN` is the GitHub binding — other trackers link spec path in PR body.

## Topology — pick one branch

```text
# Single small task
main → feat|fix|doc/<ticket-slug>          # base: main
         | wt --tdd / --refactor (ephemeral --phase children)

# Parallel small tasks (2–3 independent)
main → feat/<a> , feat/<b>                 # each targets main

# Huge — Wayfinder/Grill says SCOPE: multi-branch integration
main → map/<slug> → feat/<a> , feat/<b>    # feat base = map/<slug>, map PR → main
```

Rules:

- `feat|fix|doc/<ticket-slug>` for tickets; `map/<slug>` replaces `dev` for integration.
- Ephemeral children `feat/<slug>--<phase>` are never pushed; only parent branches push to origin.
- Ticket branch base = `map/<slug>` when map exists, else `main`.

> [!tip] Target stays in place — `git switch`, children are `wt` worktrees
> Orchestrator (the coding agent session) is bound to its current cwd (e.g. `/project` on `main`). `wt switch --create <target>` would create a _sibling_ dir `../<repo>-<target>` — the session would have to leave its cwd, beyond its scope. Instead **create the target in place** and keep children isolated:
>
> ```bash
> git switch -c feat/<slug> origin/main   # or map/<slug> — stays in same dir, branch changes in place
> wt switch --create feat/<slug>--moduleA --base feat/<slug> --no-cd  # sibling worktree, cwd stays on target
> ```
>
> `wt switch --create` changing cwd is _desired_ only when you intend to abandon the current session; for orchestrated `ticket → branch` inside the same session, `git switch -c` is the correct first switch. Children still get `wt` hooks (`copy-ignored`/`hash_port`) and isolated dirs. Restore with `git switch main` or `wt switch main` (`^`).

## Worktrunk config — `==environment as source of truth==`

Do not restate hook mechanics in docs beyond a pointer — `.config/wt.toml` is the truth.

- Template: `$SKILL_DIR/references/wt-template.toml` → copy to `.config/wt.toml` on first use: `wt config create --project` then merge template. See [wt-template.toml](references/wt-template.toml).
- Project overrides replace global `~/.config/worktrunk/config.toml`. Per-project `pre-merge` gate is authoritative.
- Minimal template seeds `post-start = "wt step copy-ignored"`, `pre-merge` gate, `hash_port` URL, `pre-remove` port cleanup.

> [!tip] Always `wt`, never raw
> Use `wt switch`, `wt list`, `wt merge`, `wt remove`, `wt step copy-ignored`. Raw `git worktree add` / `git merge` bypass hooks, cold-start copy, and port allocation. Raw is fallback only.

## Phases — do them in order. Each ends on `Done when`.

### Phase 0 — Claim ticket (admission)

Validate once at admission, trust types inside.

```bash
# GitHub (default tracker)
gh issue view <N> --json number,title,body,labels,assignee,comments --jq .
# Local markdown tracker
fd --glob "*.md" .scratch --exec cat {} \;
# Wayfinder map
gh issue view <map-N> --json body --jq .body
```

> [!tip] Shim — typed Python (via _lib) — delegates to gh
>
> ```bash
> uv run scripts/claim_gate.py <N>  # or: uv run scripts/worktree.py claim <N>
> # checks assignees/blockedBy via gh issue view --json (list args, no shell=True)
> ```

Rules:

- Ticket must be **unblocked** and **unassigned** before claim.
- Wayfinder `Blocked by` / native dependencies checked via `issue_dependencies_summary.blocked_by`.

> [!note] Frontier claim
> `gh issue edit <N> --add-assignee @me` is the session's first write — do it before any branch.

**Done when** ticket body + comments are captured and assignee is you.

### Phase 1 — Create target branch _in place_ — stay in session cwd

> [!note] Orchestrator stays in its session dir — don't `wt switch` the target
> The agent was launched at e.g. `/project` on `main`. `wt switch --create <target>` creates a sibling dir `../<repo>-<target>` and would require leaving the session cwd (beyond scope). Create the **target branch in place** instead:

```bash
# From the session cwd (main worktree) — stay in same dir, switch branch in place
 git switch -c feat/<ticket-slug> origin/main   # or map/<slug> for integration
# Verify
 git branch --show-current          # → feat/<ticket-slug> (or map/<slug>)
 wt list --format=json | jq '.[] | select(.is_current) | {branch, path}'
```

> [!tip] Shim — stays in cwd, validates via _lib.wt_list
>
> ```bash
> uv run scripts/create_target.py feat/<ticket-slug> origin/main
> # dispatcher: uv run scripts/worktree.py create-target feat/<ticket-slug> origin/main
> ```

Use `feat|fix|doc` per ticket type; `map/<slug>` for Wayfinder map — both via `git switch -c` in the session worktree. Children will be `wt` siblings (Phase 2).

> [!warning] `wt` only `cd`s with shell integration — Phase 1 stays in place by design
> `git switch -c <target>` keeps you in the session dir (no `wt` side-effect). `wt switch --create <child> --no-cd` keeps children from leaving the target even when integration is active. Under automation (no integration) `wt switch` never `cd`s — verify with `wt list` / `git -C <worktree> branch --show-current` and dispatch subagents with absolute paths.

**Done when** `git branch --show-current == feat/<slug>` (or `map/<slug>`) at the **session path** and `wt list --format=json | jq '.[] | select(.is_current)'` shows the same branch at that path (not a sibling).

> [!warning] Single writer
> Every phase below runs on this parent worktree. Never run ≥2 file-writing subagents in the same worktree — see Phase 2.

### Phase 2 — Dispatch isolated worktrees (fan-out)

Decision:

- Ticket is `read-only` (research, audit) → **no worktree** — run subagent in parent cwd or directly.
- Ticket requires writes → **one ticket = one worktree + one owner subagent**.
- Parallel tickets → parallel worktrees.

Main creates worktrees; subagents work isolated:

```bash
# Create children without leaving the parent target — --no-cd keeps cwd on parent
# Example: feat dispatches isolated modules (your case) — one worktree per module/ticket
wt switch --create feat/<slug>--auth --base feat/<slug> --no-cd   # module A / ticket A
wt switch --create feat/<slug>--store --base feat/<slug> --no-cd  # module B / ticket B
# Legacy phase-named example:
# wt switch --create feat/<slug>--tdd --base feat/<slug> --no-cd
```

> [!tip] Shim — creates child via wt switch --create --no-cd --yes, finds path via _lib.wt_list
>
> ```bash
> COPY=$(uv run scripts/make_copy.py feat/<slug>--auth feat/<slug>)
> # dispatcher: COPY=$(uv run scripts/worktree.py make-copy feat/<slug>--auth feat/<slug>)
> ```

#### Dispatch table — one worktree per isolated module/ticket (feat fans out to modules)

| Child suffix                | When                                         | Subagent template                                                           |
| --------------------------- | -------------------------------------------- | --------------------------------------------------------------------------- |
| `--auth`, `--store`, `--ui` | feat dispatches parallel modules (your case) | `implement` worker scoped to that module's seams (may run `tdd` internally) |
| `--tdd`                     | test-first phase (legacy)                    | `tdd` loop: RED → GREEN → REFACTOR                                          |
| `--refactor`                | second pass / cleanup                        | `refactor-expert` with graded surfaces                                      |
| `--verify`                  | pre-merge gate                               | runs gate in that worktree only                                             |

#### Subagent template (copy per dispatch)

```text
Agent (worker):
  description: "implement <ticket-slug> — <phase>"
  prompt: |
    You are in worktree at <absolute-path> on branch <branch> — only edit there.
    Ticket: <absolute-path-to-spec> (or gh issue <N> body)
    Scope: <files/seams>
    Return format per handoff:
    ## Summary
    ## Artifacts (absolute paths)
    ## Route (COMPLETED|BLOCKED)
    ## Issues
```

**Done when** each worktree subagent returns `COMPLETED` and its `git status --porcelain` in that worktree is inspectable. Main never writes inside child worktrees.

For BDD scenarios driving this phase see [bdd-scenarios.md](references/bdd-scenarios.md).

### Phase 3 — Merge back via `wt merge` (fan-in)

`wt merge <TARGET>` = **merge the current branch INTO the target, then remove the current
worktree** (like GitHub's merge button — confirmed in worktrunk-guide `004-merge.md`). So
fan-in runs **from the child worktree**, naming the parent/map as target. The parent is never
the source; running `wt merge <child>` from the parent worktree deletes the parent.

```bash
# Children were created with --no-cd (cwd stayed on parent) — enter child first
wt switch <child>                 # e.g. wt switch feat/<slug>--tdd
wt merge map/<slug>               # from child: merge child → map, child worktree removed
# or straight to default:
wt merge                          # current → default branch
wt merge <parent> --no-remove     # keep child worktree after merging (debug)
wt list --format=json | jq .
```

> [!tip] Shim — merges from copy, fixes DU/UU/AA inside copy, runs gate via _lib.read_gate
>
> ```bash
> uv run scripts/merge_copy.py "$COPY" map/<slug>
> # dispatcher: uv run scripts/worktree.py merge-copy "$COPY" map/<slug>
> # wt merge <target> --yes is still final gate; Python delegates and fixes conflicts inside copy only
> ```

- `wt merge` runs blocking `pre-merge` gate (project's `.config/wt.toml`).
- Prefer `--squash` for heterogeneous children; `--no-squash` only when preserving bisectability matters.
- Never run `wt merge <child>` from the parent worktree — the parent becomes the merge source and is removed.
- Children created with `--no-cd` left cwd on parent — `wt switch <child>` first, then `wt merge <parent>` from child; without shell integration use `git -C <child-path> wt merge <parent>`.

**Done when** `wt list` shows the child gone, `git log --oneline map/<slug> ^origin/main` contains the child's diff squashed, and the child's branch no longer resolves locally.

If gate fails → Phase 2 iteration (subagent fixes in child worktree, re-dispatch).

### Phase 4 — Verify parent gate (heavy)

Gate is environment, not this doc. Default recommendation (override in `.config/wt.toml`):

```bash
# Gate is .config/wt.toml [pre-merge].gate — auto-scaffolded once via _lib.read_gate
# (sniffs Cargo.toml > pyproject.toml > package.json); unknown stack fails loud
uv run scripts/verify_parent.py  # or: uv run scripts/worktree.py verify
# delegates to wt.toml gate, then git diff --check and git status clean (allows .lsz/tmp)
```

But authoritative gate is `.config/wt.toml [pre-merge]` — skill demands _that_ gate passes, not a hard-coded `npm` string.

**Done when** parent worktree's pre-merge hook exits 0 and `git status --porcelain` is clean or only intended untracked under `.lsz/tmp`.

### Phase 5 — History hygiene (atomic inside, squash outside)

Inside `feat/*` / `map/*`: keep **atomic commits** — one intent per commit, bisectable.

```bash
git add <group> && git commit -m "feat: <what> (#<ticket>)"
# split if code + docs staged together:
git status --porcelain  # audit
git reset HEAD && git add <code> && git commit && git add <docs> && git commit
```

> [!tip] Shim — validates via _lib helpers (git log fallback to merge-base)
>
> ```bash
> uv run scripts/check_history.py  # or: uv run scripts/worktree.py check-history
> # checks atomic commits and CHANGELOG ## [Unreleased] bullet with (#issue) or by @
> ```

Never `git reset --hard` — See `[[git-workflow-conventions]]`:

```bash
git reset HEAD~N          # keep staged
git restore <file>         # discard working tree
git restore --staged <file> # unstage
```

**CHANGELOG:** one bullet under `## [Unreleased]` before PR:

```md
### Added|Changed|Fixed

- Preserve stripped UTF-8 BOM across edit writes (#23).
- Broadened interactive_shell guidance (#32, by @Rianico).
```

Rules: link inline where tracker exists; use `by @<author>` when ticket author ≠ merger — universal, not GitHub-only.

**Co-authored-by trailer (universal):** if ticket/spec author differs from merger, add to **squash** commit message:

```
Co-authored-by: <Ticket Author> <email>
```

Squash loses ancestry — trailer is the only provenance. See `[[git-merge-pr]]` for exact shape.

**Done when** `git log --oneline --no-merges | head` shows atomic commits, `CHANGELOG.md` diff shows one new bullet under `## [Unreleased]` with correct subsection, and `git show -s HEAD --format=%B` contains trailers where needed.

### Phase 6 — Open PR (squash boundary)

```bash
# Push and open PR — ensures Closes trailer and CHANGELOG check via _lib
uv run scripts/open_pr.py feat/<ticket-slug> main <issue-number>
# dispatcher: uv run scripts/worktree.py open-pr feat/<ticket-slug> main <issue-number>
# internally: git push -u origin <branch>, gh pr list --head / gh pr view, gh pr create --fill --base <base>, gh pr edit for Closes, git diff --check (not gh pr diff --check), CHANGELOG [Unreleased]
```

- `Closes #<ticket>` last line when ticket is fully resolved; `Part of #<map>` for wayfinder children.
- PR description: what was done, closed ticket/spec, and `by @<author>` when external.

**Completion for review:**

- [ ] PR `OPEN` with base `main` (or `map/<slug>`)
- [ ] Body ends with `Closes #<ticket>` / `Part of #<map>`
- [ ] `CHANGELOG.md` bullet present
- [ ] Squash preview (`git log origin/main..HEAD`) coherent

> [!warning] NEVER merge without explicit user approval
> **Do NOT** run `gh pr merge`, `wt merge <main>`, or `git merge` that lands the PR. Stop at `gh pr view`/`gh pr diff`. Wait for user's `approve` — user needs to review and run ==extra verification==. If blocked, state `BLOCKED: awaiting PR approval`.

**Done when** PR is `OPEN` and `git diff --check` is clean. Merge is a **user decision**, not a model transition.

### Phase 7 — Tag / Release / Publish (never proactive)

> [!warning] NEVER tag, release, or publish proactively
> At workflow end, **confirm with the user** — present options, wait for explicit approval. Tag-first loop is `develop → release → publish`; tag must exist before registry publish.

Show this dialog and wait:

```text
PR #<N> is open and green.
Do you want to:
  [a] merge PR to <base> now?
  [b] tag/release vX.Y.Z after merge? (npm run release -- X.Y.Z — bumps manifest+lock, moves CHANGELOG Unreleased→[X.Y.Z], commits chore: release, annotated tag, pushes tag to trigger release.yml)
  [c] publish to registry? (interactive_shell only — needs browser OTP; guard asserts tag exists)
  [d] hold — keep PR open for further verification

⚠️  I will not run merge/tag/release/publish until you reply. Which option?
```

Rules from `[[git-workflow-conventions#Tag, Release, And Publish]]`:

- Release demands clean worktree, newer version than current, `vX.Y.Z` not exists, `npm run typecheck && npm test && npm run build` green.
- Release is headless-safe: `npm run release -- X.Y.Z` (or `--dry-run`), creates annotated tag, pushes branch+tag.
- Publish is **interactive only**: `npm login`/`npm publish --registry https://registry.npmjs.org` via `interactive_shell` — hand browser OTP to user. `prepublishOnly` asserts tag exists; verify `npm whoami` + `curl -s https://registry.npmjs.org/<pkg> | jq .["dist-tags"]`.

**Done when** user explicitly replies `no release` or after approved merge/tag/publish gates all pass.

## Completion checklist

- [ ] Ticket claimed (`assignee == me`)
- [ ] Parent `feat|fix|doc/<slug>` or `map/<slug>` worktree created and verified via `wt list`
- [ ] Write tickets fanned out as isolated worktrees (read-only tickets skipped); children merged back via `wt merge` pre-merge gate
- [ ] Parent heavy gate (`wt.toml pre-merge`) green, atomic commits clean, `CHANGELOG.md` bullet under `## [Unreleased]`
- [ ] `Co-authored-by` trailers present when ticket author ≠ merger
- [ ] PR `OPEN` with body ending `Closes #<ticket>` / `Part of #<map>`; diff clean; **NOT merged**
- [ ] Tag/release/publish **confirmed with user** — no proactive tag/publish executed

## Disclosed references

| Trigger                                              | Material                                                          |
| ---------------------------------------------------- | ----------------------------------------------------------------- |
| Fork PR you can't push                               | `[[git-merge-pr]]` — `pr_prefix/<N>-<suffix>` + squash trailers   |
| Upstream `pi-better-edit` sync                       | `CLAUDE.md:Upstream sync` — `absorb/tN-*` worktrees               |
| Worktrunk mechanics (hooks, hash_port, copy-ignored) | `worktrunk-guide` skill, `$SKILL_DIR/references/wt-template.toml` |
| Reset / atomic commits / changelog layout            | `[[git-workflow-conventions]]`                                    |

For full BDD scenarios see [bdd-scenarios.md](references/bdd-scenarios.md).
