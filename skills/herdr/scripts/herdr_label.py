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
label is waiting for an occupant; `stale_labels` is what reports that orphaned label, and a
normal `herdr-dispatch` prints it on stderr without any operator-invoked pass.

Exit status: 0 ok, 1 herdr failure, 2 usage or missing precondition, 3 label/agent mismatch.

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    AGENT_NAME_PATTERN,
    EXIT_BLOCKED,
    EXIT_OK,
    METHOD_CONSTRAINT_EPILOG,
    UsageError,
    add_shared_argument,
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
    add_shared_argument(parser, "pane", help="label this pane instead of the calling pane")
    add_shared_argument(
        parser,
        "tab",
        help="rename the calling tab (Task Group) instead of labelling a pane",
    )
    add_shared_argument(
        parser,
        "task_group",
        help="scope NAME with this task-group slug before naming the pane and agent",
    )
    _ = parser.add_argument(
        "--label-only",
        action="store_true",
        help="set the pane label but leave the agent name alone",
    )
    _ = parser.add_argument("--clear", action="store_true", help="drop both names")
    add_shared_argument(parser, "json", help="print the result as JSON")
    add_shared_argument(parser, "dry_run", help="print the herdr calls, rename nothing")
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


def stale_labels(
    panes: Sequence[Mapping[str, object]] | None,
    agents: Sequence[Mapping[str, object]] | None,
) -> list[tuple[str, str]]:
    """Panes carrying an agent-shaped label that no live agent owns: (pane id, label).

    `pairs`, `pair_mismatches` and `descriptive_labels` all iterate the *agent* inventory, so a
    pane whose agent has exited is invisible to every one of them. This iterates the *pane*
    inventory instead, so a normal dispatch reports the orphan from inventories it reads anyway.

    A pane counts as live when the agent inventory gives it a `pane_id`, or when its label is
    the name of a live agent whose `agent list` row carries no `pane_id` (then the row does not
    say which pane it occupies, so the match is the only evidence available), so a healthy pair
    is never reported. An agent row that names another pane does not excuse this one: the row
    locates its agent elsewhere, so a pane no live agent occupies stays stale. Rows are deduped
    by pane id, since `pane list` can repeat one.

    Positivist evidence (#210): an unreadable or empty inventory answers nothing, so `None` or
    an empty sequence reports no stale label rather than declaring every label stale.
    """
    if not panes or not agents:
        return []
    live_panes = {pane for entry in agents if (pane := entry_optional_text(entry, "pane_id"))}
    # A name-match suppresses only when the agent row does not say which pane it occupies.
    faceless_names = {
        name
        for entry in agents
        if not entry_optional_text(entry, "pane_id")
        and (name := entry_optional_text(entry, "name"))
    }
    stale: list[tuple[str, str]] = []
    seen: set[str] = set()
    for entry in panes:
        pane = entry_optional_text(entry, "pane_id")
        label = entry_optional_text(entry, "label")
        if not pane or not label or not AGENT_NAME.match(label):
            continue
        if pane in live_panes or label in faceless_names or pane in seen:
            continue
        seen.add(pane)
        stale.append((pane, label))
    return stale


# ── rename argv builders: the one place a rename is spelled ─────────────────────────


def pane_rename_argv(herdr: str, pane_id: str, label: str) -> list[str]:
    """The argv that sets a pane's visible label, anchored on its physical pane id."""
    return [herdr, "pane", "rename", pane_id, label]


def agent_rename_argv(herdr: str, pane_id: str, name: str) -> list[str]:
    """The argv that names the agent hosting a pane, anchored on its physical pane id."""
    return [herdr, "agent", "rename", pane_id, name]


def tab_rename_argv(herdr: str, tab_id: str, title: str) -> list[str]:
    """The argv that sets a Task Group (tab) title, anchored on its physical tab id."""
    return [herdr, "tab", "rename", tab_id, title]


