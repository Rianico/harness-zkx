#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = ["jinja2>=3.1.6"]
# ///

"""
Deterministic scaffold generator — tool owns bytes, model owns intent.

Usage:
  uv run $SKILL_DIR/scripts/scaffold.py --flavor git [--project-name NAME] [--dry-run] [--only pre-push|releaserc|...] [--without ...] [--components ...]
  uv run $SKILL_DIR/scripts/scaffold.py --flavor python [--project-name NAME] [--dry-run] [--with-coverage --coverage-threshold 80]
  uv run $SKILL_DIR/scripts/scaffold.py --flavor rust [--project-name NAME] [--dry-run] [--with-coverage --coverage-threshold 80]
  uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript [--ts-variant lib|cli|pi-extension] [--project-name NAME] [--dry-run] [--with-coverage --coverage-threshold 80]
  uv run $SKILL_DIR/scripts/scaffold.py --flavor ci [--project-name NAME] [--dry-run] [--with-coverage]
  uv run $SKILL_DIR/scripts/scaffold.py --flavor all [--project-name NAME] [--dry-run] [--with-coverage]
  uv run $SKILL_DIR/scripts/scaffold.py --update [--flavor git|all] [--dry-run]  # refresh generated infrastructure in place; project-owned files are preserved and printed as NEXT actions
  uv run $SKILL_DIR/scripts/scaffold.py --flavor typescript --no-format  # skip the oxfmt pass (no Node needed); the generated CI format gate stays red until `pnpm run format:fix`
  uv run $SKILL_DIR/scripts/scaffold.py ensure rust-dep --name tokio --version 1
  uv run $SKILL_DIR/scripts/scaffold.py ensure py-dep --req "httpx>=0.27"
  uv run $SKILL_DIR/scripts/scaffold.py ensure ts-dep --name zod --version "^3"
  uv run $SKILL_DIR/scripts/scaffold.py ensure ts-script --name coverage --cmd "vitest run --coverage"
  uv run $SKILL_DIR/scripts/scaffold.py ensure coverage-threshold --flavor python --value 90

Boundary contract (run 1 vs run 2+): run 1 (field absent) means the tool writes
byte-identical bytes with no model judgment; run 2 and later (field present) means the
project owns the file and the model decides replace / update one field / untouched.
`--update` preserves project-owned files and reports them as NEXT actions;
`ensure <op>` performs one confirmed field edit (absent adds minimally, present reports
unchanged, invalid or ambiguous refuses) and never rewrites file semantics wholesale
(package.json edits normalize to 2-space JSON; key order kept, non-ASCII kept literal).

Information boundary: script emits byte-identical artifacts; for mixed
deterministic+semantic files it writes the skeleton and warns on stderr
so the model proofreads semantic sections.
Static bytes live in ../templates/<flavor>/<target path>: raw files ship verbatim,
`.j2` files render through one Jinja Environment (see render_template).
Never hand-copy a template. This script is the single source of truth — preview with --dry-run.
"""

from __future__ import annotations

import argparse
import difflib
import json
import keyword
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import asdict, dataclass
from typing import cast

from jinja2 import Environment, FileSystemLoader, StrictUndefined, TemplateNotFound

# Pinned GH Actions SHAs (single source) — every JavaScript entry runs on node24
# (taiki-e/install-action is composite), and the same table is asserted against
# .github/workflows/*.yml by tests/scaffold/test_templates.py.
SHA_TABLE = {
    "checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",  # actions/checkout v7.0.1
    "setup-node": "820762786026740c76f36085b0efc47a31fe5020",  # actions/setup-node v7.0.0
    "setup-python": "5fda3b95a4ea91299a34e894583c3862153e4b97",  # actions/setup-python v7.0.0
    "github-script": "3a2844b7e9c422d3c10d287c895573f7108da1b3",  # actions/github-script v9.0.0
    "pnpm-setup": "ea17c68df8912ef543352723c149a84f56e3d413",  # pnpm/action-setup v6.1.0
    "rust-cache": "6323deb102c322ba6fcbdcafc7e3dddab59af2b6",  # Swatinem/rust-cache v2.9.2
    "setup-uv": "bec219d24cd3e171d82865faccec33120bb574f4",  # astral-sh/setup-uv v10.1.0
    "install-action": "3f74d7c16a4242f1c95561e98edc25d36adb4375",  # taiki-e/install-action v2.87.12
}

NODE_VERSION_NUM = "26"
NODE_VERSION = NODE_VERSION_NUM + "\n"

# Formatter contract — the pinned formatter owns every byte it can reach.
#
# A generated TypeScript repo's CI gate is `oxfmt --check .` (package.json `format`), so
# whatever this script writes must already be canonical for the version that repo resolves.
# The pin is exact on purpose: formatter output is a byte contract, and upgrades reformat the
# tree (0.15.0 left the generated files untouched; 0.17.0 rewrote seven). Bumping
# OXFMT_VERSION means running tests/scaffold/test_oxfmt_canonical.py and committing whatever it
# reformats — never a silent upgrade.
OXFMT_VERSION = "0.67.0"
# Extensions oxfmt accepts via --stdin-filepath; anything else must not be piped to it (it
# exits 1 with "Unsupported file type for stdin-filepath").
OXFMT_EXTENSIONS = frozenset(
    {
        ".js",
        ".jsx",
        ".mjs",
        ".cjs",
        ".ts",
        ".tsx",
        ".mts",
        ".cts",
        ".json",
        ".jsonc",
        ".css",
        ".scss",
        ".less",
        ".html",
        ".htm",
        ".yaml",
        ".yml",
        ".md",
        ".mdx",
        ".toml",
        ".graphql",
        ".gql",
    }
)


# ------------------------------------------------------------------ template rendering
# Raw templates ship byte-for-byte (Jinja never parses them); a `.j2` suffix marks a file
# that `render_template` renders.
#
# Environment rules (jinja skill, Authoring Rules), each one deliberate:
#   - one Environment, built once here, never per render;
#   - autoescape=False: these artifacts are code/config/prose, not markup, and escaping
#     would corrupt YAML/shell/Markdown bytes;
#   - StrictUndefined: a typo in a context variable fails loud instead of printing "";
#   - trim_blocks/lstrip_blocks: tag-only lines disappear, so composition needs no
#     `{%- -%}` markers. Consequence: never end a line with an inline tag, or its newline
#     is eaten — the byte pins in tests/scaffold/test_templates.py catch that;
#   - keep_trailing_newline=True: the default strips the trailing newline, which is part
#     of the byte contract.
TEMPLATES_DIR = pathlib.Path(__file__).parent.parent / "templates"

_ENV = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=False,
    undefined=StrictUndefined,
    trim_blocks=True,
    lstrip_blocks=True,
    keep_trailing_newline=True,
    newline_sequence="\n",
)

# A GitHub Actions expression (`${{ … }}`) reaches templates as a *variable*: Jinja's
# delimiters are the default `{{ }}`, so the literal must never enter the parser.
GH_ACTIONS_TOKEN = "${{ secrets.GITHUB_TOKEN }}"

DEFAULT_COVERAGE_THRESHOLD = 80


def _template_missing(rel: str) -> FileNotFoundError:
    return FileNotFoundError(
        f"scaffold template missing: {TEMPLATES_DIR / rel}\n"
        "templates/ ships with scripts/ — copy the whole skill directory "
        "(or pass --cwd to a checkout that has it)."
    )


def load_template(rel: str) -> str:
    """Read a static template verbatim. Fails loud — a missing template must never fall back.

    Vendoring only `scripts/` breaks the byte contract; better to refuse than to
    invent bytes that no human reviewed.
    """
    path = TEMPLATES_DIR / rel
    if not path.is_file():
        raise _template_missing(rel)
    return path.read_text(encoding="utf-8")


def render_template(rel: str, /, **context: object) -> str:
    """Render a `.j2` template. Same fail-loud contract as `load_template`."""
    try:
        return _ENV.get_template(rel).render(**context)
    except TemplateNotFound as exc:
        raise _template_missing(rel) from exc


# ------------------------------------------------------------------ templates
# Raw: shipped byte-for-byte — Jinja never parses these, so the `${{ … }}` expressions and
# `${…}` expansions inside workflow YAML and shell stay untouched.
RELEASERC_JSON = load_template("git/.releaserc.json")


CHANGELOG_CHECK_YML = load_template("git/.github/workflows/changelog-check.yml")

GITHOOK_PRE_PUSH = load_template("git/.githooks/pre-push")

HUSKY_PRE_PUSH = load_template("git/.husky/pre-push")

COMMITLINT_JS = load_template("git/commitlint.config.js")

ISSUE_BUG_REPORT_YML = load_template("git/.github/ISSUE_TEMPLATE/01-bug_report.yml")

ISSUE_FEATURE_REQUEST_YML = load_template("git/.github/ISSUE_TEMPLATE/02-feature_request.yml")

ISSUE_CONFIG_YML = load_template("git/.github/ISSUE_TEMPLATE/config.yml")

PULL_REQUEST_TEMPLATE_MD = load_template("git/.github/pull_request_template.md")

CHANGELOG_MD = load_template("git/CHANGELOG.md")

# Other flavors' static artifacts — same contract, one byte source per flavor.
RUST_TOOLCHAIN_TOML = load_template("rust/rust-toolchain.toml")
RUST_LIB_RS = load_template("rust/src/lib.rs")
OXLINT_JSON = load_template("typescript/.oxlintrc.json")
OXFMT_JSON = load_template("typescript/.oxfmtrc.json")
OXLINT_COMMENT_GATE_JS = load_template("typescript/scripts/oxlint-plugin-comment-gate.js")
INDEX_TEST_TS = load_template("typescript/tests/index.test.ts")
CLI_TS = load_template("typescript/src/cli.ts")

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

# Component granularity — git flavor default is all; --only/--without/--components select subset
GIT_COMPONENTS: set[str] = {
    "releaserc",  # .releaserc.json
    "release-yml",  # .github/workflows/release.yml (git variant)
    "changelog-check",  # .github/workflows/changelog-check.yml
    "pre-push",  # .githooks/pre-push + .husky/pre-push + wt hook
    "changelog-script",  # scripts/changelog-unreleased.py
    "commitlint",  # commitlint.config.js
    "changelog-md",  # CHANGELOG.md
    "issue-templates",  # .github/ISSUE_TEMPLATE/* + config.yml
    "pr-template",  # .github/pull_request_template.md
    "contributing",  # CONTRIBUTING.md
    "agents",  # AGENTS.md patch
    "gitignore",  # .gitignore append
}

CI_COMPONENTS: set[str] = {
    "release-yml",  # .github/workflows/release.yml (ci variant)
}

# --update ownership contract. Generated infrastructure is refreshed byte-identically;
# files the project owns are preserved and reported as NEXT actions. Keys are generated
# basenames, values are the reason shown to the model.
PROJECT_OWNED: dict[str, str] = {
    "CHANGELOG.md": "release history — @semantic-release/changelog owns versioned sections",
    "CONTRIBUTING.md": "mixed (project name + toolchain line) and language-variant",
    "pyproject.toml": "project manifest — deps and tool config",
    "Cargo.toml": "project manifest — deps and edition",
    "package.json": "project manifest — deps and scripts",
}

# Components whose file belongs to another flavor's projection: an --update in this
# flavor must not rewrite it (a Node/pnpm verify job would break a uv or cargo repo).
FLAVOR_FOREIGN: dict[str, str] = {
    "release-yml": "owned by the ci flavor — this flavor ships the Node/pnpm verify job"
}

# Ownership of *source*, as opposed to generated infrastructure. --update refreshes the
# latter; these paths are code a project grows by hand, so clobbering them would lose work no
# template can regenerate. Keyed by repo-relative path, not basename: the map only earns its
# keep if it is precise (a basename key would also swallow a project's own `src/other.ts`).
# Same contract as SOURCE_OWNED, for paths whose directory segment is computed from the
# project name — a static key cannot express `src/<module>/__init__.py`.
SOURCE_OWNED_PATTERNS: dict[str, str] = {
    "src/*/__init__.py": "package source — the starting point the project edits",
}


