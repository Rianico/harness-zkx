#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""herdr-label — give a pane the one name a person sees and an agent can address.

Herdr keeps two names for the same thing, and they disagree about who can use them. The pane
*label* is what the pane border shows, so it is the name a person reads off the screen — but
no command accepts it as a target. The agent *name* is the addressable handle, but it is
hidden unless `ui.show_agent_labels_on_pane_borders` is on, and it is cleared when the agent
exits.

Setting both to the same string removes the mismatch: the person says what they see, and that
string addresses the agent.

    herdr-label reviewer               label this pane and name its agent reviewer
    herdr-label reviewer --pane w1:p2
    herdr-label reviewer --label-only  label the pane, leave the agent name alone
    herdr-label --clear                drop both names
    herdr-label reviewer --dry-run     print the herdr calls, rename nothing
    herdr-label --verify               check that no live agent disagrees with its pane label
    herdr-label --sync                 set each drifting pane label back to its agent name

A multi-word label needs `--label-only`, because an agent name must match
``[a-z][a-z0-9_-]{0,31}``.

The agent name dies with the agent; the label outlives it. So the pair drifts on every agent
exit, and a pane that an agent later comes back into inherits the stale label. `--verify` exits 3
on that mismatch and `--sync` converges it, which is what keeps `herdr-label NAME` true for
more than one moment. Convergence runs both ways: a drifting label is set from the agent name,
and an agent that came back without a name takes the surviving label as its own. A label on a
pane with no live agent is not a mismatch — that is the state an agent leaves behind, and the
label is waiting for an occupant.

Exit status: 0 ok, 1 herdr failure, 2 usage or missing precondition, 3 label/agent mismatch.

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    AGENT_NAME_PATTERN,
    EXIT_BLOCKED,
    EXIT_OK,
    METHOD_CONSTRAINT_EPILOG,
    UsageError,
    current_pane_id,
    entries,
    entry_optional_text,
    fetch_inventory,
    find_herdr,
    guard,
    require_herdr_env,
    run_herdr_checked,
    scoped_agent_name,
    validate_agent_name,
)

AGENT_NAME = re.compile(rf"{AGENT_NAME_PATTERN}\Z")


@dataclass
class Options:
    """CLI options; `argparse` writes into this typed namespace."""

    name: str = ""
    pane: str | None = None
    tab: str | None = None
    task_group: str | None = None
    label_only: bool = False
    clear: bool = False
    verify: bool = False
    sync: bool = False
    json: bool = False
    dry_run: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-label",
        description=(
            "Give a pane one name: its visible label and, when it hosts an agent, "
            "that agent's name."
        ),
        epilog=(
            "exit status: 0 ok, 1 herdr failure, 2 usage or precondition, 3 mismatch\n\n"
            + METHOD_CONSTRAINT_EPILOG
        ),
    )
    _ = parser.add_argument("name", nargs="?", metavar="NAME", help="the name to set")
    _ = parser.add_argument(
        "--pane", metavar="ID", help="label this pane instead of the calling pane"
    )
    _ = parser.add_argument(
        "--tab",
        metavar="NAME",
        default=None,
        help="rename the calling tab (Task Group) instead of labelling a pane",
    )
    _ = parser.add_argument(
        "--task-group",
        metavar="SLUG",
        default=None,
        help="scope NAME with this task-group slug before naming the pane and agent",
    )
    _ = parser.add_argument(
        "--label-only",
        action="store_true",
        help="set the pane label but leave the agent name alone",
    )
    _ = parser.add_argument("--clear", action="store_true", help="drop both names")
    _ = parser.add_argument("--json", action="store_true", help="print the result as JSON")
    _ = parser.add_argument(
        "--dry-run", action="store_true", help="print the herdr calls, rename nothing"
    )
    _ = parser.add_argument(
        "--verify",
        action="store_true",
        help="check that every pane hosting a live agent carries that agent's name as its label",
    )
    _ = parser.add_argument(
        "--sync",
        action="store_true",
        help="converge every pane label and live agent name, in both directions",
    )
    return parser


def conflict_with(agents: Sequence[Mapping[str, object]], name: str, pane_id: str) -> str | None:
    """The other pane already using `name`, if any; agent names must be unique among live agents."""
    for entry in agents:
        other = entry_optional_text(entry, "pane_id")
        if other and other != pane_id and entry_optional_text(entry, "name") == name:
            return other
    return None


def pairs(
    panes: Sequence[Mapping[str, object]],
    agents: Sequence[Mapping[str, object]],
    pane_id: str | None = None,
) -> list[tuple[str, str | None, str | None]]:
    """Every pane hosting a live agent, as (pane id, pane label, agent name or None)."""
    labels = {
        entry_optional_text(entry, "pane_id"): entry_optional_text(entry, "label")
        for entry in panes
    }
    rows: list[tuple[str, str | None, str | None]] = []
    for entry in agents:
        pane = entry_optional_text(entry, "pane_id")
        if not pane or (pane_id and pane != pane_id):
            continue
        rows.append((pane, labels.get(pane), entry_optional_text(entry, "name")))
    return rows


