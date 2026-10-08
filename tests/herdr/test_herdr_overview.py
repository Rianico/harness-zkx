"""Tests for skills/herdr/scripts/herdr_overview.py (herdr-overview helper).

Scoping, task-group grouping, and every renderer are unit-tested directly on the pure
core; the read path runs through the shared stub `herdr`. The emitted YAML is validated by
parsing it back with PyYAML, which is what proves the hand-rolled scalar quoting survives
labels and paths full of metacharacters.
"""

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping
from io import StringIO
from pathlib import Path

import herdr_cli
import herdr_overview
import pytest
import yaml
from rich.console import Console

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness

SCRIPT = SCRIPTS_DIR / "herdr_overview.py"

ENV = {
    "HERDR_ENV": "1",
    "HERDR_PANE_ID": "w9:p1",
    "HERDR_TAB_ID": "w9:t1",
    "HERDR_WORKSPACE_ID": "w9",
    "HOME": "/home/tester",
}

PANE_ENV = {key: value for key, value in ENV.items() if key != "HERDR_ENV"}

NASTY = 'quote" colon: hash # dash - tab\tnewline\nunicode ✓'


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPT)


def pane(
    pane_id: str,
    *,
    workspace_id: str = "w9",
    tab_id: str = "w9:t1",
    agent: str | None = "pi",
    status: str | None = "idle",
    name: str | None = None,
    label: str | None = None,
    cwd: str | None = "/tmp/work",
    tokens: Mapping[str, str] | None = None,
) -> herdr_overview.Pane:
    return herdr_overview.Pane(
        pane_id=pane_id,
        tab_id=tab_id,
        workspace_id=workspace_id,
        agent=agent,
        agent_status=status,
        name=name,
        label=label,
        cwd=cwd,
        current=False,
        tokens=tokens,
    )


def json_panes(*entries: dict[str, object]) -> str:
    return json.dumps({"result": {"panes": list(entries)}})


def json_tabs(*entries: dict[str, object]) -> str:
    return json.dumps({"result": {"tabs": list(entries)}})


def two_tab_state() -> dict[str, object]:
    """A session with two task groups in one workspace, one pane each."""
    return {
        **DEFAULT_STATE,
        "tabs": [
            {"tab_id": "w9:t1", "workspace_id": "w9", "label": "harness"},
            {"tab_id": "w9:t2", "workspace_id": "w9", "label": "scratch"},
        ],
        "panes": [
            {
                "pane_id": "w9:p1",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": "pi",
                "agent_status": "working",
                "cwd": "/tmp/harness",
            },
            {
                "pane_id": "w9:p2",
                "tab_id": "w9:t2",
                "workspace_id": "w9",
                "agent": None,
                "agent_status": "unknown",
                "cwd": "/tmp/scratch",
                "label": "scratch pad",
            },
        ],
    }


def rich_text(overview: herdr_overview.Overview, home: str | None) -> str:
    buffer = StringIO()
    console = Console(file=buffer, width=120, force_terminal=False, no_color=True)
    herdr_overview.render_rich(overview, home, console)
    return buffer.getvalue()


# ── unit: admission ─────────────────────────────────────────────────────────────────


def test_parse_panes_joins_agent_names_and_tolerates_missing_optionals() -> None:
    raw = json_panes(
        {
            "pane_id": "w9:p1",
            "tab_id": "w9:t1",
            "workspace_id": "w9",
            "agent": "pi",
            "agent_status": "idle",
            "cwd": "/tmp/work",
        },
        {"pane_id": "w9:p2", "tab_id": "w9:t1", "workspace_id": "w9"},
    )
    panes = herdr_overview.parse_panes(raw, {"w9:p1": "reviewer"})
    assert panes[0].name == "reviewer"
    assert panes[1].agent is None
    assert panes[1].agent_status is None
    assert panes[1].cwd is None
    assert not any(entry.current for entry in panes)


def test_parse_panes_rejects_a_non_list_payload() -> None:
    with pytest.raises(herdr_cli.HerdrError, match="is not a list"):
        _ = herdr_overview.parse_panes(json.dumps({"result": {"panes": {}}}), {})


def test_parse_panes_requires_pane_identity() -> None:
    with pytest.raises(herdr_cli.HerdrError, match="tab_id"):
        _ = herdr_overview.parse_panes(json_panes({"pane_id": "w9:p1"}), {})


