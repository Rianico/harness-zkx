#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""herdr-wait — wait for one or more Herdr agents to settle (barrier or any).

Polls ``herdr agent get <target>`` per target on a short tick instead of spawning
concurrent ``herdr agent wait`` subprocesses. Polling re-reads state on every tick,
so it is immune to the upstream event-blindness bug behind #83, where an
event-driven ``agent wait --until idle`` never wakes: background agents settle to
``done`` (not ``idle``), and a later ``seen`` flip to ``idle`` emits no event.
Polling still trusts the state feed, so a false-positive ``idle``/``done`` with
revision 0 and no session (weak recognition, seen on agy panes whose status bar
still reads WORKING, or when agents report idle while background subagents run)
is held, never settled; a wait that can no longer succeed fails fast (exit 2)
instead of hanging to the watchdog.

    herdr-wait action1 action2 --timeout 300000   # barrier: ALL settle (default)
    herdr-wait review1 review2 --any              # reactive: ANY settles
    herdr-wait action1 action2 --json             # machine-readable summary

Settled means ``idle``, ``done``, or ``blocked`` unless ``--until`` narrows it.
A wanted state with revision 0 is not settled (agent unrecognized); it makes the
wait unsatisfiable, so herdr-wait fails fast with exit 2 and steering toward the
event-driven Dispatch & Yield (``herdr-reply``) pattern instead of holding until
the watchdog: ANY held target in barrier mode, ALL held in ``--any`` mode.
``blocked`` always exits 3 (the agent needs human input, matching herdr-prompt).
A watchdog ``--timeout`` (default 300s) always applies; expiry exits 1 naming the
unsettled targets.

An opt-in ``--stale-after SEC`` advisory (#230) reports a target once per stall episode —
status and revision unchanged for that long (the clock restarts each time the status/revision
pair changes, and starts at the target's first sighting, so a target already stalled still waits
a further full window) — and never kills, retries, restarts, or
interrupts it. It collects evidence only: it never establishes a result, and completion for
a pane this skill did not launch is cooperative, not guaranteed.


Exit status: 0 settled, 1 herdr failure or timeout, 2 usage, missing precondition,
or an unsatisfiable wait (revision-0 weakly-recognized targets), 3 a target needs
human input (blocked).

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

# The `herdr agent get` unwrap and the state vocabulary moved to `herdr_agent`; these
# names stay reachable as `herdr_wait.<name>` for every existing consumer.
# `is_recognized`/`has_active_subagents` resolve from this module's namespace in the
# hold loop below; `is_agent_settled` is the shared settle rule `is_settled` adapts.
from herdr_agent import (
    has_active_subagents as has_active_subagents,
)
from herdr_agent import (
    is_agent_settled as is_agent_settled,
)
from herdr_agent import (
    is_recognized as is_recognized,
)
from herdr_agent import (
    observe_agent as observe_agent,
)

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    EXIT_BLOCKED,
    EXIT_HERDR,
    EXIT_OK,
    EXIT_USAGE,
    METHOD_CONSTRAINT_EPILOG,
    UsageError,
    add_shared_argument,
    entries,
    entry_optional_text,
    entrypoint,
    find_herdr,
    require_herdr_env,
    run_herdr_checked,
)

KNOWN_STATES = ("idle", "working", "blocked", "done", "unknown")
DEFAULT_SETTLED = ("idle", "done", "blocked")
DEFAULT_TIMEOUT_MS = 300000
DEFAULT_INTERVAL_S = 1.0
DEFAULT_HOLD_WARN_INTERVAL_S = 15.0


@dataclass
class Options:
    """CLI options; `argparse` writes into this typed namespace."""

    targets: list[str] = field(default_factory=list)
    any: bool = False
    until: list[str] = field(default_factory=list)
    timeout: int = DEFAULT_TIMEOUT_MS
    interval: float = DEFAULT_INTERVAL_S
    hold_interval: float = DEFAULT_HOLD_WARN_INTERVAL_S
    json: bool = False
    stale_after: float | None = None


