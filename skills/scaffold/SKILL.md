---
name: scaffold
description: >-
  Deterministic project scaffolding for Git, Python, Rust, TypeScript, and CI — conventional commits, semantic-release, and runtime wiring. Use when initializing or retrofitting a repo, wiring release flow, or selecting a toolchain.
arguments: flavor
argument-hint: |-
  git-scaffolding -- loads conventional commits, semantic-release, changelog, and branch hygiene
  python-scaffolding -- loads uv, .python-version, pyproject, and pytest wiring
  rust-scaffolding -- loads Cargo, rust-toolchain, fmt/clippy/test wiring
  typescript-scaffolding -- loads pnpm v12, .nvmrc, package.json/tsconfig, and oxlint/oxfmt + vite/vitest wiring (TS v7) (lib/cli/pi-extension)
  ci-scaffolding -- loads GitHub Actions verify+release and on-demand dispatch
  omitted -- loads the 80/20 spine, GDD wiring, and dispatch registry
metadata:
  manage: [git-scaffolding, python-scaffolding, rust-scaffolding, typescript-scaffolding, ci-scaffolding]
disable-model-invocation: true
---

# Scaffold

Deterministic project scaffolding — one spine, many projections. The 20% that solves 80%: every project that runs this scaffold gets the same byte-identical artifacts, so human intent (`feat`/`fix` → release) maps to one shared contract (BDD) and env truth (`commitlint`/`semantic-release`/CI) is the gate (EDD).

## GDD Wiring

- **BDD contract:** `Given` conventional commit `feat`/`fix`, `When` `repository_dispatch` `semantic-release` (or `workflow_dispatch`) fires on `main`, `Then` `semantic-release` cuts a version with `### Features`/`### Bug Fixes` and updates `CHANGELOG.md`. Shared contract is `CONTRIBUTING.md` + `.releaserc.json` (git) plus language toolchain files.
- **EDD gate:** `commitlint` + `npm run lint/typecheck/test` (or `uv`/`cargo` equivalent) are deterministic. Tag push fails if commit not conventional. Env truth is `npm ls` / `uv lock --check` / `cargo --version` + `git tag -l`.
- **Semantic vs deterministic split:** `feat`/`fix` intent → human/model; bump + notes + changelog → `commit-analyzer` / `release-notes-generator` / tool.

## Keel Spine

Keep the spine small. One load-bearing path: **declared runtime → deterministic artifacts → verification gate → on-demand release**. Language variants (Python/Rust/TypeScript/CI) are projections, not parallel spines. Adding a variant must not fork the git contract.

Grade every surface:

| Surface                                                                                                                                            | Promise                    | Change rule                                                                                                                                                                             |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Router description + `argument-hint`                                                                                                               | Public contract            | Versioned, never silently broken                                                                                                                                                        |
| Subskill SKILL.md                                                                                                                                  | Cross-module interface     | Consumer-found-by-tooling, cutover via docs                                                                                                                                             |
| `$SKILL_DIR/templates/<flavor>/<target path>` (raw bytes; `.j2` = rendered) + `scripts/scaffold.py` (one Jinja `Environment`, builders, detection) | Module internals           | Free churn behind BDD/EDD; static bytes and template structure only — computed artifacts stay in code                                                                                   |
| Generated project files (`.releaserc.json`, `.github/workflows/*`, hooks, `CHANGELOG.md`, `pyproject.toml`)                                        | Projection (not authority) | `--update` regenerates infrastructure byte-identically; project-owned files (`CHANGELOG.md`, `CONTRIBUTING.md`, manifests) are created once, then merged — see `git-scaffolding` Update |

Authority: scaffold skill owns scaffolding decisions; project owns files. Writers propose via explicit `/scaffold` invocation. Projections are regenerated from source.

## Dispatch

Read the subskill that matches the projection you need. Use `Read` (not `Skill` tool — subskills hidden from discovery).

