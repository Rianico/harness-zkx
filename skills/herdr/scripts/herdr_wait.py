#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""herdr-wait — wait for one or more Herdr agents to settle (barrier or any).

Polls ``herdr agent get <target>`` per target on a short tick instead of spawning
concurrent ``herdr agent wait`` subprocesses. Polling re-reads state on every tick,
so it is immune to the upstream event-blindness bug behind #83, where an
event-driven ``agent wait --until idle`` never wakes: background agents settle to
``done`` (not ``idle``), and a later ``seen`` flip to ``idle`` emits no event.

    herdr-wait action1 action2 --timeout 300000   # barrier: ALL settle (default)
    herdr-wait review1 review2 --any              # reactive: ANY settles
    herdr-wait action1 action2 --json             # machine-readable summary

Settled means ``idle``, ``done``, or ``blocked`` unless ``--until`` narrows it.
``blocked`` always exits 3 (the agent needs human input, matching herdr-prompt).
A watchdog ``--timeout`` (default 300s) always applies; expiry exits 1 naming the
unsettled targets.

Exit status: 0 settled, 1 herdr failure or timeout, 2 usage or missing
precondition, 3 a target needs human input (blocked).

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (  # pyright: ignore[reportImplicitRelativeImport]
    EXIT_BLOCKED,
    EXIT_HERDR,
    EXIT_OK,
    HerdrError,
    UsageError,
    decode_response,
    entry_optional_text,
    find_herdr,
    guard,
    require_herdr_env,
    run_herdr,
)

KNOWN_STATES = ("idle", "working", "blocked", "done", "unknown")
DEFAULT_SETTLED = ("idle", "done", "blocked")
DEFAULT_TIMEOUT_MS = 300000
DEFAULT_INTERVAL_S = 1.0


@dataclass
class Options:
    """CLI options; `argparse` writes into this typed namespace."""

    targets: list[str] = field(default_factory=list)
    any: bool = False
    until: list[str] = field(default_factory=list)
    timeout: int = DEFAULT_TIMEOUT_MS
    interval: float = DEFAULT_INTERVAL_S
    json: bool = False


@dataclass
class Snapshot:
    """One target's latest observed state."""

    target: str
    status: str
    revision: str | None = None
    session: str | None = None
    elapsed_ms: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-wait",
        description="Wait until Herdr agents settle (barrier over ALL targets by default).",
        epilog=(
            "exit status: 0 settled, 1 herdr failure or timeout, "
            "2 usage or precondition, 3 a target needs human input"
        ),
    )
    _ = parser.add_argument("targets", nargs="*", metavar="TARGET", help="agent names or pane ids")
    _ = parser.add_argument(
        "--any",
        action="store_true",
        help="exit 0 when ANY target settles instead of ALL (default is barrier mode)",
    )
    _ = parser.add_argument(
        "--until",
        action="append",
        default=[],
        metavar="STATUS",
        help=f"exact state to match, repeatable (default: {', '.join(DEFAULT_SETTLED)})",
    )
    _ = parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_MS,
        metavar="MS",
        help=f"watchdog: fail after this many milliseconds (default {DEFAULT_TIMEOUT_MS})",
    )
    _ = parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL_S,
        metavar="SEC",
        help=f"poll period in seconds (default {DEFAULT_INTERVAL_S})",
    )
    _ = parser.add_argument("--json", action="store_true", help="print a machine-readable summary")
    return parser


def resolve_until(until: Sequence[str]) -> list[str]:
    """Narrow the match set, auto-expanding `--until idle` to include `done`.

    Background agents settle to `done`, never `idle` (#83); waiting on `idle`
    alone hangs until a UI focus flip, so expand with a stderr warning.
    """
    if not until:
        return list(DEFAULT_SETTLED)
    for state in until:
        if state not in KNOWN_STATES:
            raise UsageError(
                f"--until {state!r} is not a known agent state (expected one of "
                f"{', '.join(KNOWN_STATES)})"
            )
    wanted = list(until)
    if "idle" in wanted and "done" not in wanted:
        wanted.append("done")
        print(
            "herdr-wait: warning: --until idle alone misses background completions "
            "(they settle to done, not idle); matching idle or done",
            file=sys.stderr,
        )
    return wanted


