"""Tests for gh-router subskill pr-land (skills/gh-router/subskills/pr-land/scripts/pr.py and pr.sh)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
PR_PY = PR_SCRIPTS / "pr.py"
PR_SH = PR_SCRIPTS / "pr.sh"
PR_TEMPLATE = REPO_ROOT / ".github/pull_request_template.md"

if str(PR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PR_SCRIPTS))

from pr import (  # noqa: E402
    PrError,
    parse_args,
    pr_conflict_verdict,
    run_command,
    squash_message,
)


def test_missing_body_file_exits_2() -> None:
    """Missing or unreadable --body-file must fail loud with exit 2, never silently falling back."""
    # Test pr.py directly
    result_py = subprocess.run(
        [
            sys.executable,
            str(PR_PY),
            "--head",
            "feature-test",
            "--body-file",
            "/nonexistent/path/pr.md",
        ],
        capture_output=True,
        text=True,
    )
    assert result_py.returncode == 2
    assert "not found or not readable" in result_py.stderr.lower()
    assert "/nonexistent/path/pr.md" in result_py.stderr

    # Test pr.sh wrapper
    result_sh = subprocess.run(
        ["bash", str(PR_SH), "--head", "feature-test", "--body-file", "/nonexistent/path/pr.md"],
        capture_output=True,
        text=True,
    )
    assert result_sh.returncode == 2
    assert "not found or not readable" in result_sh.stderr.lower()
    assert "/nonexistent/path/pr.md" in result_sh.stderr


def test_pr_sh_wrapper_delegates_to_pr_py() -> None:
    """pr.sh must be an executable wrapper delegating argv to pr.py."""
    result = subprocess.run(
        ["bash", str(PR_SH), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "pr.py" in result.stdout


def test_parse_args_tracks_supplied_title_and_body() -> None:
    """parse_args must record whether --title and --body/--body-file were explicitly supplied."""
    # Neither supplied
    opts = parse_args([])
    assert not opts.title_supplied
    assert not opts.body_supplied

    # Only title supplied
    opts = parse_args(["--title", "feat: test"])
    assert opts.title_supplied
    assert not opts.body_supplied

    # Only body supplied
    opts = parse_args(["--body", "some body"])
    assert not opts.title_supplied
    assert opts.body_supplied

    # Only body-file supplied
    opts = parse_args(["--body-file", "tmp/body.md"])
    assert not opts.title_supplied
    assert opts.body_supplied

    # Both supplied
    opts = parse_args(["--title", "feat: test", "--body", "some body"])
    assert opts.title_supplied
    assert opts.body_supplied


def test_squash_message_falls_back_when_body_is_template_or_empty() -> None:
    """When PR body matches the template or is empty, squash_message returns empty to let GitHub use commit subjects."""
    template_content = (
        PR_TEMPLATE.read_text(encoding="utf-8")
        if PR_TEMPLATE.is_file()
        else "## Summary\n<!-- template -->\n"
    )

    # Empty body -> empty squash message
    assert squash_message("", template_path=PR_TEMPLATE) == ""

    # Template body -> empty squash message
    assert squash_message(template_content, template_path=PR_TEMPLATE) == ""

    # Authored body -> preserved
    authored = "feat: add cool feature\n\nCo-authored-by: someone <someone@example.com>"
    assert squash_message(authored, template_path=PR_TEMPLATE) == authored


CONFLICT_CASES = [
    ("conflicting REST false/dirty", "false", "dirty", "conflicting"),
    ("conflicting REST false/clean", "false", "clean", "conflicting"),
    ("conflicting GraphQL CONFLICTING/DIRTY", "CONFLICTING", "DIRTY", "conflicting"),
    ("conflicting dirty with true", "true", "dirty", "conflicting"),
    ("behind branch", "true", "behind", "behind"),
    ("behind branch uppercase", "MERGEABLE", "BEHIND", "behind"),
    ("clean branch", "true", "clean", "clean"),
    ("clean branch uppercase", "MERGEABLE", "CLEAN", "clean"),
    ("unknown calculation null/unknown", "null", "unknown", "unknown"),
    ("unknown calculation empty", "", "", "unknown"),
]


@pytest.mark.parametrize(
    ("label", "mergeable", "state", "expected"), CONFLICT_CASES, ids=[c[0] for c in CONFLICT_CASES]
)
def test_pr_conflict_verdict(label: str, mergeable: str, state: str, expected: str) -> None:
    """pr_conflict_verdict pure function evaluates mergeable and mergeable_state/mergeStateStatus."""
    assert pr_conflict_verdict(mergeable, state) == expected, label


def test_reuse_pr_only_patches_supplied_fields(tmp_path: Path) -> None:
    """Reusing PR must only patch fields explicitly supplied, never overwriting body with template."""
    mock_bin = tmp_path / "bin"
    mock_bin.mkdir()
    gh_mock = mock_bin / "gh"
    log_file = tmp_path / "gh_calls.log"

    gh_script = f"""#!/usr/bin/env bash
