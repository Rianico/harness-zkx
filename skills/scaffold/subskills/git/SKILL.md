---
name: git
description: >-
  Deterministic Git scaffolding — conventional commits, semantic-release, changelog, and branch hygiene. Use when wiring release flow, commit linting, or retrofitting Git artifacts. TRIGGER: git scaffold, semantic-release, conventional commits, commitlint
metadata:
  managed-by: scaffold
---

# Git Scaffold

Migrated from `~/.pi/agent/prompts/scaffold-git.md`. Explicit human authority (`/scaffold git`) to create or retrofit Git scaffolding. Goal (GDD): every project gets the same deterministic artifacts so `feat`/`fix` intent maps to one shared contract (BDD) and env truth is the gate (EDD).

## Deterministic Artifacts — Tool Owns Bytes

Source of truth is `$SKILL_DIR/scripts/scaffold.py` (embedded `RELEASERC_JSON`, `RELEASE_YML`, etc.) — run `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --dry-run` to preview byte-identical files.

```bash
uv run $SKILL_DIR/scripts/scaffold.py --flavor git --project-name <name>
uv run $SKILL_DIR/scripts/scaffold.py --flavor git --project-name <name> --dry-run  # diff without writing
```

Pure-deterministic (no proofread, byte-identical):

- `.releaserc.json` — conventional commits preset `conventionalcommits@8.0.0` (`writer@8.4.0`), `[skip ci]` message
- `.github/workflows/release.yml` — pinned `actions/checkout@11d596...` + `setup-node@49933...` (v4), `repository_dispatch` + `workflow_dispatch` only, `verify` (read) → `release` (write+id-token, `needs: verify`); `release` job runs `scripts/changelog-unreleased.py clear` before `npx semantic-release` to hand off `## [Unreleased]`
- `.github/workflows/changelog-check.yml` — on `pull_request` to `main` (required), `diff -q` vs `scripts/changelog-unreleased.py update`, `fail+comment` if stale
- `.githooks/pre-push` — `warn+block`, `cp before + update + diff`, hint `uv run python scripts/changelog-unreleased.py update && git add && git commit --amend`
- `scripts/changelog-unreleased.py` — manages `## [Unreleased]` (`update` stages notes from `git log <last-tag>..HEAD`, `clear` strips it before release)
- `commitlint.config.js` — `export default { extends: ['@commitlint/config-conventional'] }`
- `CHANGELOG.md` — initial `# Changelog` header

Mixed (script writes skeleton + warns on stderr → model must proofread):

- `CONTRIBUTING.md` — `{{project_name}}` + `Before PR` toolchain line (`npm run lint && npm run typecheck && npm test`); script warns: proofread name + lint commands
- `AGENTS.md` patch — appends `### Contribution` pointer, keeps existing 3 sections; script warns: verify pointer wording

Byte view: `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --dry-run` (tool owns bytes). Pin check: `conventional-changelog-conventionalcommits@8.0.0` via `npm ls conventional-changelog-writer` → `8.4.0`.

## GDD Wiring

- **BDD contract:** `Given` conventional commit `feat`/`fix`, `When` `repository_dispatch` `semantic-release` (or `workflow_dispatch`) is sent, `Then` `semantic-release` on `main` cuts `v1.3.0` with `### Features`/`### Bug Fixes` and updates `CHANGELOG.md`. Contract is `CONTRIBUTING.md` + `.releaserc.json`.
- **EDD gate:** `commitlint` + `npm run lint/typecheck/test` are deterministic; tag push fails if commit not conventional. Env truth is `npm ls` + `git tag -l`.
- **Semantic vs deterministic split:** `feat`/`fix` intent → model/human; `commit-analyzer` bump + `release-notes-generator` → tool.

## Steps — Tool Owns Determinism

Run the generator (tool owns bytes). Model proofreads only the mixed warnings on stderr.

1. Generate: `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --project-name <name>` (or `--dry-run` to preview diff) — handles `--cwd` and `--project-name` inference via `git rev-parse`.
2. Install wiring: `npm i -D conventional-changelog-conventionalcommits@8.0.0 @semantic-release/changelog @semantic-release/git @semantic-release/github semantic-release @commitlint/cli @commitlint/config-conventional` + wire `husky` pre-commit (`npx commitlint --from=origin/main --to=HEAD`). The script does not install deps — it owns file bytes only.
3. Proofread mixed warnings (stderr): `CONTRIBUTING.md` project name + Before PR line; `AGENTS.md` 3-section preservation. Do not hand-edit deterministic files except `{{project_name}}` (already handled by script).
4. Verify deterministic gate: `uv run $SKILL_DIR/scripts/scaffold.py --flavor git --dry-run` shows `unchanged`; `uv run $SKILL_DIR/subskills/skill-authoring/scripts/validate-deps.py check` + `npm ls conventional-changelog-writer` shows `8.4.0`

> [!tip] Verification — run before every push/release
>
> - `npm run lint` / `npm run typecheck` / `npm test` — if any fails → `BLOCKED`
> - `custom/no-comments` allows only `SAFETY:` + Gherkin; `noUncheckedIndexedAccess` needs `(l: string)` in tests

## Notes

- On-demand via `repository_dispatch` + `workflow_dispatch` is the deterministic default — no `push: tags` or `push: [main]` auto-release. Tag is created by `semantic-release` on dispatch.
- `CHANGELOG.md` `## [Unreleased]` guarded by `pre-push` hook (`warn+block`, `uv run python scripts/changelog-unreleased.py update`) and `changelog-check.yml` (`pull_request` required); `release.yml` (`release` job) runs `scripts/changelog-unreleased.py clear` then `semantic-release` owns versioned sections (`@semantic-release/changelog` + `@semantic-release/git` with `[skip ci]`). Do not hand-edit versioned sections.
- `@semantic-release/git` bumps `package.json` + `CHANGELOG.md` + commits + tags atomically; no manual `git tag` or manifest bump.
- For CI workflow detail and `zizmor: ignore[cache-poisoning]` justification see `$SKILL_DIR/subskills/ci/SKILL.md`.

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

Git flavor is spine — always present. Grilling `Project Shape` selects sibling flavors (python/rust/polyglot) to scaffold alongside git. Coverage/CI leaves affect those flavors, not `.releaserc.json` itself. Direct `uv run $SKILL_DIR/scripts/scaffold.py --flavor git` omits coverage (git has no coverage gate).

## Arguments

- `--project-name <name>` — replaces `{{project_name}}` (inferred from `git rev-parse` if omitted)
- `--cwd <path>` — target repo root (default `.`)
- `--dry-run` — print diff without writing + emit mixed warnings on stderr
- `--retrofit` behavior is implicit: `.gitignore` dedup + `AGENTS.md` append-only (preserves manual sections)