| Flavor       | Subskill                                               | When to load                                                                                                                                                 |
| ------------ | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `git`        | `$SKILL_DIR/subskills/git-scaffolding/SKILL.md`        | Conventional commits, semantic-release, changelog, `.gitignore`, `AGENTS.md` patch — [git-scaffolding](subskills/git-scaffolding/SKILL.md)                   |
| `python`     | `$SKILL_DIR/subskills/python-scaffolding/SKILL.md`     | `uv` + `.python-version` + `pyproject.toml` wiring — [python-scaffolding](subskills/python-scaffolding/SKILL.md)                                             |
| `rust`       | `$SKILL_DIR/subskills/rust-scaffolding/SKILL.md`       | `rust-toolchain.toml` + `cargo fmt/clippy/test` wiring — [rust-scaffolding](subskills/rust-scaffolding/SKILL.md)                                             |
| `typescript` | `$SKILL_DIR/subskills/typescript-scaffolding/SKILL.md` | `pnpm` + `.nvmrc` + `package.json`/`tsconfig.json` wiring (`lib`/`cli`/`pi-extension`) — [typescript-scaffolding](subskills/typescript-scaffolding/SKILL.md) |
| `ci`         | `$SKILL_DIR/subskills/ci-scaffolding/SKILL.md`         | GitHub Actions verify+release + on-demand dispatch — [ci-scaffolding](subskills/ci-scaffolding/SKILL.md)                                                     |
| `adr`        | `$SKILL_DIR/subskills/adr-scaffolding/SKILL.md`        | `.adr-dir` pointer to `docs/adr` + `.gitignore` entry — [adr-scaffolding](subskills/adr-scaffolding/SKILL.md)                                                |

Omitted flavor loads only the spine above. For interactive scaffolding, run **Explore First** then **Grilling** — explore detects, grilling confirms only ambiguous leaves.

## Explore First — Detect Before Asking

> [!tip] GDD boundary
> **Tool owns detection, model owns recommendation.** Detection is deterministic and cheap (file existence + content sniff, no LLM guessing). Run the detector, then the model interprets the JSON into 2–4 curated combos with reasons tied to detection.

### Detection command

```bash
uv run $SKILL_DIR/scripts/scaffold.py --detect --cwd .          # JSON to stdout, human summary to stderr
uv run $SKILL_DIR/scripts/scaffold.py --detect --cwd . > /tmp/detect.json  # machine path
```

Single source of truth — no new script. `--detect` never writes; it exits 0 after printing. Cheap: `pathlib.exists()` + ≤4k content sniff per file, no deps.

### Output shape (excerpt)

```json
{
  "inferred_shape": "python",
  "project_name": "my-app",
  "files": { ".python-version": true, "pyproject.toml": true, "Cargo.toml": false, ".releaserc.json": false },
  "git_contract": { "complete": false, "changelog_guard_absent": false, "drift": null },
  "python": { "present": true, "coverage": false, "threshold": null },
  "ci": { "present": false, "variant": null, "coverage": false },
  "verify_gates": { "formatter": true, "linter": true, "typecheck": true, "tests": true }
}
```

Full keys: `cwd`, `inferred_shape` (`greenfield|python|rust|node|polyglot`), `files` (20 entries), `git_contract`, `runtimes`, `python`/`rust`/`ci`/`changelog`/`verify_gates`. Human summary on `stderr`: `shape=… present: … missing: …`, plus `git contract drift: N` when the git plan has drifted.

`git_contract` is three fields, and only the last reads the plan: `complete` (the `.releaserc.json` + `CHANGELOG.md` + `commitlint.config.js` existence census), `changelog_guard_absent` (the CI half is missing — this field used to be named `stale`, which never measured staleness), and `drift` (`{total, stale, missing, patched, appended}` — the counts `--check` exits 1 on, produced by the same git plan). `drift` is `null` only where the census is taken without the plan (the internal probes: `print_next_actions`, the coverage-script default).

### From detection → Recommended combos

After `--detect`, the model **must** render 2–4 curated combos before any grill dialog. Each combo ties reason to detected evidence, not generic menus.

