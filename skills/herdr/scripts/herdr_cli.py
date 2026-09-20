#!/usr/bin/env python3
"""Shared adapter for the local herdr helper scripts.

Internal — import it, do not run it. `herdr_pane.py`, `herdr_prompt.py`, and
`herdr_overview.py` all need the same four things: the `HERDR_ENV` precondition, the
location of the `herdr` binary, a way to run it, and one error/exit taxonomy. Owning them
here keeps a change to the guard, the exit statuses, or the response decoding in one place
instead of three.
"""

from __future__ import annotations

import errno
import json
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from typing import cast

EXIT_OK = 0
EXIT_HERDR = 1
EXIT_USAGE = 2
EXIT_BLOCKED = 3


class UsageError(Exception):
    """Caller misuse or a missing precondition (exit status 2)."""


class HerdrError(Exception):
    """`herdr` could not be run or answered with an unusable response (exit status 1)."""


def require_herdr_env(env: Mapping[str, str]) -> None:
    if env.get("HERDR_ENV") != "1":
        raise UsageError("not inside a Herdr-managed pane (HERDR_ENV!=1); refusing session control")


def find_herdr(env: Mapping[str, str]) -> str:
    found = shutil.which("herdr", path=env.get("PATH"))
    if found is None:
        found = env.get("HERDR_BIN_PATH") or None
    if found is None:
        raise UsageError("herdr not found on PATH (HERDR_BIN_PATH unset)")
    return found


def run_herdr(argv: Sequence[str], env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
    """Run herdr and return the process; a non-zero status is the caller's to interpret."""
    try:
        return subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            check=False,
            env=dict(env),
        )
    except OSError as exc:
        if exc.errno == errno.E2BIG:
            raise HerdrError(
                "argument list is too large (E2BIG); pass a shorter payload or a file path"
            ) from exc
        raise HerdrError(f"cannot run {argv[0]}: {exc}") from exc


def run_herdr_checked(argv: Sequence[str], env: Mapping[str, str]) -> str:
    """Run herdr, raising with its own error output when it fails; return stdout."""
    done = run_herdr(argv, env)
    if done.returncode != 0:
        detail = (done.stderr or done.stdout).strip() or f"exit status {done.returncode}"
        raise HerdrError(f"{shlex.join(argv)} failed: {detail}")
    return done.stdout


def decode_response(raw: str) -> dict[str, object]:
    """Decode a herdr JSON response object, or explain what was unreadable."""
    try:
        # json.loads is Any-typed; keep the response an unvalidated object until narrowed.
        decoded = cast(object, json.loads(raw))
    except json.JSONDecodeError as exc:
        raise HerdrError(f"herdr returned non-JSON output: {raw.strip()[:200]!r}") from exc
    if not isinstance(decoded, dict):
        raise HerdrError(f"herdr returned a non-object response: {raw.strip()[:200]!r}")
    return decoded


def payload_field(raw: str, *path: str) -> object:
    """Read a nested field from a herdr JSON response, or explain what was missing."""
    value: object = decode_response(raw)
    for key in path:
        if not isinstance(value, dict) or key not in value:
            raise HerdrError(f"herdr response missing {'.'.join(path)}: {raw.strip()[:200]}")
        value = value[key]
    return value


def entries(raw: str, *path: str) -> list[Mapping[str, object]]:
    """Read a list of objects from a herdr response, or explain what was wrong."""
    value = payload_field(raw, *path)
    if not isinstance(value, list):
        raise HerdrError(f"herdr response {'.'.join(path)} is not a list: {raw.strip()[:200]}")
    found: list[Mapping[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise HerdrError(f"herdr response {'.'.join(path)} has a non-object entry: {item!r}")
        found.append(item)
    return found


def text_field(raw: str, *path: str) -> str:
    value = payload_field(raw, *path)
    if not isinstance(value, str) or not value:
        raise HerdrError(f"herdr response field {'.'.join(path)} is not a non-empty string")
    return value


def entry_text(entry: Mapping[str, object], key: str, *, where: str) -> str:
    """Read a required string field from one list entry."""
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise HerdrError(f"{where} has no usable {key!r}")
    return value


def entry_optional_text(entry: Mapping[str, object], key: str) -> str | None:
    """Read a nullable string field from one list entry; absence is None."""
    value = entry.get(key)
    return value if isinstance(value, str) and value else None


def current_pane_id(herdr: str, env: Mapping[str, str]) -> str:
    """Resolve the calling pane through `herdr pane current --current`."""
    raw = run_herdr_checked([herdr, "pane", "current", "--current"], env)
    return text_field(raw, "result", "pane", "pane_id")


def error_code(stderr: str) -> str | None:
    """Read the error code from herdr's stderr envelope, if it carries one."""
    try:
        decoded: object = json.loads(stderr)
    except json.JSONDecodeError:
        return None
    if not isinstance(decoded, dict):
        return None
    error = decoded.get("error")
    if isinstance(error, str):
        return error
    if isinstance(error, dict):
        code = error.get("code")
        return code if isinstance(code, str) and code else None
    return None


def guard(prog: str, action: Callable[[], int]) -> int:
    """Run one helper action, mapping the shared error taxonomy onto exit statuses."""
    try:
        return action()
    except UsageError as exc:
        print(f"{prog}: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except HerdrError as exc:
        print(f"{prog}: {exc}", file=sys.stderr)
        return EXIT_HERDR
