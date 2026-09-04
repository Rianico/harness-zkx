# Semantic Release — Release Steps & Plugins

Source: semantic-release **25.0.9** (scraped 2026-08-29) — <https://semantic-release.org/foundation/release-steps/> · <https://semantic-release.org/foundation/plugins/> · <https://semantic-release.org/foundation/how-it-works/>
Raw: `$SKILL_DIR/subskills/git-scaffolding/references/semantic-release-raw/006-how-it-works.md` · `007-release-steps.md` · `008-plugins.md`
Lead: **release steps** — the fixed-order phases of one `semantic-release` run; plugins bind lifecycle hooks onto them.

## The core model

semantic-release answers three questions each run: should a release happen, what version, and where/how to publish. It compares commits since the last Git tag on a configured release branch and derives impact from commit semantics (default: Angular/Conventional Commits):

- `fix` → patch release
- `feat` → minor release
- `BREAKING CHANGE` footer → major release
- no recognized type since last release → no release

Inputs: commit history, branch configuration, plugin pipeline + options, CI credentials. Outputs: next version, release notes, git tags, published artifacts/channels.

## Step sequence (fixed order)

| Release Step           | Lifecycle Hook(s)  | Purpose                                                    |
| ---------------------- | ------------------ | ---------------------------------------------------------- |
| Verify Conditions      | `verifyConditions` | Confirm config + credentials are valid.                    |
| Get Last Release       | None (core)        | Find the most recent release via Git tags and history.     |
| Analyze Commits        | `analyzeCommits`   | **Decision point**: whether to release and which type.     |
| Verify Release         | `verifyRelease`    | Validate computed release metadata before publishing.      |
| Generate Notes         | `generateNotes`    | Build release notes for the included commits.              |
| Create Git Tag         | None (core)        | Tag the release version.                                   |
| Add Channel (optional) | `addChannel`       | Associate release with a distribution channel when needed. |
| Prepare                | `prepare`          | Pre-publish updates (e.g. bump files, commit).             |
| Publish                | `publish`          | Publish artifacts to destinations/channels.                |
| Notify                 | `success`, `fail`  | Report success/failure via integrations.                   |

Order matters: a failure in an early step blocks later steps. Some steps are core-only (`Get Last Release`, `Create Git Tag`); `Add Channel` runs only when channel management applies.

## Plugins

Plugins extend release steps via lifecycle methods. Core owns the lifecycle; hooks are exposed for selected steps. Multiple plugins on one hook run in plugin-declaration order.

| Lifecycle Hook     | Related Step      | Required | Notes                                                                                                                     |
| ------------------ | ----------------- | -------- | ------------------------------------------------------------------------------------------------------------------------- |
| `verifyConditions` | Verify Conditions | No       | Config + token validity.                                                                                                  |
| `analyzeCommits`   | Analyze Commits   | **Yes**  | Returns `major`/`minor`/`patch`; highest type wins across plugins. Fallback default: `@semantic-release/commit-analyzer`. |
| `verifyRelease`    | Verify Release    | No       | Validate version/type/distribution tag.                                                                                   |
| `generateNotes`    | Generate Notes    | No       | Concatenated across plugins.                                                                                              |
| `prepare`          | Prepare           | No       | e.g. bump `package.json`, `CHANGELOG.md`, commit.                                                                         |
| `publish`          | Publish           | No       | Publish the release.                                                                                                      |
| `addChannel`       | Add Channel       | No       | e.g. npm dist-tag assignment.                                                                                             |
| `success` / `fail` | Notify            | No       | Post-release / failure notifications.                                                                                     |

### Default vs. additional plugins

Defaults (bundled, in execution order, do not install separately): `@semantic-release/commit-analyzer`, `@semantic-release/release-notes-generator`, `@semantic-release/npm`, `@semantic-release/github`. Additional plugins (`@semantic-release/git`, `@semantic-release/changelog`, …) are passed via `npx --package` or installed + declared in `plugins`.

### Declaration and order

`plugins` **overrides** the default list (no merge). Per release step, implementing plugins execute in declaration order. Per-plugin options via `["name", {options}]`; root-level options go to all plugins.

> Scaffold note: `.releaserc.json` declares `commit-analyzer` → `release-notes-generator` (with `conventionalcommits` preset types table) → `changelog` → `github` → `git`. `@semantic-release/git` covers Create-tag/Prepare (bump `package.json` + `CHANGELOG.md`, commit with `[skip ci]` message). Regenerate from `scaffold.py`.