SOURCE_OWNED: dict[str, str] = {
    "src/index.ts": "project source — entry module, hand-grown after scaffold",
    "src/cli.ts": "project source — CLI entry, hand-grown after scaffold",
    "tests/index.test.ts": "project tests — scaffold smoke test, extended by the project",
    "vitest.config.ts": "test config — coverage thresholds are project policy",
    "tsconfig.json": "project config — include/module adapted to real entry points",
    ".oxlintrc.json": "project lint policy — rules adapted per repo",
    ".oxfmtrc.json": "project format policy — ignore patterns adapted per repo",
    "src/lib.rs": "crate source — the starting point the project edits",
    "tests/test_smoke.py": "smoke test — the project replaces it with real tests",
}


# ------------------------------------------------------------------ run report
# A run reports itself in one of three modes. `verbose` is the historical per-file prose and
# unified diffs (humans and the tests read it). `summary` collapses to one line per file plus
# totals; `json` emits the plan as data. Suppressing prose in the last two is the point: the
# plan *is* the payload, so a caller never greps diffs out of stdout to decide what to do.
VERBOSE, SUMMARY, JSON_OUT = "verbose", "summary", "json"

# What happened to one path — the vocabulary the summary, the JSON plan and `--check` share.
UNCHANGED = "unchanged"  # already byte-identical to the template
STALE = "stale"  # exists, differs from the template
MISSING = "missing"  # absent, would be created
PRESERVED = "preserved"  # project-owned, deliberately untouched
PATCHED = "patched"  # append-only or section merge — existing lines never rewritten
APPENDED = "appended"  # lines added to an existing file (.gitignore dedup)

# Drift = the repo and the template disagree. Preservation is a decision, not drift.
DRIFT_KINDS = frozenset({STALE, MISSING, PATCHED, APPENDED})


@dataclass(frozen=True)
class Entry:
    """One path in the run plan. `detail` is the reason (preserved) or the edit (patched)."""

    path: str
    kind: str
    detail: str = ""


@dataclass(frozen=True)
class Finding:
    """A defect found while checking written bytes.

    `blocking` separates "the bytes we just wrote do not parse or run" (our bug — exit 1)
    from "a generated file points at something absent" (a gap in what the skill ships:
    reported, never a reason to fail a project's update).
    """

    area: str
    detail: str
    remedy: str = ""
    blocking: bool = True


class Report:
    """Collects what a run did and renders it once, in the mode the CLI selected."""

    def __init__(self) -> None:
        self.mode = VERBOSE
        self.cwd = pathlib.Path()
        self.entries: list[Entry] = []
        self.findings: list[Finding] = []
        self.notes: list[str] = []

    def start(self, mode: str, cwd: pathlib.Path) -> None:
        """Begin a run: the plan is per-run state, so a second run never inherits the first."""
        self.mode = mode
        self.cwd = cwd
        self.entries = []
        self.findings = []
        self.notes = []

    # --- rendering primitives: verbose only, so summary/json stay machine-readable ----

    def out(self, text: str) -> None:
        """Write an exact payload (diff, created content) to stdout — verbose only."""
        if self.mode == VERBOSE:
            sys.stdout.write(text)

    def err(self, text: str, *, always: bool = False) -> None:
        """Write a prose line to stderr; `always` for lines no mode may swallow."""
        if always or self.mode == VERBOSE:
            print(text, file=sys.stderr)

    def _rel(self, path: pathlib.Path) -> str:
        try:
            return path.resolve().relative_to(self.cwd).as_posix()
        except ValueError:  # outside the target repo — report the path as given
            return path.as_posix()

    def record(self, path: pathlib.Path, kind: str, detail: str = "") -> None:
        self.entries.append(Entry(self._rel(path), kind, detail))

    # --- file events: each records the kind and prints today's prose when verbose -----

    def unchanged(self, path: pathlib.Path, label: str = "") -> None:
        suffix = f" ({label})" if label else ""
        self.err(f"unchanged  {path}{suffix}")
        self.record(path, UNCHANGED, label)

    def stale(self, path: pathlib.Path, diff: str) -> None:
        self.out(diff)
        self.record(path, STALE)

    def missing(self, path: pathlib.Path, preview: str) -> None:
        self.out(f"would create {path}:\n{preview}")
        self.record(path, MISSING)

    def wrote(self, path: pathlib.Path, *, mixed: bool = False, changed: bool = True) -> None:
        self.err(f"wrote ({'mixed' if mixed else 'deterministic'}) {path}")
        self.record(path, STALE if changed else UNCHANGED)

    def preserved(self, path: pathlib.Path, reason: str) -> str:
        """Report a project-owned file; returns the NEXT note naming it."""
        self.err(f"preserved  {path} ({reason})")
        self.record(path, PRESERVED, reason)
        return f"{self._rel(path)}: preserved — {reason}"

    def patched(
        self, path: pathlib.Path, detail: str, message: str, *, stdout: bool = False
    ) -> None:
        """An append-only or section edit; `stdout` keeps a preview's historical stream."""
        if stdout:
            self.out(f"{message}\n")
        else:
            self.err(message)
        self.record(path, PATCHED, detail)

    def appended(
        self, path: pathlib.Path, detail: str, message: str, *, stdout: bool = False
    ) -> None:
        if stdout:
            self.out(f"{message}\n")
        else:
            self.err(message)
        self.record(path, APPENDED, detail)

    def note(self, message: str) -> None:
        """Information the caller must see in every mode (a NOTE, not a file event)."""
        self.notes.append(message)
        self.err(message, always=True)

    def finding(self, area: str, detail: str, remedy: str = "", *, blocking: bool = True) -> None:
        self.findings.append(Finding(area, detail, remedy, blocking))
        mark = "SELF-CHECK" if blocking else "WARNING (self-check)"
        tail = f" — fix: {remedy}" if remedy else ""
        self.err(f"{mark}: {area}: {detail}{tail}", always=True)

    # --- rendering ------------------------------------------------------------------

    @property
    def drift_entries(self) -> list[Entry]:
        return [e for e in self.entries if e.kind in DRIFT_KINDS]

    @property
    def blocking_findings(self) -> list[Finding]:
        return [f for f in self.findings if f.blocking]

    def paths_of(self, kinds: frozenset[str] | set[str]) -> list[pathlib.Path]:
        """Existing files this run claims — the self-check's targets, real run or preview."""
        found: list[pathlib.Path] = []
        for entry in self.entries:
            if entry.kind in kinds and (self.cwd / entry.path).is_file():
                found.append(self.cwd / entry.path)
        return found

    def render_summary(self, header: str) -> None:
        """One line per path that needs attention, then totals — the `--check` payload."""
        print(header)
        for entry in self.entries:
            if entry.kind == UNCHANGED:
                continue
            detail = f" — {entry.detail}" if entry.detail else ""
            print(f"{entry.kind:<10} {entry.path}{detail}")
        counts: dict[str, int] = {}
        for entry in self.entries:
            counts[entry.kind] = counts.get(entry.kind, 0) + 1
        tally = " · ".join(f"{counts[k]} {k}" for k in sorted(counts))
        print(f"{tally or 'nothing to report'} · drift {len(self.drift_entries)}")

    def plan(self, *, flavor: str, update: bool, dry_run: bool) -> dict[str, object]:
        """The run as data — what `--json` prints instead of prose."""
        return {
            "cwd": str(self.cwd),
            "flavor": flavor,
            "update": update,
            "dry_run": dry_run,
            "drift": bool(self.drift_entries),
            "entries": [asdict(e) for e in self.entries],
            "findings": [asdict(f) for f in self.findings],
            "notes": list(self.notes),
        }


REPORT = Report()


def _declares_pnpm(cwd: pathlib.Path) -> bool:
    """True when the repo's package manager is pnpm — the trigger for the lockfile patch.

    Probed, not assumed: a lockfile, a `packageManager` field, or a workspace file. Without
    this, the assets patch lived in the TypeScript flavor only, so refreshing a pnpm repo
    with `--update` silently put `package-lock.json` back into the release assets.
    """
    if (cwd / "pnpm-lock.yaml").exists() or (cwd / "pnpm-workspace.yaml").exists():
        return True
    try:
        pkg = (cwd / "package.json").read_text(encoding="utf-8")
    except FileNotFoundError:
        return False
    return '"packageManager"' in pkg and "pnpm" in pkg


def _parse_components(raw: str | None, available: set[str], flag: str) -> set[str] | None:
    if raw is None:
        return None
    # allow comma-separated, plus alias normalization for pre-push vs pre_push, changelog vs changelog-script, etc.
    alias = {
        "hooks": "pre-push",
        "hook": "pre-push",
        "pre_push": "pre-push",
        "changelog": "changelog-md",
        "script": "changelog-script",
        "templates": "issue-templates",
        "issues": "issue-templates",
        "pr-template": "pr-template",
        "pr_template": "pr-template",
        "pull-request": "pr-template",
        "pull_request": "pr-template",
        "pullrequest": "pr-template",
    }
    parts = [s.strip() for s in raw.split(",") if s.strip()]
    resolved: set[str] = set()
    for part in parts:
        low = part.lower()
        low = alias.get(low, low)
        if low not in available:
            raise ValueError(
                f"unknown component '{part}' for {flag} (available: {', '.join(sorted(available))})"
            )
        resolved.add(low)
    return resolved


def _resolve_selected(
    only: str | None, without: str | None, components: str | None, available: set[str]
) -> set[str]:
    # --components is alias for --only
    effective_only = components if components is not None else only
    if effective_only is not None:
        sel = _parse_components(effective_only, available, "--only/--components")
        assert sel is not None
    else:
        sel = set(available)
    if without is not None:
        excl = _parse_components(without, available, "--without")
        assert excl is not None
        sel -= excl
    return sel


PYTHON_VERSION = "3.14\n"


def build_pyproject(project_name: str, with_coverage: bool, threshold: int) -> str:
    cov_deps = ', "pytest-cov>=7"' if with_coverage else ""
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
dev = ["pytest>=9", "ruff>=0.16", "basedpyright>=1.40"{cov_deps}]

[tool.ruff]
line-length = 100
target-version = "py314"

# An explicit selection, not the tool's default: ruff >=0.16 defaults to every rule it ships
# (413 of them in 0.16.7) and adds more each release, so a generated repo would go red on a
# lockfile bump nobody could review. `E501` stays off because the formatter owns line length.
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
ignore = ["E501"]

