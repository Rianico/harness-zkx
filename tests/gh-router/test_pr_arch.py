"""The pr-land module split: the import DAG, the one subprocess seam, and the thin CLI entry.

The CLI started as a single 2168-line script. Phase 1 moved the squash domain and the error
types out; phase 2 moved the GitHub boundary, the `--check` gates, the draft phase, and the
changelog seam into private siblings. T3c retired the `pr.py` re-export monolith: `pr.py` is
now only the CLI entry (`main`/`parse_args`/`create_or_reuse_pr`/`print_usage`), and every
consumer imports domain names from its home module. Three properties keep that split from
silently rotting:

* the import direction stays a DAG — no sibling module may import `pr` back;
* every subprocess call in pr-land's own modules (`pr.py` + `_*.py`) goes through the single
  `_github.run_command` seam the tests patch. A bare `from _github import run_command` binding
  is early-bound, so patching `_github.run_command` would stop intercepting and the tests
  would shell out for real. The ast scans here catch both that and a sibling spawning its own
  `subprocess.run`; the identity check alone would not. The range/repo-root authority helper
  in `lib/range_authority.py` spawns its own `subprocess.run` coverage, outside the seam and
  outside this scan;
* `pr.py` carries no `X as X` self-alias re-exports, and tests import from `pr` only the
  entry names the module itself defines.

Deterministic and offline: this file reads the sources and imports the modules, nothing else.
"""

from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
PR_PY = PR_SCRIPTS / "pr.py"
PR_PY_MAX_LINES = 600
PR_FROM_IMPORT_ALLOWLIST = frozenset({"create_or_reuse_pr", "parse_args"})
SIBLING_MODULES = [
    "_errors.py",
    "_squash.py",
    "_options.py",
    "_github.py",
    "_check.py",
    "_draft.py",
    "_status.py",
    "_changelog.py",
]

if str(PR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PR_SCRIPTS))

import _draft  # noqa: E402
import pr as pr_mod  # noqa: E402


def _module_texts() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in sorted(PR_SCRIPTS.glob("*.py"))}


def test_pr_py_stays_within_its_line_budget() -> None:
    """The entry script stays a CLI: the domains live in the siblings, not back in pr.py."""
    lines = len(PR_PY.read_text(encoding="utf-8").splitlines())
    assert lines <= PR_PY_MAX_LINES, f"pr.py is {lines} lines (budget {PR_PY_MAX_LINES})"


def test_every_sibling_module_exists_with_a_docstring() -> None:
    for name in SIBLING_MODULES:
        path = PR_SCRIPTS / name
        assert path.is_file(), f"missing sibling module {name}"
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"), filename=name))
        assert doc is not None and doc.strip(), f"{name} has no module docstring"


def test_no_sibling_module_imports_pr() -> None:
    """The import direction is a DAG: a sibling importing `pr` back is an import cycle."""
    offenders = [
        f"{name}:{node.lineno}"
        for name in SIBLING_MODULES
        for node in ast.walk(
            ast.parse((PR_SCRIPTS / name).read_text(encoding="utf-8"), filename=name)
        )
        if (isinstance(node, ast.ImportFrom) and node.module == "pr")
        or (isinstance(node, ast.Import) and any(alias.name == "pr" for alias in node.names))
    ]
    assert not offenders, f"sibling modules import the entry script: {', '.join(offenders)}"


def test_only_github_calls_run_command_by_bare_name() -> None:
    """One patch point: outside `_github.py`, the seam is called as `_github.run_command(...)`."""
    offenders = [
        f"{name}:{node.lineno}"
        for name, text in _module_texts().items()
        for node in ast.walk(ast.parse(text, filename=name))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_command"
        and name != "_github.py"
    ]
    assert not offenders, (
        "call the seam as `_github.run_command(...)` outside _github.py; a bare name binds "
        f"early and escapes the tests' single patch point: {', '.join(offenders)}"
    )


