#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""herdr-overview — show the Herdr session as task-grouped panes by workspace.

Answers the two questions an agent usually has — "which pane am I?" and "which pane do I
hand this to?" — without reading three raw JSON payloads. `pane list` carries a pane's
label but never the agent name, and `agent list` carries the name but never the label, so
the view joins them per pane. Panes nest under the Task Group (tab) that hosts them, and
task groups nest under their workspace.

Output is Markdown when stdout is not a terminal (the model case) and a colored rich table
when it is (the human case); `--format` forces a specific format. The calling pane is
marked `*` after its id, the calling task group and workspace headers are marked `*`, and
the calling pane id is exposed in the YAML/JSON `current` block.

    herdr-overview                 every workspace in the session
    herdr-overview --workspace     only the calling workspace
    herdr-overview --tab           only the calling tab
    herdr-overview --tab harness   only the tab named harness (or its id)
    herdr-overview --task-group harness
    herdr-overview --current       only the calling pane
    herdr-overview | less          piping selects Markdown

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, replace
from typing import Any

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    EXIT_OK,
    METHOD_CONSTRAINT_EPILOG,
    UsageError,
    entries,
    entry_optional_text,
    entry_text,
    find_herdr,
    guard,
    require_herdr_env,
    run_herdr_checked,
)

SCOPE_ALL = "all"
SCOPE_WORKSPACE = "workspace"
SCOPE_TAB = "tab"
SCOPE_CURRENT = "current"

FORMAT_AUTO = "auto"
FORMAT_RICH = "rich"
FORMAT_MARKDOWN = "markdown"
FORMAT_TABLE = "table"  # compat alias: renders rich
FORMAT_YAML = "yaml"
FORMAT_JSON = "json"

FORMAT_CHOICES = (
    FORMAT_AUTO,
    FORMAT_RICH,
    FORMAT_MARKDOWN,
    FORMAT_TABLE,
    FORMAT_YAML,
    FORMAT_JSON,
)

SCOPE_ANCHORS = {
    SCOPE_WORKSPACE: "HERDR_WORKSPACE_ID",
    SCOPE_TAB: "HERDR_TAB_ID",
    SCOPE_CURRENT: "HERDR_PANE_ID",
}

DASH = "-"
MD_COLUMNS = ("Pane", "Agent", "State", "Name/Role", "Tokens", "Cwd")
STATUS_STYLES = {
    "idle": "green",
    "working": "yellow",
    "blocked": "red",
    "done": "cyan",
}
_YAML_RESERVED = frozenset(
    {"y", "yes", "n", "no", "true", "false", "on", "off", "null", "nan", "inf"}
)


@dataclass(frozen=True)
class Pane:
    """One pane, with the agent details herdr splits across `pane list` and `agent list`."""

    pane_id: str
    tab_id: str
    workspace_id: str
    agent: str | None
    agent_status: str | None
    name: str | None
    label: str | None
    cwd: str | None
    current: bool
    tokens: Mapping[str, str] | None = None


@dataclass(frozen=True)
class TaskGroup:
    """One Herdr tab (Task Group) and the panes it hosts inside its workspace."""

    tab_id: str
    label: str | None
    current: bool
    panes: tuple[Pane, ...]


@dataclass(frozen=True)
class WorkspaceGroup:
    workspace_id: str
    label: str | None
    number: int | None
    current: bool
    task_groups: tuple[TaskGroup, ...]

    @property
    def panes(self) -> tuple[Pane, ...]:
        return tuple(pane for group in self.task_groups for pane in group.panes)


@dataclass(frozen=True)
class Overview:
    scope: str
    current_pane_id: str | None
    current_workspace_id: str | None
    current_tab_id: str | None
    groups: tuple[WorkspaceGroup, ...]

    @property
    def pane_total(self) -> int:
        return sum(len(group.panes) for group in self.groups)