def snapshot_agent(herdr: str, target: str, env: Mapping[str, str]) -> Snapshot:
    """Poll one target's state via `herdr agent get`; a failed poll is fail-loud."""
    done = run_herdr([herdr, "agent", "get", target], env)
    if done.returncode != 0:
        detail = (done.stderr or done.stdout).strip() or f"exit status {done.returncode}"
        raise HerdrError(f"herdr agent get {target} failed: {detail}")
    result = decode_response(done.stdout).get("result")
    if not isinstance(result, dict):
        raise HerdrError(f"herdr agent get {target} returned no result")
    agent = result.get("agent")
    if not isinstance(agent, dict):
        raise HerdrError(f"herdr agent get {target} returned no agent record")
    status = agent.get("agent_status")
    if not isinstance(status, str) or not status:
        raise HerdrError(f"herdr agent get {target} returned no agent_status")
    revision = agent.get("revision")
    session_raw = agent.get("agent_session")
    session: str | None = None
    if isinstance(session_raw, dict):
        session = entry_optional_text(session_raw, "value")
    elif isinstance(session_raw, str) and session_raw:
        session = session_raw
    return Snapshot(
        target=target,
        status=status,
        revision=revision if isinstance(revision, str) and revision else None,
        session=session,
    )


def format_table(snaps: Sequence[Snapshot]) -> str:
    """Render the aligned TARGET STATUS REVISION ELAPSED SESSION_PATH table."""
    rows = [
        (
            snap.target,
            snap.status,
            snap.revision or "-",
            f"{snap.elapsed_ms}ms",
            snap.session or "-",
        )
        for snap in snaps
    ]
    header = ("TARGET", "STATUS", "REVISION", "ELAPSED", "SESSION_PATH")
    widths = [len(cell) for cell in header]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    lines = ["  ".join(cell.ljust(widths[index]) for index, cell in enumerate(header)).rstrip()]
    for row in rows:
        lines.append("  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)).rstrip())
    return "\n".join(lines)


def emit(snaps: Sequence[Snapshot], *, as_json: bool) -> None:
    if as_json:
        print(
            json.dumps(
                {
                    "targets": {
                        snap.target: {
                            "status": snap.status,
                            "revision": snap.revision,
                            "elapsed_ms": snap.elapsed_ms,
                            "session": snap.session,
                        }
                        for snap in snaps
                    }
                }
            )
        )
    else:
        print(format_table(snaps))


def wait_agents(options: Options, env: Mapping[str, str]) -> int:
    require_herdr_env(env)
    if not options.targets:
        raise UsageError("pass at least one TARGET (agent name or pane id)")
    if options.timeout <= 0:
        raise UsageError(f"--timeout {options.timeout} is not positive")
    if options.interval <= 0:
        raise UsageError(f"--interval {options.interval} is not positive")
    if len(set(options.targets)) != len(options.targets):
        raise UsageError("duplicate TARGETs; list each agent once")
    wanted = resolve_until(options.until)
    herdr = find_herdr(env)

    start = time.monotonic()
    deadline = start + options.timeout / 1000.0
    snaps: list[Snapshot] = []
    while True:
        now = time.monotonic()
        snaps = [snapshot_agent(herdr, target, env) for target in options.targets]
        for snap in snaps:
            # Invariant: both operands are time.monotonic() floats, so their
            # difference is always a finite float and int() cannot raise here.
            snap.elapsed_ms = int((now - start) * 1000)
        blocked = sorted(snap.target for snap in snaps if snap.status == "blocked")
        if blocked:
            emit(snaps, as_json=options.json)
            names = ", ".join(blocked)
            print(f"herdr-wait: {names} need human input (blocked)", file=sys.stderr)
            return EXIT_BLOCKED
        matched = [snap.target for snap in snaps if snap.status in wanted]
        if options.any and matched:
            emit(snaps, as_json=options.json)
            return EXIT_OK
        if not options.any and len(matched) == len(snaps):
            emit(snaps, as_json=options.json)
            return EXIT_OK
        remaining = deadline - now
        if remaining <= 0:
            unsettled = sorted(f"{snap.target} ({snap.status})" for snap in snaps)
            emit(snaps, as_json=options.json)
            print(
                f"herdr-wait: timed out after {options.timeout}ms "
                f"waiting for: {', '.join(unsettled)}",
                file=sys.stderr,
            )
            return EXIT_HERDR
        time.sleep(min(options.interval, remaining))


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    return guard("herdr-wait", lambda: wait_agents(options, env_map))


if __name__ == "__main__":
    raise SystemExit(main())
