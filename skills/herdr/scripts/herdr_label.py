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

A multi-word label needs `--label-only`, because an agent name must match
``[a-z][a-z0-9_-]{0,31}``.

Exit status: 0 ok, 1 herdr failure, 2 usage or missing precondition.

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
from herdr_cli import (  # pyright: ignore[reportImplicitRelativeImport]
    EXIT_OK,
    UsageError,
    current_pane_id,
    entries,
    entry_optional_text,
    find_herdr,
    guard,
    require_herdr_env,
    run_herdr_checked,
)

AGENT_NAME = re.compile(r"[a-z][a-z0-9_-]{0,31}\Z")


@dataclass
class Options:
    """CLI options; `argparse` writes into this typed namespace."""

    name: str = ""
    pane: str | None = None
    label_only: bool = False
    clear: bool = False
    json: bool = False
    dry_run: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-label",
        description=(
            "Give a pane one name: its visible label and, when it hosts an agent, "
            "that agent's name."
        ),
        epilog="exit status: 0 ok, 1 herdr failure, 2 usage or precondition",
    )
    _ = parser.add_argument("name", nargs="?", metavar="NAME", help="the name to set")
    _ = parser.add_argument(
        "--pane", metavar="ID", help="label this pane instead of the calling pane"
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
    return parser


def conflict_with(agents: Sequence[Mapping[str, object]], name: str, pane_id: str) -> str | None:
    """The other pane already using `name`, if any; agent names must be unique among live agents."""
    for entry in agents:
        other = entry_optional_text(entry, "pane_id")
        if other and other != pane_id and entry_optional_text(entry, "name") == name:
            return other
    return None


def label_pane(options: Options, env: Mapping[str, str]) -> int:
    require_herdr_env(env)
    herdr = find_herdr(env)

    if options.clear and options.name:
        raise UsageError("pass either NAME or --clear, not both")
    if not options.clear and not options.name:
        raise UsageError("pass NAME, or --clear to drop the names")

    pane_id = options.pane or current_pane_id(herdr, env)
    agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
    hosts_agent = any(entry_optional_text(entry, "pane_id") == pane_id for entry in agents)
    rename_agent = hosts_agent and not options.label_only

    # Validate before mutating anything, so a bad name never leaves a half-applied label.
    if rename_agent and not options.clear:
        if not AGENT_NAME.match(options.name):
            raise UsageError(
                f"{options.name!r} is not a valid agent name (want [a-z][a-z0-9_-]{{0,31}}); "
                "use --label-only for a multi-word label"
            )
        taken = conflict_with(agents, options.name, pane_id)
        if taken:
            raise UsageError(f"agent name {options.name!r} is already used by pane {taken}")

    suffix = ["--clear"] if options.clear else [options.name]
    pane_argv = [herdr, "pane", "rename", pane_id, *suffix]
    agent_argv = [herdr, "agent", "rename", pane_id, *suffix]
    if options.dry_run:
        print(json.dumps([pane_argv] + ([agent_argv] if rename_agent else [])))
        return EXIT_OK

    _ = run_herdr_checked(pane_argv, env)
    if rename_agent:
        _ = run_herdr_checked(agent_argv, env)

    label_state = None if options.clear else options.name
    agent_state = None if (options.clear or not rename_agent) else options.name
    if options.json:
        print(json.dumps({"pane_id": pane_id, "label": label_state, "agent": agent_state}))
    else:
        verb = "cleared" if options.clear else "named"
        print(f"{verb} {pane_id}  label={label_state or '-'}  agent={agent_state or '-'}")
    return EXIT_OK


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    return guard("herdr-label", lambda: label_pane(options, env_map))


if __name__ == "__main__":
    raise SystemExit(main())