@dataclass
class Options:
    """CLI options; `argparse` writes into this typed namespace.

    `tab` is `None` when the flag is absent, `""` for a bare `--tab` (calling-tab scope),
    and the value for `--tab VALUE` (a task-group filter).
    """

    current: bool = False
    tab: str | None = None
    task_group: str | None = None
    workspace: bool = False
    format: str = FORMAT_AUTO
    json: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-overview",
        description="Show Herdr panes grouped by workspace and task group.",
        epilog=METHOD_CONSTRAINT_EPILOG,
    )
    scope = parser.add_mutually_exclusive_group()
    _ = scope.add_argument("--current", action="store_true", help="only the calling pane")
    _ = scope.add_argument(
        "--tab",
        nargs="?",
        const="",
        default=None,
        metavar="NAME|ID",
        help="bare: only the calling tab; with a value: only that tab",
    )
    _ = scope.add_argument("--workspace", action="store_true", help="only the calling workspace")
    _ = parser.add_argument(
        "--task-group",
        default=None,
        metavar="NAME",
        help="only the task group (tab) with this label or id; cannot combine with --tab VALUE",
    )
    _ = parser.add_argument(
        "--format",
        choices=FORMAT_CHOICES,
        default=FORMAT_AUTO,
        help="auto: rich on a terminal, Markdown otherwise; table aliases rich (default: auto)",
    )
    _ = parser.add_argument(
        "--json",
        action="store_true",
        help="output clean, valid JSON (equivalent to --format json)",
    )
    return parser


# ── admission: herdr JSON -> typed rows ──────────────────────────────────────────────


def _optional_int(entry: Mapping[str, object], key: str) -> int | None:
    value = entry.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def parse_workspaces(raw: str) -> dict[str, tuple[str | None, int | None]]:
    """Read workspace label and number, keyed by workspace id."""
    workspaces: dict[str, tuple[str | None, int | None]] = {}
    for entry in entries(raw, "result", "workspaces"):
        workspace_id = entry_text(entry, "workspace_id", where="workspace list entry")
        workspaces[workspace_id] = (
            entry_optional_text(entry, "label"),
            _optional_int(entry, "number"),
        )
    return workspaces


def parse_tabs(raw: str) -> dict[str, str | None]:
    """Read Task Group (tab) labels keyed by tab id; `pane list` never carries the label."""
    tabs: dict[str, str | None] = {}
    for entry in entries(raw, "result", "tabs"):
        tab_id = entry_text(entry, "tab_id", where="tab list entry")
        tabs[tab_id] = entry_optional_text(entry, "label")
    return tabs


def parse_agent_names(raw: str) -> dict[str, str]:
    """Read the agent name herdr tracks per pane; `pane list` never carries it."""
    names: dict[str, str] = {}
    for entry in entries(raw, "result", "agents"):
        pane_id = entry_optional_text(entry, "pane_id")
        name = entry_optional_text(entry, "name")
        if pane_id and name:
            names[pane_id] = name
    return names


def parse_agent_tokens(raw: str) -> dict[str, Mapping[str, str]]:
    """Read agent tokens herdr tracks per pane, if present."""
    tokens_by_pane: dict[str, Mapping[str, str]] = {}
    for entry in entries(raw, "result", "agents"):
        pane_id = entry_optional_text(entry, "pane_id")
        raw_tokens = entry.get("tokens")
        if pane_id and isinstance(raw_tokens, dict):
            tokens_by_pane[pane_id] = {
                str(k): str(v) for k, v in raw_tokens.items() if isinstance(v, str)
            }
    return tokens_by_pane


