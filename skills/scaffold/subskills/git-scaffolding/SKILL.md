---
name: git-scaffolding
description: >-
  Deterministic Git scaffolding — conventional commits, semantic-release, changelog, and branch hygiene. Use when wiring release flow, commit linting, or retrofitting Git artifacts.
metadata:
  managed-by: scaffold
---

# Git Scaffold

Migrated from `~/.pi/agent/prompts/scaffold-git.md`. Explicit human authority (`/scaffold git-scaffolding`) to create or retrofit Git scaffolding. Goal (GDD): every project gets the same deterministic artifacts so `feat`/`fix` intent maps to one shared contract (BDD) and env truth is the gate (EDD).

## Deterministic Artifacts — Tool Owns Bytes

Byte source is `$SKILL_DIR/templates/<flavor>/<target path>` (`templates/git/.githooks/pre-push` → `.githooks/pre-push`, `templates/shared/CONTRIBUTING.*.md` for the language dimension); `scaffold.py` loads them with `load_template()` and fails loud when the directory is missing — never a silent fallback to embedded bytes. Still in code: `build_pyproject` / `build_package_json` / `build_tsconfig` (computed), the CI variants (next extraction), `{{project_name}}`/threshold substitution. Preview with `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --dry-run`; `tests/scaffold/test_templates.py` pins layout, registry coherence and template SHA-256 so a formatter or editor rewrite fails there before it ships.

```bash
uv run $SKILL_DIR/scripts/scaffold.py --flavor git --project-name <name>
uv run $SKILL_DIR/scripts/scaffold.py --flavor git --project-name <name> --dry-run  # diff without writing
```

Pure-deterministic (no proofread, byte-identical):