[tool.basedpyright]
typeCheckingMode = "strict"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
{cov_section}"""


def _py_module_name(project_name: str) -> str:
    """`Demo Py` / `demo-py` -> `demo_py`: a module name is an identifier, so no `-`, no
    leading digit, and not a keyword."""
    name = re.sub(r"[^0-9a-zA-Z]+", "_", project_name).strip("_").lower()
    if not name or name[0].isdigit() or keyword.iskeyword(name):
        name = f"pkg_{name}"
    return name


def _ts_normalize_name(project_name: str) -> str:
    return project_name.lower().replace(" ", "-").replace("_", "-")


def build_package_json(
    project_name: str, ts_variant: str, with_coverage: bool, coverage_script: str = "coverage"
) -> str:
    npm_name = _ts_normalize_name(project_name)
    scripts: dict[str, str] = {
        "lint": "oxlint .",
        "format": "oxfmt --check .",
        "format:fix": "oxfmt .",
        "typecheck": "tsc --noEmit",
        "test": "vitest run",
    }
    dev_deps: dict[str, str] = {
        "typescript": "^7",
        "oxlint": "^1",
        # exact, not a range: oxfmt's output is a byte contract (see git-scaffolding)
        "oxfmt": OXFMT_VERSION,
        "vite": "^8",
        "vitest": "^5",
        "tsx": "^4",
        "@types/node": "^26",
        "@semantic-release/changelog": "^7",
        "@semantic-release/commit-analyzer": "^13",
        "@semantic-release/git": "^11",
        "@semantic-release/github": "^12",
        "@semantic-release/npm": "^13",
        "@semantic-release/release-notes-generator": "^14",
        # NOT the latest major: v10 needs conventional-changelog-writer@9+, and
        # @semantic-release/release-notes-generator@14 still loads writer 8.4.0 — the
        # release job then dies at the notes step. v9 is the newest major that renders.
        "conventional-changelog-conventionalcommits": "^9",
        "semantic-release": "^25",
    }
    if with_coverage:
        scripts[coverage_script] = "vitest run --coverage"
        dev_deps["@vitest/coverage-v8"] = "^5"
    pkg: dict[str, object] = {
        "name": npm_name,
        "version": "0.1.0",
        "description": "",
        "type": "module",
        "packageManager": "pnpm@12.4.1",
        "engines": {"node": ">=26"},
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
    return rendered + "\n"


# TypeScript artifacts that need no substitution ship verbatim from `templates/`; index.ts,
# vitest.config.ts and Cargo.toml are `.j2` templates rendered at their call sites.

# CI release workflow — one base (`ci/release.yml.j2`) plus one fragment per runtime, so
# adding a runtime costs one registry entry and one file while the coverage axis stays a
# branch inside the fragment. `--ci-variant` takes its choices from here.
CI_RUNTIMES: dict[str, str] = {
    "node": "ci/runtimes/node.yml.j2",
    "python": "ci/runtimes/python.yml.j2",
    "rust": "ci/runtimes/rust.yml.j2",
}


def infer_project_name(cwd: pathlib.Path) -> str:
    try:
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


class FormatterUnavailable(RuntimeError):
    """The pinned formatter could not run, so the bytes it owns would ship uncanonical."""


# Module-private mutable state, not constants: `enable_formatter` sets the root for the run
# and `canonicalize` memoizes the temp config it writes. Lowercase on purpose — pyright reads an
# UPPERCASE name as a constant and rejects the reassignment (reportConstantRedefinition).
_formatter_root: pathlib.Path | None = None
_formatter_config: pathlib.Path | None = None
_formatter_tmp: tempfile.TemporaryDirectory[str] | None = None


def enable_formatter(root: pathlib.Path) -> None:
    """Let `canonicalize` run for this session.

    Enabled for every flavor, not only the one that ships the formatter: oxfmt's reach spans
    files several flavors own, so an opt-in pass made the bytes depend on *how the run was
    split*. Reproduced before this fix — `--flavor all` followed by `--update --flavor git`
    left `.releaserc.json` uncanonical, and `--flavor typescript` followed by
    `--flavor ci --ci-variant node` left `release.yml` uncanonical, so the generated repo's
    own `pnpm run format` gate went red on bytes no run had canonicalized.
    `--no-format` / `SCAFFOLD_NO_FORMAT=1` is the opt-out for a run without Node.
    """
    global _formatter_root
    _formatter_root = root.resolve()
    print(
        f"formatting: oxfmt@{OXFMT_VERSION} owns the bytes it can reach (see OXFMT_VERSION)",
        file=sys.stderr,
    )


def canonicalize(path: pathlib.Path, content: str) -> str:
    """Return `content` exactly as the pinned formatter would write it.

    This runs at the single write seam, so `--dry-run`, `--update` and the `unchanged`
    compare all see canonical bytes; a formatter pass over the tree afterwards would make
    the preview and the idempotence check disagree with what actually lands.
    """
    if _formatter_root is None or path.suffix.lower() not in OXFMT_EXTENSIONS:
        return content
    global _formatter_config, _formatter_tmp
    if _formatter_config is None:
        # The shipped config, so the result never depends on whether .oxfmtrc.json has been
        # written yet — and its ignorePatterns keep CHANGELOG.md (MD004 `*` pin) untouched.
        _formatter_tmp = tempfile.TemporaryDirectory(prefix="scaffold-oxfmt-")
        _formatter_config = pathlib.Path(_formatter_tmp.name) / "oxfmtrc.json"
        _formatter_config.write_text(OXFMT_JSON, encoding="utf-8")
    try:
        rel = path.resolve().relative_to(_formatter_root)
    except ValueError:
        rel = pathlib.Path(path.name)
    cmd = [
        "npx",
        "--yes",
        f"oxfmt@{OXFMT_VERSION}",
        "-c",
        str(_formatter_config),
        "--stdin-filepath",
        rel.as_posix(),
    ]
    try:
        proc = subprocess.run(
            cmd, input=content, capture_output=True, text=True, cwd=str(_formatter_root)
        )
    except OSError as exc:
        raise FormatterUnavailable(f"{cmd[0]} not runnable: {exc}") from exc
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
        raise FormatterUnavailable(f"oxfmt@{OXFMT_VERSION} failed on {rel}: {detail}")
    return proc.stdout


def write_file(
    path: pathlib.Path, content: str, dry_run: bool, *, warn_mixed: str | None = None
) -> bool:
    """Write (or preview) one generated artifact and report it in the run plan.

    Returns True when the file was written. Previews go through REPORT so `--summary`
    and `--json` drop the prose and keep the plan instead.
    """
    is_mixed = warn_mixed is not None
    content = canonicalize(path, content)
    if dry_run:
        if path.exists():
            old = path.read_text(encoding="utf-8")
            if old == content:
                REPORT.unchanged(path)
            else:
                diff = difflib.unified_diff(
                    old.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile=str(path),
                    tofile=str(path) + " (new)",
                )
                REPORT.stale(path, "".join(diff))
        else:
            REPORT.missing(path, content)
        if is_mixed:
            REPORT.err(f"WARNING (dry-run): {path}: {warn_mixed}")
        return False
    changed = not path.exists() or path.read_text(encoding="utf-8") != content
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    REPORT.wrote(path, mixed=is_mixed, changed=changed)
    if is_mixed:
        REPORT.err(f"WARNING: {path}: {warn_mixed}")
    return True


def preserve(path: pathlib.Path, reason: str) -> str:
    """Report a project-owned file preserved by --update; returns its NEXT note."""
    return REPORT.preserved(path, reason)


def write_generated(
    path: pathlib.Path,
    content: str,
    dry_run: bool,
    *,
    update: bool = False,
    warn_mixed: str | None = None,
) -> str | None:
    """write_file, minus project-owned files when --update is running.

    Update refreshes generated infrastructure byte-identically and preserves what
    the project owns (see PROJECT_OWNED); the returned note feeds the NEXT block.
    """
    reason = PROJECT_OWNED.get(path.name) if update else None
    if reason and path.exists():
        return preserve(path, reason)
    write_file(path, content, dry_run, warn_mixed=warn_mixed)
    return None


def append_gitignore(path: pathlib.Path, entries: list[str], dry_run: bool) -> None:
    """Add missing ignore lines; never rewrites what is already there."""
    existed = path.exists()
    existing: set[str] = set()
    if existed:
        existing = {
            ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()
        }
    missing = [e for e in entries if e not in existing]
    if not missing:
        REPORT.unchanged(path, "gitignore dedup")
        return
    if dry_run:
        REPORT.appended(
            path, f"would add {missing}", f"would append to {path}: {missing}", stdout=True
        )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        if existed and path.stat().st_size > 0:
            content = path.read_text(encoding="utf-8")
            if not content.endswith("\n"):
                handle.write("\n")
        for entry in missing:
            handle.write(entry + "\n")
    verb = "added" if existed else "created"
    REPORT.appended(path, f"{verb} {missing}", f"appended ({len(missing)}) to {path}: {missing}")


def patch_agents(path: pathlib.Path, snippet: str, dry_run: bool) -> None:
    """Append the runtime pointer when it is absent — never rewrites existing sections."""
    # Canonicalize the snippet, never the whole file: an append must not reformat headings or
    # prose the project already had. The junction stays canonical because the snippet opens
    # with its own heading and the append below guarantees a blank line in front of it.
    snippet = canonicalize(path, snippet.rstrip() + "\n")
    marker = snippet.strip().splitlines()[0][:40]
    proofread = "proofread — keep existing 3 sections, verify pointer wording."
    if dry_run:
        if path.exists():
            body = path.read_text(encoding="utf-8")
            if marker.strip("# ") in body or snippet.strip() in body:
                REPORT.unchanged(path, "AGENTS patch present")
            else:
                REPORT.patched(
                    path,
                    "would append runtime pointer",
                    f"would patch {path} with:\n{snippet}",
                    stdout=True,
                )
        else:
            REPORT.missing(path, snippet)
        REPORT.err(f"WARNING (dry-run): {path}: {proofread}")
        return
    if path.exists():
        body = path.read_text(encoding="utf-8")
        if snippet.strip() in body or marker.strip("# ") in body:
            REPORT.unchanged(path, "AGENTS patch present")
            REPORT.err(f"WARNING: {path}: {proofread}")
            return
        with path.open("a", encoding="utf-8") as handle:
            if not body.endswith("\n"):
                handle.write("\n")
            if not body.endswith("\n\n"):
                handle.write("\n")
            handle.write(snippet.rstrip() + "\n")
        REPORT.patched(path, "appended runtime pointer", f"patched {path} (mixed)")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(snippet, encoding="utf-8")
        REPORT.wrote(path, mixed=True, changed=True)
    REPORT.err(f"WARNING: {path}: {proofread}")


def patch_wt_hooks(cwd: pathlib.Path, dry_run: bool) -> None:
    """Ensure worktrees get live hooks — `wt switch` clones a fresh checkout, not the config."""
    wt = cwd / ".config/wt.toml"
    if not wt.exists():
        return
    text = wt.read_text(encoding="utf-8")
    if "core.hooksPath" in text:
        REPORT.unchanged(wt, "hooksPath present")
        return
    hook_line = 'setup-hooks = "git config core.hooksPath .githooks"'
    if dry_run:
        REPORT.patched(
            wt, "would add setup-hooks", f"would patch {wt} with {hook_line}", stdout=True
        )
        return
    if "[post-start]" in text:
        lines: list[str] = []
        inserted = False
        for line in text.splitlines():
            lines.append(line)
            if not inserted and line.strip() == "[post-start]":
                lines.append(hook_line)
                inserted = True
        if not inserted:
            lines.extend(["[post-start]", hook_line])
        new_text = "\n".join(lines) + "\n"
        new_text = new_text.replace("\n\n\n", "\n\n")
    else:
        new_text = text.rstrip() + "\n\n[post-start]\n" + hook_line + "\n"
    wt.write_text(new_text, encoding="utf-8")
    REPORT.patched(wt, "added setup-hooks", f"patched {wt} with hooksPath")


def patch_releaserc_lockfile(cwd: pathlib.Path, dry_run: bool) -> None:
    """pnpm contract: a repo that declares pnpm ships pnpm-lock.yaml in the release assets.

    Gated on the repo, not on the flavor — the assets line is a property of the package
    manager. Before this, only the TypeScript flavor patched it, so a pnpm repo refreshed
    with `--update` silently put `package-lock.json` back into its release assets.
    """
    path = cwd / ".releaserc.json"
    if not path.exists():
        REPORT.err(
            f"NOTE: no {path} — run the git flavor first so the pnpm lockfile patch has a target"
        )
        return
    text = path.read_text(encoding="utf-8")
    if '"package-lock.json"' not in text:
        REPORT.unchanged(path, "releaserc lockfile already pnpm")
        return
    if not _declares_pnpm(cwd):
        return
    if dry_run:
        REPORT.patched(
            path,
            "package-lock.json → pnpm-lock.yaml",
            f"would patch {path}: package-lock.json → pnpm-lock.yaml (pnpm contract)",
            stdout=True,
        )
        return
    path.write_text(text.replace('"package-lock.json"', '"pnpm-lock.yaml"'), encoding="utf-8")
    REPORT.patched(
        path,
        "package-lock.json → pnpm-lock.yaml",
        f"patched {path}: package-lock.json → pnpm-lock.yaml (pnpm contract)",
    )


def render_ci_release(
    variant: str, with_coverage: bool, threshold: int, coverage_script: str = "coverage"
) -> str:
    """Render .github/workflows/release.yml for one CI runtime variant."""
    return render_template(
        CI_RUNTIMES[variant],
        shas=SHA_TABLE,
        node_version=NODE_VERSION_NUM,
        gh_actions_token=GH_ACTIONS_TOKEN,
        with_coverage=with_coverage,
        threshold=threshold,
        coverage_script=coverage_script,
    )


def do_git(
    cwd: pathlib.Path,
    project_name: str,
    dry_run: bool,
    selected: set[str] | None = None,
    update: bool = False,
    merge_mixed: bool = False,
) -> list[str]:
    """Ship the git contract: release config, workflows, hooks, changelog, router."""
    # finer granularity: default all, filtered by --only/--without/--components
    sel = selected if selected is not None else GIT_COMPONENTS
    notes: list[str] = []
    if "releaserc" in sel:
        write_file(cwd / ".releaserc.json", releaserc_content(cwd), dry_run)
    if "release-yml" in sel:
        rel = cwd / ".github" / "workflows" / "release.yml"
        if update and rel.exists():
            notes.append(preserve(rel, FLAVOR_FOREIGN["release-yml"]))
        else:
            write_file(
                rel,
                render_ci_release(
                    "node", with_coverage=False, threshold=DEFAULT_COVERAGE_THRESHOLD
                ),
                dry_run,
            )
    if "changelog-check" in sel:
        write_file(
            cwd / ".github" / "workflows" / "changelog-check.yml", CHANGELOG_CHECK_YML, dry_run
        )
    if "pre-push" in sel:
        write_file(cwd / ".githooks" / "pre-push", GITHOOK_PRE_PUSH, dry_run)
        write_file(cwd / ".husky" / "pre-push", HUSKY_PRE_PUSH, dry_run)
    if "pre-push" in sel and not dry_run:
        for _hook in (cwd / ".githooks" / "pre-push", cwd / ".husky" / "pre-push"):
            try:
                _hook.chmod(0o755)
            except OSError:  # best-effort chmod, ignore on read-only FS
                pass
    if "changelog-script" in sel:
        write_file(cwd / "scripts" / "changelog-unreleased.py", CHANGELOG_UNRELEASED_PY, dry_run)
    if "commitlint" in sel:
        write_file(cwd / "commitlint.config.js", COMMITLINT_JS, dry_run)
    if "changelog-md" in sel:
        note = write_generated(cwd / "CHANGELOG.md", CHANGELOG_MD, dry_run, update=update)
        if note:
            notes.append(note)
    if "issue-templates" in sel:
        write_file(
            cwd / ".github" / "ISSUE_TEMPLATE" / "01-bug_report.yml", ISSUE_BUG_REPORT_YML, dry_run
        )
        write_file(
            cwd / ".github" / "ISSUE_TEMPLATE" / "02-feature_request.yml",
            ISSUE_FEATURE_REQUEST_YML,
            dry_run,
        )
        write_file(cwd / ".github" / "ISSUE_TEMPLATE" / "config.yml", ISSUE_CONFIG_YML, dry_run)
    if "pr-template" in sel:
        write_file(cwd / ".github" / "pull_request_template.md", PULL_REQUEST_TEMPLATE_MD, dry_run)
    # migrate legacy markdown template (pre-YAML) — keep spine small
    legacy_md = cwd / ".github" / "ISSUE_TEMPLATE" / "bug_report.md"
    if legacy_md.exists():
        if dry_run:
            REPORT.out(f"would remove legacy {legacy_md} (migrated to 01-bug_report.yml)\n")
        else:
            try:
                legacy_md.unlink()
                REPORT.err(f"removed legacy {legacy_md} (migrated to 01-bug_report.yml)")
            except OSError:
                pass
    if "contributing" in sel:
        contrib = render_template("shared/CONTRIBUTING.default.md.j2", project_name=project_name)
        note = write_contributing(
            cwd,
            contrib,
            dry_run,
            warn_mixed="mixed: contains {{project_name}} + toolchain 'Before PR' line — proofread project name and lint/test commands.",
            update=update,
            merge_mixed=merge_mixed,
        )
        if note:
            notes.append(note)
    if "gitignore" in sel:
        append_gitignore(cwd / ".gitignore", GITIGNORE_GIT, dry_run)
    if "agents" in sel:
        patch_agents(
            cwd / "AGENTS.md",
            "### Contribution\nConventional commits & changelog: see CONTRIBUTING.md\nGit hooks: `git config core.hooksPath .githooks` (or `npm install` with husky → `.husky` delegates to `.githooks`) so pre-push CHANGELOG guard is live on fresh clone/worktree.\n",
            dry_run,
        )
    if "pre-push" in sel:
        patch_wt_hooks(cwd, dry_run)
    return notes


def do_python(
    cwd: pathlib.Path,
    project_name: str,
    dry_run: bool,
    with_coverage: bool,
    threshold: int,
    update: bool = False,
) -> list[str]:
    notes: list[str] = []
    write_file(cwd / ".python-version", PYTHON_VERSION, dry_run)
    module = _py_module_name(project_name)
    for relative, content in (
        (
            f"src/{module}/__init__.py",
            render_template("python/src/_pkg/__init__.py.j2", project_name=project_name),
        ),
        ("tests/test_smoke.py", render_template("python/tests/test_smoke.py.j2", module=module)),
    ):
        note = write_source(cwd, relative, content, dry_run, update=update)
        if note:
            notes.append(note)
    pyproj = build_pyproject(project_name, with_coverage, threshold)
    warn = (
        f"mixed: {{{{project_name}}}} + coverage gate {threshold}% — proofread name and fail_under"
        if with_coverage
        else "mixed: {{project_name}} + description/readme — proofread package name and description."
    )
    note = write_generated(
        cwd / "pyproject.toml",
        pyproj,
        dry_run,
        update=update,
        warn_mixed=warn,
    )
    if note:
        notes.append(note)
        notes.append(
            "pyproject.toml: user-owned — per-field edits via `uv run $SKILL_DIR/scripts/scaffold.py ensure py-dep --req ...` / `uv run $SKILL_DIR/scripts/scaffold.py ensure coverage-threshold --flavor python --value N`"
        )
    append_gitignore(cwd / ".gitignore", GITIGNORE_GIT + GITIGNORE_PYTHON_EXTRA, dry_run)
    patch_agents(
        cwd / "AGENTS.md",
        "### Runtime\nPython: uv + .python-version (3.14), run via uv run; see pyproject.toml\n",
        dry_run,
    )
    contrib_py = render_template("shared/CONTRIBUTING.python.md.j2", project_name=project_name)
    note = write_generated(
        cwd / "CONTRIBUTING.md",
        contrib_py,
        dry_run,
        update=update,
        warn_mixed="mixed: contains {{project_name}} + toolchain 'Before PR' line — proofread project name and lint/test commands.",
    )
    if note:
        notes.append(note)
    if with_coverage:
        print(
            f"NOTE: Python coverage wired — run `uv run pytest --cov --cov-fail-under={threshold}`",
            file=sys.stderr,
        )
    return notes


def do_rust(
    cwd: pathlib.Path,
    project_name: str,
    dry_run: bool,
    with_coverage: bool,
    threshold: int,
    update: bool = False,
) -> list[str]:
    notes: list[str] = []
    cargo_name = project_name.lower().replace("_", "-").replace(" ", "-")
    if cargo_name != project_name:
        print(
            f"WARNING: Cargo package name normalized to '{cargo_name}' (from '{project_name}') — proofread Cargo.toml name.",
            file=sys.stderr,
        )
    write_file(cwd / "rust-toolchain.toml", RUST_TOOLCHAIN_TOML, dry_run)
    note = write_source(cwd, "src/lib.rs", RUST_LIB_RS, dry_run, update=update)
    if note:
        notes.append(note)
    cargo = render_template("rust/Cargo.toml.j2", project_name=cargo_name)
    warn = "mixed: {{project_name}} normalized to kebab-case — proofread package name and edition."
    if with_coverage:
        warn += f" + coverage llvm-cov {threshold}%"
    note = write_generated(
        cwd / "Cargo.toml",
        cargo,
        dry_run,
        update=update,
        warn_mixed=warn,
    )
    if note:
        notes.append(note)
        notes.append(
            "Cargo.toml: user-owned — per-field edits via `uv run $SKILL_DIR/scripts/scaffold.py ensure rust-dep --name ... [--version ...]`"
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
    return notes


def do_typescript(
    cwd: pathlib.Path,
    project_name: str,
    dry_run: bool,
    ts_variant: str,
    with_coverage: bool,
    threshold: int,
    coverage_script: str = "coverage",
    update: bool = False,
    merge_mixed: bool = False,
) -> list[str]:
    """Ship the Node/pnpm toolchain projection: configs, entry skeleton, CONTRIBUTING."""
    notes: list[str] = []
    npm_name = _ts_normalize_name(project_name)
    if npm_name != project_name:
        REPORT.err(
            f"WARNING: npm package name normalized to '{npm_name}' (from '{project_name}') — proofread package.json name."
        )
    write_file(cwd / ".nvmrc", NODE_VERSION, dry_run)
    pkg_json = build_package_json(project_name, ts_variant, with_coverage, coverage_script)
    warn = "mixed: {{project_name}} + description — proofread package name and description."
    if with_coverage:
        warn += f" + coverage @vitest/coverage-v8 {threshold}%"
    note = write_generated(cwd / "package.json", pkg_json, dry_run, update=update, warn_mixed=warn)
    if note:
        notes.append(note)
        notes.append(
            "package.json: user-owned — per-field edits via `uv run $SKILL_DIR/scripts/scaffold.py ensure ts-dep/ts-script ...`"
        )
    note = write_source(cwd, "tsconfig.json", build_tsconfig(), dry_run, update=update)
    if note:
        notes.append(note)
    note = write_source(cwd, ".oxlintrc.json", OXLINT_JSON, dry_run, update=update)
    if note:
        notes.append(note)
    write_file(cwd / "scripts" / "oxlint-plugin-comment-gate.js", OXLINT_COMMENT_GATE_JS, dry_run)
    note = write_source(cwd, ".oxfmtrc.json", OXFMT_JSON, dry_run, update=update)
    if note:
        notes.append(note)
    for relative, content in (
        ("src/index.ts", render_template("typescript/src/index.ts.j2", project_name=npm_name)),
        ("tests/index.test.ts", INDEX_TEST_TS),
    ):
        entry_note = write_source(cwd, relative, content, dry_run, update=update)
        if entry_note:
            notes.append(entry_note)
    if ts_variant == "cli":
        note = write_source(cwd, "src/cli.ts", CLI_TS, dry_run, update=update)
        if note:
            notes.append(note)
        if not dry_run:
            try:
                (cwd / "src" / "cli.ts").chmod(0o755)
            except OSError:
                pass
    if with_coverage:
        note = write_source(
            cwd,
            "vitest.config.ts",
            render_template("typescript/vitest.config.ts.j2", threshold=threshold),
            dry_run,
            update=update,
        )
        if note:
            notes.append(note)
        REPORT.note(
            f"NOTE: TypeScript coverage wired — run `pnpm run {coverage_script}` (fail_under lines/functions {threshold}%)"
        )
    patch_releaserc_lockfile(cwd, dry_run)
    append_gitignore(cwd / ".gitignore", GITIGNORE_GIT + GITIGNORE_TS_EXTRA, dry_run)
    patch_agents(
        cwd / "AGENTS.md",
        "### Runtime\nTypeScript: pnpm v12 + .nvmrc (26) + TS v7 + Vite v8, verify via oxlint/oxfmt/tsc/vitest; see package.json\n",
        dry_run,
    )
    contrib_ts = render_template("shared/CONTRIBUTING.typescript.md.j2", project_name=project_name)
    note = write_contributing(
        cwd,
        contrib_ts,
        dry_run,
        warn_mixed="mixed: contains {{project_name}} + toolchain 'Before PR' line — proofread project name and lint/test commands.",
        update=update,
        merge_mixed=merge_mixed,
    )
    if note:
        notes.append(note)
    if ts_variant == "pi-extension":
        REPORT.note(
            "NOTE: pi-extension entry is ./src/index.ts (pi loads .ts directly, no build step) — proofread package.json `pi.extensions` path."
        )
    return notes


def do_ci(
    cwd: pathlib.Path,
    dry_run: bool,
    variant: str,
    with_coverage: bool,
    threshold: int,
    selected: set[str] | None = None,
    coverage_script: str = "coverage",
    update: bool = False,
) -> list[str]:
    sel = selected if selected is not None else CI_COMPONENTS
    if "release-yml" not in sel:
        return []
    rel = cwd / ".github" / "workflows" / "release.yml"
    if update and rel.exists():
        return [preserve(rel, FLAVOR_FOREIGN["release-yml"])]
    content = render_ci_release(
        variant, with_coverage=with_coverage, threshold=threshold, coverage_script=coverage_script
    )
    if variant == "node" and with_coverage:
        print(
            f"NOTE: Node/TS coverage runs `pnpm run {coverage_script}` in verify — thresholds owned by vitest.config.ts (run typescript flavor with --with-coverage to generate it)",
            file=sys.stderr,
        )
    write_file(cwd / ".github" / "workflows" / "release.yml", content, dry_run)
    return []


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
        ".oxlintrc.json": exists(".oxlintrc.json"),
        ".oxfmtrc.json": exists(".oxfmtrc.json"),
        "oxlint.json": exists("oxlint.json"),
        "oxfmt.json": exists("oxfmt.json"),
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
        ".github/pull_request_template.md": exists(".github/pull_request_template.md"),
    }

    pyproject = read_text("pyproject.toml")
    release_yml = read_text(".github/workflows/release.yml")
    changelog = read_text("CHANGELOG.md")
    releaserc = read_text(".releaserc.json")
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
    # Name-agnostic: any script whose command matches vitest.*--coverage counts,
    # whatever the key is called (coverage, test:coverage, cov, test) — but only
    # when the key itself has the shared coverage-script shape, so detect and
    # generation (which falls back past invalid names) can never disagree.
    node_coverage_script: str | None = None
    try:
        _pkg_data = json.loads(pkg_json) if pkg_json else {}
        _pkg_scripts = _pkg_data.get("scripts", {}) if isinstance(_pkg_data, dict) else {}
    except ValueError:
        _pkg_scripts = {}
    if not isinstance(_pkg_scripts, dict):
        _pkg_scripts = {}
    if isinstance(_pkg_scripts, dict):
        for _name, _cmd in _pkg_scripts.items():
            if (
                isinstance(_name, str)
                and isinstance(_cmd, str)
                and _is_coverage_script_name(_name)
                and re.search(r"vitest.*--coverage", _cmd)
            ):
                node_coverage_script = _name
                break
    ts_coverage = (
        node_coverage_script is not None
        or "coverage" in vitest_config
        or "@vitest/coverage" in pkg_json
    )
    ts_coverage_threshold: int | None = None
    m_ts = re.search(r"lines:\s*(\d+)", vitest_config)
    if m_ts:
        try:
            ts_coverage_threshold = int(m_ts.group(1))
        except ValueError:
            ts_coverage_threshold = None
    if ts_coverage_threshold is None:
        for _cmd in _pkg_scripts.values():
            if not isinstance(_cmd, str):
                continue
            m_inline = re.search(r"coverage\.thresholds\.lines=(\d+)", _cmd)
            if m_inline:
                try:
                    ts_coverage_threshold = int(m_inline.group(1))
                except ValueError:
                    ts_coverage_threshold = None
                break
    if not ts_coverage:
        ts_coverage_threshold = None
    ci_coverage = (
        "--cov" in release_yml
        or "llvm-cov" in release_yml
        or "fail-under" in release_yml
        or "--coverage" in release_yml
        or (
            node_coverage_script is not None
            and f"pnpm run {node_coverage_script}" in release_yml
        )
    )
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
    changelog_lines = changelog.splitlines()
    title_line = next(
        (n for n, line in enumerate(changelog_lines, 1) if line.strip() == "# Changelog"), 0
    )
    title_at_top = bool(changelog) and changelog.lstrip().startswith("# Changelog")

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
            re.search(
                r"ruff.*format|cargo fmt|prettier|biome|oxfmt", pyproject + release_yml + pkg_json
            )
        ),
        "linter": bool(
            re.search(
                r"ruff check|clippy|eslint|biome|oxlint",
                pyproject + release_yml + pkg_json,
                re.IGNORECASE,
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

    # Findings are the difference between a census and a task list: detection already knows
    # these are wrong, so it names the remedy instead of making the caller re-derive it.
    findings: list[dict[str, str]] = []

    def finding(area: str, detail: str, remedy: str) -> None:
        findings.append({"area": area, "detail": detail, "remedy": remedy})

    scaffold_root = pathlib.Path(__file__).parent.parent
    if git_stale:
        finding(
            ".github/workflows/changelog-check.yml",
            "absent — the CHANGELOG guard has no CI half",
            f"uv run {scaffold_root}/scripts/scaffold.py --update --only changelog-check",
        )
    if node_present and not files[".github/pull_request_template.md"]:
        finding(
            ".github/pull_request_template.md",
            "absent — PR bodies lose the checklist and impact/risk line",
            f"uv run {scaffold_root}/scripts/scaffold.py --update --only pr-template",
        )
    if changelog and not git_stale:
        # Both defects are real and independent: a release needs the heading *and* a title the
        # plugin can anchor on, so one must never mask the other.
        if "## [Unreleased]" not in changelog:
            finding(
                "CHANGELOG.md",
                "no `## [Unreleased]` section — the pre-push guard has nothing to update",
                "uv run python scripts/changelog-unreleased.py update",
            )
        if not title_at_top:
            finding(
                "CHANGELOG.md",
                f"`# Changelog` title sits at line {title_line}, so each release prepends its notes above it",
                "move `# Changelog` to the FIRST line of CHANGELOG.md AND set "
                '"changelogTitle": "# Changelog" in .releaserc.json — @semantic-release/changelog '
                "rewrites the title in place only while the file starts with it, and prepends "
                "release notes above it otherwise (the pair is the fix)",
            )
    if files[".releaserc.json"] and '"package-lock.json"' in releaserc and _declares_pnpm(cwd):
        finding(
            ".releaserc.json",
            "release assets name package-lock.json but the repo declares pnpm",
            f"uv run {scaffold_root}/scripts/scaffold.py --update",
        )
    # The harness repo is the *source* of these skills — `~/.agents/skills/<name>` symlinks
    # back into it — so `skills/<name>` there is the canonical copy. Reporting it as a vendored
    # duplicate would advise deleting the original.
    is_harness = scaffold_root.resolve() == (cwd / "skills" / "scaffold").resolve()
    vendored_skill = cwd / "skills" / "gh-router"
    if vendored_skill.exists() and not is_harness:
        # A sibling skill copied into a repo is a duplicate that drifts from the harness
        # original; scaffold no longer writes it, and must not delete it either (it may be
        # project content). Report the decision instead of guessing it.
        finding(
            "skills/gh-router",
            "vendored copy of a harness skill — scaffold no longer manages this path",
            "git rm -r skills/gh-router (pi discovers gh-router from ~/.agents/skills), "
            "or keep it as project content",
        )

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
            "coverage_script": node_coverage_script,
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
            "title_at_top": bool(changelog) and changelog.lstrip().startswith("# Changelog"),
            "title_line": title_line,
        },
        "verify_gates": verify_gates,
        "findings": findings,
    }
    return result


def print_detect(cwd: pathlib.Path, as_json: bool) -> int:
    """Census + findings. JSON always goes to stdout; `--json` drops the human summary."""
    data = detect_project(cwd)
    print(json.dumps(data, indent=2, sort_keys=True))
    if as_json:
        return 0
    # `detect_project` returns the census as `dict[str, object]` — one shape for JSON, prose and
    # tests. Narrowing at the printer is the fix (the values are built right here); ignoring the
    # unknown types only moved the guess into the checker.
    files = cast("dict[str, bool]", data["files"])
    print(f"\n# Detect summary for {cwd}", file=sys.stderr)
    print(f"shape={data['inferred_shape']} project={data['project_name']}", file=sys.stderr)
    present = [k for k, v in files.items() if v]
    missing = [k for k, v in files.items() if not v]
    print(f"present: {', '.join(present) if present else '(none)'}", file=sys.stderr)
    print(f"missing: {', '.join(missing) if missing else '(none)'}", file=sys.stderr)
    findings = cast("list[dict[str, str]]", data["findings"])
    if findings:
        print(f"\nfindings ({len(findings)}):", file=sys.stderr)
        for item in findings:
            print(f"  - {item['area']}: {item['detail']}", file=sys.stderr)
            print(f"    → {item['remedy']}", file=sys.stderr)
    return 0


def print_next_actions(cwd: pathlib.Path, notes: list[str]) -> None:
    """Report what --update preserved and the concrete follow-up for each.

    Detection supplies the runtime; the remaining calls are judgement, so they are
    printed rather than guessed (see the Update section of the git subskill).
    """
    if not notes:
        return
    det = detect_project(cwd)
    ci = det["ci"]
    ci_variant = ci.get("variant") if isinstance(ci, dict) else None
    shape = det["inferred_shape"]
    variant = ci_variant if ci_variant in CI_RUNTIMES else shape
    follow_up: dict[str, str] = {
        "release.yml": f"uv run $SKILL_DIR/scripts/scaffold.py --flavor ci --ci-variant {variant}",
        "CONTRIBUTING.md": "add the sections the note lists, or re-run with --merge-mixed to insert them (existing lines untouched) — templates/shared/CONTRIBUTING.{default,python,typescript}.md.j2",
        "CHANGELOG.md": "nothing to do — @semantic-release/changelog owns versioned sections",
        "pyproject.toml": "regenerate deliberately: --flavor python [--with-coverage --coverage-threshold N]",
        "Cargo.toml": "regenerate deliberately: --flavor rust [--with-coverage --coverage-threshold N]",
        "package.json": "regenerate deliberately: --flavor typescript [--ts-variant lib|cli|pi-extension]",
    }
    print("\nNEXT — undetermined, decide before acting:", file=sys.stderr)
    for note in notes:
        print(f"  - {note}", file=sys.stderr)
        action = follow_up.get(note.split(":")[0].strip())
        if action:
            print(f"    → {action}", file=sys.stderr)


# ------------------------------------------------------------------ mixed files
# CONTRIBUTING.md (and AGENTS.md) are project-owned *and* template-derived: the project's
# wording wins, but the template's sections must not silently go missing. Parsing by `## `
# heading keeps the merge additive — a missing section is inserted in template order and no
# existing line is touched, so a human still proofreads prose instead of the tool rewriting it.
SECTION_RE = re.compile(r"^## (?!#)(.+)$", re.MULTILINE)

# `scripts/…` references a generated file must resolve: a hook or workflow that names a script
# nobody ships fails at the worst moment, and the gap survives review because it spans files.
REFERENCE_RE = re.compile(r"(?:[\w.-]+/)*scripts/[\w.-]+\.(?:sh|py)")

SCRIPT_NAMES = {"pre-push", "pre-commit", "pre-merge-commit", "commit-msg", "post-commit"}


def template_sections(text: str) -> list[tuple[str, str]]:
    """Split a markdown template into (heading, body) pairs at `## ` level."""
    matches = list(SECTION_RE.finditer(text))
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.append((match.group(1).strip(), text[match.start() : end].rstrip() + "\n"))
    return sections


def missing_sections(existing: str, template: str) -> list[str]:
    """Template `## ` headings absent from the file, in template order."""
    present = {heading for heading, _ in template_sections(existing)}
    return [heading for heading, _ in template_sections(template) if heading not in present]


def merge_missing_sections(path: pathlib.Path, template: str, dry_run: bool) -> bool:
    """Insert the template's absent sections; every existing line survives verbatim.

    Each missing section lands before the first existing section the template places after
    it, else at the end — so the file keeps the template's order without a rewrite.
    """
    existing = path.read_text(encoding="utf-8")
    wanted = template_sections(template)
    order = {heading: index for index, (heading, _) in enumerate(wanted)}
    present = [(match.group(1).strip(), match.start()) for match in SECTION_RE.finditer(existing)]
    present_headings = {heading for heading, _ in present}
    absent = [heading for heading, _ in wanted if heading not in present_headings]
    if not absent:
        REPORT.unchanged(path, "all template sections present")
        return False
    inserts: dict[int, list[str]] = {}
    for heading, body in wanted:
        if heading in present_headings:
            continue
        offset = len(existing)
        for present_heading, present_offset in present:
            if order[present_heading] > order[heading]:
                offset = present_offset
                break
        inserts.setdefault(offset, []).append(body)
    merged = existing
    for offset in sorted(inserts, reverse=True):
        block = "\n".join(part.rstrip("\n") for part in inserts[offset]) + "\n"
        before = merged[:offset].rstrip("\n")
        after = merged[offset:].lstrip("\n")
        merged = f"{before}\n\n{block}\n{after}"
    if not merged.endswith("\n"):
        merged += "\n"
    if dry_run:
        diff = difflib.unified_diff(
            existing.splitlines(keepends=True),
            merged.splitlines(keepends=True),
            fromfile=str(path),
            tofile=str(path) + " (merged)",
        )
        REPORT.stale(path, "".join(diff))
        return False
    path.write_text(merged, encoding="utf-8")
    REPORT.patched(
        path, f"merged {', '.join(absent)}", f"merged {len(absent)} section(s) into {path} (mixed)"
    )
    return True


def write_contributing(
    cwd: pathlib.Path,
    content: str,
    dry_run: bool,
    *,
    warn_mixed: str,
    update: bool = False,
    merge_mixed: bool = False,
) -> str | None:
    """Write CONTRIBUTING.md, or report what a preserved copy is missing.

    `--merge-mixed` is opt-in because prose is a semantic surface: the default path names
    the absent sections and leaves the merge to judgement.
    """
    path = cwd / "CONTRIBUTING.md"
    if not (update and path.exists()):
        write_file(path, content, dry_run, warn_mixed=warn_mixed)
        return None
    reason = PROJECT_OWNED["CONTRIBUTING.md"]
    absent = missing_sections(path.read_text(encoding="utf-8"), content)
    if not absent:
        return preserve(path, reason)
    if merge_mixed:
        merge_missing_sections(path, content, dry_run)
        return None
    return f"{path.name}: preserved — {reason}; missing template sections: {', '.join(absent)}"


def releaserc_content(cwd: pathlib.Path) -> str:
    """The release config this repo's package manager calls for.

    `.releaserc.json` ships a `package-lock.json` asset (the npm default); a pnpm repo needs
    `pnpm-lock.yaml` there. Resolving it *before* the write keeps `--check` honest — the plan
    compares the repo against the bytes the run would really produce, not against the raw
    template, so a pnpm repo stops reporting permanent drift.
    """
    if _declares_pnpm(cwd):
        return RELEASERC_JSON.replace('"package-lock.json"', '"pnpm-lock.yaml"')
    return RELEASERC_JSON


def write_source(
    cwd: pathlib.Path, relative: str, content: str, dry_run: bool, *, update: bool = False
) -> str | None:
    """Write generated source — unless --update is refreshing a repo that owns the file.

    SOURCE_OWNED marks the difference between "the scaffold ships a starting point" and
    "this repo owns the code": without it, `--update --flavor typescript` would replace a
    project's entry point with a skeleton.
    """
    path = cwd / relative
    reason = SOURCE_OWNED.get(relative)
    if reason is None:
        reason = next(
            (
                why
                for pattern, why in SOURCE_OWNED_PATTERNS.items()
                if pathlib.PurePosixPath(relative).match(pattern)
            ),
            None,
        )
    if update and reason and path.exists():
        return REPORT.preserved(path, reason)
    write_file(path, content, dry_run)
    return None


# ------------------------------------------------------------------ ensure ops
# Per-field edits on user-owned manifests — the deterministic half of the
# deterministic/semantic boundary. The script never rewrites these files wholesale
# (see PROJECT_OWNED + write_generated); `scaffold.py ensure <op>` performs one named
# field edit the model decided on, after confirming with the user when the value is
# ambiguous. An absent field is added with minimal bytes; a present field is reported
# unchanged, never rewritten. No state file: scaffold runs at low frequency, so every
# op re-detects from disk and stays honest when the project edits by hand.


class EnsureError(RuntimeError):
    """A per-field edit the script refuses: missing file, missing section, bad value."""


def _ensure_read(path: pathlib.Path, create_hint: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise EnsureError(f"{path}: no such file — {create_hint}") from None


def _ensure_write(path: pathlib.Path, body: str, dry_run: bool, action: str) -> str:
    if dry_run:
        return f"{path.name}: would {action} (dry-run)"
    path.write_text(body, encoding="utf-8")
    return f"{path.name}: {action}"


def _cargo_dependencies_span(body: str) -> tuple[int, int] | None:
    """Byte span of the [dependencies] section body (header line excluded)."""
    header = re.search(r"(?m)^\s*\[\s*dependencies\s*\]\s*(?:[#;].*)?$", body)
    if header is None:
        return None
    start = header.end()
    nxt = re.search(r"(?m)^\s*\[.*\]\s*(?:[#;].*)?$", body[start:])
    end = start + nxt.start() if nxt else len(body)
    return (start, end)


_COVERAGE_SCRIPT_PATTERN = r"[A-Za-z0-9:_-]+"


def _is_coverage_script_name(name: str) -> bool:
    """Shared shape for coverage script names (ensure/detect/generation agree)."""
    return re.fullmatch(_COVERAGE_SCRIPT_PATTERN, name) is not None


def _validate_coverage_script(name: str) -> None:
    if not _is_coverage_script_name(name):
        raise EnsureError(
            f"invalid coverage script name {name!r}: must match ^[A-Za-z0-9:_-]+$"
        )


def ensure_cargo_dep(
    cwd: pathlib.Path, name: str, version: str = "*", *, dry_run: bool = False
) -> str:
    """Add one entry under [dependencies] in Cargo.toml; existing entries never touched."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise EnsureError(f"invalid crate name {name!r}")
    if '"' in version or "\n" in version or "\r" in version:
        raise EnsureError(f"invalid version {version!r}: must not contain a quote or newline")
    path = cwd / "Cargo.toml"
    body = _ensure_read(path, "run --flavor rust first so there is a manifest to edit")
    error = _toml_syntax_error(path, body)
    if error:
        raise EnsureError(f"{path}: {error} — fix by hand first")
    span = _cargo_dependencies_span(body)
    if span is not None and re.search(
        rf"(?m)^\s*{re.escape(name)}\s*=", body[span[0] : span[1]]
    ):
        return f"Cargo.toml: unchanged — dependency {name!r} already present"
    entry = f'{name} = "{version}"'
    section = re.search(r"(?m)^\s*\[\s*dependencies\s*\]\s*(?:[#;].*)?$", body)
    if section is None:
        new_body = body.rstrip("\n") + f"\n\n[dependencies]\n{entry}\n"
    else:
        new_body = body[: section.end()] + f"\n{entry}" + body[section.end() :]
    try:
        tomllib.loads(new_body)
    except tomllib.TOMLDecodeError as exc:
        raise EnsureError(
            f"{path}: refusing edit that would write invalid TOML ({exc})"
            " — fix by hand first"
        ) from None
    return _ensure_write(path, new_body, dry_run, f"added dependency {entry}")


