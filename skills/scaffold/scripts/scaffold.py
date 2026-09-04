#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///

"""
Deterministic scaffold generator — tool owns bytes, model owns intent.

Usage:
  uv run $SKILL_DIR/scripts/scaffold.py --flavor git [--project-name NAME] [--dry-run]
  uv run $SKILL_DIR/scripts/scaffold.py --flavor python [--project-name NAME] [--dry-run] [--with-coverage --coverage-threshold 80]
  uv run $SKILL_DIR/scripts/scaffold.py --flavor rust [--project-name NAME] [--dry-run] [--with-coverage --coverage-threshold 80]
  uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript [--ts-variant lib|cli|pi-extension] [--project-name NAME] [--dry-run] [--with-coverage --coverage-threshold 80]
  uv run $SKILL_DIR/scripts/scaffold.py --flavor ci [--project-name NAME] [--dry-run] [--with-coverage]
  uv run $SKILL_DIR/scripts/scaffold.py --flavor all [--project-name NAME] [--dry-run] [--with-coverage]

Information boundary: script emits byte-identical artifacts; for mixed
deterministic+semantic files it writes the skeleton and warns on stderr
so the model proofreads semantic sections. Never hand-copy templates.
This script is the single source of truth — preview with --dry-run.
"""

from __future__ import annotations

import argparse
import difflib
import json
import pathlib
import re
import sys

# Pinned GH Actions SHAs for Node 24 (single source) — keep in sync with .github/workflows/*.yml
SHA_TABLE = {
    "checkout": "93cb6efe18208431cddfb8368fd83d5badbf9bfd",  # actions/checkout v5
    "setup-node": "a0853c24544627f65ddf259abe73b1d18a591444",  # actions/setup-node v5
    "setup-python": "e797f83bcb11b83ae66e0230d6156d7c80228e7c",  # actions/setup-python v6
    "github-script": "ed597411d8f924073f98dfc5c65a23a2325f34cd",  # actions/github-script v8
}

NODE_VERSION_NUM = "24"
NODE_VERSION = NODE_VERSION_NUM + "\n"


def _expand_node_version(text: str) -> str:
    """Single-source Node version: expand the placeholder from NODE_VERSION_NUM."""
    return text.replace("__NODE_VERSION__", NODE_VERSION_NUM)


# ------------------------------------------------------------------ templates (pure-deterministic except {{project_name}})
RELEASERC_JSON = """\
{
  "branches": ["main"],
  "plugins": [
    "@semantic-release/commit-analyzer",
    [
      "@semantic-release/release-notes-generator",
      {
        "preset": "conventionalcommits",
        "presetConfig": {
          "types": [
            {"type": "feat", "section": "Features"},
            {"type": "fix", "section": "Bug Fixes"},
            {"type": "perf", "section": "Performance Improvements"},
            {"type": "revert", "section": "Reverts"},
            {"type": "docs", "section": "Documentation", "hidden": false},
            {"type": "style", "section": "Styles", "hidden": true},
            {"type": "chore", "section": "Miscellaneous Chores", "hidden": true},
            {"type": "refactor", "section": "Code Refactoring", "hidden": true},
            {"type": "test", "section": "Tests", "hidden": true},
            {"type": "build", "section": "Build System", "hidden": true},
            {"type": "ci", "section": "Continuous Integration", "hidden": true}
          ]
        }
      }
    ],
    ["@semantic-release/changelog", {"changelogFile": "CHANGELOG.md"}],
    ["@semantic-release/npm", {"npmPublish": false}],
    "@semantic-release/github",
    [
      "@semantic-release/git",
      {
        "assets": ["CHANGELOG.md", "package.json", "package-lock.json"],
        "message": "chore(release): ${nextRelease.version}\\n\\n${nextRelease.notes}"
      }
    ]
  ]
}
"""

RELEASE_YML = """\
name: Verify and Release
on:
  repository_dispatch:
    types: [semantic-release]
  workflow_dispatch:
permissions:
  contents: read
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5
        with: {fetch-depth: 0}
      - uses: actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444 # v5  # zizmor: ignore[cache-poisoning]
        with: {node-version: __NODE_VERSION__}
      - run: corepack enable
      - run: pnpm install --no-frozen-lockfile
      - run: pnpm audit --audit-level high
      - run: pnpm run lint && pnpm run typecheck && pnpm test
  release:
    needs: verify
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write
      id-token: write
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5
        with: {fetch-depth: 0}
      - uses: actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444 # v5  # zizmor: ignore[cache-poisoning]
        with: {node-version: __NODE_VERSION__}
      - uses: actions/setup-python@e797f83bcb11b83ae66e0230d6156d7c80228e7c # v6
        with: {python-version: "3.12"}
      - name: Clear Unreleased section (handoff to semantic-release)
        run: python scripts/changelog-unreleased.py clear
      - run: corepack enable
      - run: pnpm install --no-frozen-lockfile
      - run: pnpm dlx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          HUSKY: "0"
"""

CHANGELOG_CHECK_YML = """\
name: Changelog Check
on:
  pull_request:
    branches: [main]
permissions:
  contents: read
concurrency:
  group: changelog-check-${{ github.event.pull_request.number }}
  cancel-in-progress: true
jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5
        with:
          persist-credentials: false
          fetch-depth: 0
      - uses: actions/setup-python@e797f83bcb11b83ae66e0230d6156d7c80228e7c # v6
        with:
          python-version: "3.12"
      - name: Check Unreleased is up to date
        run: |
          # save committed version
          cp CHANGELOG.md /tmp/before.md 2>/dev/null || touch /tmp/before.md
          python scripts/changelog-unreleased.py update
          if diff -q /tmp/before.md CHANGELOG.md >/dev/null; then
            echo "CHANGELOG.md Unreleased ok"
            exit 0
          fi
          echo "::error::CHANGELOG.md Unreleased stale"
          echo ""
          echo "Visible conventional commits in this PR require Unreleased update."
          echo "Expected diff:"
          diff -u /tmp/before.md CHANGELOG.md || true
          echo ""
          echo "Fix locally:"
          echo "  uv run python scripts/changelog-unreleased.py update"
          echo "  git add CHANGELOG.md && git commit --amend --no-edit --no-verify && git push --force-with-lease"
          echo ""
          echo "Hidden types (style/chore/refactor/test/build/ci) without BREAKING CHANGE don't need Unreleased."
          # restore committed file so subsequent steps see original
          cp /tmp/before.md CHANGELOG.md
          exit 1
      - name: Comment on failure
        if: failure()
        uses: actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd # v8
        with:
          script: |
            const body = `> [!warning] CHANGELOG.md Unreleased stale
            This PR contains visible conventional commits (\\`feat|fix|perf|revert|docs\\` or \\`!\\/BREAKING CHANGE\\`) but \\`## [Unreleased]\\` doesn't match \\`scripts/changelog-unreleased.py update\\`.

            Fix:
            \\`\\`\\`bash
            uv run python scripts/changelog-unreleased.py update
            git add CHANGELOG.md && git commit --amend --no-edit
            git push --force-with-lease
            \\`\\`\\`
            Hidden types \\`style|chore|refactor|test|build|ci\\` only need update when breaking.`;
            // avoid duplicate comments
            const {data: comments} = await github.rest.issues.listComments({
              owner: context.repo.owner, repo: context.repo.repo, issue_number: context.issue.number
            });
            if (comments.some(c => c.body.includes('CHANGELOG.md Unreleased stale'))) return;
            await github.rest.issues.createComment({
              owner: context.repo.owner, repo: context.repo.repo, issue_number: context.issue.number, body
            });
"""

