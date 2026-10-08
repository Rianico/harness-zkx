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

Turns someone else's PR into a landable one without ever rewriting their history. Seam: **refine pushes, land merges** — this subskill owns branch prep and body trailers; `pr-land` owns watch and landing. Read [pr-land](../pr-land/SKILL.md) for the landing flow; never merge here.

**Ledger.** A refined PR carries the artifacts a contributor's branch cannot: the ledger entry (Flow A pushes it onto their branch, Flow B ships it in the superseding PR) and, when the change is an architectural decision, an ADR on the same surface. Per `rules/common/git-convention.md` §5; the checks live in `scripts/changelog-gate.py`: invoke them, never restate them.

## Script

`$SKILL_DIR/scripts/refine.sh` (755, `set -euo pipefail`, `GH_TOKEN` via `gh auth`). Attribution gates are reused from `$SKILL_DIR/../../pr-land/scripts/pr.sh`, never re-derived.

```bash
uv run $SKILL_DIR/scripts/refine.sh observe 157   # which flow?
uv run $SKILL_DIR/scripts/refine.sh checkout 157  # head intact, locally
uv run $SKILL_DIR/scripts/refine.sh lint-body --body-file .lsz/tmp/pr_body.md
```

## Flow

**Routing.** `observe <N>` prints `maintainerCanModify`, head repo, base repo, and the flow. The choice is an observation, not a judgment call. *Done when* the last line names Flow A or Flow B.

| Flow | `observe` signal | Action |
| --- | --- | --- |
| **A** — push onto their branch | `maintainerCanModify=true`, or head repo equals base repo | push refinements onto *their* branch, fix the body, then hand to `pr-land` |
| **B** — superseding PR | anything else: a fork you cannot modify, or a deleted fork | merge their head intact into *your* branch, open a superseding PR |

1. **Refine** — Flow A: `gh pr checkout <N>`, push refinements onto their branch, replace or delete the `CODE_AUTHORS` token, keep their trailers. Flow B: `checkout <N>`, merge their head intact (never rebase or amend their commits), open a superseding PR whose body holds `Supersedes #N`, a hand-written `Co-authored-by` trailer, and `Closes #A` for the original issue, then leave a courtesy comment on the original PR. *Done when* the branch is pushed and the body is staged.
2. **Lint** — `lint-body` enforces what the merge step enforces: no raw `CODE_AUTHORS` token. Run it before the handoff so `pr-land` never refuses. *Done when* it prints `body ok: no raw token` and exits `0`.
3. **Hand off** — Read `pr-land` and follow its flow: Flow A lands their PR under your account, and their commits keep their attribution; Flow B lands yours. *Done when* the PR reads merged on GitHub.

## Rules

- **Preservation:** contributor history is read-only. Merge it, don't rewrite it.
- **Trailers:** every distinct commit author except the merger is credited, including the PR author; dedupe is by lowercase email, and redundant trailers are harmless.
- **Handoff:** push the branch, stage the body, then Read `pr-land` — never merge here.

Exit: `0` ok · `1` gate refused or `gh` failed · `2` usage.
