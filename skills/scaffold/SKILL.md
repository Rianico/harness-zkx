---
name: scaffold
description: >-
  Deterministic project scaffolding for Git, Python, Rust, and CI — conventional commits, semantic-release, and runtime wiring. Use when initializing or retrofitting a repo, wiring release flow, or selecting a toolchain. TRIGGER: scaffold, init project, retrofit, semantic-release, conventional commits
arguments: flavor
argument-hint: |-
  git -- loads conventional commits, semantic-release, changelog, and branch hygiene
  python -- loads uv, .python-version, pyproject, and pytest wiring
  rust -- loads Cargo, rust-toolchain, fmt/clippy/test wiring
  ci -- loads GitHub Actions verify+release and on-demand dispatch
  omitted -- loads the 80/20 spine, GDD wiring, and dispatch registry
metadata:
  manage: [git, python, rust, ci]
---

# Scaffold

Deterministic project scaffolding — one spine, many projections. The 20% that solves 80%: every project that runs this scaffold gets the same byte-identical artifacts, so human intent (`feat`/`fix` → release) maps to one shared contract (BDD) and env truth (`commitlint`/`semantic-release`/CI) is the gate (EDD).

## GDD Wiring

- **BDD contract:** `Given` conventional commit `feat`/`fix`, `When` `repository_dispatch` `semantic-release` (or `workflow_dispatch`) fires on `main`, `Then` `semantic-release` cuts a version with `### Features`/`### Bug Fixes` and updates `CHANGELOG.md`. Shared contract is `CONTRIBUTING.md` + `.releaserc.json` (git) plus language toolchain files.
- **EDD gate:** `commitlint` + `npm run lint/typecheck/test` (or `uv`/`cargo` equivalent) are deterministic. Tag push fails if commit not conventional. Env truth is `npm ls` / `uv lock --check` / `cargo --version` + `git tag -l`.
- **Semantic vs deterministic split:** `feat`/`fix` intent → human/model; bump + notes + changelog → `commit-analyzer` / `release-notes-generator` / tool.

## Keel Spine

Keep the spine small. One load-bearing path: **declared runtime → deterministic artifacts → verification gate → on-demand release**. Language variants (Python/Rust/CI) are projections, not parallel spines. Adding a variant must not fork the git contract.

Grade every surface:

| Surface                                                                       | Promise                    | Change rule                                                         |
| ----------------------------------------------------------------------------- | -------------------------- | ------------------------------------------------------------------- |
| Router description + `argument-hint`                                          | Public contract            | Versioned, never silently broken                                    |
| Subskill SKILL.md                                                             | Cross-module interface     | Consumer-found-by-tooling, cutover via docs                         |
| `$SKILL_DIR/scripts/scaffold.py` (embedded templates)                         | Module internals           | Free churn behind BDD/EDD                                           |
| Generated project files (`.releaserc.json`, `CHANGELOG.md`, `pyproject.toml`) | Projection (not authority) | Regenerate from scaffold, never hand-edit except `{{project_name}}` |

Authority: scaffold skill owns scaffolding decisions; project owns files. Writers propose via explicit `/scaffold` invocation. Projections are regenerated from source.

## Dispatch

Read the subskill that matches the projection you need. Use `Read` (not `Skill` tool — subskills hidden from discovery).