GITHOOK_PRE_PUSH = """\
#!/usr/bin/env bash
set -e
# skip in CI / when uv missing — semantic-release push must not fail on hook
if [ "${HUSKY:-}" = "0" ]; then exit 0; fi
if ! command -v uv >/dev/null 2>&1; then exit 0; fi
# pre-push hook: warn if CHANGELOG.md Unreleased stale
while read -r local_ref local_sha remote_ref remote_sha; do
  [ "$local_sha" = "0000000000000000000000000000000000000000" ] && continue
  range="$remote_sha..$local_sha"
  [ "$remote_sha" = "0000000000000000000000000000000000000000" ] && range="$local_sha"
  if ! git log "$range" --pretty=%s --no-merges | grep -Eq '^(feat|fix|perf|revert|docs)(\\(.+\\))?!?: '; then
    if ! git log "$range" --pretty=%B --no-merges | grep -q "BREAKING CHANGE:"; then
      continue
    fi
  fi
  tmp=$(mktemp)
  cp CHANGELOG.md "$tmp" 2>/dev/null || touch "$tmp"
  uv run python scripts/changelog-unreleased.py update >/dev/null
  if ! diff -q CHANGELOG.md "$tmp" >/dev/null; then
    cat >&2 <<'EOF'
> [!warning] CHANGELOG.md [Unreleased] stale
Visible conventional commit in push range but Unreleased not updated.
Fix:
  uv run python scripts/changelog-unreleased.py update
  git add CHANGELOG.md
  git commit --amend --no-edit   # feature branch ok
  git push --force-with-lease
Bypass (human): git push --no-verify
EOF
    cp "$tmp" CHANGELOG.md
    rm "$tmp"
    exit 1
  fi
  rm "$tmp"
done
"""

HUSKY_PRE_PUSH = """\
#!/bin/sh
# husky delegation — exec deterministic hook in .githooks
# Keeps single source of truth in .githooks/pre-push; husky sets core.hooksPath=.husky
# so this delegation ensures the changelog guard remains live under husky.
exec .githooks/pre-push "$@"
"""

COMMITLINT_JS = 'export default { extends: ["@commitlint/config-conventional"] };\n'

ISSUE_BUG_REPORT_YML = """\
name: "\U0001f41b Bug report"
description: Concise, paste-complete repro \u2014 see #38 as exemplar
title: "[bug] "
labels: ["bug"]
body:
  - type: checkboxes
    id: searched
    attributes:
      label: Is there an existing issue for this?
      description: Please search to see if an issue already exists for the bug you encountered.
      options:
        - label: I have searched the existing issues
          required: true
  - type: textarea
    id: summary
    attributes:
      label: Summary
      description: One line \u2014 what broke + failure mode (e.g. trailingDups silently drops `}` \u2192 brace imbalance)
      placeholder: "Plugin 0.5.0 \u2014 trailingDups removes replacement's last line \u2192 brace imbalance"
    validations:
      required: true
  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: plugin/app version, module/file, trigger command
      placeholder: |
        - Version: 0.5.0
        - Module: lib/hashline/anchor-pipeline.js
        - Trigger: edit with remove_from/remove_to
      value: |
        - Version:
        - Module:
        - Trigger:
    validations:
      required: true
  - type: textarea
    id: repro
    attributes:
      label: Steps to Reproduce
      description: Minimal complete file + operation map + exact payload (paste-complete, prefer text over screenshots)
      placeholder: |
        1. Minimal file content (paste-complete):
        ```cpp
        void foo() { }
        ```
        2. Operation map / payload:
        ```json
        { "edits": [["<from>", "<to>", "<replacement_text>"]], "path": "D:\\test.txt" }
        ```
        3. Run: `...`
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: Expected behavior
      description: What you expected to happen (paste expected file/diff)
      placeholder: |
        ```cpp
        // 10 lines, brace-balanced
        ```
    validations:
      required: true
  - type: textarea
    id: actual
    attributes:
      label: Actual behavior
      description: What actually happened \u2014 quote diff / logs / autoFixes / balance delta
      placeholder: |
        ```json
        {"kind":"trailing","removedLine":"\\t}"}
        ```
        brace balance -1
      render: shell
    validations:
      required: true
  - type: textarea
    id: impact
    attributes:
      label: Impact & Trigger Conditions
      description: When it fires, frequency, blast radius
    validations:
      required: false
  - type: textarea
    id: root-cause
    attributes:
      label: Root Cause / Suggested Fixes (optional)
      description: Hypothesis + numbered alternatives with tradeoff (threshold / fail-closed / symmetric range)
    validations:
      required: false
"""

ISSUE_FEATURE_REQUEST_YML = """\
name: "\u2728 Feature request"
description: Suggest an idea \u2014 problem, proposal, alternatives
title: "[feat] "
labels: ["enhancement"]
body:
  - type: checkboxes
    id: searched
    attributes:
      label: Is there an existing issue for this?
      description: Please search to see if an issue already exists.
      options:
        - label: I have searched the existing issues
          required: true
  - type: textarea
    id: problem
    attributes:
      label: Problem \u2014 is your request related to a problem?
      description: What problem does this solve? Who is affected?
      placeholder: "When doing X, I need Y but currently Z happens..."
    validations:
      required: true
  - type: textarea
    id: proposal
    attributes:
      label: Proposal \u2014 describe the solution you'd like
      description: Concise proposal, API/UX sketch if applicable
      placeholder: "Add `...` / change `...` so that ..."
    validations:
      required: true
  - type: textarea
    id: alternatives
    attributes:
      label: Alternatives considered
      description: Other approaches you considered and why not
    validations:
      required: false
  - type: textarea
    id: context
    attributes:
      label: Additional context
      description: Examples, prior art, links (e.g. similar issues, RFC)
    validations:
      required: false
"""

ISSUE_CONFIG_YML = """\
blank_issues_enabled: false
contact_links:
  - name: "Exemplar: well-structured bug report #38"
    url: https://github.com/Rianico/dsh-better-edit/issues/38
    about: Concise Summary \u2192 Environment \u2192 Repro \u2192 Expected/Actual \u2192 Impact \u2014 copy this structure
  - name: "Ask a question \u2014 Discussions"
    url: https://github.com/Rianico/dsh-better-edit/discussions
    about: For questions/support, use Discussions instead of an issue
"""

