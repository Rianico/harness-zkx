---
name: branch-worktree-pr
description: >-
  Orchestration for branch+worktree+PR workflow — ticket/spec → isolated worktrees → verify → squash merge. Use when creating a branch from a ticket/spec, dispatching parallel worktrees, merging via wt merge, or opening a PR that closes tickets. TRIGGER: branch, worktree, wt merge, squash, Closes
disable-model-invocation: true

---

# branch-worktree-pr — ==tight worktree== orchestration

> **Type:** Orchestration — owns sequencing, checkpoints, and fan-out/fan-in. Delegates ==all== implementation to subagents. The orchestrator never writes code. All code-writing subagents MUST use `tdd` (`tdd-cycle` skill) — red → green → refactor — tests live in `tests/` per `AGENTS.md`.

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

> [!warning] `wt list --format=json` emits its schema warning on **stderr** — never pipe with `2>&1 | jq`
> `wt list --format=json 2>&1 | jq` mixes the `▲ JSON output is schema 1` warning into `jq`'s stdin and breaks parsing. Use `wt list --format=json | jq` (stderr stays separate) or `wt list --format=json 2>/dev/null | jq` to suppress.
>
> Schema matters — `json-schema = 1` (current default) is a top-level array: `jq '.[] | {branch, path, is_current}'` and `jq '.[] | select(.is_current)'`. `json-schema = 2` (future default, see `wt config update`) wraps in `{items:[...]}` with `worktree` nesting: `jq '.items[] | {branch, path: .worktree.path, is_current: .worktree.current}'` and `jq '.items[] | select(.worktree.current)'`. Pin with `[list] json-schema = 1` in `.config/wt.toml` until migrated, or handle both: `jq '.items // . | .[]? | {branch, path: (.worktree.path // .path), is_current: (.worktree.current // .is_current)}'`.

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
 wt list --format=json 2>/dev/null | jq '.items // . | .[]? | select((.worktree.current // .is_current)) | {branch, path: (.worktree.path // .path)}'
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

**Done when** `git branch --show-current == feat/<slug>` (or `map/<slug>`) at the **session path** and `wt list --format=json 2>/dev/null | jq '.items // . | .[]? | select((.worktree.current // .is_current))'` shows the same branch at that path (not a sibling).

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

#### Dispatch table — one copy per ticket (feat fans out to modules)

| Copy suffix                 | When                                         | Subagent prompt (plain words)                                                                                           |
| --------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `--auth`, `--store`, `--ui` | feat dispatches parallel modules (your case) | `implement` via `tdd` — red → green → refactor, tests in `tests/` (see `tdd` skill)                                     |
| `--tdd`                     | mandatory for all code (was legacy)          | `tdd-cycle` (full: design → implement → verify) — each ticket subagent runs `tdd`                                       |
| `--refactor`                | second pass / cleanup                        | `refactor` — fix shape, keep tests green                                                                                |
| `--verify`                  | pre-merge gate                               | `check` — run gate in that copy only                                                                                    |
| `conflict-fixer`            | merge hit conflict (Phase 3)                 | `fix` — inherit_context: true, plain words: branch, copy, merge, conflict, fix, test, check, file, folder (see Phase 3) |

#### Subagent template (copy per dispatch)

```text
Agent (worker):
  inherit_context: false  # normal worker starts fresh
  cwd: <absolute-copy-path>   # folder for this copy
  description: "implement <ticket-slug> — <phase>"
  prompt: |
    You are in copy at <absolute-copy-path> on branch <branch> — only fix there.
    Ticket: <absolute-path-to-spec> (or gh issue <N> body)
    Scope: files/folder for this copy
    Steps:
      0. Self-check (phase 0, run before touching any file):
         uv run scripts/self_check.py <branch> <absolute-copy-path>
         # or: uv run scripts/worktree.py self-check <branch> <absolute-copy-path>
         # exit 0 → cwd is THIS copy on <branch>. Non-zero → wrong worktree
         # (likely base branch dir) — edit nothing, return BLOCKED + hint.
      1. tdd (mandatory): use `tdd` skill — red (failing test in `tests/`) → green (minimal code) → refactor, keep `uv run ruff check . && uv run pytest -q` green
    Return per handoff:
    ## Summary
    ## Artifacts (absolute paths)
    ## Route (COMPLETED|BLOCKED)
    ## Issues
```

