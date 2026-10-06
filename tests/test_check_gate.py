"""Tests for scripts/check.sh and .githooks/pre-commit — the local CI gate mirror.

Covers file presence, mode bits, the gate command ordering contract, the
graded-root fix (check.sh grades its own repo, not the caller's git root),
stubbed-toolchain proofs that every gate runs and a failed gate stops the run,
and the hook's `HARNESS_CHECK_SKIP_TESTS=1` escape.

Every test either passes `--skip-tests` (directly or via the env escape) or runs
the script against a stubbed toolchain, so no test can launch a nested
`uv run pytest`. The former `HARNESS_CHECK_GATE` skipif anti-recursion guard was
redundant (the variable was write-only) and has been removed, with no new reader.
Real-toolchain end-to-end tests probe `uv run --no-sync basedpyright --version`
and skip when it fails; the CI pytest job runs `uv run --no-sync pytest` with
basedpyright uninstalled, so that probe fails there, the five `@REQUIRES_UV` tests
skip, and the stubbed-toolchain tests carry gate coverage in CI.
"""

from __future__ import annotations

import functools
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
# The root as check.sh prints it: physically resolved (pwd -P). On macOS this is
# /private/tmp/..., so banner asserts must use the physical path, not a raw /tmp.
HARNESS_ROOT = os.path.realpath(REPO_ROOT)
CHECK_SCRIPT = REPO_ROOT / "scripts" / "check.sh"
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

GATE_COMMANDS = [
    "uv run ruff check .",
    "uv run ruff format --check .",
    "uv run basedpyright --warnings",
    "uv run pytest",
]

# The stubbed `uv` argv log mirrors GATE_COMMANDS with the `uv ` prefix removed.
STUB_GATE_LOG = [command.removeprefix("uv ") for command in GATE_COMMANDS]

REAL_TIMEOUT = 600
STUB_TIMEOUT = 60