def parse_panes(
    raw: str,
    agent_names: Mapping[str, str],
    agent_tokens: Mapping[str, Mapping[str, str]] | None = None,
) -> tuple[Pane, ...]:
    panes: list[Pane] = []
    for entry in entries(raw, "result", "panes"):
        pane_id = entry_text(entry, "pane_id", where="pane list entry")
        tokens: Mapping[str, str] | None = None
        raw_tokens = entry.get("tokens")
        if isinstance(raw_tokens, dict) and raw_tokens:
            tokens = {str(k): str(v) for k, v in raw_tokens.items() if isinstance(v, str)}
        elif agent_tokens and pane_id in agent_tokens:
            tokens = agent_tokens[pane_id]
        panes.append(
            Pane(
                pane_id=pane_id,
                tab_id=entry_text(entry, "tab_id", where=f"pane {pane_id}"),
                workspace_id=entry_text(entry, "workspace_id", where=f"pane {pane_id}"),
                agent=entry_optional_text(entry, "agent"),
                agent_status=entry_optional_text(entry, "agent_status"),
                name=agent_names.get(pane_id),
                label=entry_optional_text(entry, "label"),
                cwd=entry_optional_text(entry, "cwd"),
                current=False,
                tokens=tokens,
            )
        )
    return tuple(panes)


# ── pure core: scope, filter, group, render ──────────────────────────────────────────


def scope_of(options: Options) -> str:
    if options.current:
        return SCOPE_CURRENT
    if options.tab == "":
        return SCOPE_TAB
    if options.workspace:
        return SCOPE_WORKSPACE
    return SCOPE_ALL


def tab_filter_value(options: Options) -> str | None:
    """The value narrowing rows to a resolved tab id set, or None when no filter is set.

    A `--tab VALUE` and a `--task-group NAME` are mutually exclusive filters; a bare
    `--tab` (calling-tab scope) leaves `tab` empty and is not a filter.
    """
    if options.task_group:
        if options.tab:
            raise UsageError("--task-group cannot be combined with a --tab value")
        return options.task_group
    return options.tab or None


def resolve_tab_filter(
    value: str,
    tabs: Mapping[str, str | None],
    pane_tab_ids: AbstractSet[str],
    *,
    allow_pane_fallback: bool,
) -> frozenset[str]:
    """Resolve a filter value to the tab ids it names, or explain the known tabs.

    Precedence: an exact tab id wins, then an exact label (every match), then (for a
    `--tab` value only) a tab id that only the pane list carries. A `--task-group` value
    never borrows the pane fallback: it matches label or tab id only.
    """
    if value in tabs:
        return frozenset({value})
    matched = frozenset(tab_id for tab_id, label in tabs.items() if label == value)
    if matched:
        return matched
    if allow_pane_fallback and value in pane_tab_ids:
        return frozenset({value})
    known = ", ".join(f"{label or DASH} ({tab_id})" for tab_id, label in sorted(tabs.items()))
    raise UsageError(f"unknown tab {value!r}; known tabs: {known or 'none'}")


def _scope_anchor(scope: str, env: Mapping[str, str]) -> str:
    key = SCOPE_ANCHORS.get(scope)
    if key is None:
        return ""
    anchor = env.get(key)
    if not anchor:
        raise UsageError(f"--{scope} needs {key} in the environment; it is unset")
    return anchor


def _in_scope(pane: Pane, scope: str, anchor: str) -> bool:
    match scope:
        case "workspace":
            return pane.workspace_id == anchor
        case "tab":
            return pane.tab_id == anchor
        case "current":
            return pane.pane_id == anchor
        case _:
            return True


