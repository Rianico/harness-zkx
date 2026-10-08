"""The pr-land module split: the import DAG, the one subprocess seam, and the re-exports.

The CLI started as a single 2168-line script. Phase 1 moved the squash domain and the error
types out; phase 2 moved the GitHub boundary, the `--check` gates, the draft phase, and the
changelog seam into private siblings. Two properties keep that split from silently rotting:

* the import direction stays a DAG — no sibling module may import `pr` back;
* every subprocess call in pr-land's own modules (`pr.py` + `_*.py`) goes through the single
  `_github.run_command` seam the tests patch. A bare `from _github import run_command` binding
  is early-bound, so patching `_github.run_command` would stop intercepting and the tests
  would shell out for real. The ast scans here catch both that and a sibling spawning its own
  `subprocess.run`; the identity check alone would not. The range/repo-root authority helper
  in `lib/range_authority.py` spawns its own `subprocess.run` coverage, outside the seam and
  outside this scan.

Deterministic and offline: this file reads the sources and imports the modules, nothing else.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
PR_PY = PR_SCRIPTS / "pr.py"
PR_PY_MAX_LINES = 800
SIBLING_MODULES = [
    "_errors.py",
    "_squash.py",
    "_options.py",
    "_github.py",
    "_check.py",
    "_draft.py",
    "_changelog.py",
]

if str(PR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PR_SCRIPTS))

import _check  # noqa: E402
import _draft  # noqa: E402
import _github  # noqa: E402
import _options  # noqa: E402
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


def test_run_command_is_reexported_from_github() -> None:
    assert pr_mod.run_command is _github.run_command


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


def test_names_the_tests_import_from_pr_resolve() -> None:
    """The `pr` public surface is the re-export block: whatever a test imports must resolve."""
    importers: dict[str, set[str]] = {}
    for path in sorted((REPO_ROOT / "tests/gh-router").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "pr":
                for alias in node.names:
                    importers.setdefault(alias.name, set()).add(path.name)
    assert importers, "no test imports from `pr` — this guard would pass vacuously"
    missing = sorted(name for name in importers if not hasattr(pr_mod, name))
    assert not missing, f"pr.py does not re-export: {', '.join(missing)}"


def test_shared_objects_are_the_sibling_definitions() -> None:
    """Re-exports are the same object, not a copy: `is` is what the tests' patches rely on."""
    assert pr_mod.PrOptions is _options.PrOptions
    assert pr_mod.CheckReport is _check.CheckReport
    assert pr_mod.DRAFT_OUT_DIR is _draft.DRAFT_OUT_DIR


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


def test_no_test_imports_run_command_from_pr() -> None:
    """`pr.run_command` is a patch-blind alias: tests must reach the seam through `_github`.

    `pr.py` re-exports `run_command` for the public surface, but `from pr import run_command`
    binds the function object early — a later patch of `_github.run_command` no longer reaches
    it, so the test silently runs the real subprocess. Only the alias used *inside tests* is a
    hazard; the re-export itself stays.
    """
    offenders = [
        f"{path.relative_to(REPO_ROOT)}:{node.lineno}"
        for path in sorted((REPO_ROOT / "tests").rglob("*.py"))
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=path.name))
        if isinstance(node, ast.ImportFrom)
        and node.module == "pr"
        and any(alias.name == "run_command" for alias in node.names)
    ]
    assert not offenders, (
        "import `run_command` from `_github`, not `pr`; the `pr` alias is early-bound and "
        f"escapes the `_github.run_command` patch point: {', '.join(offenders)}"
    )