# ── #182 t2: ID-anchored self-healing reconciliation (ADR-0020) ─────────────────────

# The orchestrator half of a lane's name: `<task_group>` titles the tab, `<task_group>-orch`
# names the sending pane. Five characters, so a 32-char slug cannot compose a valid agent name.
ORCHESTRATOR_SUFFIX = "-orch"


def _one_line(text: str, limit: int = 160) -> str:
    """Collapse a message onto one line, so one skipped step prints exactly one line."""
    return " ".join(text.split())[:limit]


def tab_id_by_pane(panes: Sequence[Mapping[str, object]]) -> dict[str, str]:
    """Pane id -> tab id, read from the pane inventory: the physical anchor of a lane."""
    rows: dict[str, str] = {}
    for entry in panes:
        pane = entry_optional_text(entry, "pane_id")
        tab = entry_optional_text(entry, "tab_id")
        if pane and tab:
            _ = rows.setdefault(pane, tab)
    return rows


def agent_name_by_pane(agents: Sequence[Mapping[str, object]]) -> dict[str, str | None]:
    """Pane id -> live agent name, with None for an agent that dropped its name."""
    rows: dict[str, str | None] = {}
    for entry in agents:
        pane = entry_optional_text(entry, "pane_id")
        if pane:
            _ = rows.setdefault(pane, entry_optional_text(entry, "name"))
    return rows


def tab_titles(herdr: str, env: Mapping[str, str]) -> dict[str, str | None]:
    """Task Group (tab) titles keyed by tab id; `pane list` never carries the title."""
    titles: dict[str, str | None] = {}
    for entry in entries(run_herdr_checked([herdr, "tab", "list"], env), "result", "tabs"):
        tab = entry_optional_text(entry, "tab_id")
        if tab:
            titles[tab] = entry_optional_text(entry, "label")
    return titles