def build_overview(
    panes: Sequence[Pane],
    workspaces: Mapping[str, tuple[str | None, int | None]],
    tabs: Mapping[str, str | None],
    scope: str,
    env: Mapping[str, str],
    *,
    tab_filter: AbstractSet[str] | None = None,
) -> Overview:
    anchor = _scope_anchor(scope, env)
    current_workspace_id = env.get("HERDR_WORKSPACE_ID") or None
    current_tab_id = env.get("HERDR_TAB_ID") or None
    current_pane_id = env.get("HERDR_PANE_ID") or None

    grouped: dict[str, dict[str, list[Pane]]] = {}
    for pane in panes:
        if not _in_scope(pane, scope, anchor):
            continue
        if tab_filter is not None and pane.tab_id not in tab_filter:
            continue
        marked = replace(pane, current=pane.pane_id == current_pane_id)
        grouped.setdefault(marked.workspace_id, {}).setdefault(marked.tab_id, []).append(marked)

    groups: list[WorkspaceGroup] = []
    for workspace_id, tab_members in grouped.items():
        label, number = workspaces.get(workspace_id, (None, None))
        task_groups = tuple(
            TaskGroup(
                tab_id=tab_id,
                label=tabs.get(tab_id),
                current=tab_id == current_tab_id,
                panes=tuple(sorted(tab_members[tab_id], key=lambda pane: pane.pane_id)),
            )
            for tab_id in sorted(tab_members)
        )
        groups.append(
            WorkspaceGroup(
                workspace_id=workspace_id,
                label=label,
                number=number,
                current=workspace_id == current_workspace_id,
                task_groups=task_groups,
            )
        )
    groups.sort(key=lambda group: (group.number is None, group.number or 0, group.workspace_id))

    return Overview(
        scope=scope,
        current_pane_id=current_pane_id,
        current_workspace_id=current_workspace_id,
        current_tab_id=current_tab_id,
        groups=tuple(groups),
    )


# ── pure core: scalar helpers and shared cells ───────────────────────────────────────


def _plain_safe(text: str) -> bool:
    """True when YAML reads the text back as this exact string without quotes.

    Conservative on purpose: only an unquoted word starting with a letter or underscore,
    built from `[A-Za-z0-9_.-]`, and not spelled like a YAML bool or null. Pane ids and
    paths keep their quotes, which is always correct.
    """
    if not text or text.lower() in _YAML_RESERVED:
        return False
    first = text[0]
    if not first.isascii() or not (first.isalpha() or first == "_"):
        return False
    return all(
        character.isascii() and (character.isalnum() or character in "_.-") for character in text
    )


