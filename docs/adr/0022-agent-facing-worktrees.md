# 22. Agent-facing worktrees are bound to roles, not feature branches

Date: 2026-10-19

## Status

Accepted

Relates to [13. Worktree Python Shims with wt Gate Delegation and Auto-Scaffold](0013-worktree-python-shims-with-wt-gate-delegation.md)

Clarifies [5. Manifest-Driven Orchestration and Provenance Trace](0005-manifest-driven-orchestration-and-provenance-trace.md)

## Context

The programme brief asked for `docs/adr/0021-agent-facing-worktrees.md`. Number 0021 was already
taken by [21. pr-land derives state and emits facts instead of persisting
artifacts](0021-pr-land-derives-state-and-emits-facts-instead-of-persisting-artifacts.md) (accepted
2026-10-17), so the decision is recorded here as ADR-0022. The brief's number is not reused and
0021 is not rewritten.

The lane model gave every participant one feature-bound worktree. `herdr-worktree allocate
<branch>` created `<repo>.<sanitized-branch>`, and Task Manager, Implementer, and Reviewer shared
it. Two facts made that model fail once roles became long-lived:

- **One branch, one worktree.** Git refuses to check out a branch that another registered
  worktree already has. The check consults every worktree's `HEAD` symref (G1); `--ignore-other-worktrees`
  and `git worktree add --force` are the only bypasses, and the latter produces the classic
  double-checkout where one index/HEAD pair is permanently stale (G11). `switch -C` also resets
  the branch ref to its start point — HEAD by default, not `origin/<branch>` (G2) — and the reset
  is not atomic with the in-use refusal (G3). A shared tree therefore either blocks the next
  ticket's branch or silently rewrites the previous one.
- **Review races the writer.** A reviewer in the writer's tree sees files, index, and HEAD move
  under it; gates run there can mutate the very tree they verify. Git does allow many worktrees at
  one detached commit (G5), which makes a pinned-SHA read safe, and `refs/stash` is shared across
  worktrees while HEAD and the index are not (G8). Same-branch writers also serialize on ref locks
  and the loser's history can vanish (G9).

The review in `.lane/tmp/agent-worktree-review/drafts.design.json` records these constraints as
G1–G12, and its F5/F6/F10 findings add two repository-specific costs: `.lane/` is a shared live
database resolved through the git common dir — not per-worktree state — yet it is gitignored and
copied into every new worktree; and Worktrunk's `branch_worktree_mismatch` state is exactly what a
per-role path produces. Options 2a (shared cwd) and 2b (detached-only writers) were both rejected;
this ADR adopts the review's Option C.

## Decision

Agent worktrees are bound to roles, and review is commit-addressed rather than tree-addressed.

1. **Three-tier branch namespace.** Every agent branch is
   `lane/<task-group>/<role>/<ticket>`. The task group scopes a programme, the role scopes the
   writer, and the ticket scopes the unit of work. Bare feature branches, `main`, and any shorter
   path are refused at claim time.

2. **One worktree per role.** The layout is `<repo-root>.<task-group>.<role>`. A role keeps a
   stable working directory across tickets, and each ticket changes only the branch inside it.
   `herdr-worktree claim` performs the guarded in-place transition: the tree must be clean, the
   base must be passed explicitly, the path must be a registered worktree, and the branch must be
   inside the namespace. Claim verifies the base and switches with `switch --create <branch>
   <verified-base-sha>`; it never resets an existing branch. Bindings are persisted in
   `.lane/tasks.yaml` under a path-keyed top-level `worktrees` map, anchored by
   `resolve_lane_base_dir`, never by `PWD`. `status` reports branch, cleanliness, detached HEAD,
   namespace violations, and layout drift; `retire` removes a clean tree and only its fully merged
   branch; `doctor --prune` drops only admin entries for missing directories.

