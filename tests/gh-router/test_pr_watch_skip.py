"""The `--watch` verdict reads a skipped check by the head, not the latest run.

`gh pr checks` reports one row per check name — the *latest* run's bucket. A later
`skipped` run therefore shadows an earlier `success` (or `failure`), so the merge
gate could read green without the gate having passed. When any bucket is `skipping`
the watch resolves the truth from the head's full check-run list: a skipping name
that succeeded on the head is a shadowed pass, and any other skip stays not green.

Every case drives `_github.watch_checks` in-process against a scripted fake `gh`
and a recording `time.sleep`, so no network and no real waits. Each test names the
mutation it kills.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"

import _github as github_mod  # noqa: E402
from _errors import CommandFailed  # noqa: E402
from _github import resolve_skipped  # noqa: E402

NUM = "999"
URL = "https://github.com/test/repo/pull/999"
SHA = "0dc59dfa"


class FakeWatch:
    """Scripted `gh`: mergeability, the checks poll, the head sha, and the check-run list."""

    def __init__(
        self,
        *,
        checks: str,
        conclusions: str = "",
        sha: str = SHA,
        check_runs_rc: int = 0,
        merge_state: str = "clean",
        check_runs_raises: bool = False,
    ) -> None:
        self.checks = checks
        self.conclusions = conclusions
        self.sha = sha
        self.check_runs_rc = check_runs_rc
        self.check_runs_raises = check_runs_raises
        self.merge_state = merge_state
        self.calls: list[list[str]] = []
        self.sleeps: list[float] = []

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(github_mod, "run_command", self.run)
        monkeypatch.setattr(github_mod.time, "sleep", self.sleep)

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)

    @staticmethod
    def _result(cmd: list[str], text: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, returncode, text, "")

    def run(
        self,
        cmd: list[str],
        *,
        timeout: float = 30.0,
        cwd: Path | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = False,
        env: dict[str, str] | None = None,
        required: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        _ = (timeout, cwd, capture_output, text, check, env, required)
        self.calls.append(list(cmd))
        joined = " ".join(cmd)
        if cmd[:3] == ["gh", "api", f"repos/test/repo/pulls/{NUM}"] and cmd[-1] == ".head.sha":
            return self._result(cmd, f"{self.sha}\n")
        if "check-runs" in joined:
            if self.check_runs_raises:
                raise CommandFailed("gh", list(cmd), self.check_runs_rc, "boom")
            return self._result(cmd, self.conclusions, self.check_runs_rc)
        if cmd[:3] == ["gh", "api", f"repos/test/repo/pulls/{NUM}"]:
            return self._result(cmd, f"true\t{self.merge_state}\t{URL}\n")
        if cmd[:3] == ["gh", "pr", "checks"]:
            return self._result(cmd, self.checks)
        return self._result(cmd, "")

    def check_runs_calls(self) -> list[list[str]]:
        return [c for c in self.calls if "check-runs" in " ".join(c)]

    def head_sha_calls(self) -> list[list[str]]:
        return [
            c
            for c in self.calls
            if c[:3] == ["gh", "api", f"repos/test/repo/pulls/{NUM}"] and c[-1] == ".head.sha"
        ]


def _watch(monkeypatch: pytest.MonkeyPatch, gh: FakeWatch, *, tries: int = 1) -> bool:
    gh.install(monkeypatch)
    return github_mod.watch_checks("test/repo", NUM, "main", poll_tries=tries, poll_interval=0)


# --- the resolution rule (pure) -------------------------------------------------------


def test_resolve_skipped_reads_a_shadowed_success_green() -> None:
    """`success` then `skipped`: the head's check-run list confirms the skip was a pass.

    Mutation: return `verdict` unchanged for every skip -> a shadowed success stays
    `pending`.
    """
    assert resolve_skipped("pending", {"check"}, {"check": {"success"}}) == "success"


def test_resolve_skipped_keeps_an_unbacked_skip_not_green() -> None:
    """A skip the head never succeeded is not green, even beside a passing check.

    Mutation: treat any `skipping` bucket as a pass -> the mixed case returns
    `success` and a skip that shadows a failure merges red.
    """
    assert resolve_skipped("pending", {"check"}, {}) == "pending"
    assert resolve_skipped("pending", {"check"}, {"other": {"success"}}) == "pending"
    assert resolve_skipped("success", {"check"}, {}) == "pending"
    assert resolve_skipped("success", {"check"}, {"check": {"success"}}) == "success"


def test_resolve_skipped_never_downgrades_a_failure() -> None:
    """A genuine failing check stays red whatever the skip says.

    Mutation: run the skip resolution before the failure short-circuit -> a
    `failure` verdict becomes `pending` and the watch waits instead of failing.
    """
    assert resolve_skipped("failure", {"check"}, {"check": {"success"}}) == "failure"
    assert resolve_skipped("failure", {"check"}, {}) == "failure"


def test_resolve_skipped_without_skips_is_the_verdict() -> None:
    """No skipping bucket: the poll verdict passes through untouched."""
    assert resolve_skipped("pending", set(), {}) == "pending"
    assert resolve_skipped("success", set(), {}) == "success"


def test_resolve_skipped_fails_fast_on_a_shadowed_failure() -> None:
    """A skip over a failed run is a failure, not an unresolved skip.

    Reading it as `pending` polled the full 60x10s budget and reported a timeout
    instead of naming a red head. The head's own conclusion says `failure`.

    Mutation: return `pending` for an unbacked skip without consulting the
    conclusions -> the verdict waits instead of failing.
    """
    assert resolve_skipped("pending", {"check"}, {"check": {"failure"}}) == "failure"
    assert resolve_skipped("pending", {"check"}, {"check": {"cancelled"}}) == "failure"
    assert resolve_skipped("pending", {"check"}, {"check": {"skipped"}}) == "pending"
    assert resolve_skipped("pending", {"check"}, {"check": {"failure", "success"}}) == "success", (
        "a head that also succeeded is a shadowed pass, not a shadowed failure"
    )


# --- the watch path (integration through the seam) ------------------------------------


def test_watch_reads_a_shadowed_success_green(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The poll reports `skipping`; the head's check-run list proves it was a success.

    Mutation: judge the head from `gh pr checks` alone -> the poll stays `pending`
    and the watch returns False instead of True.
    """
    gh = FakeWatch(checks="check\tskipping\n", conclusions="success\tcheck\n")

    assert _watch(monkeypatch, gh) is True
    assert "checks success (mergeable_state=clean, 1/1)" in capsys.readouterr().err
    assert gh.head_sha_calls(), "the head sha must be read to key the check-run lookup"
    assert gh.check_runs_calls(), "the head's check-run list must be read for a skip"


