#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""herdr-overview — show the Herdr session as panes grouped by workspace.

Answers the two questions an agent usually has — "which pane am I?" and "which pane do I
hand this to?" — without reading three raw JSON payloads. `pane list` carries a pane's
label but never the agent name, and `agent list` carries the name but never the label, so
the view joins them per pane.

Output is YAML when stdout is not a terminal (the model case) and an aligned table when it
is (the human case); `--format` forces either. The calling pane is marked `*` in the table,
current in the YAML, and the calling workspace header is marked `, current`.

    herdr-overview                every workspace in the session
    herdr-overview --workspace    only the calling workspace
    herdr-overview --tab          only the calling tab
    herdr-overview --current      only the calling pane
    herdr-overview | yq           piping selects YAML

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (  # pyright: ignore[reportImplicitRelativeImport]
    EXIT_OK,
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
FORMAT_TABLE = "table"
FORMAT_YAML = "yaml"

SCOPE_ANCHORS = {
    SCOPE_WORKSPACE: "HERDR_WORKSPACE_ID",
    SCOPE_TAB: "HERDR_TAB_ID",
    SCOPE_CURRENT: "HERDR_PANE_ID",
}

DASH = "-"
TABLE_COLUMNS = ("PANE", "AGENT", "STATE", "NAME", "LABEL", "TAB", "CWD")
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


@dataclass(frozen=True)
class WorkspaceGroup:
    workspace_id: str
    label: str | None
    number: int | None
    current: bool
    panes: tuple[Pane, ...]


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
    """CLI options; `argparse` writes into this typed namespace."""

    current: bool = False
    tab: bool = False
    workspace: bool = False
    format: str = FORMAT_AUTO


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-overview",
        description="Show Herdr panes grouped by workspace, marking the calling pane.",
    )
    scope = parser.add_mutually_exclusive_group()
    _ = scope.add_argument("--current", action="store_true", help="only the calling pane")
    _ = scope.add_argument("--tab", action="store_true", help="only the calling tab")
    _ = scope.add_argument("--workspace", action="store_true", help="only the calling workspace")
    _ = parser.add_argument(
        "--format",
        choices=(FORMAT_AUTO, FORMAT_TABLE, FORMAT_YAML),
        default=FORMAT_AUTO,
        help="auto: table on a terminal, YAML otherwise (default: auto)",
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


def parse_agent_names(raw: str) -> dict[str, str]:
    """Read the agent name herdr tracks per pane; `pane list` never carries it."""
    names: dict[str, str] = {}
    for entry in entries(raw, "result", "agents"):
        pane_id = entry_optional_text(entry, "pane_id")
        name = entry_optional_text(entry, "name")
        if pane_id and name:
            names[pane_id] = name
    return names


def parse_panes(
    raw: str,
    agent_names: Mapping[str, str],
) -> tuple[Pane, ...]:
    panes: list[Pane] = []
    for entry in entries(raw, "result", "panes"):
        pane_id = entry_text(entry, "pane_id", where="pane list entry")
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
            )
        )
    return tuple(panes)


# ── pure core: scope, group, render ──────────────────────────────────────────────────


def scope_of(options: Options) -> str:
    if options.current:
        return SCOPE_CURRENT
    if options.tab:
        return SCOPE_TAB
    if options.workspace:
        return SCOPE_WORKSPACE
    return SCOPE_ALL


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
    scope: str,
    env: Mapping[str, str],
) -> Overview:
    anchor = _scope_anchor(scope, env)
    current_workspace_id = env.get("HERDR_WORKSPACE_ID") or None

    current_pane_id = env.get("HERDR_PANE_ID") or None
    grouped: dict[str, list[Pane]] = {}
    for pane in panes:
        if _in_scope(pane, scope, anchor):
            marked = replace(pane, current=pane.pane_id == current_pane_id)
            grouped.setdefault(marked.workspace_id, []).append(marked)

    groups: list[WorkspaceGroup] = []
    for workspace_id, members in grouped.items():
        label, number = workspaces.get(workspace_id, (None, None))
        groups.append(
            WorkspaceGroup(
                workspace_id=workspace_id,
                label=label,
                number=number,
                current=workspace_id == current_workspace_id,
                panes=tuple(sorted(members, key=lambda pane: pane.pane_id)),
            )
        )
    groups.sort(key=lambda group: (group.number is None, group.number or 0, group.workspace_id))

    return Overview(
        scope=scope,
        current_pane_id=env.get("HERDR_PANE_ID") or None,
        current_workspace_id=current_workspace_id,
        current_tab_id=env.get("HERDR_TAB_ID") or None,
        groups=tuple(groups),
    )


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


