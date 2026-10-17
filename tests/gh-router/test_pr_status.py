"""`pr.py --status`: pinned-schema conformance, read-only proof, and refusal shapes.

`--status` derives the landing state from git and `gh` on every run, emits
facts on stdout, and always exits 0 — it pushes nothing, creates nothing, and
deletes nothing. A companion set pins the mutating-command contracts that share
the same refusal entries: the `--merge` title preflight (before any `gh`
mutation), the reused-draft refusal with its ready-flip transition, and the
post-creation stamp hard-fail with the PR url and remedy.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tests.git_env import git_env

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS_DIR = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"
PR_PY = PR_SCRIPTS_DIR / "pr.py"

if str(PR_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(PR_SCRIPTS_DIR))

GH_STUB = """#!/usr/bin/env bash
echo "$@" >> "$GH_LOG"
for arg in "$@"; do
  case "$arg" in
    *'pulls?head='*)
      if [[ -z "${PR_NUMBER:-}" ]]; then echo "null"; elif [[ " $* " == *".merged"* ]]; then printf '%s\\t%s\\t%s\\t%s\\n' "$PR_NUMBER" "${PR_STATE:-open}" "${PR_DRAFT:-false}" "${PR_MERGED:-false}"; elif [[ " $* " == *'.[0].number'* ]]; then printf '%s\\n' "$PR_NUMBER"; else printf '%s\\t%s\\n' "$PR_NUMBER" "${PR_DRAFT:-false}"; fi
      exit 0 ;;
  esac
done
if [[ " $* " == *" POST "* ]]; then printf '%s\\n' "${POST_NUMBER:-7}"; exit 0; fi
for arg in "$@"; do
  case "$arg" in
    *'/commits'*) printf '%s' "${COMMITS_TSV:-}"; exit 0 ;;
  esac
done
if [[ "$1" == "pr" && "$2" == "checks" ]]; then printf '%s' "${CHECKS_TSV:-}"; exit 0; fi
for arg in "$@"; do
  case "$arg" in
    *'body // ""'*) printf '%s' "${PR_BODY:-}"; exit 0 ;;
    *'html_url'*) printf '%s\\n' "${PR_URL:-https://github.com/test/repo/pull/7}"; exit 0 ;;
    *'nameWithOwner'*) printf 'test/repo\\n'; exit 0 ;;
  esac
done
if [[ "${1:-}" == "user" ]]; then printf 'me\\n'; exit 0; fi
for arg in "$@"; do
  case "$arg" in
    *'/pulls/'*) printf '%s\\n' "${MERGE_TSV:-true\\tclean\\thttps://github.com/test/repo/pull/7}"; exit 0 ;;
  esac
