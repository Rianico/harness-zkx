"""Tests for gh-router subskill pr-land (skills/gh-router/subskills/pr-land/scripts/pr.sh)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SH = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts/pr.sh"
PR_TEMPLATE = REPO_ROOT / ".github/pull_request_template.md"


def test_missing_body_file_exits_2() -> None:
    """Missing or unreadable --body-file must fail loud with exit 2, never silently falling back."""
    result = subprocess.run(
        ["bash", str(PR_SH), "--head", "feature-test", "--body-file", "/nonexistent/path/pr.md"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "not found or not readable" in result.stderr.lower()
    assert "/nonexistent/path/pr.md" in result.stderr


def test_parse_args_tracks_supplied_title_and_body() -> None:
    """parse_args must record whether --title and --body/--body-file were explicitly supplied."""
    script = f"""
source "{PR_SH}"
parse_args "$@"
echo "TITLE_SUPPLIED=$TITLE_SUPPLIED BODY_SUPPLIED=$BODY_SUPPLIED"
"""
    # Neither supplied
    res = subprocess.run(["bash", "-c", script, "bash"], capture_output=True, text=True)
    assert res.returncode == 0
    assert res.stdout.strip() == "TITLE_SUPPLIED=0 BODY_SUPPLIED=0"

    # Only title supplied
    res = subprocess.run(
        ["bash", "-c", script, "bash", "--title", "feat: test"], capture_output=True, text=True
    )
    assert res.returncode == 0
    assert res.stdout.strip() == "TITLE_SUPPLIED=1 BODY_SUPPLIED=0"

    # Only body supplied
    res = subprocess.run(
        ["bash", "-c", script, "bash", "--body", "some body"], capture_output=True, text=True
    )
    assert res.returncode == 0
    assert res.stdout.strip() == "TITLE_SUPPLIED=0 BODY_SUPPLIED=1"

    # Both supplied
    res = subprocess.run(
        ["bash", "-c", script, "bash", "--title", "feat: test", "--body", "some body"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert res.stdout.strip() == "TITLE_SUPPLIED=1 BODY_SUPPLIED=1"


def test_squash_message_falls_back_when_body_is_template_or_empty() -> None:
    """When PR body matches the template or is empty, squash_message returns empty to let GitHub use commit subjects."""
    template_content = (
        PR_TEMPLATE.read_text() if PR_TEMPLATE.is_file() else "## Summary\n<!-- template -->\n"
    )

    # Empty body -> empty squash message
    res = subprocess.run(
        ["bash", "-c", f'source "{PR_SH}"\nBODY=""\nsquash_message'],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0
    assert res.stdout == ""

    # Template body -> empty squash message
    res = subprocess.run(
        ["bash", "-c", f'source "{PR_SH}"\nBODY="$TEMPLATE"\nsquash_message'],
        capture_output=True,
        text=True,
        env={**os.environ, "TEMPLATE": template_content},
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0
    assert res.stdout == ""

    # Authored body -> preserved
    authored = "feat: add cool feature\n\nCo-authored-by: someone <someone@example.com>"
    res = subprocess.run(
        ["bash", "-c", f'source "{PR_SH}"\nBODY="$AUTHORED"\nsquash_message'],
        capture_output=True,
        text=True,
        env={**os.environ, "AUTHORED": authored},
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0
    assert res.stdout == authored


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
    script = f'source "{PR_SH}"\npr_conflict_verdict "$1" "$2"'
    res = subprocess.run(["bash", "-c", script, "bash", mergeable, state], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert res.stdout == expected, label


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
source "{PR_SH}"
REPO="test/repo"
HEAD_REF="feat-branch"
parse_args --title "Updated Title"
create_or_reuse_pr
echo "FINAL_TITLE=$TITLE"
echo "FINAL_BODY=$BODY"
"""
    res = subprocess.run(
        ["bash", "-c", test_run_title],
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
source "{PR_SH}"
REPO="test/repo"
HEAD_REF="feat-branch"
parse_args --watch
create_or_reuse_pr
echo "FINAL_TITLE=$TITLE"
echo "FINAL_BODY=$BODY"
"""
    res = subprocess.run(
        ["bash", "-c", test_run_none],
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
source "{PR_SH}"
REPO="test/repo"
NUM="999"
BASE="main"
check_conflicts
"""
    res = subprocess.run(
        ["bash", "-c", test_conflicting],
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
source "{PR_SH}"
REPO="test/repo"
NUM="888"
BASE="main"
check_conflicts
"""
    res = subprocess.run(
        ["bash", "-c", test_clean],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0
    assert "conflicting" not in res.stderr

    # Case 3: Behind PR 777
    test_behind = f"""
source "{PR_SH}"
REPO="test/repo"
NUM="777"
BASE="main"
check_conflicts
"""
    res = subprocess.run(
        ["bash", "-c", test_behind],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0
    assert "warning: head branch is behind main" in res.stderr

