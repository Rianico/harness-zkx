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

Extracts compact conflict hunks and dual commit intent (`ours` vs `theirs`) to preserve context tokens and reconcile conflicts without whole-file churn.

## Workflow

### 1. Inspect Conflict & Author Intent (Deterministic Tool)
Triage unmerged paths across the repository:
```bash
uv run $SKILL_DIR/scripts/extract_conflict_context.py
```
Extract isolated conflict hunks with operation and author intent for a single file:
```bash
uv run $SKILL_DIR/scripts/extract_conflict_context.py --file path/to/file
```
*(Append `--json` for structured agent consumption).*

### 2. Reconcile Dual Author Intent (Semantic Resolution)
Inspect the dual commit intent displayed by the tool (`ours` on HEAD vs `theirs` on MERGE_HEAD / REBASE_HEAD / CHERRY_PICK_HEAD):
- **Intent Invariant:** Preserve both authors' intents where compatible. When conflicting, select the change aligning with the landing/rebase target and document the trade-off. Never invent extraneous logic.
- **Marker-based conflicts:** Surgically edit the file to merge logic, removing all `<<<<<<<`, `=======`, `>>>>>>>` markers.
- **Whole-file conflicts:** When one side fully supersedes, use `git checkout --ours -- path/to/file` or `git checkout --theirs -- path/to/file`.
- **Tree conflicts:** Resolve file existence (`git rm` or `git add`) based on verified intent.

### 3. Verify & Continue (Falsifiable Gate)
1. Assert zero conflict markers and unmerged index entries:
   ```bash
   uv run $SKILL_DIR/scripts/extract_conflict_context.py
   git diff --name-only --diff-filter=U
   ```
2. Run project tests and linters (e.g. `uv run pytest`, `uv run basedpyright`).
3. Stage and continue the Git operation:
   ```bash
   git add path/to/file
   # Rebase: git rebase --continue
   # Merge:  git commit
   ```

## CLI Reference

```bash
uv run $SKILL_DIR/scripts/extract_conflict_context.py --file path/to/file --json
uv run $SKILL_DIR/scripts/extract_conflict_context.py --all
uv run $SKILL_DIR/scripts/extract_conflict_context.py --file path/to/file --context 3 --max-lines 60
```
