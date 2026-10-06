---
name: git-diff-digest
description: >-
  Commit-range brief payloads from local git history. Resolves a caller-supplied spec through the shared range authority and emits versioned commit, file, area, and signal rows with honest caps. Use when an agent needs what-changed context for a base..head interval without raw gh or network calls.
arguments: range_spec
argument-hint: |-
  "<spec> [PATH_FILTER] [--mode ..|...] [--commit SHA] [--file PATH] [--hunks] [--context N] [--max-lines N] [--group-by area|category|status] [--yaml|--json]"
metadata:
  managed-by: gh-router
---

# Range Brief — Resolve → Brief → Drill Down

Deterministic what-changed context for a commit interval via local git plumbing only (never `gh`, never the network). Base/range resolution belongs to the shared authority in `$SKILL_DIR/../../lib/range_authority.py` — the brief consumes it and never re-implements it.

## Script

`$SKILL_DIR/scripts/brief.py` (755, PEP 723, Python >=3.14 via `uv run`, `dependencies=["pyyaml"]`).

```bash
uv run $SKILL_DIR/scripts/brief.py 'main...HEAD'
uv run $SKILL_DIR/scripts/brief.py 'main...HEAD' --yaml > tmp/range.yaml
uv run $SKILL_DIR/scripts/brief.py 'a1b2c3 d4e5f6' --mode .. --commit a1b2c3 --hunks
```

Default output is the text brief (precomputed overview: commit count+kinds, file counts by change kind, per-area rollup, churn ranking, test-line share, author count, date span). `--yaml` is the structured default, `--json` the alternate; both decode to equal mappings. Drill down with `--commit`, `--file`, `--hunks` (`--context N`), `--max-lines N`, `--group-by area|category|status`, and an optional `PATH_FILTER`. Full flag and payload detail lives in [references/digest-schema.md](references/digest-schema.md).

## Invariants & Gates

- **Authority First**: every run resolves through `resolve_range(spec, mode)`; the brief adds rows, never resolution.
- **Honest Caps**: `truncated.*` counts omitted rows (0 when none); `range.counts` always carries true totals; every capped block prints its remainder plus a ready-to-paste rerun command quoting the same spec.
- **Full Bodies**: commit bodies render untruncated with conventional kind/scope, `#N`/sha refs, and each commit's own file rows.
- **No Directives**: the payload carries facts only — commits, files, areas, signals — and never guidance prose.
- **Fail-Loud Exits**: `0` ok · `2` malformed spec or usage · `3` refusal (unknown ref, commit outside the interval) · `1` unexpected failure.

## Flow

1. **Resolve** — caller passes a spec (`base...head`, `base..head`, or a sha pair with `--mode`); the authority returns the ordered interval, merge base, and base-side count.
2. **Brief** — read the text overview or the structured payload; per-area rollups and change signals (`breaking`, `deps`, `changelog`, `renames`, `evidence_candidates`) stay range-wide while file rows narrow under filters.
3. **Drill Down** — narrow to one `--commit` or `--file`, add `--hunks` for unified hunks, widen `--max-lines` from any remainder line, and regroup areas with `--group-by`.

`--help` answers from the header alone (no repo access) and stays within 14 lines.
