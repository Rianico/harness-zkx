<!-- markdownlint-disable MD041 -->

## Summary

<!-- 2-3 sentences: why this change, user-visible effect. -->
<!-- Review path (optional): start at <file:line>. -->

## What Changed

<!-- Grouped by system/feature, not a file list. For a large refactor, add a short sequence
outline. Flag migrations, contract, or payload changes. -->

-

## Blast Radius & Safety

**Downstream consumers:**
**Breaking changes:**
**Data / state invariants:**
**Rollback / containment:**

## Evidence

<!-- Exact commands run and what they assert; link the CI run. -->

## Architecture

<!-- Mermaid before/after only when structural seams, layering, or data-flow changes; delete the section otherwise. -->

## Landing

Landing: squash <!-- or: Landing: merge — see git-convention §5 -->

## Checklist

- [ ] Formatter, linter, typecheck, and tests green (exact commands in `CONTRIBUTING.md`)
- [ ] Conventional Commits (`commitlint` + `husky`) — `npx commitlint --from=origin/main --to=HEAD`
- [ ] `CHANGELOG.md` `## [Unreleased]` updated (if user-facing)
- [ ] Docs / `docs/adr/` updated when seams or contracts change
- [ ] No generated artifacts committed outside `.lsz/tmp`
- [ ] Linked issue with `Closes #NN` (if applicable)

<!-- Related issues: list each on its own line below (never comma-separated: "Closes #1, #2" fails to close #2).
Closes #123
Closes #456
-->

<!-- CODE_AUTHORS: replace with `Co-authored-by: Name <email>` lines for each outside
     contributor whose commits this PR carries, or delete this block. The merge step
     refuses a body that still contains the raw `CODE_AUTHORS` token. -->
