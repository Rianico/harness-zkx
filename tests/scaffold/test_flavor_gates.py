"""Fresh-tree gate contract — every gate a flavor wires must pass on generated output.

See `skills/scaffold/SKILL.md` § Adding a Flavor — Gate Contract. The misses that motivated
this file: a Rust repo wired `cargo fmt`/`clippy`/`test` but shipped no target, so all three
died on `failed to parse manifest: no targets specified`; a Python repo wired `uv run pytest`
with no tests, so the gate exited 5. Both were invisible because no test ran a generated tree
through the commands the generated `release.yml` runs.

Gates only exist for the combination the scaffold prescribes: `--flavor <lang>` plus
`--flavor ci --ci-variant <lang>` (`--flavor all` always ships the Node verify job).
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "skills" / "scaffold" / "scripts" / "scaffold.py"


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