> [!example] Render pattern (plain text, not JSON dump)
>
> ```
> **Explore** — python detected (.python-version + pyproject.toml, no .releaserc.json, no CI)
> present: .python-version, pyproject.toml, uv.lock  missing: .releaserc.json, release.yml
>
> **Recommended combos**
> 1. ✅ Recommended — Python 80% + CI (python) — adds coverage + verify→release; reason: python present, no coverage, no CI → smallest delta to full gate
> 2. Minimal — Git only — wire .releaserc.json + changelog guard; reason: git contract missing, keeps spine
> 3. Full — Python 90% strict + CI — for high-rigor teams; reason: opt-in, same files + threshold bump
> ```

Selection rule: **preset when confident, ask only when ambiguous.** If `inferred_shape` is confident and `git_contract.complete` clear, prefill Dialog 1/4 and skip. Read `git_contract.drift` before recommending: a non-zero `total` means the contract exists but is not current, so the first combo is `--update`, never a new flavor. Grill only leaves where detection is inconclusive (e.g. greenfield, polyglot variant, coverage threshold choice).

| Detected state                                                                               | Recommended combos (2–4, with generator)                                                                                                                                                                                                                                                                                                                                                                                                  |
| -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Greenfield** (no runtime, no git contract)                                                 | 1. Python 80% + CI — `scaffold.py --flavor all --with-coverage --coverage-threshold 80` + `ci --ci-variant python --with-coverage` + `git` (reason: most common, minimal seam) · 2. Rust + CI — `rust --with-coverage` + `ci --ci-variant rust` (reason: alternative runtime) · 3. TypeScript lib + CI — `typescript --ts-variant lib` + `ci --ci-variant node` + `git` (reason: no python/rust files, pnpm v12 + oxlint/oxfmt/vite gate) |
| **Existing Python, no scaffold** (`pyproject.toml` present, no `.releaserc.json`)            | 1. ✅ Retrofit Python 80% + CI — `python --with-coverage 80` + `ci --ci-variant python --with-coverage` + `git` (reason: preserve existing pyproject, add missing contract) · 2. Minimal — `git` only (reason: wire release without touching runtime) · 3. Add --dry-run preview first (reason: show diff before writes)                                                                                                                  |
| **Existing Rust, no scaffold** (`Cargo.toml` present)                                        | 1. ✅ Retrofit Rust + CI — `rust` + `ci --ci-variant rust` + `git` (reason: mirror python pattern) · 2. With coverage — add `--with-coverage --coverage-threshold 80` (reason: opt-in llvm-cov)                                                                                                                                                                                                                                           |
| **Python scaffold stale** (has `.releaserc.json` but missing `changelog-check.yml` or hooks) | 1. ✅ Repair git contract — `git --dry-run` then `git` (reason: changelog guard stale, `--dry-run` shows drift) · 2. Add coverage if `python.coverage==false` — `python --with-coverage 80` (reason: coverage absent)                                                                                                                                                                                                                     |
| **Scaffold complete, no coverage** (`git_contract.complete && !python.coverage`)             | 1. ✅ Add 80% coverage — `python --with-coverage 80` + `ci --ci-variant python --with-coverage` (reason: cheapest rigor bump) · 2. Add 90% strict (reason: high-rigor variant) · 3. Hold — keep as-is (reason: tests without gate is valid)                                                                                                                                                                                               |
| **Polyglot / .tool-versions**                                                                | 1. ✅ Matrix CI — `all --with-coverage 80` + `ci --matrix` note in `ci-scaffolding/SKILL.md` (reason: `polyglot==true`, needs `asdf install` sync) · 2. Single-variant CI — `ci --ci-variant python` (reason: cheapest, one verify job)                                                                                                                                                                                                   |
| **CI variant mismatch** (`Cargo.toml` + `ci.variant==node`)                                  | 1. ✅ Fix variant — `ci --ci-variant rust` (reason: runtime is rust but workflow is node) · 2. Matrix — `ci --matrix` (reason: if both runtimes present)                                                                                                                                                                                                                                                                                  |

