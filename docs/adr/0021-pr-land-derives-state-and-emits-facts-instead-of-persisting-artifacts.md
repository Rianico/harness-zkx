# 21. pr-land derives state and emits facts instead of persisting artifacts

Date: 2026-10-17

## Status

Accepted

Amends [10. Versioned Phase-Run Pattern for Artifact Organization](0010-versioned-phase-run-pattern-for-artifact-organization.md)

Clarifies [5. Manifest-Driven Orchestration and Provenance Trace](0005-manifest-driven-orchestration-and-provenance-trace.md)

## Context

Issue #265 reported four friction points in `pr-land`, all of one shape: the script made a
reasoned decision and then left the model unable to see the facts behind it.

- `--check` wrote `draft.json` and `pr_body.md` at fixed `.lsz/tmp` paths. No production code
  read `draft.json`; the scaffold file was preserved byte-for-byte, so a body filled on one
  branch was picked up on the next.
- `title_supplied` / `body_supplied` were computed in `main` and dropped before the gate ran,
  so a title refusal could not say the title came from `HEAD`.
- No artifact carried push state, so a missing remote branch surfaced only as a `gh api` failure.
- One title decision was evaluated in three places with three different information states:
  `--check` with a placeholder `(#9999)`, create with none, merge with the real `#N`.

The structural cause was two output channels — a persisted artifact and stderr prose — with no
rule about which carries what, and no single authority for the operation's state.

## Decision

`pr-land` derives its state from git and `gh` on every run, emits the facts that decisions need,
and persists nothing about its own phase.

1. **State is derived, never stored.** `draft.json` is deleted. Facts go to stdout — the scaffold
   when no body is supplied, `--json` for machine reading — and commentary goes to stderr. The
   derived squash message preview stays an output, since ADR-0019 requires `--check` to preview it.
   `--status` is the read-only orientation command. `--check` remains the gate and keeps its exit
   codes (`1` refusal, `2` no body supplied). The `--status --json` fields, the `transitions[]`
   entries, and the `refusals[]` entries are contract; the acceptance spec pins their schema before
   implementation starts.
2. **One artifact, tool-owned prefix.** The draft scaffold is written to `.lsz/gh-router/`. The leaf
   defaults to an **injective** head-ref slug — `feat/x`, `feat-x` and `feat.x` must not share a
   leaf — so the default path is branch-scoped; a caller may name another leaf with `--out`. A
   body-less `--check` writes it only when the leaf is absent; when it exists the tool writes
   nothing and reports the path, a deterministic `stale` flag computed against the head commit, and
   the legal transitions (`--force-scaffold` to regenerate, `--out` another leaf, or reuse it
   as-is).
   The tool never reads an existing artifact to *decide* anything — no preservation rule, no
   overwrite guess, no provenance check — so byte-for-byte preservation, body provenance, and the
   scaffold signature are removed. `--status` does read the leaf, but only to report `body_state`
   and the preview: reporting is not deciding.
3. **Refusals are data.** A refusal is carried by `refusals[]` entries — reason, remedy, and site —
   in the report and on stderr. An empty array means there is nothing to report; a read-only report
   with entries still exits 0, while a mutating command with entries exits 1.
   Mechanical impossibility (branch has no remote, remote diverged, base unresolvable, `gh` missing
   or unauthenticated) and contract violations (missing squash message, unfilled body, raw
   `CODE_AUTHORS`) refuse on mutating commands. Read-only commands never refuse: `--status` reports
   the same predicates and exits 0.
   Judgment calls (body wording, scaffold reuse, an open draft PR) emit the state, remedies, and the
   transition list, including the ready-flip command; on a mutating command the transition that
   cannot proceed still refuses, with those facts attached. `site` names the caller's input or
   artifact — never a `pr-land` source location, which stays behind `--verbose`.
4. **Shared vocabulary, local implementation.** `branch_pushed`, `pr_state` (`none` | `open` |
   `merged` | `closed`), `pr_draft`, `body_state` (`none` | `scaffold` | `unfilled` | `ready`),
   `worktree_clean`, `changelog_stamped`, `head_pushed`, and the failure states `diverged`,
   `head_stale`, `stamp_failed` are defined once for the router's PR lifecycle and implemented in
   `pr-land` first; `pr-refine` and `pr-enhance` adopt them later.

### Considered Options

- Rejected: keep `draft.json` as the artifact and require the model to read it. Nothing read it,
  a stored status goes stale the moment anything changes, and the stale `pr_body.md` was exactly
  that failure mode.
- Rejected: persist provenance in the scaffold signature or a run token. That marks up the
  caller's document to guard a state the design removes.
- Rejected: `run-[N]` directories (ADR-0010) for the scaffold. The pattern exists for remediation
  history; a scaffold has none, so it accumulates directories and forces the caller to resolve the
  latest run.
- Rejected: refuse when the leaf exists. It fires on the model's normal iterate loop and
  reproduces the `--force-scaffold` friction the issue reported.
- Rejected: emit one `next` step instead of a transition list. It hides the alternatives the model
  is meant to choose between.

## Consequences

The friction-2 leak is gone on the default paths: the leaf is branch-scoped and nothing is read
back across branches. With a caller-chosen leaf the caller owns the name, and the tool reports the
path and its `stale` flag rather than deciding for it. `is_untouched_scaffold` and the scaffold signature
lose their only consumer and go with it; `--out-dir` goes with `draft.json`. The `pr-land`,
`pr-refine`, and `pr-enhance` SKILL.md body-file examples move to `.lsz/gh-router/`, and the
scaffold tests re-point to the new prefix.

Boundary with `state.sh`: `scripts/state.sh` stays the human-facing one-line orientation and keeps
its `gh pr view` query; `--status` is the machine-readable landing state and is authoritative for
landing decisions. The two will never agree field-for-field, so the router SKILL names which one a
caller trusts, and `state.sh` does not grow landing predicates.

Load-bearing assumptions: git and `gh` stay the state authority, so every command must remain
safe to re-run from any state — `stamp_changelog` violates this today, returning early when
`(#N)` is already present and stranding an unpushed commit; a caller that hands over a body from
another branch by hand is beyond any check, and the tool does not pretend otherwise. When `gh` is
unreachable or unauthenticated, `--status` reports that as data with a remedy rather than a
traceback, because the dependency is declared, not incidental.

Scope: this narrows ADR-0010 to mission phase artifacts — a single-command router operation that
never rewrites history keeps one artifact per purpose. ADR-0005 still governs multi-phase
missions; `pr-land` is one command, not a mission phase.
