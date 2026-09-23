---
name: pr-refine
description: >-
  Contributor-PR takeover: push refinements onto their branch (Flow A) or open an intact-history superseding PR (Flow B). Use when asked to refine, take over, supersede, or land someone's PR with local changes. Not for own-PR prose (pr-enhance) or watching/merging (pr-land).
arguments: pr_number
argument-hint: |-
  "<number> -- contributor PR to refine, take over, or supersede"
metadata:
  managed-by: gh-router
---

# PR Refine — Take Over a Contributor's PR

Turns someone else's PR into a landable one without ever rewriting their history.
Seam: **refine pushes, land merges** — this subskill owns up to push (branch prep, body
trailers); `pr-land` owns watch + squash. The shared contract is the squash body.

## Script

`$SKILL_DIR/scripts/refine.sh` (755, `set -euo pipefail`, `GH_TOKEN` via `gh auth`).
Attribution gates are reused from `$SKILL_DIR/../../pr-land/scripts/pr.sh`, never re-derived.

```bash
uv run $SKILL_DIR/scripts/refine.sh observe 157        # step 0: which flow?
uv run $SKILL_DIR/scripts/refine.sh checkout 157       # Flow B: head intact, locally
uv run $SKILL_DIR/scripts/refine.sh lint-body --body-file tmp/pr_body.md
```

## Flow

0. **Observe** — `observe <N>` prints `maintainerCanModify`, head, author, base, and the
   resulting flow. The selection is a deterministic observation, not a judgment call:
   `true` → Flow A, anything else → Flow B.
1. **Flow A** (primary) — `gh pr checkout <N>`, push refinements onto *their* branch,
   fix the body (replace-or-delete the `CODE_AUTHORS` token; keep their trailers), then
   hand to `pr-land --watch --merge` on their PR. It shows merged; only they get trailers.
2. **Flow B** (recovery) — `checkout <N>`, merge their head intact into *your* branch
   (never rebase or amend their commits), open a superseding PR whose body holds
   `Supersedes #N`, a hand-written `Co-authored-by` trailer, and `Closes #A` for the
   original issue; leave a courtesy comment on the original PR. Landing closes both.
3. **Lint** — `lint-body` enforces what the merge step enforces: no raw `CODE_AUTHORS`
   token, no line over 100 chars. Run before handing off so `pr-land` never refuses.

## Rules

- **Preservation:** contributor history is read-only. Merge it, don't rewrite it.
- **Trailers:** every distinct commit author except the merger is credited, including
  the PR author; dedupe is by lowercase email and redundant trailers are harmless.
- **Handoff:** push the branch, stage the body, then Read `pr-land` — never merge here.

Exit: `0` ok · `1` gate refused or `gh` failed · `2` usage.