def _pep508_name(req: str) -> str:
    return re.split(r"[<>=!~;\s\[]", req.strip(), maxsplit=1)[0].strip()


def _toml_code_mask(body: str) -> list[bool]:
    """True per index for TOML code (False inside strings/comments)."""
    mask = [True] * len(body)
    i, n = 0, len(body)
    while i < n:
        ch = body[i]
        if ch == "#":
            j = body.find("\n", i)
            j = n if j == -1 else j
            for k in range(i, j):
                mask[k] = False
            i = j
        elif body.startswith('"""', i) or body.startswith("'''", i):
            quote = body[i : i + 3]
            j = body.find(quote, i + 3)
            j = n if j == -1 else j + 3
            for k in range(i, j):
                mask[k] = False
            i = j
        elif ch == '"':
            mask[i] = False
            i += 1
            while i < n:
                mask[i] = False
                if body[i] == "\\":
                    i += 2
                    continue
                if body[i] == '"':
                    i += 1
                    break
                if body[i] == "\n":
                    i += 1
                    break
                i += 1
        elif ch == "'":
            mask[i] = False
            i += 1
            while i < n and body[i] != "\n":
                mask[i] = False
                if body[i] == "'":
                    i += 1
                    break
                i += 1
        else:
            i += 1
    return mask


