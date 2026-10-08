"""pr-land watch fast-fail: dirty debounce, unknown retries, slim vs verbose output.

Every case drives `pr.py` in-process against a scripted fake `gh` and a recording
`time.sleep`, so no network, no real waits, and no subprocess: the assertion is on the
exact argv sequence, the exact sleeps, and the exact stderr the gates emit.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PR_SCRIPTS = REPO_ROOT / "skills/gh-router/subskills/pr-land/scripts"

if str(PR_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(PR_SCRIPTS))

import _github as github_mod  # noqa: E402
import pr as pr_mod  # noqa: E402

NUM = "999"
URL = "https://github.com/test/repo/pull/999"
CONFLICT_POINTER = (
    "uv run skills/gh-router/subskills/pr-conflict/scripts/extract_conflict_context.py"
)
FAILING_JSON = (
    '[{"name": "build", "bucket": "pass", "link": "", "state": "SUCCESS"},'
    ' {"name": "test", "bucket": "fail",'
    ' "link": "https://github.com/test/repo/actions/runs/77777/job/2", "state": "FAILURE"}]'
)
RUN_BODY = "FAIL: test_something() failed assert 1 == 2"


class FakeGh:
    """Scripted `gh`: a queue of (mergeable, mergeable_state) readings plus check fixtures."""

    def __init__(
        self,
        readings: list[tuple[str, str]],
        *,
        files: str = "",
        files_rc: int = 0,
        checks_payload: str = "",
        checks_json: str = "",
        checks_tail: str = "",
        run_body: str = "",
    ) -> None:
        self.readings = list(readings)
        self.files = files
        self.files_rc = files_rc
        self.checks_payload = checks_payload
        self.checks_json = checks_json
        self.checks_tail = checks_tail
        self.run_body = run_body
        self.calls: list[list[str]] = []
        self.sleeps: list[float] = []
        self.poll_count = 0

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(github_mod, "run_command", self.run)
        monkeypatch.setattr(pr_mod.time, "sleep", self.sleep)

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)

    def _reading(self) -> tuple[str, str]:
        if len(self.readings) > 1:
            return self.readings.pop(0)
        return self.readings[0]

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
    ) -> subprocess.CompletedProcess[str]:
        _ = (timeout, cwd, capture_output, text, check, env)
        self.calls.append(list(cmd))
        if (
            cmd[:3] == ["gh", "api", f"repos/test/repo/pulls/{NUM}"]
            and cmd[-1] == ".mergeable_state"
        ):
            return self._result(cmd, f"{self._reading()[1]}\n")
        if f"/pulls/{NUM}" in " ".join(cmd) and cmd[-1] == ".html_url":
            return self._result(cmd, f"{URL}\n")
        if cmd[:3] == ["gh", "api", f"repos/test/repo/pulls/{NUM}"] and "-X" in cmd:
            return self._result(cmd, "")
        if cmd[:3] == ["gh", "api", f"repos/test/repo/pulls/{NUM}"]:
            mergeable, state = self._reading()
            self.poll_count += 1
            return self._result(cmd, f"{mergeable}\t{state}\t{URL}\n")
        if cmd[:3] == ["gh", "pr", "view"]:
            return self._result(cmd, self.files, self.files_rc)
        if cmd[:3] == ["gh", "pr", "checks"] and "name,bucket,link,state" in cmd:
            return self._result(cmd, self.checks_json)
        if cmd[:3] == ["gh", "pr", "checks"] and "--json" in cmd:
            return self._result(cmd, self.checks_payload)
        if cmd[:3] == ["gh", "pr", "checks"]:
            return self._result(cmd, self.checks_tail)
        if cmd[:3] == ["gh", "run", "view"]:
            return self._result(cmd, self.run_body)
        # --- repo/create plumbing so main() can be driven end-to-end (M-4) --------------
        joined = " ".join(cmd)
        if "rev-parse --abbrev-ref" in joined:
            return self._result(cmd, "feat-x\n")
        if "config --get branch." in joined:
            return self._result(cmd, "", 1)
        if "remote get-url" in joined:
            return self._result(cmd, "https://github.com/test/repo.git\n")
        if cmd[:3] == ["gh", "api", "repos/test/repo"] and cmd[-1] == ".default_branch":
            return self._result(cmd, "main\n")
        if "pulls?head=" in joined:
            return self._result(cmd, f"{NUM}\tfalse\n")
        return self._result(cmd, "")


# The spec's literal budgets: two dirty strikes 3s apart, five unknown tries 2s apart,
# ten files shown before `(+N more)`. Pinned as numbers so a constant edit fails here too.
DIRTY_STRIKES = 2
DIRTY_INTERVAL = 3.0
UNKNOWN_TRIES = 5
UNKNOWN_INTERVAL = 2.0
CONFLICT_FILES_MAX = 10

# --- dirty: two strikes, DIRTY_STRIKES confirmations, then the conflict path -----------


def test_dirty_is_confirmed_twice_before_the_gate_refuses(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A single `dirty` reading is a candidate, not a verdict: poll again after DIRTY_INTERVAL.

    Mutation: returning on the first `dirty` reading fails the poll/sleep counts below.
    """
    gh = FakeGh([("false", "dirty")], files="a.py b.py")
    gh.install(monkeypatch)

    assert pr_mod.check_conflicts("test/repo", NUM, "main") is False

    assert gh.poll_count == DIRTY_STRIKES
    assert gh.sleeps == [DIRTY_INTERVAL]
    err = capsys.readouterr().err
    assert "conflicting: mergeable=false merge_state_status=dirty" in err
    assert "touched files: a.py b.py" in err
    assert f"run '{CONFLICT_POINTER}'" in err