> [!warning] Anti-pattern
> Do not dump raw JSON to the user as the recommendation. Translate detection into combos with reasons. Raw JSON is the handle; combos are the surface.

### Information boundary

- Deterministic → tool: file existence, `fail_under` sniff, `setup-uv`/`dtolnay` markers, `## [Unreleased]` check.
- Semantic → model: which combo fits team intent, threshold 80 vs 90, whether polyglot needs matrix.

## Grilling — Confirm Ambiguous Leaves

Grilling is the selection projection **after** Explore First. One truth: `scaffold.py` owns bytes; dialogs own selection. Ask only for ambiguous leaves — skip any dialog where detection is confident (preset the answer and note `preset from detect: <evidence>`). Sequential, one question per dialog, 2–4 options + `Other`, header ≤20 chars — then map answers to the generator. Branch only on prior answer (see notes). Present each dialog as plain text per `dialog-contract.md`.

### Dialog 1 — Project Shape

```yaml
Dialog:
  header: 'Project Shape'
  question: 'Which runtime owns this repo?'
  multipleChoice: false
  options:
    - label: 'Python (uv)'
      description: 'Single-runtime Python 3.14 — uv + .python-version + pyproject.toml; minimal seam'
    - label: 'Rust (cargo)'
      description: 'Single-runtime Rust — stable toolchain + rustfmt/clippy; minimal seam'
    - label: 'Node (pnpm)'
      description: 'Single-runtime Node 24 — pnpm + .nvmrc + package.json/tsconfig (lib/cli/pi-extension); minimal seam'
    - label: 'Polyglot (asdf)'
      description: 'Two+ runtimes — asdf + .tool-versions syncs uv/cargo/pnpm; adds matrix'
    - label: 'Other'
      description: 'Custom/Go/Kotlin etc. — describe stack'
```

Plain-text render:

```
**Project Shape**

Which runtime owns this repo?

1. Python (uv) — Single-runtime Python 3.14 — uv + .python-version + pyproject.toml
2. Rust (cargo) — Single-runtime Rust — stable toolchain + rustfmt/clippy
3. Node (pnpm) — Single-runtime Node 24 — pnpm + .nvmrc + package.json/tsconfig (lib/cli/pi-extension)
4. Polyglot (asdf) — Two+ runtimes — asdf + .tool-versions syncs uv/cargo/pnpm
5. Other — Custom stack
```

### Dialog 2 — Verification Gate

```yaml
Dialog:
  header: 'Verification Gate'
  question: 'Which gates should the pre-merge check enforce?'
  multipleChoice: true
  options:
    - label: 'Formatter'
      description: 'Enforces style without debate — ruff format / cargo fmt / oxlint / oxfmt --check'
    - label: 'Linter'
      description: 'Catches bugs/idioms — ruff check / clippy -D warnings / oxlint / oxfmt --check'
    - label: 'Type check'
      description: 'Proves contracts — basedpyright strict / tsc --noEmit / cargo check'
    - label: 'Tests'
      description: 'Proves behavior — pytest / cargo test / pnpm test; required for coverage'
    - label: 'Other'
      description: 'Custom gate (e.g., audit, zizmor, actionlint)'
```

Plain-text render (multi-select):

```
**Verification Gate**

Which gates should the pre-merge check enforce? (select any)

1. Formatter — ruff format / cargo fmt
2. Linter — ruff check / clippy -D warnings
3. Type check — basedpyright strict / tsc --noEmit
4. Tests — pytest / cargo test / pnpm test
5. Other — Custom gate
```

> Branching: if Q1=Python, defaults map to ruff/basedpyright/pytest; if Rust, to fmt/clippy/test; if Node, to biome/tsc --noEmit/vitest (tsx runner) — but user may skip any leaf; skipping does not remove the flavor file, only the gate step.

### Dialog 3 — Coverage (conditional)

