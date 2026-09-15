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

Byte source is `$SKILL_DIR/templates/<flavor>/<target path>`: raw templates ship verbatim (`templates/git/.githooks/pre-push` → `.githooks/pre-push`, `templates/shared/CONTRIBUTING.*.md.j2` → `CONTRIBUTING.md`), while a `.j2` suffix marks a template Jinja renders through one `Environment` (`render_template()`; `StrictUndefined` so a typo fails loud, `trim_blocks`/`lstrip_blocks` so tag-only lines vanish, `keep_trailing_newline` because the trailing newline is part of the contract). `scaffold.py` fails loud when a template is missing — never a silent fallback to embedded bytes. Still in code: `build_pyproject` / `build_package_json` / `build_tsconfig` (computed, not static). Every run then canonicalizes every file the pinned `oxfmt` (`OXFMT_VERSION`) can reach at the single write seam — whichever flavor wrote it, so the grouping of invocations cannot change the bytes — templates stay as written instead of hand-mirroring the formatter's spacing, and the generated CI gate (`oxfmt --check .`) is green on the first push; the seam is also what makes `--dry-run` preview the bytes that land. `--no-format` (or `SCAFFOLD_NO_FORMAT=1`) skips the pass and needs no Node, at the cost of a red format gate. Preview with `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --dry-run`; `tests/scaffold/test_templates.py` pins the layout, registry coherence, raw template SHA-256 and every rendered cell, so a formatter or editor rewrite fails there before it ships.

```bash
uv run $SKILL_DIR/scripts/scaffold.py --flavor git --project-name <name>
uv run $SKILL_DIR/scripts/scaffold.py --flavor git --project-name <name> --dry-run  # diff without writing
```

Pure-deterministic (no proofread, byte-identical):

