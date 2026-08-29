# Semantic Release — Configuration

Source: semantic-release **25.0.9** (scraped 2026-08-29) — <https://semantic-release.org/usage/configuration/>
Raw: `$SKILL_DIR/subskills/git/references/semantic-release-raw/003-configuration.md`
Lead: **configuration** — options, plugins, and release branches via config file, CLI arguments, or shareable configs. `.releaserc.json` is the scaffold's emitted form.

## Where config lives

- `.releaserc` file: `.yaml`/`.yml`/`.json`/`.js`/`.ts`/`.cjs`/`.mjs`
- `release.config.(js|ts|cjs|mjs)` exporting an object
- `release` key in `package.json` (config must be under `release` there; without the `release` property in a `.releaserc`/`release.config.**` file)

```json
{ "branches": ["main", "next"] }
```

CLI arguments override the config file; plugin options cannot be set via CLI.

## Options

| Option          | Type / Default / CLI                                                                                                                                                                        | Description                                                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `extends`       | `Array`/`String` · `-e, --extends`                                                                                                                                                          | Shareable configurations, imported in order; later ones take precedence (config file/CLI beat all).                                              |
| `branches`      | `Array`/`String`/`Object` · default: `['+([0-9])?(.{+([0-9]),x}).x', 'master', 'main', 'next', 'next-major', {name:'beta',prerelease:true}, {name:'alpha',prerelease:true}]` · `--branches` | Branches on which releases happen. Micromatch globs supported. Missing release branch → `ERELEASEBRANCHES`.                                      |
| `repositoryUrl` | `String` · default: `package.json` `repository` or git origin · `-r, --repository-url`                                                                                                      | Git repo URL; any valid git URL format.                                                                                                          |
| `tagFormat`     | `String` · default: `v${version}` · `-t, --tag-format`                                                                                                                                      | Tag name (Lodash template with `version`); must contain `version` exactly once and compile to a valid git ref.                                   |
| `plugins`       | `Array` · default: `['@semantic-release/commit-analyzer', '@semantic-release/release-notes-generator', '@semantic-release/npm', '@semantic-release/github']` · `-p, --plugins`              | Plugins run in series per release step; config by wrapping name + options in an array. Defined `plugins` **overrides**, not merges, the default. |
| `dryRun`        | `Boolean` · default: `false` in CI, `true` otherwise · `-d, --dry-run`                                                                                                                      | Preview the pending release. Skips `prepare`, `publish`, `addChannel`, `success`, `fail`; still verifies push permission.                        |
| `ci`            | `Boolean` · default: `true` · `--ci` / `--no-ci`                                                                                                                                            | `false` skips CI-environment verifications (local releases).                                                                                     |
| `debug`         | `Boolean` · default: `false` · `--debug` (CLI only; or `DEBUG=semantic-release:*`)                                                                                                          | Debug output.                                                                                                                                    |

## Git environment variables

| Variable              | Description                        | Default                 |
| --------------------- | ---------------------------------- | ----------------------- |
| `GIT_AUTHOR_NAME`     | Author name on the release tag     | `@semantic-release-bot` |
| `GIT_AUTHOR_EMAIL`    | Author email on the release tag    | bot email address       |
| `GIT_COMMITTER_NAME`  | Committer name on the release tag  | `@semantic-release-bot` |
| `GIT_COMMITTER_EMAIL` | Committer email on the release tag | bot email address       |

## Existing version tags

Releases are determined by Git tags. If a release existed before semantic-release setup, the last release commit must be in the release-branch history and tagged per `tagFormat` (default `vx.y.z`). `npm publish`-published histories already satisfy this. Repair: `git tag v1.1.0 <sha>` then `git push origin v1.1.0`.

> Scaffold note: `.releaserc.json` emits `branches: ["main"]` + `tagFormat` default + the plugin chain `commit-analyzer` → `release-notes-generator` (conventionalcommits preset) → `changelog` → `github` → `git`. Regenerate from `scaffold.py`, never hand-edit.