Only ask if **Tests** selected in Dialog 2; otherwise skip.

```yaml
Dialog:
  header: 'Coverage'
  question: 'Enforce test coverage gate?'
  multipleChoice: false
  options:
    - label: 'No coverage'
      description: 'Tests run without gate — cheapest, no fail_under'
    - label: '80% line (Recommended)'
      description: 'Balances rigor and velocity — fail_under=80, lcov emitted'
    - label: '90% strict'
      description: 'High rigor — fail_under=90, may slow velocity'
    - label: 'Other'
      description: 'Custom threshold 0–100'
```

Plain-text render:

```
**Coverage**

Enforce test coverage gate?

1. No coverage — Tests without gate
2. 80% line (Recommended) — fail_under=80, lcov emitted
3. 90% strict — fail_under=90
4. Other — Custom threshold
```

### Dialog 4 — CI Release

```yaml
Dialog:
  header: 'CI Release'
  question: 'Wire on-demand release + CI verify gate?'
  multipleChoice: false
  options:
    - label: 'Yes (Recommended)'
      description: 'repository_dispatch + workflow_dispatch, verify→release with pinned SHAs and minimal perms'
    - label: 'No — local only'
      description: 'No workflow; local commitlint + verify.sh only'
    - label: 'Other'
      description: 'Custom variant/matrix (e.g., python+rust)'
```

Plain-text render:

```
**CI Release**

Wire on-demand release + CI verify gate?

1. Yes (Recommended) — repository_dispatch + workflow_dispatch, verify→release
2. No — local only
3. Other — Custom variant/matrix
```

### Selection → Generator Mapping

After Explore + Grilling, map **preset + confirmed** answers to the deterministic generator. Tool owns bytes; model proofreads mixed warnings on stderr. If detection was confident, Dialog 1/4 values come from `--detect` preset (note `preset from detect`), not re-asked.

| Grilling answers                   | Generator invocation                                                                                                                                                                                                                                                                                                    |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Python + Tests + 80% + Yes         | `uv run $SKILL_DIR/scripts/scaffold.py --flavor python --with-coverage --coverage-threshold 80 --project-name <name>` then `uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant python --with-coverage --coverage-threshold 80` + `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --project-name <name>` |
| Rust + Tests + 90% + Yes           | `uv run $SKILL_DIR/scripts/scaffold.py --flavor rust --with-coverage --coverage-threshold 90` + `uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant rust --with-coverage --coverage-threshold 90`                                                                                                           |
| Python + Tests + No coverage + Yes | `uv run $SKILL_DIR/scripts/scaffold.py --flavor python --project-name <name>` (no flag) + `uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant python --project-name <name>`                                                                                                                                 |
| Any shape + No Tests + — + Yes     | Skip `--with-coverage` entirely — coverage flag is inert without tests; generator omits `pytest-cov`/`llvm-cov` wiring                                                                                                                                                                                                  |
| Polyglot Python+Rust + 80% + Yes   | `uv run $SKILL_DIR/scripts/scaffold.py --flavor all --with-coverage --coverage-threshold 80` + `uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant python --with-coverage` and matrix note in `$SKILL_DIR/subskills/ci-scaffolding/SKILL.md`                                                                |
| Any + Formatter skipped            | Generator still writes file (formatter config is deterministic); CI verify step for that gate is omitted by the caller — file remains byte-identical, gate is optional leaf                                                                                                                                             |

> Formatter/linter/type/test are always wired in the flavor file (one concept one location). Skipping a gate means not running it, not deleting its config — keeps the spine small. Coverage is the only leaf that changes file bytes (`pyproject.toml` `pytest-cov` + `[tool.coverage.*]`, Rust `llvm-cov` note, CI `*COVERAGE_YML`). All other leaves are verification choices, not artifact changes.

Omitted grilling (direct dispatch) defaults to: Tests=on, Coverage=off, CI=Yes, threshold 80 — so `/scaffold python-scaffolding` without grilling still gets the current byte-identical output.

