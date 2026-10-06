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

import pr as pr_mod  # noqa: E402
from pr import (  # noqa: E402
    PrError,
    RefusalError,
    UsageError,
    check_trailers,
    checks_verdict,
    clean_squash_body,
    is_unfilled_body,
    merge_pr,
    parse_args,
    pr_conflict_verdict,
    resolve_squash_message,
    run_command,
    squash_message,
    stamp_changelog,
    unreleased_attributes_pr,
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
    """squash_message keeps the empty sentinel for template/empty bodies; the merge/check layer refuses that case (see test_merge_pr_never_omits_commit_message)."""
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


def test_parse_args_squash_message_flags() -> None:
    """--squash-message and --squash-message-file set supplied; both together or missing arg is a usage error."""
    opts = parse_args(["--squash-message", "feat: x"])
    assert opts.squash_message == "feat: x"
    assert opts.squash_message_supplied

    opts = parse_args(["--squash-message-file", "tmp/msg.md"])
    assert opts.squash_message_file == Path("tmp/msg.md")
    assert opts.squash_message_supplied

    with pytest.raises(UsageError):
        parse_args(["--squash-message", "a", "--squash-message-file", "b"])
    with pytest.raises(UsageError):
        parse_args(["--squash-message"])
    with pytest.raises(UsageError):
        parse_args(["--squash-message-file"])


def test_resolve_squash_message_prefers_explicit() -> None:
    """An explicit message wins over the body and is sanitized through clean_squash_body."""
    explicit = (
        "## Summary\nChosen message.\n\n"
        "## Architecture\n```mermaid\ngraph TD\n    A --> B\n```\n\n"
        "<details><summary>out</summary>\ntrace\n</details>\n\n"
        "Co-authored-by: X <x@y>\nCloses #12\n"
    )
    out = resolve_squash_message("## Summary\nignored\n", explicit=explicit, supplied=True)
    assert "Chosen message." in out
    assert "Co-authored-by: X <x@y>" in out
    assert "Closes #12" in out
    assert "A --> B" not in out
    assert "<details" not in out
    assert "ignored" not in out

    assert resolve_squash_message("", explicit="feat: only this", supplied=True) == (
        "feat: only this"
    )
    with pytest.raises(UsageError):
        resolve_squash_message("## Summary\nwhatever\n", explicit="   ", supplied=True)


def test_resolve_squash_message_refuses_fallback_without_explicit(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A fallback body without an explicit message must raise RefusalError with remediation."""
    with pytest.raises(RefusalError):
        resolve_squash_message("", explicit=None, supplied=False)
    err = capsys.readouterr().err
    assert "--squash-message" in err
    assert "remediation:" in err


def test_merge_pr_never_omits_commit_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """The merge argv always carries exactly one commit_message; a fallback body refuses with no merge call."""
    calls: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(list(cmd))
        joined = " ".join(cmd)
        if "mergeable_state" in joined:
            out = "clean"
        elif "api user" in joined:
            out = "merger"
        elif "/commits" in joined:
            out = "ghuser\tWf Zyx\twf@x.io\n"
        else:
            out = '{"merged":true}'
        return subprocess.CompletedProcess(cmd, 0, out + "\n", "")

    monkeypatch.setattr(pr_mod, "run_command", fake_run)

    assert (
        merge_pr("test/repo", "7", "main", "feat: x", "## Summary\nReal.\n\nCloses #12\n") is True
    )
    merge_calls = [c for c in calls if len(c) > 2 and c[1] == "api" and "/merge" in c[2]]
    assert len(merge_calls) == 1
    msg_fields = [a for a in merge_calls[0] if a.startswith("commit_message=")]
    assert len(msg_fields) == 1
    assert "Closes #12" in msg_fields[0]

    calls.clear()
    assert merge_pr("test/repo", "7", "main", "feat: x", "") is False
    assert not [c for c in calls if len(c) > 2 and c[1] == "api" and "/merge" in c[2]]


def test_check_trailers_refuses_fallback_without_explicit(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """check_trailers mirrors the merge gate: fallback body without explicit message returns 1."""

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        joined = " ".join(cmd)
        out = "7" if "pulls?head=" in joined else ""
        return subprocess.CompletedProcess(cmd, 0, out + "\n", "")

    monkeypatch.setattr(pr_mod, "run_command", fake_run)

    rc = check_trailers("test/repo", "feat-branch", "", body_supplied=True)
    assert rc == 1
    err = capsys.readouterr().err
    assert "--squash-message" in err


def test_resolve_squash_message_refuses_raw_token_body_with_explicit() -> None:
    """A PR body still holding the raw CODE_AUTHORS token is refused even with an explicit message."""
    template = (
        PR_TEMPLATE.read_text(encoding="utf-8")
        if PR_TEMPLATE.is_file()
        else "intro\n\n<!-- CODE_AUTHORS: fill me -->\n"
    )
    with pytest.raises(RefusalError):
        resolve_squash_message(template, explicit="feat(scope): real", supplied=True)


def test_clean_squash_body_preserves_evidence_section() -> None:
    """## Evidence is authored corpus content, not review-only; it must survive untouched."""
    raw_body = """## Summary
Feature works.

## Evidence
uv run pytest tests/x -q → 5 passed
manual check: button renders

## Verification Evidence
<details><summary>log</summary>
trace
</details>

Closes #12
"""
    cleaned = clean_squash_body(raw_body)
    assert (
        "## Evidence\nuv run pytest tests/x -q → 5 passed\nmanual check: button renders" in cleaned
    )
    assert "## Verification Evidence" not in cleaned
    assert "trace" not in cleaned
    assert "Closes #12" in cleaned


def test_clean_squash_body_strips_mermaid_fence_under_authored_heading() -> None:
    """Balanced mermaid strip must bite under an authored heading (mutation: MERMAID_FENCE_RE.sub)."""
    raw_body = """## Summary
Feature works.
```mermaid
graph TD
    A --> B
```
- authored tail

## What Changed
- real change
"""
    cleaned = clean_squash_body(raw_body)
    assert "Feature works." in cleaned
    assert "A --> B" not in cleaned
    assert "```mermaid" not in cleaned
    assert "- authored tail" in cleaned
    assert "## What Changed\n- real change" in cleaned


def test_clean_squash_body_strips_unclosed_mermaid_under_authored_heading() -> None:
    """Unclosed mermaid strip must bite under an authored heading (mutation: _strip_unclosed mermaid line)."""
    raw_body = """## Summary
Feature works.
```mermaid
graph TD
    A --> B

## What Changed
- real change
"""
    cleaned = clean_squash_body(raw_body)
    assert "Feature works." in cleaned
    assert "A --> B" not in cleaned
    assert "```mermaid" not in cleaned
    assert "## What Changed\n- real change" in cleaned


def test_clean_squash_body_strips_details_block_under_authored_heading() -> None:
    """Balanced <details> strip must bite under an authored heading (mutation: DETAILS_BLOCK_RE.sub)."""
    raw_body = """## Summary
Feature works.
<details><summary>log</summary>
trace line
</details>
- authored tail

## What Changed
- real change
"""
    cleaned = clean_squash_body(raw_body)
    assert "Feature works." in cleaned
    assert "trace line" not in cleaned
    assert "<details" not in cleaned
    assert "- authored tail" in cleaned
    assert "## What Changed\n- real change" in cleaned


def test_clean_squash_body_strips_bullet_prefixed_details_block() -> None:
    """A list-marker-prefixed <details> block is stripped, later bullets survive."""
    raw_body = """## Summary
Feature works.
- <details><summary>log</summary>
  trace
  </details>
- real point
"""
    cleaned = clean_squash_body(raw_body)
    assert "trace" not in cleaned
    assert "<details" not in cleaned
    assert "- real point" in cleaned
    assert "Feature works." in cleaned


def test_clean_squash_body_preserves_prose_mentions_of_details() -> None:
    """Mentions of <details> mid-line are prose; nothing may be deleted (P2 counterexamples)."""
    mention_unclosed = (
        "## Summary\nStrips `<details>` ephemera from squash bodies.\n\n"
        "- bullet under summary\n\n## What Changed\n- real change\n\nCloses #12\n"
    )
    cleaned = clean_squash_body(mention_unclosed)
    assert "Strips `<details>` ephemera from squash bodies." in cleaned
    assert "- bullet under summary" in cleaned
    assert "## What Changed\n- real change" in cleaned
    assert "Closes #12" in cleaned

    mention_balanced = (
        "## Summary\nWe render a <details> collapsible for logs.\n\n"
        "Closes #12\n\n## Evidence\nmanual check; the closer is </details>.\n"
    )
    cleaned = clean_squash_body(mention_balanced)
    assert "We render a <details> collapsible for logs." in cleaned
    assert "Closes #12" in cleaned
    assert "## Evidence\nmanual check; the closer is </details>." in cleaned


def test_clean_squash_body_preserves_midline_details_closer() -> None:
    """A </details> quoted in later prose must not start or extend a cross-section deletion."""
    raw_body = """## Summary
Feature works.
<details><summary>log</summary>
trace line
</details>

## What Changed
- real change
- note: legacy prose mentioned <details> tags

## Decisions
- use </details> only inside blocks
"""
    cleaned = clean_squash_body(raw_body)
    assert "trace line" not in cleaned
    assert "<details><summary>" not in cleaned
    assert "## What Changed\n- real change" in cleaned
    assert "- note: legacy prose mentioned <details> tags" in cleaned
    assert "## Decisions\n- use </details> only inside blocks" in cleaned


def test_clean_squash_body_is_idempotent() -> None:
    """Double-sanitizing (build_squash_message cleans again) must be a fixed point."""
    raw_body = """## Summary
Feature works.

## What Changed
- item 1

## Verification Evidence
<details><summary>log</summary>
trace
</details>

## Architecture
```mermaid
graph TD
    A --> B
```

Co-authored-by: X <x@y>
Closes #12
"""
    once = clean_squash_body(raw_body)
    twice = clean_squash_body(once)
    assert twice == once
    assert "Feature works." in once
    assert "## What Changed\n- item 1" in once
    assert "Co-authored-by: X <x@y>" in once
    assert "Closes #12" in once


def test_pr_sh_forwards_squash_message(tmp_path: Path) -> None:
    """pr.sh must forward --squash-message to parse_args with flag-dependent observable."""
    mock_bin = tmp_path / "bin"
    mock_bin.mkdir()
    gh_mock = mock_bin / "gh"
    _ = gh_mock.write_text(
        "#!/usr/bin/env bash\n"
        'if [[ "$*" =~ pulls\\?head= ]]; then echo "null"; exit 0; fi\n'
        "exit 0\n",
        encoding="utf-8",
    )
    gh_mock.chmod(0o755)
    _ = subprocess.run(["git", "init", "-q"], cwd=tmp_path, capture_output=True, check=True)
    _ = subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/test/repo.git"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    env = {**os.environ, "PATH": f"{mock_bin}:{os.environ.get('PATH', '')}"}

    with_flag = subprocess.run(
        [
            "bash",
            str(PR_SH),
            "--check",
            "--head",
            "feat-x",
            "--body",
            "",
            "--squash-message",
            "",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
        timeout=120,
    )
    assert with_flag.returncode == 2, with_flag.stderr
    assert "--squash-message is empty" in with_flag.stderr

    without_flag = subprocess.run(
        ["bash", str(PR_SH), "--check", "--head", "feat-x", "--body", ""],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
        timeout=120,
    )
    assert without_flag.returncode == 1, without_flag.stderr
    assert "remediation:" in without_flag.stderr
    assert "--squash-message" in without_flag.stderr


def test_check_trailers_enforces_title_budget_on_existing_pr(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--check must refuse an over-budget title on an existing PR, same as the merge gate."""

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        joined = " ".join(cmd)
        out = "7" if "pulls?head=" in joined else ""
        return subprocess.CompletedProcess(cmd, 0, out + "\n", "")

    monkeypatch.setattr(pr_mod, "run_command", fake_run)

    long_title = "feat: " + "a" * 110
    rc = check_trailers(
        "test/repo", "feat-branch", "## Summary\nok\n", body_supplied=True, title=long_title
    )
    assert rc == 1
    assert "commit title exceeds 100 chars" in capsys.readouterr().err

    short_rc = check_trailers(
        "test/repo", "feat-branch", "## Summary\nok\n", body_supplied=True, title="feat: short"
    )
    assert short_rc == 0


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
num, title, body, created = create_or_reuse_pr(
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
num, title, body, created = create_or_reuse_pr(
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
    assert (
        "conflict detected: run 'uv run skills/gh-router/subskills/pr-conflict/scripts/extract_conflict_context.py' to inspect hunks and commit intent, then delegate resolution to a worker subagent."
        in res.stderr
    )

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
    elif [[ "$arg" == "--log" || "$arg" == "--log-failed" ]]; then
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


def test_parse_args_tracks_no_stamp() -> None:
    """parse_args must support --no-stamp (True) and --stamp (False), defaulting to False."""
    assert not parse_args([]).no_stamp
    assert parse_args(["--no-stamp"]).no_stamp
    assert not parse_args(["--no-stamp", "--stamp"]).no_stamp


def test_stamp_changelog_attributes_entries_and_commits(tmp_path: Path) -> None:
    """stamp_changelog must attribute unreleased entries with PR number, preserve BREAKING CHANGE, and push commit."""
    remote_path = tmp_path / "remote.git"
    _ = subprocess.run(["git", "init", "--bare", str(remote_path)], check=True, capture_output=True)

    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    _ = subprocess.run(
        ["git", "init", "-b", "main", str(repo_path)], check=True, capture_output=True
    )
    _ = subprocess.run(
        ["git", "-C", str(repo_path), "remote", "add", "origin", str(remote_path)],
        check=True,
        capture_output=True,
    )
    _ = subprocess.run(["git", "-C", str(repo_path), "config", "user.name", "Tester"], check=True)
    _ = subprocess.run(
        ["git", "-C", str(repo_path), "config", "user.email", "tester@example.com"], check=True
    )

    readme = repo_path / "README.md"
    _ = readme.write_text("# Repo\n", encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(repo_path), "add", "README.md"], check=True)
    _ = subprocess.run(["git", "-C", str(repo_path), "commit", "-m", "chore: initial"], check=True)
    _ = subprocess.run(["git", "-C", str(repo_path), "push", "-u", "origin", "main"], check=True)

    _ = subprocess.run(
        ["git", "-C", str(repo_path), "checkout", "-b", "feat/my-feature"], check=True
    )

    config_dir = repo_path / ".config"
    config_dir.mkdir(parents=True)
    baseline_file = config_dir / "changelog-unattributed-baseline.txt"
    _ = baseline_file.write_text("# baseline\nlegacy baseline entry\n", encoding="utf-8")

    changelog_content = """# Changelog

## [Unreleased]

### Features
* **pr-land:** test auto-stamp
* **scope:** breaking change (BREAKING CHANGE)
* legacy baseline entry
* already attributed (#99)

## [1.0.0] - 2026-01-01
* initial entry (#1)
"""
    changelog_file = repo_path / "CHANGELOG.md"
    _ = changelog_file.write_text(changelog_content, encoding="utf-8")
    _ = subprocess.run(["git", "-C", str(repo_path), "add", "CHANGELOG.md", ".config"], check=True)
    _ = subprocess.run(
        ["git", "-C", str(repo_path), "commit", "-m", "feat: add feature"], check=True
    )
    _ = subprocess.run(
        ["git", "-C", str(repo_path), "push", "-u", "origin", "feat/my-feature"], check=True
    )

    stamped = stamp_changelog("feat/my-feature", "145", cwd=repo_path)
    assert stamped is True

    updated_text = changelog_file.read_text(encoding="utf-8")
    assert "* **pr-land:** test auto-stamp (#145)" in updated_text
    assert "* **scope:** breaking change (#145) (BREAKING CHANGE)" in updated_text
    assert "* legacy baseline entry" in updated_text
    assert "legacy baseline entry (#145)" not in updated_text
    assert "* already attributed (#99)" in updated_text
    assert "already attributed (#99) (#145)" not in updated_text

    log_res = subprocess.run(
        ["git", "-C", str(repo_path), "log", "-1", "--pretty=%s"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert log_res.stdout.strip() == "chore(changelog): attribute #145 in unreleased ledger"

    # Idempotent
    stamped_again = stamp_changelog("feat/my-feature", "145", cwd=repo_path)
    assert stamped_again is False


def test_dump_failure_logs_targets_check_link_and_log_failed(tmp_path: Path) -> None:
    """dump_failure_logs must resolve failed run ID from check links and invoke gh run view --log-failed."""
    mock_bin = tmp_path / "bin"
    mock_bin.mkdir(exist_ok=True)
    gh_mock = mock_bin / "gh"
    log_file = tmp_path / "calls.log"

    gh_script = f"""#!/usr/bin/env bash
echo "$@" >> "{log_file}"
if [[ "$*" =~ name,bucket,link,state ]]; then
    cat <<'EOF'
[
  {{"name": "build", "bucket": "pass", "link": "https://github.com/test/repo/actions/runs/1111/job/1", "state": "SUCCESS"}},
  {{"name": "test", "bucket": "fail", "link": "https://github.com/test/repo/actions/runs/77777/job/2", "state": "FAILURE"}}
]
EOF
    exit 0
elif [[ "$*" =~ view\\ 77777.*--log-failed ]]; then
    echo "FAIL: test_something() failed assert 1 == 2"
    exit 0
elif [[ "$*" =~ pr\\ checks\\ 123 ]]; then
    echo "test   fail   1m"
    exit 0
fi
exit 0
"""
    _ = gh_mock.write_text(gh_script, encoding="utf-8")
    gh_mock.chmod(0o755)

    env = {
        **os.environ,
        "PATH": f"{mock_bin}:{os.environ.get('PATH', '')}",
    }

    test_script = f"""
import sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import dump_failure_logs
dump_failure_logs("test/repo", "123")
"""
    res = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res.returncode == 0
    assert "FAIL: test_something() failed assert 1 == 2" in res.stderr
    assert "test   fail   1m" in res.stderr

    calls = log_file.read_text(encoding="utf-8")
    assert "run view 77777 --repo test/repo --log-failed" in calls


def test_check_trailers_local_preflight_no_remote_pr(tmp_path: Path) -> None:
    """check_trailers without open PR: exit 2 when no body supplied; exit 0 on valid body; exit 1 on bad title or raw token."""
    mock_bin = tmp_path / "bin"
    mock_bin.mkdir(exist_ok=True)
    gh_mock = mock_bin / "gh"

    gh_script = """#!/usr/bin/env bash
if [[ "$*" =~ pulls\\?head= ]]; then
    echo "null"
    exit 0
elif [[ "$*" =~ api\\ user ]]; then
    echo "merger-user"
    exit 0
fi
exit 0
"""
    _ = gh_mock.write_text(gh_script, encoding="utf-8")
    gh_mock.chmod(0o755)

    env = {
        **os.environ,
        "PATH": f"{mock_bin}:{os.environ.get('PATH', '')}",
    }

    # Case 1: no open PR and no body_supplied -> returns 2
    test_no_body = f"""
import sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import check_trailers
rc = check_trailers("test/repo", "feat-branch", "", body_supplied=False)
sys.exit(rc)
"""
    res1 = subprocess.run(
        [sys.executable, "-c", test_no_body],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res1.returncode == 2
    assert "no open PR for head feat-branch" in res1.stderr

    # Case 2: body_supplied=True, valid body & title -> returns 0
    test_valid = f"""
import sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import check_trailers
rc = check_trailers("test/repo", "feat-branch", "feat: short description", body_supplied=True, title="feat: short title")
sys.exit(rc)
"""
    res2 = subprocess.run(
        [sys.executable, "-c", test_valid],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res2.returncode == 0

    # Case 3: body_supplied=True, body has raw CODE_AUTHORS token -> returns 1
    test_raw_token = f"""
import sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import check_trailers
rc = check_trailers("test/repo", "feat-branch", "feat: body <!-- CODE_AUTHORS -->", body_supplied=True)
sys.exit(rc)
"""
    res3 = subprocess.run(
        [sys.executable, "-c", test_raw_token],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res3.returncode == 1
    assert "raw CODE_AUTHORS token still present" in res3.stderr

    # Case 4: body_supplied=True, title exceeds 100 chars -> returns 1
    long_title = "feat: " + "a" * 95
    test_long_title = f"""
import sys
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import check_trailers
rc = check_trailers("test/repo", "feat-branch", "feat: body", body_supplied=True, title="{long_title}")
sys.exit(rc)
"""
    res4 = subprocess.run(
        [sys.executable, "-c", test_long_title],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )
    assert res4.returncode == 1
    assert "commit title exceeds 100 chars" in res4.stderr


def test_clean_squash_body_strips_checklist_landing_and_comments() -> None:
    """clean_squash_body must strip HTML comments, ## Landing, ## Checklist, and empty sections while keeping closes."""
    raw_body = """<!-- markdownlint-disable MD041 -->

## Summary
Add important feature.

<!-- 2-3 sentences -->
**Impact**: 2 files · **Risk**: Low

## What Changed
- item 1
- item 2

## Architecture
<!-- Mermaid diagram here -->

## Landing
Landing: squash
Ledger-Waiver: test-waiver

## Checklist
- [x] Formatter green
- [ ] Tests passed

Closes #123
"""
    cleaned = clean_squash_body(raw_body)
    assert "<!--" not in cleaned
    assert "## Checklist" not in cleaned
    assert "Formatter green" not in cleaned
    assert "## Landing" not in cleaned
    assert "Landing: squash" not in cleaned
    assert "Ledger-Waiver" not in cleaned
    assert "## Architecture" not in cleaned
    assert "## Summary\nAdd important feature.\n\n**Impact**: 2 files · **Risk**: Low" in cleaned
    assert "## What Changed\n- item 1\n- item 2" in cleaned
    assert "Closes #123" in cleaned


def test_clean_squash_body_strips_mermaid_and_details_leaks() -> None:
    """Review-only mermaid and <details> leaks must not survive into squash history."""
    raw_body = """## Summary
Add important feature.

**Impact**: 2 files · **Risk**: Low

## Architecture
```mermaid
graph TD
    A --> B
```

## Verification Evidence
<details><summary>Output</summary>

trace: pytest exit 0

</details>

## Blast Radius & Safety
- touches only squash logic

## What Changed
- item 1
- item 2

Co-authored-by: X <x@y>
Closes #12
"""
    cleaned = clean_squash_body(raw_body)
    assert "## Summary\nAdd important feature." in cleaned
    assert "**Impact**: 2 files · **Risk**: Low" in cleaned
    assert "## Blast Radius & Safety" in cleaned
    assert "## What Changed\n- item 1\n- item 2" in cleaned
    assert "Co-authored-by: X <x@y>" in cleaned
    assert "Closes #12" in cleaned
    assert "A --> B" not in cleaned
    assert "trace" not in cleaned
    assert "## Architecture" not in cleaned
    assert "## Verification Evidence" not in cleaned
    assert "<details" not in cleaned


def test_clean_squash_body_strips_unclosed_details() -> None:
    """An unclosed <details> block strips to end of text."""
    raw_body = "## Summary\nFine.\n\n## Notes\n<details><summary>Output</summary>\ntrace tail\n"
    cleaned = clean_squash_body(raw_body)
    assert "## Summary\nFine." in cleaned
    assert "<details" not in cleaned
    assert "trace tail" not in cleaned


def test_clean_squash_body_unclosed_mermaid_keeps_following_sections() -> None:
    """An unclosed mermaid fence must not delete later authored sections or Closes."""
    raw_body = """## Summary
Real motivation.

## Architecture
```mermaid
graph TD
    A --> B

## What Changed
- real change

Closes #12
"""
    cleaned = clean_squash_body(raw_body)
    assert "Real motivation." in cleaned
    assert "## Architecture" not in cleaned
    assert "A --> B" not in cleaned
    assert "## What Changed" in cleaned
    assert "- real change" in cleaned
    assert "Closes #12" in cleaned


def test_clean_squash_body_unclosed_details_keeps_following_sections() -> None:
    """An unclosed <details> block must not delete later authored sections or Closes."""
    raw_body = """## Summary
Real motivation.

## Verification Evidence
<details><summary>Output</summary>
trace line 1

## What Changed
- real change

Closes #12
"""
    cleaned = clean_squash_body(raw_body)
    assert "Real motivation." in cleaned
    assert "## Verification Evidence" not in cleaned
    assert "trace line 1" not in cleaned
    assert "<details" not in cleaned
    assert "## What Changed" in cleaned
    assert "- real change" in cleaned
    assert "Closes #12" in cleaned


def test_clean_squash_body_unclosed_mermaid_keeps_trailing_closes_and_trailer() -> None:
    """An unclosed mermaid fence with no following heading must keep trailing Closes/trailer."""
    raw_body = """## Summary
S.

## Architecture
```mermaid
graph LR
  A --> B
Closes #12
Co-authored-by: Real <r@e.com>
"""
    cleaned = clean_squash_body(raw_body)
    assert "## Summary\nS." in cleaned
    assert "A --> B" not in cleaned
    assert "graph LR" not in cleaned
    assert "Closes #12" in cleaned
    assert "Co-authored-by: Real <r@e.com>" in cleaned


def test_clean_squash_body_unclosed_details_keeps_trailing_closes() -> None:
    """An unclosed <details> as final section must keep a trailing Closes line."""
    raw_body = """## Summary
S.

## Verification Evidence
<details><summary>Output</summary>
trace line 1
Closes #7
"""
    cleaned = clean_squash_body(raw_body)
    assert "## Summary\nS." in cleaned
    assert "trace line 1" not in cleaned
    assert "<details" not in cleaned
    assert "Closes #7" in cleaned


def test_clean_squash_body_refuses_raw_token() -> None:
    """clean_squash_body must refuse when raw CODE_AUTHORS token is present."""
    with pytest.raises(PrError):
        clean_squash_body("## Summary\nText\n<!-- CODE_AUTHORS -->\n")


def test_squash_message_returns_empty_when_body_has_only_procedural_sections() -> None:
    """When a PR body contains only procedural checklists, comments, or directives, squash_message returns empty."""
    procedural_only = """<!-- markdownlint-disable MD041 -->
## Landing
Landing: squash

## Checklist
- [x] Tests green
"""
    assert squash_message(procedural_only) == ""


def test_is_unfilled_body_detects_empty_and_template() -> None:
    """is_unfilled_body is true only for an empty body or the repo template verbatim."""
    template = (
        PR_TEMPLATE.read_text(encoding="utf-8")
        if PR_TEMPLATE.is_file()
        else "## Summary\n<!-- note -->\n"
    )
    assert is_unfilled_body("")
    assert is_unfilled_body(template, template_path=PR_TEMPLATE)
    assert not is_unfilled_body("## Summary\nAuthored description.", template_path=PR_TEMPLATE)


def test_create_or_reuse_refuses_missing_or_template_body(tmp_path: Path) -> None:
    """create_or_reuse_pr refuses to open a PR with no body or with the unfilled repo template."""
    mock_bin = tmp_path / "bin"
    mock_bin.mkdir()
    gh_mock = mock_bin / "gh"
    _ = gh_mock.write_text(
        '#!/usr/bin/env bash\nif [[ "$*" =~ pulls\\\\?head= ]]; then echo "null"; exit 0; fi\nexit 0\n',
        encoding="utf-8",
    )
    gh_mock.chmod(0o755)
    env = {**os.environ, "PATH": f"{mock_bin}:{os.environ.get('PATH', '')}"}

    def refuse(body_expr: str, body_supplied: bool) -> subprocess.CompletedProcess[str]:
        script = f"""
import sys
from pathlib import Path
sys.path.insert(0, "{PR_SCRIPTS}")
from pr import PrError, create_or_reuse_pr
body = {body_expr}
try:
    create_or_reuse_pr(
        repo="test/repo",
        head_ref="feat-branch",
        base="main",
        title="feat: x",
        body=body,
        title_supplied=True,
        body_supplied={body_supplied!r},
    )
except PrError as e:
    print(f"REFUSED: {{e}}", file=sys.stderr)
    sys.exit(1)
sys.exit(0)
"""
        return subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, env=env, cwd=REPO_ROOT
        )

    missing = refuse('""', False)
    assert missing.returncode == 1, missing.stderr
    assert "no PR body supplied" in missing.stderr

    template_literal = f'Path({str(PR_TEMPLATE)!r}).read_text(encoding="utf-8")'
    unfilled = refuse(template_literal, True)
    assert unfilled.returncode == 1, unfilled.stderr
    assert "unfilled repo template" in unfilled.stderr


class _FakeRun:
    """Stub pr_mod.run_command: records argv and returns canned gh/git outputs.

    existing_pr selects the reuse path ("7") or the fresh-create path ("null").
    ready_rc controls the gh pr ready outcome. reuse_draft adds isDraft=true to the
    reuse payload (the same pulls?head= response the reuse path already fetches).
    """

    def __init__(
        self, *, existing_pr: str = "null", ready_rc: int = 0, reuse_draft: bool = False
    ) -> None:
        self.calls: list[list[str]] = []
        self.existing_pr = existing_pr
        self.ready_rc = ready_rc
        self.reuse_draft = reuse_draft

    def __call__(self, cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(cmd))
        joined = " ".join(cmd)
        out, err, rc = "", "", 0
        if "rev-parse --abbrev-ref" in joined:
            out = "feat-x\n"
        elif "config --get branch." in joined:
            rc = 1
        elif "remote get-url" in joined:
            out = "https://github.com/test/repo.git\n"
        elif "default_branch" in joined:
            out = "main\n"
        elif "pulls?head=" in joined:
            if self.existing_pr == "null":
                out = "null\n"
            else:
                draft_flag = "true" if self.reuse_draft else "false"
                out = f"{self.existing_pr}\t{draft_flag}\n"
        elif "pulls -X POST" in joined:
            out = "7\n"
        elif "html_url" in joined:
            out = "https://github.com/test/repo/pull/7\n"
        elif "pr ready" in joined:
            rc = self.ready_rc
            err = "GraphQL: Something went wrong\n" if rc != 0 else ""
        return subprocess.CompletedProcess(cmd, rc, out, err)


def _write_changelog(
    tmp_path: Path, entry: str | None = "* **pr-land:** handshake entry\n"
) -> Path:
    body = (
        f"# Changelog\n\n## [Unreleased]\n\n### Features\n{entry}"
        if entry
        else "# Changelog\n\n## [Unreleased]\n\n### Features\n"
    )
    changelog = tmp_path / "CHANGELOG.md"
    _ = changelog.write_text(body, encoding="utf-8")
    return changelog


def _main_args(*extra: str) -> list[str]:
    return ["--head", "feat-x", "--title", "feat: x", "--body", "## Summary\nReal.\n", *extra]


def test_draft_handshake_create_stamp_then_ready(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Fresh create is draft=true, then changelog commit+push, then gh pr ready last (mutation: create arg draft=true -> draft=false)."""
    _ = _write_changelog(tmp_path)
    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args())
    assert rc == 0, fake.calls

    creates = [c for c in fake.calls if "pulls -X POST" in " ".join(c)]
    assert len(creates) == 1
    assert "draft=true" in creates[0]

    assert any(c[:3] == ["git", "add", "CHANGELOG.md"] for c in fake.calls)
    commits = [c for c in fake.calls if c[:2] == ["git", "commit"]]
    assert len(commits) == 1
    assert "chore(changelog): attribute #7 in unreleased ledger" in commits[0][-1]
    assert ["git", "push", "origin", "feat-x"] in fake.calls

    ready_calls = [c for c in fake.calls if "pr ready" in " ".join(c)]
    assert len(ready_calls) == 1
    assert fake.calls[-1] == ["gh", "pr", "ready", "7", "--repo", "test/repo"]

    err = capsys.readouterr().err
    assert "carries" not in err
    assert "no ## [Unreleased]" not in err


def test_draft_flag_skips_ready_flip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """--draft leaves the PR draft: created with draft=true but gh pr ready is ABSENT (mutation: drop options.draft guard in main -> ready appears)."""
    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args("--draft"))
    assert rc == 0, fake.calls

    creates = [c for c in fake.calls if "pulls -X POST" in " ".join(c)]
    assert len(creates) == 1
    assert "draft=true" in creates[0]
    assert not [c for c in fake.calls if "pr ready" in " ".join(c)]


def test_reuse_existing_pr_never_touches_draft_state(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An existing open PR is reused untouched: no gh pr ready, no re-draft, no create (mutation: reuse branch returns created=True -> ready flip appears)."""
    fake = _FakeRun(existing_pr="7")
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args())
    assert rc == 0, fake.calls

    assert not [c for c in fake.calls if "pr ready" in " ".join(c)]
    assert not [c for c in fake.calls if "pulls -X POST" in " ".join(c)]
    all_joined = " ".join(" ".join(c) for c in fake.calls)
    assert "draft=" not in all_joined


def test_ready_failure_exits_1_with_manual_fix(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Non-zero gh pr ready makes the program exit 1 naming the verbatim manual fix (mutation: ready_pr failure path return False -> return True)."""
    fake = _FakeRun(ready_rc=1)
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args())
    assert rc == 1

    err = capsys.readouterr().err
    assert "gh pr ready 7 --repo test/repo" in err
    assert "still a draft" in err


def test_no_stamp_skips_stamping_but_still_readies(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--no-stamp runs no stamp commands but the flip to ready still happens with a warning (mutation: gate the ready flip on not no_stamp -> ready absent)."""
    _ = _write_changelog(tmp_path)
    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args("--no-stamp"))
    assert rc == 0, fake.calls

    assert not [c for c in fake.calls if "CHANGELOG.md" in " ".join(c)]
    assert fake.calls[-1] == ["gh", "pr", "ready", "7", "--repo", "test/repo"]
    err = capsys.readouterr().err
    assert "not stamped" in err
    assert "changelog gate" in err


def test_reuse_draft_pr_without_draft_flag_fails_loud(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Reused draft PR without --draft exits 1 with the verbatim manual remediation and NEVER calls gh pr ready (mutation: auto-flip via ready_pr on reuse -> the no-mutation argv assert fails)."""
    fake = _FakeRun(existing_pr="7", reuse_draft=True)
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args())
    assert rc == 1, fake.calls

    err = capsys.readouterr().err
    assert (
        "remediation: PR #7 is still a draft; run manually: gh pr ready 7 --repo test/repo" in err
    )
    assert not [c for c in fake.calls if c[:3] == ["gh", "pr", "ready"]]


def test_reuse_draft_pr_with_draft_flag_proceeds(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A reused draft PR with --draft is the caller's stated intent: rc 0, no remediation, no flip (mutation: ignore options.draft on the reuse check -> rc flips to 1)."""
    fake = _FakeRun(existing_pr="7", reuse_draft=True)
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args("--draft"))
    assert rc == 0, fake.calls

    err = capsys.readouterr().err
    assert "remediation" not in err
    assert not [c for c in fake.calls if c[:3] == ["gh", "pr", "ready"]]


def test_checks_verdict_all_skipping_is_pending() -> None:
    """An all-skipping rollup (draft PRs get zero CI runs) must never read as success (mutation: restore bucket in ("pass", "skipping") unconditional -> returns success)."""
    assert checks_verdict("lint\tskipping\ntest\tskipping\n") == "pending"


def test_checks_verdict_mixed_pass_and_skipping_is_success() -> None:
    """Partially-skipped PRs stay success; skipping alone must not become a --watch timeout (mutation: treat any skipping as pending -> returns pending)."""
    assert checks_verdict("build\tpass\nlint\tskipping\n") == "success"


def test_ready_flip_warns_when_unreleased_carries_no_entry_for_pr(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Unattributed Unreleased warns with the gate text yet still flips ready with rc 0 (mutation: drop the warning branch -> gate text vanishes; gate the flip on attribution -> ready absent)."""
    _ = _write_changelog(tmp_path)
    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)

    def _no_stamp(*args: object, **kwargs: object) -> bool:
        return False

    monkeypatch.setattr(pr_mod, "stamp_changelog", _no_stamp)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args())
    assert rc == 0, fake.calls

    err = capsys.readouterr().err
    assert "warning: no ## [Unreleased] entry carries (#7)" in err
    assert "carries no entries in ## [Unreleased]" in err
    assert fake.calls[-1] == ["gh", "pr", "ready", "7", "--repo", "test/repo"]


def test_ready_flip_stays_silent_when_entry_carries_pr_number(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An entry ending in (#7) silences the advisory while the flip still happens (mutation: scan every line instead of bullets -> heading text could false-positive; match mid-entry (#7) -> silence without a real entry)."""
    _ = _write_changelog(tmp_path, entry="* **pr-land:** handshake entry (#7)\n")
    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args())
    assert rc == 0, fake.calls

    err = capsys.readouterr().err
    assert "warning:" not in err
    assert "carries" not in err
    assert fake.calls[-1] == ["gh", "pr", "ready", "7", "--repo", "test/repo"]


def test_draft_flag_prints_milder_note_when_unattributed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--draft downgrades the advisory to note: with no ready call and rc 0 (mutation: reuse the warning: branch under --draft -> stderr gains warning:; call ready_pr under --draft -> ready appears)."""
    _ = _write_changelog(tmp_path)
    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)

    def _no_stamp_draft(*args: object, **kwargs: object) -> bool:
        return False

    monkeypatch.setattr(pr_mod, "stamp_changelog", _no_stamp_draft)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args("--draft"))
    assert rc == 0, fake.calls

    err = capsys.readouterr().err
    assert "note: no ## [Unreleased] entry carries (#7)" in err
    assert "warning:" not in err
    assert not [c for c in fake.calls if "pr ready" in " ".join(c)]


def test_no_stamp_stays_silent_when_entry_carries_pr_number(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--no-stamp with an attributed entry prints nothing about the changelog (mutation: warn unconditionally under --no-stamp -> not stamped appears)."""
    _ = _write_changelog(tmp_path, entry="* **pr-land:** handshake entry (#7)\n")
    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args("--no-stamp"))
    assert rc == 0, fake.calls

    err = capsys.readouterr().err
    assert "not stamped" not in err
    assert "carries" not in err
    assert fake.calls[-1] == ["gh", "pr", "ready", "7", "--repo", "test/repo"]


def test_no_stamp_warns_when_unreleased_carries_no_entry_for_pr(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """--no-stamp without attribution warns once naming the missing stamp and the gate (mutation: keep the old static warning -> gate text missing; skip the scan -> warning fires even when attributed)."""
    _ = _write_changelog(tmp_path)
    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args("--no-stamp"))
    assert rc == 0, fake.calls

    err = capsys.readouterr().err
    assert "not stamped" in err
    assert "changelog gate" in err
    assert "carries no entries in ## [Unreleased]" in err
    assert fake.calls[-1] == ["gh", "pr", "ready", "7", "--repo", "test/repo"]


def test_unreleased_attributes_pr_matches_gate_attribution_rules(tmp_path: Path) -> None:
    """unreleased_attributes_pr mirrors the gate end-of-entry rule: (#N) and (#N) (BREAKING CHANGE) count, anything else does not (mutation: accept mid-entry (#N) -> outside-block case flips true; drop the BREAKING CHANGE tail -> breaking case flips false)."""

    def scan(content: str | None, pr_num: str = "7") -> bool:
        target = tmp_path / "CHANGELOG.md"
        if content is None:
            if target.exists():
                target.unlink()
        else:
            _ = target.write_text(content, encoding="utf-8")
        return unreleased_attributes_pr(pr_num, cwd=tmp_path)

    assert (
        scan(
            "# Changelog\n\n## [Unreleased]\n\n### Features\n* **pr-land:** handshake entry (#7)\n"
        )
        is True
    )
    assert (
        scan(
            "# Changelog\n\n## [Unreleased]\n\n### Features\n* **scope:** breaking change (#7) (BREAKING CHANGE)\n"
        )
        is True
    )
    assert (
        scan(
            "# Changelog\n\n## [Unreleased]\n\n### Features\n* **pr-land:** handshake entry (#3)\n"
        )
        is False
    )
    assert scan("# Changelog\n\n### Features\n* **pr-land:** handshake entry (#7)\n") is False
    assert scan(None) is False
    assert (
        scan(
            "# Changelog\n\n## [Unreleased]\n\n### Features\n* **pr-land:** handshake entry\n\n## [1.0.0] - 2026-01-01\n* initial entry (#7)\n"
        )
        is False
    )


def test_unreleased_attributes_pr_non_utf8_reads_unattributed(tmp_path: Path) -> None:
    """Non-UTF-8 CHANGELOG bytes read as unattributed False, never a crash (mutation: narrow the guard to OSError -> UnicodeDecodeError escapes)."""
    target = tmp_path / "CHANGELOG.md"
    _ = target.write_bytes(b"# \xff\xfe\n")
    assert unreleased_attributes_pr("7", cwd=tmp_path) is False


def test_non_utf8_changelog_no_stamp_still_readies(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Non-UTF-8 CHANGELOG under --no-stamp still flips ready with rc 0 and no traceback (mutation: let the decode error propagate -> traceback, ready absent)."""
    _ = (tmp_path / "CHANGELOG.md").write_bytes(b"# \xff\xfe\n")
    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args("--no-stamp"))
    assert rc == 0, fake.calls
    assert fake.calls[-1] == ["gh", "pr", "ready", "7", "--repo", "test/repo"]
    err = capsys.readouterr().err
    assert "Traceback" not in err


def test_loose_bullet_without_section_is_unattributed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A (#7) bullet with no ### section above it does not attribute, yet still warns and readies (mutation: drop the section gate -> scan flips true, gate text vanishes)."""
    _ = (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n* loose entry (#7)\n", encoding="utf-8"
    )
    assert unreleased_attributes_pr("7", cwd=tmp_path) is False

    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)

    def _no_stamp(*args: object, **kwargs: object) -> bool:
        return False

    monkeypatch.setattr(pr_mod, "stamp_changelog", _no_stamp)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args())
    assert rc == 0, fake.calls
    err = capsys.readouterr().err
    assert "carries no entries in ## [Unreleased]" in err
    assert fake.calls[-1] == ["gh", "pr", "ready", "7", "--repo", "test/repo"]


def test_sectioned_bullet_attributes_pr(tmp_path: Path) -> None:
    """A (#7) bullet under a ### section attributes True (mutation: require a blank line after the heading -> flips false)."""
    _ = (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n### Features\n* **pr-land:** entry (#7)\n",
        encoding="utf-8",
    )
    assert unreleased_attributes_pr("7", cwd=tmp_path) is True


def test_no_stamp_draft_prints_milder_note(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--no-stamp --draft downgrades to note: keeping the --no-stamp framing and no ready flip (mutation: reuse the warning: branch -> harsh form appears; flip ready under --draft -> ready appears)."""
    _ = _write_changelog(tmp_path)
    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args("--no-stamp", "--draft"))
    assert rc == 0, fake.calls

    err = capsys.readouterr().err
    assert "note:" in err
    assert "not stamped" in err
    assert "changelog gate" in err
    assert "warning:" not in err
    assert not [c for c in fake.calls if "pr ready" in " ".join(c)]


def test_absent_unreleased_block_warns_naming_missing_section(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """No ## [Unreleased] block warns naming the missing section, never quoting the gate finding (mutation: reuse the block-exists text -> 'carries no entries' appears)."""
    _ = (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n### Features\n* **pr-land:** entry (#7)\n", encoding="utf-8"
    )
    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)

    def _no_stamp(*args: object, **kwargs: object) -> bool:
        return False

    monkeypatch.setattr(pr_mod, "stamp_changelog", _no_stamp)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args())
    assert rc == 0, fake.calls
    err = capsys.readouterr().err
    assert "no ## [Unreleased] section" in err
    assert "carries no entries" not in err
    assert fake.calls[-1] == ["gh", "pr", "ready", "7", "--repo", "test/repo"]


def test_baseline_entry_stamp_is_noop_and_advisory_silent(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A baseline-listed entry makes the real stamp a no-op while the (#7) entry keeps the advisory silent (mutation: ignore baseline in stamp -> a commit appears)."""
    _ = (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n### Features\n"
        "* legacy baseline entry\n"
        "* **pr-land:** handshake entry (#7)\n",
        encoding="utf-8",
    )
    config_dir = tmp_path / ".config"
    config_dir.mkdir()
    _ = (config_dir / "changelog-unattributed-baseline.txt").write_text(
        "# legacy baseline\nlegacy baseline entry\n", encoding="utf-8"
    )
    fake = _FakeRun()
    monkeypatch.setattr(pr_mod, "run_command", fake)
    monkeypatch.chdir(tmp_path)

    rc = pr_mod.main(_main_args())
    assert rc == 0, fake.calls

    assert not [c for c in fake.calls if c[:2] == ["git", "commit"]]
    err = capsys.readouterr().err
    assert "warning:" not in err
    assert "carries" not in err
    assert fake.calls[-1] == ["gh", "pr", "ready", "7", "--repo", "test/repo"]
