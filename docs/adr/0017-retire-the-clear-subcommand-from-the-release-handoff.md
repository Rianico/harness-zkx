# 17. Retire the clear subcommand from the release handoff

Date: 2026-09-30

## Status

Accepted

Amends [16. Changelog Ledger Gate with Deterministic Floor and Adversarial Accounting](0016-changelog-ledger-gate-with-deterministic-floor-and-adversarial-accounting.md)

## Context

ADR-0016 made the curated `## [Unreleased]` ledger the release-notes source and required
`changelog-unreleased.py clear` to move *after* capture. The step was never moved — it was replaced.
`scripts/release-changelog.mjs` now exports `generateNotes` (returns the curated block) and
`prepare` (promotes it to `## [X.Y.Z] - <date>` and re-opens an empty `## [Unreleased]`), and the
scaffold ships that plugin with no `clear` step in any rendered `release.yml`. The harness's own
release job had already dropped `clear`.

The subcommand survived only as documentation: `CONTRIBUTING.md`, the three scaffold CONTRIBUTING
templates, the `git-scaffolding` skill, and `CONTEXT.md` each claimed `release.yml` ran `clear`
before `semantic-release`. A downstream scaffold followed the documented handoff, deleted its
curated ledger before the plugin read it, and shipped two releases with empty bodies. The only
remaining callers of `clear` were tests asserting the destruction.

## Decision

Remove the `clear` subcommand from `scripts/changelog-unreleased.py` and its byte-identical scaffold
copy. The promotion plugin owns emptying `## [Unreleased]`; no harness-shipped or scaffolded
`release.yml` may clear the ledger before `release-changelog.mjs` reads it.

### Considered Options

- Rejected: move `clear` after capture in `release.yml`. It cannot be a step in the same job —
  semantic-release runs capture and promotion in one process — and the plugin already performs the
  emptying, so a second writer would race the first.
- Rejected: keep `clear` behind a guard. A subcommand with no legitimate caller is a footgun with a
  warning label; the destructive step it encodes has no remaining legitimate use.

## Consequences

- `update` and `check` remain; the script is no longer part of the release handoff, only the ledger
  authoring and drift gate.
- The scaffold byte parity (`scripts/changelog-unreleased.py` vs
  `skills/scaffold/scripts/changelog-unreleased.py`) and the `tests/scaffold` pins move with the
  removal, and the `CONTRIBUTING` rendered-byte pins are re-pinned.
- A regression test renders every `release.yml` variant and scaffolds the git flavor, failing if any
  shipped workflow clears the ledger before the plugin reads it.
