#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""herdr-dispatch — manager-side task dispatch helper for Herdr multi-agent lanes.

Dispatches a ticket file to one or more callees with caller context and reply contract,
validates addressable agent names (refusing kinds), and verifies post-dispatch delivery
in one command.

    herdr-dispatch callee --file ticket.md --no-wait
    herdr-dispatch callee --file ticket.md --wait --timeout 15000
    herdr-dispatch callee1 callee2 --file ticket.md --no-wait

Exit status: 0 accepted, 1 herdr failure, 2 usage or missing precondition,
3 a target needs human input (blocked), 4 prompt delivered but wait timed out.

Local addition to the absorbed upstream Herdr skill; not part of `herdrdev/herdr`.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    EXIT_OK,
    METHOD_CONSTRAINT_EPILOG,
    UsageError,
    entries,
    entry_optional_text,
    find_herdr,
    guard,
    require_herdr_env,
    run_herdr_checked,
)
from herdr_lease import acquire_lease, get_lease, release_lease
from herdr_prompt import (
    EXIT_WAIT_TIMEOUT,
    PROMPT_STATES,
    WaitTimeout,
    prompt_agents,
    resolve_caller,
    resolve_targets,
)
from herdr_prompt import Options as PromptOptions


@dataclass
class Options(PromptOptions):
    """CLI options; `argparse` writes into this typed namespace."""

    force: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-dispatch",
        description="Dispatch a ticket file to a Herdr callee with caller context and reply contract.",
        epilog=(
            "exit status: 0 accepted, 1 herdr failure, 2 usage or precondition, "
            "3 a target needs human input, 4 prompt delivered but wait timed out\n\n"
            + METHOD_CONSTRAINT_EPILOG
        ),
    )
    _ = parser.add_argument(
        "targets",
        nargs="*",
        metavar="TARGET",
        help="callee agent names or pane ids (one or more)",
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
        help="wait for callee to settle after receiving ticket",
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
    _ = parser.add_argument(
        "--force",
        action="store_true",
        help="bypass active ticket lease checks and dispatch anyway",
    )
    return parser


def resolve_target_identity(
    herdr: str, target: str, env: Mapping[str, str]
) -> tuple[str, str | None]:
    """Resolve target to (canonical_agent_name_or_target, pane_id)."""
    try:
        agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
        for a in agents:
            name = entry_optional_text(a, "name")
            pane = entry_optional_text(a, "pane_id")
            if target == name:
                return target, pane
            if target == pane:
                canonical = name if name is not None else target
                return canonical, pane
    except Exception:
        pass
    return target, None


def dispatch_agents(options: Options, env: Mapping[str, str]) -> int:
    if not options.file:
        raise UsageError("pass --file PATH to dispatch a ticket")
    require_herdr_env(env)
    herdr = find_herdr(env)
    targets = resolve_targets(options, herdr, env)

    if not options.force and not options.dry_run:
        for target in targets:
            canonical, pane = resolve_target_identity(herdr, target, env)
            lease = get_lease(canonical, env=env) or (get_lease(pane, env=env) if pane else None)
            if lease:
                raise UsageError(
                    f"target {target} has an active ticket lease ({lease['ticket']}) issued by {lease['caller']}. Await reply or pass --force"
                )

    caller_name = "caller"
    if not options.dry_run:
        try:
            caller_ctx = resolve_caller(herdr, env)
            caller_name = caller_ctx.agent or caller_ctx.label or caller_ctx.pane_id
        except Exception:
            pass

    acquired_targets: list[str] = []
    if not options.dry_run:
        for target in targets:
            canonical, pane = resolve_target_identity(herdr, target, env)
            _ = acquire_lease(canonical, options.file, caller_name, pane_id=pane, env=env)
            acquired_targets.append(canonical)

    try:
        code = prompt_agents(options, env)
    except WaitTimeout:
        # Prompt accepted; wait timed out. Retain lease.
        raise
    except BaseException:
        if not options.dry_run:
            for acq in acquired_targets:
                _ = release_lease(acq, env=env)
        raise

    if code != EXIT_OK and not options.dry_run:
        for acq in acquired_targets:
            _ = release_lease(acq, env=env)

    return code


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
