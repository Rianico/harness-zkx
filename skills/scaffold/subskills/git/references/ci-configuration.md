# Semantic Release — CI Configuration & Running

Source: semantic-release **25.0.9** (scraped 2026-08-29) — <https://semantic-release.org/usage/ci-configuration/> · <https://semantic-release.org/recipes/ci-configurations/github-actions/> · <https://semantic-release.org/usage/running/> · <https://semantic-release.org/support/git-version/> · <https://semantic-release.org/support/node-version/>
Raw: `$SKILL_DIR/subskills/git/references/semantic-release-raw/004-ci-configuration.md` · `015-github-actions.md` · `005-running.md` · `016-git-version.md` · `017-node-version.md` · `018-faq.md`
Lead: **CI** — run semantic-release only after all tests pass, with Git + registry auth; npx invocation; version requirements.

## Two core requirements

1. **Run only after all tests succeed** — if the build has multiple jobs (OS/Node matrix), guarantee `semantic-release` runs only after all jobs pass.
2. **Authentication** — push access (Git tags) + registry/API tokens.

### Git authentication (push access)

| Variable                       | Description                                                                                               |
| ------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `GH_TOKEN` / `GITHUB_TOKEN`    | GitHub token. In Actions, workflow-provided `GITHUB_TOKEN` is automatic; prefer it or a GitHub App token. |
| `GL_TOKEN` / `GITLAB_TOKEN`    | GitLab personal access token.                                                                             |
| `BB_TOKEN` / `BITBUCKET_TOKEN` | Bitbucket token.                                                                                          |
| `GIT_CREDENTIALS`              | URL-encoded `<username>:<password>` (each part individually encoded).                                     |

Alternative: SSH keys. Prefer short-lived credentials (OIDC trusted publishing, GitHub App tokens) over long-lived secrets.

### Plugin authentication

- `NPM_TOKEN` — npm publish token; trusted publishing (OIDC) is recommended for the official registry; a token is required for alternative registries.
- `GH_TOKEN` / `GITHUB_TOKEN` — GitHub releases (see @semantic-release/github auth).

## Running semantic-release

**Recommended: `npx` in CI** (semantic-release is a release dependency, not a dev dependency — avoid local install):

```sh
npx semantic-release                # unpinned (less deterministic)
npx semantic-release@25             # pin at least the major
npx --package semantic-release@25 --package conventional-changelog-conventionalcommits@9 semantic-release
```

Pinning notes: pin all packages in the `npx` command (major at minimum); plugins/presets release majors on their own schedule. Renovate regex manager can auto-bump `npx semantic-release@…` in workflows. Local install is possible but pulls npm into `node_modules` and can conflict with commitlint.

## Version requirements

- **Git ≥ 2.7.1** — required for `git tag --merged`, `git ls-files` bug fixes used internally.
- **Node ≥ 22.14.0** (ECMAScript 2017+, untranspiled). Run `semantic-release` from a job on the latest LTS. Alternatives: `npx -p node@v24 -c "npx semantic-release"`, or `nvm install 'lts/*' && npx semantic-release`.

## GitHub Actions recipe (secure defaults)

Reference shape (scaffold's `release.yml` follows this with pinned action SHAs + on-demand dispatch):

```yaml
name: Verify and Release
on:
  push:
    branches: [main]        # scaffold: repository_dispatch/workflow_dispatch only
permissions:
  contents: read            # verify job: read-only
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: {fetch-depth: 0}
      - uses: actions/setup-node@v4
        with: {node-version-file: .nvmrc}
      - run: npm clean-install
      - run: npm audit signatures
      - run: npm test
  release:
    needs: verify
    permissions:
      contents: write       # publish GitHub release
      issues: write         # comment on released issues
      pull-requests: write  # comment on released PRs
      id-token: write       # OIDC trusted publishing + npm provenance
    steps:
      - uses: actions/checkout@v4
        with: {fetch-depth: 0}
      - uses: actions/setup-node@v4
        with: {node-version: "lts/*"}
      - run: npm clean-install
      - run: npx semantic-release
        env: {GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}}
```

Key facts:

- **Trusted publishing (Path A, recommended):** no long-lived npm token; requires `id-token: write` + an npm Trusted Publisher configured for the triggering workflow; npm provenance generated automatically.
- **`NPM_TOKEN` (Path B, fallback):** repository secret; keep `GITHUB_TOKEN` for releases/comments.
- **Branch protection:** the auto-populated `GITHUB_TOKEN` cannot push when branch protection is enabled on the target branch — use a GitHub App token (`create-github-app-token`); avoid PATs (broad security risk).
- **Publish pipeline Node version** can differ from verification jobs, but must meet the Node requirement.

> Scaffold note: `release.yml` emits verify (read) → release (write + id-token, `needs: verify`) with pinned SHAs, `npm ci` + `npm audit signatures` + `npm test` gates, and `npx semantic-release` with `GITHUB_TOKEN`. On-demand via `repository_dispatch`/`workflow_dispatch`. Regenerate from `scaffold.py`.
