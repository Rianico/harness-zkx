"""Tests for skills/herdr/scripts/herdr_bootstrap.py (herdr-bootstrap helper)."""

import contextlib
import io
import json
import os
import re
import stat
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import override

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


def invariant_file(tmp_path: Path, agent: str) -> Path:
    """The per-agent lane-local snippet file the inline kinds are pointed at."""
    return (tmp_path / ".lane" / "invariants" / f"{agent}.md").resolve()


# ── unit: the invariant snippet and the idempotent append ───────────────────────────


def test_snippet_stays_within_the_word_budget() -> None:
    """The implementer ceiling is deliberate: the cooperation contract raised it from 45."""
    assert len(herdr_bootstrap.render_invariant("Implementer").split()) <= 80


def test_coordination_snippet_stays_within_the_55_word_budget() -> None:
    """A role outside both block vocabularies pays for neither: the cap stays 55."""
    for role in ("reviewer", "msg-reviewer"):
        assert len(herdr_bootstrap.render_invariant(role).split()) <= 55


def test_tm_named_roles_carry_the_task_manager_contract() -> None:
    """#260: bare and scoped TM vocabulary appends the Task Manager contract."""
    for role in (
        "tm",
        "msg-tm",
        "lane-orch",
        "task-manager",
        "task_manager",
        "herdr228-task-manager",
        "orchestrator",
        "sr-coord",
        "coordinator",
        "gaps-orch-2",
    ):
        assert herdr_bootstrap.is_tm_role(role) is True, role
        text = herdr_bootstrap.render_invariant(role)
        assert "NEVER edit source or test code directly" in text, role
        assert "single writer for your task" not in text, role


def test_tm_contract_is_appended_verbatim_and_within_its_budget() -> None:
    text = herdr_bootstrap.render_invariant("tm")
    assert text.endswith(herdr_bootstrap.TM_CONTRACT)
    assert len(text.split()) == 51 + len(herdr_bootstrap.TM_CONTRACT.split())


def test_tm_match_is_segment_exact_not_prefix() -> None:
    """`tmux`/`orchid`/`coordination` hold a TM term only as a prefix — no contract for them."""
    for role in ("tmux", "orchid", "coordination", "impl-1", "reviewer"):
        assert herdr_bootstrap.is_tm_role(role) is False, role


def test_scoped_implementer_names_carry_the_cooperation_contract() -> None:
    """The lane convention is `<slug>-<role>[-<n>]`; `herdr228-impl-1` is an implementer."""
    for role in ("impl-1", "herdr228-impl-1", "msg-impl-1", "herdr228_impl_1"):
        assert herdr_bootstrap.is_implementer_role(role) is True, role
        assert "single writer for your task" in herdr_bootstrap.render_invariant(role), role


def test_coordination_names_omit_the_implementer_block() -> None:
    """`tm`/`task-manager` never match the implementer vocabulary, scoped or bare."""
    for role in ("tm", "msg-tm", "task-manager", "herdr228-task-manager"):
        assert herdr_bootstrap.is_implementer_role(role) is False, role
        assert "single writer for your task" not in herdr_bootstrap.render_invariant(role), role
    # Accepted over-match, stated in `is_implementer_role`'s docstring: a lane slug segment
    # that itself begins with `impl` drags its coordination role into the block.
    assert herdr_bootstrap.is_implementer_role("impl-hardening-tm") is True


def test_a_scoped_implementer_reviewer_still_fits_the_80_word_cap() -> None:
    """The widest newly matching role must stay inside the implementer ceiling."""
    text = herdr_bootstrap.render_invariant("msg-impl-reviewer")
    assert "single writer for your task" in text
    assert len(text.split()) <= 80


def test_implementer_contract_does_not_restate_the_reply_contract() -> None:
    """The shared Reply Contract already owes the reply; the block must not repeat it."""
    text = herdr_bootstrap.render_invariant("impl-1")
    assert "Blockers: report immediately, never idle." in text
    assert "reply via the reply contract" not in text
    assert len(text.split()) <= 80


def test_snippet_names_the_role() -> None:
    assert "You are an implementer in a Herdr lane." in herdr_bootstrap.render_invariant(
        "implementer"
    )


