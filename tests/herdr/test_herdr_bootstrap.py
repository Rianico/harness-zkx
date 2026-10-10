"""Tests for skills/herdr/scripts/herdr_bootstrap.py (herdr-bootstrap helper)."""

import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import herdr_bootstrap
import herdr_cli
import pytest

from tests.git_env import git_env
from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness, flag_value

SCRIPT = SCRIPTS_DIR / "herdr_bootstrap.py"


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPT)


def starts(stub: StubHarness) -> list[list[str]]:
    return [call for call in stub.calls() if call[1:3] == ["agent", "start"]]


def pane_renames(stub: StubHarness) -> list[list[str]]:
    return [call for call in stub.calls() if call[1:3] == ["pane", "rename"]]


def pane_runs(stub: StubHarness) -> list[list[str]]:
    return [call for call in stub.calls() if call[1:3] == ["pane", "run"]]


def cwd_state(cwd: Path, pane: str = "w9:p1") -> dict[str, object]:
    """DEFAULT_STATE with one pane already working in `cwd` (no cd needed)."""
    panes = [dict(p, cwd=str(cwd)) if p["pane_id"] == pane else p for p in DEFAULT_STATE["panes"]]
    return {**DEFAULT_STATE, "panes": panes}


def invariant_file(tmp_path: Path) -> Path:
    """The lane-local snippet file the inline kinds are pointed at."""
    return (tmp_path / ".lane" / "role-invariant.md").resolve()


# ── unit: the invariant snippet and the idempotent append ───────────────────────────


def test_snippet_stays_within_the_word_budget() -> None:
    assert len(herdr_bootstrap.render_invariant("Implementer").split()) <= 45


def test_snippet_names_the_role() -> None:
    assert "You are an implementer in a Herdr lane." in herdr_bootstrap.render_invariant(
        "implementer"
    )


def test_append_invariant_creates_a_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "AGENTS.md"
    snippet = herdr_bootstrap.render_invariant("tm")
    assert herdr_bootstrap.append_invariant(path, snippet) is True
    assert path.read_text() == (
        f"{herdr_bootstrap.START_MARKER}\n{snippet}\n{herdr_bootstrap.END_MARKER}\n"
    )


def test_append_invariant_preserves_content_and_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "AGENTS.md"
    _ = path.write_text("# Existing rules\n\nKeep this line.\n")
    snippet = herdr_bootstrap.render_invariant("impl-1")

    assert herdr_bootstrap.append_invariant(path, snippet) is True
    first = path.read_text()
    assert first.startswith("# Existing rules\n\nKeep this line.\n")
    assert snippet in first

    assert herdr_bootstrap.append_invariant(path, snippet) is False
    assert path.read_text() == first
    assert first.count(herdr_bootstrap.START_MARKER) == 1
    assert first.count(herdr_bootstrap.END_MARKER) == 1


# ── integration: naming, delivery mechanism, and dry-run ─────────────────────────────


