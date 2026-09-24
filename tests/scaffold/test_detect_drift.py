"""What `--detect` claims about the git contract, against what `--check` does with the same tree.

Three defects, all hit for real while refreshing a Node/pi-extension repo:

- the git flavor ships `scripts/*.py`, but only `do_python` appended `__pycache__/`, so running the
  shipped gate left `?? scripts/__pycache__/` in a non-Python tree (#114);
- `append_gitignore` deduped by exact string, so a pre-existing `.lsz/` survived next to the
  scaffold's `.lsz/*` + `!.lsz/config.yaml` pair and silently defeated the negation (#115);
- `git_contract.stale` was existence-only, so `--detect` reported `stale: false` while `--check`
  reported drift on the same tree — the documented entry point pointing away from the repair
  (#116).

`test_changelog_title_gate.py` covers the other half of the same refresh: the title guard and the
waiver the shipped workflow advertises.
"""

from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Protocol, cast

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "scaffold"
SCRIPT = SKILL_DIR / "scripts" / "scaffold.py"

# Append-only or preserve-only: `patch_agents` never reformats the file it appends to, and
# `write_contributing` preserves an existing one — neither is ever byte-compared to a template.
NEVER_BYTE_COMPARED = frozenset({"AGENTS.md", "CONTRIBUTING.md"})


class _Scaffold(Protocol):
    """The surface these tests read, so the dynamically loaded module stops typing as `Any`."""

    OXFMT_VERSION: str
    OXFMT_EXTENSIONS: frozenset[str]
    _formatter_root: Path | None
    _formatter_config: Path | None
    _formatter_tmp: object

    def do_git(
        self,
        cwd: Path,
        project_name: str,
        dry_run: bool,
        *,
        selected: set[str] | None = ...,
        update: bool = ...,
        merge_mixed: bool = ...,
    ) -> list[str]: ...

    def git_contract_drift(self, cwd: Path, project_name: str) -> dict[str, int]: ...

    def detect_project(self, cwd: Path, *, drift: bool = ...) -> dict[str, object]: ...

    def canonicalize(self, path: Path, content: str) -> str: ...

    def changelog_title_is_first(self, content: str) -> bool: ...


def _load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = cast("_Scaffold", cast("object", _load("scaffold_mod_detect_drift", SCRIPT)))


def _generate(target: Path, *invocations: list[str]) -> None:
    for args in invocations:
        _ = subprocess.run(
            [sys.executable, str(SCRIPT), *args, "--project-name", "demo", "--cwd", str(target)],
            check=True,
            capture_output=True,
            text=True,
        )


def _git(tree: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=tree, capture_output=True, text=True, check=False)


def _init_repo(tree: Path) -> None:
    _ = _git(tree, "init", "-q", "-b", "main")
    _ = _git(tree, "config", "user.email", "t@example.invalid")
    _ = _git(tree, "config", "user.name", "t")
    _ = _git(tree, "add", "-A")
    _ = _git(tree, "commit", "-qm", "chore: init")


def _env_writing_bytecode() -> dict[str, str]:
    """The gate's own `__pycache__` is the subject of #114 — never let the ambient env hide it."""
    return {key: value for key, value in os.environ.items() if key != "PYTHONDONTWRITEBYTECODE"}


# --- #114: the flavor that ships the Python scripts owns the bytecode ignore ------------------