def test_snippet_article_follows_the_roles_first_letter() -> None:
    """`a`/`an` comes from the role's first letter, so the header reads as prose."""
    assert "You are an implementer in a Herdr lane." in herdr_bootstrap.render_invariant(
        "implementer"
    )
    assert "You are an impl-1 in a Herdr lane." in herdr_bootstrap.render_invariant("impl-1")
    assert "You are a tm in a Herdr lane." in herdr_bootstrap.render_invariant("tm")
    assert "You are an tm" not in herdr_bootstrap.render_invariant("tm")


def test_snippet_states_the_lane_coordination_pattern() -> None:
    for role in ("tm", "impl-1"):
        assert "Follow the lane coordination pattern." in herdr_bootstrap.render_invariant(role)


def test_snippet_replies_through_the_lanes_own_helper() -> None:
    """Absolute and lane-local: the reply runs from any cwd, never an older symlinked tree."""
    helper = herdr_bootstrap.REPLY_HELPER
    assert helper.is_absolute()
    assert helper.name == "herdr_reply.py"
    assert helper.exists()

    text = herdr_bootstrap.render_invariant("impl-1")
    assert f"`uv run {helper} <caller> --file <reply.md>`" in text
    assert "~/.agents" not in text


def test_snippet_reply_command_path_is_absolute() -> None:
    """A shell outside the lane spawns the rendered command only when its path is absolute."""
    for role in ("tm", "impl-1"):
        command = re.search(r"`uv run (\S+) <caller>", herdr_bootstrap.render_invariant(role))
        assert command is not None, role
        assert command.group(1).startswith("/"), role
        assert Path(command.group(1)).name == "herdr_reply.py", role


def test_invariant_file_name_is_sanitised_and_cannot_escape(tmp_path: Path) -> None:
    path = herdr_bootstrap.lane_invariant_path(str(tmp_path), "Msg/Tm 1")
    assert path == (tmp_path / ".lane" / "invariants" / "Msg_Tm_1.md").resolve()
    with pytest.raises(herdr_cli.UsageError):
        _ = herdr_bootstrap.lane_invariant_path(str(tmp_path), "..")
    with pytest.raises(herdr_cli.UsageError):
        _ = herdr_bootstrap.lane_invariant_path(str(tmp_path), "")


def test_implementer_injected_text_carries_the_cooperation_contract(
    stub: StubHarness, tmp_path: Path
) -> None:
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

    text = invariant_file(tmp_path, "impl-1").read_text()
    for clause in (
        "single writer for your task",
        "never edit outside your worktree",
        "red-then-green test results",
        "artifacts reported by path",
        "report immediately, never idle",
    ):
        assert clause in text
    assert "reply via the reply contract" not in text


