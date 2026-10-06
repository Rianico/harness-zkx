# Range Brief Payload (`git-diff-digest`)

Flag and payload detail for `$SKILL_DIR/scripts/brief.py`. The brief resolves
its interval through `lib/range_authority.py` (`resolve_range(spec, mode)`,
local plumbing only) and layers the versioned payload below on top. For the
one-phase workflow, see [SKILL.md](../SKILL.md).

## Usage

```bash
uv run $SKILL_DIR/scripts/brief.py SPEC [PATH_FILTER] [options]
```

`SPEC` is `base...head`, `base..head`, a single ref (base auto-resolved:
explicit base, then `origin/HEAD`, `origin/main`, `origin/master`), or a
whitespace-separated sha pair. When `SPEC` carries no operator, `--mode`
(`..` or `...`, default `...`) applies. `--pr [SPEC]` defaults to `HEAD` as a
single ref with the same base order and `--mode` applying. `PATH_FILTER`
narrows file and area rows by exact path or subtree prefix.

## Flags

| Flag | Effect |
| --- | --- |
| `--mode ..\|...` | Operator for operator-less specs (default `...`). |
| `--repo DIR` | Path inside the repository (default `.`). |
| `--commit SHA` | Narrow commit rows to one member of the interval (full or short sha). |
| `--file PATH` | Repeatable file narrowing (exact path or subtree prefix). |
| `--hunks` | Text only: unified hunks under each shown file row. |
| `--context N` | Hunk context lines (default `3`, must be ≥ 0). |
| `--max-lines N` | Cap per capped block (default `40`, must be > 0). |
| `--group-by KEY` | Area rollup key: `area` (top directory), `category`, or `status`. |
| `--yaml` | Structured payload as YAML (the structured default). |
| `--json` | Structured payload as JSON (alternate; decodes to an equal mapping). |
| `--pr [SPEC]` | Landing view for the range through the range authority only (local git only); `SPEC` optional, default `HEAD` as a single ref with `--mode` applying; adds the `landing` block to the text brief and the payload; zero-commit head refuses exit `3`. |
| `--verify FINGERPRINT` | Recompute the range fingerprint for `SPEC` and compare to the expected 64-char value: hit exits `0` with confirmation, miss exits `3` naming `spec`, `merge_base`, or the commit set; malformed values exit `2`. |

`--yaml` and `--json` are exclusive. `--hunks` affects the text brief only,
so the structured keys below stay fixed.

## Payload (`schema: 1`)

- `range`: `spec_in`, `mode` (effective operator), `merge_base`,
  `only_in_base` (base-side count, always computed), `resolved_from`,
  `counts` (`commits`, `files`, `insertions`, `deletions`, `added`,
  `modified`, `renamed`, `deleted`), `fingerprint`.
- `commits` (oldest first): `sha`, `short`, `subject`, `type`, `scope`,
  `breaking` (`!` marker or `BREAKING CHANGE` body), `refs` (`numbers` from
  `#N`, `shas` in first-seen order), `author` (`name`, `email`), `date`
  (iso-strict), `body` (full, never capped), `counts` (`files`,
  `insertions`, `deletions`), `files` (own rows: `path`, `status`,
  `insertions`, `deletions`; first-parent view for merges).
- `areas`: `path`, `files`, `insertions`, `deletions` per `--group-by` key,
  ordered by churn. Never capped.
- `files`: `path`, `status` (`added`, `modified`, `deleted`, `renamed`,
  `copied`, `type-changed`, `unmerged`, `unknown`), `insertions`,
  `deletions`, `commits` (interval commits touching the path), `category`
  (`source`, `test`, `config`, `docs`, `build`, `other`), `binary`,
  `renamed_from` (set only for renames). Churn-ordered.
- `signals` (always range-wide): `breaking` (short shas), `deps`
  (manifest paths changed), `changelog` (bool), `renames` (new paths),
  `evidence_candidates` (changed test and workflow paths).
- `truncated`: `files` and `commits` omitted-row counts (`0` when none).
- `landing` (pr view only): `commits` (range commit count), `conventional` (count of conventional subjects), `multi_entry` (true when the change set carries more than one commit that would each merit a changelog entry, i.e. `commits > 1`). Rendered in the text brief and the payload.
- `verification` (verify view with `--json`/`--yaml` on hit): `expected`, `actual`, `ok`.
`PATH_FILTER` / `--file` narrow the file view (`files`, `areas`,
`range.counts` over that view); `signals` and the fingerprint stay
range-wide. `--commit` narrows commit rows only.

## Semantics

- **True totals**: `range.counts` reflects the full (possibly filtered) view
  even when caps omit rows; `truncated.*` reports exactly those omissions.
- **Remainder lines**: every capped text block prints its omitted count plus
  a ready-to-paste rerun quoting the same spec, e.g.
  `uv run $SKILL_DIR/subskills/git-diff-digest/scripts/brief.py 'main...HEAD' --mode ... --max-lines 42`.
- **Fingerprint**: `sha256(spec_in, mode, merge_base, ordered commit shas)`.
  Emitted in every readout (range, pr, verify); `resolved_from` is present in
  text and payload; `only_in_base` is present in the text brief.
  Caps and flags change the rendering, never the fingerprint.
- **Pr**: full range payload plus `landing`; zero-commit head refuses exit `3`
  with a model-facing fix (head is behind its base; nothing to land).
- **Verify**: recompute and compare field by field (`spec`, `merge_base`,
  commit set); hit exits `0` confirming, miss exits `3` naming what moved.
- **Facts only**: the payload carries commits, files, areas, and signals —
  no guidance prose.
- **Exit codes** (via `range_authority.exit_code_for`): `0` ok (range, pr,
  verify hit) · `2` malformed spec, fingerprint shape, or usage · `3` refusal
  (unknown ref, commit outside the interval, empty pr range, verify mismatch)
  · `1` unexpected failure.
