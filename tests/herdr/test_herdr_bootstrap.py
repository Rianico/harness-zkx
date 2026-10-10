"""Tests for skills/herdr/scripts/herdr_bootstrap.py (herdr-bootstrap helper)."""

import json
from collections.abc import Callable
from pathlib import Path

import herdr_bootstrap
import herdr_cli
import pytest

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