def test_non_dirty_reading_resets_the_dirty_strikes(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """dirty -> clean clears the strike; the gate passes instead of latching a conflict.

    This pair alone cannot refute the reset — a latched streak passes it too. The reset is
    refuted by test_dirty_strikes_reset_through_an_unknown_reading (dirty -> unknown ->
    dirty -> clean), which a deleted `strikes = 0` turns into a refusal.
    """
    gh = FakeGh([("true", "dirty"), ("true", "clean")], files="a.py b.py")
    gh.install(monkeypatch)

    assert pr_mod.check_conflicts("test/repo", NUM, "main") is True

    assert gh.poll_count == 2
    assert gh.sleeps == [DIRTY_INTERVAL]
    assert "conflicting" not in capsys.readouterr().err


def test_dirty_strikes_reset_through_an_unknown_reading(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """dirty -> unknown -> dirty -> clean returns True: the `unknown` poll resets the strike.

    Mutation: deleting `strikes = 0` in `resolve_merge_state` latches the streak, so the
    second `dirty` reaches DIRTY_STRIKES and the gate refuses (False, 3 polls). The real
    sequence observed here is 4 polls with sleeps [3.0, 2.0, 3.0].
    """
    gh = FakeGh([("true", "dirty"), ("null", "unknown"), ("true", "dirty"), ("true", "clean")])
    gh.install(monkeypatch)

    assert pr_mod.check_conflicts("test/repo", NUM, "main") is True

    assert gh.poll_count == 4
    assert gh.sleeps == [DIRTY_INTERVAL, UNKNOWN_INTERVAL, DIRTY_INTERVAL]
    assert "conflicting" not in capsys.readouterr().err


# --- unknown: UNKNOWN_TRIES attempts, UNKNOWN_INTERVAL apart, then the refusal ---------


def test_unknown_mergeability_retries_then_fails_fast(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An unresolved mergeability refuses the gate; it must not burn the 60x10s watch.

    Mutation: returning True here (the old defect) makes the watch stall and fails this.
    """
    gh = FakeGh([("null", "unknown")], files="a.py b.py")
    gh.install(monkeypatch)

    assert pr_mod.check_conflicts("test/repo", NUM, "main") is False

    assert gh.poll_count == UNKNOWN_TRIES
    assert gh.sleeps == [UNKNOWN_INTERVAL] * (UNKNOWN_TRIES - 1)
    err = capsys.readouterr().err
    assert "unknown: mergeable=null merge_state_status=unknown" in err
    assert f"PR {URL}" in err
    assert "touched files: a.py b.py" in err
    assert f"run '{CONFLICT_POINTER}'" in err


def test_unknown_that_recovers_is_not_refused(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A second reading of `clean` ends the unknown retries at once (no full budget spent)."""
    gh = FakeGh([("null", "unknown"), ("true", "clean")])
    gh.install(monkeypatch)

    assert pr_mod.check_conflicts("test/repo", NUM, "main") is True

    assert gh.poll_count == 2
    assert gh.sleeps == [UNKNOWN_INTERVAL]
    assert "unknown" not in capsys.readouterr().err


# --- conflict report shape: verdict + url + capped files + pointer --------------------


def test_conflict_report_caps_files_at_ten_with_a_more_marker(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Twelve conflicting files print ten, then `(+2 more)`; a short list prints in full."""
    twelve = " ".join(f"f{i}.py" for i in range(1, 13))
    gh = FakeGh([("false", "dirty")], files=twelve)
    gh.install(monkeypatch)

    assert pr_mod.check_conflicts("test/repo", NUM, "main") is False
    err = capsys.readouterr().err
    files_line = next(line for line in err.splitlines() if line.startswith("touched files: "))
    assert files_line.endswith(" (+2 more)")
    assert (
        len(files_line[len("touched files: ") : -len(" (+2 more)")].split()) == CONFLICT_FILES_MAX
    )

    gh = FakeGh([("false", "dirty")], files="a.py b.py")
    gh.install(monkeypatch)
    assert pr_mod.check_conflicts("test/repo", NUM, "main") is False
    err = capsys.readouterr().err
    assert "touched files: a.py b.py" in err
    assert "more)" not in err


def test_report_line_names_the_verdict_word_the_url_and_the_helper(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The shared report is URL, verdict word, files, and the pr-conflict pointer, in order."""
    gh = FakeGh([("false", "dirty")], files="a.py")
    gh.install(monkeypatch)

    assert pr_mod.check_conflicts("test/repo", NUM, "main") is False
    lines = capsys.readouterr().err.splitlines()
    assert lines[0] == f"PR {URL}"
    assert lines[1].startswith("conflicting: ")
    assert lines[2] == "touched files: a.py"
    assert CONFLICT_POINTER in lines[3]
    assert "delegate resolution to a worker subagent" in lines[3]


def test_conflict_report_prints_none_resolved_when_files_are_empty(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """M-2: empty or failed `gh pr view` prints `touched files: (none resolved)`, never a drop.

    The list is every path the PR touches (`gh pr view --json files` has no conflict
    filter), so the label says `touched`, not `conflicting`.
    """
    gh = FakeGh([("false", "dirty")], files="")
    gh.install(monkeypatch)
    assert pr_mod.check_conflicts("test/repo", NUM, "main") is False
    lines = capsys.readouterr().err.splitlines()
    assert lines[2] == "touched files: (none resolved)"

    gh = FakeGh([("false", "dirty")], files="boom", files_rc=1)
    gh.install(monkeypatch)
    assert pr_mod.check_conflicts("test/repo", NUM, "main") is False
    lines = capsys.readouterr().err.splitlines()
    assert lines[2] == "touched files: (none resolved)"


# --- watch output: one line per poll, slim failure, verbose dumps ---------------------


def pending_then_timeout(monkeypatch: pytest.MonkeyPatch) -> FakeGh:
    gh = FakeGh(
        [("true", "clean")],
        checks_payload="",  # every check still pending -> the loop keeps polling
        checks_tail="test-suite\tfail\t1m\nother\tpass\t2m",
    )
    gh.install(monkeypatch)
    return gh


def test_watch_prints_one_poll_line_with_state_and_verdict(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Each poll is a single line carrying both `mergeable_state` and the checks verdict."""
    _ = pending_then_timeout(monkeypatch)

    assert pr_mod.watch_checks("test/repo", NUM, "main", poll_tries=3, poll_interval=0) is False

    polls = [line for line in capsys.readouterr().err.splitlines() if "mergeable_state=" in line]
    assert len(polls) == 3
    for i, line in enumerate(polls, start=1):
        assert line == f"checks pending (mergeable_state=clean, {i}/3)"


def test_watch_folds_a_behind_head_into_the_poll_line(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A `behind` head still prints exactly ONE line per poll — no standalone warning.

    M-1: the old loop printed `warning: head branch is behind <base>` plus the poll line,
    so a behind PR produced two stderr lines per poll (up to 120 over 60 polls).
    """
    gh = FakeGh([("true", "behind")], checks_payload="")
    gh.install(monkeypatch)

    assert pr_mod.watch_checks("test/repo", NUM, "main", poll_tries=3, poll_interval=0) is False

    lines = capsys.readouterr().err.splitlines()
    polls = [line for line in lines if "mergeable_state=" in line]
    assert len(polls) == 3
    for i, line in enumerate(polls, start=1):
        assert line == f"checks pending (mergeable_state=behind, {i}/3, head behind main)"
    assert not [line for line in lines if line.startswith("warning: head branch is behind")]


def test_watch_timeout_is_slim_without_verbose(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Default (slim): the timeout line alone — no `gh pr checks` tail dump."""
    gh = pending_then_timeout(monkeypatch)

    assert pr_mod.watch_checks("test/repo", NUM, "main", poll_tries=2, poll_interval=0) is False

    err = capsys.readouterr().err
    assert "checks timeout after 0s — no green verdict" in err
    assert "test-suite" not in err
    assert not [c for c in gh.calls if c[:3] == ["gh", "pr", "checks"] and "--json" not in c]


def test_watch_timeout_dumps_the_checks_tail_with_verbose(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--verbose` restores the `gh pr checks` tail after the timeout line."""
    _ = pending_then_timeout(monkeypatch)

    assert (
        pr_mod.watch_checks("test/repo", NUM, "main", poll_tries=2, poll_interval=0, verbose=True)
        is False
    )

    err = capsys.readouterr().err
    assert "checks timeout after 0s — no green verdict" in err
    assert "test-suite" in err


def failing_fixture(monkeypatch: pytest.MonkeyPatch) -> FakeGh:
    gh = FakeGh(
        [("true", "clean")],
        checks_payload="test\tfail\n",
        checks_json=FAILING_JSON,
        run_body=RUN_BODY,
    )
    gh.install(monkeypatch)
    return gh


def test_watch_failure_is_slim_by_default(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Slim failure: the run id(s) plus the one-line pointer, never the log body."""
    gh = failing_fixture(monkeypatch)

    assert pr_mod.watch_checks("test/repo", NUM, "main", poll_tries=2, poll_interval=0) is False

    err = capsys.readouterr().err
    assert "checks failure (mergeable_state=clean, 1/2)" in err
    assert "checks failed: failing run id(s): 77777" in err
    assert "run 'gh run view --run-id <id> --log-failed' (or 'ci.sh why')" in err
    assert RUN_BODY not in err
    assert not [c for c in gh.calls if c[:3] == ["gh", "run", "view"]]


def test_watch_failure_dumps_logs_with_verbose(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--verbose` fetches `gh run view <id> --log-failed` and prints its body."""
    gh = failing_fixture(monkeypatch)

    assert (
        pr_mod.watch_checks("test/repo", NUM, "main", poll_tries=2, poll_interval=0, verbose=True)
        is False
    )

    err = capsys.readouterr().err
    assert RUN_BODY in err
    assert ["gh", "run", "view", "77777", "--repo", "test/repo", "--log-failed"] in gh.calls


def test_watch_fails_fast_on_dirty_with_the_conflict_report(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A dirty PR stops the watch after the debounce, with the shared report — not 600s."""
    gh = FakeGh([("false", "dirty")], files="a.py")
    gh.install(monkeypatch)

    assert pr_mod.watch_checks("test/repo", NUM, "main", poll_tries=60, poll_interval=10) is False

    assert gh.poll_count == DIRTY_STRIKES
    assert gh.sleeps == [DIRTY_INTERVAL]
    err = capsys.readouterr().err
    assert "conflicting: mergeable=false merge_state_status=dirty" in err
    assert f"run '{CONFLICT_POINTER}'" in err


def test_watch_does_not_poll_checks_when_mergeability_is_unresolved(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unknown mergeability returns before any checks read — the stall the gate must avoid."""
    gh = FakeGh([("null", "unknown")])
    gh.install(monkeypatch)

    assert pr_mod.watch_checks("test/repo", NUM, "main", poll_tries=60, poll_interval=10) is False

    assert gh.poll_count == UNKNOWN_TRIES
    assert not [c for c in gh.calls if c[:3] == ["gh", "pr", "checks"]]
    assert "unknown: mergeable=null merge_state_status=unknown" in capsys.readouterr().err


# --- merge_pr shares the same fast-fail and report ------------------------------------


def test_merge_pr_fails_fast_on_dirty_through_the_conflict_report(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`merge_pr` refuses a dirty PR after the two-strike debounce, before any merge PUT."""
    gh = FakeGh([("false", "dirty")], files="a.py")
    gh.install(monkeypatch)

    assert pr_mod.merge_pr("test/repo", NUM, "main", "feat: x", "Body") is False

    state_polls = [c for c in gh.calls if c[-1] == ".mergeable_state"]
    assert len(state_polls) == DIRTY_STRIKES
    assert gh.sleeps == [DIRTY_INTERVAL]
    err = capsys.readouterr().err
    assert "conflicting: merge_state_status=dirty" in err
    assert f"PR {URL}" in err
    assert f"run '{CONFLICT_POINTER}'" in err
    assert "refusing to merge: mergeable_state=dirty (not clean)" in err
    assert not [c for c in gh.calls if "/merge" in " ".join(c)]


def test_merge_pr_refuses_a_state_that_never_settles(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A non-clean state that is not `clean`/`dirty` still refuses (blocked/unstable/behind)."""
    gh = FakeGh([("null", "unstable")])
    gh.install(monkeypatch)

    assert pr_mod.merge_pr("test/repo", NUM, "main", "feat: x", "Body") is False

    state_polls = [c for c in gh.calls if c[-1] == ".mergeable_state"]
    assert len(state_polls) == UNKNOWN_TRIES
    err = capsys.readouterr().err
    assert "refusing to merge: mergeable_state=unstable (not clean)" in err
    assert not [c for c in gh.calls if "/merge" in " ".join(c)]


# --- flag plumbing and the help budget ------------------------------------------------


def test_verbose_flag_is_off_by_default_and_parsed() -> None:
    """`--verbose` is opt-in; the slim default is what `--watch` gets without it."""
    assert pr_mod.parse_args([]).verbose is False
    assert pr_mod.parse_args(["--watch"]).verbose is False
    assert pr_mod.parse_args(["--watch", "--verbose"]).verbose is True


def test_help_stays_within_the_line_budget_and_names_verbose(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Adding `--verbose` must not push `--help` past its 14-line budget."""
    pr_mod.print_usage()
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) <= 14
    assert any("--verbose" in line for line in lines)


# --- end-to-end wiring: `--verbose` must reach the watch path through main() ----------


def _main_watch_args(*extra: str) -> list[str]:
    return [
        "--head",
        "feat-x",
        "--title",
        "feat: x",
        "--body",
        "## Summary\nReal.\n",
        "--watch",
        "--no-stamp",
        *extra,
    ]


def test_main_watch_verbose_dumps_the_failing_log(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`main(["--watch", "--verbose", ...])` threads `verbose` into the watch failure dump.

    M-4: deleting `verbose=options.verbose` in `main` left every other test green, so this
    drives the real `main` end-to-end (reuse path -> watch -> failure). `merge_pr` owns no
    log dump, so there is nothing to thread there.
    """
    gh = FakeGh(
        [("true", "clean")],
        checks_payload="test\tfail\n",
        checks_json=FAILING_JSON,
        run_body=RUN_BODY,
    )
    gh.install(monkeypatch)

    assert pr_mod.main(_main_watch_args("--verbose")) == 1

    err = capsys.readouterr().err
    assert RUN_BODY in err
    assert ["gh", "run", "view", "77777", "--repo", "test/repo", "--log-failed"] in gh.calls


def test_main_watch_is_slim_without_verbose(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`main(["--watch", ...])` without `--verbose` keeps the slim failure line only.

    M-4 counterpart: neither the verbose log body nor the `gh run view` call may appear.
    """
    gh = FakeGh(
        [("true", "clean")],
        checks_payload="test\tfail\n",
        checks_json=FAILING_JSON,
        run_body=RUN_BODY,
    )
    gh.install(monkeypatch)

    assert pr_mod.main(_main_watch_args()) == 1

    err = capsys.readouterr().err
    assert "checks failed: failing run id(s): 77777" in err
    assert RUN_BODY not in err
    assert not [c for c in gh.calls if c[:3] == ["gh", "run", "view"]]
