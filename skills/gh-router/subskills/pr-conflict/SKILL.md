---
name: pr-conflict
description: >-
  Git conflict reconciliation engine for PR landing and rebase. Extracts compact conflict hunks via Git plumbing and reconciles dual author intent. Use when a merge, rebase, cherry-pick, or stash pop stops on conflicts, or files contain conflict markers; not for clean branch merges.
arguments: file_path
argument-hint: |-
  "[--file PATH] [--all] [--json] -- extract compact conflict hunks and commit intent"
metadata:
  managed-by: gh-router
---

# PR Conflict

Goal: reconcile a stopped Git operation without whole-file churn. Read the compact conflict hunks and the dual author intent (`ours` vs `theirs`).

## CLI

| Flag | Effect |
| --- | --- |
| (none) | repo triage: unmerged paths, conflict type, hunk counts |
| `--file PATH` | detail for one conflicted path: operation, author intent, compact hunks; repeatable |
| `--all` | detail for every conflicted path |
| `--json` | JSON instead of text |
| `--context N` | context lines around each hunk (default 2) |
| `--max-lines N` | truncate each section (default 40) |

A path that is not conflicted, or `--all` combined with `--file`, exits `2`.

## Flow

1. **Triage** — `uv run $SKILL_DIR/scripts/extract_conflict_context.py`. *Done when* it prints `conflicted files: 0` or lists every unmerged path with its conflict type, stages, and hunk count (add `--file` or `--all` for the git operation and author intent).
2. **Reconcile** — the tool labels `ours` from HEAD and `theirs` from MERGE_HEAD / REBASE_HEAD / CHERRY_PICK_HEAD / REVERT_HEAD. Resolve each path by its type:
   - **Marker conflict** — edit the file to merge both intents, then delete every `<<<<<<<`, `=======`, `|||||||`, and `>>>>>>>` line.
   - **Whole-file conflict** — one side fully supersedes: `git checkout --ours -- PATH` or `git checkout --theirs -- PATH`.
   - **Tree conflict** — the file exists on one side only: `git add PATH` or `git rm PATH`, by verified intent.
   - **Intent rule** — preserve both authors where compatible. Where they contradict, keep the change the landing or rebase target needs and record the trade-off. Never invent logic neither side wrote.
   *Done when* no path holds a marker and no path still needs context.
3. **Verify** — `uv run $SKILL_DIR/scripts/extract_conflict_context.py --file PATH` shows no hunks, `git diff --name-only --diff-filter=U` prints nothing, and the project tests and linters pass (`uv run pytest`, `uv run basedpyright`). *Done when* all three are clean.
4. **Continue** — `git add PATH`, then resume: `git rebase --continue`, `git commit` (merge), `git cherry-pick --continue`, `git revert --continue`, or finish the stash pop. *Done when* the operation reports success and `git status` lists no unmerged paths.