def reconciliation_argv(
    herdr: str,
    panes: Sequence[Mapping[str, object]],
    agents: Sequence[Mapping[str, object]],
    tabs: Mapping[str, str | None],
    *,
    lane_tab_id: str | None,
    orchestrator_pane_id: str | None,
    task_group: str | None,
) -> tuple[list[list[str]], list[str]]:
    """Plan one active reconciliation pass as (rename argv, one note per skipped step).

    ADR-0020: physical ids (`pane_id`, `tab_id`) are the anchors and the source of truth, so
    every row here is keyed on an id and matched against what the inventory says that id should
    carry. A visible label is never a target: it is only ever the value being written.

    Three cases, all no-ops when already correct — the central invariant is that a correct lane
    yields ZERO argv, so a caller may run this on every dispatch and reply:

    1. A worker in this lane whose live agent dropped its name takes the surviving pane label
       back, as `agent rename` AND `pane rename` (ADR-0020 names both — docs/adr/0020:41, so the
       second rename is issued even when the pane already carries that label; see the loop).
       Matching the worker to THIS lane is a `tab_id` question, so a snapshot that answers no lane
       tab id cannot repair any worker: that skip prints a note too, rather than passing for the
       healthy lane's silence.
    2. The lane's tab title differs from `<task_group>` -> `tab rename`.
    3. The sending orchestrator pane hosts a live agent with no name -> `agent rename` to
       `<task_group>-orch`. Case 1 skips that pane, so the orchestrator is named by its lane,
       never by a stale label, and never renamed twice.

    `task_group` None asks for neither case 2 nor case 3, so it is silent: the caller that
    derived nothing says so itself (see `reconcile_lane`). A slug, or the slug with the
    `-orch` suffix appended, that breaks `[a-z][a-z0-9_-]{0,31}` is SKIPPED with a note and
    never reaches herdr. Notes carry no marker prefix: the caller owns its own stderr prefix.

    The tab half distinguishes two absences, and only one of them is evidence (#182 t5 2.5e). A
    `lane_tab_id` that is not a key of `tabs` means `tab list` never reported that tab at all, so
    there is no row to compare and the tab is left alone with a note; a row that IS reported with
    an empty label is a title that positively differs from `<task_group>`, so it takes the rename
    and no note. Behaviour is unchanged here — this is the inventory of what each note means.
    """
    argv: list[list[str]] = []
    notes: list[str] = []
    pane_tabs = tab_id_by_pane(panes)
    names = agent_name_by_pane(agents)
    composed = f"{task_group}{ORCHESTRATOR_SUFFIX}" if task_group else ""
    orchestrator_regained = bool(
        orchestrator_pane_id
        and composed
        and AGENT_NAME.match(composed)
        and names.get(orchestrator_pane_id) is None
        and orchestrator_pane_id in names
        and conflict_with(agents, composed, orchestrator_pane_id) is None
    )

    restorable = restorable_agents(panes, agents)
    # Case 1 can only prove a nameless worker belongs to THIS lane through `tab_id`, so a snapshot
    # that answers none heals nothing — and silence there looked exactly like the healthy lane's
    # own empty plan (#182 t5 2.5d). Say it once, and only while a candidate actually waits on the
    # anchor: the pane case 3 is about to name is not a worker left behind, and a pane on another
    # tab was never this lane's to heal.
    unanchorable = [
        pane
        for pane, _label in restorable
        if pane != orchestrator_pane_id or not orchestrator_regained
    ]
    if lane_tab_id is None and unanchorable:
        notes.append(
            f"{len(unanchorable)} nameless worker pane(s) wait on a lane tab id this snapshot "
            "does not answer; left their names alone"
        )

    for pane, label in restorable:
        if pane == orchestrator_pane_id and orchestrator_regained:
            continue
        if lane_tab_id is None or pane_tabs.get(pane) != lane_tab_id:
            continue
        # ADR-0020 names BOTH commands for this case (docs/adr/0020:41), so the pane re-mark is
        # issued even though the label being written is the one the pane already carries: the pair
        # is the contract, and a pane that kept its label while its agent lost its name is only
        # provably back in service once both renames answer. Dropping the second rename is the
        # mutant `test_a_dropped_agent_name_takes_the_agent_rename_and_the_pane_rename` catches.
        argv.append(agent_rename_argv(herdr, pane, label))
        argv.append(pane_rename_argv(herdr, pane, label))

    if task_group is None:
        return argv, notes

    if not AGENT_NAME.match(task_group):
        # One ungrammatical slug poisons both halves — the tab title and the composed
        # `<task_group>-orch` share it — so it is one skipped decision and one note, not two.
        notes.append(
            f"task group {task_group!r} is not a valid name (want {AGENT_NAME_PATTERN} "
            "(max 32 chars)); left the tab title and the orchestrator name alone"
        )
        return argv, notes
    if lane_tab_id is None:
        notes.append("cannot anchor a tab id on the calling pane; left the tab title alone")
    elif lane_tab_id not in tabs:
        notes.append(f"tab {lane_tab_id!r} carries no title to compare; left it alone")
    elif tabs[lane_tab_id] != task_group:
        argv.append(tab_rename_argv(herdr, lane_tab_id, task_group))

    if not AGENT_NAME.match(composed):
        notes.append(
            f"{composed!r} is not a valid agent name (want {AGENT_NAME_PATTERN} (max 32 chars), "
            f"the slug plus the {len(ORCHESTRATOR_SUFFIX)}-char '{ORCHESTRATOR_SUFFIX}' "
            "suffix); left the orchestrator name alone"
        )
    elif orchestrator_pane_id is None:
        notes.append("cannot anchor a pane id for the sending orchestrator; left it alone")
    elif names.get(orchestrator_pane_id) is None and orchestrator_pane_id in names:
        # A live agent on that pane that dropped its name: the only state worth a rename.
        taken = conflict_with(agents, composed, orchestrator_pane_id)
        if taken is not None:
            notes.append(
                f"agent name {composed!r} is already used by pane {taken}; "
                "left the orchestrator name alone"
            )
        else:
            argv.append(agent_rename_argv(herdr, orchestrator_pane_id, composed))
    return argv, notes


