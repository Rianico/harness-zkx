"""Tests for skills/herdr/scripts/herdr_overview.py (herdr-overview helper).

Scoping, grouping, and both renderers are unit-tested directly on the pure core; the read
path runs through the shared stub `herdr`. The emitted YAML is validated by parsing it back
with PyYAML, which is what proves the hand-rolled scalar quoting survives labels and paths
full of metacharacters.
"""

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import herdr_cli
import herdr_overview
import pytest
import yaml

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
    )


def json_panes(*entries: dict[str, object]) -> str:
    return json.dumps({"result": {"panes": list(entries)}})


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


# ── unit: scope and grouping ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        (herdr_overview.Options(), "all"),
        (herdr_overview.Options(workspace=True), "workspace"),
        (herdr_overview.Options(tab=True), "tab"),
        (herdr_overview.Options(current=True), "current"),
    ],
)
def test_scope_of_maps_the_flags(options: herdr_overview.Options, expected: str) -> None:
    assert herdr_overview.scope_of(options) == expected


def test_build_overview_groups_by_workspace_sorted_by_number() -> None:
    panes = (
        pane("wB:p1", workspace_id="wB", tab_id="wB:t1"),
        pane("w1:p2", workspace_id="w1", tab_id="w1:t1"),
        pane("w1:p1", workspace_id="w1", tab_id="w1:t1"),
    )
    overview = herdr_overview.build_overview(
        panes, {"w1": ("one", 1), "wB": ("bee", 2)}, "all", ENV
    )
    assert [group.workspace_id for group in overview.groups] == ["w1", "wB"]
    assert [entry.pane_id for entry in overview.groups[0].panes] == ["w1:p1", "w1:p2"]
    assert overview.pane_total == 3


def test_build_overview_marks_the_calling_pane_and_workspace() -> None:
    panes = (pane("w9:p1"), pane("w9:p2"), pane("wB:p1", workspace_id="wB", tab_id="wB:t1"))
    overview = herdr_overview.build_overview(panes, {}, "all", ENV)
    marked = [entry for group in overview.groups for entry in group.panes if entry.current]
    assert [entry.pane_id for entry in marked] == ["w9:p1"]
    assert [group.current for group in overview.groups] == [True, False]


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
    overview = herdr_overview.build_overview(panes, {}, scope, ENV)
    assert [entry.pane_id for group in overview.groups for entry in group.panes] == expected


@pytest.mark.parametrize(
    ("scope", "key"),
    [("workspace", "HERDR_WORKSPACE_ID"), ("tab", "HERDR_TAB_ID"), ("current", "HERDR_PANE_ID")],
)
def test_scope_anchor_missing_is_a_usage_error(scope: str, key: str) -> None:
    env = {name: value for name, value in ENV.items() if name != key}
    with pytest.raises(herdr_cli.UsageError, match=key):
        _ = herdr_overview.build_overview((pane("w9:p1"),), {}, scope, env)


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
    overview = herdr_overview.build_overview(panes, {"w9": (NASTY, 1)}, "all", ENV)

    parsed = yaml.safe_load(herdr_overview.render_yaml(overview))

    assert parsed["scope"] == "all"
    assert parsed["pane_total"] == 1
    assert parsed["current"] == {"pane_id": "w9:p1", "workspace_id": "w9", "tab_id": "w9:t1"}
    (group,) = parsed["workspaces"]
    assert group["workspace_id"] == "w9"
    assert group["label"] == NASTY
    assert group["number"] == 1
    assert group["current"] is True
    assert group["pane_count"] == 1
    (entry,) = group["panes"]
    assert entry == {
        "pane_id": "w9:p1",
        "tab_id": "w9:t1",
        "agent": "pi",
        "agent_status": "idle",
        "name": NASTY,
        "label": NASTY,
        "current": True,
        "cwd": NASTY,
    }


def test_render_yaml_with_no_panes_is_an_empty_list() -> None:
    overview = herdr_overview.build_overview((), {}, "all", ENV)
    parsed = yaml.safe_load(herdr_overview.render_yaml(overview))
    assert parsed["pane_total"] == 0
    assert parsed["workspaces"] == []


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


def test_table_aligns_columns_and_marks_the_calling_pane() -> None:
    panes = (
        pane("w9:p1", name="reviewer", status="working", cwd="/home/tester/project"),
        pane("w9:p2", agent=None, status="unknown", cwd="/tmp/scratch", label="scratch pad"),
    )
    overview = herdr_overview.build_overview(panes, {"w9": ("harness", 1)}, "all", ENV)

    lines = herdr_overview.render_table(overview, "/home/tester").splitlines()
    header, group_header, first, second = lines[0], lines[1], lines[2], lines[3]

    assert header.startswith("    PANE")
    assert group_header == "w9  harness  (2 panes, current)"
    assert first.startswith("  * w9:p1")
    assert second.startswith("    w9:p2")
    assert first.index("w9:p1") == second.index("w9:p2") == 4
    assert first.index("working") == second.index("unknown")
    assert "~/project" in first
    assert "scratch pad" in second


def test_table_marks_a_non_current_workspace_without_the_suffix() -> None:
    panes = (pane("wB:p1", workspace_id="wB", tab_id="wB:t1"),)
    overview = herdr_overview.build_overview(panes, {"wB": ("other", 2)}, "all", ENV)
    assert "wB  other  (1 pane)" in herdr_overview.render_table(overview, None)


def test_table_with_no_panes_still_prints_the_header() -> None:
    overview = herdr_overview.build_overview((), {}, "all", ENV)
    assert herdr_overview.render_table(overview, None).startswith("    PANE")


# ── integration: the stub herdr ─────────────────────────────────────────────────────


def test_reads_the_pane_agent_and_workspace_lists(stub: StubHarness) -> None:
    _ = stub.run(env=PANE_ENV)
    assert [call[1:3] for call in stub.calls()] == [
        ["pane", "list"],
        ["agent", "list"],
        ["workspace", "list"],
    ]


def test_yaml_is_the_default_when_stdout_is_not_a_terminal(stub: StubHarness) -> None:
    done = stub.run(env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    parsed = yaml.safe_load(done.stdout)
    assert parsed["scope"] == "all"
    assert parsed["current"]["pane_id"] == "w9:p1"
    assert parsed["pane_total"] == 2
    (group,) = parsed["workspaces"]
    assert group["label"] == "harness"
    assert group["current"] is True
    assert [entry["name"] for entry in group["panes"]] == ["reviewer", None]


def test_format_table_renders_a_table(stub: StubHarness) -> None:
    done = stub.run("--format", "table", env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stdout.startswith("    PANE")
    assert "w9  harness  (2 panes, current)" in done.stdout
    assert "* w9:p1" in done.stdout


@pytest.mark.parametrize(
    ("flag", "expected"),
    [("--current", ["w9:p1"]), ("--tab", ["w9:p1", "w9:p2"]), ("--workspace", ["w9:p1", "w9:p2"])],
)
def test_scope_flags_narrow_the_stub_session(
    stub: StubHarness, flag: str, expected: list[str]
) -> None:
    done = stub.run(flag, env=PANE_ENV)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    parsed = yaml.safe_load(done.stdout)
    assert [entry["pane_id"] for group in parsed["workspaces"] for entry in group["panes"]] == (
        expected
    )


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
    assert 'requires-python = ">=3.12"' in header
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