def render_yaml(overview: Overview) -> str:
    lines = [
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
        lines.append("    panes:")
        for pane in group.panes:
            lines.append(f"      - pane_id: {_scalar(pane.pane_id)}")
            lines.append(f"        tab_id: {_scalar(pane.tab_id)}")
            lines.append(f"        agent: {_scalar(pane.agent)}")
            lines.append(f"        agent_status: {_scalar(pane.agent_status)}")
            lines.append(f"        name: {_scalar(pane.name)}")
            lines.append(f"        label: {_scalar(pane.label)}")
            lines.append(f"        current: {_scalar(pane.current)}")
            lines.append(f"        cwd: {_scalar(pane.cwd)}")
    return "\n".join(lines) + "\n"


def _display_cwd(cwd: str | None, home: str | None) -> str:
    if not cwd:
        return DASH
    if home and (cwd == home or cwd.startswith(f"{home}{os.sep}")):
        return f"~{cwd[len(home) :]}"
    return cwd


def _cells(pane: Pane, home: str | None) -> tuple[str, ...]:
    return (
        pane.pane_id,
        pane.agent or DASH,
        pane.agent_status or DASH,
        pane.name or DASH,
        pane.label or DASH,
        pane.tab_id,
        _display_cwd(pane.cwd, home),
    )


def _pane_count(count: int) -> str:
    return f"{count} pane" if count == 1 else f"{count} panes"


def _row(cells: Sequence[str], widths: Sequence[int]) -> str:
    return "  ".join(cell.ljust(width) for cell, width in zip(cells, widths, strict=True)).rstrip()


def render_table(overview: Overview, home: str | None) -> str:
    rows = [_cells(pane, home) for group in overview.groups for pane in group.panes]
    widths = [
        max([len(TABLE_COLUMNS[index])] + [len(row[index]) for row in rows])
        for index in range(len(TABLE_COLUMNS))
    ]
    lines = [f"    {_row(TABLE_COLUMNS, widths)}"]
    for position, group in enumerate(overview.groups):
        if position:
            lines.append("")
        marker = ", current" if group.current else ""
        lines.append(
            f"{group.workspace_id}  {group.label or DASH}  "
            f"({_pane_count(len(group.panes))}{marker})"
        )
        for pane in group.panes:
            lines.append(f"  {'*' if pane.current else ' '} {_row(_cells(pane, home), widths)}")
    return "\n".join(lines) + "\n"


# ── impure shell: read herdr, print the view ─────────────────────────────────────────


def run(options: Options, env: Mapping[str, str]) -> int:
    require_herdr_env(env)
    scope = scope_of(options)
    # Reject a scope whose anchor is unset before spending any herdr calls; the pure core
    # re-derives the same anchor on its own so it stays usable in isolation.
    _ = _scope_anchor(scope, env)
    herdr = find_herdr(env)
    panes_raw = run_herdr_checked([herdr, "pane", "list"], env)
    agents_raw = run_herdr_checked([herdr, "agent", "list"], env)
    workspaces_raw = run_herdr_checked([herdr, "workspace", "list"], env)

    overview = build_overview(
        parse_panes(panes_raw, parse_agent_names(agents_raw)),
        parse_workspaces(workspaces_raw),
        scope,
        env,
    )

    chosen = options.format
    if chosen == FORMAT_AUTO:
        chosen = FORMAT_TABLE if sys.stdout.isatty() else FORMAT_YAML
    rendered = (
        render_table(overview, env.get("HOME")) if chosen == FORMAT_TABLE else render_yaml(overview)
    )
    sys.stdout.write(rendered)
    return EXIT_OK


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    return guard("herdr-overview", lambda: run(options, env_map))


if __name__ == "__main__":
    raise SystemExit(main())