| Flavor   | Subskill                               | When to load                                                                                                       |
| -------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `git`    | `$SKILL_DIR/subskills/git/SKILL.md`    | Conventional commits, semantic-release, changelog, `.gitignore`, `AGENTS.md` patch — [git](subskills/git/SKILL.md) |
| `python` | `$SKILL_DIR/subskills/python/SKILL.md` | `uv` + `.python-version` + `pyproject.toml` wiring — [python](subskills/python/SKILL.md)                           |
| `rust`   | `$SKILL_DIR/subskills/rust/SKILL.md`   | `rust-toolchain.toml` + `cargo fmt/clippy/test` wiring — [rust](subskills/rust/SKILL.md)                           |
| `ci`     | `$SKILL_DIR/subskills/ci/SKILL.md`     | GitHub Actions verify+release + on-demand dispatch — [ci](subskills/ci/SKILL.md)                                   |

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
  "git_contract": { "complete": false, "stale": false },
  "python": { "present": true, "coverage": false, "threshold": null },
  "ci": { "present": false, "variant": null, "coverage": false },
  "verify_gates": { "formatter": true, "linter": true, "typecheck": true, "tests": true }
}
```

Full keys: `cwd`, `inferred_shape` (`greenfield|python|rust|node|polyglot`), `files` (20 entries), `git_contract`, `runtimes`, `python`/`rust`/`ci`/`changelog`/`verify_gates`. Human summary on `stderr`: `shape=… present: … missing: …`.

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

Selection rule: **preset when confident, ask only when ambiguous.** If `inferred_shape` is confident and `git_contract.complete` clear, prefill Dialog 1/4 and skip. Grill only leaves where detection is inconclusive (e.g. greenfield, polyglot variant, coverage threshold choice).

| Detected state                                                                               | Recommended combos (2–4, with generator)                                                                                                                                                                                                                                                                                                                        |
| -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Greenfield** (no runtime, no git contract)                                                 | 1. Python 80% + CI — `scaffold.py --flavor all --with-coverage --coverage-threshold 80` + `ci --ci-variant python --with-coverage` + `git` (reason: most common, minimal seam) · 2. Rust + CI — `rust --with-coverage` + `ci --ci-variant rust` (reason: alternative runtime) · 3. Node minimal — `git` + `ci --ci-variant node` (reason: no python/rust files) |
| **Existing Python, no scaffold** (`pyproject.toml` present, no `.releaserc.json`)            | 1. ✅ Retrofit Python 80% + CI — `python --with-coverage 80` + `ci --ci-variant python --with-coverage` + `git` (reason: preserve existing pyproject, add missing contract) · 2. Minimal — `git` only (reason: wire release without touching runtime) · 3. Add --dry-run preview first (reason: show diff before writes)                                        |
| **Existing Rust, no scaffold** (`Cargo.toml` present)                                        | 1. ✅ Retrofit Rust + CI — `rust` + `ci --ci-variant rust` + `git` (reason: mirror python pattern) · 2. With coverage — add `--with-coverage --coverage-threshold 80` (reason: opt-in llvm-cov)                                                                                                                                                                 |
| **Python scaffold stale** (has `.releaserc.json` but missing `changelog-check.yml` or hooks) | 1. ✅ Repair git contract — `git --dry-run` then `git` (reason: changelog guard stale, `--dry-run` shows drift) · 2. Add coverage if `python.coverage==false` — `python --with-coverage 80` (reason: coverage absent)                                                                                                                                           |
| **Scaffold complete, no coverage** (`git_contract.complete && !python.coverage`)             | 1. ✅ Add 80% coverage — `python --with-coverage 80` + `ci --ci-variant python --with-coverage` (reason: cheapest rigor bump) · 2. Add 90% strict (reason: high-rigor variant) · 3. Hold — keep as-is (reason: tests without gate is valid)                                                                                                                     |
| **Polyglot / .tool-versions**                                                                | 1. ✅ Matrix CI — `all --with-coverage 80` + `ci --matrix` note in `ci/SKILL.md` (reason: `polyglot==true`, needs `asdf install` sync) · 2. Single-variant CI — `ci --ci-variant python` (reason: cheapest, one verify job)                                                                                                                                     |
| **CI variant mismatch** (`Cargo.toml` + `ci.variant==node`)                                  | 1. ✅ Fix variant — `ci --ci-variant rust` (reason: runtime is rust but workflow is node) · 2. Matrix — `ci --matrix` (reason: if both runtimes present)                                                                                                                                                                                                        |

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
      description: 'Single-runtime Node 22 — semantic-release + npm audit; minimal seam'
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
3. Node (pnpm) — Single-runtime Node 22 — semantic-release + npm audit
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
      description: 'Enforces style without debate — ruff format / cargo fmt / prettier'
    - label: 'Linter'
      description: 'Catches bugs/idioms — ruff check / clippy -D warnings / eslint'
    - label: 'Type check'
      description: 'Proves contracts — basedpyright strict / tsc --noEmit / cargo check'
    - label: 'Tests'
      description: 'Proves behavior — pytest / cargo test / npm test; required for coverage'
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
4. Tests — pytest / cargo test / npm test
5. Other — Custom gate
```

> Branching: if Q1=Python, defaults map to ruff/basedpyright/pytest; if Rust, to fmt/clippy/test; if Node, to prettier/eslint/tsc/vitest — but user may skip any leaf; skipping does not remove the flavor file, only the gate step.

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
| Polyglot Python+Rust + 80% + Yes   | `uv run $SKILL_DIR/scripts/scaffold.py --flavor all --with-coverage --coverage-threshold 80` + `uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant python --with-coverage` and matrix note in `$SKILL_DIR/subskills/ci/SKILL.md`                                                                            |
| Any + Formatter skipped            | Generator still writes file (formatter config is deterministic); CI verify step for that gate is omitted by the caller — file remains byte-identical, gate is optional leaf                                                                                                                                             |

> Formatter/linter/type/test are always wired in the flavor file (one concept one location). Skipping a gate means not running it, not deleting its config — keeps the spine small. Coverage is the only leaf that changes file bytes (`pyproject.toml` `pytest-cov` + `[tool.coverage.*]`, Rust `llvm-cov` note, CI `*COVERAGE_YML`). All other leaves are verification choices, not artifact changes.

Omitted grilling (direct dispatch) defaults to: Tests=on, Coverage=off, CI=Yes, threshold 80 — so `/scaffold python` without grilling still gets the current byte-identical output.

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
```

- **Pure-deterministic** (no proofread): `.releaserc.json`, `.github/workflows/release.yml`, `commitlint.config.js`, `CHANGELOG.md`, `.gitignore` entries, `.python-version`, `rust-toolchain.toml`.
- **Mixed** (script writes skeleton + warns on stderr → proofread): `CONTRIBUTING.md` (`{{project_name}}` + Before PR line), `pyproject.toml`/`Cargo.toml` (name/description/edition; with `--with-coverage` also `fail_under`), `AGENTS.md` patch (keep 3 sections, verify pointer wording).

- `$SKILL_DIR/scripts/scaffold.py` — deterministic source of truth (tool owns bytes); preview with `uv run $SKILL_DIR/scripts/scaffold.py --flavor <git|python|rust|ci> --dry-run`; detect with `uv run $SKILL_DIR/scripts/scaffold.py --detect --cwd .` (JSON to stdout, summary to stderr)
- `$SKILL_DIR/scripts/verify.sh` — deterministic gate runner (`--dry-run` + `validate-deps` + `npm ls`/`cargo` checks)