def reconcile_lane(
    herdr: str,
    env: Mapping[str, str],
    *,
    task_group: str | None,
    marker: str,
    dry_run: bool = False,
    missing_note: str | None = None,
    pane_id: str | None = None,
    tab_id: str | None = None,
    inventory: tuple[Sequence[Mapping[str, object]], Sequence[Mapping[str, object]]] | None = None,
) -> list[list[str]]:
    """Run the active ID-anchored reconciliation pass; best-effort, never fatal (ADR-0020).

    `herdr-dispatch` and `herdr-reply` call this on their own path, so a lane self-heals without
    an operator pass: it renames only what the inventories prove has drifted (see
    `reconciliation_argv`), which makes an already-correct lane issue zero calls.

    Every failure is a line on stderr, never an exit status: an unreadable inventory prints
    `{marker}: reconciliation skipped: ...`, each refused rename prints one
    `{marker}: rename skipped: ...`, and the caller delivers whatever it was going to deliver.
    `marker` is the calling script's own stderr marker, so the line stays in the register the
    lease bookkeeping already uses. `missing_note` is the caller's sentence for a task group it
    could not derive from its own records; when absent the pass stays silent about it.

    `dry_run` prints the planned argv as JSON and renames nothing, including when the caller has
    nothing to reconcile (then it prints nothing at all). Returns the argv actually issued.
    """
    try:
        panes, agents = fetch_inventory(herdr, env) if inventory is None else inventory
        caller = pane_id or env.get("HERDR_PANE_ID") or current_pane_id(herdr, env)
        lane_tab = tab_id or tab_id_by_pane(panes).get(caller)
        tabs = tab_titles(herdr, env) if task_group is not None else {}
        # The planner is part of the guarded read, not of the verdict it hands back (#182 t5 2.3):
        # it consumes the snapshot above, so a row shape it cannot plan over raises here, where
        # one skipped pass is the answer. Left outside the `try` it propagated into
        # `herdr-dispatch` before `resolve_targets` and into `herdr-reply` before the delivery —
        # two callers whose whole contract for this pass is that it annotates, never aborts.
        argv, notes = reconciliation_argv(
            herdr,
            panes,
            agents,
            tabs,
            lane_tab_id=lane_tab,
            orchestrator_pane_id=caller,
            task_group=task_group,
        )
    except Exception as exc:
        print(f"{marker}: reconciliation skipped: {_one_line(str(exc))}", file=sys.stderr)
        return []

    # Both sentences are the pass's own answer, so neither is printed over a pass that never
    # reached an answer.
    if task_group is None and missing_note is not None:
        print(f"{marker}: {missing_note}", file=sys.stderr)
    for note in notes:
        print(f"{marker}: {note}", file=sys.stderr)
    if not argv:
        return []
    if dry_run:
        print(json.dumps(argv))
        return argv

    issued: list[list[str]] = []
    for step in argv:
        try:
            _ = run_herdr_checked(step, env)
        except Exception as exc:
            print(f"{marker}: rename skipped: {_one_line(str(exc))}", file=sys.stderr)
            continue
        issued.append(step)
    return issued


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
        label_argv = [pane_rename_argv(herdr, pane, agent) for pane, _, agent in mismatches]
        name_argv = [agent_rename_argv(herdr, pane, label) for pane, label in restorable]
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
    argv = tab_rename_argv(herdr, tab_id, name)
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

    # `--clear` is the one argv argument that drops both names; the builders stay string-typed.
    stated = "--clear" if options.clear else name
    pane_argv = pane_rename_argv(herdr, pane_id, stated)
    agent_argv = agent_rename_argv(herdr, pane_id, stated)
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