@dataclass
class Snapshot:
    """One target's latest observed state."""

    target: str
    status: str
    revision: str | None = None
    session: str | None = None
    elapsed_ms: int = 0
    tokens: Mapping[str, str] | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-wait",
        description="Wait until Herdr agents settle (barrier over ALL targets by default).",
        epilog=(
            "exit status: 0 settled, 1 herdr failure or timeout, "
            "2 usage, precondition, or unsatisfiable wait (revision 0 targets), "
            "3 a target needs human input\n\n" + METHOD_CONSTRAINT_EPILOG
        ),
    )
    _ = parser.add_argument("targets", nargs="*", metavar="TARGET", help="agent names or pane ids")
    _ = parser.add_argument(
        "--any",
        action="store_true",
        help="exit 0 when ANY target settles instead of ALL (default is barrier mode)",
    )
    add_shared_argument(
        parser,
        "until",
        default=[],
        help=f"exact state to match, repeatable (default: {', '.join(DEFAULT_SETTLED)})",
    )
    add_shared_argument(
        parser,
        "timeout",
        default=DEFAULT_TIMEOUT_MS,
        help=f"watchdog: fail after this many milliseconds (default {DEFAULT_TIMEOUT_MS})",
    )
    _ = parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL_S,
        metavar="SEC",
        help=f"poll period in seconds (default {DEFAULT_INTERVAL_S})",
    )
    _ = parser.add_argument(
        "--hold-interval",
        type=float,
        default=DEFAULT_HOLD_WARN_INTERVAL_S,
        metavar="SEC",
        help=f"heartbeat period in seconds for held revision 0 targets (default {DEFAULT_HOLD_WARN_INTERVAL_S})",
    )

    _ = parser.add_argument(
        "--stale-after",
        type=float,
        default=None,
        metavar="SEC",
        help=(
            "opt-in staleness advisory: report a target once per stall episode (status and "
            "revision unchanged for SEC seconds; the window restarts each time the "
            "status/revision pair changes and starts at the first sighting, so an already-stalled "
            "target still waits a full window); warning only, never kills, retries, or restarts"
        ),
    )
    add_shared_argument(parser, "json", help="print a machine-readable summary")
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
    obs = observe_agent(herdr, target, env)
    return Snapshot(
        target=obs.target,
        status=obs.status,
        revision=obs.revision,
        session=obs.session,
        tokens=obs.tokens,
    )