def _normalize_toml_section(name: str) -> str:
    """Strip whitespace and surrounding quotes from a TOML table header."""
    s = name.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        s = s[1:-1].strip()
    return s


def _toml_sections(code_text: str) -> list[tuple[int, str]]:
    """Header offsets with normalized table names, located on TOML code only."""
    return [
        (m.start(), _normalize_toml_section(m.group(1)))
        for m in re.finditer(r"(?m)^[ \t]*\[{1,2}([^\]\n\[]+)\]{1,2}[ \t]*$", code_text)
    ]


def _toml_section_at(sections: list[tuple[int, str]], pos: int) -> str:
    """Table owning `pos`: the last header at or before it, else no table."""
    name = ""
    for start, sec in sections:
        if start <= pos:
            name = sec
        else:
            break
    return name


def ensure_py_dep(cwd: pathlib.Path, req: str, *, dry_run: bool = False) -> str:
    """Add one PEP 508 requirement to pyproject.toml `dependencies`; present ones untouched."""
    if '"' in req or "\n" in req or "\r" in req:
        raise EnsureError(f"invalid requirement {req!r}: must not contain a quote or newline")
    name = _pep508_name(req)
    if not name or not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        raise EnsureError(f"invalid requirement {req!r}")
    path = cwd / "pyproject.toml"
    body = _ensure_read(path, "run --flavor python first so there is a manifest to edit")
    error = _toml_syntax_error(path, body)
    if error:
        raise EnsureError(f"{path}: {error} — fix by hand first")
    try:
        data = tomllib.loads(body)
    except tomllib.TOMLDecodeError as exc:
        raise EnsureError(f"{path}: invalid TOML: {exc} — fix by hand first") from None
    proj = data.get("project")
    existing = proj.get("dependencies") if isinstance(proj, dict) else None
    if isinstance(existing, list):
        for item in existing:
            if isinstance(item, str) and _pep508_name(item) == name:
                return f"pyproject.toml: unchanged — dependency {name!r} already present"
    mask = _toml_code_mask(body)
    code_text = "".join(
        ch if ok else ("\n" if ch == "\n" else " ")
        for ch, ok in zip(body, mask, strict=True)
    )
    sections = _toml_sections(code_text)
    lines_body = body.splitlines(keepends=True)
    lines_code = code_text.splitlines(keepends=True)
    offsets: list[int] = []
    _off = 0
    for _ln in lines_body:
        offsets.append(_off)
        _off += len(_ln)
    start = next(
        (
            i
            for i, ln in enumerate(lines_code)
            if re.match(r"^\s*dependencies\s*=\s*\[", ln)
            and _toml_section_at(sections, offsets[i]) == "project"
        ),
        None,
    )
    if start is None:
        any_open = next(
            re.finditer(r"dependencies\s*=\s*\[", code_text), None
        )
        if any_open is not None:
            found = _toml_section_at(sections, any_open.start()) or "(no table)"
            raise EnsureError(
                f"{path}: no `dependencies` in [project]"
                f" (found in [{found}])"
                " — run --flavor python first or move the array"
                " into [project] by hand"
            )
        raise EnsureError(
            f"{path}: no `dependencies = [...]` array — run --flavor python first"
        )
    open_idx = lines_code[start].find("[")
    close_idx = lines_code[start].find("]", open_idx + 1) if open_idx != -1 else -1
    if open_idx != -1 and close_idx != -1:
        inner = lines_body[start][open_idx + 1 : close_idx]
        suffix = lines_body[start][close_idx + 1 :]
        kept = [f'    {inner.strip().rstrip(",")},\n'] if inner.strip() else []
        lines_body[start : start + 1] = [
            "dependencies = [\n",
            *kept,
            f'    "{req}",\n',
            "]" + suffix,
        ]
    else:
        end = next(
            (
                i
                for i in range(start + 1, len(lines_code))
                if re.match(r"^\s*\]\s*,?\s*$", lines_code[i])
            ),
            None,
        )
        if end is None:
            raise EnsureError(f"{path}: `dependencies = [` never closes — fix by hand first")
        lines_body[end:end] = [f'    "{req}",\n']
    new_body = "".join(lines_body)
    try:
        tomllib.loads(new_body)
    except tomllib.TOMLDecodeError as exc:
        raise EnsureError(
            f"{path}: refusing edit that would write invalid TOML ({exc})"
            " — fix by hand first"
        ) from None
    return _ensure_write(path, new_body, dry_run, f'added dependency "{req}"')