def test_cli_kind_delivers_the_snippet_through_a_lane_file(
    stub: StubHarness, tmp_path: Path
) -> None:
    """The inline kind receives a file PATH; the file holds the rendered snippet."""
    done = stub.run(
        "--kind",
        "pi",
        "--pane",
        "w9:p1",
        "--role",
        "impl-1",
        "--cwd",
        str(tmp_path),
        state=cwd_state(tmp_path),
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    start = starts(stub)[0]
    after = start[start.index("--") + 1 :]
    path = flag_value(after, "--append-system-prompt")
    assert after == ["--append-system-prompt", path, "--approve"]
    assert not (tmp_path / "AGENTS.md").exists()
    assert f"role-invariant={path}" in done.stdout
    assert pane_runs(stub) == []

    assert Path(path).is_absolute()
    assert Path(path) == invariant_file(tmp_path)
    assert Path(path).read_text() == herdr_bootstrap.render_invariant("impl-1")


def test_inline_snippet_file_rewrite_is_idempotent(stub: StubHarness, tmp_path: Path) -> None:
    """Re-bootstrapping the same lane rewrites the file without duplicating the snippet."""
    args = ("--kind", "pi", "--pane", "w9:p1", "--role", "impl-1", "--cwd", str(tmp_path))
    for _ in range(2):
        done = stub.run(*args, state=cwd_state(tmp_path))
        assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    text = invariant_file(tmp_path).read_text()
    assert text == herdr_bootstrap.render_invariant("impl-1")
    assert text.count("ROLE INVARIANT") == 1


def test_file_kind_appends_agents_md_without_the_inline_flag(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run(
        "--kind",
        "codex",
        "--pane",
        "w9:p1",
        "--role",
        "impl-1",
        "--cwd",
        str(tmp_path),
        state=cwd_state(tmp_path),
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    start = starts(stub)[0]
    assert "--append-system-prompt" not in start
    assert "--" not in start
    written = (tmp_path / "AGENTS.md").read_text()
    assert herdr_bootstrap.render_invariant("impl-1") in written
    assert str(tmp_path / "AGENTS.md") in done.stdout


def test_cline_prefers_an_existing_clinerules_file(stub: StubHarness, tmp_path: Path) -> None:
    rules = tmp_path / ".clinerules"
    _ = rules.write_text("# cline rules\n")

    done = stub.run(
        "--kind",
        "cline",
        "--pane",
        "w9:p1",
        "--role",
        "tm",
        "--cwd",
        str(tmp_path),
        state=cwd_state(tmp_path),
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert herdr_bootstrap.START_MARKER in rules.read_text()
    assert not (tmp_path / "AGENTS.md").exists()


def test_pane_rename_precedes_agent_start(stub: StubHarness, tmp_path: Path) -> None:
    _ = stub.run(
        "--kind",
        "codex",
        "--pane",
        "w9:p2",
        "--role",
        "tm",
        "--task-group",
        "msg",
        "--cwd",
        str(tmp_path),
        state=cwd_state(tmp_path, pane="w9:p2"),
    )
    order = [call[1:3] for call in stub.calls()]
    assert order.index(["pane", "rename"]) < order.index(["agent", "start"])


def test_target_dir_defaults_to_the_pane_cwd(stub: StubHarness, tmp_path: Path) -> None:
    lane = tmp_path / "lane"
    lane.mkdir()
    panes = [dict(DEFAULT_STATE["panes"][0], cwd=str(lane)), DEFAULT_STATE["panes"][1]]
    state = {**DEFAULT_STATE, "panes": panes}

    done = stub.run("--kind", "codex", "--pane", "w9:p1", "--role", "tm", state=state)

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert (lane / "AGENTS.md").exists()


def test_dry_run_prints_the_plan_and_mutates_nothing(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "--kind",
        "codex",
        "--pane",
        "w9:p1",
        "--role",
        "tm",
        "--task-group",
        "msg",
        "--cwd",
        str(tmp_path),
        "--dry-run",
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    plan = json.loads(done.stdout)
    assert plan["agents_md"] == str(tmp_path / "AGENTS.md")
    assert plan["role_invariant"] is None
    assert plan["pane_rename"][1:3] == ["pane", "rename"]
    assert plan["agent_start"][1:5] == ["agent", "start", "msg-tm", "--kind"]
    assert "--append-system-prompt" not in plan["agent_start"]
    assert plan["cwd_ensure"] == str(tmp_path)
    assert stub.calls() == []
    assert not (tmp_path / "AGENTS.md").exists()


def test_dry_run_cli_kind_prints_the_invariant_file_path(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "--kind", "pi", "--pane", "w9:p1", "--role", "tm", "--cwd", str(tmp_path), "--dry-run"
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    plan = json.loads(done.stdout)
    assert plan["agents_md"] is None
    assert plan["role_invariant"] == str(invariant_file(tmp_path))
    start = plan["agent_start"]
    after = start[start.index("--") + 1 :]
    assert after == ["--append-system-prompt", plan["role_invariant"], "--approve"]
    assert plan["cwd_ensure"] == str(tmp_path)
    assert stub.calls() == []
    assert not invariant_file(tmp_path).exists()


def test_dry_run_issues_no_herdr_call_without_cwd(stub: StubHarness) -> None:
    done = stub.run("--kind", "codex", "--pane", "w9:p1", "--role", "tm", "--dry-run")

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.calls() == []


# ── unit: naming scope and validation ───────────────────────────────────────────────


def test_scoped_name_labels_the_pane_and_names_the_agent(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "--kind",
        "codex",
        "--pane",
        "w9:p1",
        "--role",
        "tm",
        "--task-group",
        "msg",
        "--cwd",
        str(tmp_path),
        state=cwd_state(tmp_path),
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert starts(stub)[0][3] == "msg-tm"
    assert pane_renames(stub)[0][3:] == ["w9:p1", "msg-tm"]
    assert "bootstrapped msg-tm (codex) pane=w9:p1" in done.stdout


def test_already_scoped_name_is_unchanged(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "--kind",
        "codex",
        "--pane",
        "w9:p1",
        "--role",
        "msg-tm",
        "--task-group",
        "msg",
        "--cwd",
        str(tmp_path),
        state=cwd_state(tmp_path),
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert starts(stub)[0][3] == "msg-tm"


def test_name_argument_scopes_a_bare_role(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "impl-1",
        "--kind",
        "codex",
        "--pane",
        "w9:p1",
        "--role",
        "impl-1",
        "--task-group",
        "msg",
        "--cwd",
        str(tmp_path),
        state=cwd_state(tmp_path),
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert starts(stub)[0][3] == "msg-impl-1"


@pytest.mark.parametrize("role", ["a" * 40, "Message", "msg impl"])
def test_invalid_name_exits_2_and_starts_nothing(stub: StubHarness, role: str) -> None:
    done = stub.run("--kind", "pi", "--pane", "w9:p1", "--role", role)

    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "not a valid agent name" in done.stderr
    assert stub.calls() == []


def test_missing_name_and_role_is_a_usage_error(stub: StubHarness) -> None:
    done = stub.run("--kind", "pi", "--pane", "w9:p1")

    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "pass NAME or --role" in done.stderr


# ── trust flags: per-kind native args after `--` ────────────────────────────────────


def test_claude_start_carries_its_own_trust_flag(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "--kind",
        "claude",
        "--pane",
        "w9:p1",
        "--role",
        "tm",
        "--cwd",
        str(tmp_path),
        state=cwd_state(tmp_path),
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    start = starts(stub)[0]
    after = start[start.index("--") + 1 :]
    path = flag_value(after, "--append-system-prompt")
    assert after == [
        "--append-system-prompt",
        path,
        "--dangerously-skip-permissions",
    ]
    assert Path(path) == invariant_file(tmp_path)
    assert Path(path).read_text() == herdr_bootstrap.render_invariant("tm")
    assert not (tmp_path / "AGENTS.md").exists()


def test_unknown_kind_falls_back_to_file_without_trust_flags(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run("--kind", "maki", "--pane", "w9:p1", "--role", "tm", state=cwd_state(tmp_path))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    start = starts(stub)[0]
    assert "--append-system-prompt" not in start
    assert "--" not in start
    assert herdr_bootstrap.render_invariant("tm") in (tmp_path / "AGENTS.md").read_text()


# ── agent-level flags: model, snippet, and trust flags all ride after `--` ──────────


def test_inline_kind_puts_the_invariant_path_and_model_after_the_separator(
    stub: StubHarness, tmp_path: Path
) -> None:
    model = "clinepass/cline-pass/deepseek-v4.1-flash"
    done = stub.run(
        "--kind",
        "pi",
        "--pane",
        "w9:p1",
        "--role",
        "impl-1",
        "--model",
        model,
        "--cwd",
        str(tmp_path),
        "--dry-run",
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    start = json.loads(done.stdout)["agent_start"]
    split = start.index("--")
    before = start[:split]
    assert "--model" not in before
    assert "--append-system-prompt" not in before
    assert start[split + 1 :] == [
        "--append-system-prompt",
        str(invariant_file(tmp_path)),
        "--model",
        model,
        "--approve",
    ]
    assert stub.calls() == []


def test_every_agent_arg_after_the_separator_is_single_line(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Regression for the live failure: herdr refuses any agent arg carrying a newline.

    The rendered invariant is multi-line and full of backticks, so passing it as text can
    never work. Fails on the previous inline-the-snippet fix, which looked correct here.
    """
    done = stub.run(
        "--kind",
        "pi",
        "--pane",
        "w9:p1",
        "--role",
        "tm",
        "--model",
        "clinepass/cline-pass/deepseek-v4.1-flash",
        "--cwd",
        str(tmp_path),
        state=cwd_state(tmp_path),
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (start,) = starts(stub)
    after = start[start.index("--") + 1 :]
    assert "--append-system-prompt" in after
    for arg in after:
        assert "\n" not in arg
        assert "\r" not in arg


def test_build_start_argv_rejects_a_multiline_agent_arg() -> None:
    entry = herdr_bootstrap.KindEntry(trust_flags=(), inline_invariant=False)
    with pytest.raises(ValueError, match="single-line"):
        _ = herdr_bootstrap.build_start_argv(
            "herdr",
            herdr_bootstrap.Options(kind="codex", pane="w9:p1", model="a\nb"),
            "msg-tm",
            entry=entry,
        )


def test_inline_kind_without_an_invariant_path_is_refused() -> None:
    entry = herdr_bootstrap.KindEntry(trust_flags=(), inline_invariant=True)
    with pytest.raises(ValueError, match="role-invariant"):
        _ = herdr_bootstrap.build_start_argv(
            "herdr",
            herdr_bootstrap.Options(kind="pi", pane="w9:p1"),
            "msg-tm",
            entry=entry,
        )


def test_file_kind_trust_flags_ride_after_a_single_separator() -> None:
    entry = herdr_bootstrap.KindEntry(trust_flags=("--auto-approve",), inline_invariant=False)
    argv = herdr_bootstrap.build_start_argv(
        "herdr",
        herdr_bootstrap.Options(kind="codex", pane="w9:p1"),
        "msg-tm",
        entry=entry,
    )

    assert argv.count("--") == 1
    assert argv[argv.index("--") + 1 :] == ["--auto-approve"]
    assert "--append-system-prompt" not in argv
    assert "--model" not in argv


def test_kind_with_nothing_to_pass_plans_no_separator(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run(
        "--kind",
        "codex",
        "--pane",
        "w9:p1",
        "--role",
        "tm",
        "--cwd",
        str(tmp_path),
        "--dry-run",
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "--" not in json.loads(done.stdout)["agent_start"]
    assert stub.calls() == []


# ── cwd guarantee: the pane must converge before start ─────────────────────────────


def test_cwd_cd_converges_then_starts(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("--kind", "codex", "--pane", "w9:p1", "--role", "tm", "--cwd", str(tmp_path))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    runs = pane_runs(stub)
    assert len(runs) == 1
    assert runs[0][3:] == ["w9:p1", f"cd {tmp_path}"]
    assert len(starts(stub)) == 1
    assert (tmp_path / "AGENTS.md").exists()


def test_cwd_without_convergence_refuses_before_start(stub: StubHarness) -> None:
    done = stub.run(
        "--kind",
        "codex",
        "--pane",
        "w9:p9",
        "--role",
        "tm",
        "--cwd",
        "/tmp/elsewhere",
        "--cwd-timeout",
        "0",
    )

    assert done.returncode == herdr_cli.EXIT_HERDR, done.stdout
    assert len(pane_runs(stub)) == 1
    assert starts(stub) == []


def test_cwd_cd_failure_refuses_before_start(stub: StubHarness, tmp_path: Path) -> None:
    state = {**DEFAULT_STATE, "pane_run_error": "denied"}
    done = stub.run(
        "--kind",
        "pi",
        "--pane",
        "w9:p1",
        "--role",
        "tm",
        "--cwd",
        str(tmp_path),
        state=state,
    )

    assert done.returncode == herdr_cli.EXIT_HERDR, done.stdout
    assert len(pane_runs(stub)) == 1
    assert starts(stub) == []


# ── unit: kinds.yaml parsing and loading ───────────────────────────────────────────


def test_kinds_config_loads_the_verified_kinds() -> None:
    config = SCRIPTS_DIR.parent / "references" / "kinds.yaml"
    table = herdr_bootstrap.parse_kinds_config(config.read_text())

    assert table["pi"] == herdr_bootstrap.KindEntry(("--approve",), True)
    assert table["claude"] == herdr_bootstrap.KindEntry(("--dangerously-skip-permissions",), True)
    assert table["codex"] == herdr_bootstrap.KindEntry((), False)


def test_load_kind_entry_falls_back_for_unknown_kinds() -> None:
    assert herdr_bootstrap.load_kind_entry("maki") == herdr_bootstrap.FALLBACK_ENTRY


@pytest.mark.parametrize(
    "text",
    [
        "pi:\n  invariant: inline\n",
        "pi:\n  trust_flags: [--approve]\n  invariant: inline\n",
        "pi:\n  trust_flags: []\n  invariant: everywhere\n",
        "pi:\n  trust_flags: []\n  model: x\n  invariant: file\n",
        "pi:\n trust_flags: []\n  invariant: file\n",
    ],
)
def test_kinds_config_rejects_bad_shapes(text: str) -> None:
    with pytest.raises(ValueError):
        herdr_bootstrap.parse_kinds_config(text)


def test_load_kind_entry_missing_file_is_a_usage_error(tmp_path: Path) -> None:
    with pytest.raises(herdr_cli.UsageError):
        herdr_bootstrap.load_kind_entry("pi", config_path=tmp_path / "nope.yaml")


def test_load_kind_entry_bad_file_is_a_usage_error(tmp_path: Path) -> None:
    bad = tmp_path / "kinds.yaml"
    _ = bad.write_text("pi:\n  trust_flags: []\n  invariant: everywhere\n")
    with pytest.raises(herdr_cli.UsageError):
        herdr_bootstrap.load_kind_entry("pi", config_path=bad)


# ── tracked targets: refuse by default, override explicitly ─────────────────────────
#
# The file-reading kinds reach the agent through AGENTS.md, so the append cannot simply move
# elsewhere. Instead bootstrap refuses to dirty a version-controlled target unless the caller
# opts in. These cases build a real repository so "tracked" is git's own answer, not a fake.

GIT_TIMEOUT_S = 60


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run git for the fixture's own plumbing, with the ambient git overrides scrubbed."""
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        env=git_env(),
        capture_output=True,
        text=True,
        check=False,
        timeout=GIT_TIMEOUT_S,
    )


def init_repo(path: Path) -> None:
    """Create a real worktree with a fixture identity, so the tracked case is genuine."""
    path.mkdir(parents=True, exist_ok=True)
    done = git(path, "init", "-q", "-b", "main")
    assert done.returncode == 0, done.stderr
    for key, value in (("user.email", "fixture@example.invalid"), ("user.name", "Fixture")):
        configured = git(path, "config", key, value)
        assert configured.returncode == 0, configured.stderr


def commit_path(repo: Path, *paths: str) -> None:
    _ = git(repo, "add", "--", *paths)
    done = git(repo, "commit", "-q", "-m", "fixture seed")
    assert done.returncode == 0, done.stderr


def repo_status(repo: Path) -> str:
    """The whole worktree's `git status --porcelain` text, as git prints it."""
    done = git(repo, "status", "--porcelain")
    assert done.returncode == 0, done.stderr
    return done.stdout


def repo_status_for(repo: Path, path: str) -> str:
    """The one `git status --porcelain` entry for `path`, or "" when git lists none."""
    done = git(repo, "status", "--porcelain", "--", path)
    assert done.returncode == 0, done.stderr
    return done.stdout


def tracked_repo(tmp_path: Path, body: str = "# Lane rules\n") -> Path:
    """A repo whose `AGENTS.md` is committed with `body`."""
    repo = tmp_path / "repo"
    init_repo(repo)
    _ = (repo / "AGENTS.md").write_text(body)
    commit_path(repo, "AGENTS.md")
    return repo


def bootstrap_args(repo: Path, *extra: str) -> tuple[str, ...]:
    return ("--kind", "codex", "--pane", "w9:p1", "--role", "impl-1", "--cwd", str(repo), *extra)


def no_git_env(stub: StubHarness, tmp_path: Path) -> dict[str, str]:
    """A PATH with the stub `herdr` and an interpreter, but no git.

    The stub `herdr` runs through `#!/usr/bin/env python3`, so the restricted PATH still needs a
    `python3`; it must not carry git, so every tracked probe fails to exec and reads undetermined.
    """
    bin_dir = tmp_path / "no-git-bin"
    bin_dir.mkdir()
    (bin_dir / "python3").symlink_to(sys.executable)
    return {"PATH": f"{stub.bin_dir}:{bin_dir}"}


def volume_is_case_insensitive(directory: Path) -> bool:
    """True when two case-variant spellings name one file on this volume (#229's pattern)."""
    on_disk = directory / "CaseProbe"
    _ = on_disk.write_text("")
    variant = directory / "caseprobe"
    try:
        return variant.exists() and os.path.samefile(on_disk, variant)
    finally:
        on_disk.unlink()


def test_tracked_agents_md_refuses_and_leaves_the_tree_untouched(
    stub: StubHarness, tmp_path: Path
) -> None:
    """RED on base: the launch appended to a committed AGENTS.md and dirtied the tree."""
    repo = tracked_repo(tmp_path)
    agents = repo / "AGENTS.md"
    before = repo_status(repo)
    body_before = agents.read_text()

    done = stub.run(*bootstrap_args(repo), state=cwd_state(repo))

    assert repo_status(repo) == before, (
        f"a launch dirtied the tree: before={before!r} after={repo_status(repo)!r} "
        f"exit={done.returncode} stderr={done.stderr!r}"
    )
    assert done.returncode == herdr_cli.EXIT_USAGE, (
        f"exit={done.returncode} stdout={done.stdout!r} stderr={done.stderr!r}"
    )
    assert str(agents) in done.stderr
    assert "--allow-tracked-invariant" in done.stderr
    assert before == ""
    assert agents.read_text() == body_before
    assert starts(stub) == []
    assert pane_renames(stub) == []


def test_override_appends_to_the_tracked_file_and_dirties_only_that_file(
    stub: StubHarness, tmp_path: Path
) -> None:
    repo = tracked_repo(tmp_path)
    agents = repo / "AGENTS.md"

    done = stub.run(*bootstrap_args(repo, "--allow-tracked-invariant"), state=cwd_state(repo))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert repo_status_for(repo, "AGENTS.md") == " M AGENTS.md\n"
    assert agents.read_text().startswith("# Lane rules\n")
    block = herdr_bootstrap.invariant_block(herdr_bootstrap.render_invariant("impl-1"))
    assert agents.read_text() == f"# Lane rules\n{block}"
    (start,) = starts(stub)
    assert start[1:] == ["agent", "start", "impl-1", "--kind", "codex", "--pane", "w9:p1"]


def test_already_correct_tracked_block_skips_the_write_and_still_launches(
    stub: StubHarness, tmp_path: Path
) -> None:
    block = herdr_bootstrap.invariant_block(herdr_bootstrap.render_invariant("impl-1"))
    repo = tracked_repo(tmp_path, body=block)
    agents = repo / "AGENTS.md"
    before = repo_status(repo)
    stamp = agents.stat().st_mtime_ns

    done = stub.run(*bootstrap_args(repo), state=cwd_state(repo))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert repo_status(repo) == before == ""
    assert agents.read_text() == block
    assert agents.stat().st_mtime_ns == stamp
    assert len(starts(stub)) == 1
    assert pane_renames(stub)[0][3:] == ["w9:p1", "impl-1"]


def test_untracked_agents_md_in_a_repo_is_appended_and_idempotent(
    stub: StubHarness, tmp_path: Path
) -> None:
    repo = tmp_path / "repo"
    init_repo(repo)
    _ = (repo / "seed.txt").write_text("seed\n")
    commit_path(repo, "seed.txt")
    agents = repo / "AGENTS.md"

    first = stub.run(*bootstrap_args(repo), state=cwd_state(repo))
    assert first.returncode == herdr_cli.EXIT_OK, first.stderr
    body = agents.read_text()
    assert herdr_bootstrap.invariant_block(herdr_bootstrap.render_invariant("impl-1")) in body
    assert repo_status_for(repo, "AGENTS.md") == "?? AGENTS.md\n"

    second = stub.run(*bootstrap_args(repo), state=cwd_state(repo))
    assert second.returncode == herdr_cli.EXIT_OK, second.stderr
    assert agents.read_text() == body
    assert body.count(herdr_bootstrap.START_MARKER) == 1
    assert repo_status_for(repo, "AGENTS.md") == "?? AGENTS.md\n"


def test_agents_md_outside_any_repo_is_appended(stub: StubHarness, tmp_path: Path) -> None:
    """Nothing in a non-repo reports the lane-local file: `git status` cannot answer there."""
    lane = tmp_path / "lane"
    lane.mkdir()
    assert git(lane, "rev-parse", "--is-inside-work-tree").returncode != 0

    done = stub.run(*bootstrap_args(lane), state=cwd_state(lane))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert herdr_bootstrap.START_MARKER in (lane / "AGENTS.md").read_text()
    assert git(lane, "status", "--porcelain").returncode != 0


def test_dry_run_reports_the_tracked_verdict_without_writing(
    stub: StubHarness, tmp_path: Path
) -> None:
    repo = tracked_repo(tmp_path)
    agents = repo / "AGENTS.md"

    done = stub.run(*bootstrap_args(repo, "--dry-run"))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    plan = json.loads(done.stdout)
    assert plan["agents_md"] == str(agents)
    assert plan["agents_md_tracked"] is True
    assert str(agents) in plan["would_refuse"]
    assert "--allow-tracked-invariant" in plan["would_refuse"]
    assert stub.calls() == []
    assert agents.read_text() == "# Lane rules\n"
    assert repo_status(repo) == ""


def test_dry_run_reports_the_tracked_verdict_with_the_override(
    stub: StubHarness, tmp_path: Path
) -> None:
    repo = tracked_repo(tmp_path)

    done = stub.run(*bootstrap_args(repo, "--allow-tracked-invariant", "--dry-run"))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    plan = json.loads(done.stdout)
    assert plan["agents_md_tracked"] is True
    assert "would_refuse" not in plan
    assert stub.calls() == []


def test_dry_run_reports_an_untracked_target_without_a_refusal(
    stub: StubHarness, tmp_path: Path
) -> None:
    lane = tmp_path / "lane"
    lane.mkdir()

    done = stub.run(*bootstrap_args(lane, "--dry-run"))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    plan = json.loads(done.stdout)
    assert plan["agents_md_tracked"] is False
    assert "would_refuse" not in plan
    assert stub.calls() == []


def test_dry_run_needs_no_git_verdict_for_an_inline_kind(stub: StubHarness, tmp_path: Path) -> None:
    """The inline kinds write no target file, so the tracked question does not arise."""
    done = stub.run(
        "--kind", "pi", "--pane", "w9:p1", "--role", "tm", "--cwd", str(tmp_path), "--dry-run"
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    plan = json.loads(done.stdout)
    assert plan["agents_md"] is None
    assert "agents_md_tracked" not in plan
    assert "would_refuse" not in plan


def test_tracked_detection_falls_back_to_untracked_without_a_git_binary(
    tmp_path: Path,
) -> None:
    """Detection that cannot run reads as undetermined, not as tracked; the append still happens.

    Updated from `is False` to `is None`: the probe is now tri-state (H1), so a host with no
    usable git is *undetermined* — the caller appends and warns — rather than silently "not
    version-controlled".
    """
    repo = tracked_repo(tmp_path)

    assert herdr_bootstrap.target_is_tracked(repo / "AGENTS.md", {"PATH": str(tmp_path)}) is None


def test_invariant_block_matches_what_append_invariant_writes(tmp_path: Path) -> None:
    path = tmp_path / "AGENTS.md"
    snippet = herdr_bootstrap.render_invariant("tm")

    assert herdr_bootstrap.append_invariant(path, snippet) is True

    assert path.read_text() == herdr_bootstrap.invariant_block(snippet)


def test_a_target_that_cannot_be_read_is_a_usage_error(stub: StubHarness, tmp_path: Path) -> None:
    """The new read must not escape as a traceback: a directory named AGENTS.md exits 2."""
    lane = tmp_path / "lane"
    (lane / "AGENTS.md").mkdir(parents=True)

    for extra in (("--dry-run",), ()):
        done = stub.run(*bootstrap_args(lane, *extra))

        assert done.returncode == herdr_cli.EXIT_USAGE, f"{extra}: {done.stdout!r} {done.stderr!r}"
        assert "cannot read" in done.stderr
        assert stub.calls() == []


# ── B1: the probe must ask git about the on-disk entry name ─────────────────────────


def test_tracked_lowercase_name_on_a_case_insensitive_volume_is_refused(
    stub: StubHarness, tmp_path: Path
) -> None:
    """B1 RED on base: a repo tracking `agents.md`, targeted as `AGENTS.md`, was appended to.

    On a case-insensitive volume the two spellings are one inode, but `git ls-files` matches its
    pathspec against the stored name, so the base probe answered "untracked" and dirtied the tree.
    """
    repo = tmp_path / "repo"
    init_repo(repo)
    if not volume_is_case_insensitive(repo):
        pytest.skip("case-sensitive volume")
    _ = (repo / "agents.md").write_text("# lowercase tracked\n")
    commit_path(repo, "agents.md")
    agents = repo / "AGENTS.md"
    before = repo_status(repo)
    body_before = (repo / "agents.md").read_text()

    done = stub.run(*bootstrap_args(repo), state=cwd_state(repo))

    assert repo_status(repo) == before == "", (
        f"the case-variant target was appended to: {repo_status(repo)!r} exit={done.returncode}"
    )
    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert str(agents) in done.stderr
    assert "--allow-tracked-invariant" in done.stderr
    assert (repo / "agents.md").read_text() == body_before
    assert starts(stub) == []


# ── H1: the tracked probe is tri-state; the fail-open is never silent ───────────────


def test_undetermined_without_git_appends_with_one_warning_line(
    stub: StubHarness, tmp_path: Path
) -> None:
    """H1(a) RED on base: no git on PATH appended silently; now one stderr line says so."""
    repo = tracked_repo(tmp_path)

    done = stub.run(*bootstrap_args(repo), state=cwd_state(repo), env=no_git_env(stub, tmp_path))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    lines = done.stderr.splitlines()
    assert len(lines) == 1, done.stderr
    assert "could not determine" in lines[0]
    assert str(repo / "AGENTS.md") in lines[0]
    assert repo_status_for(repo, "AGENTS.md") == " M AGENTS.md\n"
    assert len(starts(stub)) == 1


def test_dry_run_reports_an_undetermined_target_with_a_note(
    stub: StubHarness, tmp_path: Path
) -> None:
    """H1(a): without git the plan is `null` with a note and no stderr warning; nothing is written."""
    repo = tracked_repo(tmp_path)

    done = stub.run(*bootstrap_args(repo, "--dry-run"), env=no_git_env(stub, tmp_path))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    plan = json.loads(done.stdout)
    assert plan["agents_md_tracked"] is None
    assert "could not determine" in plan["note"]
    assert str(repo / "AGENTS.md") in plan["note"]
    assert "would_refuse" not in plan
    assert done.stderr == ""
    assert repo_status(repo) == ""
    assert stub.calls() == []


def test_confirmed_repo_with_an_unreadable_index_is_refused(
    stub: StubHarness, tmp_path: Path
) -> None:
    """H1(b) RED on base: git confirmed the repo but the index was unreadable, and it appended."""
    repo = tracked_repo(tmp_path)
    bad_index = tmp_path / "corrupt-index"
    _ = bad_index.write_bytes(b"not a git index")
    before = repo_status(repo)

    done = stub.run(
        *bootstrap_args(repo), state=cwd_state(repo), env={"GIT_INDEX_FILE": str(bad_index)}
    )

    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert str(repo / "AGENTS.md") in done.stderr
    assert "--allow-tracked-invariant" in done.stderr
    assert repo_status(repo) == before == ""
    assert starts(stub) == []


def test_dry_run_reports_an_unreadable_index_as_undetermined_and_would_refuse(
    stub: StubHarness, tmp_path: Path
) -> None:
    """H1(b): the confirmed-but-unreadable index is `null` with a refusal and writes nothing."""
    repo = tracked_repo(tmp_path)
    bad_index = tmp_path / "corrupt-index"
    _ = bad_index.write_bytes(b"not a git index")

    done = stub.run(*bootstrap_args(repo, "--dry-run"), env={"GIT_INDEX_FILE": str(bad_index)})

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    plan = json.loads(done.stdout)
    assert plan["agents_md_tracked"] is None
    assert "--allow-tracked-invariant" in plan["would_refuse"]
    assert "could not determine" in plan["note"]
    assert done.stderr == ""
    assert repo_status(repo) == ""
    assert stub.calls() == []


def test_genuinely_untracked_appends_without_a_warning(stub: StubHarness, tmp_path: Path) -> None:
    """H1(c): git answered "not tracked", so the append happens with no warning line."""
    repo = tmp_path / "repo"
    init_repo(repo)
    _ = (repo / "seed.txt").write_text("seed\n")
    commit_path(repo, "seed.txt")

    done = stub.run(*bootstrap_args(repo), state=cwd_state(repo))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stderr == ""
    assert herdr_bootstrap.START_MARKER in (repo / "AGENTS.md").read_text()


# ── L1: a worktree root with trailing whitespace ────────────────────────────────────


def test_worktree_root_with_a_trailing_space_is_still_recognized(
    stub: StubHarness, tmp_path: Path
) -> None:
    """L1 RED on base: `.strip()` dropped the trailing space, so a tracked file was appended to."""
    repo = tmp_path / "repo "
    init_repo(repo)
    _ = (repo / "AGENTS.md").write_text("# spaced root\n")
    commit_path(repo, "AGENTS.md")
    agents = repo / "AGENTS.md"
    before = repo_status(repo)
    body_before = agents.read_text()

    done = stub.run(*bootstrap_args(repo), state=cwd_state(repo))

    assert repo_status(repo) == before == "", (
        f"a spaced root dirtied the tree: {repo_status(repo)!r} exit={done.returncode}"
    )
    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert str(agents) in done.stderr
    assert agents.read_text() == body_before
    assert starts(stub) == []


# ── L2: the skip path is not role-checked, and the docs say so ──────────────────────


def test_tracked_block_for_another_role_is_delivered_unchanged(
    stub: StubHarness, tmp_path: Path
) -> None:
    """L2: a committed `tm` block launched as `impl-1` is delivered unchanged, not rewritten."""
    tm_block = herdr_bootstrap.invariant_block(herdr_bootstrap.render_invariant("tm"))
    repo = tracked_repo(tmp_path, body=tm_block)
    agents = repo / "AGENTS.md"
    before = repo_status(repo)
    stamp = agents.stat().st_mtime_ns

    done = stub.run(*bootstrap_args(repo), state=cwd_state(repo))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert repo_status(repo) == before == ""
    assert agents.read_text() == tm_block
    assert "You are an tm in a Herdr lane." in agents.read_text()
    assert herdr_bootstrap.render_invariant("impl-1") not in agents.read_text()
    assert agents.stat().st_mtime_ns == stamp
    assert len(starts(stub)) == 1
    assert pane_renames(stub)[0][3:] == ["w9:p1", "impl-1"]