done
exit 0
"""


def _run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=git_env(), check=True)


def _git(repo: Path, *args: str) -> None:
    _ = _run(["git", "-C", str(repo), *args])


def _make_repo(repo: Path) -> Path:
    """Synthetic repo with a LOCAL bare origin: pushes succeed when attempted."""
    repo.mkdir(parents=True)
    bare = repo.parent / "origin.git"
    _ = _run(["git", "init", "--bare", str(bare)])
    _ = _run(["git", "init", "-b", "main", str(repo)])
    for key, value in (
        ("user.name", "Status Synthetic"),
        ("user.email", "status@x.io"),
        ("commit.gpgsign", "false"),
    ):
        _ = _run(["git", "-C", str(repo), "config", key, value])
    _ = (repo / "base.txt").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "base.txt")
    _git(repo, "commit", "-m", "chore: base")
    _git(repo, "remote", "add", "origin", str(bare))
    _git(repo, "push", "origin", "main")
    _git(repo, "update-ref", "refs/remotes/origin/main", "refs/heads/main")
    _git(repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    _git(repo, "checkout", "-b", "feat-status")
    _ = (repo / "one.txt").write_text("one\n", encoding="utf-8")
    _git(repo, "add", "one.txt")
    _git(repo, "commit", "-m", "feat: one")
    _ = (repo / "two.txt").write_text("two\n", encoding="utf-8")
    _git(repo, "add", "two.txt")
    _git(repo, "commit", "-m", "feat: two")
    return bare


def _gh_env(tmp_path: Path, **extra: str) -> dict[str, str]:
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    _ = gh.write_text(GH_STUB, encoding="utf-8")
    gh.chmod(0o755)
    env = git_env(
        PATH=f"{bindir}{os.pathsep}{os.environ['PATH']}",
        GH_LOG=str(tmp_path / "gh.log"),
        PR_URL="https://github.com/test/repo/pull/7",
    )
    env.update(extra)
    return env


def _run_status(repo: Path, env: dict[str, str], *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PR_PY), "--status", "--head", "feat-status", *extra],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )


def _payload(r: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    assert r.returncode == 0, r.stderr
    payload: dict[str, Any] = json.loads(r.stdout)
    return payload


def _bare_refs(bare: Path) -> list[str]:
    out = _run(["git", "--git-dir", str(bare), "for-each-ref", "--format=%(refname)"])
    return sorted(line for line in out.stdout.splitlines() if line.strip())


def test_status_json_matches_pinned_schema(tmp_path: Path) -> None:
    """Schema conformance: every pinned key, type, and enum value is present."""
    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    env = _gh_env(tmp_path)

    payload = _payload(_run_status(repo, env, "--json"))

    assert payload["schema"] == "gh-router/pr-land/status@1"
    assert payload["repo"] == "test/repo"
    assert payload["head"] == "feat-status"
    assert payload["base"] == "main"
    predicates = payload["predicates"]
    assert predicates["branch_pushed"] is False
    assert predicates["remote"] == "origin"
    assert predicates["ahead"] == 0
    assert predicates["behind"] == 0
    assert predicates["pr_state"] == "none"
    assert predicates["pr_number"] is None
    assert predicates["pr_draft"] is False
    assert predicates["body_state"] == "none"
    assert predicates["worktree_clean"] is True
    assert predicates["changelog_stamped"] is False
    assert predicates["head_pushed"] is False
    assert predicates["checks"] == {"state": "none", "ok": 0, "total": 0}
    assert predicates["mergeable"] == "unknown"
    assert payload["failure_states"] == []
    assert payload["artifact"] == {"path": ".lsz/gh-router/feat-status.md", "stale": False}
    assert payload["title"]["text"] == "feat: two"
    assert payload["title"]["chars"] == 9
    assert payload["title"]["budget"] == 100
    assert payload["title"]["derived"] is True
    assert payload["squash_body_preview"] == ""
    for entry in payload["refusals"]:
        assert set(entry) == {"code", "reason", "remedy", "site"}
        assert entry["site"] != "", "a site always names the caller input or artifact"
    for entry in payload["transitions"]:
        assert set(entry) == {"command", "preconditions", "mutation"}
        assert entry["mutation"] in ("none", "local", "remote")
        assert isinstance(entry["preconditions"], list)
    assert any(entry["mutation"] == "remote" for entry in payload["transitions"]), (
        "the create transition mutates the remote"
    )


def test_status_is_read_only(tmp_path: Path) -> None:
    """Instrumented run: `--status` pushes nothing, creates nothing, deletes nothing."""
    repo = tmp_path / "repo"
    bare = _make_repo(repo)
    env = _gh_env(tmp_path)
    before_refs = _bare_refs(bare)
    before_tree = _run(["git", "-C", str(repo), "status", "--porcelain"]).stdout

    r = _run_status(repo, env, "--json")

    assert r.returncode == 0, r.stderr
    assert _bare_refs(bare) == before_refs, "no ref moved on the origin remote"
    assert not (repo / ".lsz").exists(), "no artifact was created"
    assert _run(["git", "-C", str(repo), "status", "--porcelain"]).stdout == before_tree
    log = Path(env["GH_LOG"]).read_text(encoding="utf-8")
    assert "push" not in log.split()
    assert " POST " not in f" {log} "
    assert "/merge" not in log


def test_status_reports_artifact_stale(tmp_path: Path) -> None:
    """Present leaf: untouched, `stale` reported against the head commit."""
    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    env = _gh_env(tmp_path)
    leaf = repo / ".lsz" / "gh-router" / "feat-status.md"
    _ = leaf.parent.mkdir(parents=True, exist_ok=True)
    _ = leaf.write_text("## Summary\nhand-authored, no marker\n", encoding="utf-8")

    payload = _payload(_run_status(repo, env, "--json"))

    assert payload["artifact"] == {"path": ".lsz/gh-router/feat-status.md", "stale": True}
    assert leaf.read_text(encoding="utf-8") == "## Summary\nhand-authored, no marker\n"

    sha = _run(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.strip()
    _ = leaf.write_text(f"<!-- pr-land scaffold: head={sha} -->\n## Summary\n", encoding="utf-8")
    fresh = _payload(_run_status(repo, env, "--json"))
    assert fresh["artifact"]["stale"] is False


def test_status_out_leaf_is_honoured(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    env = _gh_env(tmp_path)

    payload = _payload(_run_status(repo, env, "--json", "--out", "other/leaf.md"))

    assert payload["artifact"]["path"] == ".lsz/gh-router/other/leaf.md"


def test_status_never_refuses_and_attaches_ready_flip(tmp_path: Path) -> None:
    """Judgment case (advisory): a reused open draft PR exits 0 with the flip attached."""
    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    env = _gh_env(tmp_path, PR_NUMBER="7", PR_STATE="open", PR_DRAFT="true")

    payload = _payload(_run_status(repo, env, "--json"))

    assert payload["predicates"]["pr_state"] == "open"
    assert payload["predicates"]["pr_number"] == "7"
    assert payload["predicates"]["pr_draft"] is True
    codes = [entry["code"] for entry in payload["refusals"]]
    assert "pr_draft" in codes
    flips = [
        entry
        for entry in payload["transitions"]
        if entry["command"] == "gh pr ready 7 --repo test/repo"
    ]
    assert len(flips) == 1
    assert flips[0]["mutation"] == "remote"


def test_status_diverged_is_mechanical_data(tmp_path: Path) -> None:
    """Mechanical case (advisory): a remote-ahead branch reports `diverged` as data."""
    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    env = _gh_env(tmp_path)
    _git(repo, "checkout", "-qb", "scratch", "main")
    _git(repo, "commit", "--allow-empty", "-m", "teammate work")
    other = _run(["git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.strip()
    _git(repo, "checkout", "feat-status")
    _git(repo, "update-ref", "refs/remotes/origin/feat-status", other)

    payload = _payload(_run_status(repo, env, "--json"))

    assert payload["failure_states"] == ["diverged"]
    assert payload["predicates"]["behind"] == 1
    diverged = [entry for entry in payload["refusals"] if entry["code"] == "diverged"]
    assert len(diverged) == 1
    assert diverged[0]["site"] == "origin/feat-status"
    assert "never force-pushes" in diverged[0]["remedy"]


def test_reused_draft_refuses_watch_with_facts_attached(tmp_path: Path) -> None:
    """Judgment case (mutating): `--watch` on a reused draft refuses exit 1 with facts."""
    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    env = _gh_env(tmp_path, PR_NUMBER="7", PR_STATE="open", PR_DRAFT="true")

    r = subprocess.run(
        [
            sys.executable,
            str(PR_PY),
            "--watch",
            "--no-stamp",
            "--head",
            "feat-status",
            "--title",
            "feat: x",
            "--body",
            "## Summary\nReal.\n",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )

    assert r.returncode == 1, r.stderr
    assert "reused PR #7 is still a draft" in r.stderr
    assert "gh pr ready 7 --repo test/repo" in r.stderr
    lines = r.stderr.splitlines()
    facts = json.loads("\n".join(lines[lines.index("{") :]))
    assert facts["refusals"][0]["code"] == "pr_draft"
    assert facts["refusals"][0]["site"] == "PR #7"
    assert facts["transitions"][0]["command"] == "gh pr ready 7 --repo test/repo"
    assert facts["transitions"][0]["mutation"] == "remote"


def test_no_ready_flag_exists(tmp_path: Path) -> None:
    """No `--ready` flag: the flip stays a manual transition, never a flag."""
    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    env = _gh_env(tmp_path)

    r = subprocess.run(
        [sys.executable, str(PR_PY), "--ready"],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )

    assert r.returncode == 2
    assert "unknown arg: --ready" in r.stderr


def test_merge_title_gate_runs_before_any_gh_mutation(tmp_path: Path) -> None:
    """Contract case: under `--merge` the title gate fires before `create_or_reuse_pr`."""
    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    env = _gh_env(tmp_path)
    msg_file = tmp_path / "msg.md"
    _ = msg_file.write_text("## Summary\n- Core: x\n", encoding="utf-8")

    r = subprocess.run(
        [
            sys.executable,
            str(PR_PY),
            "--merge",
            "--no-stamp",
            "--head",
            "feat-status",
            "--title",
            "wip stuff",
            "--body",
            "## Summary\nReal.\n",
            "--squash-message-file",
            str(msg_file),
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )

    assert r.returncode == 1, r.stderr
    assert not Path(env["GH_LOG"]).exists(), "no gh call precedes the title preflight"
    assert '"code": "title_shape"' in r.stderr
    assert '"site": "--title"' in r.stderr


def test_derived_title_refusal_names_the_derivation() -> None:
    """`title_gate` names `HEAD` (not `--title`) when the title came from the log."""
    from _status import title_gate

    entry = title_gate("wip stuff", None, derived=True)
    assert entry is not None
    assert entry["site"] == "HEAD"
    assert "derived from the HEAD commit subject" in entry["reason"]

    supplied = title_gate("wip stuff", None, derived=False)
    assert supplied is not None
    assert supplied["site"] == "--title"
    assert "title from --title" in supplied["reason"]


def test_stamp_failure_hard_fails_with_url_and_remedy(tmp_path: Path) -> None:
    """Stamp half deferred from T1: a wanted stamp that fails exits 1 with url + remedy."""
    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    env = _gh_env(tmp_path)
    _ = (repo / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n### Features\n* landing flow entry\n",
        encoding="utf-8",
    )
    hook = repo / ".git" / "hooks" / "pre-commit"
    _ = hook.write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)

    r = subprocess.run(
        [
            sys.executable,
            str(PR_PY),
            "--head",
            "feat-status",
            "--title",
            "feat: x",
            "--body",
            "## Summary\nReal.\n",
        ],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo,
    )

    assert r.returncode == 1, r.stderr
    assert "PR https://github.com/test/repo/pull/7" in r.stdout
    assert '"code": "stamp_failed"' in r.stderr
    assert "(#7)" in r.stderr
    assert '"site": "CHANGELOG.md"' in r.stderr
    assert "commit it to feat-status" in r.stderr


def test_gh_failure_is_a_structured_refusal_not_a_traceback(tmp_path: Path) -> None:
    """Mechanical case: `gh` errors become refusal data on `--status`, exit 0, no traceback."""
    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    env = _gh_env(tmp_path)
    bindir = tmp_path / "broken-bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    _ = gh.write_text('#!/usr/bin/env bash\necho "Bad credentials" >&2\nexit 1\n', encoding="utf-8")
    gh.chmod(0o755)
    env["PATH"] = f"{bindir}{os.pathsep}{os.environ['PATH']}"

    r = _run_status(repo, env, "--json")

    assert r.returncode == 0
    assert "Traceback" not in r.stderr
    payload: dict[str, Any] = json.loads(r.stdout)
    assert payload["predicates"]["pr_state"] == "none"
    assert payload["refusals"], "the gh failure is refusal data, not silence"
    assert all(set(entry) == {"code", "reason", "remedy", "site"} for entry in payload["refusals"])


def test_status_text_mode_names_mutations(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    env = _gh_env(tmp_path)

    r = _run_status(repo, env)

    assert r.returncode == 0, r.stderr
    assert "transitions:" in r.stdout
    assert "mutates: remote" in r.stdout
    assert "mutates: local" in r.stdout
    assert "refusals:" in r.stdout


@pytest.mark.parametrize(
    "argv_prefix",
    [
        ["git", "rev-parse", "HEAD"],
        ["git", "--no-optional-locks", "status", "--porcelain"],
        ["gh", "pr", "checks"],
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        ["git", "log", "-1", "--pretty=%s"],
        ["git", "config"],
    ],
)
def test_status_survives_read_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    argv_prefix: list[str],
) -> None:
    """R1/R9: every derived read degrades — a raising read never escapes `--status`."""
    import _github
    from _options import PrOptions
    from _status import run_status

    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    env = _gh_env(tmp_path, PR_NUMBER="7", PR_STATE="open", CHECKS_TSV="a\tpass")
    _status_env(monkeypatch, env)
    real = _github.run_command

    def boom(cmd: list[str], **kwargs: object) -> object:
        if cmd[: len(argv_prefix)] == argv_prefix:
            raise _github.PrError(f"command failed: {cmd[0]}: boom")
        return real(cmd, **kwargs)

    monkeypatch.setattr(_github, "run_command", boom)
    assert run_status(PrOptions(head=None, json_output=True), cwd=repo) == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert payload["schema"] == "gh-router/pr-land/status@1"


def _status_env(monkeypatch: pytest.MonkeyPatch, env: dict[str, str]) -> None:
    for key, value in env.items():
        if key == "PATH" or key.startswith(
            ("GH_", "PR_", "POST_", "CHECKS_", "MERGE_", "COMMITS_")
        ):
            monkeypatch.setenv(key, value)


def test_push_auth_failure_is_not_gh_labelled() -> None:
    """R11: a git push auth failure routes to `command_failed`, never `gh_*`."""
    from _errors import PrError
    from _status import pr_error_to_refusal

    entry = pr_error_to_refusal(
        PrError(
            "failed to push feat-x to origin: fatal: Authentication failed for 'https://github.com/t/r.git'"
        )
    )
    assert entry is not None
    assert entry["code"] == "command_failed"
    assert entry["site"] == "git"


def test_bare_unresolvable_host_is_not_gh_labelled() -> None:
    """R11: network failures without a layer fingerprint stay generic."""
    from _errors import PrError
    from _status import pr_error_to_refusal

    entry = pr_error_to_refusal(PrError("Could not resolve host github.com"))
    assert entry is not None
    assert entry["code"] == "command_failed"
    assert not entry["code"].startswith("gh_")
    bare = pr_error_to_refusal(PrError("Could not resolve host"))
    assert bare is not None
    assert bare["code"] == "command_failed"


def test_genuine_gh_failures_still_route_gh() -> None:
    """R11: the gh mapping survives for real gh failures (missing + gh-side auth)."""
    from _errors import PrError
    from _status import pr_error_to_refusal

    missing = pr_error_to_refusal(PrError("command not found or not executable: gh: [Errno 2]"))
    assert missing is not None
    assert missing["code"] == "gh_unavailable"
    assert missing["site"] == "gh"
    auth = pr_error_to_refusal(PrError("failed to query PRs for head feat-x: Bad credentials"))
    assert auth is not None
    assert auth["code"] == "gh_unauthenticated"


def test_failed_compare_asserts_no_push_facts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """R10: a failed compare forces push flags False and records the refusal."""
    import _github
    from _options import PrOptions
    from _status import run_status

    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    _ = _run(["git", "-C", str(repo), "push", "origin", "feat-status"], cwd=None)
    _status_env(monkeypatch, _gh_env(tmp_path))
    real = _github.run_command

    def boom(cmd: list[str], **kwargs: object) -> object:
        if cmd[:2] == ["git", "rev-list"]:
            raise _github.PrError("command failed: git rev-list: boom")
        return real(cmd, **kwargs)

    monkeypatch.setattr(_github, "run_command", boom)
    assert run_status(PrOptions(head="feat-status", json_output=True), cwd=repo) == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert payload["predicates"]["branch_pushed"] is False
    assert payload["predicates"]["head_pushed"] is False
    assert payload["predicates"]["ahead"] == 0
    assert payload["predicates"]["behind"] == 0
    compare = [entry for entry in payload["refusals"] if "compare" in entry["reason"]]
    assert len(compare) == 1
    assert "origin/feat-status" in compare[0]["reason"]


def test_git_failure_is_not_labelled_gh() -> None:
    """R3: a `git` failure is `command_failed` at site `git`, never `gh_offline`."""
    from _errors import PrError
    from _status import pr_error_to_refusal

    entry = pr_error_to_refusal(PrError("command timed out after 30.0s: git rev-parse HEAD"))
    assert entry is not None
    assert entry["code"] == "command_failed"
    assert entry["site"] == "git"
    assert "github is unreachable" not in entry["reason"]


def test_author_substring_is_not_unauthenticated() -> None:
    """R3: the auth markers match real auth failures but not `author`."""
    from _errors import PrError
    from _status import pr_error_to_refusal

    assert pr_error_to_refusal(PrError("could not list commit authors"), tool="gh") is None
    entry = pr_error_to_refusal(PrError("authentication failed for gh"), tool="gh")
    assert entry is not None
    assert entry["code"] == "gh_unauthenticated"


def test_head_slug_is_injective_and_path_safe() -> None:
    """R2: `feat/x`, `feat-x` and `feat.x` map to three distinct safe leaves."""
    from _status import head_slug

    slashed, dashed, dotted = head_slug("feat/x"), head_slug("feat-x"), head_slug("feat.x")
    assert len({slashed, dashed, dotted}) == 3, (slashed, dashed, dotted)
    assert dashed == "feat-x"
    assert dotted == "feat.x"
    assert "/" not in slashed
    assert slashed == "feat%2Fx"
    assert head_slug("100%25") == "100%2525"


def test_head_slug_stays_within_name_max_and_distinct() -> None:
    """R13: expanded refs cap to a digest-suffixed stem within `NAME_MAX`."""
    from _status import head_slug

    long_unicode = head_slug("\u00fc" * 86)
    slashed = head_slug("a/" * 100)
    assert long_unicode != slashed
    for slug in (long_unicode, slashed):
        raw = slug.encode("utf-8")
        assert len(raw) <= 255, len(raw)
        assert "/" not in slug
        assert len(slug.split("-")) >= 2, "the full-ref digest rides the capped stem"


def test_status_prints_no_refusal_prose(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """R4: the advisory preview swallows its prose — stderr stays empty at exit 0."""
    from _options import PrOptions
    from _status import run_status

    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    _status_env(monkeypatch, _gh_env(tmp_path))
    assert run_status(PrOptions(head="feat-status"), cwd=repo) == 0
    captured = capsys.readouterr()
    assert captured.err == ""


@pytest.mark.parametrize("dirty_kind", ["unstaged", "untracked"])
def test_status_reports_dirty_worktree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    dirty_kind: str,
) -> None:
    """R6: `worktree_clean` is False for unstaged and untracked changes alike."""
    from _options import PrOptions
    from _status import run_status

    repo = tmp_path / "repo"
    _ = _make_repo(repo)
    _status_env(monkeypatch, _gh_env(tmp_path))
    if dirty_kind == "unstaged":
        _ = (repo / "one.txt").write_text("edited\n", encoding="utf-8")
    else:
        _ = (repo / "scratch.txt").write_text("scratch\n", encoding="utf-8")
    assert run_status(PrOptions(head="feat-status", json_output=True), cwd=repo) == 0
    payload: dict[str, Any] = json.loads(capsys.readouterr().out)
    assert payload["predicates"]["worktree_clean"] is False