def test_coordination_role_injected_text_omits_the_implementer_block(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run(
        "--kind",
        "pi",
        "--pane",
        "w9:p1",
        "--role",
        "tm",
        "--cwd",
        str(tmp_path),
        state=cwd_state(tmp_path),
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    text = invariant_file(tmp_path, "tm").read_text()
    for clause in (
        "single writer for your task",
        "never edit outside your worktree",
        "red-then-green",
        "artifacts reported by path",
        "reply via the reply contract",
    ):
        assert clause not in text


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
    assert Path(path) == invariant_file(tmp_path, "impl-1")
    assert Path(path).read_text() == herdr_bootstrap.render_invariant("impl-1")


def test_inline_snippet_file_rewrite_is_idempotent(stub: StubHarness, tmp_path: Path) -> None:
    """Re-bootstrapping the same lane rewrites the file without duplicating the snippet."""
    args = ("--kind", "pi", "--pane", "w9:p1", "--role", "impl-1", "--cwd", str(tmp_path))
    for _ in range(2):
        done = stub.run(*args, state=cwd_state(tmp_path))
        assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    text = invariant_file(tmp_path, "impl-1").read_text()
    assert text == herdr_bootstrap.render_invariant("impl-1")
    assert text.count("ROLE INVARIANT") == 1


def test_invariant_file_is_per_agent_and_isolated(stub: StubHarness, tmp_path: Path) -> None:
    """Two agents in one lane each inject their own file; the second never touches the first.

    RED on the single shared `.lane/role-invariant.md`: the second bootstrap overwrote the
    first agent's text, so an inline agent read another role's invariant after compaction.
    """
    lane = tmp_path / "lane"
    lane.mkdir()
    state = cwd_state(lane)
    args = ("--kind", "pi", "--pane", "w9:p1", "--cwd", str(lane))

    first = stub.run("--role", "impl-1", *args, state=state)
    assert first.returncode == herdr_cli.EXIT_OK, first.stderr
    impl_path = (lane / ".lane" / "invariants" / "impl-1.md").resolve()
    impl_text = impl_path.read_text()
    impl_stamp = impl_path.stat().st_mtime_ns

    second = stub.run("--role", "tm", *args, state=state)
    assert second.returncode == herdr_cli.EXIT_OK, second.stderr
    tm_path = (lane / ".lane" / "invariants" / "tm.md").resolve()
    tm_text = tm_path.read_text()
    tm_stamp = tm_path.stat().st_mtime_ns
    # The second agent's launch wrote its own file and left the first agent's byte-identical.
    assert impl_path.stat().st_mtime_ns == impl_stamp
    assert impl_path.read_text() == impl_text

    third = stub.run("--role", "impl-1", *args, state=state)
    assert third.returncode == herdr_cli.EXIT_OK, third.stderr
    # Re-bootstrapping the first agent rewrites only its own file.
    assert tm_path.stat().st_mtime_ns == tm_stamp
    assert tm_path.read_text() == tm_text

    assert impl_path != tm_path
    assert impl_text == herdr_bootstrap.render_invariant("impl-1")
    assert tm_text == herdr_bootstrap.render_invariant("tm")
    injected = [
        flag_value(start[start.index("--") + 1 :], "--append-system-prompt")
        for start in starts(stub)
    ]
    assert injected == [str(impl_path), str(tm_path), str(impl_path)]


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
    assert plan["role_invariant"] == str(invariant_file(tmp_path, "tm"))
    start = plan["agent_start"]
    after = start[start.index("--") + 1 :]
    assert after == ["--append-system-prompt", plan["role_invariant"], "--approve"]
    assert plan["cwd_ensure"] == str(tmp_path)
    assert stub.calls() == []
    assert not invariant_file(tmp_path, "tm").exists()


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
    path = flag_value(after, "--append-system-prompt-file")
    assert after == [
        "--append-system-prompt-file",
        path,
        "--dangerously-skip-permissions",
    ]
    assert Path(path) == invariant_file(tmp_path, "tm")
    assert Path(path).read_text() == herdr_bootstrap.render_invariant("tm")
    assert not (tmp_path / "AGENTS.md").exists()


@pytest.mark.parametrize(
    ("kind", "flag"),
    [
        ("pi", "--append-system-prompt"),
        ("claude", "--append-system-prompt-file"),
    ],
)
def test_each_inline_kind_passes_the_snippet_file_through_its_own_flag(
    stub: StubHarness, tmp_path: Path, kind: str, flag: str
) -> None:
    """Per-kind flag pin (#240): the invariant file rides through the flag the kind reads.

    `pi` reads file contents through `--append-system-prompt`; `claude` treats that flag's
    value as literal text and reads a path only through `--append-system-prompt-file`, so a
    claude launch carrying the path under the text flag boots with the path string as its
    system prompt. The suite could not distinguish the two, which is why the defect shipped.

    Mutant killed: route claude through `--append-system-prompt` again — the claude case
    fails naming the literal-path defect. Mutant killed: drop `invariant_flag` from
    kinds.yaml — the config parser refuses the inline kind without its flag.
    """
    done = stub.run(
        "--kind",
        kind,
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
    path = flag_value(after, flag)
    assert Path(path) == invariant_file(tmp_path, "tm")
    assert Path(path).read_text() == herdr_bootstrap.render_invariant("tm")
    other = (
        "--append-system-prompt-file"
        if flag == "--append-system-prompt"
        else "--append-system-prompt"
    )
    assert other not in after


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
        str(invariant_file(tmp_path, "impl-1")),
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


def test_inline_kind_without_its_flag_is_refused() -> None:
    """An inline entry naming no flag is refused even when the file path is present (#240).

    Mutant killed: default the flag to `--append-system-prompt` inside `build_start_argv`
    — this passes and the claude launch silently returns to the literal-path defect.
    """
    entry = herdr_bootstrap.KindEntry(trust_flags=(), inline_invariant=True)
    with pytest.raises(ValueError, match="invariant_flag"):
        _ = herdr_bootstrap.build_start_argv(
            "herdr",
            herdr_bootstrap.Options(kind="pi", pane="w9:p1"),
            "msg-tm",
            entry=entry,
            invariant_path="/tmp/lane/.lane/invariants/tm.md",
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

    assert table["pi"] == herdr_bootstrap.KindEntry(("--approve",), True, "--append-system-prompt")
    assert table["claude"] == herdr_bootstrap.KindEntry(
        ("--dangerously-skip-permissions",), True, "--append-system-prompt-file"
    )
    assert table["qodercli"] == herdr_bootstrap.KindEntry(
        ("--dangerously-skip-permissions",), False, None
    )
    assert table["codex"] == herdr_bootstrap.KindEntry((), False)
    # `lifecycle_bridge` is the kind's own bridge, named by the revision-static remedy (#238).
    assert table["agy"] == herdr_bootstrap.KindEntry((), False, None, False, "herdr-agy-bridge")
    assert table["pi"].lifecycle_bridge is None


def test_load_kind_entry_falls_back_for_unknown_kinds() -> None:
    assert herdr_bootstrap.load_kind_entry("maki") == herdr_bootstrap.FALLBACK_ENTRY


@pytest.mark.parametrize(
    "text",
    [
        "pi:\n  invariant: inline\n",
        "pi:\n  trust_flags: [--approve]\n  invariant: inline\n",
        "pi:\n  trust_flags: []\n  invariant: file\n  invariant_flag: --append-system-prompt\n",
        "pi:\n  trust_flags: []\n  invariant: inline\n  invariant_flag: not-a-flag\n",
        "pi:\n  trust_flags: []\n  invariant: inline\n  invariant_flag: --a --b\n",
        "pi:\n  trust_flags: []\n  invariant: everywhere\n",
        "pi:\n  trust_flags: []\n  model: x\n  invariant: file\n",
        "pi:\n trust_flags: []\n  invariant: file\n",
        "pi:\n  trust_flags: []\n  invariant: file\n  lifecycle_bridge: two words\n",
        "pi:\n  trust_flags: []\n  invariant: file\n  lifecycle_bridge:\n",
    ],
)
def test_kinds_config_rejects_bad_shapes(text: str) -> None:
    with pytest.raises(ValueError):
        herdr_bootstrap.parse_kinds_config(text)


# ── unit: `lifecycle_bridge` is a bare script name, not free text (#241) ────────────
#
# The value is echoed to the operator inside the revision-0 advice, so a malformed one is
# rendered as though it were a real script name. One row per refusal class: quote characters,
# path separators, shell metacharacters, whitespace, empty, and the two path segments (`.`,
# `..`) that are not names. The `+@~%=` and non-ASCII rows pin the charset BREADTH, not just one
# row per class: a widened `BARE_SCRIPT_NAME_PATTERN` that accepts any of them fails here.
NON_BARE_BRIDGES = (
    '"herdr-x"',
    "'herdr-x'",
    "../x",
    "/bin/sh",
    "x/y",
    "herdr-x;id",
    "$(id)",
    "`id`",
    "herdr-x|id",
    "herdr-x>out",
    "herdr-x&id",
    "herdr-x y",
    "herdr-x@2",
    "herdr-x~1",
    "herdr-x%2",
    "herdr-x+1",
    "herdr-x:2",
    "h\u00e9rder-x",
    "",
    ".",
    "..",
)

# The accepted side of the same rule: one path segment of `[A-Za-z0-9._-]`. A dotted name stays
# legal — a bridge script may carry a `.sh` suffix (`herdr_agy_bridge.BRIDGE_SCRIPT_NAME`).
BARE_BRIDGES = ("herdr-x", "herdr-agy-bridge.sh", "x_1", "x-", "x.", ".hidden", "-x")


def _bridge_config(value: str) -> str:
    """One kind table whose only interesting field is `lifecycle_bridge: <value>`."""
    return f"pi:\n  trust_flags: []\n  invariant: file\n  lifecycle_bridge: {value}\n"


@pytest.mark.parametrize("value", NON_BARE_BRIDGES)
def test_kinds_config_refuses_a_non_bare_lifecycle_bridge(value: str) -> None:
    """A quote, separator, metacharacter, whitespace, empty value, `.` or `..` is refused."""
    with pytest.raises(ValueError, match="bare script name"):
        herdr_bootstrap.parse_kinds_config(_bridge_config(value))


@pytest.mark.parametrize("value", BARE_BRIDGES)
def test_kinds_config_stores_a_bare_lifecycle_bridge(value: str) -> None:
    """A bare script name is stored verbatim, so the tightened rule stays minimal."""
    table = herdr_bootstrap.parse_kinds_config(_bridge_config(value))

    assert table["pi"].lifecycle_bridge == value


def test_kinds_config_real_file_bridge_names_are_bare_script_names() -> None:
    """The shipped kinds.yaml must keep loading: the rule accepts the real `agy` bridge."""
    config = SCRIPTS_DIR.parent / "references" / "kinds.yaml"
    table = herdr_bootstrap.parse_kinds_config(config.read_text())

    assert table["agy"].lifecycle_bridge == "herdr-agy-bridge"
    assert herdr_bootstrap.load_kind_entry("agy").lifecycle_bridge == "herdr-agy-bridge"


def test_bare_script_name_pattern_refuses_every_excluded_character() -> None:
    """The bare-name pattern is pinned by breadth: every character outside `[A-Za-z0-9._-]`.

    One refusal row per metacharacter class does not pin the charset's breadth, so a mutant that
    widens `BARE_SCRIPT_NAME_PATTERN` to `[A-Za-z0-9._+@~%=-]+` left every row green (measured at
    3b5e078b: PIN-BROKEN count 0). Asserting the pattern directly against one member of each
    excluded class kills that mutant without widening the production charset, whose strictness is a
    usability choice (the value only reaches operator advice text, never a path or command).
    """
    for value in ("x@y", "x~y", "x%y", "x+y", "x=y", "x:y", "x\u00e9"):
        assert re.fullmatch(herdr_bootstrap.BARE_SCRIPT_NAME_PATTERN, value) is None, (
            f"{value!r} must not match the bare script name charset"
        )


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


def test_tracked_detection_is_undetermined_without_a_git_binary(
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


def test_casefold_entry_is_taken_only_for_the_same_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """W4 RED on a case-sensitive host: the fold must name the same file, not a case-variant twin.

    `agents.md` exists and `AGENTS.md` does not. On a case-insensitive volume the two spellings
    are one inode, so the fold is right; on a case-sensitive volume they are different files, so
    the fold would ask git about a path the launch never touches. Assert the iff, which holds on
    both volume types without needing a case-sensitive filesystem.
    """
    directory = tmp_path / "lane"
    directory.mkdir()
    candidate = directory / "agents.md"
    _ = candidate.write_text("# lowercase\n")
    target = directory / "AGENTS.md"
    try:
        same_file = os.path.samefile(target, candidate)
    except OSError:
        same_file = False

    assert herdr_bootstrap.on_disk_entry_name(target) == ("agents.md" if same_file else None)

    # Pinning the guard on the volume this test runs on: on a case-insensitive volume the fold
    # above is satisfied by the unfixed implementation too, so the `samefile` guard is only
    # observable when the OS boundary cannot prove the two spellings are one file.
    def unprovable(*_args: object, **_kwargs: object) -> bool:
        raise FileNotFoundError(2, "No such file or directory")

    monkeypatch.setattr(os.path, "samefile", unprovable)

    assert herdr_bootstrap.on_disk_entry_name(target) is None


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


def test_override_appends_through_an_unreadable_index(stub: StubHarness, tmp_path: Path) -> None:
    """W1 RED on cd1f0eb7: the undetermined refusal ignored `--allow-tracked-invariant`.

    The refusal's own sentence tells the operator to pass the flag; before this fix the flag did
    nothing on the undetermined branch, so a confirmed repo whose index git could not read was a
    permanent dead end for the invariant. The override must append and launch, like the tracked
    branch.
    """
    repo = tracked_repo(tmp_path)
    bad_index = tmp_path / "corrupt-index"
    _ = bad_index.write_bytes(b"not a git index")
    agents = repo / "AGENTS.md"
    body_before = agents.read_text()

    done = stub.run(
        *bootstrap_args(repo, "--allow-tracked-invariant"),
        state=cwd_state(repo),
        env={"GIT_INDEX_FILE": str(bad_index)},
    )

    assert done.returncode == herdr_cli.EXIT_OK, (done.stdout, done.stderr)
    assert agents.read_text() != body_before
    assert herdr_bootstrap.START_MARKER in agents.read_text()
    assert repo_status_for(repo, "AGENTS.md") == " M AGENTS.md\n"
    assert len(starts(stub)) == 1


def test_dubious_ownership_is_undetermined_and_refused(stub: StubHarness, tmp_path: Path) -> None:
    """W2 RED on cd1f0eb7: a failed `rev-parse --is-inside-work-tree` read as a definitive "not tracked".

    git refusing to answer (a foreign-owned checkout) is not an answer that the file is untracked,
    and the `.git` entry git refused over says the target may well be tracked, so the launch
    refuses with a clean tree instead of appending and dirtying a version-controlled file.
    """
    repo = tracked_repo(tmp_path)
    before = repo_status(repo)
    owned_by_stranger = {"GIT_TEST_ASSUME_DIFFERENT_OWNER": "1"}

    done = stub.run(*bootstrap_args(repo), state=cwd_state(repo), env=owned_by_stranger)

    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert str(repo / "AGENTS.md") in done.stderr
    assert "--allow-tracked-invariant" in done.stderr
    assert repo_status(repo) == before == ""
    assert starts(stub) == []

    override = stub.run(
        *bootstrap_args(repo, "--allow-tracked-invariant"),
        state=cwd_state(repo),
        env=owned_by_stranger,
    )

    assert override.returncode == herdr_cli.EXIT_OK, override.stderr
    assert herdr_bootstrap.START_MARKER in (repo / "AGENTS.md").read_text()
    assert repo_status(repo) == " M AGENTS.md\n"
    assert len(starts(stub)) == 1


def test_a_git_dir_that_does_not_exist_is_undetermined_and_refused(
    stub: StubHarness, tmp_path: Path
) -> None:
    """W2 RED on cd1f0eb7: `GIT_DIR` at a missing path made git answer "not tracked" silently.

    The stale override cannot be trusted either way, and the repo's own `.git` still sits above
    the target, so the launch refuses with a clean tree instead of appending to a tracked file.
    """
    repo = tracked_repo(tmp_path)
    before = repo_status(repo)
    stale_override = {"GIT_DIR": str(tmp_path / "no-such-repo" / ".git")}

    done = stub.run(*bootstrap_args(repo), state=cwd_state(repo), env=stale_override)

    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert str(repo / "AGENTS.md") in done.stderr
    assert "--allow-tracked-invariant" in done.stderr
    assert repo_status(repo) == before == ""
    assert starts(stub) == []

    override = stub.run(
        *bootstrap_args(repo, "--allow-tracked-invariant"),
        state=cwd_state(repo),
        env=stale_override,
    )

    assert override.returncode == herdr_cli.EXIT_OK, override.stderr
    assert herdr_bootstrap.START_MARKER in (repo / "AGENTS.md").read_text()
    assert repo_status(repo) == " M AGENTS.md\n"
    assert len(starts(stub)) == 1


def test_an_unreadable_git_dir_is_undetermined_and_refused(
    stub: StubHarness, tmp_path: Path
) -> None:
    """W2 RED on cd1f0eb7: an unreadable `.git` printed "not a git repository" and appended silently.

    That message cannot tell an unreadable `.git` from a genuinely absent one; the presence of a
    `.git` entry does, so the state is undetermined — and the target may be tracked, so it is
    refused with a clean tree.
    """
    if os.geteuid() == 0:
        pytest.skip("root bypasses directory permissions")
    repo = tracked_repo(tmp_path)
    dotgit = repo / ".git"
    original = stat.S_IMODE(dotgit.stat().st_mode)
    os.chmod(dotgit, 0o000)
    try:
        done = stub.run(*bootstrap_args(repo), state=cwd_state(repo))
    finally:
        os.chmod(dotgit, original)

    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert str(repo / "AGENTS.md") in done.stderr
    assert "--allow-tracked-invariant" in done.stderr
    assert repo_status(repo) == ""
    assert starts(stub) == []

    os.chmod(dotgit, 0o000)
    try:
        override = stub.run(
            *bootstrap_args(repo, "--allow-tracked-invariant"), state=cwd_state(repo)
        )
    finally:
        os.chmod(dotgit, original)

    assert override.returncode == herdr_cli.EXIT_OK, override.stderr
    assert herdr_bootstrap.START_MARKER in (repo / "AGENTS.md").read_text()
    assert repo_status(repo) == " M AGENTS.md\n"
    assert len(starts(stub)) == 1


def test_a_missing_index_file_is_undetermined_not_untracked(
    stub: StubHarness, tmp_path: Path
) -> None:
    """W3 RED on cd1f0eb7: a missing `GIT_INDEX_FILE` made git answer from an empty index."""
    repo = tracked_repo(tmp_path)
    before = repo_status(repo)

    done = stub.run(
        *bootstrap_args(repo),
        state=cwd_state(repo),
        env={"GIT_INDEX_FILE": str(tmp_path / "no-such-index")},
    )

    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert str(repo / "AGENTS.md") in done.stderr
    assert "--allow-tracked-invariant" in done.stderr
    assert repo_status(repo) == before == ""
    assert starts(stub) == []


def test_a_git_dir_pointing_at_the_targets_own_repo_is_refused(
    stub: StubHarness, tmp_path: Path
) -> None:
    """W3: a deliberate same-repo `GIT_DIR` is refused by default — fail closed, and overridable.

    A wrapper or hook exporting `GIT_DIR` for the target's own repository could be answered
    correctly, but the variable outranks `-C`, so the probe answers about the override rather than
    about the file's own repository and the tracked state is undetermined. Bootstrap refuses
    rather than trust it; `--allow-tracked-invariant` appends and launches anyway.
    """
    repo = tracked_repo(tmp_path)
    before = repo_status(repo)
    deliberate_override = {"GIT_DIR": str(repo / ".git")}

    done = stub.run(*bootstrap_args(repo), state=cwd_state(repo), env=deliberate_override)

    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert str(repo / "AGENTS.md") in done.stderr
    assert "--allow-tracked-invariant" in done.stderr
    assert repo_status(repo) == before == ""
    assert starts(stub) == []

    override = stub.run(
        *bootstrap_args(repo, "--allow-tracked-invariant"),
        state=cwd_state(repo),
        env=deliberate_override,
    )

    assert override.returncode == herdr_cli.EXIT_OK, override.stderr
    assert herdr_bootstrap.START_MARKER in (repo / "AGENTS.md").read_text()
    assert repo_status(repo) == " M AGENTS.md\n"
    assert len(starts(stub)) == 1


def test_a_foreign_git_dir_is_undetermined_not_untracked(stub: StubHarness, tmp_path: Path) -> None:
    """W3 RED on cd1f0eb7: a foreign `GIT_DIR` read that repo's index and answered "untracked"."""
    repo = tracked_repo(tmp_path)
    other = tmp_path / "other"
    init_repo(other)
    _ = (other / "seed.txt").write_text("seed\n")
    commit_path(other, "seed.txt")
    before = repo_status(repo)

    done = stub.run(
        *bootstrap_args(repo),
        state=cwd_state(repo),
        env={"GIT_DIR": str(other / ".git")},
    )

    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert str(repo / "AGENTS.md") in done.stderr
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


@pytest.mark.parametrize("dirname", ["repo\n", "repo ", "repo\r", "repo\t", " repo"])
def test_worktree_root_whitespace_does_not_break_tracked_detection(
    stub: StubHarness, tmp_path: Path, dirname: str
) -> None:
    """W6 RED on base: a root whose name ends in a newline read as undetermined, not tracked.

    `rev-parse --show-toplevel` prints the root plus its own newline, so a name that already ends
    in one arrives as `name\\n\\n`; stripping every newline hid the real separator and broke
    `relative_to`. Trailing space, trailing CR, tab and leading space must keep working.
    """
    repo = tmp_path / dirname
    init_repo(repo)
    _ = (repo / "AGENTS.md").write_text("# named root\n")
    commit_path(repo, "AGENTS.md")

    done = stub.run(*bootstrap_args(repo, "--dry-run"))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert json.loads(done.stdout)["agents_md_tracked"] is True


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
    assert "You are a tm in a Herdr lane." in agents.read_text()
    assert herdr_bootstrap.render_invariant("impl-1") not in agents.read_text()
    assert agents.stat().st_mtime_ns == stamp
    assert len(starts(stub)) == 1
    assert pane_renames(stub)[0][3:] == ["w9:p1", "impl-1"]


# ── #238: settle a freshly spawned pane before treating it as acceptant ─────────────


class _ReportStream(io.StringIO):
    """stdout that records the moment bootstrap reports success, for ordering assertions."""

    def __init__(self, events: list[object]) -> None:
        super().__init__()
        self._events = events

    @override
    def write(self, text: str) -> int:
        if "bootstrapped" in text:
            self._events.append("report")
        return super().write(text)


def _record_start_and_settle(monkeypatch: pytest.MonkeyPatch, events: list[object]) -> None:
    """Record `agent start` and the settle into one ordered event list (in-process bootstrap)."""

    def fake_sleep(seconds: float) -> None:
        events.append(("settle", seconds))

    monkeypatch.setattr(herdr_bootstrap, "_sleep", fake_sleep)
    real = herdr_bootstrap.run_herdr_checked

    def recording(argv: list[str], env: object) -> str:
        if list(argv)[1:3] == ["agent", "start"]:
            events.append("start")
        return real(argv, env)

    monkeypatch.setattr(herdr_bootstrap, "run_herdr_checked", recording)


def test_settle_runs_after_agent_start_and_before_the_success_report(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pin 1 (#238): a fresh pane settles after `agent start`, before it is reported ready.

    Mutant killed: move `settle_fresh_pane(...)` above `run_herdr_checked(start_argv, env)` —
    the recorded order becomes settle, start, report and this test fails.
    """
    events: list[object] = []
    _record_start_and_settle(monkeypatch, events)
    options = herdr_bootstrap.Options(kind="codex", pane="w9:p1", role="tm", cwd=str(tmp_path))
    stream = _ReportStream(events)

    with contextlib.redirect_stdout(stream):
        code = herdr_bootstrap.bootstrap(options, stub.base_env())

    assert code == herdr_cli.EXIT_OK
    assert events == ["start", ("settle", herdr_bootstrap.DEFAULT_SETTLE_SECONDS), "report"], (
        "the settle must sit between the spawn and the success report"
    )


def test_settle_zero_is_exact_and_the_default_settles_once(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pin 2 (#238): `--settle 0` sleeps not at all; the default is one 5s wait.

    Mutant killed: drop the `seconds <= 0` guard in `settle_fresh_pane` — `--settle 0` then
    records a `0.0` sleep and the `slept == []` assertion fails.
    """
    slept: list[float] = []
    monkeypatch.setattr(herdr_bootstrap, "_sleep", slept.append)
    zero = herdr_bootstrap.Options(
        kind="codex", pane="w9:p1", role="tm", cwd=str(tmp_path), settle=0.0
    )
    assert herdr_bootstrap.bootstrap(zero, stub.base_env()) == herdr_cli.EXIT_OK
    assert slept == [], "--settle 0 must not sleep at all, not even a token sleep"

    parser = herdr_bootstrap.build_parser()
    assert parser.parse_args(["--kind", "codex", "--pane", "w9:p1"]).settle == 5.0
    assert parser.parse_args(["--kind", "codex", "--pane", "w9:p1", "--settle", "0"]).settle == 0.0

    default = herdr_bootstrap.Options(kind="codex", pane="w9:p1", role="tm", cwd=str(tmp_path))
    assert herdr_bootstrap.bootstrap(default, stub.base_env()) == herdr_cli.EXIT_OK
    assert slept == [herdr_bootstrap.DEFAULT_SETTLE_SECONDS]


def test_bootstrap_refuses_a_negative_settle(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F3 (#238): a negative `--settle` is refused; `0` stays valid and exact.

    RED on base: `--settle -5` exits 0 and spawns the agent — the `seconds <= 0` guard silently
    reads a deliberately invalid wait as "no wait".
    Mutant killed: drop the `settle < 0` refusal — the run spawns and exits 0.
    """
    slept: list[float] = []
    monkeypatch.setattr(herdr_bootstrap, "_sleep", slept.append)

    done = stub.run(*bootstrap_args(tmp_path, "--settle", "-5"), state=cwd_state(tmp_path))

    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert "must not be negative" in done.stderr
    assert starts(stub) == []
    assert slept == []