CONTRIBUTING_MD_TMPL = """\
# Contributing to {project_name}
## Conventional commits
- `feat[(scope)]: description` → MINOR, `fix[(scope)]:` → PATCH, `feat!:` / `BREAKING CHANGE:` → MAJOR
- Other types `docs|style|refactor|perf|test|build|ci|chore|revert` hidden unless `!`
- Scope is noun, description imperative present, lowercase, no period, ≤72 chars
- Enforced by `commitlint` + `husky` (`npx commitlint --from=origin/main --to=HEAD`)
## Changelog
`CHANGELOG.md` `## [Unreleased]` guarded by `pre-push` hook (`warn+block`, `uv run python scripts/changelog-unreleased.py update`) and `changelog-check.yml` (`pull_request` required, `diff -q` vs generated); `release.yml` runs `scripts/changelog-unreleased.py clear` then `semantic-release` owns versioned sections. Do not hand-edit versioned sections. Hidden types `style|chore|refactor|test|build|ci` only appear when `!`/`BREAKING CHANGE`.
## Reporting Issues
Pick the template that matches your intent \u2014 see `.github/ISSUE_TEMPLATE/` (blank issues disabled, `config.yml` links #38):
| Intent | Template | Structure |
|---|---|---|
| **Bug** | `01-bug_report.yml` | **Exemplar #38**: Summary \u2192 Environment (Version/Module/Trigger) \u2192 Steps to Reproduce (paste-complete file + operation map + exact payload) \u2192 Expected vs Actual (quote diff/logs) \u2192 Impact & Trigger Conditions \u2192 Root Cause / Suggested Fixes (optional, numbered tradeoffs) |
| **Feature** | `02-feature_request.yml` | Problem \u2192 Proposal \u2192 Alternatives \u2192 Additional context |
- Bugs: paste-complete, prefer text over screenshots, include `read` hashes / payload and `autoFixes`/balance delta. Link #38 as style reference.
- Features: state problem + proposal at minimum; alternatives optional.
Prompt rule: when the model helps file an issue, infer `bug` vs `feat` from intent, ask for any missing `body` field of that form, and render via `gh issue create --template <file>`. View exemplar with `gh issue view 38 --json title,body --repo Rianico/dsh-better-edit`.
## Before PR
`pnpm run lint && pnpm run typecheck && pnpm test` must pass. See `AGENTS.md` for agent rules.
"""
CONTRIBUTING_MD_TMPL_PYTHON = """\
# Contributing to {project_name}
## Conventional commits
- `feat[(scope)]: description` → MINOR, `fix[(scope)]:` → PATCH, `feat!:` / `BREAKING CHANGE:` → MAJOR
- Other types `docs|style|refactor|perf|test|build|ci|chore|revert` hidden unless `!`
- Scope is noun, description imperative present, lowercase, no period, ≤72 chars
- Enforced by `commitlint` + `husky` (`npx commitlint --from=origin/main --to=HEAD`)
## Changelog
`CHANGELOG.md` `## [Unreleased]` guarded by `pre-push` hook (`warn+block`, `uv run python scripts/changelog-unreleased.py update`) and `changelog-check.yml` (`pull_request` required); `release.yml` runs `scripts/changelog-unreleased.py clear` then `semantic-release` owns versioned sections. Do not hand-edit versioned sections. Hidden types only appear when `!`/`BREAKING CHANGE`.
## Reporting Issues
Pick the template that matches your intent \u2014 see `.github/ISSUE_TEMPLATE/` (blank issues disabled, `config.yml` links #38):
| Intent | Template | Structure |
|---|---|---|
| **Bug** | `01-bug_report.yml` | **Exemplar #38**: Summary \u2192 Environment (Version/Module/Trigger) \u2192 Steps to Reproduce (paste-complete file + operation map + exact payload) \u2192 Expected vs Actual (quote diff/logs) \u2192 Impact & Trigger Conditions \u2192 Root Cause / Suggested Fixes (optional, numbered tradeoffs) |
| **Feature** | `02-feature_request.yml` | Problem \u2192 Proposal \u2192 Alternatives \u2192 Additional context |
- Bugs: paste-complete, prefer text over screenshots, include `read` hashes / payload and `autoFixes`/balance delta. Link #38 as style reference.
- Features: state problem + proposal at minimum; alternatives optional.
Prompt rule: when the model helps file an issue, infer `bug` vs `feat` from intent, ask for any missing `body` field of that form, and render via `gh issue create --template <file>`. View exemplar with `gh issue view 38 --json title,body --repo Rianico/dsh-better-edit`.
## Before PR
`uv run ruff check . && uv run basedpyright && uv run pytest` must pass. See `AGENTS.md` for agent rules.
"""

CHANGELOG_MD = """\
# Changelog
All notable changes to this project will be documented in this file.
"""

try:
    CHANGELOG_UNRELEASED_PY = (pathlib.Path(__file__).parent / "changelog-unreleased.py").read_text(
        encoding="utf-8"
    )
except FileNotFoundError:
    CHANGELOG_UNRELEASED_PY = (
        "#!/usr/bin/env python3\n# managed by scaffold — see scripts/changelog-unreleased.py\n"
    )

GITIGNORE_GIT = [".lsz/", ".pi/", "coverage/"]

GITIGNORE_PYTHON_EXTRA = ["__pycache__/", ".venv/"]
GITIGNORE_RUST_EXTRA = ["target/"]
GITIGNORE_TS_EXTRA = ["node_modules/", "dist/"]

PYTHON_VERSION = "3.14\n"


def build_pyproject(project_name: str, with_coverage: bool, threshold: int) -> str:
    cov_deps = ', "pytest-cov>=5"' if with_coverage else ""
    cov_section = ""
    if with_coverage:
        cov_section = f"""
[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
show_missing = true
fail_under = {threshold}
"""
    return f"""[project]
name = "{project_name}"
version = "0.1.0"
description = ""
readme = "README.md"
requires-python = ">=3.14"
dependencies = []

[dependency-groups]
dev = ["pytest>=8", "ruff>=0.11", "basedpyright>=1.30"{cov_deps}]

[tool.ruff]
line-length = 100
target-version = "py314"

[tool.basedpyright]
typeCheckingMode = "strict"

[tool.pytest.ini_options]
testpaths = ["tests"]
{cov_section}"""


PYPROJECT_TOML_TMPL = build_pyproject("{project_name}", False, 80)

RUST_TOOLCHAIN_TOML = """\
[toolchain]
channel = "stable"
components = ["rustfmt", "clippy"]
"""

CARGO_TOML_TMPL = """\
[package]
name = "{project_name}"
version = "0.1.0"
edition = "2021"

[dependencies]
"""


def _ts_normalize_name(project_name: str) -> str:
    return project_name.lower().replace(" ", "-").replace("_", "-")


def build_package_json(project_name: str, ts_variant: str, with_coverage: bool) -> str:
    npm_name = _ts_normalize_name(project_name)
    scripts: dict[str, str] = {
        "lint": "biome check .",
        "typecheck": "tsc --noEmit",
        "test": "vitest run",
    }
    dev_deps: dict[str, str] = {
        "typescript": ">=5.6",
        "@biomejs/biome": ">=2",
        "vitest": ">=3",
        "tsx": ">=4",
        "@types/node": ">=24",
    }
    if with_coverage:
        scripts["coverage"] = "vitest run --coverage"
        dev_deps["@vitest/coverage-v8"] = ">=3"
    pkg: dict[str, object] = {
        "name": npm_name,
        "version": "0.1.0",
        "description": "",
        "type": "module",
        "packageManager": "pnpm@10.0.0",
        "engines": {"node": ">=24"},
        "scripts": scripts,
        "devDependencies": dev_deps,
    }
    if ts_variant == "cli":
        pkg["bin"] = {npm_name: "./src/cli.ts"}
    elif ts_variant == "pi-extension":
        pkg["pi"] = {"extensions": ["./src/index.ts"]}
    else:
        pkg["main"] = "./src/index.ts"
        pkg["exports"] = {".": "./src/index.ts"}
    return json.dumps(pkg, indent=2) + "\n"


def build_tsconfig() -> str:
    tsconfig: dict[str, object] = {
        "compilerOptions": {
            "target": "ES2022",
            "module": "NodeNext",
            "moduleResolution": "NodeNext",
            "strict": True,
            "verbatimModuleSyntax": True,
            "skipLibCheck": True,
            "noEmit": True,
            "types": ["node"],
        },
        "include": ["src", "tests"],
    }
    rendered = json.dumps(tsconfig, indent=2)
    # biome collapses short arrays — match its bytes so `biome check` is green
    rendered = rendered.replace('[\n    "src",\n    "tests"\n  ]', '["src", "tests"]')
    rendered = rendered.replace('[\n      "node"\n    ]', '["node"]')
    return rendered + "\n"


