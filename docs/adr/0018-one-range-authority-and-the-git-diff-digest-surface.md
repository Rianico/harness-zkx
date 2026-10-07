# 18. One range authority and the git-diff-digest surface

Date: 2026-10-06

## Status

Accepted

## Context

Agents need a commit range as context. Three consumers need the same answer: the new digest surface, the landing script (`skills/gh-router/subskills/pr-land/scripts/pr.py`), and the conflict extractor (issue #201). Each resolves a base today, or will soon, with its own ad-hoc order.

The existing diff analyser cannot grow into this role. It is diff-only and PR-shaped. Placing the resolver inside the new subskill spreads the same risk: sibling subskills then depend on one subskill for a shared invariant.

## Decision

One shared Python module in `skills/gh-router/lib/` owns base and range resolution. The digest surface, `pr.py`, and the conflict extractor consume it. The shared module owns no presentation.

Base resolution is local-first and ordered: explicit base → `origin/HEAD` → `origin/main` → `origin/master`. It never touches the network.

One new subskill under `skills/gh-router/subskills/`, named `git-diff-digest`, owns the digest surface, with modes `range`, `pr`, `verify`.

The payload is versioned `schema: 1`. YAML is the default rendering and JSON is the alternate: one value model, two emitters, equal round-trip.

### Considered Options

- Rejected: extend the existing diff analyser in place. It is diff-only and PR-shaped, so range resolution does not fit it.
- Rejected: place the range resolver inside the new subskill. It makes sibling subskills depend on one subskill for an invariant.
- Rejected: JSON-only payload. Two emitters share one value model so YAML stays the default and JSON stays available with equal round-trip.
- Rejected: rename the subskill away from `git-diff-digest`. The name carries the surface contract.

## Consequences

- `git-diff-digest` renders the Diff Digest; `pr.py` and the conflict extractor (issue #201) reuse the same base without duplicating the order.
- Presentation changes stay in the subskill. Range semantics stay in the shared module.
- **Diff Digest**, **Range**, **Only in base**, and **Fingerprint** enter `CONTEXT.md`, disambiguated from **Changelog Digest**.
- The local diff analyser (`skills/gh-router/subskills/pr-enhance/scripts/analyze-pr.py`) keeps its drafting-schema role; its diff-analysis role retires with its callers in #205.