def _ensure_json_field(
    cwd: pathlib.Path,
    filename: str,
    section: str,
    name: str,
    value: str,
    kind: str,
    *,
    dry_run: bool = False,
) -> str:
    """Add one key to a package.json object section. Key order preserved; whitespace
    normalized through json round-trip — the result line says so."""
    path = cwd / filename
    raw = _ensure_read(path, "run --flavor typescript first so there is a manifest to edit")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EnsureError(f"{path}: invalid JSON ({exc.msg}) — fix by hand first") from None
    node = data.get(section)
    if node is None:
        node = {}
        data[section] = node
    if not isinstance(node, dict):
        raise EnsureError(
            f"{path}: `{section}` is not an object — add a `\"{section}\": {{}}` object by hand, then re-run ensure"
        )
    if name in node:
        return f"{filename}: unchanged — {kind} {name!r} already present"
    node[name] = value
    out = json.dumps(data, indent=2, ensure_ascii=False)
    if raw.endswith("\n"):
        out += "\n"
    return _ensure_write(path, out, dry_run, f"added {kind} {name!r} (whitespace normalized)")


def _reject_ts_control(value: str, label: str) -> None:
    """Refuse control chars that would mis-set package.json (mirrors cargo/py)."""
    if "\n" in value or "\r" in value:
        raise EnsureError(f"invalid {label} {value!r}: must not contain a newline")