BIOME_JSON = """\
{
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2
  },
  "linter": {
    "enabled": true
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "double"
    }
  }
}
"""

VITEST_CONFIG_TMPL = """\
import {{ defineConfig }} from "vitest/config";

export default defineConfig({{
  test: {{
    coverage: {{
      provider: "v8",
      reporter: ["text", "lcov"],
      thresholds: {{ lines: {threshold}, functions: {threshold} }},
    }},
  }},
}});
"""

INDEX_TS_TMPL = """\
export function main(): void {{
  console.log("hello from {project_name}");
}}

main();
"""

INDEX_TEST_TS_TMPL = """\
import {{ describe, expect, it }} from "vitest";
import {{ main }} from "../src/index.js";

describe("main", () => {{
  it("runs without throwing", () => {{
    expect(() => main()).not.toThrow();
  }});
}});
"""

CLI_TS_TMPL = """\
#!/usr/bin/env -S pnpm dlx tsx
export function run(args: readonly string[]): void {{
  console.log(`args: ${{args.join(" ")}}`);
}}

run(process.argv.slice(2));
"""

CONTRIBUTING_MD_TMPL_TYPESCRIPT = """\
# Contributing to {project_name}
## Conventional commits
- `feat[(scope)]: description` → MINOR, `fix[(scope)]:` → PATCH, `feat!:` / `BREAKING CHANGE:` → MAJOR
- Other types `docs|style|refactor|perf|test|build|ci|chore|revert` hidden unless `!`
- Scope is noun, description imperative present, lowercase, no period, ≤72 chars
- Enforced by `commitlint` + `husky` (`npx commitlint --from=origin/main --to=HEAD`)
## Changelog
`CHANGELOG.md` `## [Unreleased]` guarded by `pre-push` hook (`warn+block`, `uv run python scripts/changelog-unreleased.py update`) and `changelog-check.yml` (`pull_request` required); `release.yml` runs `scripts/changelog-unreleased.py clear` then `semantic-release` owns versioned sections. Do not hand-edit versioned sections. Hidden types only appear when `!`/`BREAKING CHANGE`.
## Reporting Issues
Pick the template that matches your intent — see `.github/ISSUE_TEMPLATE/` (blank issues disabled).
- Bugs: paste-complete, prefer text over screenshots.
- Features: state problem + proposal at minimum; alternatives optional.
## Before PR
`pnpm run lint && pnpm run typecheck && pnpm test` must pass. See `AGENTS.md` for agent rules.
"""

CI_PYTHON_VERIFY_YML = """\
name: Verify and Release
on:
  repository_dispatch:
    types: [semantic-release]
  workflow_dispatch:
permissions:
  contents: read
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd
        with: {fetch-depth: 0}
      - uses: astral-sh/setup-uv@v5
        with: {python-version: '3.14'}
      - run: uv sync --group dev
      - run: uv run ruff check .
      - run: uv run basedpyright
      - run: uv run pytest
  release:
    needs: verify
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write
      id-token: write
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd
        with: {fetch-depth: 0}
      - uses: actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444 # v5  # zizmor: ignore[cache-poisoning]
        with: {node-version: __NODE_VERSION__}
      - run: npm ci
      - run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          HUSKY: "0"
"""

CI_PYTHON_COVERAGE_YML = """\
name: Verify and Release
on:
  repository_dispatch:
    types: [semantic-release]
  workflow_dispatch:
permissions:
  contents: read
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd
        with: {fetch-depth: 0}
      - uses: astral-sh/setup-uv@v5
        with: {python-version: '3.14'}
      - run: uv sync --group dev
      - run: uv run ruff check .
      - run: uv run basedpyright
      - run: uv run pytest --cov --cov-report=term-missing --cov-report=lcov --cov-fail-under=80
  release:
    needs: verify
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write
      id-token: write
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd
        with: {fetch-depth: 0}
      - uses: actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444 # v5  # zizmor: ignore[cache-poisoning]
        with: {node-version: __NODE_VERSION__}
      - run: npm ci
      - run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          HUSKY: "0"
"""

CI_RUST_VERIFY_YML = """\
name: Verify and Release
on:
  repository_dispatch:
    types: [semantic-release]
  workflow_dispatch:
permissions:
  contents: read
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd
        with: {fetch-depth: 0}
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo fmt --check
      - run: cargo clippy -- -D warnings
      - run: cargo test
  release:
    needs: verify
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write
      id-token: write
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd
        with: {fetch-depth: 0}
      - uses: actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444 # v5  # zizmor: ignore[cache-poisoning]
        with: {node-version: __NODE_VERSION__}
      - run: npm ci
      - run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          HUSKY: "0"
"""

CI_RUST_COVERAGE_YML = """\
name: Verify and Release
on:
  repository_dispatch:
    types: [semantic-release]
  workflow_dispatch:
permissions:
  contents: read
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd
        with: {fetch-depth: 0}
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo llvm-cov --workspace --lcov --output-path lcov.info
      - run: cargo llvm-cov report --fail-under-lines 80
      - run: cargo fmt --check
      - run: cargo clippy -- -D warnings
  release:
    needs: verify
    runs-on: ubuntu-latest
    permissions:
      contents: write
      issues: write
      pull-requests: write
      id-token: write
    steps:
      - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd
        with: {fetch-depth: 0}
      - uses: actions/setup-node@a0853c24544627f65ddf259abe73b1d18a591444 # v5  # zizmor: ignore[cache-poisoning]
        with: {node-version: __NODE_VERSION__}
      - run: npm ci
      - run: npx semantic-release
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          HUSKY: "0"
"""


# Resolve the single-sourced Node version in every CI template above.
RELEASE_YML = _expand_node_version(RELEASE_YML)
CI_PYTHON_VERIFY_YML = _expand_node_version(CI_PYTHON_VERIFY_YML)
CI_PYTHON_COVERAGE_YML = _expand_node_version(CI_PYTHON_COVERAGE_YML)
CI_RUST_VERIFY_YML = _expand_node_version(CI_RUST_VERIFY_YML)
CI_RUST_COVERAGE_YML = _expand_node_version(CI_RUST_COVERAGE_YML)
GH_ROUTER_SKILL = """---
name: gh-router
description: >-
  GitHub workflow router \u2014 release via dispatch and PR enhancement. Use when releasing, dispatching semantic-release, submitting or refining PRs. TRIGGER: release, dispatch, pr enhance, submit PR, refine PR
argument-hint: |-
  gh-release [--dry-run] -- changelog and publish via dispatch
  pr-enhance [base|pr_url] -- PR description generation
metadata:
  manage: [gh-release, pr-enhance]
---

# GH Router

GitHub workflow router. Model-invocable \u2014 dispatches to `gh-release` or `pr-enhance` via subskill load.

## Subskills

| Subskill | Trigger |
|----------|---------|
| `gh-release` | `release`, dispatch semantic-release |
| `pr-enhance` | `submit PR`, `refine PR` |

Load via `Read $SKILL_DIR/subskills/<name>/SKILL.md`.
"""

GH_RELEASE_SKILL = (
    pathlib.Path(__file__)
    .parent.parent.joinpath("..", "gh-router", "subskills", "gh-release", "SKILL.md")
    .read_text(encoding="utf-8")
    if pathlib.Path(__file__)
    .parent.parent.joinpath("..", "gh-router", "subskills", "gh-release", "SKILL.md")
    .exists()
    else """---
name: gh-release
description: >-
  Release via semantic-release dispatch. Validates conventional commits, runs verification, dispatches publish. TRIGGER: release, dispatch, publish, dry-run
argument-hint: |-
  "[--dry-run] -- dispatch semantic-release (dry-run previews version)"
metadata:
  managed-by: gh-router
---

# GH Release

Dispatch semantic-release from `main`.
"""
)

