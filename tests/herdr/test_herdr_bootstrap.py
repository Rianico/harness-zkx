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


def test_cli_kind_passes_the_snippet_inline_and_writes_no_file(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run("--kind", "pi", "--pane", "w9:p1", "--role", "impl-1", "--cwd", str(tmp_path))

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    start = starts(stub)[0]
    assert flag_value(start, "--append-system-prompt") == herdr_bootstrap.render_invariant("impl-1")
    assert not (tmp_path / "AGENTS.md").exists()
    assert "agents-md=-" in done.stdout


def test_file_kind_appends_agents_md_without_the_inline_flag(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run(
        "--kind", "codex", "--pane", "w9:p1", "--role", "impl-1", "--cwd", str(tmp_path)
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    start = starts(stub)[0]
    assert "--append-system-prompt" not in start
    written = (tmp_path / "AGENTS.md").read_text()
    assert herdr_bootstrap.render_invariant("impl-1") in written
    assert str(tmp_path / "AGENTS.md") in done.stdout


def test_cline_prefers_an_existing_clinerules_file(stub: StubHarness, tmp_path: Path) -> None:
    rules = tmp_path / ".clinerules"
    _ = rules.write_text("# cline rules\n")

    done = stub.run("--kind", "cline", "--pane", "w9:p1", "--role", "tm", "--cwd", str(tmp_path))

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
    assert plan["pane_rename"][1:3] == ["pane", "rename"]
    assert plan["agent_start"][1:5] == ["agent", "start", "msg-tm", "--kind"]
    assert "--append-system-prompt" not in plan["agent_start"]
    assert stub.calls() == []
    assert not (tmp_path / "AGENTS.md").exists()


def test_dry_run_cli_kind_prints_the_inline_snippet(stub: StubHarness) -> None:
    done = stub.run("--kind", "pi", "--pane", "w9:p1", "--role", "tm", "--dry-run")

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    plan = json.loads(done.stdout)
    assert plan["agents_md"] is None
    assert flag_value(plan["agent_start"], "--append-system-prompt") == (
        herdr_bootstrap.render_invariant("tm")
    )
    assert stub.calls() == []


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
