"""Fresh-tree gate contract — every gate a flavor wires must pass on generated output.

See `skills/scaffold/SKILL.md` § Adding a Flavor — Gate Contract. The misses that motivated
this file: a Rust repo wired `cargo fmt`/`clippy`/`test` but shipped no target, so all three
died on `failed to parse manifest: no targets specified`; a Python repo wired `uv run pytest`
with no tests, so the gate exited 5. Both were invisible because no test ran a generated tree
through the commands the generated `release.yml` runs.

Gates only exist for the combination the scaffold prescribes: `--flavor <lang>` plus
`--flavor ci --ci-variant <lang>` (`--flavor all` always ships the Node verify job).
"""

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "skills" / "scaffold" / "scripts" / "scaffold.py"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


scaffold = _load("scaffold_mod_flavor_gates", SCRIPT)


def _generate(target: Path, *invocations: list[str]) -> None:
    for args in invocations:
        subprocess.run(
            [sys.executable, str(SCRIPT), *args, "--project-name", "demo", "--cwd", str(target)],
            check=True,
            capture_output=True,
            text=True,
        )


def _run(tree: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=str(tree), capture_output=True, text=True)


# --- rust: cargo fmt --check / cargo clippy -- -D warnings / cargo test ------


@pytest.mark.skipif(shutil.which("cargo") is None, reason="needs cargo")
@pytest.mark.skipif(shutil.which("rustfmt") is None, reason="needs the rustfmt component")
def test_rust_gates_pass_on_a_fresh_tree(tmp_path: Path) -> None:
    _generate(tmp_path, ["--flavor", "rust"], ["--flavor", "ci", "--ci-variant", "rust"])
    assert (tmp_path / "src" / "lib.rs").is_file(), "cargo needs a target to act on"
    for command in (
        ["cargo", "fmt", "--check"],
        ["cargo", "clippy", "--", "-D", "warnings"],
        ["cargo", "test"],
    ):
        result = _run(tmp_path, command)
        assert result.returncode == 0, f"{' '.join(command)}\n{result.stdout}\n{result.stderr}"


# --- python: ruff check . / pytest -----------------------------------------


@pytest.mark.skipif(shutil.which("ruff") is None, reason="needs ruff on PATH")
def test_python_gates_pass_on_a_fresh_tree(tmp_path: Path) -> None:
    _generate(tmp_path, ["--flavor", "python"], ["--flavor", "ci", "--ci-variant", "python"])
    assert (tmp_path / "tests" / "test_smoke.py").is_file(), "pytest needs a test to collect"
    for command in (
        [shutil.which("ruff") or "ruff", "check", "."],
        [shutil.which("ruff") or "ruff", "format", "--check", "."],
        [sys.executable, "-m", "pytest", "-q"],
    ):
        result = _run(tmp_path, command)
        assert result.returncode == 0, f"{' '.join(command)}\n{result.stdout}\n{result.stderr}"


def test_generated_pyproject_pins_the_lint_selection():
    """`ruff check` inherits the tool's default selection when nothing is configured, and that
    default is the tool's opinion: 413 rules in ruff 0.16.7, more each release. A generated repo
    would then go red on a lockfile bump nobody could review — and it did, on the git flavor's own
    `scripts/changelog-unreleased.py` (#31)."""
    pyproject = scaffold.build_pyproject("demo", with_coverage=False, threshold=80)
    assert "[tool.ruff.lint]" in pyproject
    assert 'select = ["E", "F", "I", "UP", "B"]' in pyproject
    assert 'ignore = ["E501"]' in pyproject, "line length belongs to the formatter"