def pair_mismatches(
    panes: Sequence[Mapping[str, object]],
    agents: Sequence[Mapping[str, object]],
    pane_id: str | None = None,
) -> list[tuple[str, str | None, str]]:
    """Live-agent panes whose label is missing or differs: (pane id, pane label, agent name).

    A label on a pane with no live agent is not a mismatch — there is nothing to match it
    against. A label that could never be an agent name is reported by `descriptive_labels`.
    """
    return [
        (pane, label, agent)
        for pane, label, agent in pairs(panes, agents, pane_id)
        if agent and label != agent and (label is None or AGENT_NAME.match(label))
    ]


def descriptive_labels(
    panes: Sequence[Mapping[str, object]],
    agents: Sequence[Mapping[str, object]],
    pane_id: str | None = None,
) -> list[tuple[str, str, str]]:
    """Live-agent panes whose `--label-only` label is descriptive and can never equal the name."""
    return [
        (pane, label, agent)
        for pane, label, agent in pairs(panes, agents, pane_id)
        if label and agent and not AGENT_NAME.match(label)
    ]


def unnamed_agents(
    panes: Sequence[Mapping[str, object]],
    agents: Sequence[Mapping[str, object]],
    pane_id: str | None = None,
) -> list[tuple[str, str | None]]:
    """Live agents with no name: (pane id, label). Nothing can address or reply to them."""
    return [(pane, label) for pane, label, agent in pairs(panes, agents, pane_id) if agent is None]


def restorable_agents(
    panes: Sequence[Mapping[str, object]],
    agents: Sequence[Mapping[str, object]],
    pane_id: str | None = None,
) -> list[tuple[str, str]]:
    """Unnamed agents whose surviving label can name them again: (pane id, label).

    This is the recovery path. An agent that exits loses its name while the pane keeps its
    label, so a pane that an agent later comes back into is labelled but unreachable. The
    label is the durable half of the pair, so it names the occupant that lost its own.
    """
    named = {entry_optional_text(entry, "name") for entry in agents}
    return [
        (pane, label)
        for pane, label in unnamed_agents(panes, agents, pane_id)
        if label and AGENT_NAME.match(label) and label not in named
    ]


def check_pairs(options: Options, env: Mapping[str, str]) -> int:
    """Verify or converge the pane-label/agent-name pair, which a rename cannot hold together.

    Only a mismatch `--sync` can fix changes the exit status: a descriptive label and an agent
    with no name at all are reported, but failing on them would keep the gate red forever.
    """
    if options.verify and options.sync:
        raise UsageError("pass --verify or --sync, not both")
    if options.name or options.clear or options.label_only:
        raise UsageError("pass --verify or --sync alone, without NAME, --clear, or --label-only")

    require_herdr_env(env)
    herdr = find_herdr(env)
    panes, agents = fetch_inventory(herdr, env)
    mismatches = pair_mismatches(panes, agents, options.pane)
    descriptive = descriptive_labels(panes, agents, options.pane)
    unnamed = unnamed_agents(panes, agents, options.pane)
    restorable = restorable_agents(panes, agents, options.pane)

    if options.sync:
        label_argv = [[herdr, "pane", "rename", pane, agent] for pane, _, agent in mismatches]
        name_argv = [[herdr, "agent", "rename", pane, label] for pane, label in restorable]
        if options.dry_run:
            print(json.dumps(label_argv + name_argv))
            return EXIT_OK
        for argv in label_argv + name_argv:
            _ = run_herdr_checked(argv, env)
        if options.json:
            print(
                json.dumps(
                    {
                        "labelled": [pane for pane, _, _ in mismatches],
                        "renamed": [pane for pane, _ in restorable],
                    }
                )
            )
        elif label_argv or name_argv:
            for pane, label, agent in mismatches:
                print(f"labelled {pane}  label={label or '-'} -> {agent}")
            for pane, label in restorable:
                print(f"renamed {pane}  agent=- -> {label}")
        else:
            print("labels already in sync with agent names")
        return EXIT_OK

    if options.json:
        print(
            json.dumps(
                {
                    "in_sync": not mismatches,
                    "mismatches": [
                        {"pane_id": pane, "label": label, "agent": agent}
                        for pane, label, agent in mismatches
                    ],
                    "descriptive": [
                        {"pane_id": pane, "label": label, "agent": agent}
                        for pane, label, agent in descriptive
                    ],
                    "unnamed": [{"pane_id": pane, "label": label} for pane, label in unnamed],
                    "restorable": [pane for pane, _ in restorable],
                }
            )
        )
    elif mismatches:
        for pane, label, agent in mismatches:
            print(f"{pane}  label={label or '-'}  agent={agent}")
        print("run herdr-label --sync, or name the pane again after the agent settles")
    else:
        print("labels in sync with agent names")
    if unnamed and not options.json:
        print(f"unnamed live agents ({len(unnamed)}): " + ", ".join(pane for pane, _ in unnamed))
        if restorable:
            print(
                f"  {len(restorable)} can take a name back from the surviving label: "
                "run herdr-label --sync"
            )
    return EXIT_OK if not mismatches else EXIT_BLOCKED