def test_parse_agent_names_skips_unnamed_agents() -> None:
    raw = json.dumps(
        {
            "result": {
                "agents": [
                    {"pane_id": "w9:p1", "name": "reviewer"},
                    {"pane_id": "w9:p2", "name": None},
                    {"pane_id": None, "name": "orphan"},
                ]
            }
        }
    )
    assert herdr_overview.parse_agent_names(raw) == {"w9:p1": "reviewer"}


def test_parse_workspaces_reads_label_and_number() -> None:
    raw = json.dumps(
        {
            "result": {
                "workspaces": [
                    {"workspace_id": "w9", "label": "harness", "number": 1},
                    {"workspace_id": "wB"},
                ]
            }
        }
    )
    assert herdr_overview.parse_workspaces(raw) == {"w9": ("harness", 1), "wB": (None, None)}


def test_parse_workspaces_requires_the_workspace_id() -> None:
    raw = json.dumps({"result": {"workspaces": [{"label": "nameless"}]}})
    with pytest.raises(herdr_cli.HerdrError, match="workspace_id"):
        _ = herdr_overview.parse_workspaces(raw)


def test_parse_tabs_reads_labels_keyed_by_tab_id() -> None:
    raw = json_tabs({"tab_id": "w9:t1", "label": "harness"}, {"tab_id": "w9:t2"})
    assert herdr_overview.parse_tabs(raw) == {"w9:t1": "harness", "w9:t2": None}


def test_parse_tabs_requires_the_tab_id() -> None:
    raw = json_tabs({"label": "nameless"})
    with pytest.raises(herdr_cli.HerdrError, match="tab_id"):
        _ = herdr_overview.parse_tabs(raw)


# ── unit: scope and grouping ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        (herdr_overview.Options(), "all"),
        (herdr_overview.Options(workspace=True), "workspace"),
        (herdr_overview.Options(tab=""), "tab"),
        (herdr_overview.Options(current=True), "current"),
        (herdr_overview.Options(tab="w9:t1"), "all"),
        (herdr_overview.Options(task_group="harness"), "all"),
    ],
)
def test_scope_of_maps_the_flags(options: herdr_overview.Options, expected: str) -> None:
    assert herdr_overview.scope_of(options) == expected


def test_tab_filter_value_normalizes_flags() -> None:
    assert herdr_overview.tab_filter_value(herdr_overview.Options()) is None
    assert herdr_overview.tab_filter_value(herdr_overview.Options(tab="")) is None
    assert herdr_overview.tab_filter_value(herdr_overview.Options(tab="w9:t1")) == "w9:t1"
    assert (
        herdr_overview.tab_filter_value(herdr_overview.Options(task_group="harness")) == "harness"
    )


def test_tab_filter_value_rejects_task_group_with_tab_value() -> None:
    with pytest.raises(herdr_cli.UsageError, match="combine"):
        _ = herdr_overview.tab_filter_value(
            herdr_overview.Options(tab="w9:t1", task_group="harness")
        )


def test_resolve_tab_filter_prefers_id_then_label_then_pane() -> None:
    tabs = {"w9:t1": "harness", "w9:t2": "harness"}
    # Exact tab id wins even when a label also matches it.
    assert herdr_overview.resolve_tab_filter(
        "w9:t1", tabs, set(), allow_pane_fallback=True
    ) == frozenset({"w9:t1"})
    # A label resolves to every matching tab id.
    assert herdr_overview.resolve_tab_filter(
        "harness", tabs, set(), allow_pane_fallback=True
    ) == frozenset({"w9:t1", "w9:t2"})
    # A --tab value may borrow a tab id only the pane list carries.
    assert herdr_overview.resolve_tab_filter(
        "w9:t9", tabs, {"w9:t9"}, allow_pane_fallback=True
    ) == frozenset({"w9:t9"})
    # A --task-group value never takes the pane fallback.
    with pytest.raises(herdr_cli.UsageError, match="known tabs"):
        _ = herdr_overview.resolve_tab_filter("w9:t9", tabs, {"w9:t9"}, allow_pane_fallback=False)


def test_resolve_tab_filter_unknown_lists_known_tabs() -> None:
    with pytest.raises(herdr_cli.UsageError, match="harness \\(w9:t1\\)"):
        _ = herdr_overview.resolve_tab_filter(
            "nope", {"w9:t1": "harness"}, set(), allow_pane_fallback=True
        )


