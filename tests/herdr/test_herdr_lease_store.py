"""One lease store per lane — resolution, provisioning export, and mismatch reporting (#229).

These cases drive the helpers' observable contract only: argv in, then exit code, store
contents, and stdout/stderr out. The regression case is behavioural on purpose — it seats
the store through the dispatcher's working directory and releases through a callee's other
one, so it refutes the pre-#229 `PWD` authority rather than any private function.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
from collections.abc import Callable
from pathlib import Path

import herdr_cli
import herdr_lease
import herdr_worktree
import pytest
import yaml

from tests.herdr.stub import SCRIPTS_DIR, STUB_SOURCE, StubHarness, flag_value

DISPATCH = SCRIPTS_DIR / "herdr_dispatch.py"
REPLY = SCRIPTS_DIR / "herdr_reply.py"
PANE = SCRIPTS_DIR / "herdr_pane.py"
# The published anchor name, spelled out: the regression case must collect against the
# pre-#229 tree too, so it cannot import a constant that tree never defined.
LANE_DIR_ENV = "HERDR_LANE_DIR"
STORE = Path(".lane") / "tasks.yaml"


@pytest.fixture
def lane(tmp_path: Path) -> Callable[[Path], StubHarness]:
    """One stub `herdr` for the lane, one argv log per helper (dispatch/reply/pane)."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    herdr = bin_dir / "herdr"
    _ = herdr.write_text(STUB_SOURCE)
    herdr.chmod(herdr.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    def make(script: Path) -> StubHarness:
        return StubHarness(
            script,
            tmp_path,
            bin_dir,
            tmp_path / f"{script.stem}.jsonl",
            tmp_path / "state.json",
        )

    return make


def git(*args: str) -> None:
    """Run git in the test's own environment; a failure is a test failure."""
    _ = subprocess.run(["git", *args], check=True, capture_output=True, text=True)


def make_git_repo(base: Path, name: str = "repo") -> Path:
    """A real, empty repository; its root is what the git-common-dir fallback resolves to."""
    repo = base / name
    repo.mkdir()
    git("init", "-q", str(repo))
    return Path(os.path.realpath(repo))


def ticket_file(tmp_path: Path, name: str = "ticket.md") -> Path:
    path = tmp_path / name
    _ = path.write_text("TICKET BODY", encoding="utf-8")
    return path


# ── red-then-green regression: one lane, two working directories ─────────────────────


def test_release_from_another_working_directory_lands_in_the_shared_store(
    lane: Callable[[Path], StubHarness], tmp_path: Path
) -> None:
    """A caller in directory A and a callee in directory B of one lane share one store.

    Pre-#229 the store came from `PWD`: dispatch seated `A/.lane/tasks.yaml`, the reply
    looked in `B`, released nothing, and the next dispatch to that callee was refused.
    """
    dispatch = lane(DISPATCH)
    reply = lane(REPLY)
    repo = make_git_repo(tmp_path)
    dir_a = repo / "dir-a"
    dir_b = repo / "dir-b"
    dir_a.mkdir()
    dir_b.mkdir()
    ticket = ticket_file(tmp_path)

    caller_env = {LANE_DIR_ENV: None, "PWD": str(dir_a)}
    callee_env = {LANE_DIR_ENV: None, "PWD": str(dir_b)}

    first = dispatch.run("reviewer", "--file", str(ticket), "--no-wait", env=caller_env, cwd=repo)
    assert first.returncode == herdr_cli.EXIT_OK, first.stderr

    # The store the dispatcher wrote is the one both sides resolve.
    assert (repo / STORE).is_file()
    assert herdr_lease.get_lease("reviewer", base_dir=repo) is not None

    delivered = reply.run("orchestrator", "COMPLETED", env=callee_env, cwd=repo)
    assert delivered.returncode == herdr_cli.EXIT_OK, delivered.stderr

    # The release is recorded: the shared store no longer holds the lease.
    assert herdr_lease.get_lease("reviewer", base_dir=repo) is None

    # ...so the next dispatch to that callee is accepted without --force.
    second = dispatch.run("reviewer", "--file", str(ticket), "--no-wait", env=caller_env, cwd=repo)
    assert second.returncode == herdr_cli.EXIT_OK, second.stderr


# ── a missing anchor aborts loudly and writes nothing ────────────────────────────────


def test_dispatch_without_any_anchor_aborts_and_writes_no_store(
    lane: Callable[[Path], StubHarness], tmp_path: Path
) -> None:
    dispatch = lane(DISPATCH)
    bare = tmp_path / "no-repo"
    bare.mkdir()
    ticket = ticket_file(tmp_path)

    done = dispatch.run(
        "reviewer",
        "--file",
        str(ticket),
        "--no-wait",
        env={LANE_DIR_ENV: None, "PWD": str(bare)},
        cwd=bare,
    )

    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "no lane state anchor" in done.stderr
    assert LANE_DIR_ENV in done.stderr
    assert "git common dir" in done.stderr
    assert not (bare / ".lane").exists()
    assert not (bare / ".herdr-lease.json").exists()
    assert dispatch.prompts() == []


# ── provisioning exports the anchor into the pane it creates ─────────────────────────


def test_split_pane_exports_the_resolved_anchor_in_plan_and_argv(
    lane: Callable[[Path], StubHarness], tmp_path: Path
) -> None:
    pane = lane(PANE)
    repo = make_git_repo(tmp_path)
    env = {LANE_DIR_ENV: None, "PWD": str(repo)}
    expected = f"{LANE_DIR_ENV}={repo}"

    planned = pane.run("vertical", "--dry-run", env=env, cwd=repo)
    assert planned.returncode == herdr_cli.EXIT_OK, planned.stderr
    assert f"--env {expected}" in planned.stdout
    assert pane.splits() == []

    live = pane.run("vertical", env=env, cwd=repo)
    assert live.returncode == herdr_cli.EXIT_OK, live.stderr
    (call,) = pane.splits()
    assert call.count("--env") == 1
    assert flag_value(call, "--env") == expected


def test_split_pane_reexports_the_anchor_the_caller_already_holds(
    lane: Callable[[Path], StubHarness], tmp_path: Path
) -> None:
    """N3: a pane is launched by the herdr server, so the caller's env is not inherited.

    The anchor is therefore always written into the argv; only an explicit
    `--env HERDR_LANE_DIR=...` on this invocation (which would emit the key twice) skips it.
    """
    pane = lane(PANE)
    pinned = tmp_path / "pinned-lane"

    from_env = pane.run("vertical", env={LANE_DIR_ENV: str(pinned)})
    assert from_env.returncode == herdr_cli.EXIT_OK, from_env.stderr

    from_flag = pane.run("vertical", "--env", f"{LANE_DIR_ENV}=/pinned", env={LANE_DIR_ENV: None})
    assert from_flag.returncode == herdr_cli.EXIT_OK, from_flag.stderr

    env_call, flag_call = pane.splits()
    assert env_call.count("--env") == 1
    assert flag_value(env_call, "--env") == f"{LANE_DIR_ENV}={pinned}"
    assert flag_call.count("--env") == 1
    assert flag_value(flag_call, "--env") == f"{LANE_DIR_ENV}=/pinned"


# ── the lease records its store; a cross-store release reports instead of moving ─────


def test_cross_store_release_reports_the_mismatch_and_releases_nothing(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    store_a = tmp_path / "store-a"
    store_b = tmp_path / "store-b"
    _ = herdr_lease.acquire_lease("reviewer", "t.md", "orch", base_dir=store_a)
    written = (store_a / STORE).read_bytes()
    (store_b / ".lane").mkdir(parents=True)
    _ = (store_b / STORE).write_bytes(written)

    # A reported no-op, never a fabricated success and never a relocated write.
    assert herdr_lease.release_lease("reviewer", base_dir=store_b) is False

    captured = capsys.readouterr()
    assert str(store_a) in captured.err
    assert str(store_b) in captured.err
    assert "refusing to relocate the write" in captured.err
    assert (store_a / STORE).read_bytes() == written
    assert (store_b / STORE).read_bytes() == written
    assert herdr_lease.get_lease("reviewer", base_dir=store_b) is not None


def test_legacy_lease_without_a_recorded_store_still_releases(tmp_path: Path) -> None:
    lane_dir = tmp_path / "lane"
    (lane_dir / ".lane").mkdir(parents=True)
    _ = (lane_dir / ".lane" / "lease.json").write_text(
        json.dumps({"reviewer": {"ticket": "t.md", "caller": "orch"}}), encoding="utf-8"
    )

    assert herdr_lease.release_lease("reviewer", base_dir=lane_dir) is True
    assert herdr_lease.get_lease("reviewer", base_dir=lane_dir) is None


# ── the same-store edge is unchanged ─────────────────────────────────────────────────


def test_one_working_directory_still_acquires_replies_and_reaccepts(
    lane: Callable[[Path], StubHarness], tmp_path: Path
) -> None:
    dispatch = lane(DISPATCH)
    reply = lane(REPLY)
    lane_dir = tmp_path / "lane"
    env = {LANE_DIR_ENV: str(lane_dir)}
    ticket = ticket_file(tmp_path)

    first = dispatch.run("reviewer", "--file", str(ticket), "--no-wait", env=env)
    assert first.returncode == herdr_cli.EXIT_OK, first.stderr
    assert (lane_dir / STORE).is_file()
    assert herdr_lease.get_lease("reviewer", base_dir=lane_dir) is not None

    delivered = reply.run("orchestrator", "COMPLETED", env=env)
    assert delivered.returncode == herdr_cli.EXIT_OK, delivered.stderr
    assert herdr_lease.get_lease("reviewer", base_dir=lane_dir) is None

    second = dispatch.run("reviewer", "--file", str(ticket), "--no-wait", env=env)
    assert second.returncode == herdr_cli.EXIT_OK, second.stderr


# ── resolution layering is a property of the store, not of a working directory ───────


def test_resolve_base_dir_layers_explicit_then_anchor(tmp_path: Path) -> None:
    pinned = tmp_path / "pinned"

    assert herdr_lease.resolve_base_dir(tmp_path, env={LANE_DIR_ENV: str(pinned)}) == tmp_path
    assert herdr_lease.resolve_base_dir(env={LANE_DIR_ENV: str(pinned)}) == pinned


def test_resolve_base_dir_ignores_pwd_for_the_git_common_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_git_repo(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(repo)
    env = {"PATH": os.environ["PATH"], "PWD": str(elsewhere)}

    resolved = herdr_lease.resolve_base_dir(env=env)

    assert resolved == herdr_worktree.git_repo_root({"PATH": os.environ["PATH"]})
    assert resolved == repo
    assert resolved != elsewhere


def test_repo_root_and_a_nested_subdirectory_resolve_to_one_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = make_git_repo(tmp_path)
    nested = repo / "deep" / "nested"
    nested.mkdir(parents=True)
    env = {"PATH": os.environ["PATH"]}

    monkeypatch.chdir(repo)
    at_root = herdr_lease.resolve_base_dir(env=env)
    monkeypatch.chdir(nested)
    below = herdr_lease.resolve_base_dir(env=env)

    assert at_root == below == repo


# ── B2: store identity is physical, not textual ──────────────────────────────────────


@pytest.mark.parametrize("acquire_via_alias", [True, False])
def test_release_across_two_spellings_of_one_physical_store(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, acquire_via_alias: bool
) -> None:
    """B2: a symlinked anchor and its realpath are one store, so the release must land.

    Comparing spellings refused it, leaked the lease, and made the next dispatch demand
    `--force` — the exact outage #229 exists to remove.
    """
    real = tmp_path / "real-store"
    real.mkdir()
    alias = tmp_path / "alias-store"
    alias.symlink_to(real, target_is_directory=True)
    assert os.path.samefile(alias, real)

    _ = herdr_lease.acquire_lease(
        "reviewer", "t.md", "orch", base_dir=alias if acquire_via_alias else real
    )

    released = herdr_lease.release_lease("reviewer", base_dir=real if acquire_via_alias else alias)

    assert released is True
    assert "refusing" not in capsys.readouterr().err
    assert herdr_lease.get_lease("reviewer", base_dir=real) is None


def test_recorded_store_is_matched_by_physical_identity(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """A record written under another spelling of the same directory still releases.

    Records are canonical when written now; this pins that the *comparison* is physical too,
    so a store written by an older helper or another tool is not falsely refused.
    """
    real = tmp_path / "real-store"
    real.mkdir()
    alias = tmp_path / "alias-store"
    alias.symlink_to(real, target_is_directory=True)
    (real / ".lane").mkdir()
    _ = (real / STORE).write_text(
        yaml.safe_dump(
            {
                "active_leases": {
                    "reviewer": {
                        "target": "reviewer",
                        "ticket": "t.md",
                        "caller": "orch",
                        "store": str(alias),
                    }
                },
                "tasks": {},
            }
        ),
        encoding="utf-8",
    )

    assert herdr_lease.release_lease("reviewer", base_dir=real) is True

    assert "refusing" not in capsys.readouterr().err
    assert herdr_lease.get_lease("reviewer", base_dir=real) is None


# ── N1: the mismatch diagnostic's exact reach ────────────────────────────────────────


def test_release_from_a_store_that_never_saw_the_lease_is_a_silent_no_op(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """The documented limit: a lease in a store this process never resolves is invisible.

    Nothing is comparable, so the release is an honest no-op — `False`, no diagnostic, no
    write into the store the lease names.
    """
    caller_store = tmp_path / "caller-store"
    callee_store = tmp_path / "callee-store"
    _ = herdr_lease.acquire_lease("reviewer", "t.md", "orch", base_dir=caller_store)
    assert herdr_lease.get_lease("reviewer", base_dir=callee_store) is None

    assert herdr_lease.release_lease("reviewer", base_dir=callee_store) is False

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""
    assert herdr_lease.get_lease("reviewer", base_dir=caller_store) is not None


# ── N2: the repo root is not always outside a git directory ──────────────────────────


def test_separate_git_dir_store_is_the_git_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`resolve_lane_base_dir` returns the common dir itself when it is not named `.git`."""
    repo = tmp_path / "separate"
    repo.mkdir()
    git_dir = tmp_path / "separate-gitdir"
    git("init", "-q", f"--separate-git-dir={git_dir}", str(repo))
    monkeypatch.chdir(repo)

    resolved = herdr_worktree.resolve_lane_base_dir({"PATH": os.environ["PATH"]})

    assert resolved == Path(os.path.realpath(git_dir))
    assert resolved != repo


def test_submodule_store_is_its_common_dir_under_the_superproject(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A submodule's base is `<super>/.git/modules/<name>` — inside a git directory.

    Documented, not preferred: it is still one path for every worktree of that submodule.
    """
    origin = make_git_repo(tmp_path, "origin")
    _ = (origin / "f.txt").write_text("x", encoding="utf-8")
    git("-C", str(origin), "add", "-A")
    git(
        "-C",
        str(origin),
        "-c",
        "user.email=t@example.com",
        "-c",
        "user.name=t",
        "commit",
        "-qm",
        "init",
    )
    superproject = tmp_path / "super"
    superproject.mkdir()
    git("init", "-q", str(superproject))
    git(
        "-c",
        "protocol.file.allow=always",
        "-C",
        str(superproject),
        "submodule",
        "add",
        "-q",
        str(origin),
        "mods",
    )
    monkeypatch.chdir(superproject / "mods")

    resolved = herdr_worktree.resolve_lane_base_dir({"PATH": os.environ["PATH"]})

    assert resolved == Path(os.path.realpath(superproject / ".git" / "modules" / "mods"))