def test_python_gate_holds_with_the_git_flavor_present(tmp_path: Path) -> None:
    """The git flavor ships `scripts/changelog-unreleased.py`, which lands inside the Python
    gate's reach — a combination no earlier test generated. Run the wired commands on it."""
    _generate(
        tmp_path,
        ["--flavor", "git"],
        ["--flavor", "python", "--with-coverage", "--coverage-threshold", "80"],
    )
    assert (tmp_path / "scripts" / "changelog-unreleased.py").is_file()
    for command in (
        [shutil.which("ruff") or "ruff", "check", "."],
        [shutil.which("ruff") or "ruff", "format", "--check", "."],
        [sys.executable, "-m", "pytest", "--cov", "--cov-fail-under=80", "-q"],
    ):
        result = _run(tmp_path, command)
        assert result.returncode == 0, f"{' '.join(command)}\n{result.stdout}\n{result.stderr}"


@pytest.mark.parametrize("variant", ["node", "python", "rust"])
def test_no_variant_disables_the_lockfile_guard(tmp_path: Path, variant: str) -> None:
    """pnpm's CI default is frozen when a lockfile is present, so a stale lockfile fails loudly.
    `--no-frozen-lockfile` re-resolves instead — and it silently masked the formatter drift that
    motivated `OXFMT_VERSION`. The flag has no home in a generated job (#25)."""
    _generate(tmp_path, ["--flavor", "ci", "--ci-variant", variant])
    workflow = (tmp_path / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "--no-frozen-lockfile" not in workflow
    installs = re.findall(r"^\s*- run: (pnpm install.*)$", workflow, re.MULTILINE)
    if variant == "node":
        assert installs == ["pnpm install"] * 2, installs
    else:
        assert installs == []


# --- coverage variants: the wired command must exit 0 on a fresh tree --------


def test_python_coverage_gate_passes_on_a_fresh_tree(tmp_path: Path) -> None:
    """`--with-coverage` wires `uv run pytest --cov --cov-fail-under=<threshold>`, which needs
    code to measure: the flavor ships `src/<module>/__init__.py`, so the gate is green instead
    of failing at 0%."""
    _generate(
        tmp_path,
        ["--flavor", "python", "--with-coverage", "--coverage-threshold", "80"],
    )
    assert (tmp_path / "src" / "demo" / "__init__.py").is_file(), "coverage has nothing to measure"
    # the harness venv carries pytest-cov, so this is the shipped command minus the `uv run`
    # wrapper — no network, and the tree's own pyproject supplies source/pythonpath/fail_under.
    result = _run(
        tmp_path,
        [sys.executable, "-m", "pytest", "--cov", "--cov-fail-under=80", "-q"],
    )
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"
    assert "Total coverage: 100.00%" in result.stdout, result.stdout


@pytest.mark.skipif(shutil.which("cargo-llvm-cov") is None, reason="needs cargo-llvm-cov on PATH")
def test_rust_coverage_gate_passes_on_a_fresh_tree(tmp_path: Path) -> None:
    _generate(tmp_path, ["--flavor", "rust", "--with-coverage", "--coverage-threshold", "80"])
    for command in (
        ["cargo", "llvm-cov", "--workspace", "--lcov", "--output-path", "lcov.info"],
        ["cargo", "llvm-cov", "report", "--fail-under-lines", "80"],
    ):
        result = _run(tmp_path, command)
        assert result.returncode == 0, f"{' '.join(command)}\n{result.stdout}\n{result.stderr}"


def test_rust_coverage_job_installs_what_it_calls(tmp_path: Path) -> None:
    """A bare runner has no `cargo llvm-cov` (`error: no such command: llvm-cov`): the job has
    to install the crate and its `llvm-tools-preview` component before the first call."""
    plain = tmp_path / "plain"
    plain.mkdir()
    _generate(tmp_path, ["--flavor", "ci", "--ci-variant", "rust", "--with-coverage"])
    _generate(plain, ["--flavor", "ci", "--ci-variant", "rust"])
    workflow = (tmp_path / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert f"taiki-e/install-action@{scaffold.SHA_TABLE['install-action']}" in workflow
    first_call = workflow.index("cargo llvm-cov --workspace")
    assert workflow.index("taiki-e/install-action") < first_call
    assert workflow.index("llvm-tools-preview") < first_call
    without = (plain / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "install-action" not in without, "the install step must stay scoped to coverage"