def test_build_overview_groups_by_workspace_sorted_by_number() -> None:
    panes = (
        pane("wB:p1", workspace_id="wB", tab_id="wB:t1"),
        pane("w1:p2", workspace_id="w1", tab_id="w1:t1"),
        pane("w1:p1", workspace_id="w1", tab_id="w1:t1"),
    )
    overview = herdr_overview.build_overview(
        panes, {"w1": ("one", 1), "wB": ("bee", 2)}, {}, "all", ENV
    )
    assert [group.workspace_id for group in overview.groups] == ["w1", "wB"]
    assert [entry.pane_id for entry in overview.groups[0].panes] == ["w1:p1", "w1:p2"]
    assert overview.pane_total == 3


def test_build_overview_nests_task_groups_inside_workspace() -> None:
    panes = (
        pane("w9:p2", tab_id="w9:t2"),
        pane("w9:p1", tab_id="w9:t1"),
        pane("w9:p3", tab_id="w9:t1"),
    )
    tabs = {"w9:t1": "harness", "w9:t2": "scratch"}
    overview = herdr_overview.build_overview(panes, {"w9": ("harness", 1)}, tabs, "all", ENV)

    (workspace,) = overview.groups
    assert [task_group.tab_id for task_group in workspace.task_groups] == ["w9:t1", "w9:t2"]
    assert workspace.task_groups[0].label == "harness"
    assert workspace.task_groups[0].current is True
    assert workspace.task_groups[1].current is False
    assert [entry.pane_id for entry in workspace.task_groups[0].panes] == ["w9:p1", "w9:p3"]
    assert [entry.pane_id for entry in workspace.task_groups[1].panes] == ["w9:p2"]
    assert [entry.pane_id for entry in workspace.panes] == ["w9:p1", "w9:p3", "w9:p2"]
    assert overview.pane_total == 3


def test_build_overview_marks_the_calling_pane_and_workspace() -> None:
    panes = (pane("w9:p1"), pane("w9:p2"), pane("wB:p1", workspace_id="wB", tab_id="wB:t1"))
    overview = herdr_overview.build_overview(panes, {}, {}, "all", ENV)
    marked = [entry for group in overview.groups for entry in group.panes if entry.current]
    assert [entry.pane_id for entry in marked] == ["w9:p1"]
    assert [group.current for group in overview.groups] == [True, False]


def test_build_overview_narrows_by_tab_filter() -> None:
    panes = (
        pane("w9:p1", tab_id="w9:t1"),
        pane("w9:p2", tab_id="w9:t2"),
        pane("wB:p1", workspace_id="wB", tab_id="wB:t1"),
    )
    overview = herdr_overview.build_overview(
        panes, {}, {"w9:t2": "scratch"}, "all", ENV, tab_filter=frozenset({"w9:t2"})
    )
    assert [entry.pane_id for group in overview.groups for entry in group.panes] == ["w9:p2"]


@pytest.mark.parametrize(
    ("scope", "expected"),
    [
        ("workspace", ["w9:p1", "w9:p2"]),
        ("tab", ["w9:p1"]),
        ("current", ["w9:p1"]),
    ],
)
def test_build_overview_narrows_by_scope(scope: str, expected: list[str]) -> None:
    panes = (
        pane("w9:p1"),
        pane("w9:p2", tab_id="w9:t2"),
        pane("wB:p1", workspace_id="wB", tab_id="wB:t1"),
    )
    overview = herdr_overview.build_overview(panes, {}, {}, scope, ENV)
    assert [entry.pane_id for group in overview.groups for entry in group.panes] == expected


@pytest.mark.parametrize(
    ("scope", "key"),
    [("workspace", "HERDR_WORKSPACE_ID"), ("tab", "HERDR_TAB_ID"), ("current", "HERDR_PANE_ID")],
)
def test_scope_anchor_missing_is_a_usage_error(scope: str, key: str) -> None:
    env = {name: value for name, value in ENV.items() if name != key}
    with pytest.raises(herdr_cli.UsageError, match=key):
        _ = herdr_overview.build_overview((pane("w9:p1"),), {}, {}, scope, env)


