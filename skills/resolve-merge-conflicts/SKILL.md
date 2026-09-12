---
name: resolve-merge-conflicts
description: >-
  Extracts compact conflict hunks via Git plumbing and reconciles dual author intent. Use when a merge, rebase, cherry-pick, or stash pop stops on conflicts, when git status shows unmerged paths, or when files contain conflict markers; not for clean branch merges or standard rebases.
---

# Resolve Merge Conflicts

Extracts only conflicted hunks, surrounding lines, and index-stage diffs to preserve context tokens. Reconciles conflicting code by preserving dual author intent, verified by falsifiable test and marker checks.

## Workflow

### 1. Triage Unmerged Paths (Deterministic Tool)
Inspect repo-level unmerged status and conflict types (`text`, `add/add`, `deleted-by-them`, `deleted-by-us`, `index-only`):
```bash
uv run $SKILL_DIR/scripts/extract_conflict_context.py
```
*(Fallback from workspace root if `$SKILL_DIR` unset: `uv run skills/resolve-merge-conflicts/scripts/extract_conflict_context.py`)*

### 2. Inspect Single Conflicted File
Extract isolated conflict hunks with compact `ours` vs `theirs` unified diff without reading the whole file:
```bash
uv run $SKILL_DIR/scripts/extract_conflict_context.py --file path/to/file
```
*Note: For automated agents or subagents, append `--json` for machine-readable output.*

### 3. Discover Author Intent (Semantic Reconciliation)
Before modifying code, understand why both changes were introduced:
- Check recent commit logs on both sides: `git log -n 5 -p HEAD -- path/to/file` and `git log -n 5 -p MERGE_HEAD -- path/to/file` (or `REBASE_HEAD`).
- Check relevant PR descriptions or issues when available.
- **Intent Invariant:** Preserve both intents where compatible. When incompatible, select the choice matching the merge's stated goal and document the trade-off. Never invent extraneous behavior. Never `--abort` when resolution is possible.

### 4. Reconcile Code
- **Marker-based conflicts:** Surgically edit the file, reconcile logic, and remove all `<<<<<<<`, `=======`, `>>>>>>>` markers.
- **Whole-file resolution:** When one side fully supersedes the other, run `git checkout --ours -- path/to/file` or `git checkout --theirs -- path/to/file`.
- **Index/Tree conflicts (add/add, modify/delete):** Resolve file existence (`git rm` or `git add`) based on verified intent.

### 5. Falsifiable Verification Gate
1. **Assert zero conflict markers & unmerged stages:**
   ```bash
   uv run $SKILL_DIR/scripts/extract_conflict_context.py
   git diff --name-only --diff-filter=U
   ```
2. **Execute project verification gates:** Run native typechecks, unit tests, and linters (e.g. `uv run pytest`, `uv run basedpyright`).
3. **Stage & Continue:**
   ```bash
   git add path/to/file
   # Finish merge or proceed with rebase:
   git commit   # or git rebase --continue
   ```

## CLI Reference

```bash
# Detailed view of all conflicted files
uv run $SKILL_DIR/scripts/extract_conflict_context.py --all

# Machine-readable JSON output
uv run $SKILL_DIR/scripts/extract_conflict_context.py --file path/to/file --json

# Adjust surrounding context lines or truncation limits
uv run $SKILL_DIR/scripts/extract_conflict_context.py --file path/to/file --context 3 --max-lines 60
```