def test_the_shipped_gate_never_dirties_a_non_python_tree(tmp_path: Path) -> None:
    """Reproduced on a Node/pi-extension repo: the shipped gate left `?? scripts/__pycache__/`."""
    _generate(
        tmp_path, ["--flavor", "git"], ["--flavor", "typescript", "--ts-variant", "pi-extension"]
    )
    _init_repo(tmp_path)
    assert _git(tmp_path, "status", "--short").stdout == ""

    # The gate is standalone; py_compile populates scripts/__pycache__ so git ignore is refuted
    _ = subprocess.run(
        [sys.executable, "-m", "py_compile", "scripts/changelog-gate.py"],
        cwd=tmp_path,
        check=True,
    )
    result = subprocess.run(
        [sys.executable, "scripts/changelog-gate.py", "ledger"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        env=_env_writing_bytecode(),
    )

    assert (tmp_path / "scripts" / "__pycache__").is_dir(), "the gate must have cached bytecode"
    assert result.returncode in (0, 1, 2), "the ledger verdict is not this test's subject"
    assert _git(tmp_path, "status", "--short").stdout == ""


def test_the_bytecode_entry_travels_with_the_component_that_writes_python(tmp_path: Path) -> None:
    """Keyed on "this run writes `scripts/*.py`", not on the target language."""
    _ = scaffold.do_git(tmp_path, "demo", dry_run=False, selected={"gitignore"})
    assert "__pycache__/" not in (tmp_path / ".gitignore").read_text(encoding="utf-8")

    with_scripts = tmp_path / "with-scripts"
    with_scripts.mkdir()
    _ = scaffold.do_git(
        with_scripts, "demo", dry_run=False, selected={"gitignore", "changelog-script"}
    )
    assert "__pycache__/" in (with_scripts / ".gitignore").read_text(encoding="utf-8")


# --- #115: a dead negation under a superseded directory rule ----------------------------------


def test_a_superseded_directory_rule_is_replaced_not_kept(tmp_path: Path) -> None:
    gitignore = tmp_path / ".gitignore"
    _ = gitignore.write_text("node_modules/\n.lsz/\n", encoding="utf-8")

    _ = scaffold.do_git(tmp_path, "demo", dry_run=False, selected={"gitignore"})

    lines = gitignore.read_text(encoding="utf-8").splitlines()
    assert ".lsz/" not in lines, "the directory-form rule must be replaced"
    assert ".lsz/*" in lines and "!.lsz/config.yaml" in lines
    assert "node_modules/" in lines, "unrelated lines are never rewritten"


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git to ask the real ignore engine")
def test_the_negation_survives_a_preexisting_directory_rule(tmp_path: Path) -> None:
    """git cannot re-include a file inside an excluded directory, so `.lsz/` won — silently."""
    _ = (tmp_path / ".gitignore").write_text(".lsz/\n", encoding="utf-8")
    _generate(tmp_path, ["--flavor", "git"])
    (tmp_path / ".lsz").mkdir()
    _ = (tmp_path / ".lsz" / "config.yaml").write_text("x: 1\n", encoding="utf-8")
    _ = (tmp_path / ".lsz" / "scratch.txt").write_text("scratch\n", encoding="utf-8")
    _ = _git(tmp_path, "init", "-q", "-b", "main")

    kept = _git(tmp_path, "check-ignore", ".lsz/config.yaml")
    ignored = _git(tmp_path, "check-ignore", ".lsz/scratch.txt")

    assert kept.returncode == 1, f"the negation must re-include it:\n{kept.stdout}"
    assert ignored.returncode == 0, "the rest of .lsz/ stays ignored"


# --- #116: `--detect` and `--check` answer the same question ----------------------------------


def test_detect_and_check_agree_on_a_drifted_tree(tmp_path: Path) -> None:
    """`--detect` said `stale: false` while `--check` reported drift on the same tree."""
    _generate(tmp_path, ["--flavor", "git"])
    releaserc = tmp_path / ".releaserc.json"
    body = releaserc.read_text(encoding="utf-8").replace('"main"', '"trunk"')
    _ = releaserc.write_text(body, encoding="utf-8")

    check = subprocess.run(
        [sys.executable, str(SCRIPT), "--check", "--cwd", str(tmp_path)],
        capture_output=True,
        text=True,
    )

    assert check.returncode == 1, check.stdout + check.stderr
    reported = re.search(r"drift (\d+)", check.stdout)
    assert reported is not None, check.stdout
    assert reported.group(1) != "0"

    contract = cast(
        "dict[str, object]", scaffold.detect_project(tmp_path, drift=True)["git_contract"]
    )
    counts = cast("dict[str, int]", contract["drift"])
    assert counts["total"] == int(reported.group(1))
    assert contract["changelog_guard_absent"] is False


def test_a_fresh_tree_reports_no_git_contract_drift(tmp_path: Path) -> None:
    """The formatter-free compare must not invent drift that `--check` (formatter on) denies."""
    _generate(tmp_path, ["--flavor", "git"])

    counts = scaffold.git_contract_drift(tmp_path, "demo")

    assert counts["total"] == 0, (
        "a shipped git template is no longer canonical for the pinned oxfmt, so the "
        f"formatter-free compare drifts from --check: {counts}"
    )


@pytest.mark.skipif(shutil.which("npx") is None, reason="needs Node/npx to run the pinned oxfmt")
def test_the_git_contracts_bytes_are_canonical_for_the_pin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Why `git_contract_drift` can skip the formatter: `canonicalize` is the identity on the
    template side, so its compare is the one `--check` makes. Bump `OXFMT_VERSION` and this test
    names every shipped file the new formatter would rewrite."""
    _ = scaffold.do_git(tmp_path, "demo", dry_run=False)  # the autouse fixture keeps it raw

    monkeypatch.setattr(scaffold, "_formatter_root", tmp_path)
    monkeypatch.setattr(scaffold, "_formatter_config", None)
    monkeypatch.setattr(scaffold, "_formatter_tmp", None)

    offenders: list[str] = []
    for path in sorted(tmp_path.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in scaffold.OXFMT_EXTENSIONS:
            continue
        if path.name in NEVER_BYTE_COMPARED:
            continue
        body = path.read_text(encoding="utf-8")
        if scaffold.canonicalize(path, body) != body:
            offenders.append(path.relative_to(tmp_path).as_posix())

    assert not offenders, f"not canonical for oxfmt@{scaffold.OXFMT_VERSION}: {offenders}"


# --- #117: the detector's half of the title rule -----------------------------------------------


def test_the_detector_reads_the_title_rule_the_gate_enforces() -> None:
    """The gate is the other half; `test_changelog_title_gate.py` holds the two together."""
    cases = {
        "# Changelog\n\n## [Unreleased]\n": True,
        "\n\n# Changelog\n\n## [Unreleased]\n": True,
        "<!-- keep -->\n# Changelog\n\n## [Unreleased]\n": False,
        "## [1.0.0] - 2026-01-01\n\n# Changelog\n": False,
        "no title at all\n": False,
        "# Changelog notes\n\n## [Unreleased]\n": False,
    }

    for content, expected in cases.items():
        assert scaffold.changelog_title_is_first(content) is expected, content
