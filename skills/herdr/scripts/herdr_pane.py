#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""herdr-pane — create one Herdr pane from one direction argument.

Confirms the caller lives inside a Herdr-managed pane (``HERDR_ENV=1``), resolves the
target pane, maps the direction word to ``herdr pane split --direction``, and prints the
new pane id.

    herdr-pane vertical      stack a new pane below the caller
    herdr-pane horizontal    place a new pane right of the caller
    herdr-pane               pick by caller aspect ratio (wide -> right, tall -> down)

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import os
import shlex
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (  # pyright: ignore[reportImplicitRelativeImport]
    EXIT_OK,
    HerdrError,
    UsageError,
    current_pane_id,
    find_herdr,
    guard,
    payload_field,
    require_herdr_env,
    run_herdr_checked,
    text_field,
)

DIRECTION_ALIASES = {
    "vertical": "down",
    "vert": "down",
    "v": "down",
    "down": "down",
    "below": "down",
    "under": "down",
    "underneath": "down",
    "stack": "down",
    "stacked": "down",
    "horizontal": "right",
    "horiz": "right",
    "h": "right",
    "right": "right",
    "side": "right",
    "beside": "right",
    "alongside": "right",
}


@dataclass
class Options:
    """CLI options; `argparse` writes into this typed namespace."""

    direction: str | None = None
    pane: str | None = None
    cwd: str | None = None
    ratio: float | None = None
    env: list[str] = field(default_factory=list)
    focus: bool = False
    no_focus: bool = False
    json: bool = False
    dry_run: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-pane",
        description="Split the caller's Herdr pane in the requested direction.",
    )
    _ = parser.add_argument(
        "direction",
        nargs="?",
        metavar="DIRECTION",
        help="vertical (down) / horizontal (right); omit to pick by pane aspect ratio",
    )
    _ = parser.add_argument(
        "--pane", metavar="ID", help="split this pane instead of the calling pane"
    )
    _ = parser.add_argument(
        "--cwd", metavar="DIR", help="working directory for the new pane (default: $PWD)"
    )
    _ = parser.add_argument(
        "--ratio", type=float, metavar="FLOAT", help="new-pane size ratio, e.g. 0.3"
    )
    _ = parser.add_argument(
        "--env",
        action="append",
        metavar="KEY=VALUE",
        help="environment variable for the new pane (repeatable)",
    )
    focus = parser.add_mutually_exclusive_group()
    _ = focus.add_argument("--focus", action="store_true", help="move focus to the new pane")
    _ = focus.add_argument(
        "--no-focus",
        action="store_true",
        help="keep focus in the calling pane (default)",
    )
    _ = parser.add_argument("--json", action="store_true", help="print herdr's raw JSON response")
    _ = parser.add_argument("--dry-run", action="store_true", help="print the command, run nothing")
    return parser


def normalize_direction(token: str) -> str:
    """Map a direction word to a `herdr pane split --direction` value."""
    direction = DIRECTION_ALIASES.get(token.strip().lower())
    if direction is None:
        raise UsageError(f"unknown direction {token!r}: want vertical (down) or horizontal (right)")
    return direction


def resolve_cwd(requested: str | None, env: Mapping[str, str]) -> str:
    cwd = requested or env.get("PWD") or os.getcwd()
    if not Path(cwd).is_dir():
        raise UsageError(f"--cwd {cwd!r} is not an existing directory")
    return cwd


def pane_size(pane_id: str, herdr: str, env: Mapping[str, str]) -> tuple[int, int]:
    raw = run_herdr_checked([herdr, "pane", "layout", "--pane", pane_id], env)
    panes = payload_field(raw, "result", "layout", "panes")
    if not isinstance(panes, list):
        raise HerdrError(f"pane layout is not a pane list: {raw.strip()[:200]}")
    for entry in panes:
        if not isinstance(entry, dict) or entry.get("pane_id") != pane_id:
            continue
        rect = entry.get("rect")
        if not isinstance(rect, dict):
            continue
        width, height = rect.get("width"), rect.get("height")
        if not isinstance(width, int) or not isinstance(height, int):
            raise HerdrError(f"pane {pane_id} layout rect is not numeric: {rect!r}")
        return width, height
    raise HerdrError(f"pane {pane_id} was not present in its own layout response")


def auto_direction(pane_id: str, herdr: str, env: Mapping[str, str]) -> str:
    """Wide pane -> right; narrow or tall pane -> down."""
    width, height = pane_size(pane_id, herdr, env)
    return "right" if width > height else "down"


def build_split_argv(
    herdr: str,
    pane_id: str,
    direction: str,
    *,
    cwd: str,
    ratio: float | None,
    extra_env: Sequence[str],
    focus: bool,
) -> list[str]:
    argv = [herdr, "pane", "split", "--pane", pane_id, "--direction", direction]
    if cwd:
        argv += ["--cwd", cwd]
    if ratio is not None:
        if not 0.0 < ratio < 1.0:
            raise UsageError(f"--ratio {ratio} is out of range: want 0 < ratio < 1")
        argv += ["--ratio", f"{ratio:g}"]
    for item in extra_env:
        if "=" not in item:
            raise UsageError(f"--env {item!r} is malformed: want KEY=VALUE")
        argv += ["--env", item]
    argv.append("--focus" if focus else "--no-focus")
    return argv


def format_summary(new_pane: str, direction: str, caller: str, cwd: str, focus: bool) -> str:
    return (
        f"new pane {new_pane}  direction={direction}  caller={caller}  "
        f"cwd={cwd}  focus={'new pane' if focus else 'caller'}"
    )


def split_pane(options: Options, env: Mapping[str, str]) -> int:
    require_herdr_env(env)
    herdr = find_herdr(env)
    cwd = resolve_cwd(options.cwd, env)
    caller = options.pane or current_pane_id(herdr, env)
    direction = (
        normalize_direction(options.direction)
        if options.direction
        else auto_direction(caller, herdr, env)
    )
    argv = build_split_argv(
        herdr,
        caller,
        direction,
        cwd=cwd,
        ratio=options.ratio,
        extra_env=options.env,
        focus=options.focus,
    )
    if options.dry_run:
        print(shlex.join(argv))
        return EXIT_OK
    raw = run_herdr_checked(argv, env)
    if options.json:
        print(raw, end="" if raw.endswith("\n") else "\n")
        return EXIT_OK
    print(
        format_summary(
            text_field(raw, "result", "pane", "pane_id"), direction, caller, cwd, options.focus
        )
    )
    return EXIT_OK


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    return guard("herdr-pane", lambda: split_pane(options, env_map))


if __name__ == "__main__":
    raise SystemExit(main())