def test_watch_paginates_the_check_run_read(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The check-run read must walk every page, not just the first 30.

    Mutation: drop `--paginate` -> a shadowed success past the first page reads as
    absent and the skip stays not green, so a valid merge is blocked by a page
    boundary. The argv is the contract here; the seam returns a single page.
    """
    gh = FakeWatch(checks="check\tskipping\n", conclusions="success\tcheck\n")

    assert _watch(monkeypatch, gh) is True
    _ = capsys.readouterr()
    reads = gh.check_runs_calls()
    assert reads, "the head's check-run list must be read for a skip"
    assert all("--paginate" in call for call in reads), reads


def test_watch_keeps_a_skip_that_shadows_a_failure_not_green(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A later `skipped` run over an earlier `failure` must fail, not wait.

    The head's check-run list holds `check` as a `failure`, so the verdict is
    `failure`: the watch fails on the first poll and names the red head, instead of
    polling the full budget and reporting a timeout.

    Mutation: return `pending` for an unbacked skip -> the poll prints `pending` and
    the watch waits.
    """
    gh = FakeWatch(checks="check\tskipping\n", conclusions="failure\tcheck\n")

    assert _watch(monkeypatch, gh, tries=1) is False
    assert "checks failure (mergeable_state=clean, 1/1)" in capsys.readouterr().err


def test_watch_keeps_a_skip_masked_beside_a_passing_check_not_green(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A passing check must not carry an unbacked skip to green (the red-ledger window).

    `gh pr checks` reads `success` (one pass, one skip), but the head never succeeded
    on `check` — the case a later stale-payload `synchronize` run produces.

    Mutation: only resolve the verdict when it is already `pending` -> the mixed
    case stays `success` and a red ledger merges.
    """
    gh = FakeWatch(checks="tests\tpass\ncheck\tskipping\n", conclusions="success\ttests\n")

    assert _watch(monkeypatch, gh, tries=1) is False
    assert "checks pending (mergeable_state=clean, 1/1)" in capsys.readouterr().err


def test_watch_keeps_a_skip_with_no_success_on_the_head_not_green(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Only `skipped` on the head: zero CI ran, so the gate never goes green.

    Mutation: treat a skip with no check-run evidence as a pass -> the watch
    returns True.
    """
    gh = FakeWatch(checks="check\tskipping\n", conclusions="")

    assert _watch(monkeypatch, gh, tries=1) is False
    assert "checks pending (mergeable_state=clean, 1/1)" in capsys.readouterr().err


def test_watch_makes_no_check_run_read_without_a_skip(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A clean poll costs exactly the mergeability read plus the checks read.

    Mutation: read the check-run list unconditionally -> the two extra reads appear.
    """
    gh = FakeWatch(checks="tests\tpass\n")

    assert _watch(monkeypatch, gh) is True
    assert "checks success (mergeable_state=clean, 1/1)" in capsys.readouterr().err
    assert gh.check_runs_calls() == []
    assert gh.head_sha_calls() == []


def test_watch_stays_not_green_when_the_check_run_read_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A failed check-run read fails closed with no traceback.

    Mutation: drop the try/except (or the non-zero guard) in `head_check_conclusions` ->
    the read raises or reads the skip as a pass, so the watch crashes or returns True.
    """
    gh = FakeWatch(checks="check\tskipping\n", conclusions="", check_runs_rc=1)
    assert _watch(monkeypatch, gh, tries=1) is False
    assert "checks pending (mergeable_state=clean, 1/1)" in capsys.readouterr().err

    gh = FakeWatch(checks="check\tskipping\n", check_runs_raises=True)
    assert _watch(monkeypatch, gh, tries=1) is False
    assert "checks pending (mergeable_state=clean, 1/1)" in capsys.readouterr().err


def test_watch_never_reads_green_while_github_says_unstable(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An all-pass poll beside `unstable` is a partial read, not a green head.

    Observed on PR #354: the poll's rows were all pass or resolved-skip while the
    `tests` check had not registered yet, so the verdict read `success` with the
    suite unrun. `unstable` is GitHub saying a status is still not passing.

    Mutation: drop the `obs.state == "unstable"` guard -> the watch returns True on
    the first poll and reports `checks success`.
    """
    gh = FakeWatch(checks="tests\tpass\n", merge_state="unstable")

    assert _watch(monkeypatch, gh, tries=1) is False
    assert "checks pending (mergeable_state=unstable, 1/1)" in capsys.readouterr().err


def test_watch_reads_green_when_github_says_clean(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The guard is scoped to `unstable`: a clean head still goes green at once."""
    gh = FakeWatch(checks="tests\tpass\n", merge_state="clean")

    assert _watch(monkeypatch, gh) is True
    assert "checks success (mergeable_state=clean, 1/1)" in capsys.readouterr().err