def ensure_ts_dep(
    cwd: pathlib.Path, name: str, version: str = "*", *, dev: bool = True, dry_run: bool = False
) -> str:
    """Add one package.json dependency (devDependencies by default); present ones untouched."""
    if not name.strip():
        raise EnsureError("empty package name")
    _reject_ts_control(name, "package name")
    _reject_ts_control(version, "version")
    section = "devDependencies" if dev else "dependencies"
    return _ensure_json_field(cwd, "package.json", section, name, version, "dependency", dry_run=dry_run)


def ensure_ts_script(cwd: pathlib.Path, name: str, cmd: str, *, dry_run: bool = False) -> str:
    """Add one package.json script; a present script is never overwritten."""
    if not name.strip():
        raise EnsureError("empty script name")
    if not cmd.strip():
        raise EnsureError("empty script command")
    _reject_ts_control(name, "script name")
    _reject_ts_control(cmd, "script command")
    if not _is_coverage_script_name(name):
        raise EnsureError(
            f"invalid script name {name!r}: must match ^[A-Za-z0-9:_-]+$"
        )
    return _ensure_json_field(cwd, "package.json", "scripts", name, cmd, "script", dry_run=dry_run)


def ensure_coverage_threshold(
    cwd: pathlib.Path, flavor: str, value: int, *, dry_run: bool = False
) -> str:
    """Set the coverage fail-under field for one flavor; rust has no manifest field."""
    if not 0 <= value <= 100:
        raise EnsureError(f"invalid threshold {value}: must be 0-100")
    if flavor == "python":
        path = cwd / "pyproject.toml"
        body = _ensure_read(path, "run --flavor python --with-coverage first")
        error = _toml_syntax_error(path, body)
        if error:
            raise EnsureError(f"{path}: {error} — fix by hand first")
        code_text = "".join(
            ch if ok else ("\n" if ch == "\n" else " ")
            for ch, ok in zip(body, _toml_code_mask(body), strict=True)
        )
        sections: list[tuple[int, str]] = _toml_sections(code_text)

        def _coverage_section(pos: int) -> bool:
            name = _toml_section_at(sections, pos)
            return name == "tool.coverage.report" or name.startswith(
                "tool.coverage.report."
            )

        hits = [
            m
            for m in re.finditer(r"(fail_under\s*=\s*)\d+", code_text)
            if _coverage_section(m.start())
        ]
        if not hits:
            raise EnsureError(f"{path}: no coverage gate — run --flavor python --with-coverage first")
        parts: list[str] = []
        last = 0
        for m in hits:
            parts.append(body[last : m.start(1)])
            parts.append(m.group(1))
            parts.append(str(value))
            last = m.end()
        parts.append(body[last:])
        new_body = "".join(parts)
        try:
            tomllib.loads(new_body)
        except tomllib.TOMLDecodeError as exc:
            raise EnsureError(
                f"{path}: refusing edit that would write invalid TOML ({exc})"
                " — fix by hand first"
            ) from None
        return _ensure_write(path, new_body, dry_run, f"set coverage fail_under to {value}")
    if flavor == "typescript":
        path = cwd / "vitest.config.ts"
        body = _ensure_read(path, "run --flavor typescript --with-coverage first")
        error = _ts_syntax_error(body)
        if error:
            raise EnsureError(f"{path}: invalid TypeScript ({error}) — fix by hand first")
        mask = _ts_code_mask(body)
        if _ts_code_match(r"lines:\s*\d+", body, mask) is None:
            raise EnsureError(f"{path}: no coverage thresholds — run --flavor typescript --with-coverage first")
        new_body = body
        for key in ("lines", "functions", "branches", "statements"):
            mask = _ts_code_mask(new_body)
            code_matches = [
                m
                for m in re.finditer(rf"({key}:\s*)\d+", new_body)
                if all(mask[m.start() : m.end()])
            ]
            if code_matches:
                parts: list[str] = []
                last = 0
                for m in code_matches:
                    parts.append(new_body[last : m.start(1)])
                    parts.append(m.group(1))
                    parts.append(str(value))
                    last = m.end()
                parts.append(new_body[last:])
                new_body = "".join(parts)
            else:
                mask = _ts_code_mask(new_body)
                head = _ts_code_match(r"thresholds\s*:\s*\{", new_body, mask)
                if head is None:
                    raise EnsureError(
                        f"{path}: threshold `{key}` untouched — no `thresholds: {{...}}` block to extend; add `{key}: {value}` by hand"
                    )
                tail = next(
                    (
                        i
                        for i in range(head.end(), len(new_body))
                        if new_body[i] == "}" and mask[i]
                    ),
                    None,
                )
                if tail is None:
                    raise EnsureError(
                        f"{path}: threshold `{key}` untouched — no `thresholds: {{...}}` block to extend; add `{key}: {value}` by hand"
                    )
                inner = new_body[head.end() : tail].rstrip()
                sep = "" if not inner.strip() else ("" if inner.rstrip().endswith(",") else ",")
                insertion = f"{sep} {key}: {value}" if inner.strip() else f" {key}: {value} "
                new_body = (
                    new_body[: head.end()] + new_body[head.end() : tail].rstrip() + insertion + new_body[tail:]
                )
        return _ensure_write(path, new_body, dry_run, f"set coverage thresholds to {value}")
    raise EnsureError(
        "rust has no manifest threshold field — thresholds live in the CI verify step; "
        "pass --coverage-threshold at scaffold time"
    )


def ensure_main(argv: list[str]) -> int:
    """`scaffold.py ensure <op>`: one confirmed field edit on a user-owned manifest."""
    ap = argparse.ArgumentParser(
        prog="scaffold.py ensure",
        description="Per-field edits on user-owned manifests "
        "(package.json edits normalize to 2-space JSON; never wholesale rewrites)",
    )
    ap.add_argument("--cwd", default=".", help="target directory (default: .)")
    ap.add_argument("--dry-run", action="store_true", help="report the edit without writing")
    sub = ap.add_subparsers(dest="op", required=True)
    rust_dep = sub.add_parser("rust-dep", help="add a Cargo.toml [dependencies] entry")
    rust_dep.add_argument("--name", required=True)
    rust_dep.add_argument("--version", default="*")
    py_dep = sub.add_parser("py-dep", help="add a pyproject.toml dependency (PEP 508)")
    py_dep.add_argument("--req", required=True, help='e.g. "httpx>=0.27"')
    ts_dep = sub.add_parser("ts-dep", help="add a package.json dependency")
    ts_dep.add_argument("--name", required=True)
    ts_dep.add_argument("--version", default="*")
    ts_dep.add_argument("--dev", action=argparse.BooleanOptionalAction, default=True)
    ts_script = sub.add_parser("ts-script", help="add a package.json script")
    ts_script.add_argument("--name", required=True)
    ts_script.add_argument("--cmd", required=True)
    cov = sub.add_parser("coverage-threshold", help="set the coverage fail-under field")
    cov.add_argument("--flavor", choices=["python", "typescript"], required=True)
    cov.add_argument("--value", type=int, required=True)
    args = ap.parse_args(argv)
    cwd = pathlib.Path(args.cwd).resolve()
    # Write detection compares bytes, never prose: a value (e.g. a crate
    # named `unchanged`) must not be able to silence the writer gate.
    _watched = [
        cwd / name
        for name in ("Cargo.toml", "pyproject.toml", "package.json", "vitest.config.ts")
    ]
    before = {p: p.read_bytes() if p.is_file() else None for p in _watched}
    try:
        if args.op == "rust-dep":
            note = ensure_cargo_dep(cwd, args.name, args.version, dry_run=args.dry_run)
            print(note)
            target = cwd / "Cargo.toml"
        elif args.op == "py-dep":
            note = ensure_py_dep(cwd, args.req, dry_run=args.dry_run)
            print(note)
            target = cwd / "pyproject.toml"
        elif args.op == "ts-dep":
            note = ensure_ts_dep(
                cwd, args.name, args.version, dev=args.dev, dry_run=args.dry_run
            )
            print(note)
            target = cwd / "package.json"
        elif args.op == "ts-script":
            note = ensure_ts_script(cwd, args.name, args.cmd, dry_run=args.dry_run)
            print(note)
            target = cwd / "package.json"
        elif args.op == "coverage-threshold":
            note = ensure_coverage_threshold(
                cwd, args.flavor, args.value, dry_run=args.dry_run
            )
            print(note)
            target = (
                cwd / "pyproject.toml" if args.flavor == "python" else cwd / "vitest.config.ts"
            )
        else:
            ap.error(f"unknown op {args.op}")
    except EnsureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if not args.dry_run and target.is_file() and before.get(target) != target.read_bytes():
        for finding in self_check([target]):
            mark = "SELF-CHECK" if finding.blocking else "WARNING (self-check)"
            tail = f" — fix: {finding.remedy}" if finding.remedy else ""
            print(f"{mark}: {finding.area}: {finding.detail}{tail}", file=sys.stderr)
            if finding.blocking:
                return 1
    return 0

# ------------------------------------------------------------------ self-check
# What a run wrote must parse, run, and resolve. Everything here is deterministic and cheap:
# in-process compile() for Python, `bash -n` for shell, json/yaml parsers for configs, an
# exec-bit and a referenced-path probe. `blocking` separates our byte defects from a gap in
# what the skill ships — the caller fails on the first and only reads the second.
def _yaml_available() -> bool:
    """pyyaml is optional: the script's PEP-723 env ships jinja2, so probe, don't assume."""
    try:
        import yaml  # noqa: F401
    except ImportError:
        return False
    return True


def _yaml_error(text: str) -> str | None:
    import yaml

    try:
        yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return f"invalid YAML: {str(exc)[:200]}"
    return None