def _run(
    *args: str,
    cwd: Path = REPO_ROOT,
    env: dict[str, str] | None = None,
    timeout: int = REAL_TIMEOUT,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [*args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=env,
    )


@functools.cache
def _real_toolchain_ready() -> bool:
    """True only if `uv run --no-sync` finds a provisioned basedpyright; never syncs."""
    uv = shutil.which("uv")
    if uv is None:
        return False
    try:
        result = subprocess.run(
            [uv, "run", "--no-sync", "basedpyright", "--version"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=REAL_TIMEOUT,
        )
    except OSError, subprocess.TimeoutExpired:
        return False
    return result.returncode == 0


# Evaluated once at import; the probe itself uses --no-sync, so collection stays offline.
REQUIRES_UV = pytest.mark.skipif(
    not _real_toolchain_ready(),
    reason="real uv toolchain not pre-provisioned (uv run --no-sync basedpyright --version failed)",
)


@functools.cache
def _skip_tests_run() -> subprocess.CompletedProcess[str]:
    """One shared `check.sh --skip-tests` run for the gate-banner assertions."""
    return _run("bash", "scripts/check.sh", "--skip-tests")


def _stub_toolchain(
    tmp_path: Path, fail_pattern: str | None = None, log_pwd: bool = False
) -> tuple[dict[str, str], Path]:
    """A fake `uv` on PATH that logs its argv and optionally fails one gate pattern.

    With `log_pwd`, each call also writes a `pwd=$PWD` line, letting a test prove
    which directory the gate ran in without a real toolchain.
    """
    stub_bin = tmp_path / "bin"
    stub_bin.mkdir()
    calls = tmp_path / "calls.log"
    record = 'printf "%s\\npwd=%s\\n" "$*" "$PWD"' if log_pwd else 'printf "%s\\n" "$*"'
    lines = ["#!/usr/bin/env bash", f'{record} >> "{calls}"']
    if fail_pattern is not None:
        lines.append(f'case "$*" in "{fail_pattern}"*) exit 1;; esac')
    lines.append("exit 0")
    stub = stub_bin / "uv"
    _ = stub.write_text("\n".join(lines) + "\n")
    stub.chmod(0o755)
    env = {**os.environ, "PATH": f"{stub_bin}{os.pathsep}{os.environ['PATH']}"}
    return env, calls


def _make_foreign_repo(tmp_path: Path) -> Path:
    """A temp git repo whose only Python file trips `ruff check` (F401 unused import)."""
    foreign = tmp_path / "foreign"
    # exist_ok: pytest truncates both foreign-root test names to the same tmp_path
    # basename, so a rerun may land in a directory an earlier attempt populated.
    foreign.mkdir(parents=True, exist_ok=True)
    _ = subprocess.run(
        ["git", "init", "-q", str(foreign)],
        capture_output=True,
        text=True,
        check=True,
        timeout=STUB_TIMEOUT,
    )
    _ = (foreign / "bad.py").write_text("import os\n", encoding="utf-8")
    return foreign


def _assert_grades_harness_from_foreign_dir(tmp_path: Path, extra_env: dict[str, str]) -> None:
    """From a foreign git root, --skip-tests must still pass and name the harness root.

    Pre-fix (`git rev-parse --show-toplevel`), check.sh would cd into the foreign
    repo and gate 1 (`uv run ruff check .`) would fail on bad.py, so the exit-0
    assert below is the discriminator.
    """
    foreign = _make_foreign_repo(tmp_path)
    result = _run(
        "bash", str(CHECK_SCRIPT), "--skip-tests", cwd=foreign, env={**os.environ, **extra_env}
    )
    assert result.returncode == 0, f"graded the foreign tree:\n{result.stdout}\n{result.stderr}"
    assert f"==> checking {HARNESS_ROOT}" in result.stdout


@REQUIRES_UV
def test_check_script_grades_harness_root_not_caller_git_root(tmp_path: Path) -> None:
    _assert_grades_harness_from_foreign_dir(tmp_path, {})


@REQUIRES_UV
def test_check_script_grades_harness_root_despite_foreign_git_dir(tmp_path: Path) -> None:
    foreign = _make_foreign_repo(tmp_path)
    _assert_grades_harness_from_foreign_dir(tmp_path, {"GIT_DIR": str(foreign / ".git")})


@REQUIRES_UV
def test_check_script_grades_harness_root_despite_foreign_git_work_tree(
    tmp_path: Path,
) -> None:
    foreign = _make_foreign_repo(tmp_path)
    _assert_grades_harness_from_foreign_dir(tmp_path, {"GIT_WORK_TREE": str(foreign)})


def test_check_script_symlinked_entry_point_refuses_foreign_tree(tmp_path: Path) -> None:
    """TM reproduction: a symlinked check.sh must NOT attest the directory it links into.

    `ln -s <harness>/scripts/check.sh <probe>/bin/check.sh; bash <probe>/bin/check.sh`
    resolved BASH_SOURCE to the shadow `bin` dir, so the root became the shadow and
    every gate silently linted an empty tree. The ownership check must refuse instead.
    """
    shadow = tmp_path / "symprobe"
    shadow_bin = shadow / "bin"
    shadow_bin.mkdir(parents=True)
    link = shadow_bin / "check.sh"
    os.symlink(CHECK_SCRIPT, link)
    env, calls = _stub_toolchain(tmp_path)
    result = _run("bash", str(link), "--skip-tests", cwd=shadow, env=env, timeout=STUB_TIMEOUT)
    assert result.returncode == 3, result.stdout + result.stderr
    assert "refusing:" in result.stderr
    assert "is not the claude-skills-harness repo" in result.stderr
    assert HARNESS_ROOT not in result.stderr, "refusal named the harness root"
    assert "checking" not in result.stdout, "symlink attested a foreign tree"
    assert not calls.exists(), "refusal ran gates anyway"


def test_check_script_unsets_cdpath_and_grades_harness(tmp_path: Path) -> None:
    """A shadowing CDPATH must never divert grading onto the shadow tree.

    Pins `unset CDPATH` (removing the line fails the source assert) and proves the
    effect: with CDPATH aimed at a decoy, check.sh still grades the harness root.
    """
    # Whole-line match: the explanatory comment also contains the phrase.
    assert "unset CDPATH" in CHECK_SCRIPT.read_text(encoding="utf-8").splitlines()
    env, calls = _stub_toolchain(tmp_path, log_pwd=True)
    shadow = tmp_path / "shadow"
    (shadow / "scripts").mkdir(parents=True)
    env["CDPATH"] = str(shadow)
    result = _run(
        "bash", str(CHECK_SCRIPT), "--skip-tests", cwd=tmp_path, env=env, timeout=STUB_TIMEOUT
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"==> checking {HARNESS_ROOT}" in result.stdout
    assert str(shadow) not in result.stdout, "graded the CDPATH shadow"
    records = calls.read_text().splitlines()
    assert [line for line in records if not line.startswith("pwd=")] == STUB_GATE_LOG[:3]
    assert set(line for line in records if line.startswith("pwd=")) == {f"pwd={HARNESS_ROOT}"}


def test_files_exist_and_are_executable() -> None:
    for path in (CHECK_SCRIPT, HOOK):
        assert path.is_file(), f"{path} missing"
        assert stat.S_IMODE(path.stat().st_mode) == 0o755, f"{path} is not mode 0755"


def test_check_script_content_contract() -> None:
    text = CHECK_SCRIPT.read_text(encoding="utf-8")
    assert "set -euo pipefail" in text
    previous = -1
    for command in GATE_COMMANDS:
        index = text.index(command)
        assert index > previous, f"gate command out of order: {command!r}"
        previous = index


@REQUIRES_UV
def test_skip_tests_exit_zero_and_gate_banners() -> None:
    result = _skip_tests_run()
    assert result.returncode == 0, result.stderr[-2000:]
    # Regression: check.sh prints the PHYSICAL root (pwd -P), never a /tmp alias.
    assert f"==> checking {HARNESS_ROOT}" in result.stdout
    for banner in GATE_COMMANDS[:3]:
        assert banner in result.stdout, f"gate banner missing from stdout: {banner!r}"


@REQUIRES_UV
def test_skip_tests_banner_reports_skipped_gate() -> None:
    result = _skip_tests_run()
    assert result.returncode == 0, result.stderr[-2000:]
    assert "SKIPPED" in result.stdout
    assert "uv run pytest was skipped" in result.stdout
    assert "3/4 gates passed (pytest skipped: --skip-tests)" in result.stdout
    # Pinning the absence: the unconditional "All gates passed." must not lie
    # when gate 4 never ran.
    assert "All gates passed." not in result.stdout


def test_stubbed_gates_all_invoked_in_order(tmp_path: Path) -> None:
    """Every gate command actually reaches `uv`, exactly once, in CI order."""
    env, calls = _stub_toolchain(tmp_path)
    result = _run("bash", str(CHECK_SCRIPT), env=env, timeout=STUB_TIMEOUT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert calls.read_text().splitlines() == STUB_GATE_LOG
    assert "All gates passed." in result.stdout


def test_stubbed_gate2_failure_stops_before_gate3(tmp_path: Path) -> None:
    """A failing gate 2 aborts the run; gate 3/4 tools are never invoked."""
    env, calls = _stub_toolchain(tmp_path, fail_pattern="run ruff format --check ")
    result = _run("bash", str(CHECK_SCRIPT), env=env, timeout=STUB_TIMEOUT)
    combined = result.stdout + result.stderr
    assert result.returncode != 0, combined
    assert "FAILED: gate 2/4" in combined
    invoked = calls.read_text()
    assert "run ruff check ." in invoked
    assert "basedpyright" not in invoked, "early stop broken: gate 3 ran after gate 2 failed"
    assert "run pytest" not in invoked, "early stop broken: gate 4 ran after gate 2 failed"
    assert "All gates passed." not in result.stdout


def test_check_script_deep_relative_invocation_grades_harness(tmp_path: Path) -> None:
    """Invoked as `bash ../../.../check.sh` from a deep cwd, the BASH_SOURCE anchor holds."""
    env, calls = _stub_toolchain(tmp_path)
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    relative = os.path.relpath(CHECK_SCRIPT, deep)
    result = _run("bash", relative, "--skip-tests", cwd=deep, env=env, timeout=STUB_TIMEOUT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert calls.read_text().splitlines() == STUB_GATE_LOG[:3]
    assert f"==> checking {HARNESS_ROOT}" in result.stdout
    assert "3/4 gates passed (pytest skipped: --skip-tests)" in result.stdout


def test_check_script_gates_run_in_harness_root_from_foreign_cwd(tmp_path: Path) -> None:
    """T3 anchor fix, CI-safe: from a foreign cwd the gate tools still run in the root.

    The stub records `$PWD` per call; every gate must execute in the harness root,
    not the foreign cwd it was invoked from.
    """
    env, calls = _stub_toolchain(tmp_path, log_pwd=True)
    foreign_cwd = tmp_path / "elsewhere"
    foreign_cwd.mkdir()
    result = _run("bash", str(CHECK_SCRIPT), env=env, cwd=foreign_cwd, timeout=STUB_TIMEOUT)
    assert result.returncode == 0, result.stdout + result.stderr
    records = calls.read_text().splitlines()
    assert [line for line in records if not line.startswith("pwd=")] == STUB_GATE_LOG
    assert set(line for line in records if line.startswith("pwd=")) == {f"pwd={HARNESS_ROOT}"}


def test_pre_commit_hook_forwards_to_check_script(tmp_path: Path) -> None:
    """The hook must `exec scripts/check.sh` so all four real gates reach `uv`.

    Asserted through the stub argv log (a side effect of the real invocation),
    not banner text: echoing gate names from the hook cannot fake the log, and a
    body that skips `exec` (e.g. `echo done; exit 0`) leaves the log file absent.
    """
    env, calls = _stub_toolchain(tmp_path, log_pwd=True)
    # No env var, no args: the hook must run every gate, exactly as check.sh does.
    result = _run("bash", str(HOOK), env=env, timeout=STUB_TIMEOUT)
    assert result.returncode == 0, result.stdout + result.stderr
    records = calls.read_text().splitlines()
    assert [line for line in records if not line.startswith("pwd=")] == STUB_GATE_LOG


def test_pre_commit_hook_skip_tests_env_escape(tmp_path: Path) -> None:
    """HARNESS_CHECK_SKIP_TESTS=1 makes the hook run check.sh --skip-tests."""
    env, calls = _stub_toolchain(tmp_path)
    env["HARNESS_CHECK_SKIP_TESTS"] = "1"
    result = _run("bash", str(HOOK), env=env, timeout=STUB_TIMEOUT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "3/4 gates passed (pytest skipped: --skip-tests)" in result.stdout
    assert "All gates passed." not in result.stdout
    assert "run pytest" not in calls.read_text()


def test_unknown_flag_exits_two_with_usage() -> None:
    result = _run("bash", "scripts/check.sh", "--bogus")
    assert result.returncode == 2
    assert "usage" in result.stderr