def test_tests_import_from_pr_only_the_entry_names() -> None:
    """`pr.py` is an entry, not a surface: tests may import only what it defines itself.

    `create_or_reuse_pr` and `parse_args` are defined in `pr.py` (CLI arg parsing plus the
    create-flow orchestration, which composes `_status` refusals with `_github` mutations —
    moving it into a sibling would force a `_github`/`_status` import cycle). Everything else
    a test needs comes from its home module. This also subsumes the old `run_command` guard:
    a `from pr import run_command` alias would bind the seam early and escape the tests'
    `_github.run_command` patch point, and `run_command` is not in the allowlist.
    """
    offenders = sorted(
        f"{path.name}:{node.lineno}:{alias.name}"
        for path in sorted((REPO_ROOT / "tests/gh-router").glob("*.py"))
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=path.name))
        if isinstance(node, ast.ImportFrom) and node.module == "pr"
        for alias in node.names
        if alias.name not in PR_FROM_IMPORT_ALLOWLIST
    )
    assert not offenders, (
        "import domain names from their home module, not `pr`; `pr` exposes only "
        f"{sorted(PR_FROM_IMPORT_ALLOWLIST)}: {', '.join(offenders)}"
    )


def test_only_github_module_spawns_subprocesses() -> None:
    """The seam is the single spawn point: no pr-land module but `_github.py` may run its own.

    `_github.run_command` is the one interception point the tests patch, so a sibling that
    spawns `subprocess.run`/`Popen` directly — or binds `from subprocess import run` — shells
    out for real behind the fake's back. The range/repo-root authority helper in
    `lib/range_authority.py` is out of reach by design and lives outside this scan. A
    type-only reference such as `_check.py`'s `subprocess.CompletedProcess[str]` annotation
    spawns nothing and stays legal.
    """
    offenders: list[str] = []
    for name, text in _module_texts().items():
        if name == "_github.py":
            continue
        for node in ast.walk(ast.parse(text, filename=name)):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
            ):
                offenders.append(f"{name}:{node.lineno} spawns subprocess.{node.func.attr}")
            elif isinstance(node, ast.ImportFrom) and node.module == "subprocess":
                offenders.append(f"{name}:{node.lineno} binds a bare subprocess name")
    assert not offenders, (
        "spawn subprocesses only through `_github.run_command` (the tests' single patch "
        f"point): {', '.join(offenders)}"
    )


def test_pr_py_exposes_only_the_cli_surface() -> None:
    """`pr.py` is an entry, not a surface: no `X as X` re-exports, retired names stay gone.

    T3c retired the re-export monolith. The AST scan is the airtight pin: any
    `from _sibling import name as name` self-alias is a re-export, whether or not a test
    imports it yet. The `hasattr` pins name the entry surface plus a sample of retired
    domain names that `pr.py` no longer binds at all (`check_conflicts`, `run_command`,
    `check_trailers`, `build_squash_message`, `finalize_squash_message`,
    `dump_failure_logs`, `watch_checks`, `checks_verdict`).
    """
    tree = ast.parse(PR_PY.read_text(encoding="utf-8"), filename="pr.py")
    aliases = sorted(
        f"{node.lineno}:{alias.name}"
        for node in ast.walk(tree)
        if isinstance(node, (ast.ImportFrom, ast.Import))
        for alias in node.names
        if alias.asname is not None and alias.asname == alias.name
    )
    assert not aliases, f"pr.py re-exports names again: {', '.join(aliases)}"
    for name in ("main", "parse_args", "create_or_reuse_pr", "print_usage"):
        obj = inspect.getattr_static(pr_mod, name)
        assert getattr(obj, "__module__", None) == "pr", (
            f"pr.py entry name is imported, not defined here: {name}"
        )
    for name in (
        "check_conflicts",
        "run_command",
        "check_trailers",
        "build_squash_message",
        "finalize_squash_message",
        "dump_failure_logs",
        "checks_verdict",
    ):
        assert not hasattr(pr_mod, name), f"pr.py re-exports retired name: {name}"


def test_retired_draft_surface_stays_gone() -> None:
    """ADR-0021 deletion proof: no retired helper survives outside the CHANGELOG."""
    for name in (
        "DRAFT_OUT_DIR",
        "DRAFT_SCHEMA",
        "SCAFFOLD_SIGNATURE_PREFIX",
        "is_untouched_scaffold",
        "build_draft_payload",
        "resolve_out_dir",
        "_draft_dirty",
    ):
        assert not hasattr(pr_mod, name), f"retired name still on pr: {name}"
        assert not hasattr(_draft, name), f"retired name still on _draft: {name}"
    texts = _module_texts()
    for name in (
        "draft.json",
        "is_untouched_scaffold",
        "SCAFFOLD_SIGNATURE",
        "--out-dir",
        "_draft_dirty",
    ):
        offenders = [mod for mod, text in texts.items() if name in text]
        assert not offenders, f"{name!r} still referenced in: {', '.join(offenders)}"