PR_ENHANCE_SKILL = (
    pathlib.Path(__file__)
    .parent.parent.joinpath("..", "gh-router", "subskills", "pr-enhance", "SKILL.md")
    .read_text(encoding="utf-8")
    if pathlib.Path(__file__)
    .parent.parent.joinpath("..", "gh-router", "subskills", "pr-enhance", "SKILL.md")
    .exists()
    else """---
name: pr-enhance
description: >-
  Pull Request optimization expert. TRIGGER: submit PR, refine PR
arguments: base_or_pr
argument-hint: |-
  "[base|pr_url] -- base branch or PR URL"
metadata:
  managed-by: gh-router
---

# PR Enhance

See gh-router.
"""
)


def _write_gh_router(cwd: pathlib.Path, dry_run: bool) -> None:
    # Deterministic gh-router skill with subskills — mirrors current harness
    base = cwd / "skills" / "gh-router"
    write_file(base / "SKILL.md", GH_ROUTER_SKILL, dry_run)
    # Use current harness files as source if available, else fallback to embedded
    for sub in ["gh-release", "pr-enhance"]:
        src = (
            pathlib.Path(__file__).parent.parent.parent
            / "gh-router"
            / "subskills"
            / sub
            / "SKILL.md"
        )
        # fallback to embedded already handled
        if src.exists():
            content = src.read_text(encoding="utf-8")
            write_file(base / "subskills" / sub / "SKILL.md", content, dry_run)
        else:
            content = GH_RELEASE_SKILL if sub == "gh-release" else PR_ENHANCE_SKILL
            if content.strip():
                write_file(base / "subskills" / sub / "SKILL.md", content, dry_run)
    # Scripts for gh-release (check/verify/dispatch) — copy if present
    src_scripts = (
        pathlib.Path(__file__).parent.parent.parent
        / "gh-router"
        / "subskills"
        / "gh-release"
        / "scripts"
    )
    if src_scripts.exists():
        for p in src_scripts.iterdir():
            if p.is_file():
                try:
                    write_file(
                        base / "subskills" / "gh-release" / "scripts" / p.name,
                        p.read_text(encoding="utf-8"),
                        dry_run,
                    )
                    if not dry_run:
                        (base / "subskills" / "gh-release" / "scripts" / p.name).chmod(0o755)
                except Exception:
                    pass
    src_pr_scripts = (
        pathlib.Path(__file__).parent.parent.parent
        / "gh-router"
        / "subskills"
        / "pr-enhance"
        / "scripts"
    )
    if src_pr_scripts.exists():
        for p in src_pr_scripts.iterdir():
            if p.is_file():
                try:
                    write_file(
                        base / "subskills" / "pr-enhance" / "scripts" / p.name,
                        p.read_text(encoding="utf-8"),
                        dry_run,
                    )
                    if not dry_run and p.suffix == ".py":
                        (base / "subskills" / "pr-enhance" / "scripts" / p.name).chmod(0o755)
                except Exception:
                    pass


def infer_project_name(cwd: pathlib.Path) -> str:
    try:
        import subprocess

        out = (
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], cwd=str(cwd), stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
        if out:
            return pathlib.Path(out).name
    except Exception:
        pass
    return cwd.name


def write_file(
    path: pathlib.Path, content: str, dry_run: bool, *, warn_mixed: str | None = None
) -> bool:
    is_mixed = warn_mixed is not None
    if dry_run:
        if path.exists():
            old = path.read_text(encoding="utf-8")
            if old == content:
                print(f"unchanged  {path}", file=sys.stderr)
            else:
                diff = difflib.unified_diff(
                    old.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile=str(path),
                    tofile=str(path) + " (new)",
                )
                sys.stdout.writelines(diff)
        else:
            print(f"would create {path}:\n{content}", file=sys.stdout)
        if is_mixed:
            print(f"WARNING (dry-run): {path}: {warn_mixed}", file=sys.stderr)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    tag = "mixed" if is_mixed else "deterministic"
    print(f"wrote ({tag}) {path}", file=sys.stderr)
    if is_mixed:
        print(f"WARNING: {path}: {warn_mixed}", file=sys.stderr)
    return True


def append_gitignore(path: pathlib.Path, entries: list[str], dry_run: bool) -> None:
    if dry_run:
        existing: set[str] = set()
        if path.exists():
            existing = {
                ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()
            }
        missing = [e for e in entries if e not in existing]
        if missing:
            print(f"would append to {path}: {missing}", file=sys.stdout)
        else:
            print(f"unchanged  {path} (gitignore dedup)", file=sys.stderr)
        return
    existing_set: set[str] = set()
    if path.exists():
        text = path.read_text(encoding="utf-8")
        existing_set = {ln.strip() for ln in text.splitlines() if ln.strip()}
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
    missing = [e for e in entries if e not in existing_set]
    if not missing:
        print(f"unchanged  {path} (gitignore dedup)", file=sys.stderr)
        return
    with path.open("a", encoding="utf-8") as f:
        if path.exists() and path.stat().st_size > 0:
            content = path.read_text(encoding="utf-8")
            if not content.endswith("\n"):
                f.write("\n")
        for e in missing:
            f.write(e + "\n")
    print(f"appended ({len(missing)}) to {path}: {missing}", file=sys.stderr)


def patch_agents(path: pathlib.Path, snippet: str, dry_run: bool) -> None:
    marker = snippet.strip().splitlines()[0][:40]
    if dry_run:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if marker.strip("# ") in text or snippet.strip() in text:
                print(f"unchanged  {path} (AGENTS patch present)", file=sys.stderr)
            else:
                print(f"would patch {path} with:\n{snippet}", file=sys.stdout)
        else:
            print(f"would create {path} with:\n{snippet}", file=sys.stdout)
        print(
            f"WARNING (dry-run): {path}: proofread — keep existing 3 sections, verify pointer wording.",
            file=sys.stderr,
        )
        return
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if snippet.strip() in text or marker.strip("# ") in text:
            print(f"unchanged  {path} (AGENTS patch present)", file=sys.stderr)
            print(
                f"WARNING: {path}: proofread — keep existing 3 sections, verify pointer wording.",
                file=sys.stderr,
            )
            return
        with path.open("a", encoding="utf-8") as f:
            if not text.endswith("\n"):
                f.write("\n")
            if not text.endswith("\n\n"):
                f.write("\n")
            f.write(snippet.rstrip() + "\n")
        print(f"patched {path} (mixed)", file=sys.stderr)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(snippet.rstrip() + "\n", encoding="utf-8")
        print(f"wrote {path} (mixed)", file=sys.stderr)
    print(
        f"WARNING: {path}: proofread — keep existing 3 sections, verify pointer wording.",
        file=sys.stderr,
    )