def _strip_ts_noise(body: str) -> str:
    """Drop TS comments and string/template literal contents (escape-aware).

    Template `${...}` code is treated as opaque: dropping balanced code keeps
    the balance verdict, while literal brackets inside strings no longer skew it.
    """
    out: list[str] = []
    i, n = 0, len(body)
    while i < n:
        ch = body[i]
        nxt = body[i + 1] if i + 1 < n else ""
        if ch == "/" and nxt == "/":
            j = body.find("\n", i)
            i = n if j == -1 else j
        elif ch == "/" and nxt == "*":
            j = body.find("*/", i + 2)
            i = n if j == -1 else j + 2
        elif ch in ("'", '"', "`"):
            out.append(" ")
            i += 1
            while i < n:
                if body[i] == "\\":
                    i += 2
                    continue
                if body[i] == ch:
                    i += 1
                    break
                i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _ts_code_mask(body: str) -> list[bool]:
    """True per index for TS code (False inside comments/strings)."""
    mask = [True] * len(body)
    i, n = 0, len(body)
    while i < n:
        ch = body[i]
        nxt = body[i + 1] if i + 1 < n else ""
        if ch == "/" and nxt == "/":
            j = body.find("\n", i)
            j = n if j == -1 else j
            for k in range(i, j):
                mask[k] = False
            i = j
        elif ch == "/" and nxt == "*":
            j = body.find("*/", i + 2)
            j = n if j == -1 else j + 2
            for k in range(i, j):
                mask[k] = False
            i = j
        elif ch in ("'", '"', "`"):
            quote = ch
            mask[i] = False
            i += 1
            while i < n:
                mask[i] = False
                if body[i] == "\\":
                    i += 2
                    continue
                if body[i] == quote:
                    i += 1
                    break
                i += 1
        else:
            i += 1
    return mask


def _ts_code_match(pattern: str, body: str, mask: list[bool]) -> re.Match[str] | None:
    """First regex match fully inside TS code (comments/strings excluded)."""
    for m in re.finditer(pattern, body):
        if all(mask[m.start() : m.end()]):
            return m
    return None


def _ts_syntax_error(body: str) -> str | None:
    """Lightweight TS parse probe: bracket balance without needing Node."""
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    for ch in _strip_ts_noise(body):
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return f"unbalanced {ch!r}"
    if stack:
        return f"unbalanced {stack[-1]!r}"
    return None


def _toml_syntax_error(path: pathlib.Path, body: str) -> str | None:
    try:
        tomllib.loads(body)
    except tomllib.TOMLDecodeError as exc:
        return f"invalid TOML: {exc}"
    return None


def referenced_path_findings(path: pathlib.Path) -> list[Finding]:
    """Report `scripts/x.sh` style references that resolve to nothing (non-blocking).

    Resolved against the repo root: the only files that can raise this are generated hooks,
    workflows and scripts, since scaffold writes no `SKILL.md` of its own.
    """
    findings: list[Finding] = []
    for reference in sorted(set(REFERENCE_RE.findall(path.read_text(encoding="utf-8")))):
        if not (REPORT.cwd / reference).is_file():
            findings.append(
                Finding(
                    str(path),
                    f"references absent path {reference!r}",
                    f"ship {reference} or drop the reference",
                    blocking=False,
                )
            )
    return findings


def self_check(targets: list[pathlib.Path]) -> list[Finding]:
    """Validate the files a run claims: syntax, parseability, exec bit, referenced paths."""
    findings: list[Finding] = []
    yaml_ok = _yaml_available()
    if not yaml_ok:
        REPORT.note("NOTE (self-check): pyyaml unavailable — YAML parse skipped")
    for path in targets:
        if not path.is_file():
            continue
        suffix = path.suffix
        is_script = suffix == ".sh" or path.name in SCRIPT_NAMES
        checkable = is_script or suffix in {".py", ".json", ".yml", ".yaml", ".toml", ".ts"}
        if not checkable:
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            findings.append(Finding(str(path), f"unreadable: {exc}", "check permissions/encoding"))
            continue
        if suffix == ".py":
            try:
                compile(body, str(path), "exec")
            except SyntaxError as exc:
                findings.append(
                    Finding(str(path), f"python syntax error: {exc.msg} (line {exc.lineno})")
                )
        elif suffix == ".json":
            try:
                json.loads(body)
            except json.JSONDecodeError as exc:
                findings.append(Finding(str(path), f"invalid JSON: {exc.msg} (line {exc.lineno})"))
        elif suffix in {".yml", ".yaml"} and yaml_ok:
            error = _yaml_error(body)
            if error:
                findings.append(Finding(str(path), error))
        elif suffix == ".toml":
            error = _toml_syntax_error(path, body)
            if error:
                findings.append(Finding(str(path), error))
        elif suffix == ".ts":
            error = _ts_syntax_error(body)
            if error:
                findings.append(Finding(str(path), f"invalid TypeScript: {error}"))
        if is_script:
            bash = shutil.which("bash")
            if bash is None:
                REPORT.note("NOTE (self-check): bash unavailable — shell syntax skipped")
            else:
                proc = subprocess.run(
                    [bash, "-n", str(path)], capture_output=True, text=True, check=False
                )
                if proc.returncode != 0:
                    findings.append(
                        Finding(str(path), f"shell syntax error: {proc.stderr.strip()[:200]}")
                    )
            if not path.stat().st_mode & 0o111:
                findings.append(Finding(str(path), "not executable", f"chmod +x {path}"))
        if is_script or suffix in {".yml", ".yaml"}:
            findings.extend(referenced_path_findings(path))
    return findings


def main() -> int:
    """Resolve the flags, run the requested flavors, report once, exit with the verdict."""
    if len(sys.argv) > 1 and sys.argv[1] == "ensure":
        return ensure_main(sys.argv[2:])
    ap = argparse.ArgumentParser(
        description="Deterministic scaffold generator",
        epilog="Boundary: run 1 (field absent) the tool writes byte-identical bytes; "
        "run 2+ (field present) the project owns the file — model decides replace / "
        "update one field / untouched; --update preserves, ensure <op> performs one "
        "confirmed field edit. See `scaffold.py ensure --help`.",
    )
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
        choices=list(CI_RUNTIMES),
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
        default=DEFAULT_COVERAGE_THRESHOLD,
        help="coverage fail-under threshold (default: 80)",
    )
    ap.add_argument(
        "--coverage-script",
        default=None,
        help="package.json script name the coverage gate runs (default: detected script, else coverage)",
    )
    ap.add_argument(
        "--detect", action="store_true", help="detect project state and exit (no writes)"
    )
    ap.add_argument(
        "--update",
        action="store_true",
        help="refresh generated infrastructure in place: project-owned files are preserved and reported as NEXT actions; implies --flavor git when --flavor is omitted",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="one-line-per-file drift report for the update plan; exit 1 when the repo has drifted (implies --update --dry-run --summary)",
    )
    ap.add_argument(
        "--summary",
        action="store_true",
        help="collapse per-file reporting to one line each instead of diffs/prose",
    )
    ap.add_argument(
        "--self-check",
        action="store_true",
        help="also validate the files this run claims (syntax, parse, exec bit, referenced paths); runs automatically after a real write",
    )
    ap.add_argument(
        "--merge-mixed",
        action="store_true",
        help="with --update: insert CONTRIBUTING.md template sections that are missing; existing lines are never rewritten",
    )
    ap.add_argument(
        "--only",
        default=None,
        help="only scaffold these components (comma-separated, e.g. 'pre-push,releaserc'); default all",
    )
    ap.add_argument(
        "--without",
        default=None,
        dest="without",
        help="exclude these components (comma-separated, e.g. 'release-yml,changelog-check')",
    )
    ap.add_argument(
        "--components",
        default=None,
        help="alias for --only (comma-separated)",
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="emit the run plan (or the detect census) as JSON instead of prose",
    )
    ap.add_argument(
        "--no-format",
        action="store_true",
        help="skip the pinned oxfmt pass over generated bytes (needs no Node; bytes the formatter would rewrite ship as written, so a repo that wires `oxfmt --check` stays red until `pnpm run format:fix`)",
    )
    args = ap.parse_args()

    cwd = pathlib.Path(args.cwd).resolve()
    if args.detect:
        return print_detect(cwd, as_json=args.json)
    if args.flavor is None and not (args.update or args.check):
        ap.error("--flavor is required unless --update, --check or --detect is used")
    # --check is the read-only projection of --update: same plan, machine-readable verdict.
    update: bool = args.update or args.check
    dry_run: bool = args.dry_run or args.check
    if args.json:
        mode = JSON_OUT
    elif args.summary or args.check:
        mode = SUMMARY
    else:
        mode = VERBOSE
    project_name = args.project_name or infer_project_name(cwd)
    flavor: str = args.flavor or "git"
    with_coverage: bool = args.with_coverage
    threshold: int = args.coverage_threshold
    if args.coverage_script is not None:
        try:
            _validate_coverage_script(args.coverage_script)
        except EnsureError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        coverage_script: str = args.coverage_script
    else:
        try:
            _detected = detect_project(cwd).get("typescript")
            _name = _detected.get("coverage_script") if isinstance(_detected, dict) else None
        except Exception:
            _name = None
        if isinstance(_name, str) and _is_coverage_script_name(_name):
            coverage_script = _name
        else:
            coverage_script = "coverage"

    if threshold < 0 or threshold > 100:
        print("error: --coverage-threshold must be 0-100", file=sys.stderr)
        return 2

    if not project_name or not project_name.strip():
        print("error: --project-name is required when cwd has no inferrable name", file=sys.stderr)
        return 2

    REPORT.start(mode, cwd)

    # finer granularity: resolve selected components (git/ci)
    git_selected: set[str] | None = None
    ci_selected: set[str] | None = None
    if flavor in ("git", "all") or flavor == "ci":
        try:
            if flavor in ("git", "all"):
                git_selected = _resolve_selected(
                    args.only, args.without, args.components, GIT_COMPONENTS
                )
            if flavor == "ci":
                ci_selected = _resolve_selected(
                    args.only, args.without, args.components, CI_COMPONENTS
                )
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    if not args.no_format and not os.environ.get("SCAFFOLD_NO_FORMAT"):
        enable_formatter(cwd)
    notes: list[str] = []
    try:
        if flavor in ("git", "all"):
            notes += do_git(
                cwd,
                project_name,
                dry_run,
                selected=git_selected,
                update=update,
                merge_mixed=args.merge_mixed,
            )
        if flavor in ("python", "all"):
            notes += do_python(cwd, project_name, dry_run, with_coverage, threshold, update=update)
        if flavor in ("rust", "all"):
            notes += do_rust(cwd, project_name, dry_run, with_coverage, threshold, update=update)
        if flavor in ("typescript", "all"):
            notes += do_typescript(
                cwd,
                project_name,
                dry_run,
                args.ts_variant,
                with_coverage,
                threshold,
                coverage_script,
                update=update,
                merge_mixed=args.merge_mixed,
            )
        if flavor in ("ci", "all"):
            notes += do_ci(
                cwd,
                dry_run,
                args.ci_variant,
                with_coverage,
                threshold,
                selected=ci_selected,
                coverage_script=coverage_script,
                update=update,
            )

        # A real write validates itself; a preview validates what it touched when asked.
        check_targets = REPORT.paths_of({STALE, MISSING, PATCHED, APPENDED})
        if check_targets and (args.self_check or not dry_run):
            for finding in self_check(check_targets):
                REPORT.finding(
                    finding.area,
                    finding.detail,
                    finding.remedy,
                    blocking=finding.blocking,
                )

    except FormatterUnavailable as exc:
        print(f"error: {exc}", file=sys.stderr)
        print(
            "hint: oxfmt owns the bytes it can reach — install Node/npx, or pass --no-format to "
            "emit bytes the formatter would rewrite as written (a repo wiring `oxfmt --check` stays red)",
            file=sys.stderr,
        )
        return 2

    if update and mode == VERBOSE:
        print_next_actions(cwd, notes)

    if mode == SUMMARY:
        REPORT.render_summary(
            f"scaffold {'check' if args.check else 'plan'}: {cwd} "
            f"(flavor {flavor}, {'update' if update else 'scaffold'}"
            f"{', dry-run' if dry_run else ''})"
        )
    if mode == JSON_OUT:
        print(
            json.dumps(
                REPORT.plan(flavor=flavor, update=update, dry_run=dry_run), indent=2, sort_keys=True
            )
        )

    if dry_run and mode == VERBOSE:
        print(
            "dry-run complete — no files written (warnings on stderr are expected for mixed files)",
            file=sys.stderr,
        )
    if REPORT.blocking_findings:
        return 1
    if args.check and REPORT.drift_entries:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