## Trade-offs

- Latency vs context efficiency: on-demand loading keeps router lean; deep templates disclosed behind subskill pointers.
- Artifact hygiene: consolidate, don't accumulate; one concept one location. Cross-reference, don't copy-paste.
- Tool preference: `uv run`, `cargo`, `pnpm`, `rg`, `fd` per `tool-preferences.md`; `asdf` + `.tool-versions` when multi-runtime.

## Runtime Matrix — Declared Runtimes

Per `development-patterns.md` §3 — native tool owns version+deps; commit version file.

| Project shape       | Owner tool              | Version file(s)                                        | Install        |
| ------------------- | ----------------------- | ------------------------------------------------------ | -------------- |
| Python only         | `uv`                    | `.python-version` (3.14), `pyproject.toml` + `uv.lock` | `uv sync`      |
| Rust only           | `cargo`                 | `rust-toolchain.toml`, `Cargo.toml`                    | `cargo fetch`  |
| Node only           | `pnpm`/`corepack`/`nvm` | `.nvmrc` or `packageManager` in `package.json`         | `pnpm i`       |
| Multi (2+ runtimes) | `asdf`                  | `.tool-versions` + each native version file            | `asdf install` |

Native tool still owns deps — `asdf` syncs, it does not replace `uv`/`cargo`/`pnpm`.

## Deterministic Generation — Tool Owns Bytes

### Boundary contract — per field, on a time axis

Run 1 (field absent) means the tool writes byte-identical bytes with no model
judgment. Run 2 and later (field present) means the project owns the file and
the model decides replace / update one field / untouched — the tool never
silently chooses the destructive option and never escalates a one-field edit
into a whole-file write. `--update` preserves project-owned files and reports
them as NEXT actions; `ensure <op>` performs one confirmed field edit (absent
adds minimally, present reports unchanged, invalid or ambiguous refuses).
Package.json edits normalize to 2-space JSON (key order kept, non-ASCII kept
literal, trailing-newline state kept).

```bash
uv run $SKILL_DIR/scripts/scaffold.py ensure rust-dep --name tokio --version 1
uv run $SKILL_DIR/scripts/scaffold.py ensure py-dep --req "httpx>=0.27"
uv run $SKILL_DIR/scripts/scaffold.py ensure ts-dep --name zod --version "^3"
uv run $SKILL_DIR/scripts/scaffold.py ensure ts-script --name coverage --cmd "vitest run --coverage"
uv run $SKILL_DIR/scripts/scaffold.py ensure coverage-threshold --flavor python --value 90
```

`--coverage-script` names the package.json script the coverage gate runs
(default: detected script, else `coverage`); it reaches the rendered workflow
through `do_ci` for `--flavor ci` and `--flavor all`.

Do not hand-copy templates. Run the generator — it emits byte-identical artifacts and warns on mixed files:

```bash
uv run $SKILL_DIR/scripts/scaffold.py --flavor git --project-name <name>      # git contract
uv run $SKILL_DIR/scripts/scaffold.py --flavor python --project-name <name>   # + .python-version/pyproject
uv run $SKILL_DIR/scripts/scaffold.py --flavor python --with-coverage --coverage-threshold 80  # + pytest-cov wiring
uv run $SKILL_DIR/scripts/scaffold.py --flavor rust --project-name <name>     # + rust-toolchain/Cargo
uv run $SKILL_DIR/scripts/scaffold.py --flavor rust --with-coverage --coverage-threshold 90   # + llvm-cov wiring
uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant python|rust|node
uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant python --with-coverage --coverage-threshold 80
uv run $SKILL_DIR/scripts/scaffold.py --flavor all --project-name <name>     # git+python+rust
uv run $SKILL_DIR/scripts/scaffold.py --flavor all --with-coverage --coverage-threshold 80 --dry-run
uv run $SKILL_DIR/scripts/scaffold.py --flavor git --dry-run                  # diff without writing
uv run $SKILL_DIR/scripts/scaffold.py --update --cwd .                        # existing repo: refresh in place, preserve project-owned files, print NEXT
uv run $SKILL_DIR/scripts/scaffold.py --check --cwd .                         # one line per drifted file; exit 1 when the repo is out of sync
uv run $SKILL_DIR/scripts/scaffold.py --update --dry-run --json               # the plan as data instead of prose
uv run $SKILL_DIR/scripts/scaffold.py --update --merge-mixed                  # insert CONTRIBUTING.md sections the project is missing
```

