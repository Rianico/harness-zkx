# TICKET: #266-t2-seam-derivation — pr-land derives state and emits facts

Target files / Seams: `skills/gh-router/subskills/pr-land/scripts/{pr.py,_draft.py,_check.py,_github.py,_squash.py,_options.py}`, `skills/gh-router/SKILL.md`, `skills/gh-router/subskills/{pr-land,pr-refine,pr-enhance}/SKILL.md`, `tests/gh-router/`, `tests/{scaffold,setup-lsz-skills,docs-scraper,eval-gate}/`. Read `docs/adr/0021-pr-land-derives-state-and-emits-facts-instead-of-persisting-artifacts.md` and `GLOSSARY.md` (entries under **Pull Request Lifecycle**) first — they are the contract.

## 1. Intent (IDD)

- **Problem**: `pr-land` decides things and hides the facts. `draft.json` has no production reader; the scaffold at the fixed `.lsz/tmp/pr_body.md` path was preserved byte-for-byte across branches; `title_supplied` is computed and dropped before the gate; one title decision is evaluated in three places with three different information states; no artifact carries push state.
- **Proposed Outcome**: state is derived per run from git and `gh`, every decision's facts are emitted, and no phase artifact is persisted. Tranche T1 (push precondition, stamp recovery) already landed; **do not regress it**.
- **Non-Negotiable Constraints**:
  - **Schema first.** Implement the pinned schema below before wiring behaviour, and treat it as the contract. Adding fields is allowed; renaming, removing, or retyping the pinned ones is not.
  - `--status` is read-only and **never refuses**: it exits 0 and reports predicates, failure states, the artifact, the title facts, the squash preview, `refusals[]` and `transitions[]`. `--check` stays the gate with its existing exit codes (`1` refusal, `2` no body supplied).
  - Delete `draft.json` entirely, plus `is_untouched_scaffold`, the scaffold signature helpers and `--out-dir`. Nothing may read a pre-existing artifact to decide anything.
  - A body-less `--check` writes the scaffold only when the leaf is absent; when present it writes nothing and reports the path plus `stale` (computed against the head commit). `--force-scaffold` still overwrites deliberately.
  - `refusals[].site` names the **caller's** input or artifact (`--title`, `pr_body.md:12`) and never a `pr-land` source location; source locations stay behind `--verbose`.
  - Keep the T1 behaviour: push only from `create_or_reuse_pr`, never from `--check`/`--status`; no force-push; stamp recovery stays soft.
  - Out of scope: the `time.monotonic()` change in docs-scraper, new flags beyond `--status`/`--out`/`--force-scaffold`, and any change to `scripts/state.sh` behaviour (only the SKILL.md boundary sentence).
  - Commit locally; do not push, open a PR, or merge.

### Pinned schema: `--status --json`

```json
{
  "schema": "gh-router/pr-land/status@1",
  "repo": "owner/name",
  "head": "branch", "base": "main",
  "predicates": {
    "branch_pushed": true, "remote": "origin", "ahead": 0, "behind": 0,
    "pr_state": "none|open|merged|closed", "pr_number": null, "pr_draft": false,
    "body_state": "none|scaffold|unfilled|ready", "worktree_clean": true,
    "changelog_stamped": false, "head_pushed": false,
    "checks": {"state": "none|pending|green|red", "ok": 0, "total": 0},
    "mergeable": "unknown|mergeable|conflicting"
  },
  "failure_states": ["diverged"],
  "artifact": {"path": ".lsz/gh-router/<head-slug>.md", "stale": true},
  "title": {"text": "…", "chars": 63, "budget": 100, "derived": true},
  "squash_body_preview": "…",
  "refusals": [{"code": "string", "reason": "string", "remedy": "string", "site": "--title"}],
  "transitions": [{"command": "string", "preconditions": ["string"], "mutation": "none|local|remote"}]
}
```

On `--status`, `refusals[]` and `transitions[]` are advisory and the exit code is 0. On a mutating command, a `refusals[]` entry means exit 1 with the same entries on stderr.

## 2. Acceptance (from #266)

1. `--status`/`--json` per the schema above, with the legal transitions for the current state and `mutation` on each.
2. `draft.json` gone; facts on stdout (scaffold payload when body-less, JSON with `--json`), commentary on stderr, and `squash_body_preview` preserved as output (ADR-0019 requires the preview).
3. Scaffold leaf defaults to the head-ref slug under `.lsz/gh-router/`; `--out <leaf>` overrides; write-only-if-absent; otherwise report path + `stale`; signature machinery and `--out-dir` deleted.
4. `refusals[]` as data everywhere, with the `site` rule above; `gh` missing/unauthenticated/offline becomes a structured refusal, not a traceback; judgment calls emit state + the transition list, and a mutating command whose transition cannot proceed still refuses (exit 1) with those facts attached.
5. Title provenance: derived title, length and budget in the report; the refusal names the derivation; under `--merge` the title gate runs **before** `create_or_reuse_pr`.
6. Stamp failure after PR creation hard-fails with the PR url and remedy (the half deferred from T1), while the recovery path stays idempotent.
7. Reused open draft PR: refuse on `--watch`/`--merge` with exit 1 and record the ready-flip transition; `--status` exits 0 with it attached. No `--ready` flag.
8. Docs: `skills/gh-router/SKILL.md:35` landing row gains `--title`; the body-file examples in `pr-land`, `pr-refine` (`SKILL.md:25`) and `pr-enhance` move to `.lsz/gh-router/`; the router SKILL states the boundary — `state.sh` is human-facing orientation (`gh pr view`), `--status` is the machine-readable landing state and is authoritative for landing decisions.
9. Migrate the call sites and tests that assume the old artifacts. A grep list is in #266; confirm each for real coupling rather than bulk-editing.

## 3. Verification Contract (GDD/EDD)

- **Check Command**: `bash scripts/check.sh` (baseline on this branch: **2924 passed, 1 skipped**), plus `uv run pytest tests/gh-router -q`.
- **Required Evidence**:
  - Schema conformance: a test that loads `--status --json` and asserts every pinned key, type, and enum value.
  - The read-only proof: instrumented run showing `--status` pushes nothing, creates nothing, and deletes nothing.
  - Scaffold proofs: absent leaf → written; present leaf → untouched, `stale` reported; `--force-scaffold` → overwritten; `--out other/leaf.md` honoured.
  - Deletion proofs: `draft.json` never written on any path (`--check`, create, merge); `--out-dir` absent from the CLI; no reference to the removed helpers remains outside the CHANGELOG.
  - Refusal-shape proofs: one mechanical, one contract, one judgment case, each showing `refusals[]`/`transitions[]` and the exit code.
  - Red-then-green for the acceptance items you implement, plus `bash scripts/check.sh` output showing `All gates passed.` and the final total.
  - Commit SHAs and `git diff --stat`.

Work in atomic commits along the boundaries: schema + `--status`, artifact retirement, refusals/transitions, title/stamp contracts, docs. Reply with the standard template (`uv run skills/herdr/scripts/herdr_reply.py pi --file <payload> --ticket '#266-t2-seam-derivation'`). Delegate exploration, multi-file editing, and log triage to ephemeral subagents; never let a subagent call Herdr scripts. If a requirement conflicts with ADR-0021 or would touch out-of-scope files, reply `BLOCKED` rather than deciding.
