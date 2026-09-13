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
        [sys.executable, "-m", "pytest", "-q"],
    ):
        result = _run(tmp_path, command)
        assert result.returncode == 0, f"{' '.join(command)}\n{result.stdout}\n{result.stderr}"


def test_python_generated_files_stay_ruff_formattable(tmp_path: Path) -> None:
    """`ruff format --check` is not a wired gate, so nothing repairs Python bytes; keep them
    canonical anyway so wiring it later is a one-line change."""
    ruff = shutil.which("ruff")
    if ruff is None:
        pytest.skip("needs ruff on PATH")
    _generate(tmp_path, ["--flavor", "python"])
    result = _run(tmp_path, [ruff, "format", "--check", "."])
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"


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