- `.releaserc.json` — conventional commits preset `conventionalcommits@8.0.0` (`writer@8.4.0`), `@semantic-release/npm` with `npmPublish: false` (publish disabled by default; enable per language — Node `private:false` + `NPM_TOKEN` to publish, Python/Rust omit `npm` and use language-native registry)
- `.github/workflows/release.yml` — Node/pnpm variant: `pnpm/action-setup@b906af...` (v4) + `setup-node@a0853c...` (v5) + `setup-python@e797f8...` (v6) via `SHA_TABLE` (single source) + `setup-node` `zizmor: ignore[cache-poisoning]`, `repository_dispatch` + `workflow_dispatch` only, `verify` (read) → `release` (write+id-token, `needs: verify`); `verify` runs `pnpm install --no-frozen-lockfile` + `pnpm audit --audit-level high` + `pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test` (Node 24); `release` runs `scripts/changelog-unreleased.py clear` then `pnpm exec semantic-release` (`HUSKY: "0"` so the changelog guard skips the release push) to hand off `## [Unreleased]`. Non-Node repos take this job from `--flavor ci --ci-variant python|rust` instead (see `$SKILL_DIR/subskills/ci-scaffolding/SKILL.md`)
- `skills/gh-router` — router `gh-router` (`gh-release` + `pr-land` + `pr-enhance` subskills, `GITHUB_TOKEN=$(gh auth token)` dispatch, `tmp/` ephemeral) — GitHub surface is `gh-router`, not standalone `pr-enhance`; the three `SKILL.md` + their `scripts/` are copied from the harness when present, else from embedded stubs (a target repo without the harness gets the router + stubs, no `pr.sh`)
- `.github/workflows/changelog-check.yml` — on `pull_request` to `main` (required), `diff -q` vs `scripts/changelog-unreleased.py update`, `fail+comment` if stale — SHA pins from `SHA_TABLE` (`checkout v5`, `setup-python v6`, `github-script v8`)
- `.githooks/pre-push` (deterministic source) + `.husky/pre-push` (delegation `exec .githooks/pre-push "$@"`) — skips when `HUSKY=0` or `uv`/`python3` absent; on stale `## [Unreleased]` in the push range it `cp before + update + diff`, then auto-fixes (`git add` + `commit --amend --no-edit --no-verify`) and re-pushes in the background, aborting the current push with a retry message; with `PREPUSH_AUTOFIX=0` or a failed amend it restores the file and blocks with manual instructions (`uv run python scripts/changelog-unreleased.py update && git add && git commit -m 'chore: sync changelog unreleased section'` — hidden type required, a visible `feat`/`fix`/`docs` re-triggers the guard and loops forever) (both chmod 755; husky sets `core.hooksPath=.husky` so delegation keeps guard live)
- `scripts/changelog-unreleased.py` — manages `## [Unreleased]` (`update` stages notes from `git log <last-tag>..HEAD`, `clear` strips it before release)
- `commitlint.config.js` — `export default { extends: ['@commitlint/config-conventional'] }`
- `CHANGELOG.md` — initial `# Changelog` header + Keep-a-Changelog pointer. `--update` preserves it; a plain `--flavor git` run truncates versioned sections, so use `--without changelog-md` when refreshing an existing repo without `--update`
- `.github/ISSUE_TEMPLATE/01-bug_report.yml` — YAML form (Summary \u2192 Environment \u2192 Repro \u2192 Expected/Actual \u2192 Impact, exemplar [#38](https://github.com/Rianico/dsh-better-edit/issues/38), `required:true` on repro fields + `render:shell`) + `02-feature_request.yml` — YAML form (Problem \u2192 Proposal \u2192 Alternatives \u2192 Context, `required:true` on problem/proposal) + `config.yml` (`blank_issues_enabled:false`, exemplar + Discussions contact_links); ordered `01/02` for chooser
- `.github/pull_request_template.md` — PR template (Summary + Impact/Risk \u00b7 What Changed \u00b7 Architecture (Mermaid, delete if N/A) \u00b7 Checklist) — auto-populated by GitHub; `CONTRIBUTING.md` `## Pull Requests` documents the four headings

> PR → watch → squash + release watch live as **gh-router skill scripts** (not scaffold repo files): `uv run $GH_ROUTER_DIR/subskills/pr-land/scripts/pr.sh --watch --merge` (create via `gh api pulls`, poll `check-runs`/`gh pr checks`, dump `gh run --log` on failure for model fix, then squash) and `uv run $GH_ROUTER_DIR/subskills/gh-release/scripts/release-watch.sh --watch` (dispatch `semantic-release` then poll `actions/runs release.yml`)

Mixed (script writes skeleton + warns on stderr → model must proofread):

- `CONTRIBUTING.md` — `{{project_name}}` + `Before PR` toolchain line + `Reporting Issues` matrix (Bug `01-bug_report.yml` / Feature `02-feature_request.yml`, links #38) + `Pull Requests` (Summary/Impact/Risk \u00b7 What Changed \u00b7 Architecture \u00b7 Checklist via `.github/pull_request_template.md`); script warns: proofread name + lint commands
- `AGENTS.md` patch — appends `### Contribution` pointer + `Git hooks: git config core.hooksPath .githooks (or npm install with husky → .husky delegates)` , keeps existing 3 sections; script warns: verify pointer wording
- `.config/wt.toml` — if present, patches `[post-start] setup-hooks = "git config core.hooksPath .githooks"` (idempotent, `wt switch --create` auto-activates guard)

Byte view: `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --dry-run` (tool owns bytes). Pin check: `conventional-changelog-conventionalcommits@8.0.0` via `npm ls conventional-changelog-writer` → `8.4.0`.

## Update — Tool Replaces, Model Decides

Updating an existing repo is one command. It replaces every generated file byte-identically, preserves what the project owns, and prints the leftover decisions:

```bash
uv run $SKILL_DIR/scripts/scaffold.py --update --cwd .              # implies --flavor git
uv run $SKILL_DIR/scripts/scaffold.py --update --flavor all --dry-run  # preview
uv run $SKILL_DIR/scripts/scaffold.py --update --flavor python --with-coverage  # language files too
```

Ownership is declared in `scaffold.py` (`PROJECT_OWNED`, `FLAVOR_FOREIGN`) — the tool replaces, the model never guesses:

| Artifact                                                                                                                                                                                                                    | `--update` behaviour                                                 |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `.releaserc.json`, `changelog-check.yml`, `.githooks/pre-push`, `.husky/pre-push`, `scripts/changelog-unreleased.py`, `commitlint.config.js`, `.github/ISSUE_TEMPLATE/*`, `pull_request_template.md`, `skills/gh-router/**` | **replaced** byte-identically                                        |
| `AGENTS.md`, `.gitignore`, `.config/wt.toml`                                                                                                                                                                                | patched (append-only / dedup, never rewrites)                        |
| `CHANGELOG.md`, `CONTRIBUTING.md`, `pyproject.toml`, `Cargo.toml`, `package.json`                                                                                                                                           | **preserved** (data / mixed / project manifest)                      |
| `.github/workflows/release.yml`                                                                                                                                                                                             | **preserved** in the git flavor — it is the `ci` flavor's projection |

The printed `NEXT` block _is_ the remaining task. Work it in this order:

1. **`release.yml`** — the git flavor ships a Node/pnpm verify job. Re-run detection's variant: `--flavor ci --ci-variant python|rust|node`; confirm `verify` runs the repo's real gate (`.config/wt.toml [pre-merge].gate` is the authority for the same commands).
2. **`CONTRIBUTING.md`** — mixed file (project name + `## Before PR` toolchain line). Hand-merge the toolchain line from `templates/shared/CONTRIBUTING.{default,python,typescript}.md`; never regenerate it from the git flavor (that writes the pnpm line into a uv/cargo repo).
3. **`CHANGELOG.md`** — data, not projection. Nothing to do; `@semantic-release/changelog` owns versioned sections.
4. **Manifests** (`pyproject.toml`, `Cargo.toml`, `package.json`) — regenerate only when the gate or deps changed, deliberately, with the language flavor + `--with-coverage`.
5. **Language-variant files** — `--only`/`--without`/`--components` select git components only; language flavors write their whole file set. To refresh one language file, either re-run that flavor deliberately or edit its file under `$SKILL_DIR/templates/` (then re-pin the SHA-256 in `tests/scaffold/test_templates.py`).

> [!warning] `--update` is not `--flavor git`
> A plain `--flavor git` run rewrites everything, including `CHANGELOG.md` (header only) and `release.yml` (Node variant). Existing repo → `--update`. Greenfield repo → plain flavor.

## GDD Wiring

- **BDD contract:** `Given` conventional commit `feat`/`fix`, `When` `repository_dispatch` `semantic-release` (or `workflow_dispatch`) is sent, `Then` `semantic-release` on `main` cuts `v1.3.0` with `### Features`/`### Bug Fixes` and updates `CHANGELOG.md`. Contract is `CONTRIBUTING.md` + `.releaserc.json`.
- **EDD gate:** `commitlint` + `pnpm run lint/typecheck/test` are deterministic; tag push fails if commit not conventional. Env truth is `pnpm ls` + `git tag -l`.
- **Semantic vs deterministic split:** `feat`/`fix` intent → model/human; `commit-analyzer` bump + `release-notes-generator` → tool.

## Steps — Tool Owns Determinism

Run the generator (tool owns bytes). Model proofreads only the mixed warnings on stderr.

1. Generate: `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --project-name <name>` (or `--dry-run` to preview diff) — handles `--cwd` and `--project-name` inference via `git rev-parse`.
2. Install wiring: `npm i -D conventional-changelog-conventionalcommits@8.0.0 @semantic-release/changelog @semantic-release/git @semantic-release/github semantic-release @commitlint/cli @commitlint/config-conventional` + wire `husky` pre-commit (`npx commitlint --from=origin/main --to=HEAD`). The script does not install deps — it owns file bytes only.
3. Proofread mixed warnings (stderr): `CONTRIBUTING.md` project name + Before PR line; `AGENTS.md` 3-section preservation. Do not hand-edit deterministic files except `{{project_name}}` (already handled by script).
4. Verify deterministic gate: `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --dry-run` shows `unchanged`; `uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py check` + `npm ls conventional-changelog-writer` shows `8.4.0`

> [!tip] Verification — run before every push/release
>
> - `pnpm run lint` / `pnpm run typecheck` / `pnpm test` — if any fails → `BLOCKED`
> - `custom/no-comments` allows `SAFETY:` `WHY:` `Invariant:` `See ADR-` `via https://` `TODO(#\d+):` `HACK:` + Gherkin (`Given|When|Then`); `noUncheckedIndexedAccess` needs `(l: string)` in tests — see ADR-0014 (harness AI engineering, `files:off` is shrink-only, `edit-pipeline` hard-code deleted, harness owns regex)

## Notes

- On-demand via `repository_dispatch` + `workflow_dispatch` is the deterministic default — no `push: tags` or `push: [main]` auto-release. Tag is created by `semantic-release` on dispatch.
- `CHANGELOG.md` `## [Unreleased]` guarded by `pre-push` hook (`warn+block`, `uv run python scripts/changelog-unreleased.py update` via `.githooks/pre-push` + `.husky/pre-push` delegation) and `changelog-check.yml` (`pull_request` required); `release.yml` (`release` job) runs `scripts/changelog-unreleased.py clear` then `semantic-release` owns versioned sections (`@semantic-release/changelog` + `@semantic-release/npm` (`npmPublish: false` by default) + `@semantic-release/git`). Do not hand-edit versioned sections. Commit the sync as a hidden type (e.g. `chore: sync changelog unreleased section`) — a visible type (`docs:` etc.) re-triggers the guard and loops forever.
- `wt` worktrees: if `.config/wt.toml` exists, `scaffold` ensures `[post-start] setup-hooks = "git config core.hooksPath .githooks"` so `wt switch --create` clones get live pre-push without manual `git config`.
- `@semantic-release/git` bumps `package.json` + `CHANGELOG.md` + commits + tags atomically; no manual `git tag` or manifest bump.
- For CI workflow detail and `zizmor: ignore[cache-poisoning]` justification see `$SKILL_DIR/subskills/ci-scaffolding/SKILL.md`.

## References

Reference index (all under `references/`, raw scrape in `references/semantic-release-raw/`):

| File                                                           | Covers                                                                              | Load when                                                         |
| -------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| [semantic-release](references/semantic-release.md)             | Intro, getting-started, commit → release-type mapping, requirements                 | Explaining the release contract or the `why` of `.releaserc.json` |
| [configuration](references/configuration.md)                   | All options, git env vars, existing-tag repair                                      | Answering config questions or changing `.releaserc.json` shape    |
| [release-steps](references/release-steps.md)                   | Nine release steps, lifecycle hooks, plugin roles/order                             | Tracing what happens during a release run                         |
| [workflow-configuration](references/workflow-configuration.md) | Branch types/properties, supported models, channel/maintenance/pre-release recipes  | Branch hygiene, multi-channel or pre-release setups               |
| [ci-configuration](references/ci-configuration.md)             | CI requirements, auth tokens, GitHub Actions recipe, npx running, Node/Git versions | Verifying CI wiring or release.yml shape                          |

## Grilling

## Reporting Issues — model/user prompt

When helping file an issue, infer intent then use the matching YAML form (`.github/ISSUE_TEMPLATE/01-bug_report.yml` for `bug`, `02-feature_request.yml` for `feat`): `gh issue view 38 --json title,body --repo Rianico/dsh-better-edit` as style ref for bugs, then `gh issue create --template 01-bug_report.yml` / `--template 02-feature_request.yml`. The model must ask for any missing `body` required field of that form (bug: Summary/Environment/Repro/Expected/Actual required; feature: Problem/Proposal required) and render in form order. Prefer text over screenshots for code defects. Blank issues are disabled via `config.yml`; Q&A goes to Discussions.
Git flavor is spine — always present. Grilling `Project Shape` selects sibling flavors (python/rust/polyglot) to scaffold alongside git. Coverage/CI leaves affect those flavors, not `.releaserc.json` itself. Direct `uv run $SKILL_DIR/scripts/scaffold.py --flavor git` omits coverage (git has no coverage gate).

## Arguments

- `--project-name <name>` — replaces `{{project_name}}` (inferred from `git rev-parse` if omitted)
- `--cwd <path>` — target repo root (default `.`)
- `--dry-run` — print diff without writing + emit mixed warnings on stderr
- `--retrofit` behavior is implicit: `.gitignore` dedup + `AGENTS.md` append-only (preserves manual sections)
- `--only <a,b>` / `--components <a,b>` — write just those components keyed by `GIT_COMPONENTS` (`releaserc`, `release-yml`, `changelog-check`, `pre-push`, `changelog-script`, `commitlint`, `changelog-md`, `issue-templates`, `pr-template`, `contributing`, `agents`, `gh-router`, `gitignore`; aliases `hooks`, `changelog`, `issues`, `pull-request`)
- `--without <a,b>` — inverse of `--only`; the recorded way to retrofit without clobbering project-owned files (e.g. `--without changelog-md,release-yml,contributing`)
- `--detect` — read-only state detection (JSON to stdout, summary to stderr); never writes