### Self-reporting — one call answers "what is stale"

Every run reports once, in the mode the flags select. `--summary`/`--check` collapse prose to one line per file; `--json` emits the plan as data. **Do not parse diffs to decide what to do** — `--check` exits 1 on drift, so it is also a CI gate:

| Flag            | Effect                                                                                                                                                                              |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--check`       | `--update --dry-run --summary`: `stale`/`missing`/`patched`/`preserved` per file + `drift N`; exit 1 when drift > 0                                                                 |
| `--summary`     | same lines for any run; exit code unchanged                                                                                                                                         |
| `--json`        | plan (`entries[]`, `findings[]`, `notes[]`, `drift`) on stdout; `--detect --json` drops the human summary                                                                           |
| `--self-check`  | validate claimed files: `compile()` for `.py`, `bash -n` for shell/hooks, JSON/YAML parse, exec bit, and `scripts/…` references resolved; **runs automatically after a real write** |
| `--merge-mixed` | insert the `##` sections a preserved `CONTRIBUTING.md` is missing (never rewrites an existing line)                                                                                 |

`--detect` now also returns `findings[]` (`area`, `detail`, `remedy`) naming stale changelog, missing PR template, a pnpm/npm lockfile mismatch, and a vendored copy of a sibling skill — each with the command that fixes it. Blocking findings exit 1; a dangling reference only warns (it is a gap in what the skill ships, not in the target repo). `git_contract.drift` is the same verdict `--check` reports because it runs the same git plan, and `tests/scaffold/test_detect_drift.py` holds the two together — a detector that says "not stale" while `--check` says "drift 8" is the defect that test exists to prevent.