def is_settled(snap: Snapshot, wanted: Sequence[str]) -> bool:
    """Check if agent is settled: in wanted states, recognized, and without active subagents."""
    return is_agent_settled(snap, wanted)


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
        lines.append(
            "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)).rstrip()
        )
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
                            "tokens": dict(snap.tokens) if snap.tokens is not None else None,
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
    if options.hold_interval <= 0:
        raise UsageError(f"--hold-interval {options.hold_interval} is not positive")

    if options.stale_after is not None:
        if not math.isfinite(options.stale_after):
            raise UsageError(
                f"--stale-after must be a finite number of seconds, not {options.stale_after:g}"
            )
        if options.stale_after <= 0:
            raise UsageError(f"--stale-after {options.stale_after} is not positive")
    if len(set(options.targets)) != len(options.targets):
        raise UsageError("duplicate TARGETs; list each agent once")
    wanted = resolve_until(options.until)
    herdr = find_herdr(env)

    start = time.monotonic()
    deadline = start + options.timeout / 1000.0
    snaps: list[Snapshot] = []
    warned: set[str] = set()
    held_targets: set[str] = set()
    hold_start: dict[str, float] = {}
    hold_last_warn: dict[str, float] = {}

    stall_seen: dict[str, tuple[str, str | None]] = {}
    stall_since: dict[str, float] = {}
    stall_reported: set[str] = set()
    try:
        agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
        for a in agents:
            name = entry_optional_text(a, "name")
            pid = entry_optional_text(a, "pane_id")
            kind = entry_optional_text(a, "agent")
            for target in options.targets:
                if (target == name or target == pid) and kind == "agy":
                    if target not in warned:
                        warned.add(target)
                        print(
                            f"herdr-wait: target {target!r} is an 'agy' agent.\n"
                            "herdr-wait: agents with background subagents (e.g. agy) report idle while subagents work; "
                            "weakly-recognized agents do not advance revision and cannot be observed to completion via herdr-wait.\n"
                            "herdr-wait: Dispatch & Yield (herdr-dispatch + herdr-reply) is REQUIRED; herdr-wait cannot observe them to completion.",
                            file=sys.stderr,
                        )
    except Exception:
        pass

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
        held_now = {
            snap.target: snap
            for snap in snaps
            if snap.status in wanted and not is_recognized(snap) and not has_active_subagents(snap)
        }
        # A revision-0 target never advances to recognized, so ANY held target
        # dooms the ALL barrier and ALL held doom --any too: fail fast, never
        # hang silently to the watchdog on weak recognition.
        unsatisfiable = bool(held_now) and (not options.any or len(held_now) == len(snaps))
        for target in sorted(held_now.keys()):
            snap = held_now[target]
            held_targets.add(target)
            if target not in hold_start:
                hold_start[target] = now
                hold_last_warn[target] = now
                if target not in warned:
                    warned.add(target)
                    action = (
                        "exiting now instead of holding to the watchdog"
                        if unsatisfiable
                        else "holding wait loop"
                    )
                    print(
                        f"herdr-wait: {target} reports {snap.status} with revision 0 (unrecognized; typical of agy).\n"
                        "herdr-wait: agents with background subagents (e.g. agy) report idle while subagents work; weakly-recognized agents do not advance revision and cannot be observed to completion via herdr-wait.\n"
                        "herdr-wait: Dispatch & Yield (herdr-dispatch + herdr-reply) is REQUIRED, not advisory; herdr-wait cannot observe them to completion.\n"
                        f"herdr-wait: {action}; dispatch and yield turn for herdr-reply callback instead.",
                        file=sys.stderr,
                    )
            else:
                elapsed_hold = now - hold_start[target]
                since_last_warn = now - hold_last_warn[target]
                if since_last_warn >= options.hold_interval:
                    hold_last_warn[target] = now
                    elapsed_desc = (
                        f"{int(elapsed_hold)}s" if elapsed_hold >= 1.0 else f"{elapsed_hold:.2f}s"
                    )
                    print(
                        f"herdr-wait: holding {target} ({snap.status}, revision 0) for {elapsed_desc} (still waiting)",
                        file=sys.stderr,
                    )

        for target in list(hold_start.keys()):
            if target not in held_now:
                del hold_start[target]
                _ = hold_last_warn.pop(target, None)

        if options.stale_after is not None:
            for snap in snaps:
                target = snap.target
                observed = (snap.status, snap.revision)
                settled_now = is_settled(snap, wanted) or target in held_now
                if settled_now or stall_seen.get(target) != observed:
                    # Progress, a stop, or the first sighting: open a fresh episode.
                    stall_seen[target] = observed
                    stall_since[target] = now
                    stall_reported.discard(target)
                    continue
                stalled_for = now - stall_since[target]
                if target in stall_reported or stalled_for < options.stale_after:
                    continue
                stall_reported.add(target)
                print(
                    f"herdr-wait: staleness advisory: {target} has held status {snap.status} "
                    f"revision {snap.revision or '-'} for {stalled_for:.1f}s "
                    f"(--stale-after {options.stale_after:g}s); nothing has advanced it in that window.\n"
                    "herdr-wait: staleness advisory: collect evidence yourself (read the pane, prompt the "
                    "target, check its transcript). This helper never kills, retries, restarts, or interrupts "
                    "a target and never establishes a result; for a pane this skill did not launch, "
                    "completion is cooperative, not guaranteed.",
                    file=sys.stderr,
                )
        if unsatisfiable:
            emit(snaps, as_json=options.json)
            names = ", ".join(sorted(held_now))
            print(
                f"herdr-wait: unsatisfiable wait: {names} report a wanted state stuck at revision 0; "
                "weakly-recognized agents cannot be observed to completion by polling.\n"
                "herdr-wait: Dispatch & Yield (herdr-dispatch + herdr-reply) is REQUIRED: "
                "dispatch with herdr-prompt/herdr-dispatch, yield the turn, and await the herdr-reply callback.",
                file=sys.stderr,
            )
            return EXIT_USAGE

        matched = [snap.target for snap in snaps if is_settled(snap, wanted)]
        if options.any and matched:
            emit(snaps, as_json=options.json)
            return EXIT_OK
        if not options.any and len(matched) == len(snaps):
            emit(snaps, as_json=options.json)
            return EXIT_OK
        remaining = deadline - now
        if remaining <= 0:
            unsettled: list[str] = []
            for snap in snaps:
                desc = f"{snap.target} ({snap.status})"
                if snap.target in held_targets and not is_recognized(snap):
                    desc += (
                        " [revision 0 held; weakly-recognized agent does not settle barrier;"
                        " use dispatch & yield]"
                    )
                unsettled.append(desc)
            unsettled.sort()
            emit(snaps, as_json=options.json)
            print(
                f"herdr-wait: timed out after {options.timeout}ms "
                f"waiting for: {', '.join(unsettled)}",
                file=sys.stderr,
            )
            return EXIT_HERDR
        time.sleep(min(options.interval, remaining))


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    return entrypoint(
        "herdr-wait", build_parser, wait_agents, namespace=Options(), argv=argv, env=env
    )


if __name__ == "__main__":
    raise SystemExit(main())