- `.releaserc.json` — conventional commits preset `conventionalcommits@8.0.0` (`writer@8.4.0`), `@semantic-release/npm` with `npmPublish: false` (publish disabled by default; enable per language — Node `private:false` + `NPM_TOKEN` to publish, Python/Rust omit `npm` and use language-native registry)
- `.github/workflows/release.yml` — Node/pnpm variant: `checkout@3d3c42...` (v7.0.1) + `pnpm/action-setup@ea17c6...` (v6.1.0) + `setup-node@820762...` (v7.0.0) + `setup-python@5fda3b...` (v7.0.0) via `SHA_TABLE` (single source) + `setup-node` `zizmor: ignore[cache-poisoning]`, `repository_dispatch` + `workflow_dispatch` only, `verify` (read) → `release` (write+id-token, `needs: verify`); `verify` runs `pnpm install` (flag-free — pnpm's CI default refuses a stale `pnpm-lock.yaml`) + `pnpm audit --audit-level high` + `pnpm run lint && pnpm run format && pnpm run typecheck && pnpm test` (Node 26); `release` runs `scripts/changelog-unreleased.py clear` then `pnpm exec semantic-release` (`HUSKY: "0"` so the changelog guard skips the release push) to hand off `## [Unreleased]`. Non-Node repos take this job from `--flavor ci --ci-variant python|rust` instead (see `$SKILL_DIR/subskills/ci-scaffolding/SKILL.md`)
- **No skill is vendored** — the GitHub surface is the `gh-router` skill itself (harness tree, discovered by pi from `~/.agents/skills/`), never a copy under the target repo's `skills/`. Scaffold ships no `skills/` directory: a copy of another skill is a second source of truth that drifts from the original, and `--update` neither refreshes nor deletes one it finds — `--detect` reports it as a decision (`git rm -r skills/gh-router`, or keep it as project content)
- `.github/workflows/changelog-check.yml` — on `pull_request` to `main` (required), `diff -q` vs `scripts/changelog-unreleased.py update`, `fail+comment` if stale — SHA pins from `SHA_TABLE` (`checkout v5`, `setup-python v6`, `github-script v8`)
- `.githooks/pre-push` (deterministic source) + `.husky/pre-push` (delegation `exec .githooks/pre-push "$@"`) — skips when `HUSKY=0` or `uv`/`python3` absent; on stale `## [Unreleased]` in the push range it `cp before + update + diff`, then auto-fixes (`git add` + `commit --amend --no-edit --no-verify`) and re-pushes in the background, aborting the current push with a retry message; with `PREPUSH_AUTOFIX=0` or a failed amend it restores the file and blocks with manual instructions (`uv run python scripts/changelog-unreleased.py update && git add && git commit -m 'chore: sync changelog unreleased section'` — hidden type required, a visible `feat`/`fix`/`docs` re-triggers the guard and loops forever) (both chmod 755; husky sets `core.hooksPath=.husky` so delegation keeps guard live)
- `scripts/changelog-unreleased.py` — manages `## [Unreleased]` (`update` stages notes from `git log <last-tag>..HEAD`, `clear` strips it before release)
- `commitlint.config.js` — `export default { extends: ['@commitlint/config-conventional'] }`
- `CHANGELOG.md` — initial `# Changelog` header + Keep-a-Changelog pointer + a `markdownlint-configure-file` pin of MD004 to `asterisk`. Both writers already emit `*` (`@semantic-release/changelog` inserts the preset's notes, `scripts/changelog-unreleased.py` emits `*`), and MD004's stock `consistent` keys off whichever bullet appears first — the pin is what stops a markdown touch from rewriting every generated line. The title must stay the **first line**: the plugin rewrites it in place only while the file starts with `changelogTitle`, so `.releaserc.json` names that title and the two halves are one contract (`tests/scaffold/test_changelog_title.py` runs the plugin twice to hold it — comments below the title are fine, above it they strand it). `--update` preserves it; a plain `--flavor git` run truncates versioned sections, so use `--without changelog-md` when refreshing an existing repo without `--update`
- `CHANGELOG.md` stays out of the formatters — `oxfmt` and prettier normalize bullets to `-`, which would flip the file back on every save: `templates/typescript/.oxfmtrc.json` ships `ignorePatterns: ["CHANGELOG.md"]`, and a repo wiring prettier adds the same entry to `.prettierignore`
- `.github/ISSUE_TEMPLATE/01-bug_report.yml` — YAML form (Summary → Environment → Repro → Expected/Actual → Impact, `required:true` on repro fields) + `02-feature_request.yml` — YAML form (Problem → Proposal → Alternatives → Context, `required:true` on problem/proposal) + `config.yml` (`blank_issues_enabled:false`, with the comment block showing where a repo's own `contact_links` go); ordered `01/02` for chooser. Every shipped line is project-neutral — the templates were first lifted out of another repo, and its issue links and internals must never ride along (`test_templates.py::test_shipped_bytes_name_no_foreign_project`)
- `.github/pull_request_template.md` — PR template (Summary + Impact/Risk \u00b7 What Changed \u00b7 Architecture (Mermaid, delete if N/A) \u00b7 Checklist) — auto-populated by GitHub; `CONTRIBUTING.md` `## Pull Requests` documents the four headings

> PR → watch → squash + release watch live as **gh-router skill scripts** (in the skill itself, never vendored into the target repo): `uv run $GH_ROUTER_DIR/subskills/pr-land/scripts/pr.sh --watch --merge` (create via `gh api pulls`, poll **every** check via `gh pr checks --json name,bucket` through `lib/checks.sh`, dump `gh run --log` on failure for model fix, refuse a merge that is not `clean`, then squash with the PR body as the commit body so the `Co-authored-by` trailer survives) and `uv run $GH_ROUTER_DIR/subskills/gh-release/scripts/release-watch.sh --watch` (dispatch `semantic-release` then poll `actions/runs release.yml`), where `$GH_ROUTER_DIR` is the skill directory pi discovers

Mixed (script writes skeleton + warns on stderr → model must proofread):

- `CONTRIBUTING.md` — `{{project_name}}` + `Before PR` toolchain line + `Reporting Issues` (Bug `01-bug_report.yml` / Feature `02-feature_request.yml`) + `Pull Requests` (Summary/Impact/Risk · What Changed · Architecture · Checklist via `.github/pull_request_template.md`); script warns: proofread name + lint commands
- `AGENTS.md` patch — appends `### Contribution` pointer + `Git hooks: git config core.hooksPath .githooks (or npm install with husky → .husky delegates)` , keeps existing 3 sections; script warns: verify pointer wording
- `.config/wt.toml` — if present, patches `[post-start] setup-hooks = "git config core.hooksPath .githooks"` (idempotent, `wt switch --create` auto-activates guard)

Byte view: `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --dry-run` (tool owns bytes). Pin check: `conventional-changelog-conventionalcommits@9` — the newest major that renders, because v10 requires `conventional-changelog-writer@9+` while `@semantic-release/release-notes-generator@14` still loads `8.4.0` (`npm ls conventional-changelog-writer` → `8.4.0`).

## Update — Tool Replaces, Model Decides

Updating an existing repo is one command. It replaces every generated file byte-identically, preserves what the project owns, and prints the leftover decisions:

```bash
uv run $SKILL_DIR/scripts/scaffold.py --update --cwd .              # implies --flavor git
uv run $SKILL_DIR/scripts/scaffold.py --update --flavor all --dry-run  # preview
uv run $SKILL_DIR/scripts/scaffold.py --update --flavor python --with-coverage  # language files too
uv run $SKILL_DIR/scripts/scaffold.py --check --cwd .                # verdict only: drift per file, exit 1 when not in sync
uv run $SKILL_DIR/scripts/scaffold.py --update --merge-mixed         # also insert missing CONTRIBUTING.md sections
```

Ownership is declared in `scaffold.py` (`PROJECT_OWNED`, `SOURCE_OWNED`, `FLAVOR_FOREIGN`) — the tool replaces, the model never guesses:

| Artifact                                                                                                                                                                                             | `--update` behaviour                                                         |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| `.releaserc.json`, `changelog-check.yml`, `.githooks/pre-push`, `.husky/pre-push`, `scripts/changelog-unreleased.py`, `commitlint.config.js`, `.github/ISSUE_TEMPLATE/*`, `pull_request_template.md` | **replaced** byte-identically                                                |
| `AGENTS.md`, `.gitignore`, `.config/wt.toml`                                                                                                                                                         | patched (append-only / dedup, never rewrites)                                |
| `CHANGELOG.md`, `CONTRIBUTING.md`, `pyproject.toml`, `Cargo.toml`, `package.json`                                                                                                                    | **preserved** (data / mixed / project manifest)                              |
| `src/index.ts`, `src/cli.ts`, `tests/index.test.ts`, `vitest.config.ts` (TS flavor)                                                                                                                  | **preserved** — hand-grown source; only a greenfield run writes the skeleton |
| `.github/workflows/release.yml`                                                                                                                                                                      | **preserved** in the git flavor — it is the `ci` flavor's projection         |

The printed `NEXT` block _is_ the remaining task. Work it in this order:

1. **`release.yml`** — the git flavor ships a Node/pnpm verify job. Re-run detection's variant: `--flavor ci --ci-variant python|rust|node`; confirm `verify` runs the repo's real gate (`.config/wt.toml [pre-merge].gate` is the authority for the same commands).
2. **`CONTRIBUTING.md`** — mixed file (project name + `## Before PR` toolchain line). The note names the template sections the file is **missing**; add them, or re-run with `--merge-mixed` to insert exactly those sections (existing lines are never rewritten). Merge prose from `templates/shared/CONTRIBUTING.{default,python,typescript}.md.j2`; never regenerate it from the git flavor (that writes the pnpm line into a uv/cargo repo).
3. **`CHANGELOG.md`** — data, not projection. Nothing to do; `@semantic-release/changelog` owns versioned sections.
4. **Manifests** (`pyproject.toml`, `Cargo.toml`, `package.json`) — regenerate only when the gate or deps changed, deliberately, with the language flavor + `--with-coverage`.
5. **Language-variant files** — `--only`/`--without`/`--components` select git components only; language flavors write their whole file set. To refresh one language file, re-run that flavor deliberately, or edit its template under `$SKILL_DIR/templates/` — raw templates are pinned by file hash, `.j2` templates by rendered-output hash (both in `tests/scaffold/test_templates.py`); re-pin only when the byte change is intended.

> [!warning] `--update` is not `--flavor git`
> A plain `--flavor git` run rewrites everything, including `CHANGELOG.md` (header only) and `release.yml` (Node variant). Existing repo → `--update`. Greenfield repo → plain flavor.

## GDD Wiring

- **BDD contract:** `Given` conventional commit `feat`/`fix`, `When` `repository_dispatch` `semantic-release` (or `workflow_dispatch`) is sent, `Then` `semantic-release` on `main` cuts `v1.3.0` with `### Features`/`### Bug Fixes` and updates `CHANGELOG.md`. Contract is `CONTRIBUTING.md` + `.releaserc.json`.
- **EDD gate:** `commitlint` + `pnpm run lint/typecheck/test` are deterministic; tag push fails if commit not conventional. Env truth is `pnpm ls` + `git tag -l`.
- **Semantic vs deterministic split:** `feat`/`fix` intent → model/human; `commit-analyzer` bump + `release-notes-generator` → tool.

## Steps — Tool Owns Determinism

Run the generator (tool owns bytes). Model proofreads only the mixed warnings on stderr.

1. Generate: `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --project-name <name>` (or `--dry-run` to preview diff) — handles `--cwd` and `--project-name` inference via `git rev-parse`.
2. Install wiring: `npm i -D conventional-changelog-conventionalcommits@9 @semantic-release/changelog @semantic-release/git @semantic-release/github semantic-release @commitlint/cli @commitlint/config-conventional` + wire `husky` pre-commit (`npx commitlint --from=origin/main --to=HEAD`). The script does not install deps — it owns file bytes only.
3. Proofread mixed warnings (stderr): `CONTRIBUTING.md` project name + Before PR line; `AGENTS.md` 3-section preservation. Do not hand-edit deterministic files except `{{project_name}}` (already handled by script).
4. Verify deterministic gate: `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --dry-run` shows `unchanged`; `uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py check` + `npm ls conventional-changelog-writer` shows `8.4.0`

> [!tip] Verification — run before every push/release
>
> - `pnpm run lint` / `pnpm run typecheck` / `pnpm test` — if any fails → `BLOCKED`
> - `custom/no-comments` allows `SAFETY:` `WHY:` `Invariant:` `See ADR-` `via https://` `TODO(#\d+):` `HACK:` + Gherkin (`Given|When|Then`); `noUncheckedIndexedAccess` needs `(l: string)` in tests — see ADR-0014 (harness AI engineering, `files:off` is shrink-only, `edit-pipeline` hard-code deleted, harness owns regex)

## Notes

- On-demand via `repository_dispatch` + `workflow_dispatch` is the deterministic default — no `push: tags` or `push: [main]` auto-release. Tag is created by `semantic-release` on dispatch.
- `CHANGELOG.md` `## [Unreleased]` guarded by `pre-push` hook (`warn+block`, `uv run python scripts/changelog-unreleased.py update` via `.githooks/pre-push` + `.husky/pre-push` delegation) and `changelog-check.yml` (`pull_request` required); `release.yml` (`release` job) runs `scripts/changelog-unreleased.py clear` then `semantic-release` owns versioned sections (`@semantic-release/changelog` + `@semantic-release/npm` (`npmPublish: false` by default) + `@semantic-release/git`). Do not hand-edit versioned sections. Commit the sync as a hidden type (e.g. `chore: sync changelog unreleased section`) — a visible type (`docs:` etc.) re-triggers the guard and loops forever. Bullets are `*`; the file's MD004 pin rewrites any other style on the next markdown touch.
- `wt` worktrees: if `.config/wt.toml` exists, `scaffold` ensures `[post-start] setup-hooks = "git config core.hooksPath .githooks"` so `wt switch --create` clones get live pre-push without manual `git config`.
- `@semantic-release/git` bumps `package.json` + `CHANGELOG.md` + commits + tags atomically; no manual `git tag` or manifest bump.
- `.releaserc.json` release assets follow the repo, not the flavor: `pnpm-lock.yaml` when the repo declares pnpm (`pnpm-lock.yaml`, `pnpm-workspace.yaml` or `packageManager: pnpm`), else the template's `package-lock.json`. The swap is resolved before the write, so `--check` stays clean on a pnpm repo.
- `--check` is the CI-shaped projection of `--update` (`--update --dry-run --summary`, exit 1 on drift) and `--self-check` validates what a run wrote (syntax, parse, exec bit, `scripts/…` references) — it runs automatically after a real write, because a generated workflow or hook that does not parse is a defect worth failing on.
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

When helping file an issue, infer intent then use the matching YAML form (`.github/ISSUE_TEMPLATE/01-bug_report.yml` for `bug`, `02-feature_request.yml` for `feat`), then `gh issue create --template 01-bug_report.yml` / `--template 02-feature_request.yml`. The model must ask for any missing `body` required field of that form (bug: Summary/Environment/Repro/Expected/Actual required; feature: Problem/Proposal required) and render in form order. Prefer text over screenshots for code defects, and paste-complete input over a description of it. Blank issues are disabled via `config.yml`; Q&A goes to Discussions.
Git flavor is spine — always present. Grilling `Project Shape` selects sibling flavors (python/rust/polyglot) to scaffold alongside git. Coverage/CI leaves affect those flavors, not `.releaserc.json` itself. Direct `uv run $SKILL_DIR/scripts/scaffold.py --flavor git` omits coverage (git has no coverage gate).

## Arguments

- `--project-name <name>` — replaces `{{project_name}}` (inferred from `git rev-parse` if omitted)
- `--cwd <path>` — target repo root (default `.`)
- `--dry-run` — print diff without writing + emit mixed warnings on stderr
- `--retrofit` behavior is implicit: `.gitignore` dedup + `AGENTS.md` append-only (preserves manual sections)
- `--only <a,b>` / `--components <a,b>` — write just those components keyed by `GIT_COMPONENTS` (`releaserc`, `release-yml`, `changelog-check`, `pre-push`, `changelog-script`, `commitlint`, `changelog-md`, `issue-templates`, `pr-template`, `contributing`, `agents`, `gitignore`; aliases `hooks`, `changelog`, `issues`, `pull-request`)
- `--without <a,b>` — inverse of `--only`; the recorded way to retrofit without clobbering project-owned files (e.g. `--without changelog-md,release-yml,contributing`)
- `--detect` — read-only state detection (JSON to stdout, summary to stderr); never writes
