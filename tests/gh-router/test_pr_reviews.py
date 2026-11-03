"""`pr.py --reviews` and the review-thread read: the post-PR loop's collect step.

`_github.fetch_review_threads` owns the fail-closed read, `_reviews.run_reviews`
owns the caller shape, and `merge_pr` gates on the same list. Each case pins a
mutation: dropping the resolved filter admits a settled thread, dropping the
page cap turns a partial read into "settled", and dropping the merge gate lets
an unresolved thread through.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import _github
import _reviews
import pr as pr_mod
import pytest
from _errors import PrError, RefusalError
from _options import PrOptions

from tests.gh_helpers import review_thread_node, review_threads_payload


def _completed(cmd: list[str], out: str = "", code: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(cmd, code, out, "")


def _graphql_pages(pages: list[str], calls: list[list[str]] | None = None):
    """Answer each GraphQL call with the next page; every other call succeeds empty."""

    def fake(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        if calls is not None:
            calls.append(list(cmd))
        if "graphql" in " ".join(cmd):
            return _completed(cmd, pages.pop(0))
        return _completed(cmd)

    return fake


# --- the read -------------------------------------------------------------------------


def test_fetch_drops_resolved_threads_and_maps_every_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = review_threads_payload(
        [
            review_thread_node(thread_id="T1", resolved=True, body="already handled"),
            review_thread_node(
                thread_id="T2",
                path="clients/x.ts",
                line=42,
                author="sourcery-ai",
                body="Please fix this.",
            ),
        ]
    )
    monkeypatch.setattr(_github, "run_command", _graphql_pages([payload]))

    threads = _github.fetch_review_threads("test/repo", "7")

    assert [thread.thread_id for thread in threads] == ["T2"]
    assert threads[0].path == "clients/x.ts"
    assert threads[0].line == 42
    assert threads[0].author == "sourcery-ai"
    assert threads[0].body == "Please fix this."
    assert threads[0].outdated is False


def test_fetch_follows_the_page_cursor(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []
    pages = [
        review_threads_payload([review_thread_node(thread_id="T1")], has_next=True, cursor="c1"),
        review_threads_payload([review_thread_node(thread_id="T2")]),
    ]
    monkeypatch.setattr(_github, "run_command", _graphql_pages(pages, calls))

    threads = _github.fetch_review_threads("test/repo", "7")

    assert [thread.thread_id for thread in threads] == ["T1", "T2"]
    assert "cursor=c1" not in " ".join(calls[0])
    assert "cursor=c1" in " ".join(calls[1])


def test_fetch_refuses_a_capped_partial_read(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_github, "REVIEW_THREAD_PAGES_MAX", 1)
    pages = [review_threads_payload([], has_next=True, cursor="c1")]
    monkeypatch.setattr(_github, "run_command", _graphql_pages(pages))

    with pytest.raises(PrError, match="exceed"):
        _ = _github.fetch_review_threads("test/repo", "7")


def test_fetch_raises_on_a_failed_read(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return _completed(cmd, "", 1)

    monkeypatch.setattr(_github, "run_command", fake)

    with pytest.raises(PrError, match="failed to read review threads"):
        _ = _github.fetch_review_threads("test/repo", "7")


# --- the merge gate -------------------------------------------------------------------


def test_merge_refuses_while_a_thread_is_unresolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[list[str]] = []

    def fake(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(list(cmd))
        joined = " ".join(cmd)
        if "graphql" in joined:
            return _completed(cmd, review_threads_payload([review_thread_node()]))
        if "mergeable_state" in joined:
            return _completed(cmd, "clean\n")
        if "api user" in joined:
            return _completed(cmd, "me\n")
        return _completed(cmd, '{"merged":true}')

    monkeypatch.setattr(_github, "run_command", fake)

    with pytest.raises(RefusalError) as exc_info:
        _ = _github.merge_pr(
            "test/repo",
            "7",
            "main",
            "feat: x",
            "## Summary\nReal.\n",
            squash_message_override="feat: x (#7)",
            squash_message_supplied=True,
        )

    assert exc_info.value.refusals[0]["code"] == "reviews_unresolved"
    assert not [call for call in calls if "/merge" in " ".join(call)]


# --- the caller shape -----------------------------------------------------------------


def _options(*, json_output: bool = False) -> PrOptions:
    return PrOptions(reviews=True, json_output=json_output)


def _patch_lookup(monkeypatch: pytest.MonkeyPatch, ref: _github.PrRef | None) -> None:
    def choose_head(head: str | None = None) -> str:
        return "feat-x"

    def choose_repo(head_ref: str | None = None, cwd: Path | None = None) -> str:
        return "test/repo"

    def choose_ref(
        repo: str, head_ref: str, *, state: str = "open", cwd: Path | None = None
    ) -> _github.PrRef | None:
        return ref

    monkeypatch.setattr(_github, "resolve_head", choose_head)
    monkeypatch.setattr(_github, "resolve_repo", choose_repo)
    monkeypatch.setattr(_github, "lookup_pr", choose_ref)


def _patch_threads(monkeypatch: pytest.MonkeyPatch, threads: list[_github.ReviewThread]) -> None:
    def choose_threads(repo: str, num: str, cwd: Path | None = None) -> list[_github.ReviewThread]:
        return threads

    monkeypatch.setattr(_github, "fetch_review_threads", choose_threads)


def test_run_reviews_lists_each_thread_and_exits_one(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    thread = _github.ReviewThread("T1", "clients/x.ts", 42, "sourcery-ai", "Please fix.")
    _patch_lookup(monkeypatch, _github.PrRef("7", "open", False, False))
    _patch_threads(monkeypatch, [thread])

    assert _reviews.run_reviews(_options()) == 1
    out = capsys.readouterr()
    assert "clients/x.ts:42 [sourcery-ai]" in out.out
    assert "Please fix." in out.out
    assert "reviews: 1 unresolved" in out.err


def test_run_reviews_json_when_clean_exits_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_lookup(monkeypatch, _github.PrRef("7", "open", False, False))
    _patch_threads(monkeypatch, [])

    assert _reviews.run_reviews(_options(json_output=True)) == 0
    out = capsys.readouterr()
    assert '"unresolved": []' in out.out
    assert "reviews: 0 unresolved" in out.err


def test_run_reviews_without_a_pr_exits_one(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_lookup(monkeypatch, None)

    assert _reviews.run_reviews(_options()) == 1
    assert "nothing to collect" in capsys.readouterr().err


def test_cli_parses_the_reviews_flag() -> None:
    assert pr_mod.parse_args(["--reviews"]).reviews is True
    assert pr_mod.parse_args([]).reviews is False