def test_dir_pr_is_a_superset_of_the_pristine_surface() -> None:
    """`dir(pr)` must stay a superset of the pristine 175-name surface.

    The split moved names out of `pr.py`, so anything that enumerated the pre-split module (a
    shell completion, a `dir()`-driven smoke check, a downstream caller) must still find every
    name it used to. The annotation on `pr.py`'s `_LIB_DIR` is load-bearing here: a
    module-level variable annotation is what makes CPython 3.14 build `__annotate__` /
    `__conditional_annotations__`, and the pristine module had one. Drop the annotation and
    `dir(pr)` loses those two names. The literal below is the frozen pristine `dir(pr)`
    (captured pre-split in /tmp/golden/dir_pr.txt).
    """
    pristine = (
        "AFTER_MARKERS",
        "BEFORE_AFTER_ARROW",
        "BEFORE_MARKERS",
        "CHECKBOX_RE",
        "CLOSES_LINE_RE",
        "CLOSES_REF_RE",
        "CLOSING_RE",
        "CODE_AUTHORS_TOKEN",
        "CONFLICT_FILES_MAX",
        "CONFLICT_HELPER",
        "CONVENTIONAL_TYPES",
        "COPY_OVERLAP_THRESHOLD",
        "COPY_TOKEN_FLOOR",
        "Callable",
        "CheckFailureError",
        "CheckReport",
        "DEFAULT_TEMPLATE_PATH",
        "DEFAULT_TIMEOUT",
        "DETAILS_BLOCK_RE",
        "DETAILS_UNCLOSED_OPENER_RE",
        "DIRECTIVE_RE",
        "DIRTY_INTERVAL",
        "DIRTY_STRIKES",
        "DOOR_RE",
        "DRAFT_BODY_MAX_LINES",
        "DRAFT_BODY_PLACEHOLDER",
        "DRAFT_OUT_DIR",
        "DRAFT_SCHEMA",
        "EMAIL_KEY_RE",
        "EMPTY_BULLET_RE",
        "FENCE_RE",
        "FIX_TYPE",
        "HEADING_RE",
        "LABEL_ONLY_RE",
        "LOG_TIMEOUT",
        "MERGE_STATE_INTERVAL",
        "MERGE_STATE_TRIES",
        "MERMAID_FENCE_RE",
        "MERMAID_UNCLOSED_OPENER_RE",
        "MalformedSpec",
        "MergeFetch",
        "MergeObservation",
        "NoReturn",
        "POLL_INTERVAL",
        "POLL_TRIES",
        "PROCEDURAL_SECTION_RE",
        "Path",
        "PrError",
        "PrOptions",
        "REVIEW_ONLY_SECTION_RE",
        "ROLLBACK_RE",
        "RangeRefusal",
        "RangeResolution",
        "RefusalError",
        "SLUG_PATTERN",
        "SQUASH_BODY_MAX_BULLETS",
        "SQUASH_BULLET_RE",
        "SQUASH_HEADING_RE",
        "SQUASH_LABEL_RE",
        "SQUASH_MESSAGE_MAX_LINES",
        "SQUASH_MESSAGE_SPEC",
        "SQUASH_SECTIONS",
        "SQUASH_TITLE_MAX",
        "SQUASH_TITLE_RE",
        "TRAILER_RE",
        "UNKNOWN_INTERVAL",
        "UNKNOWN_TRIES",
        "UsageError",
        "_LIB_DIR",
        "_UNRELEASED_ATTR_RES",
        "_UNRELEASED_BULLET_RE",
        "_UNRELEASED_SECTION_RE",
        "_UNRELEASED_VERSION_END_RE",
        "__annotate__",
        "__builtins__",
        "__cached__",
        "__conditional_annotations__",
        "__doc__",
        "__file__",
        "__loader__",
        "__name__",
        "__package__",
        "__spec__",
        "_authority_resolve",
        "_copy_tokens",
        "_count_squash_bullets",
        "_digest_range_spec",
        "_draft_dirty",
        "_draft_range",
        "_evidence_marker_text",
        "_fenced_line_mask",
        "_is_label_line",
        "_is_stop_line",
        "_local_base_from_authority",
        "_read_unreleased_block",
        "_refuse_squash",
        "_remote_branch_exists",
        "_section_content",
        "_section_key",
        "_section_open",
        "_states_rollback",
        "_strip_unclosed",
        "_unreleased_attribution_re",
        "build_draft_payload",
        "build_squash_message",
        "cap_draft_body",
        "check_closes_lines",
        "check_conflicts",
        "check_explicit_squash_message",
        "check_raw_token",
        "check_squash_body",
        "check_squash_title",
        "check_title_length",
        "check_trailers",
        "check_trailers_report",
        "checks_verdict",
        "clean_squash_body",
        "conflicting_files",
        "copy_body_coverage",
        "copy_overlap",
        "create_or_reuse_pr",
        "dataclass",
        "default_branch",
        "draft_commits",
        "dump_failure_logs",
        "failing_run_ids",
        "fetch_merge_state",
        "fetch_mergeability",
        "finalize_squash_message",
        "find_repo_root",
        "get_commit_summary",
        "insert_trailers",
        "is_closing_line",
        "is_fallback_body",
        "is_trailer_line",
        "is_unfilled_body",
        "json",
        "main",
        "merge_pr",
        "merge_state_verdict",
        "os",
        "parse_args",
        "pr_co_author_trailers",
        "pr_conflict_verdict",
        "pr_url",
        "print_squash_message_required",
        "print_usage",
        "re",
        "ready_pr",
        "refuse_mechanic_copy",
        "refuse_raw_token",
        "refuse_unfilled_body",
        "repo_remote_for_ref",
        "repo_slug_from_url",
        "report_merge_refusal",
        "resolve_base",
        "resolve_head",
        "resolve_merge_state",
        "resolve_out_dir",
        "resolve_range",
        "resolve_repo",
        "resolve_squash_message",
        "resolve_squash_override",
        "resolve_title_and_body",
        "run_command",
        "run_draft_phase",
        "split_squash_sections",
        "squash_message",
        "stamp_changelog",
        "subprocess",
        "sys",
        "time",
        "trailer_email_key",
        "unreleased_attributes_pr",
        "watch_checks",
    )
    assert len(pristine) == 175, "the frozen pristine surface must list all 175 names"
    present = set(dir(pr_mod))
    missing = sorted(name for name in pristine if name not in present)
    assert not missing, f"dir(pr) lost pre-split names: {', '.join(missing)}"
