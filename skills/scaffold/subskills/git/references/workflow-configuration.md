# Semantic Release — Workflow Configuration & Recipes

Source: semantic-release **25.0.9** (scraped 2026-08-29) — <https://semantic-release.org/foundation/workflow-configuration/> · <https://semantic-release.org/foundation/supported-branching/> · <https://semantic-release.org/recipes/release-workflow/>
Raw: `$SKILL_DIR/subskills/git/references/semantic-release-raw/009-workflow-configuration.md` · `010-supported-branching.md` · `011-release-workflow.md` · `012-distribution-channels.md` · `013-maintenance-releases.md` · `014-pre-releases.md`
Lead: **branching** — release/maintenance/pre-release branches and distribution channels configured via the `branches` option.

## Branch types

The `branches` option accepts strings, micromatch globs, or objects. Branch type is auto-detected from name/properties:

| Type        | Purpose                                                    | Key property |
| ----------- | ---------------------------------------------------------- | ------------ |
| Release     | Releases on top of the last released version (1–3 allowed) | `name`       |
| Maintenance | Releases on top of an old release (range `N.N.x`/`N.x`)    | `range`      |
| Pre-release | Pre-releases (`2.0.0-beta.1`, …)                           | `prerelease` |

### Branch properties

| Property     | Branch type | Description                                                                                     | Default                                           |
| ------------ | ----------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `name`       | All         | Git branch holding commits to analyze/release. Glob-supported; ignored if branch doesn't exist. | The string value itself / matched branch name     |
| `channel`    | All         | Distribution channel for releases from this branch. `false` forces the default channel.         | `undefined` for first release branch, else `name` |
| `range`      | Maintenance | SemVer range to support (`N.N.x`/`N.x`). Required unless `name` is already range-shaped.        | The value of `name`                               |
| `prerelease` | Pre-release | Pre-release identifier appended to versions. `true` uses `name`.                                | —                                                 |

A project must define ≥1 release branch (max 3); order matters — versions on a later branch must always exceed the last release of the previous branch, else `EINVALIDNEXTVERSION`. Versions must be unique regardless of channel.

### Default branches expansion

`['+([0-9])?(.{+([0-9]),x}).x', 'master', 'main', 'next', 'next-major', {name:'beta',prerelease:true}, {name:'alpha',prerelease:true}]` activates `next`/`next-major`/`beta`/`alpha` only when those branches are created.

## Supported branching models

**Supported:** Trunk-Based Development (commit to trunk, short-lived feature branches, CI, continuous deployment/release) · GitHub Flow (short-lived PRs, frequent releases).

**Unsupported:** Branch-for-Release (except late-created maintenance branches) · Git Flow long-lived develop/release/hotfix orchestration (pre-release workflow can _simulate_ it but is unsupported) · release-for-testing-then-promote · monorepos (unsupported officially; community plugins).

> Scaffold note: the scaffold emits `branches: ["main"]` — the simplest supported release-branch setup. To add channels/maintenance/pre-releases, extend the `branches` array per this reference (or link recipes below).

## Recipes

### Distribution channels

Publish to subsets of users (npm dist-tags `@latest`, `@next`, `@beta`). Flow: `feat: initial commit` on `main` → `v1.0.0` on `@latest`; create `next` branch → `v2.0.0` on `@next`; merge `next` into `main` → `2.0.0` added to `@latest`. Users on `npm install example-module@next` get unreleased versions first.

### Maintenance releases

Fixes/features for old versions: branch `1.x` from `v1.0.0` tag → `v1.1.0` on `@release-1.x`; branch `1.0.x` from `v1.0.0` → `v1.0.1` on `@release-1.0.x`; merge fixes up the chain (`1.0.x` → `1.x` → `main`) to propagate. Channels: `@release-1.x`, `@release-1.0.x`.

### Pre-releases

`beta`/`alpha` branches produce pre-release versions (`2.0.0-beta.1`…). Promotion: merge the pre-release branch into the release branch to graduate the version to the default channel; `next-major` for the next major line. Useful to _simulate_ git-flow; keep branch lifetimes short.

> Recipes assume the default config (`branches` + 4 default plugins). The scaffold's `CONTRIBUTING.md` documents conventional-commit → release mapping; these recipes are the "why" behind branch hygiene rules.