3. **Single writer.** A branch is checked out in at most one worktree, enforced by git and checked
   before every claim. The following are forbidden inside any lane tree: `git switch -C`, `-B`, or
   `-f`, `git stash`, and `git worktree add --force`. Teardown uses `git worktree remove` without
   `--force` and `git branch -d` only; raw ref deletion and `-D` are out of bounds because they
   strand a worktree's HEAD symref (G6, G7). Worktrunk remains the read-only allocator surface
   (`allocate|resolve|list`); `wt step relocate`, `wt step prune`, and `wt remove` must not target
   agent-bound trees, whose per-role paths are outside Worktrunk's branch→path model (F6, P3).

4. **Commit-addressed review and tree freezing.** A writer commits before handoff and reports the
   SHA. Reviewers read `git diff <base>..<sha>` and `git show <sha>:<path>` against that pinned
   SHA, or use an ephemeral detached worktree when files are needed; they never check out, stash,
   or write in the writer's tree. Gates run on the pinned SHA (or the owner's committed result),
   never against a moving working tree. This satisfies the gate contract without requiring a
   second checkout of the writer's branch (P2, P5) and gives review evidence that is stable when
   the writer continues.

5. **`.lane/` is one shared database, never per-worktree state.** The store lives at the git common
   dir and all worktrees resolve the same file. Warm starts still copy gitignored artifacts, but
   project config excludes `.lane/` from that copy with `[step.copy-ignored] exclude = [".lane/"]`
   in `.config/wt.toml`. Worktrunk 0.76 exposes this exclusion as config rather than a
   `copy-ignored` flag, so a new worktree carries build caches but no stale store shadow, and the
   main checkout's live store is never touched.

6. **Migration is opt-in by path.** `allocate|resolve|list` keep their branch-keyed behaviour for
   feature-bound trees, so existing lanes do not break. `status` and `doctor` report the legacy
   `<repo>.<sanitized-branch>` shape as a `layout` flag; a lane opts into the new topology by
   claiming a per-role path. The old layout is never rewritten automatically.

### Considered Options

- **Rejected: keep the shared feature-bound tree and let roles switch branches in place.** It
  violates one-branch-one-worktree, resets the branch ref to HEAD (P0), and changes the reviewer's
  tree mid-review.
- **Rejected: option 2a, review in the writer's cwd.** It is the current model: findings cite a
  tree that can move, and gates can mutate the writer's state. A pinned SHA is strictly better
  evidence at no extra cost.
- **Rejected: option 2b, all writers detached.** Detached writers have no branch identity for
  handoff, and their commits stay reachable only through HEAD/reflogs until a ref is created (G5).
  The hybrid keeps branch-bound writers and moves readers to a SHA.
- **Rejected: reuse one branch across roles with `--force` or `--ignore-other-worktrees`.** It
  creates the double-checkout state git protects against (G11), with stale index and HEAD.
- **Rejected: keep `<repo>.<sanitized-branch>` and add a role suffix to the branch only.** The
  worktree path would still change per ticket, and per-branch derived hooks (preview port,
  pre-remove cleanup) would keep crossing tickets (P4).

## Consequences

The single-writer invariant is mechanically enforced instead of documented: a dirty tree blocks a
claim, a branch already checked out elsewhere is refused, and retirement cannot delete an unmerged
branch. Review evidence is reproducible from a SHA even while the writer continues, which removes
the reviewer race and the gate-tree conflict in one move.

Costs are explicit. Each role consumes a worktree, and a dirty tree cannot change tickets until it
is committed or cleaned. Ignored artifacts are still copied once at worktree creation, so
dependency sync after a ticket switch remains the writer's job (P4). Worktrunk's branch→path
assumption does not understand per-role paths, so its mutating verbs are out of bounds for these
trees. The `.lane/` exclusion is a Worktrunk config key rather than a `copy-ignored` flag; if the
key or its project-config precedence changes, verify the exclusion again.

Load-bearing assumptions: git remains the worktree registry authority; `git worktree list
--porcelain` is the collision check; and every writer reports a SHA before review. If a future git
or Worktrunk release changes branch/worktree semantics (for example a per-worktree stash or a
native ignored-artifact exclude), re-check G8/G10 and the hook before relying on them.
