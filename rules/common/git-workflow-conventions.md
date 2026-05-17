# Git Workflow Conventions

Rules extracted from git history analysis to prevent common mistakes.

## Atomic Commit Separation

Implementation changes and documentation updates must be separate commits.

**Rationale:** Commit `f06f577` bundled skill conversion with methodology docs and architecture updates. This violates single-responsibility and makes bisecting harder.

**Rule:**
- Code changes (skills, commands, agents) → one commit
- Methodology docs (ai-engineering-expert, CLAUDE.md) → separate commit
- Architecture guidance → separate commit

**Check before committing:**
```bash
git diff --cached --name-only | rg -E "(CLAUDE\.md|ai-engineering-expert)"
```
If matches, split the commit.

---

## Reset Safety Protocol

**Never use `git reset --hard`.** Always reset in soft mode and explicitly discard changes if needed.

**Rationale:** `git reset --hard` is a destructive operation that can silently lose uncommitted work. During session, `--hard` was used when soft reset would have preserved changes for re-commit.

**Pattern:**
```bash
# Step 1: Undo commit(s), keep all changes staged
git reset HEAD~N

# Step 2: If you need to discard changes, do so explicitly
git restore <file>           # Discard working directory changes
git restore --staged <file>  # Unstage only
git restore .                # Discard all changes in working directory
```

**Why two steps:**
- Soft reset is always safe — changes remain in working directory
- `git restore` is explicit about what you're discarding
- No accidental data loss from a single destructive command

**Forbidden:**
```bash
git reset --hard HEAD~N  # NEVER use
```

---

## Pre-Commit File Audit

Before committing, audit staged files for cross-cutting concerns.

**Audit checklist:**
1. Are there both code files and documentation files staged?
2. Does CLAUDE.md appear alongside skill/command changes?
3. Are ai-engineering-expert docs mixed with implementation?

**If cross-cutting detected:**
```bash
# Split into separate commits
git reset HEAD  # Unstage all
git add <code-files> && git commit
git add <doc-files> && git commit
```

**Excluded from this rule:**
- Pure documentation PRs (only doc files staged)
- Single-file changes
- Trivial updates (typo fixes, single-line changes)
