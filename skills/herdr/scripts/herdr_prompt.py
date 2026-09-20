#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""herdr-prompt — deliver one prompt payload to a Herdr agent without shell mangling.

Reads the payload verbatim from a file or stdin, hands it to
``herdr agent prompt <TARGET> <TEXT>`` as a single argv element, and forwards the wait
flags. No shell is involved, so quotes, backticks, ``$``, newlines, and code fences
survive byte-for-byte.

    herdr-prompt reviewer --file brief.md --wait --timeout 120000
    herdr-prompt reviewer --file - < brief.md
    git diff | herdr-prompt reviewer --wait

Exit status: 0 accepted (``--wait`` settled without needing input), 1 herdr failure,
2 usage or missing precondition, 3 the agent needs human input (``agent_blocked``, or
``--wait`` settled on ``blocked``).

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (  # pyright: ignore[reportImplicitRelativeImport]
    EXIT_BLOCKED,
    EXIT_OK,
    HerdrError,
    UsageError,
    decode_response,
    error_code,
    find_herdr,
    guard,
    require_herdr_env,
    run_herdr,
)

STDIN = "-"
BLOCKED = "blocked"
BLOCKED_CODE = "agent_blocked"
PROMPT_STATES = "idle, working, blocked, done, or unknown"


@dataclass
class Options:
    """CLI options; `argparse` writes into this typed namespace."""

    target: str = ""
    file: str | None = None
    wait: bool = False
    until: list[str] = field(default_factory=list)
    timeout: int | None = None
    json: bool = False
    dry_run: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-prompt",
        description="Submit a byte-exact prompt payload to a Herdr agent (no shell involved).",
        epilog=(
            "exit status: 0 accepted, 1 herdr failure, 2 usage or precondition, "
            "3 the agent needs human input"
        ),
    )
    _ = parser.add_argument("target", metavar="TARGET", help="agent name or pane id")
    _ = parser.add_argument(
        "--file",
        metavar="PATH",
        help="payload file; '-' or omitted reads stdin verbatim",
    )
    _ = parser.add_argument(
        "--wait",
        action="store_true",
        help="wait for the first settled state after submission",
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
    return parser


def read_payload(source: str | None) -> str:
    """Read the payload verbatim; only the choice of stream is validated, not its content."""
    if source is None or source == STDIN:
        if sys.stdin.isatty():
            raise UsageError(
                "no --file given and stdin is a terminal; pass --file PATH or pipe the payload"
            )
        try:
            raw = sys.stdin.buffer.read()
        except OSError as exc:
            raise UsageError(f"cannot read payload from stdin: {exc}") from exc
    else:
        try:
            raw = Path(source).read_bytes()
        except OSError as exc:
            raise UsageError(f"cannot read payload from {source!r}: {exc}") from exc

    if b"\x00" in raw:
        raise UsageError("payload contains a NUL byte, which cannot appear in an argv element")
    try:
        payload = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UsageError(f"payload is not valid UTF-8: {exc}") from exc
    if not payload.strip():
        raise UsageError("payload is empty; refusing to submit an empty prompt")
    return payload


def build_prompt_argv(
    herdr: str,
    target: str,
    payload: str,
    *,
    wait: bool,
    until: Sequence[str],
    timeout: int | None,
) -> list[str]:
    argv = [herdr, "agent", "prompt", target, payload]
    if wait:
        argv.append("--wait")
    for state in until:
        argv += ["--until", state]
    if timeout is not None:
        if timeout <= 0:
            raise UsageError(f"--timeout {timeout} is not positive")
        argv += ["--timeout", str(timeout)]
    return argv


def settled_state(raw: str) -> str | None:
    """Read `result.agent.agent_status` when herdr returned it; absence is not an error."""
    result = decode_response(raw).get("result")
    if not isinstance(result, dict):
        return None
    agent = result.get("agent")
    if not isinstance(agent, dict):
        return None
    state = agent.get("agent_status")
    return state if isinstance(state, str) and state else None


def prompt_agent(options: Options, env: Mapping[str, str]) -> int:
    require_herdr_env(env)
    herdr = find_herdr(env)
    payload = read_payload(options.file)
    argv = build_prompt_argv(
        herdr,
        options.target,
        payload,
        wait=options.wait,
        until=options.until,
        timeout=options.timeout,
    )
    if options.dry_run:
        print(json.dumps(argv))
        return EXIT_OK

    done = run_herdr(argv, env)
    if done.returncode != 0:
        detail = (done.stderr or done.stdout).strip() or f"exit status {done.returncode}"
        if error_code(done.stderr) == BLOCKED_CODE:
            print(f"herdr-prompt: {detail}", file=sys.stderr)
            return EXIT_BLOCKED
        raise HerdrError(f"herdr agent prompt failed: {detail}")

    _ = decode_response(done.stdout)
    state = settled_state(done.stdout)
    if options.json:
        print(done.stdout, end="" if done.stdout.endswith("\n") else "\n")
    else:
        size = len(payload.encode("utf-8"))
        suffix = f"  state={state}" if state else ""
        print(f"prompted {options.target}  bytes={size}{suffix}")
    return EXIT_BLOCKED if state == BLOCKED else EXIT_OK


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    return guard("herdr-prompt", lambda: prompt_agent(options, env_map))


if __name__ == "__main__":
    raise SystemExit(main())
