"""Smoke tests for the gh-router scripts: syntax, executability, help contract, lib wiring.

The model-facing contract of these scripts is their `--help` header and their exit codes,
so that is what is pinned here — no network, no gh auth required.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GH_ROUTER = REPO_ROOT / "skills/gh-router"
LIBS = GH_ROUTER / "lib"
# Scripts with a `--help` contract that must answer without touching gh or the repo.
SCRIPTS = [
    GH_ROUTER / "scripts/state.sh",
    GH_ROUTER / "scripts/ci.sh",
    GH_ROUTER / "subskills/gh-release/scripts/confirm.sh",
    GH_ROUTER / "scripts/changelog.sh",
    GH_ROUTER / "subskills/pr-land/scripts/pr.sh",
    GH_ROUTER / "subskills/pr-refine/scripts/refine.sh",
]


def test_scripts_exist_and_are_executable() -> None:
    for script in SCRIPTS:
        assert script.is_file(), f"missing {script}"
        assert script.stat().st_mode & 0o111, f"{script} is not executable"


def test_scripts_parse_with_bash() -> None:
    for script in SCRIPTS:
        result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
        assert result.returncode == 0, f"{script} does not parse:\n{result.stderr}"


def test_help_is_brief_and_does_not_need_the_network() -> None:
    """`--help` must answer from the file header alone, before any gh/repo access."""
    for script in SCRIPTS:
        result = subprocess.run(["bash", str(script), "--help"], capture_output=True, text=True)
        assert result.returncode == 0, f"{script} --help failed: {result.stderr}"
        assert "Usage:" in result.stdout, f"{script} --help does not print a Usage line"
        assert len(result.stdout.splitlines()) <= 14, f"{script} --help is not brief"


def test_changelog_sync_dry_run_decides_without_mutating() -> None:
    """`changelog.sh sync` reports a verdict and touches nothing unless --apply is passed."""
    script = REPO_ROOT / "skills/gh-router/scripts/changelog.sh"

    def changelog_status() -> str:
        return subprocess.run(
            ["git", "status", "--porcelain", "--", "CHANGELOG.md"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        ).stdout

    before = changelog_status()
    result = subprocess.run(
        ["bash", str(script), "sync"], capture_output=True, text=True, cwd=REPO_ROOT
    )
    assert result.returncode in (0, 1), f"dry run failed unexpectedly: {result.stderr}"
    combined = (result.stdout + result.stderr).lower()
    assert "changelog.md" in combined, "verdict does not name the file it inspected"
    assert changelog_status() == before, "dry run mutated the working tree"


def _shell_scripts() -> list[Path]:
    return sorted(GH_ROUTER.rglob("*.sh"))


def test_every_script_sources_only_libs_that_exist() -> None:
    """Shared code moved to lib/ when it was split by concern.

    A stale source path fails loudly here instead of at run time inside a release, and the
    count assertion keeps this guard from passing vacuously if the wiring is ever removed.
    """
    wired = 0
    for script in _shell_scripts():
        text = script.read_text()
        for match in re.finditer(r'^source "\$LIB_DIR/([^"]+)"', text, re.MULTILINE):
            lib = LIBS / match.group(1)
            assert lib.is_file(), (
                f"{script.relative_to(REPO_ROOT)} sources missing lib/{match.group(1)}"
            )
            wired += 1
        if "LIB_DIR" in text:
            assert 'LIB_DIR="$(cd' in text, (
                f"{script.relative_to(REPO_ROOT)} uses LIB_DIR without defining it"
            )
    assert wired >= 8, f"expected the scripts to source lib/, found {wired} wiring sites"


def test_no_script_sources_the_retired_common_helper() -> None:
    """`_common.sh` was retired into lib/{log,repo}.sh; nothing may reference it again."""
    for script in _shell_scripts():
        assert "_common.sh" not in script.read_text(), (
            f"{script.relative_to(REPO_ROOT)} references the retired helper"
        )


def test_pure_libs_install_no_trap_and_log_nothing() -> None:
    """A script that only needs a fact must be able to source it without side effects.

    repo.sh/checks.sh are consumed through command substitution, so an ERR trap or a logging
    call in them would put diagnostics on a channel callers parse as a value.
    """
    for name in ("repo.sh", "checks.sh"):
        text = (LIBS / name).read_text()
        # Match statements, not prose: these modules document that they install no trap.
        assert not re.search(r"^\s*trap\s", text, re.MULTILINE), f"lib/{name} installs a trap"
        assert not re.search(r"^\s*_log\s", text, re.MULTILINE), f"lib/{name} logs"
        assert not re.search(r"^\s*set\s+-", text, re.MULTILINE), (
            f"lib/{name} changes shell options"
        )


def test_ci_why_python_syntax_and_formatting() -> None:
    """Inline python in ci.sh must parse without SyntaxError on all supported Pythons.

    Regression test for issue #72: backslash in f-string expression caused SyntaxError on <3.12.
    """
    import ast

    ci_sh = GH_ROUTER / "scripts/ci.sh"
    text = ci_sh.read_text()
    snippets: list[str] = [m.group(1) for m in re.finditer(r"python3 -c '([^']+)'", text)]
    assert len(snippets) >= 2, (
        f"expected at least 2 inline python snippets in ci.sh, found {len(snippets)}"
    )

    for snippet in snippets:
        _ = ast.parse(snippet)

    # Execute the why snippet specifically with mock failure data
    why_snippet: str = [s for s in snippets if "bad.append" in s][0]
    mock_input = (
        '{"jobs": [{"name": "verify", "steps": [{"name": "lint", "conclusion": "failure"}]}]}'
    )
    proc = subprocess.run(
        ["python3", "-c", why_snippet],
        input=mock_input,
        capture_output=True,
        text=True,
        check=True,
    )
    assert proc.stdout.strip() == "verify › lint"


DISPATCH = GH_ROUTER / "subskills/gh-release/scripts/dispatch.sh"


def _dispatch_env(tmp_path: Path, npx_script: str) -> tuple[dict[str, str], Path]:
    """Build a hermetic PATH with fake `gh` (token) and fake `npx` (semantic-release).

    dispatch.sh runs `$_pm_exec semantic-release --dry-run`; in a dir without
    pnpm-lock.yaml that resolves to `npx --silent`. A fake `npx` on PATH lets the
    test drive the semantic-release outcome (success / no-version / failure)
    without any network or gh auth.
    """
    mock_bin = tmp_path / "bin"
    mock_bin.mkdir()
    gh_mock = mock_bin / "gh"
    gh_script = (
        "#!/usr/bin/env bash\n"
        'if [[ "$1" == "auth" && "$2" == "token" ]]; then\n'
        "  echo fake-token\n"
        "  exit 0\n"
        "fi\n"
        "exit 0\n"
    )
    _ = gh_mock.write_text(gh_script)
    _ = gh_mock.chmod(0o755)
    npx_mock = mock_bin / "npx"
    _ = npx_mock.write_text(npx_script)
    _ = npx_mock.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{mock_bin}:{os.environ.get('PATH', '')}",
    }
    return env, mock_bin


def test_dispatch_dry_run_reports_semantic_release_failure_not_no_version(
    tmp_path: Path,
) -> None:
    """Regression for #140: a failing semantic-release must surface the error.

    When semantic-release exits non-zero (e.g. SSL_ERROR_SYSCALL during git
    fetch), the script must report the failure and exit non-zero — not print
    the misleading "no new version" hint as if the release were a no-op.
    """
    npx_fails = (
        "#!/usr/bin/env bash\n"
        "echo 'SSL_ERROR_SYSCALL in function call to remote function \"git fetch\"'\n"
        "echo 'The next release version is 0.0.0'\n"
        "exit 1\n"
    )
    env, _ = _dispatch_env(tmp_path, npx_fails)
    result = subprocess.run(
        ["bash", str(DISPATCH), "--dry-run"],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    combined = result.stdout + result.stderr
    assert result.returncode != 0, f"dry-run should fail on semantic-release error:\n{combined}"
    assert "failed" in combined, f"failure not reported:\n{combined}"
    assert "SSL_ERROR_SYSCALL" in combined, f"error tail not surfaced:\n{combined}"
    assert "no new version" not in combined, f"misreported as no-op instead of failure:\n{combined}"


def test_dispatch_dry_run_still_reports_no_new_version_on_clean_noop(
    tmp_path: Path,
) -> None:
    """Exit 0 with no version line must still print the "no new version" hint."""
    npx_noop = "#!/usr/bin/env bash\necho 'No commits since last release'\nexit 0\n"
    env, _ = _dispatch_env(tmp_path, npx_noop)
    result = subprocess.run(
        ["bash", str(DISPATCH), "--dry-run"],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0, f"clean noop should succeed:\n{combined}"
    assert "no new version" in combined, f"noop hint missing:\n{combined}"


def test_dispatch_dry_run_reports_next_version_on_success(tmp_path: Path) -> None:
    """Exit 0 with a version line must print the next version and succeed."""
    npx_ok = (
        "#!/usr/bin/env bash\n"
        "echo 'The next release version is 1.2.3'\n"
        "echo ''\n"
        "echo '## 1.2.3'\n"
        "echo '### Features'\n"
        "echo '* add thing'\n"
        "exit 0\n"
    )
    env, _ = _dispatch_env(tmp_path, npx_ok)
    result = subprocess.run(
        ["bash", str(DISPATCH), "--dry-run"],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    combined = result.stdout + result.stderr
    assert result.returncode == 0, f"successful preview should succeed:\n{combined}"
    assert "next version: v1.2.3" in combined, f"next version not reported:\n{combined}"