def _scalar(value: object) -> str:
    """Render one scalar as YAML; a JSON string is already a valid YAML double-quoted scalar."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    text = str(value)
    return text if _plain_safe(text) else json.dumps(text)


def _display_cwd(cwd: str | None, home: str | None) -> str:
    if not cwd:
        return DASH
    if home and (cwd == home or cwd.startswith(f"{home}{os.sep}")):
        return f"~{cwd[len(home) :]}"
    return cwd


def _display_state(pane: Pane) -> str:
    status = pane.agent_status or DASH
    if pane.agent_status in ("idle", "done") and pane.tokens:
        summary = pane.tokens.get("summary", "")
        title_suffix = pane.tokens.get("title-suffix", "")
        if "⏳" in summary or "subagent" in summary.lower() or "⏳" in title_suffix:
            return "delegating"
    return status


def _status_style(state: str) -> str | None:
    """The rich style for a row in this state; unknown states fall back to the default."""
    return STATUS_STYLES.get(state)


def _tokens_cell(pane: Pane) -> str:
    if not pane.tokens:
        return DASH
    return " ".join(f"{key}={value}" for key, value in sorted(pane.tokens.items()))


def _row_cells(pane: Pane, home: str | None) -> tuple[str, ...]:
    return (
        f"{pane.pane_id} *" if pane.current else pane.pane_id,
        pane.agent or DASH,
        _display_state(pane),
        pane.name or pane.label or DASH,
        _tokens_cell(pane),
        _display_cwd(pane.cwd, home),
    )


def _workspace_heading(group: WorkspaceGroup) -> str:
    marker = " *" if group.current else ""
    return f"## Workspace: {group.label or DASH} ({group.workspace_id}){marker}"


def _task_group_heading(group: TaskGroup) -> str:
    marker = " *" if group.current else ""
    return f"### Task Group: {group.label or DASH} ({group.tab_id}){marker}"


# ── pure core: renderers ─────────────────────────────────────────────────────────────


def render_yaml(overview: Overview) -> str:
    lines = [
        "# herdr-overview (format: YAML; pass --json for JSON, --format markdown for Markdown)",
        f"scope: {_scalar(overview.scope)}",
        "current:",
        f"  pane_id: {_scalar(overview.current_pane_id)}",
        f"  workspace_id: {_scalar(overview.current_workspace_id)}",
        f"  tab_id: {_scalar(overview.current_tab_id)}",
        f"pane_total: {overview.pane_total}",
    ]
    if not overview.groups:
        lines.append("workspaces: []")
        return "\n".join(lines) + "\n"

    lines.append("workspaces:")
    for group in overview.groups:
        lines.append(f"  - workspace_id: {_scalar(group.workspace_id)}")
        lines.append(f"    label: {_scalar(group.label)}")
        lines.append(f"    number: {_scalar(group.number)}")
        lines.append(f"    current: {_scalar(group.current)}")
        lines.append(f"    pane_count: {len(group.panes)}")
        lines.append("    task_groups:")
        for task_group in group.task_groups:
            lines.append(f"      - tab_id: {_scalar(task_group.tab_id)}")
            lines.append(f"        label: {_scalar(task_group.label)}")
            lines.append(f"        current: {_scalar(task_group.current)}")
            lines.append(f"        pane_count: {len(task_group.panes)}")
            lines.append("        panes:")
            for pane in task_group.panes:
                lines.append(f"          - pane_id: {_scalar(pane.pane_id)}")
                lines.append(f"            tab_id: {_scalar(pane.tab_id)}")
                lines.append(f"            agent: {_scalar(pane.agent)}")
                lines.append(f"            agent_status: {_scalar(pane.agent_status)}")
                lines.append(f"            name: {_scalar(pane.name)}")
                lines.append(f"            label: {_scalar(pane.label)}")
                lines.append(f"            current: {_scalar(pane.current)}")
                lines.append(f"            cwd: {_scalar(pane.cwd)}")
                if pane.tokens is not None:
                    lines.append("            tokens:")
                    for k in sorted(pane.tokens.keys()):
                        lines.append(f"              {_scalar(k)}: {_scalar(pane.tokens[k])}")
                else:
                    lines.append("            tokens: null")
    return "\n".join(lines) + "\n"


def render_json(overview: Overview) -> str:
    data = {
        "scope": overview.scope,
        "current": {
            "pane_id": overview.current_pane_id,
            "workspace_id": overview.current_workspace_id,
            "tab_id": overview.current_tab_id,
        },
        "pane_total": overview.pane_total,
        "workspaces": [
            {
                "workspace_id": group.workspace_id,
                "label": group.label,
                "number": group.number,
                "current": group.current,
                "pane_count": len(group.panes),
                "task_groups": [
                    {
                        "tab_id": task_group.tab_id,
                        "label": task_group.label,
                        "current": task_group.current,
                        "pane_count": len(task_group.panes),
                        "panes": [
                            {
                                "pane_id": pane.pane_id,
                                "tab_id": pane.tab_id,
                                "agent": pane.agent,
                                "agent_status": pane.agent_status,
                                "name": pane.name,
                                "label": pane.label,
                                "current": pane.current,
                                "cwd": pane.cwd,
                                "tokens": dict(pane.tokens) if pane.tokens is not None else None,
                            }
                            for pane in task_group.panes
                        ],
                    }
                    for task_group in group.task_groups
                ],
            }
            for group in overview.groups
        ],
    }
    return json.dumps(data, indent=2) + "\n"


def _markdown_cell(value: str) -> str:
    """Escape one cell: `|` ends a column and a raw newline ends a row, so both break out."""
    return (
        value.replace("|", "\\|")
        .replace("\r\n", " ")
        .replace("\r", " ")
        .replace("\n", " ")
        .replace("\t", " ")
    )


def _markdown_row(cells: Sequence[str]) -> str:
    return "| " + " | ".join(_markdown_cell(cell) for cell in cells) + " |"


def render_markdown(overview: Overview, home: str | None) -> str:
    """Render nested task groups as a Markdown pipe table; the LLM/piped default."""
    lines: list[str] = []
    for workspace in overview.groups:
        lines.append(_workspace_heading(workspace))
        for task_group in workspace.task_groups:
            lines.append("")
            lines.append(_task_group_heading(task_group))
            lines.append("")
            lines.append(_markdown_row(MD_COLUMNS))
            lines.append("|" + "|".join("---" for _ in MD_COLUMNS) + "|")
            for pane in task_group.panes:
                lines.append(_markdown_row(_row_cells(pane, home)))
    return "\n".join(lines) + "\n"


def render_rich(overview: Overview, home: str | None, console: Any = None) -> None:
    """Render one rich table per task group; the TTY default.

    `rich` is imported lazily so the piped/Markdown/YAML/JSON paths never pay for it. When
    the import fails the Markdown renderer stands in. A caller may pass its own
    `rich.console.Console` (e.g. one bound to a `StringIO`) to capture the output.
    """
    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        text = render_markdown(overview, home)
        if console is None:
            _ = sys.stdout.write(text)
        else:
            _ = console.print(text, end="")
        return

    active = console if console is not None else Console()
    for workspace in overview.groups:
        _ = active.print(_workspace_heading(workspace))
        for task_group in workspace.task_groups:
            _ = active.print(_task_group_heading(task_group))
            table = Table(*MD_COLUMNS)
            for pane in task_group.panes:
                _ = table.add_row(
                    *_row_cells(pane, home), style=_status_style(_display_state(pane))
                )
            _ = active.print(table)


# ── impure shell: read herdr, print the view ─────────────────────────────────────────


def _emit(chosen: str, overview: Overview, home: str | None) -> None:
    if chosen == FORMAT_JSON:
        _ = sys.stdout.write(render_json(overview))
    elif chosen == FORMAT_YAML:
        _ = sys.stdout.write(render_yaml(overview))
    elif chosen == FORMAT_MARKDOWN:
        _ = sys.stdout.write(render_markdown(overview, home))
    else:
        render_rich(overview, home)


def run(options: Options, env: Mapping[str, str]) -> int:
    require_herdr_env(env)
    filter_value = tab_filter_value(options)
    scope = scope_of(options)
    # Reject a scope whose anchor is unset before spending any herdr calls; the pure core
    # re-derives the same anchor on its own so it stays usable in isolation.
    _ = _scope_anchor(scope, env)
    herdr = find_herdr(env)
    panes_raw = run_herdr_checked([herdr, "pane", "list"], env)
    agents_raw = run_herdr_checked([herdr, "agent", "list"], env)
    workspaces_raw = run_herdr_checked([herdr, "workspace", "list"], env)
    tabs_raw = run_herdr_checked([herdr, "tab", "list"], env)

    tabs = parse_tabs(tabs_raw)
    panes = parse_panes(
        panes_raw,
        parse_agent_names(agents_raw),
        parse_agent_tokens(agents_raw),
    )
    tab_filter: frozenset[str] | None = None
    if filter_value is not None:
        tab_filter = resolve_tab_filter(
            filter_value,
            tabs,
            {pane.tab_id for pane in panes},
            allow_pane_fallback=options.task_group is None,
        )

    overview = build_overview(
        panes,
        parse_workspaces(workspaces_raw),
        tabs,
        scope,
        env,
        tab_filter=tab_filter,
    )

    chosen = options.format
    if options.json:
        chosen = FORMAT_JSON
    elif chosen == FORMAT_TABLE:
        chosen = FORMAT_RICH
    elif chosen == FORMAT_AUTO:
        chosen = FORMAT_RICH if sys.stdout.isatty() else FORMAT_MARKDOWN
    _emit(chosen, overview, env.get("HOME"))
    return EXIT_OK


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    return guard("herdr-overview", lambda: run(options, env_map))


if __name__ == "__main__":
    raise SystemExit(main())