# ── unit: rendering ─────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "value",
    [
        "plain",
        NASTY,
        "",
        "123",
        "null",
        "true",
        "- item",
        "a: b",
        "0x1A",
        "0123",
        "1_000",
        "1e3",
        "yes",
        "no",
        "on",
        "off",
        "~",
        ".5",
        "e3",
        "nan",
        "w9:p1",
        "/tmp/x",
        "pi-better-edit.dev-x",
        "-",
        " ",
        "  padded",
        "trailing  ",
        "a#b",
        "a, b",
        "[a]",
        "{a}",
        "*a",
        "&a",
        "!a",
        "|a",
        ">a",
        "%a",
        "@a",
    ],
)
def test_scalar_output_round_trips_through_yaml(value: str) -> None:
    assert yaml.safe_load(f"k: {herdr_overview._scalar(value)}") == {"k": value}


def test_scalar_leaves_simple_words_unquoted() -> None:
    assert herdr_overview._scalar("reviewer") == "reviewer"
    assert herdr_overview._scalar("working") == "working"
    assert herdr_overview._scalar("pi-better-edit.dev-x") == "pi-better-edit.dev-x"


def test_scalar_quotes_values_yaml_would_retype() -> None:
    for value in ("123", "0x1A", "yes", "null", "w9:p1", "/tmp/x", ""):
        assert herdr_overview._scalar(value) == json.dumps(value)


def test_render_yaml_round_trips_hostile_labels_and_paths() -> None:
    panes = (pane("w9:p1", name=NASTY, label=NASTY, cwd=NASTY),)
    overview = herdr_overview.build_overview(
        panes, {"w9": (NASTY, 1)}, {"w9:t1": NASTY}, "all", ENV
    )

    parsed = yaml.safe_load(herdr_overview.render_yaml(overview))

    assert parsed["scope"] == "all"
    assert parsed["pane_total"] == 1
    assert parsed["current"] == {"pane_id": "w9:p1", "workspace_id": "w9", "tab_id": "w9:t1"}
    (workspace,) = parsed["workspaces"]
    assert workspace["workspace_id"] == "w9"
    assert workspace["label"] == NASTY
    assert workspace["number"] == 1
    assert workspace["current"] is True
    assert workspace["pane_count"] == 1
    (task_group,) = workspace["task_groups"]
    assert task_group["tab_id"] == "w9:t1"
    assert task_group["label"] == NASTY
    assert task_group["current"] is True
    assert task_group["pane_count"] == 1
    (entry,) = task_group["panes"]
    assert entry == {
        "pane_id": "w9:p1",
        "tab_id": "w9:t1",
        "agent": "pi",
        "agent_status": "idle",
        "name": NASTY,
        "label": NASTY,
        "current": True,
        "cwd": NASTY,
        "tokens": None,
    }


def test_render_yaml_with_no_panes_is_an_empty_list() -> None:
    overview = herdr_overview.build_overview((), {}, {}, "all", ENV)
    parsed = yaml.safe_load(herdr_overview.render_yaml(overview))
    assert parsed["pane_total"] == 0
    assert parsed["workspaces"] == []


def test_render_json_nests_task_groups() -> None:
    panes = (pane("w9:p1"),)
    overview = herdr_overview.build_overview(
        panes, {"w9": ("harness", 1)}, {"w9:t1": "harness"}, "all", ENV
    )
    data = json.loads(herdr_overview.render_json(overview))
    (workspace,) = data["workspaces"]
    (task_group,) = workspace["task_groups"]
    assert task_group["tab_id"] == "w9:t1"
    assert task_group["label"] == "harness"
    assert task_group["current"] is True
    assert task_group["pane_count"] == 1
    assert task_group["panes"][0]["pane_id"] == "w9:p1"


@pytest.mark.parametrize(
    ("cwd", "home", "expected"),
    [
        ("/home/tester", "/home/tester", "~"),
        ("/home/tester/project", "/home/tester", "~/project"),
        ("/home/testerish/project", "/home/tester", "/home/testerish/project"),
        ("/tmp/scratch", "/home/tester", "/tmp/scratch"),
        ("/tmp/scratch", None, "/tmp/scratch"),
        (None, "/home/tester", "-"),
    ],
)
def test_display_cwd_abbreviates_only_a_real_home_prefix(
    cwd: str | None, home: str | None, expected: str
) -> None:
    assert herdr_overview._display_cwd(cwd, home) == expected