echo "$@" >> "{log_file}"
for arg in "$@"; do
    if [[ "$arg" =~ repos/.*/pulls\\?head= ]]; then
        echo "123"
        exit 0
    elif [[ "$arg" =~ \\.title ]]; then
        echo "Authored Title"
        exit 0
    elif [[ "$arg" =~ \\.body ]]; then
        echo "Authored Body"
        exit 0
    fi
done
exit 0
"""
    _ = gh_mock.write_text(gh_script)
    gh_mock.chmod(0o755)

    env = {
        **os.environ,
        "PATH": f"{mock_bin}:{os.environ.get('PATH', '')}",
        "REPO": "test/repo",
        "HEAD_REF": "feat-branch",
    }

    # Case 1: only --title supplied
    if log_file.exists():
        log_file.unlink()
    test_run_title = f"""
import sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import create_or_reuse_pr
num, title, body = create_or_reuse_pr(
    repo="test/repo",
    head_ref="feat-branch",
    base="main",
    title="Updated Title",
    body="",
    title_supplied=True,
    body_supplied=False,
)
print(f"FINAL_TITLE={{title}}")
print(f"FINAL_BODY={{body}}")
"""
    res = subprocess.run(
        [sys.executable, "-c", test_run_title],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0, res.stderr
    assert "updating PR #123: title" in res.stderr
    assert "FINAL_TITLE=Updated Title" in res.stdout
    assert "FINAL_BODY=Authored Body" in res.stdout

    calls = log_file.read_text()
    assert "PATCH -f title=Updated Title" in calls
    assert "body=" not in calls  # body must NOT have been sent in PATCH

    # Case 2: neither title nor body supplied
    log_file.unlink()
    test_run_none = f"""
import sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import create_or_reuse_pr
num, title, body = create_or_reuse_pr(
    repo="test/repo",
    head_ref="feat-branch",
    base="main",
    title="Fallback Title",
    body="Fallback Body",
    title_supplied=False,
    body_supplied=False,
)
print(f"FINAL_TITLE={{title}}")
print(f"FINAL_BODY={{body}}")
"""
    res = subprocess.run(
        [sys.executable, "-c", test_run_none],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0, res.stderr
    assert "updating PR" not in res.stderr
    assert "FINAL_TITLE=Authored Title" in res.stdout
    assert "FINAL_BODY=Authored Body" in res.stdout

    calls = log_file.read_text()
    assert "PATCH" not in calls  # No PATCH should be performed


def test_check_conflicts_detection(tmp_path: Path) -> None:
    """check_conflicts must exit 1 immediately on conflicting state, naming files and resolution."""
    mock_bin = tmp_path / "bin"
    mock_bin.mkdir(exist_ok=True)
    gh_mock = mock_bin / "gh"

    gh_script = """#!/usr/bin/env bash
for arg in "$@"; do
    if [[ "$arg" =~ repos/.*/pulls/999 ]]; then
        printf 'false\tdirty\thttps://github.com/test/repo/pull/999\\n'
        exit 0
    elif [[ "$arg" =~ repos/.*/pulls/888 ]]; then
        printf 'true\tclean\thttps://github.com/test/repo/pull/888\\n'
        exit 0
    elif [[ "$arg" =~ repos/.*/pulls/777 ]]; then
        printf 'true\tbehind\thttps://github.com/test/repo/pull/777\\n'
        exit 0
    elif [[ "$arg" == "files" ]]; then
        echo "file1.txt file2.py"
        exit 0
    fi
done
exit 0
"""
    _ = gh_mock.write_text(gh_script)
    gh_mock.chmod(0o755)

    env = {
        **os.environ,
        "PATH": f"{mock_bin}:{os.environ.get('PATH', '')}",
    }

    # Case 1: Conflicting PR 999
    test_conflicting = f"""
import sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import check_conflicts
ok = check_conflicts("test/repo", "999", "main")
sys.exit(0 if ok else 1)
"""
    res = subprocess.run(
        [sys.executable, "-c", test_conflicting],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 1
    assert "PR https://github.com/test/repo/pull/999" in res.stderr
    assert "conflicting: mergeable=false merge_state_status=dirty" in res.stderr
    assert "files: file1.txt file2.py" in res.stderr
    assert "resolve: merge or rebase origin/main into the head branch, then re-run" in res.stderr

    # Case 2: Clean PR 888
    test_clean = f"""
import sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import check_conflicts
ok = check_conflicts("test/repo", "888", "main")
sys.exit(0 if ok else 1)
"""
    res = subprocess.run(
        [sys.executable, "-c", test_clean],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0
    assert "conflicting" not in res.stderr

    # Case 3: Behind PR 777
    test_behind = f"""
import sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import check_conflicts
ok = check_conflicts("test/repo", "777", "main")
sys.exit(0 if ok else 1)
"""
    res = subprocess.run(
        [sys.executable, "-c", test_behind],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0
    assert "warning: head branch is behind main" in res.stderr


def test_run_command_timeout_raises_pr_error() -> None:
    """run_command must raise PrError with command context when timeout expires."""
    with pytest.raises(PrError) as exc_info:
        run_command(["sleep", "2"], timeout=0.1)
    assert "timed out after 0.1s" in str(exc_info.value)
    assert "sleep 2" in str(exc_info.value)


def test_check_conflicts_fails_loud_on_api_error(tmp_path: Path) -> None:
    """check_conflicts must raise PrError when gh api returns non-zero, rather than silently returning True."""
    mock_bin = tmp_path / "bin"
    mock_bin.mkdir(exist_ok=True)
    gh_mock = mock_bin / "gh"
    _ = gh_mock.write_text("""#!/usr/bin/env bash
echo "api rate limited" >&2
exit 1
""")
    gh_mock.chmod(0o755)

    env = {
        **os.environ,
        "PATH": f"{mock_bin}:{os.environ.get('PATH', '')}",
    }

    test_script = f"""
import sys
import time
time.sleep = lambda _s: None  # retry-now semantics are the contract; wall-clock waits are not
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import check_conflicts, PrError
try:
    check_conflicts("test/repo", "123", "main")
    print("FAILED_SILENTLY")
    sys.exit(0)
except PrError as e:
    print(f"CAUGHT_PR_ERROR: {{e}}")
    sys.exit(42)
"""
    res = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 42
    assert (
        "CAUGHT_PR_ERROR: failed to check PR #123 mergeable state: api rate limited" in res.stdout
    )


def test_check_trailers_fails_loud_on_body_fetch_error(tmp_path: Path) -> None:
    """check_trailers must raise PrError when body fetch fails, rather than falling through to fallback body."""
    mock_bin = tmp_path / "bin"
    mock_bin.mkdir(exist_ok=True)
    gh_mock = mock_bin / "gh"
    _ = gh_mock.write_text("""#!/usr/bin/env bash
for arg in "$@"; do
    if [[ "$arg" =~ repos/.*/pulls\\?head= ]]; then
        echo "123"
        exit 0
    elif [[ "$arg" =~ \\.body ]]; then
        echo "500 internal server error" >&2
        exit 1
    fi
done
exit 0
""")
    gh_mock.chmod(0o755)

    env = {
        **os.environ,
        "PATH": f"{mock_bin}:{os.environ.get('PATH', '')}",
    }

    test_script = f"""
import sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import check_trailers, PrError
try:
    check_trailers("test/repo", "feat-branch", "", body_supplied=False)
    print("FAILED_SILENTLY")
    sys.exit(0)
except PrError as e:
    print(f"CAUGHT_PR_ERROR: {{e}}")
    sys.exit(42)
"""
    res = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 42
    assert (
        "CAUGHT_PR_ERROR: failed to fetch body for PR #123: 500 internal server error" in res.stdout
    )


def test_dump_failure_logs_survives_view_timeout(tmp_path: Path) -> None:
    """dump_failure_logs must warn and continue to dump checks if gh run view --log times out."""
    mock_bin = tmp_path / "bin"
    mock_bin.mkdir(exist_ok=True)
    gh_mock = mock_bin / "gh"
    _ = gh_mock.write_text("""#!/usr/bin/env bash
for arg in "$@"; do
    if [[ "$arg" =~ \\.head\\.sha ]]; then
        echo "abc1234"
        exit 0
    elif [[ "$arg" =~ \\.workflow_runs ]]; then
        echo "99999"
        exit 0
    elif [[ "$arg" == "--log" ]]; then
        sleep 5
        exit 0
    elif [[ "$arg" == "checks" ]]; then
        echo "test-suite   fail   1m"
        exit 0
    fi
done
exit 0
""")
    gh_mock.chmod(0o755)

    env = {
        **os.environ,
        "PATH": f"{mock_bin}:{os.environ.get('PATH', '')}",
    }

    test_script = f"""
import sys
sys.path.insert(0, "{PR_SCRIPTS}")
import pr
pr.LOG_TIMEOUT = 0.2
pr.dump_failure_logs("test/repo", "123")
"""
    res = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0
    assert "warning: could not fetch run logs: command timed out after 0.2s" in res.stderr
    assert "test-suite   fail   1m" in res.stderr
