#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""herdr-transcript — extract clean assistant text from a Herdr agent's session file.

Resolves the session path via ``herdr agent get <TARGET>``
(``result.agent.agent_session.value``) and pulls assistant text out of the
session JSONL, skipping terminal artifacts (spinners, status bars, alternate
screen) and tool-call envelope noise. Understands Pi JSONL
(``{"type": "message", "message": {"role", "content": [...]}}``) and Claude Code
JSONL (``{"type": "assistant", "message": {"role", "content": [...]}}``) through
one generic shape: an object with a ``message`` carrying ``role`` and
``content``, where ``content`` is text or a list of ``{"type": "text", ...}``
blocks; only ``text`` blocks are kept.

    herdr-transcript review1 --last               # latest assistant response
    herdr-transcript review1 --role user           # filter to one role
    herdr-transcript review1 --role all --json     # full conversation as JSON

Exit status: 0 extracted (session file, or pane snapshot when the record carries
no session path), 1 herdr failure or nothing to extract, 2 usage or missing precondition.

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (  # pyright: ignore[reportImplicitRelativeImport]
    EXIT_OK,
    HerdrError,
    UsageError,
    decode_response,
    entry_optional_text,
    find_herdr,
    guard,
    require_herdr_env,
    run_herdr,
    run_herdr_checked,
)


@dataclass
class Options:
    """CLI options; `argparse` writes into this typed namespace."""

    target: str | None = None
    last: bool = False
    role: str = "assistant"
    json: bool = False
    lines: int = 120
    source: str = "recent-unwrapped"


@dataclass
class Message:
    """One extracted (role, text) pair from the session file."""

    role: str
    text: str


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-transcript",
        description="Extract clean assistant text from a Herdr agent's session JSONL.",
        epilog="exit status: 0 extracted, 1 herdr failure or nothing to extract, 2 usage",
    )
    _ = parser.add_argument("target", nargs="?", metavar="TARGET", help="agent name or pane id")
    _ = parser.add_argument(
        "--last", action="store_true", help="print only the final matching message"
    )
    _ = parser.add_argument(
        "--role",
        default="assistant",
        metavar="ROLE",
        help="keep only this role ('all' keeps every role; default assistant)",
    )
    _ = parser.add_argument("--json", action="store_true", help="print messages as a JSON array")
    _ = parser.add_argument(
        "--lines",
        type=int,
        default=120,
        metavar="N",
        help="pane snapshot rows for the no-session fallback (default 120)",
    )
    _ = parser.add_argument(
        "--source",
        default="recent-unwrapped",
        metavar="SOURCE",
        help="pane snapshot source for the no-session fallback",
    )
    return parser


def resolve_session(herdr: str, target: str, env: Mapping[str, str]) -> str:
    """Read `result.agent.agent_session.value` for one target via `herdr agent get`."""
    raw = run_herdr_checked([herdr, "agent", "get", target], env)
    result = decode_response(raw).get("result")
    if not isinstance(result, dict):
        raise HerdrError(f"herdr agent get {target} returned no result")
    agent = result.get("agent")
    if not isinstance(agent, dict):
        raise HerdrError(f"herdr agent get {target} returned no agent record")
    session_raw = agent.get("agent_session")
    if isinstance(session_raw, dict):
        path = entry_optional_text(session_raw, "value")
    elif isinstance(session_raw, str) and session_raw:
        path = session_raw
    else:
        path = None
    if not path:
        raise HerdrError(
            f"agent {target} carries no agent_session path; fall back to "
            f"herdr agent read {target} --source recent-unwrapped --lines 120"
        )
    return path


def fallback_agent_read(
    herdr: str, target: str, env: Mapping[str, str], *, source: str, lines: int
) -> int:
    """Print the pane snapshot when the agent owns no session file."""
    done = run_herdr(
        [herdr, "agent", "read", target, "--source", source, "--lines", str(lines)], env
    )
    if done.returncode != 0:
        detail = (done.stderr or done.stdout).strip() or f"exit status {done.returncode}"
        raise HerdrError(f"herdr agent read {target} failed: {detail}")
    print(done.stdout, end="" if done.stdout.endswith("\n") else "\n")
    return EXIT_OK


def block_text(content: object) -> str | None:
    """Pull clean text from a message `content`: a bare string or text blocks only."""
    if isinstance(content, str):
        text = content.strip()
        return text or None
    if not isinstance(content, list):
        return None
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "text":
            continue  # skip tool_use, thinking, and other envelope noise
        text = block.get("text")
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())
    joined = "\n".join(parts).strip()
    return joined or None


def line_message(line: str) -> Message | None:
    """Parse one session JSONL line into a Message, or None when it carries no text."""
    try:
        decoded: object = json.loads(line)
    except json.JSONDecodeError:
        return None
    if not isinstance(decoded, dict):
        return None
    message = decoded.get("message")
    role: object = None
    content: object = None
    if isinstance(message, dict):
        role = message.get("role")
        content = message.get("content")
    if not isinstance(role, str) or not role:
        fallback = decoded.get("role")
        role = fallback if isinstance(fallback, str) and fallback else None
    if not isinstance(role, str) or not role:
        return None
    text = block_text(content)
    if text is None:
        return None
    return Message(role=role, text=text)


def extract_messages(raw: str) -> list[Message]:
    """Parse a whole session file into (role, text) messages, skipping blank lines."""
    return [
        message
        for line in raw.splitlines()
        if line.strip() and (message := line_message(line)) is not None
    ]


def select(messages: Sequence[Message], *, role: str, last: bool) -> list[Message]:
    """Filter by role (`all` keeps everything), then keep only the final one for `--last`."""
    kept = [message for message in messages if role == "all" or message.role == role]
    if last and kept:
        return [kept[-1]]
    return kept


def transcript(options: Options, env: Mapping[str, str]) -> int:
    require_herdr_env(env)
    if not options.target:
        raise UsageError("pass TARGET (agent name or pane id)")
    if not options.role.strip():
        raise UsageError("--role must not be blank (use 'all' for every role)")
    herdr = find_herdr(env)
    if options.lines <= 0:
        raise UsageError("--lines must be positive")
    try:
        path = resolve_session(herdr, options.target, env)
    except HerdrError as exc:
        if "no agent_session path" not in str(exc):
            raise
        print(f"herdr-transcript: {exc}; reading pane instead", file=sys.stderr)
        return fallback_agent_read(
            herdr, options.target, env, source=options.source, lines=options.lines
        )
    try:
        with open(path, encoding="utf-8") as handle:
            raw = handle.read()
    except OSError as exc:
        raise HerdrError(f"cannot read session file {path!r}: {exc}") from exc
    chosen = select(extract_messages(raw), role=options.role, last=options.last)
    if not chosen:
        qualifier = f" with role {options.role!r}" if options.role != "all" else ""
        raise HerdrError(f"session file {path!r} holds no extractable messages{qualifier}")
    if options.json:
        print(json.dumps([{"role": item.role, "text": item.text} for item in chosen]))
    elif len(chosen) == 1:
        print(chosen[0].text)
    else:
        print("\n\n---\n\n".join(item.text for item in chosen))
    return EXIT_OK


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    return guard("herdr-transcript", lambda: transcript(options, env_map))


if __name__ == "__main__":
    raise SystemExit(main())
