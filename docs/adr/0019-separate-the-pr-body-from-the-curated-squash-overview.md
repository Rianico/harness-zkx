# 19. Separate the PR body from the curated squash overview

Date: 2026-10-08

## Status

Accepted

Relates to [16. Changelog Ledger Gate with Deterministic Floor and Adversarial Accounting](0016-changelog-ledger-gate-with-deterministic-floor-and-adversarial-accounting.md)

## Context

`pr.py` treated one body as two jobs. The reviewer's description and the squash commit
message came from the same text. `--merge` fell back to the PR body, and the shape gate
judged a preview derived from that body.

The two jobs pull apart. Reviewers need full detail — Mermaid diagrams, `<details>`
blocks, raw evidence, and the review-only `## Architecture` and `## Verification Evidence`
sections. The changelog ledger reads mainline commit subjects (ADR-0016), so the squash
message must stay on one screen. The fallback also let a description pasted back verbatim
land as the durable commit message. Curation was therefore optional in practice.

## Decision

The PR body and the squash overview are separate artifacts with different size rules.
The merge operation requires the overview explicitly.

The PR body is the reviewer's document. It keeps Mermaid, `<details>`, evidence, and every
contract section. It may be long.

The squash message is a curated overview plus links. As the durable commit message, it stays
at most 5 bullets and 15 lines, contract sections only, with no Mermaid, `<details>`, or checkboxes.

`--merge` requires `--squash-message` or `--squash-message-file`. There is no PR-body
fallback. A missing message refuses (exit 1) before any `PUT`. `--check` still previews a message
derived from the body. The explicit path runs the shape gate and the copy detector. It compares
Jaccard overlap and body coverage against 0.80, above a floor of 25 tokens.

### Considered Options

- Rejected: keep the body-derived fallback. It makes the description the commit message by
  default and lets a paste-back pass as curation.
- Rejected: one artifact with one size rule. Review detail and durable-message brevity pull
  in opposite directions. Fifteen lines cannot hold the evidence reviewers need.
- Rejected: refuse any overlap between the two texts. A curated overview legitimately
  reuses the change's own vocabulary, so only near-verbatim copies above 0.80 refuse.

## Consequences

- Curation is mandatory on the merge path. The shape gate and the copy detector run on the
  explicit message, never on a fallback.
- The explicit path refuses shape-gate constructs: non-contract headings, checkboxes, Mermaid
  fences, the raw `CODE_AUTHORS` token, and line/bullet caps. It still sanitizes HTML comments,
  `<details>` blocks, `Landing:`/`Ledger-Waiver:` directives, and empty headings.
- `CONTEXT.md` states the split in **PR Body Contract** and **Curated Squash Message**. The
  pr-land SKILL.md [Squash Shape](skills/gh-router/subskills/pr-land/SKILL.md#invariants--gates) gate
  owns the rules, and the `--check` hint points at both.
- A reviewer who pastes the description regardless still trips the copy detector. Lowering
  the threshold would start refusing honest overviews that reuse the change's wording.