def pane_tab_id(herdr: str, pane_id: str, env: Mapping[str, str]) -> str:
    """The tab id hosting `pane_id`, read from the pane inventory."""
    panes = entries(run_herdr_checked([herdr, "pane", "list"], env), "result", "panes")
    for entry in panes:
        if entry_optional_text(entry, "pane_id") != pane_id:
            continue
        tab_id = entry_optional_text(entry, "tab_id")
        if tab_id:
            return tab_id
    raise UsageError(f"cannot resolve a tab id for pane {pane_id!r}")


def resolve_tab_id(herdr: str, options: Options, env: Mapping[str, str]) -> str:
    """The tab to rename: the calling tab, the `--pane` tab, or the calling pane's tab."""
    from_env = env.get("HERDR_TAB_ID")
    if from_env:
        return from_env
    if options.pane:
        return pane_tab_id(herdr, options.pane, env)
    return pane_tab_id(herdr, current_pane_id(herdr, env), env)


def rename_tab(options: Options, env: Mapping[str, str]) -> int:
    conflicts = [
        flag
        for present, flag in (
            (options.name, "NAME"),
            (options.clear, "--clear"),
            (options.label_only, "--label-only"),
            (options.verify, "--verify"),
            (options.sync, "--sync"),
            (options.task_group, "--task-group"),
        )
        if present
    ]
    if conflicts:
        raise UsageError(f"--tab cannot be combined with {', '.join(conflicts)}")
    name = options.tab
    if name is None:
        raise UsageError("--tab requires a name")

    require_herdr_env(env)
    herdr = find_herdr(env)
    tab_id = resolve_tab_id(herdr, options, env)
    argv = [herdr, "tab", "rename", tab_id, name]
    if options.dry_run:
        print(json.dumps([argv]))
        return EXIT_OK
    raw = run_herdr_checked(argv, env)
    if options.json:
        print(raw, end="" if raw.endswith("\n") else "\n")
        return EXIT_OK
    print(f"renamed tab {tab_id}  name={name}")
    return EXIT_OK


def label_pane(options: Options, env: Mapping[str, str]) -> int:
    require_herdr_env(env)
    herdr = find_herdr(env)

    if options.clear and options.name:
        raise UsageError("pass either NAME or --clear, not both")
    if not options.clear and not options.name:
        raise UsageError("pass NAME, or --clear to drop the names")

    # Scope a bare role with its task-group slug before any mutation, so an invalid
    # scoped name never leaves a half-applied label or agent rename.
    name = options.name
    if options.task_group and options.name:
        name = scoped_agent_name(options.name, options.task_group)
        validate_agent_name(name)

    pane_id = options.pane or current_pane_id(herdr, env)
    agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
    hosts_agent = any(entry_optional_text(entry, "pane_id") == pane_id for entry in agents)
    rename_agent = hosts_agent and not options.label_only

    # Validate before mutating anything, so a bad name never leaves a half-applied label.
    if rename_agent and not options.clear:
        if not AGENT_NAME.match(name):
            raise UsageError(
                f"{name!r} is not a valid agent name (want [a-z][a-z0-9_-]{{0,31}}); "
                "use --label-only for a multi-word label"
            )
        taken = conflict_with(agents, name, pane_id)
        if taken:
            raise UsageError(f"agent name {name!r} is already used by pane {taken}")

    suffix = ["--clear"] if options.clear else [name]
    pane_argv = [herdr, "pane", "rename", pane_id, *suffix]
    agent_argv = [herdr, "agent", "rename", pane_id, *suffix]
    if options.dry_run:
        print(json.dumps([pane_argv] + ([agent_argv] if rename_agent else [])))
        return EXIT_OK

    _ = run_herdr_checked(pane_argv, env)
    if rename_agent:
        _ = run_herdr_checked(agent_argv, env)

    label_state = None if options.clear else name
    agent_state = None if (options.clear or not rename_agent) else name
    if options.json:
        print(json.dumps({"pane_id": pane_id, "label": label_state, "agent": agent_state}))
    else:
        verb = "cleared" if options.clear else "named"
        print(f"{verb} {pane_id}  label={label_state or '-'}  agent={agent_state or '-'}")
    return EXIT_OK


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    if options.tab is not None:
        return guard("herdr-label", lambda: rename_tab(options, env_map))
    action = check_pairs if (options.verify or options.sync) else label_pane
    return guard("herdr-label", lambda: action(options, env_map))


if __name__ == "__main__":
    raise SystemExit(main())