def patch_wt_hooks(cwd: pathlib.Path, dry_run: bool) -> None:
    wt = cwd / ".config/wt.toml"
    if not wt.exists():
        return
    text = wt.read_text(encoding="utf-8")
    if "core.hooksPath" in text:
        if dry_run:
            print(f"unchanged  {wt} (hooksPath present)", file=sys.stderr)
        else:
            print(f"unchanged  {wt} (hooksPath present)", file=sys.stderr)
        return
    hook_line = 'setup-hooks = "git config core.hooksPath .githooks"'
    if dry_run:
        print(f"would patch {wt} with {hook_line}", file=sys.stdout)
        return
    if "[post-start]" in text:
        lines = text.splitlines()
        out: list[str] = []
        inserted = False
        for line in lines:
            out.append(line)
            if not inserted and line.strip() == "[post-start]":
                out.append(hook_line)
                inserted = True
        if not inserted:
            out.append("[post-start]")
            out.append(hook_line)
        new_text = "\n".join(out) + "\n"
        new_text = new_text.replace("\n\n\n", "\n\n")
    else:
        new_text = text.rstrip() + "\n\n[post-start]\n" + hook_line + "\n"
    wt.write_text(new_text, encoding="utf-8")
    print(f"patched {wt} with hooksPath", file=sys.stderr)


def patch_releaserc_lockfile(cwd: pathlib.Path, dry_run: bool) -> None:
    """pnpm contract: this flavor declares pnpm, so releaserc assets ship pnpm-lock.yaml."""
    path = cwd / ".releaserc.json"
    if dry_run:
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if '"package-lock.json"' in text:
                print(
                    f"would patch {path}: package-lock.json \u2192 pnpm-lock.yaml (pnpm contract)",
                    file=sys.stdout,
                )
            else:
                print(f"unchanged  {path} (releaserc lockfile already pnpm)", file=sys.stderr)
        else:
            print(
                f"NOTE (dry-run): no {path} \u2014 run git flavor first so the pnpm lockfile patch has a target",
                file=sys.stderr,
            )
        return
    if not path.exists():
        print(
            f"NOTE: no {path} \u2014 skipping pnpm lockfile patch (run git flavor first)",
            file=sys.stderr,
        )
        return
    text = path.read_text(encoding="utf-8")
    if '"package-lock.json"' not in text:
        print(f"unchanged  {path} (releaserc lockfile already pnpm)", file=sys.stderr)
        return
    path.write_text(text.replace('"package-lock.json"', '"pnpm-lock.yaml"'), encoding="utf-8")
    print(
        f"patched {path}: package-lock.json \u2192 pnpm-lock.yaml (pnpm contract)", file=sys.stderr
    )


def do_git(cwd: pathlib.Path, project_name: str, dry_run: bool) -> None:
    write_file(cwd / ".releaserc.json", RELEASERC_JSON, dry_run)
    write_file(cwd / ".github" / "workflows" / "release.yml", RELEASE_YML, dry_run)
    write_file(cwd / ".github" / "workflows" / "changelog-check.yml", CHANGELOG_CHECK_YML, dry_run)
    write_file(cwd / ".githooks" / "pre-push", GITHOOK_PRE_PUSH, dry_run)
    write_file(cwd / ".husky" / "pre-push", HUSKY_PRE_PUSH, dry_run)
    if not dry_run:
        for _hook in (cwd / ".githooks" / "pre-push", cwd / ".husky" / "pre-push"):
            try:
                _hook.chmod(0o755)
            except OSError:  # best-effort chmod, ignore on read-only FS
                pass
    write_file(cwd / "scripts" / "changelog-unreleased.py", CHANGELOG_UNRELEASED_PY, dry_run)
    write_file(cwd / "commitlint.config.js", COMMITLINT_JS, dry_run)
    write_file(cwd / "CHANGELOG.md", CHANGELOG_MD, dry_run)
    write_file(
        cwd / ".github" / "ISSUE_TEMPLATE" / "01-bug_report.yml", ISSUE_BUG_REPORT_YML, dry_run
    )
    write_file(
        cwd / ".github" / "ISSUE_TEMPLATE" / "02-feature_request.yml",
        ISSUE_FEATURE_REQUEST_YML,
        dry_run,
    )
    write_file(cwd / ".github" / "ISSUE_TEMPLATE" / "config.yml", ISSUE_CONFIG_YML, dry_run)
    # migrate legacy markdown template (pre-YAML) — keep spine small
    legacy_md = cwd / ".github" / "ISSUE_TEMPLATE" / "bug_report.md"
    if legacy_md.exists():
        if dry_run:
            print(
                f"would remove legacy {legacy_md} (migrated to 01-bug_report.yml)", file=sys.stdout
            )
        else:
            try:
                legacy_md.unlink()
                print(
                    f"removed legacy {legacy_md} (migrated to 01-bug_report.yml)", file=sys.stderr
                )
            except OSError:
                pass
    contrib = CONTRIBUTING_MD_TMPL.format(project_name=project_name)
    write_file(
        cwd / "CONTRIBUTING.md",
        contrib,
        dry_run,
        warn_mixed="mixed: contains {{project_name}} + toolchain 'Before PR' line — proofread project name and lint/test commands.",
    )
    append_gitignore(cwd / ".gitignore", GITIGNORE_GIT, dry_run)
    patch_agents(
        cwd / "AGENTS.md",
        "### Contribution\nConventional commits & changelog: see CONTRIBUTING.md\nGit hooks: `git config core.hooksPath .githooks` (or `npm install` with husky → `.husky` delegates to `.githooks`) so pre-push CHANGELOG guard is live on fresh clone/worktree.\n",
        dry_run,
    )
    _write_gh_router(cwd, dry_run)
    patch_wt_hooks(cwd, dry_run)


def do_python(
    cwd: pathlib.Path, project_name: str, dry_run: bool, with_coverage: bool, threshold: int
) -> None:
    write_file(cwd / ".python-version", PYTHON_VERSION, dry_run)
    pyproj = build_pyproject(project_name, with_coverage, threshold)
    warn = (
        f"mixed: {{{{project_name}}}} + coverage gate {threshold}% — proofread name and fail_under"
        if with_coverage
        else "mixed: {{project_name}} + description/readme — proofread package name and description."
    )
    write_file(
        cwd / "pyproject.toml",
        pyproj,
        dry_run,
        warn_mixed=warn,
    )
    append_gitignore(cwd / ".gitignore", GITIGNORE_GIT + GITIGNORE_PYTHON_EXTRA, dry_run)
    patch_agents(
        cwd / "AGENTS.md",
        "### Runtime\nPython: uv + .python-version (3.14), run via uv run; see pyproject.toml\n",
        dry_run,
    )
    contrib_py = CONTRIBUTING_MD_TMPL_PYTHON.format(project_name=project_name)
    write_file(
        cwd / "CONTRIBUTING.md",
        contrib_py,
        dry_run,
        warn_mixed="mixed: contains {{project_name}} + toolchain 'Before PR' line — proofread project name and lint/test commands.",
    )
    if with_coverage:
        print(
            f"NOTE: Python coverage wired — run `uv run pytest --cov --cov-fail-under={threshold}`",
            file=sys.stderr,
        )


def do_rust(
    cwd: pathlib.Path, project_name: str, dry_run: bool, with_coverage: bool, threshold: int
) -> None:
    cargo_name = project_name.lower().replace("_", "-").replace(" ", "-")
    if cargo_name != project_name:
        print(
            f"WARNING: Cargo package name normalized to '{cargo_name}' (from '{project_name}') — proofread Cargo.toml name.",
            file=sys.stderr,
        )
    write_file(cwd / "rust-toolchain.toml", RUST_TOOLCHAIN_TOML, dry_run)
    cargo = CARGO_TOML_TMPL.format(project_name=cargo_name)
    warn = "mixed: {{project_name}} normalized to kebab-case — proofread package name and edition."
    if with_coverage:
        warn += f" + coverage llvm-cov {threshold}%"
    write_file(
        cwd / "Cargo.toml",
        cargo,
        dry_run,
        warn_mixed=warn,
    )
    append_gitignore(cwd / ".gitignore", GITIGNORE_GIT + GITIGNORE_RUST_EXTRA, dry_run)
    patch_agents(
        cwd / "AGENTS.md",
        "### Runtime\nRust: cargo + rust-toolchain.toml (stable), verify via cargo fmt/clippy/test\n",
        dry_run,
    )
    if with_coverage:
        print(
            f"NOTE: Rust coverage requires `cargo llvm-cov` (install: cargo install cargo-llvm-cov). Threshold {threshold}% enforced via `cargo llvm-cov report --fail-under-lines {threshold}`",
            file=sys.stderr,
        )