def test_markdown_renders_task_group_headings_and_pipe_table() -> None:
    panes = (
        pane("w9:p1", name="reviewer", status="working", cwd="/home/tester/project"),
        pane("w9:p2", agent=None, status="unknown", cwd="/tmp/scratch", label="scratch pad"),
    )
    overview = herdr_overview.build_overview(
        panes, {"w9": ("harness", 1)}, {"w9:t1": "harness"}, "all", ENV
    )

    text = herdr_overview.render_markdown(overview, "/home/tester")

    assert "## Workspace: harness (w9) *" in text
    assert "### Task Group: harness (w9:t1) *" in text
    assert "| Pane | Agent | State | Name/Role | Tokens | Cwd |" in text
    assert "|---|---|---|---|---|---|" in text
    assert "| w9:p1 * | pi | working | reviewer | - | ~/project |" in text
    assert "| w9:p2 | - | unknown | scratch pad | - | /tmp/scratch |" in text


def test_markdown_escapes_pipe_characters_in_cells() -> None:
    panes = (pane("w9:p1", name="a|b"),)
    overview = herdr_overview.build_overview(
        panes, {"w9": ("harness", 1)}, {"w9:t1": "harness"}, "all", ENV
    )
    assert "a\\|b" in herdr_overview.render_markdown(overview, None)


def test_markdown_marks_a_non_current_workspace_without_the_suffix() -> None:
    panes = (pane("wB:p1", workspace_id="wB", tab_id="wB:t1"),)
    overview = herdr_overview.build_overview(panes, {"wB": ("other", 2)}, {}, "all", ENV)
    text = herdr_overview.render_markdown(overview, None)
    assert "## Workspace: other (wB)" in text
    assert "## Workspace: other (wB) *" not in text


def test_markdown_with_no_panes_is_empty() -> None:
    overview = herdr_overview.build_overview((), {}, {}, "all", ENV)
    assert herdr_overview.render_markdown(overview, None) == "\n"


@pytest.mark.parametrize(
    ("status", "style"),
    [
        ("idle", "green"),
        ("working", "yellow"),
        ("blocked", "red"),
        ("done", "cyan"),
        ("unknown", None),
        ("delegating", None),
    ],
)
def test_status_style_maps_known_states(status: str, style: str | None) -> None:
    assert herdr_overview._status_style(status) == style


def test_rich_renders_group_headers_and_a_table_per_task_group() -> None:
    panes = (
        pane("w9:p1", name="reviewer", status="working"),
        pane("w9:p2", status="idle"),
    )
    overview = herdr_overview.build_overview(
        panes, {"w9": ("harness", 1)}, {"w9:t1": "harness"}, "all", ENV
    )

    text = rich_text(overview, "/home/tester")

    assert "Workspace: harness (w9)" in text
    assert "Task Group: harness (w9:t1)" in text
    assert "Pane" in text
    assert "Name/Role" in text
    assert "w9:p1" in text
    assert "reviewer" in text


