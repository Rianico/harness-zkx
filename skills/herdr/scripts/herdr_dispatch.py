#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""herdr-dispatch — manager-side task dispatch helper for Herdr multi-agent lanes.

Dispatches a ticket file to one or more workers with caller context and reply contract,
validates addressable agent names (refusing kinds), and verifies post-dispatch delivery
in one command.

    herdr-dispatch worker --file ticket.md --no-wait
    herdr-dispatch worker --file ticket.md --wait --timeout 15000
    herdr-dispatch worker1 worker2 --file ticket.md --no-wait

Exit status: 0 accepted, 1 herdr failure, 2 usage or missing precondition,
3 a target needs human input (blocked), 4 prompt delivered but wait timed out.

Local addition to the absorbed upstream Herdr skill; not part of `herdrdev/herdr`.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import UsageError, guard
from herdr_prompt import (
    EXIT_WAIT_TIMEOUT,
    PROMPT_STATES,
    Options,
    WaitTimeout,
    prompt_agents,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-dispatch",
        description="Dispatch a ticket file to a Herdr worker with caller context and reply contract.",
        epilog=(
            "exit status: 0 accepted, 1 herdr failure, 2 usage or precondition, "
            "3 a target needs human input, 4 prompt delivered but wait timed out"
        ),
    )
    _ = parser.add_argument(
        "targets",
        nargs="*",
        metavar="TARGET",
        help="worker agent names or pane ids (one or more)",
    )
    _ = parser.add_argument(
        "--file",
        required=True,
        metavar="PATH",
        help="ticket payload file (required); '-' reads stdin verbatim",
    )
    _ = parser.add_argument(
        "--label",
        metavar="LABEL",
        help="exact pane label to resolve to a pane id, instead of TARGET",
    )
    _ = parser.add_argument(
        "--wait",
        action="store_true",
        help="wait for worker to settle after receiving ticket",
    )
    _ = parser.add_argument(
        "--no-wait",
        action="store_true",
        help="dispatch without waiting; fails when combined with --wait",
    )
    _ = parser.add_argument(
        "--until",
        action="append",
        metavar="STATUS",
        help=f"exact state to match after --wait, repeatable ({PROMPT_STATES})",
    )
    _ = parser.add_argument(
        "--timeout",
        type=int,
        metavar="MS",
        help="fail after this many milliseconds",
    )
    _ = parser.add_argument("--json", action="store_true", help="print herdr's raw JSON response")
    _ = parser.add_argument("--dry-run", action="store_true", help="print the argv, submit nothing")
    _ = parser.add_argument(
        "--no-caller-context",
        action="store_true",
        help="send payload verbatim without caller block and reply contract (warns loudly)",
    )
    return parser


def dispatch_agents(options: Options, env: Mapping[str, str]) -> int:
    if not options.file:
        raise UsageError("pass --file PATH to dispatch a ticket")
    return prompt_agents(options, env)


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    try:
        return guard("herdr-dispatch", lambda: dispatch_agents(options, env_map))
    except WaitTimeout as exc:
        print(f"herdr-dispatch: {exc}", file=sys.stderr)
        return EXIT_WAIT_TIMEOUT


if __name__ == "__main__":
    raise SystemExit(main())