def do_typescript(
    cwd: pathlib.Path,
    project_name: str,
    dry_run: bool,
    ts_variant: str,
    with_coverage: bool,
    threshold: int,
) -> None:
    npm_name = _ts_normalize_name(project_name)
    if npm_name != project_name:
        print(
            f"WARNING: npm package name normalized to '{npm_name}' (from '{project_name}') — proofread package.json name.",
            file=sys.stderr,
        )
    write_file(cwd / ".nvmrc", NODE_VERSION, dry_run)
    pkg_json = build_package_json(project_name, ts_variant, with_coverage)
    warn = "mixed: {{project_name}} + description — proofread package name and description."
    if with_coverage:
        warn += f" + coverage @vitest/coverage-v8 {threshold}%"
    write_file(
        cwd / "package.json",
        pkg_json,
        dry_run,
        warn_mixed=warn,
    )
    write_file(cwd / "tsconfig.json", build_tsconfig(), dry_run)
    write_file(cwd / "biome.json", BIOME_JSON, dry_run)
    write_file(
        cwd / "src" / "index.ts",
        INDEX_TS_TMPL.format(project_name=npm_name),
        dry_run,
    )
    write_file(cwd / "tests" / "index.test.ts", INDEX_TEST_TS_TMPL.format(), dry_run)
    if ts_variant == "cli":
        cli_path = cwd / "src" / "cli.ts"
        write_file(cli_path, CLI_TS_TMPL.format(), dry_run)
        if not dry_run:
            try:
                cli_path.chmod(0o755)
            except OSError:
                pass
    if with_coverage:
        write_file(
            cwd / "vitest.config.ts",
            VITEST_CONFIG_TMPL.format(threshold=threshold),
            dry_run,
        )
        print(
            f"NOTE: TypeScript coverage wired — run `pnpm run coverage` (fail_under lines/functions {threshold}%)",
            file=sys.stderr,
        )
    patch_releaserc_lockfile(cwd, dry_run)
    append_gitignore(cwd / ".gitignore", GITIGNORE_GIT + GITIGNORE_TS_EXTRA, dry_run)
    patch_agents(
        cwd / "AGENTS.md",
        "### Runtime\nTypeScript: pnpm + .nvmrc (24), verify via biome/tsc/vitest; see package.json\n",
        dry_run,
    )
    contrib_ts = CONTRIBUTING_MD_TMPL_TYPESCRIPT.format(project_name=project_name)
    write_file(
        cwd / "CONTRIBUTING.md",
        contrib_ts,
        dry_run,
        warn_mixed="mixed: contains {{project_name}} + toolchain 'Before PR' line — proofread project name and lint/test commands.",
    )
    if ts_variant == "pi-extension":
        print(
            "NOTE: pi-extension entry is ./src/index.ts (pi loads .ts directly, no build step) — proofread package.json `pi.extensions` path.",
            file=sys.stderr,
        )


def do_ci(
    cwd: pathlib.Path, dry_run: bool, variant: str, with_coverage: bool, threshold: int
) -> None:
    if variant == "python":
        if with_coverage:
            content = CI_PYTHON_COVERAGE_YML.replace(
                "--cov-fail-under=80", f"--cov-fail-under={threshold}"
            )
        else:
            content = CI_PYTHON_VERIFY_YML
    elif variant == "rust":
        if with_coverage:
            content = CI_RUST_COVERAGE_YML.replace(
                "--fail-under-lines 80", f"--fail-under-lines {threshold}"
            )
        else:
            content = CI_RUST_VERIFY_YML
    else:
        content = RELEASE_YML
        if with_coverage:
            content = content.replace("- run: pnpm test", "- run: pnpm run coverage")
            print(
                "NOTE: Node/TS coverage runs `pnpm run coverage` in verify — thresholds owned by vitest.config.ts (run typescript flavor with --with-coverage to generate it)",
                file=sys.stderr,
            )
    write_file(cwd / ".github" / "workflows" / "release.yml", content, dry_run)


