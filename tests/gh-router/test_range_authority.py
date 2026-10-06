"""Oracle matrix for the range authority (synthetic repos only, no network)."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LIB_DIR = REPO_ROOT / "skills" / "gh-router" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from range_authority import MalformedSpec, RangeRefusal, exit_code_for, resolve_range

COMMIT_ENV = {"GIT_CONFIG_NOSYSTEM": "1"}


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _init_repo(repo: Path) -> str:
    _ = _git(repo, "init")
    _ = _git(repo, "config", "user.name", "Tester Author")
    _ = _git(repo, "config", "user.email", "tester@example.com")
    _ = _git(repo, "config", "commit.gpgsign", "false")
    _ = (repo / "common.txt").write_text("base line\n", encoding="utf-8")
    _ = _git(repo, "add", ".")
    _ = _git(repo, "commit", "-m", "chore: base commit")
    return _git(repo, "rev-parse", "--abbrev-ref", "HEAD")


def _commit(repo: Path, name: str, content: str, message: str) -> str:
    _ = (repo / name).write_text(content, encoding="utf-8")
    _ = _git(repo, "add", ".")
    _ = _git(repo, "commit", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _resolve(repo: Path, monkeypatch: pytest.MonkeyPatch, spec: str, mode: str):  # type: ignore[no-untyped-def]
    monkeypatch.chdir(repo)
    return resolve_range(spec, mode)


def test_linear_two_dot_range(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = _init_repo(tmp_path)
    _ = _git(tmp_path, "checkout", "-b", "feature")
    first = _commit(tmp_path, "f1.txt", "one\n", "feat: one")
    second = _commit(tmp_path, "f2.txt", "two\n", "feat: two")

    resolution = _resolve(tmp_path, monkeypatch, f"{base}..feature", "..")

    assert resolution.mode == ".."
    assert resolution.resolved_from == "explicit"
    assert list(resolution.commits) == [first, second]
    assert list(resolution.only_in_base) == []
    assert (resolution.counts.commits, resolution.counts.only_in_base) == (2, 0)


def test_diverged_three_dot_reports_both_sides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = _init_repo(tmp_path)
    fork_point = _git(tmp_path, "rev-parse", "HEAD")
    _ = _git(tmp_path, "checkout", "-b", "feature")
    _ = _commit(tmp_path, "f1.txt", "one\n", "feat: one")
    head_tip = _commit(tmp_path, "f2.txt", "two\n", "feat: two")
    _ = _git(tmp_path, "checkout", base)
    base_tip = _commit(tmp_path, "b1.txt", "base\n", "fix: base work")

    resolution = _resolve(tmp_path, monkeypatch, f"{base}...feature", "...")

    assert resolution.merge_base == fork_point
    assert resolution.head_ref == "feature"
    assert head_tip in resolution.commits
    assert list(resolution.only_in_base) == [base_tip]
    assert resolution.counts.only_in_base == 1


def test_two_dot_uses_base_as_given(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = _init_repo(tmp_path)
    _ = _git(tmp_path, "checkout", "-b", "feature")
    _ = _commit(tmp_path, "f1.txt", "one\n", "feat: one")
    _ = _git(tmp_path, "checkout", base)
    _ = _commit(tmp_path, "b1.txt", "base\n", "fix: base work")

    resolution = _resolve(tmp_path, monkeypatch, f"{base}..feature", "..")

    assert resolution.mode == ".."
    assert resolution.base_ref == base
    assert len(resolution.commits) == 1
    assert len(resolution.only_in_base) == 1


def test_rebased_feature_has_empty_base_side(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = _init_repo(tmp_path)
    _ = _commit(tmp_path, "b1.txt", "base\n", "fix: base work")
    base_tip = _git(tmp_path, "rev-parse", "HEAD")
    _ = _git(tmp_path, "checkout", "-b", "feature", "HEAD~1")
    _ = _commit(tmp_path, "f1.txt", "one\n", "feat: one")
    _ = _git(tmp_path, "rebase", base)

    resolution = _resolve(tmp_path, monkeypatch, f"{base}..feature", "..")

    assert resolution.merge_base == base_tip
    assert len(resolution.commits) == 1
    assert list(resolution.only_in_base) == []


def test_root_commit_is_merge_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = _init_repo(tmp_path)
    root = _git(tmp_path, "rev-parse", "HEAD")
    _ = _git(tmp_path, "checkout", "-b", "feature")
    _ = _commit(tmp_path, "f1.txt", "one\n", "feat: one")
    _ = _git(tmp_path, "checkout", base)
    _ = _commit(tmp_path, "b1.txt", "base\n", "fix: base work")

    resolution = _resolve(tmp_path, monkeypatch, f"{base}...feature", "...")

    assert resolution.merge_base == root
    assert len(resolution.commits) == 1
    assert len(resolution.only_in_base) == 1


def test_merge_commit_included(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = _init_repo(tmp_path)
    _ = _git(tmp_path, "checkout", "-b", "feature")
    _ = _commit(tmp_path, "f1.txt", "one\n", "feat: one")
    _ = _git(tmp_path, "merge", "--no-ff", base, "-m", "merge: take base")
    merge_sha = _git(tmp_path, "rev-parse", "HEAD")

    resolution = _resolve(tmp_path, monkeypatch, f"{base}..feature", "..")

    assert merge_sha in resolution.commits
    assert list(resolution.commits)[-1] == merge_sha


def test_sha_only_pair_matches_branch_form(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = _init_repo(tmp_path)
    base_sha = _git(tmp_path, "rev-parse", "HEAD")
    _ = _git(tmp_path, "checkout", "-b", "feature")
    _ = _commit(tmp_path, "f1.txt", "one\n", "feat: one")
    head_sha = _git(tmp_path, "rev-parse", "HEAD")

    via_branches = _resolve(tmp_path, monkeypatch, f"{base}..feature", "..")
    via_dots = _resolve(tmp_path, monkeypatch, f"{base_sha}..{head_sha}", "..")
    via_space = _resolve(tmp_path, monkeypatch, f"{base_sha} {head_sha}", "..")

    assert list(via_dots.commits) == list(via_branches.commits)
    assert list(via_space.commits) == list(via_branches.commits)
    assert via_space.resolved_from == "explicit"


def test_single_ref_resolves_origin_main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = _init_repo(tmp_path)
    base_tip = _git(tmp_path, "rev-parse", "HEAD")
    _ = _git(tmp_path, "checkout", "-b", "feature")
    _ = _commit(tmp_path, "f1.txt", "one\n", "feat: one")
    _ = _git(tmp_path, "update-ref", "refs/remotes/origin/main", base_tip)

    resolution = _resolve(tmp_path, monkeypatch, "feature", "...")

    assert resolution.resolved_from == "origin/main"
    assert len(resolution.commits) == 1
    assert list(resolution.only_in_base) == []


def test_single_ref_prefers_origin_head(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = _init_repo(tmp_path)
    base_tip = _git(tmp_path, "rev-parse", "HEAD")
    _ = _git(tmp_path, "checkout", "-b", "feature")
    _ = _commit(tmp_path, "f1.txt", "one\n", "feat: one")
    _ = _git(tmp_path, "update-ref", "refs/remotes/origin/main", base_tip)
    _ = _git(tmp_path, "update-ref", "refs/remotes/origin/master", base_tip)
    _ = _git(
        tmp_path,
        "symbolic-ref",
        "refs/remotes/origin/HEAD",
        "refs/remotes/origin/main",
    )

    resolution = _resolve(tmp_path, monkeypatch, "feature", "...")

    assert resolution.resolved_from == "origin/HEAD"


def test_unknown_ref_is_refusal_exit3(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RangeRefusal):
        _ = resolve_range("does-not-exist..HEAD", "..")
    try:
        _ = resolve_range("does-not-exist..HEAD", "..")
    except RangeRefusal as error:
        assert exit_code_for(error) == 3


def test_unknown_base_is_refusal_exit3(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RangeRefusal, match="unknown base"):
        _ = resolve_range("HEAD", "...")


def test_non_repo_is_refusal_exit3(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RangeRefusal):
        _ = resolve_range("main..feature", "..")
    try:
        _ = resolve_range("main..feature", "..")
    except RangeRefusal as error:
        assert exit_code_for(error) == 3


def test_head_behind_base_reports_only_in_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = _init_repo(tmp_path)
    _ = _git(tmp_path, "checkout", "-b", "feature")
    _ = _git(tmp_path, "checkout", base)
    ahead = _commit(tmp_path, "b1.txt", "base\n", "fix: base work")

    resolution = _resolve(tmp_path, monkeypatch, f"{base}..feature", "..")

    assert list(resolution.commits) == []
    assert list(resolution.only_in_base) == [ahead]


def test_identical_tips_resolve_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = _init_repo(tmp_path)

    resolution = _resolve(tmp_path, monkeypatch, f"{base}..{base}", "..")

    assert list(resolution.commits) == []
    assert list(resolution.only_in_base) == []
    assert resolution.merge_base == _git(tmp_path, "rev-parse", "HEAD")


@pytest.mark.parametrize(
    "spec",
    ["", "..", "...", "a..b..c", "a...b...c", "..HEAD", "HEAD..", "...HEAD", "a b c"],
)
def test_malformed_specs_exit2(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, spec: str) -> None:
    _ = _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(MalformedSpec):
        _ = resolve_range(spec, "..")
    try:
        _ = resolve_range(spec, "..")
    except MalformedSpec as error:
        assert exit_code_for(error) == 2


def test_triple_colon_is_single_ref_refusal_exit3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _ = _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(RangeRefusal):
        _ = resolve_range(":::", "..")
    try:
        _ = resolve_range(":::", "..")
    except RangeRefusal as error:
        assert exit_code_for(error) == 3


def test_bogus_mode_is_malformed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _ = _init_repo(tmp_path)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(MalformedSpec):
        _ = resolve_range("HEAD", "bogus")


def test_exit_code_for_unknown_error_is_one() -> None:
    assert exit_code_for(RuntimeError("boom")) == 1


def test_resolution_is_immutable_and_json_ready(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    base = _init_repo(tmp_path)
    _ = _git(tmp_path, "checkout", "-b", "feature")
    _ = _commit(tmp_path, "f1.txt", "one\n", "feat: one")

    resolution = _resolve(tmp_path, monkeypatch, f"{base}..feature", "..")
    payload = resolution.to_dict()

    assert json.loads(json.dumps(payload)) == payload
    assert payload["counts"] == {"commits": 1, "only_in_base": 0}
    with pytest.raises(FrozenInstanceError):
        resolution.mode = "..."  # type: ignore[misc]
