---
name: git-diff-digest
description: >-
  Commit-range brief payloads from local git history. Resolves a caller-supplied spec through the shared range authority and emits versioned commit, file, area, and signal rows with honest caps. Use when an agent needs what-changed context for a base..head interval without raw gh or network calls.
arguments: range_spec
argument-hint: |-
  "<spec> [PATH_FILTER] [--mode ..|...] [--commit SHA] [--file PATH] [--hunks] [--context N] [--max-lines N] [--group-by area|category|status] [--yaml|--json] [--pr [SPEC]] [--verify FINGERPRINT]"
metadata:
  managed-by: gh-router
---

# Range Brief — Resolve → Brief → Drill Down

Goal: give deterministic what-changed context for a commit interval from local git plumbing only — never `gh`, never
the network. The payload is the change-fact source for a PR body (`pr-enhance`, `pr-land`). Base/range resolution
belongs to the shared authority in `$SKILL_DIR/../../lib/range_authority.py`: consume it, never re-implement it.

## Script

`$SKILL_DIR/scripts/brief.py` — PEP 723, run with `uv run`.

| Trigger | Run | Output |
| --- | --- | --- |
| What changed in a range | `uv run $SKILL_DIR/scripts/brief.py '<base>...HEAD'` | text brief: commit count and kinds, file counts by change kind, area rollup, churn ranking, test-line share, author count, date span |
| Facts for a PR body | `uv run $SKILL_DIR/scripts/brief.py '<base>...HEAD' --pr --yaml > tmp/pr.json` | the `schema: 1` payload plus its `landing` block |
| One commit | `uv run $SKILL_DIR/scripts/brief.py '<spec>' --commit <sha>` | that commit's own rows, uncapped body |
| One file | `uv run $SKILL_DIR/scripts/brief.py '<spec>' --file <path> --hunks` | the file row plus unified hunks (`--context N`) |
| Re-check a stored range | `uv run $SKILL_DIR/scripts/brief.py '<spec>' --verify <fingerprint>` | hit exits `0` confirming; mismatch exits `3` naming what moved |
| Uncommitted edits beside a range | `uv run $SKILL_DIR/scripts/brief.py '<spec>'` | one `dirty` block plus one `stale-when-dirty` warning. The fingerprint does not move (see [Commit-Only Fingerprint](#invariants--gates)) |

| Flag | Effect |
| --- | --- |
| `PATH_FILTER` | narrows file and area rows to a path or subtree prefix |
| `--mode ..` / `--mode ...` | operator for a spec that carries none (default `...`) |
| `--commit SHA` | narrows commit rows to one member of the interval |
| `--file PATH` | repeatable file narrowing |
| `--hunks` | adds unified hunks to the text brief |
| `--context N` | hunk context lines (default `3`) |
| `--max-lines N` | caps each capped block (default `40`) and prints the remainder with a rerun line |
| `--group-by area` / `category` / `status` | area rollup key |
| `--yaml` / `--json` | structured payload; both decode to equal mappings |
| `--pr [SPEC]` | adds the `landing` block for the same range (default `HEAD`) |
| `--verify FINGERPRINT` | recomputes the range fingerprint and compares it |
| `--repo DIR` | path inside the repository (default `.`) |

Flag detail and payload keys per block: [references/digest-schema.md](references/digest-schema.md). `--help` answers
from the header, outside a repo, in 14 lines.

## Invariants & Gates

- **Authority First** — every run resolves through `resolve_range(spec, mode)`. The brief adds rows, never resolution.
- **Commit-Only Fingerprint** — the authority and the fingerprint read commits only. A dirty tree adds the `dirty` block (worktree `head`/`branch`, `git status --porcelain` rows, and `git diff HEAD --stat` rows so staged and unstaged text changes both appear). It prints one warning that the fingerprint reads `stale-when-dirty`, and changes no `range` field. A clean tree emits no `dirty` block. The dirty read is advisory and capped. `--max-lines` bounds both listings with the shared remainder row. An unreadable `git status` (stale lock, bad index) skips the block instead of failing the brief. `--verify` still exits `0` on a matching fingerprint.
- **Honest Caps** — `truncated.*` counts omitted rows (`0` when none). `range.counts` always carries true totals. Every capped block prints its remainder plus a ready-to-paste rerun quoting the same spec.
- **Full Bodies** — commit bodies render untruncated, with conventional kind/scope and `#N`/sha refs.
- **Facts Only** — the payload carries commits, files, areas, and signals, and never guidance prose.
- **Fail-Loud Exits** — `0` ok (range, pr, verify hit) · `2` malformed spec, fingerprint shape, or usage · `3` refusal (unknown ref, commit outside the interval, empty pr range, verify mismatch) · `1` unexpected failure.

## Flow

1. **Resolve** — the authority turns your spec into the ordered interval, merge base, and base-side count. Done when the range line names the merge base you expect.
2. **Brief** — read the text overview or the structured payload. Per-area rollups and signals (`breaking`, `deps`, `changelog`, `renames`, `evidence_candidates`) stay range-wide while file rows narrow under filters. Done when `range.counts` and every `truncated.*` row are accounted for.
3. **Drill Down** — narrow to a commit or file, add `--hunks`, widen `--max-lines` from a remainder line, regroup with `--group-by`. Done when no remainder line matters.