def detect_project(cwd: pathlib.Path) -> dict[str, object]:
    """Deterministic cheap detection: file existence + content sniff (no guessing)."""

    def exists(p: str) -> bool:
        return (cwd / p).exists()

    def read_text(p: str, limit: int = 4000) -> str:
        try:
            return (cwd / p).read_text(encoding="utf-8")[:limit]
        except Exception:
            return ""

    def has_content(p: str, pattern: str) -> bool:
        txt = read_text(p)
        return bool(re.search(pattern, txt, re.IGNORECASE)) if txt else False

    files: dict[str, bool] = {
        ".python-version": exists(".python-version"),
        "pyproject.toml": exists("pyproject.toml"),
        "uv.lock": exists("uv.lock"),
        "Cargo.toml": exists("Cargo.toml"),
        "rust-toolchain.toml": exists("rust-toolchain.toml"),
        "package.json": exists("package.json"),
        ".nvmrc": exists(".nvmrc"),
        "tsconfig.json": exists("tsconfig.json"),
        "biome.json": exists("biome.json"),
        "package-lock.json": exists("package-lock.json"),
        "pnpm-lock.yaml": exists("pnpm-lock.yaml"),
        ".tool-versions": exists(".tool-versions"),
        ".releaserc.json": exists(".releaserc.json"),
        ".releaserc.js": exists(".releaserc.js"),
        ".github/workflows/release.yml": exists(".github/workflows/release.yml"),
        ".github/workflows/changelog-check.yml": exists(".github/workflows/changelog-check.yml"),
        "CHANGELOG.md": exists("CHANGELOG.md"),
        "commitlint.config.js": exists("commitlint.config.js"),
        ".githooks/pre-push": exists(".githooks/pre-push"),
        ".husky/pre-push": exists(".husky/pre-push"),
        ".gitignore": exists(".gitignore"),
        "CONTRIBUTING.md": exists("CONTRIBUTING.md"),
        "AGENTS.md": exists("AGENTS.md"),
    }

    pyproject = read_text("pyproject.toml")
    release_yml = read_text(".github/workflows/release.yml")
    changelog = read_text("CHANGELOG.md")
    tool_versions = read_text(".tool-versions")
    pkg_json = read_text("package.json")
    vitest_config = read_text("vitest.config.ts")

    python_present = files["pyproject.toml"] or files[".python-version"]
    rust_present = files["Cargo.toml"] or files["rust-toolchain.toml"]
    node_present = files["package.json"]
    polyglot = (
        files[".tool-versions"]
        or (python_present and rust_present)
        or (python_present and node_present)
        or (rust_present and node_present)
    )

    python_coverage = bool(re.search(r"pytest-cov|tool\.coverage|fail_under", pyproject))
    python_coverage_threshold: int | None = None
    m = re.search(r"fail_under\s*=\s*(\d+)", pyproject)
    if m:
        try:
            python_coverage_threshold = int(m.group(1))
        except ValueError:
            python_coverage_threshold = None
    rust_coverage = "llvm-cov" in release_yml or has_content("Cargo.toml", r"llvm-cov")
    ci_coverage = (
        "--cov" in release_yml
        or "llvm-cov" in release_yml
        or "fail-under" in release_yml
        or "pnpm run coverage" in release_yml
    )
    ts_coverage = "coverage" in vitest_config or "@vitest/coverage" in pkg_json
    ts_coverage_threshold: int | None = None
    m_ts = re.search(r"lines:\s*(\d+)", vitest_config)
    if m_ts:
        try:
            ts_coverage_threshold = int(m_ts.group(1))
        except ValueError:
            ts_coverage_threshold = None
    ts_variant: str | None
    if node_present:
        if '"extensions"' in pkg_json and '"pi"' in pkg_json:
            ts_variant = "pi-extension"
        elif '"bin"' in pkg_json:
            ts_variant = "cli"
        else:
            ts_variant = "lib"
    else:
        ts_variant = None

    ci_variant: str | None = None
    if files[".github/workflows/release.yml"]:
        if "setup-uv" in release_yml or "astral-sh/setup-uv" in release_yml:
            ci_variant = "python"
        elif "dtolnay/rust-toolchain" in release_yml:
            if "setup-uv" in release_yml and "dtolnay" in release_yml:
                ci_variant = "matrix"
            else:
                ci_variant = "rust"
        else:
            ci_variant = "node"
    if ci_variant is None and rust_present and not python_present:
        ci_variant = "rust"

    git_complete = (
        files[".releaserc.json"] and files["CHANGELOG.md"] and files["commitlint.config.js"]
    )
    git_stale = files[".releaserc.json"] and not files[".github/workflows/changelog-check.yml"]

    if polyglot:
        inferred_shape = "polyglot"
    elif python_present:
        inferred_shape = "python"
    elif rust_present:
        inferred_shape = "rust"
    elif node_present:
        inferred_shape = "node"
    else:
        inferred_shape = "greenfield"

    tool_versions_detail: dict[str, str] = {}
    if tool_versions:
        for line in tool_versions.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                tool_versions_detail[parts[0]] = parts[1]

    verify_gates: dict[str, bool] = {
        "formatter": bool(
            re.search(r"ruff.*format|cargo fmt|prettier|biome", pyproject + release_yml + pkg_json)
        ),
        "linter": bool(
            re.search(
                r"ruff check|clippy|eslint|biome", pyproject + release_yml + pkg_json, re.IGNORECASE
            )
        ),
        "typecheck": bool(
            re.search(
                r"basedpyright|mypy|tsc --noEmit|cargo check", pyproject + release_yml + pkg_json
            )
        ),
        "tests": bool(
            re.search(r"pytest|cargo test|npm test|vitest", pyproject + release_yml + pkg_json)
        ),
    }

    result: dict[str, object] = {
        "cwd": str(cwd),
        "project_name": infer_project_name(cwd),
        "inferred_shape": inferred_shape,
        "files": files,
        "git_contract": {
            "complete": git_complete,
            "stale": git_stale,
            "has_releaserc": files[".releaserc.json"] or files[".releaserc.js"],
            "has_changelog": files["CHANGELOG.md"],
            "has_changelog_check": files[".github/workflows/changelog-check.yml"],
            "has_hooks": files[".githooks/pre-push"] or files[".husky/pre-push"],
        },
        "runtimes": {
            "python": python_present,
            "rust": rust_present,
            "node": node_present,
            "polyglot": polyglot,
            "tool_versions": tool_versions_detail,
        },
        "python": {
            "present": python_present,
            "coverage": python_coverage,
            "threshold": python_coverage_threshold,
        },
        "rust": {
            "present": rust_present,
            "coverage": rust_coverage,
        },
        "typescript": {
            "present": node_present and files["tsconfig.json"],
            "coverage": ts_coverage,
            "threshold": ts_coverage_threshold,
            "variant": ts_variant,
        },
        "ci": {
            "present": files[".github/workflows/release.yml"],
            "variant": ci_variant,
            "coverage": ci_coverage,
            "has_release_yml": files[".github/workflows/release.yml"],
        },
        "changelog": {
            "has_unreleased": "## [Unreleased]" in changelog if changelog else False,
        },
        "verify_gates": verify_gates,
    }
    return result


def print_detect(cwd: pathlib.Path, as_json: bool) -> int:
    data = detect_project(cwd)
    json_str = json.dumps(data, indent=2, sort_keys=True)
    print(json_str)
    files = data["files"]  # type: ignore[assignment]
    print(f"\n# Detect summary for {cwd}", file=sys.stderr)
    print(f"shape={data['inferred_shape']} project={data['project_name']}", file=sys.stderr)
    present = [k for k, v in files.items() if v]  # type: ignore[union-attr]
    missing = [k for k, v in files.items() if not v]  # type: ignore[union-attr]
    print(f"present: {', '.join(present) if present else '(none)'}", file=sys.stderr)
    print(f"missing: {', '.join(missing) if missing else '(none)'}", file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministic scaffold generator")
    ap.add_argument(
        "--flavor",
        choices=["git", "python", "rust", "typescript", "ci", "all"],
        required=False,
        default=None,
        help="flavor to scaffold",
    )
    ap.add_argument(
        "--project-name",
        default=None,
        help="project name for {{project_name}} (default: inferred from cwd)",
    )
    ap.add_argument("--dry-run", action="store_true", help="print diff without writing")
    ap.add_argument(
        "--ci-variant",
        choices=["node", "python", "rust"],
        default="node",
        help="CI verify variant (default: node)",
    )
    ap.add_argument(
        "--ts-variant",
        choices=["lib", "cli", "pi-extension"],
        default="lib",
        help="TypeScript project variant (default: lib)",
    )
    ap.add_argument("--cwd", default=".", help="target directory (default: .)")
    ap.add_argument(
        "--with-coverage",
        action="store_true",
        help="wire coverage gate (pytest-cov / cargo llvm-cov / vitest coverage)",
    )
    ap.add_argument(
        "--coverage-threshold",
        type=int,
        default=80,
        help="coverage fail-under threshold (default: 80)",
    )
    ap.add_argument(
        "--detect", action="store_true", help="detect project state and exit (no writes)"
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="with --detect, emit JSON only (alias, JSON always to stdout)",
    )
    args = ap.parse_args()

    cwd = pathlib.Path(args.cwd).resolve()
    if args.detect:
        return print_detect(cwd, as_json=True)
    if args.flavor is None:
        ap.error("--flavor is required unless --detect is used")
    project_name = args.project_name or infer_project_name(cwd)
    flavor: str = args.flavor
    dry_run: bool = args.dry_run
    with_coverage: bool = args.with_coverage
    threshold: int = args.coverage_threshold

    if threshold < 0 or threshold > 100:
        print("error: --coverage-threshold must be 0-100", file=sys.stderr)
        return 2

    if not project_name or not project_name.strip():
        print("error: --project-name is required when cwd has no inferrable name", file=sys.stderr)
        return 2

    if flavor in ("git", "all"):
        do_git(cwd, project_name, dry_run)
    if flavor in ("python", "all"):
        do_python(cwd, project_name, dry_run, with_coverage, threshold)
    if flavor in ("rust", "all"):
        do_rust(cwd, project_name, dry_run, with_coverage, threshold)
    if flavor in ("typescript", "all"):
        do_typescript(cwd, project_name, dry_run, args.ts_variant, with_coverage, threshold)
    if flavor == "ci":
        do_ci(cwd, dry_run, args.ci_variant, with_coverage, threshold)

    if dry_run:
        print(
            "dry-run complete — no files written (warnings on stderr are expected for mixed files)",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