- **Pure-deterministic** (no proofread): `.releaserc.json`, `.github/workflows/release.yml`, `commitlint.config.js`, `CHANGELOG.md`, `.gitignore` entries, `.python-version`, `rust-toolchain.toml`, `src/lib.rs`, `src/<module>/__init__.py`, `tests/test_smoke.py`.
- **Mixed** (script writes skeleton + warns on stderr → proofread): `CONTRIBUTING.md` (`{{project_name}}` + Before PR line), `pyproject.toml`/`Cargo.toml` (name/description/edition; with `--with-coverage` also `fail_under`), `AGENTS.md` patch (keep 3 sections, verify pointer wording).
- **Project-neutral** (the target's facts only): the `git` flavor's `.github/ISSUE_TEMPLATE/*` + `pull_request_template.md` and `shared/CONTRIBUTING.*` — a generated repo must never inherit the scaffold author's own projects (`test_templates.py::test_shipped_bytes_name_no_foreign_project`). One contract spans two files: `# Changelog` is the first line of `CHANGELOG.md` **and** `changelogTitle` in `.releaserc.json`, because `@semantic-release/changelog` rewrites the title in place only while the file starts with it; ship half and every release prepends its notes above the heading (`test_changelog_title.py` runs the plugin twice).

- `$SKILL_DIR/scripts/scaffold.py` — deterministic source of truth (tool owns bytes); raw templates under `$SKILL_DIR/templates/<flavor>/<target path>` ship verbatim and `.j2` templates render through one Jinja `Environment` (the script's single PEP-723 dependency: `jinja2`); `tests/scaffold/test_templates.py` pins raw file hashes, layout/registry coherence and every rendered cell; preview with `uv run $SKILL_DIR/scripts/scaffold.py --flavor <git|python|rust|ci> --dry-run`; detect with `uv run $SKILL_DIR/scripts/scaffold.py --detect --cwd .` (JSON to stdout, summary to stderr)
- `$SKILL_DIR/scripts/verify.sh` — deterministic gate runner (`--dry-run` + `validate-deps` + `npm ls`/`cargo` checks)

### Adding a Flavor — Gate Contract

A flavor is done when **every gate it wires passes on a freshly generated tree**. The generator owns the bytes; the flavor owns the commands that judge them — and the two disagree silently.

1. **Run the gates on fresh output**, before any user edit: `--flavor <new>` plus `--flavor ci --ci-variant <new>`, then every `run:` line from the generated `release.yml`. Installed tools and plausible config are not evidence. Failure modes: a flavor wiring `cargo fmt`/`clippy`/`test` without shipping an `.rs` target dies on `failed to parse manifest: no targets specified`; one wiring `pytest` without a test exits 5; one whose gate formats bytes the emitter wrote by hand fails the format check.
2. **Ship the minimum target each gate needs** — `src/lib.rs` for `cargo`, a smoke test for `pytest`/`vitest`, `go.mod` + a package for `go build`. `do_typescript` writes `src/index.ts` + `tests/index.test.ts` for exactly this reason; check the other flavors do the equivalent before wiring their gate.
3. **Bytes a gate judges must be canonical for that gate's tool, pinned exactly** to the version the generated repo resolves, canonicalized after substitution at the single write seam — see `git-scaffolding` § Deterministic Artifacts for the oxfmt instance and the bump procedure. Canonicalization is per _file_, never per flavor: one formatter's reach spans files several flavors own, so grouping the invocations differently must not change a byte (`--flavor all` and the same flavors run one at a time are the same tree).
4. **Add the fresh-tree gate test with the flavor.** `tests/scaffold/test_oxfmt_canonical.py` is the pattern: generate, run the wired commands, assert exit 0. Rules 1–3 without this test are a hope, not a contract.
5. **Pin the gate's configuration, not just its command.** A wired gate inherits whatever its tool defaults to, and defaults move under it: `ruff check` selected 413 rules in 0.16.7, and an unconfigured `oxfmt` rewrote flow mappings no template author saw. Name the selection where the repo can read it (`[tool.ruff.lint] select`), and never pass a flag that disables a guard.
6. **Give every gate something to catch drift with** — a range plus a lockfile, not a wildcard. Generated `devDependencies` use caret ranges inside the reviewed major (`^7`, `^8`), except where the artifact _is_ the contract (`oxfmt` exact), and the generated job runs plain `pnpm install`: pnpm's CI default is already frozen-when-a-lockfile-exists, so a stale lockfile fails loudly instead of silently re-resolving. Never pass `--no-frozen-lockfile` in a generated job — it disables exactly the guard that would have caught the formatter drift above (`test_no_variant_disables_the_lockfile_guard`).

| Flavor                 | Formatter (reach)                                        | Wired gates                                                          |
| ---------------------- | -------------------------------------------------------- | -------------------------------------------------------------------- |
| typescript             | `oxfmt` — `json/yaml/md/toml/js/ts`; rejects `.py`/`.sh` | `oxlint .` · `oxfmt --check .` · `tsc --noEmit` · `vitest run`       |
| python                 | `ruff format` — `.py` at the generated `line-length`     | `ruff check .` · `ruff format --check .` · `basedpyright` · `pytest` |
| rust                   | `rustfmt` via `cargo fmt` (`.rs` only)                   | `cargo fmt --check` · `cargo clippy -- -D warnings` · `cargo test`   |
| go (not supported yet) | `gofmt`/`gofumpt` (`.go`)                                | `go vet ./...` · `gofmt -l .` · `go test ./...`                      |

Order the dependency: pick the gate set first, derive the formatter's reach from it, let that reach decide which emitted files get canonicalized — never the reverse. A gate whose formatter is unwired still judges bytes without ever repairing them, and a formatter whose files no gate judges repairs bytes nobody asked about; both are drift.