def test_rich_falls_back_to_markdown_when_rich_is_missing(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    panes = (pane("w9:p1"),)
    overview = herdr_overview.build_overview(panes, {"w9": ("harness", 1)}, {}, "all", ENV)
    # A None sentinel in sys.modules makes `from rich... import ...` raise ImportError.
    monkeypatch.delitem(sys.modules, "rich.console", raising=False)
    monkeypatch.delitem(sys.modules, "rich.table", raising=False)
    monkeypatch.setitem(sys.modules, "rich", None)

    herdr_overview.render_rich(overview, None)

    assert "### Task Group: - (w9:t1)" in capsys.readouterr().out


# ── unit: token observability ─────────────────────────────────────────────────────────


def test_parse_panes_reads_tokens_from_pane_or_agent() -> None:
    raw_panes = json_panes(
        {
            "pane_id": "w9:p1",
            "tab_id": "w9:t1",
            "workspace_id": "w9",
            "tokens": {"summary": "⏳ 1 subagent (developer)"},
        },
        {"pane_id": "w9:p2", "tab_id": "w9:t1", "workspace_id": "w9"},
    )
    agent_names = {"w9:p1": "dev1", "w9:p2": "dev2"}
    agent_tokens = {"w9:p2": {"summary": "⏳ 2 subagents (scout, editor)"}}

    panes = herdr_overview.parse_panes(raw_panes, agent_names, agent_tokens)
    assert panes[0].tokens == {"summary": "⏳ 1 subagent (developer)"}
    assert panes[1].tokens == {"summary": "⏳ 2 subagents (scout, editor)"}


def test_markdown_renders_delegating_when_idle_with_subagent_tokens() -> None:
    panes = (
        pane(
            "w9:p1",
            name="callee",
            status="idle",
            tokens={"summary": "⏳ 1 subagent (developer)"},
        ),
        pane("w9:p2", name="reviewer", status="idle", tokens=None),
    )
    overview = herdr_overview.build_overview(panes, {"w9": ("lane", 1)}, {}, "all", ENV)
    text = herdr_overview.render_markdown(overview, "/home/tester")
    assert "delegating" in text
    assert "| idle |" in text


def test_markdown_renders_delegating_when_title_suffix_has_hourglass() -> None:
    panes = (
        pane(
            "w9:p1",
            name="callee",
            status="done",
            tokens={"title-suffix": "⏳developer"},
        ),
    )
    overview = herdr_overview.build_overview(panes, {"w9": ("lane", 1)}, {}, "all", ENV)
    assert "delegating" in herdr_overview.render_markdown(overview, "/home/tester")


def test_render_json_includes_tokens() -> None:
    tokens = {"summary": "⏳ 1 subagent (developer)", "title-suffix": "⏳developer"}
    panes = (pane("w9:p1", name="callee", tokens=tokens),)
    overview = herdr_overview.build_overview(panes, {"w9": ("lane", 1)}, {}, "all", ENV)
    data = json.loads(herdr_overview.render_json(overview))
    entry = data["workspaces"][0]["task_groups"][0]["panes"][0]
    assert entry["tokens"] == tokens


def test_render_yaml_includes_tokens_mapping() -> None:
    tokens = {"summary": "⏳ 1 subagent (developer)"}
    panes = (pane("w9:p1", name="callee", tokens=tokens),)
    overview = herdr_overview.build_overview(panes, {"w9": ("lane", 1)}, {}, "all", ENV)
    parsed = yaml.safe_load(herdr_overview.render_yaml(overview))
    entry = parsed["workspaces"][0]["task_groups"][0]["panes"][0]
    assert entry["tokens"] == tokens


# ── integration: the stub herdr ─────────────────────────────────────────────────────


def test_reads_the_pane_agent_workspace_and_tab_lists(stub: StubHarness) -> None:
    _ = stub.run(env=PANE_ENV)
    assert [call[1:3] for call in stub.calls()] == [
        ["pane", "list"],
        ["agent", "list"],
        ["workspace", "list"],
        ["tab", "list"],
    ]


def test_markdown_is_the_default_when_stdout_is_not_a_terminal(stub: StubHarness) -> None:
    done = stub.run(env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    assert "## Workspace: harness (w9) *" in done.stdout
    assert "### Task Group: harness (w9:t1) *" in done.stdout
    assert "| Pane | Agent | State | Name/Role | Tokens | Cwd |" in done.stdout
    assert "| reviewer" in done.stdout
    assert "w9:p1" in done.stdout


def test_format_yaml_renders_nested_task_groups(stub: StubHarness) -> None:
    done = stub.run("--format", "yaml", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    parsed = yaml.safe_load(done.stdout)
    assert parsed["scope"] == "all"
    assert parsed["current"]["pane_id"] == "w9:p1"
    assert parsed["pane_total"] == 2
    (workspace,) = parsed["workspaces"]
    assert workspace["label"] == "harness"
    (task_group,) = workspace["task_groups"]
    assert task_group["tab_id"] == "w9:t1"
    assert task_group["label"] == "harness"
    assert task_group["pane_count"] == 2
    assert [entry["name"] for entry in task_group["panes"]] == ["reviewer", None]


def test_format_json_renders_nested_task_groups(stub: StubHarness) -> None:
    done = stub.run("--format", "json", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    data = json.loads(done.stdout)
    (workspace,) = data["workspaces"]
    (task_group,) = workspace["task_groups"]
    assert task_group["tab_id"] == "w9:t1"
    assert task_group["label"] == "harness"
    assert task_group["pane_count"] == 2


def test_format_rich_and_table_render_rich_text(stub: StubHarness) -> None:
    rich_done = stub.run("--format", "rich", env=PANE_ENV)
    table_done = stub.run("--format", "table", env=PANE_ENV)

    for done in (rich_done, table_done):
        assert done.returncode == herdr_cli.EXIT_OK, done.stderr
        assert "Task Group: harness (w9:t1)" in done.stdout
        assert "Pane" in done.stdout
        assert "w9:p1" in done.stdout
    assert rich_done.stdout == table_done.stdout


@pytest.mark.parametrize(
    ("flag", "expected"),
    [("--current", ["w9:p1"]), ("--tab", ["w9:p1", "w9:p2"]), ("--workspace", ["w9:p1", "w9:p2"])],
)
def test_scope_flags_narrow_the_stub_session(
    stub: StubHarness, flag: str, expected: list[str]
) -> None:
    done = stub.run(flag, "--format", "json", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    parsed = json.loads(done.stdout)
    assert [
        entry["pane_id"]
        for group in parsed["workspaces"]
        for task_group in group["task_groups"]
        for entry in task_group["panes"]
    ] == expected


def test_task_group_filter_narrows_to_one_group(stub: StubHarness) -> None:
    for args in (("--tab", "w9:t1"), ("--tab", "harness"), ("--task-group", "harness")):
        done = stub.run(*args, "--format", "json", env=PANE_ENV, state=two_tab_state())
        assert done.returncode == herdr_cli.EXIT_OK, done.stderr
        parsed = json.loads(done.stdout)
        groups = [
            task_group for group in parsed["workspaces"] for task_group in group["task_groups"]
        ]
        assert [task_group["tab_id"] for task_group in groups] == ["w9:t1"]
        assert parsed["pane_total"] == 1


def test_task_group_filter_matches_label(stub: StubHarness) -> None:
    done = stub.run(
        "--task-group", "scratch", "--format", "json", env=PANE_ENV, state=two_tab_state()
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    parsed = json.loads(done.stdout)
    groups = [task_group for group in parsed["workspaces"] for task_group in group["task_groups"]]
    assert [task_group["tab_id"] for task_group in groups] == ["w9:t2"]


def test_bare_tab_still_scopes_to_the_calling_tab(stub: StubHarness) -> None:
    done = stub.run("--tab", "--format", "json", env=PANE_ENV, state=two_tab_state())
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    parsed = json.loads(done.stdout)
    groups = [task_group for group in parsed["workspaces"] for task_group in group["task_groups"]]
    assert [task_group["tab_id"] for task_group in groups] == ["w9:t1"]
    assert parsed["pane_total"] == 1


def test_unknown_tab_filter_is_a_usage_error_with_a_listing(stub: StubHarness) -> None:
    done = stub.run("--tab", "nope", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "nope" in done.stderr
    assert "harness (w9:t1)" in done.stderr


def test_task_group_with_tab_value_is_rejected(stub: StubHarness) -> None:
    done = stub.run("--task-group", "harness", "--tab", "w9:t1", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "combine" in done.stderr
    assert stub.calls() == []


def test_scope_without_its_anchor_env_is_a_usage_error(stub: StubHarness) -> None:
    done = stub.run("--tab", env={**PANE_ENV, "HERDR_TAB_ID": None})
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "HERDR_TAB_ID" in done.stderr
    assert stub.calls() == []


def test_refuses_without_herdr_env(stub: StubHarness) -> None:
    done = stub.run(env={"HERDR_ENV": None})
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "HERDR_ENV" in done.stderr
    assert stub.calls() == []


def test_a_malformed_pane_list_is_reported(stub: StubHarness) -> None:
    done = stub.run(env=PANE_ENV, state={**DEFAULT_STATE, "panes": None})
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "is not a list" in done.stderr
    assert "Traceback" not in done.stderr


def test_conflicting_scope_flags_are_rejected(stub: StubHarness) -> None:
    done = stub.run("--tab", "--current", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_USAGE


# ── metadata: PEP 723 conformance ───────────────────────────────────────────────────


def test_pep723_metadata_precedes_docstring() -> None:
    header = SCRIPT.read_text().split('"""', 1)[0]
    assert header.startswith("#!/usr/bin/env python3\n")
    assert "# /// script" in header
    assert 'requires-python = ">=3.14"' in header
    assert "dependencies = []" in header
    assert header.rstrip().endswith("# ///")


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv is required for the PEP 723 runner")
def test_uv_run_help_executes_without_path_configuration(tmp_path: Path) -> None:
    done = subprocess.run(
        ["uv", "run", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        env={"HOME": os.environ.get("HOME", ""), "PATH": os.environ.get("PATH", "")},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "usage: herdr-overview" in done.stdout