> [!tip] Phase-0 self-check — admit before you touch a file
> Every dispatched subagent runs the self-check as its **first action**:
> `uv run scripts/self_check.py <branch> <absolute-copy-path>` (or dispatcher
> `uv run scripts/worktree.py self-check <branch> <absolute-copy-path>`). It
> verifies cwd is the copy worktree (never the base branch directory) and the
> branch matches the worktree registry. Exit 1 → the agent landed in the wrong
> directory; it edits nothing, returns `BLOCKED` with the script's hint, and the
> base re-dispatches with the correct absolute path.

Conflict-fixer variant uses `inherit_context: true` — it forks the main session intent +
ticket + which files hit conflict. See Phase 3 template.

**Done when** each worktree subagent returns `COMPLETED` after passing its phase-0 self-check (`cwd == <absolute-copy-path>`, branch matches) and its `git status --porcelain` in that worktree is inspectable. Main never writes inside child worktrees.
For BDD scenarios driving this phase see [bdd-scenarios.md](references/bdd-scenarios.md).

### Phase 3 — Merge back via script (fan-in)

`wt merge <TARGET>` merges the **current branch into target** then removes the current
folder (like GitHub's merge button — see `worktrunk-guide` 004-merge.md). Fan-in names the
parent/map as target. Never run `wt merge <child>` from the parent — parent is removed.

Use the thin router — base runs one command, script detects. Step is done when the script exits 0.

```bash
# Thin router — absolute path + --stage tracked keeps .lsz/.pi out, avoids cd bug
uv run $SKILL_DIR/scripts/merge_copy.py <copy-path> <target>
# or via dispatcher
uv run $SKILL_DIR/scripts/worktree.py merge-copy <copy-path> <target>
# router does: wt merge -C <absolute-copy-path> --stage tracked <target> --yes
# then detects: rebase incomplete / Unmerged paths → conflict (exit 2), else gate fail (exit 1)
# check
wt list --format=json 2>/dev/null | jq '.items // . | .[]? | {branch, path: (.worktree.path // .path), is_current: (.worktree.current // .is_current)}'
git log --oneline <target> ^origin/main | head
```

- Router only: `wt merge -C <absolute-copy-path> --stage tracked <target> --yes` — no hunk fixing, no `rebase --continue` here. `GIT_EDITOR=true GIT_SEQUENCE_EDITOR=true git -C <copy-path> rebase --continue` lives in fixer (see below), noted in script comments only.
- `--stage tracked` stages only tracked files (like `git add -u`) — keeps `.lsz/`, `.pi/`, untracked files out of the merge commit.
- `wt merge` runs the blocking `pre-merge` gate from `.config/wt.toml`.
- Keep `--no-remove` only for debug.

**Done when** `wt list` shows the copy gone, `git log --oneline <target> ^origin/main`
has the copy's change, branch no longer resolves.

**If router reports conflict (`rebase incomplete` / `Unmerged paths` / exit 2) → dispatch fixer inside the copy.** Do not edit the parent folder. Base dispatches a fixer that triggers `resolving-merge-conflicts`:

```text
Agent (conflict-fixer):
  inherit_context: true   # forks base intent + ticket + which files hit conflict
  cwd: <copy-path>        # same absolute folder that failed
  description: "fix merge conflict <copy-branch> → <target>"
  prompt: |
    Resolve merge conflicts in copy at <path>
    You are in copy at <copy-path> on branch <copy-branch> — only fix there.
    0. Self-check first: uv run scripts/self_check.py <copy-branch> <copy-path>
       Non-zero → wrong worktree — edit nothing, return BLOCKED + hint.
    Target branch: <target> — merge hit conflict.
    Use plain words: branch, copy, merge, conflict, fix, test, check, file, folder.
```

Fixer invokes `resolving-merge-conflicts` (trigger phrase above) and follows that skill inside the copy: check git status, fix each file, add, test, check, then `GIT_EDITOR=true GIT_SEQUENCE_EDITOR=true git -C <copy-path> rebase --continue` loop and retry `uv run $SKILL_DIR/scripts/merge_copy.py <copy-path> <target>` until exit 0. Main waits, checks router exits 0, then moves on. If router reported gate (no conflict markers, exit 1) → same fixer shape but fix test/typecheck, no rebase step.

> [!warning] Never bypass — the guard is the point
> If `merge_copy.py` exits non-zero for _any_ reason (conflict `exit 2`, gate `exit 1`, or leftover untracked `??` like `node_modules` / new test file not yet staged), the orchestrator's **only** move is to dispatch the fixer subagent **in that copy** (`inherit_context: true`, `cwd: <copy-path>`). Never `git -C <copy> add` / `commit` / `wt remove --force` / `git branch -D` from the orchestrator — that bypasses the `pre-merge` gate that `wt` exists to enforce. The fixer owns `git status --porcelain` in the copy, cleans stray untracked, stages tracked (`--stage tracked`), commits, and retries `merge_copy.py` until `exit 0`. Main only verifies `wt list` shows copy gone and `git log <target> ^origin/main` contains the change.

### Phase 4 — Verify parent gate (heavy)

Gate is environment, not this doc. Default recommendation (override in `.config/wt.toml`):

```bash
# Gate is .config/wt.toml [pre-merge].gate — auto-scaffolded once via _lib.read_gate
# (sniffs Cargo.toml > pyproject.toml > package.json); unknown stack fails loud
# Now includes commitlint for Conventional Commits history (pre-merge blocking, not post-merge background)
uv run scripts/verify_parent.py  # or: uv run scripts/worktree.py verify
# delegates to wt.toml gate (typecheck + test + commitlint --from=origin/{{ default_branch }} --to=HEAD), then git diff --check and git status clean (allows .lsz/tmp)
```

But authoritative gate is `.config/wt.toml [pre-merge]` — skill demands _that_ gate passes, not a hard-coded `npm` string. Current template is `gate = "npm run typecheck && npm test && npx commitlint --from=origin/{{ default_branch }} --to=HEAD --verbose"` (pipeline form: `[pre-merge]` table = concurrent, `[[pre-merge]]` serial — see `worktrunk-guide` automation.md). `commitlint` uses `{{ default_branch }}` / `{{ target }}` vars and `wt hook pre-merge --yes` to test; hook approval frozen at `~/.config/worktrunk/approvals.toml`.

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

Never `git reset --hard` — See `[[git-convention]]`:

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

### Phase 7 — Tag / Release / Publish — delegated

> [!warning] NEVER tag, release, or publish proactively — delegated
> This skill stops at PR `OPEN`. Tag → release → publish lifecycle is owned by `scaffold` (`release.yml`) and `release` skill. At workflow end confirm with user, then delegate to `release` skill if requested.

Delegation:

- `release` skill: `npm run release -- X.Y.Z` (`--dry-run` supported) — bumps manifest, moves `CHANGELOG` `Unreleased` → `[X.Y.Z]`, commits `chore: release`, annotated tag, pushes tag to trigger `release.yml`
- Publish via `release` skill only (interactive, OTP)

**Done when** PR is `OPEN` and user confirms next step or defers to `release` skill.

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
| Reset / atomic commits / changelog layout            | `[[git-convention]]`                                              |

For full BDD scenarios see [bdd-scenarios.md](references/bdd-scenarios.md).
