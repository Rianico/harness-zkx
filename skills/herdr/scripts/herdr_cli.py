#!/usr/bin/env python3
"""Shared adapter for the local herdr helper scripts.

Internal — import it, do not run it. `herdr_pane.py`, `herdr_prompt.py`, and
`herdr_overview.py` all need the same four things: the `HERDR_ENV` precondition, the
location of the `herdr` binary, a way to run it, and one error/exit taxonomy. Owning them
here keeps a change to the guard, the exit statuses, or the response decoding in one place
instead of three.

The argument families that several parsers repeat live here too (`SHARED_ARGUMENTS` and
`add_shared_argument`), so a flag declared in more than one `build_parser()` cannot drift
in its dest, action, type, or default. Each caller still supplies its own measured `help`
sentence, which is why the help text is not part of the shared table.
"""

from __future__ import annotations

import errno
import json
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

EXIT_OK = 0
EXIT_HERDR = 1
EXIT_USAGE = 2
EXIT_BLOCKED = 3

KNOWN_AGENT_KINDS: frozenset[str] = frozenset(
    {
        "aider",
        "agy",
        "amp",
        "claude",
        "cline",
        "codestral",
        "codex",
        "copilot",
        "cursor",
        "devin",
        "droid",
        "gemini",
        "grok",
        "hermes",
        "kilo",
        "kimi",
        "kiro",
        "maki",
        "mastracode",
        "omp",
        "openai",
        "opencode",
        "pi",
        "qodercli",
        "qoderclicn",
        "qwen",
    }
)


class UsageError(Exception):
    """Caller misuse or a missing precondition (exit status 2)."""


class BareShellRefusal(UsageError):
    """A target resolved to a bare shell pane with no live agent (exit status 2).

    Typed so callers with a structural remedy (dispatch --auto-start) can hook
    the condition without substring-matching prose owned by this module. The
    message stays human-readable; the TYPE is the contract.
    """


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


def reply_helper() -> Path:
    """Absolute path to this tree's `herdr_reply.py`, a sibling of this module.

    The three modules that render a reply command (`herdr_bootstrap`, `herdr_prompt`,
    `herdr_reply`) each need the same value: an absolute path resolved from the tree the
    module itself lives in, never the `~/.agents/skills/herdr` symlink, which can point into
    another worktree whose `herdr_*` code may be older. Deriving it here means one definition
    they cannot drift apart from. Pure: resolves this file's own location, no I/O, no state.
    """
    return Path(__file__).resolve().parent / "herdr_reply.py"


STDIN = "-"
NUL_BYTE_MESSAGE = "payload contains a NUL byte, which cannot appear in an argv element"


def read_payload_stream(source: str | None, *, tty_refusal: str) -> bytes:
    """Read raw payload bytes from stdin (`-` or None) or a `--file` path.

    Only the choice of stream is validated here; the bytes go back to
    `decode_payload` for the shared NUL and UTF-8 checks. `tty_refusal` is the
    caller's own sentence, because each caller names a different fallback
    (`--file PATH` for prompt, `MESSAGE, --file PATH` for reply).
    """
    if source is None or source == STDIN:
        if sys.stdin.isatty():
            raise UsageError(tty_refusal)
        try:
            return sys.stdin.buffer.read()
        except OSError as exc:
            raise UsageError(f"cannot read payload from stdin: {exc}") from exc
    try:
        return Path(source).read_bytes()
    except OSError as exc:
        raise UsageError(f"cannot read payload from {source!r}: {exc}") from exc


def decode_payload(raw: bytes | str) -> str:
    """Refuse a NUL byte, then decode UTF-8. NUL is checked before decoding.

    A NUL can never appear in an argv element, and reporting it first means a
    payload that is both NUL-bearing and invalid UTF-8 names the argv-safety
    blocker rather than the codec. A `str` (a MESSAGE argument argv already
    decoded) is checked as-is; `bytes` are then decoded as UTF-8.
    """
    if isinstance(raw, bytes):
        if b"\x00" in raw:
            raise UsageError(NUL_BYTE_MESSAGE)
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UsageError(f"payload is not valid UTF-8: {exc}") from exc
    if "\x00" in raw:
        raise UsageError(NUL_BYTE_MESSAGE)
    return raw


AGENT_NAME_PATTERN = r"[a-z][a-z0-9_-]{0,31}"  # Herdr agent name: 1..32 chars


def scoped_agent_name(role: str, task_group: str | None) -> str:
    """Prefix a bare role with its task-group slug; already-scoped values pass through."""
    if not task_group:
        return role
    if role == task_group or role.startswith(f"{task_group}-"):
        return role
    return f"{task_group}-{role}"


def validate_agent_name(name: str) -> None:
    """Reject a name Herdr would refuse, before any rename is attempted."""
    if re.fullmatch(AGENT_NAME_PATTERN, name) is None:
        raise UsageError(
            f"{name!r} is not a valid agent name (want {AGENT_NAME_PATTERN} (max 32 chars))"
        )


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


def fetch_inventory(
    herdr: str, env: Mapping[str, str]
) -> tuple[list[Mapping[str, object]], list[Mapping[str, object]]]:
    """Read the pane and agent inventories once, so every identity comes from one snapshot."""
    panes = entries(run_herdr_checked([herdr, "pane", "list"], env), "result", "panes")
    agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
    return panes, agents


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


METHOD_CONSTRAINT_EPILOG = (
    "Always use harness helper scripts in skills/herdr/scripts/, "
    "never bare herdr CLI for agent communication or pane control."
)
SHELL_PROCESS_NAMES = frozenset({"zsh", "bash", "fish", "sh", "csh", "tcsh", "ksh", "dash", "nu"})


def pane_foreground_process(herdr: str, pane_id: str, env: Mapping[str, str]) -> str | None:
    """Query `herdr pane process-info --pane <pane_id>` for the foreground process name."""
    done = run_herdr([herdr, "pane", "process-info", "--pane", pane_id], env)
    if done.returncode != 0:
        return None
    try:
        decoded = decode_response(done.stdout)
        result = decoded.get("result")
        if isinstance(result, dict):
            proc_info = result.get("process_info")
            if isinstance(proc_info, dict):
                procs = proc_info.get("foreground_processes")
                if isinstance(procs, list) and procs:
                    for p in procs:
                        if isinstance(p, dict) and p.get("name"):
                            return str(p["name"])
    except Exception:
        pass
    return None


def detect_agent_clues(
    pane: Mapping[str, object],
    target: str | None = None,
    foreground_proc: str | None = None,
) -> tuple[str, str]:
    """Detect previous agent clues (name, kind) from a pane's fields, title, or label."""
    pane_id = entry_optional_text(pane, "pane_id") or ""
    label = entry_optional_text(pane, "label")
    title = entry_optional_text(pane, "title")
    agent_attr = entry_optional_text(pane, "agent")

    suggested_name = "<name>"
    if label:
        suggested_name = label
    elif target and target != pane_id:
        suggested_name = target

    suggested_kind = "<kind>"
    if agent_attr:
        if agent_attr.lower() in KNOWN_AGENT_KINDS:
            suggested_kind = agent_attr.lower()
        else:
            suggested_kind = agent_attr
    elif title:
        tokens = re.findall(r"[a-zA-Z0-9_-]+", title.lower())
        for k in KNOWN_AGENT_KINDS:
            if k in tokens or k in title.lower():
                suggested_kind = k
                break

    if suggested_kind == "<kind>" and label:
        tokens = re.findall(r"[a-zA-Z0-9]+", label.lower())
        for k in KNOWN_AGENT_KINDS:
            if k in tokens:
                suggested_kind = k
                break

    if suggested_kind == "<kind>" and target:
        tokens = re.findall(r"[a-zA-Z0-9]+", target.lower())
        for k in KNOWN_AGENT_KINDS:
            if k in tokens:
                suggested_kind = k
                break

    if suggested_kind == "<kind>" and foreground_proc and foreground_proc in KNOWN_AGENT_KINDS:
        suggested_kind = foreground_proc

    return suggested_name, suggested_kind


@dataclass(frozen=True)
class ShellPaneInfo:
    pane_id: str
    label: str | None
    foreground_proc: str | None
    suggested_name: str
    suggested_kind: str
    is_label_match: bool


def format_shell_pane_diagnostic(
    *,
    target: str,
    pane_id: str,
    label: str | None,
    foreground_proc: str | None,
    is_label_match: bool = False,
    suggested_name: str | None = None,
    suggested_kind: str | None = None,
) -> str:
    proc_desc = foreground_proc or "shell / unknown"
    label_desc = f" (label: {label!r})" if label else ""
    if is_label_match:
        headline = (
            f"target {target!r} matches pane {pane_id}{label_desc}, "
            f"but no live agent is running in this pane (foreground process: {proc_desc})."
        )
    else:
        headline = (
            f"target pane {pane_id}{label_desc} has no live agent "
            f"(foreground process: {proc_desc})."
        )
    name = suggested_name or (label if label else (target if target != pane_id else "<name>"))
    kind = suggested_kind or "<kind>"
    recovery_cmd = f"herdr agent start {name} --kind {kind} --pane {pane_id}"
    return (
        f"{headline}\n"
        "Refusing injection: injecting prompts into a raw shell pane executes prose as commands.\n"
        "Guidance and alternatives:\n"
        f"  1. Start an agent: {recovery_cmd}\n"
        "  2. Queue/watch: wait for agent to start or monitor pane with herdr pane wait-output\n"
        "  3. Graceful abort: if caller/callee exited, abort gracefully\n"
        "  4. Safety warning: never fall back to bare pane send-text or pane send-keys into a shell pane.\n"
        f"Suggested recovery: {recovery_cmd}"
    )


def _pane_has_live_agent(p: Mapping[str, object], agents: Sequence[Mapping[str, object]]) -> bool:
    pid = entry_optional_text(p, "pane_id")
    if pid and any(entry_optional_text(a, "pane_id") == pid for a in agents):
        return True
    status = entry_optional_text(p, "agent_status")
    return bool(entry_optional_text(p, "agent")) and status in (
        "idle",
        "working",
        "done",
        "blocked",
    )


def inspect_target_shell_pane(
    herdr: str, target: str, env: Mapping[str, str]
) -> ShellPaneInfo | None:
    """Inspect pane list, agent list, and process-info to detect an open shell pane without a live agent."""
    try:
        panes = entries(run_herdr_checked([herdr, "pane", "list"], env), "result", "panes")
        agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
    except HerdrError:
        return None

    agent_names = {entry_optional_text(a, "name") for a in agents if entry_optional_text(a, "name")}
    agent_panes = {
        entry_optional_text(a, "pane_id") for a in agents if entry_optional_text(a, "pane_id")
    }
    if target in agent_names or target in agent_panes:
        return None

    # Check if target is a pane_id in panes
    for p in panes:
        pid = entry_optional_text(p, "pane_id")
        if pid is not None and pid == target:
            if not _pane_has_live_agent(p, agents):
                label = entry_optional_text(p, "label")
                proc = pane_foreground_process(herdr, pid, env)
                s_name, s_kind = detect_agent_clues(p, target, proc)
                return ShellPaneInfo(
                    pane_id=pid,
                    label=label,
                    foreground_proc=proc,
                    suggested_name=s_name,
                    suggested_kind=s_kind,
                    is_label_match=False,
                )

    # Check if target is a pane label in panes
    for p in panes:
        label = entry_optional_text(p, "label")
        if label == target:
            pid = entry_optional_text(p, "pane_id")
            if pid is not None:
                if not _pane_has_live_agent(p, agents):
                    proc = pane_foreground_process(herdr, pid, env)
                    s_name, s_kind = detect_agent_clues(p, target, proc)
                    return ShellPaneInfo(
                        pane_id=pid,
                        label=label,
                        foreground_proc=proc,
                        suggested_name=s_name,
                        suggested_kind=s_kind,
                        is_label_match=True,
                    )

    # Check if target matches pane title
    for p in panes:
        title = entry_optional_text(p, "title")
        if title and target in title:
            pid = entry_optional_text(p, "pane_id")
            if pid is not None:
                if not _pane_has_live_agent(p, agents):
                    proc = pane_foreground_process(herdr, pid, env)
                    s_name, s_kind = detect_agent_clues(p, target, proc)
                    return ShellPaneInfo(
                        pane_id=pid,
                        label=entry_optional_text(p, "label"),
                        foreground_proc=proc,
                        suggested_name=s_name,
                        suggested_kind=s_kind,
                        is_label_match=False,
                    )

    return None


def diagnose_target_pane(herdr: str, target: str, env: Mapping[str, str]) -> str | None:
    """Inspect pane list, agent list, and process-info to diagnose a non-agent target."""
    info = inspect_target_shell_pane(herdr, target, env)
    if info is None:
        return None
    return format_shell_pane_diagnostic(
        target=target,
        pane_id=info.pane_id,
        label=info.label,
        foreground_proc=info.foreground_proc,
        is_label_match=info.is_label_match,
        suggested_name=info.suggested_name,
        suggested_kind=info.suggested_kind,
    )


def diagnose_agent_not_found(herdr: str, target: str, env: Mapping[str, str]) -> str | None:
    return diagnose_target_pane(herdr, target, env)


def verify_target_not_bare_shell(herdr: str, target: str, env: Mapping[str, str]) -> None:
    diag = diagnose_target_pane(herdr, target, env)
    if diag is not None:
        raise BareShellRefusal(diag)


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


class ArgumentSink(Protocol):
    """The `add_argument` surface an `ArgumentParser` and a mutually exclusive group share."""

    def add_argument(self, *args: str, **kwargs: Any) -> object: ...


@dataclass(frozen=True)
class SharedArgument:
    """One argument declaration that several helper parsers repeat.

    `dest` is fixed here and handed to `add_argument` explicitly, so a caller reusing a
    family can never pick a different namespace attribute by accident. `kwargs` is the rest
    of the canonical declaration. `varying` names the keys a caller may override, because
    the measured declarations differ there (for example `--role` defaults to `""` in
    bootstrap and `"assistant"` in transcript); `help` is always the caller's, since every
    script has its own sentence.
    """

    options: tuple[str, ...]
    dest: str
    kwargs: Mapping[str, object]
    varying: frozenset[str] = frozenset()


# Keyed by family. Every entry preserves the dest, action, type, metavar, nargs, required,
# and default that the declaring parsers already had at commit 630eab12; the pin in
# tests/herdr/test_herdr_cli.py freezes that per script and flag.
SHARED_ARGUMENTS: Mapping[str, SharedArgument] = {
    "json": SharedArgument(("--json",), "json", {"action": "store_true"}),
    "dry_run": SharedArgument(("--dry-run",), "dry_run", {"action": "store_true"}),
    "verbose": SharedArgument(("--verbose",), "verbose", {"action": "store_true"}),
    "wait": SharedArgument(("--wait",), "wait", {"action": "store_true"}),
    "no_wait": SharedArgument(("--no-wait",), "no_wait", {"action": "store_true"}),
    "no_caller_context": SharedArgument(
        ("--no-caller-context",), "no_caller_context", {"action": "store_true"}
    ),
    "yaml": SharedArgument(("--yaml",), "yaml", {"action": "store_true"}),
    "file": SharedArgument(("--file",), "file", {"metavar": "PATH"}),
    "label": SharedArgument(("--label",), "label", {"metavar": "LABEL"}),
    "model": SharedArgument(("--model",), "model", {"metavar": "MODEL", "default": None}),
    "cwd": SharedArgument(("--cwd",), "cwd", {"metavar": "DIR", "default": None}),
    "pane": SharedArgument(("--pane",), "pane", {"metavar": "ID"}, frozenset({"required"})),
    "task_group": SharedArgument(
        ("--task-group",),
        "task_group",
        {"metavar": "SLUG", "default": None},
        frozenset({"metavar"}),
    ),
    "role": SharedArgument(
        ("--role",),
        "role",
        {"metavar": "ROLE", "default": None},
        frozenset({"metavar", "default"}),
    ),
    "auto_start": SharedArgument(
        ("--auto-start",), "auto_start", {"metavar": "KIND", "default": None}
    ),
    "tab": SharedArgument(
        ("--tab",),
        "tab",
        {"metavar": "NAME", "default": None},
        frozenset({"metavar", "nargs", "const"}),
    ),
    "until": SharedArgument(
        ("--until",),
        "until",
        {"action": "append", "metavar": "STATUS", "default": None},
        frozenset({"default"}),
    ),
    "timeout": SharedArgument(
        ("--timeout",),
        "timeout",
        {"type": int, "metavar": "MS", "default": None},
        frozenset({"default"}),
    ),
    "settle": SharedArgument(
        ("--settle",),
        "settle",
        {"type": float, "metavar": "SEC", "default": None},
        frozenset({"default"}),
    ),
    "limit": SharedArgument(("--limit",), "limit", {"type": int, "metavar": "N", "default": 20}),
}


def add_shared_argument(
    parser: ArgumentSink,
    family: str,
    *,
    help: str,
    short: str | None = None,
    **varying: object,
) -> None:
    """Declare one shared family on `parser`, keeping its dest, action, type, and default.

    `family` indexes `SHARED_ARGUMENTS`, so a typo raises `KeyError` at parser build time
    instead of silently declaring nothing. `help` is required because every caller owns its
    own sentence; only the keys in the family's `varying` set may be overridden, and any
    other keyword raises `TypeError`, which is what stops a caller from changing `dest`.
    `short` adds a one-letter alias (`-l` for `--label`); the dest still comes from the
    table, so the alias cannot move the namespace attribute.
    """
    spec = SHARED_ARGUMENTS[family]
    unexpected = set(varying) - spec.varying
    if unexpected:
        raise TypeError(f"{family}: not overridable: {', '.join(sorted(unexpected))}")
    options = (short, *spec.options) if short is not None else spec.options
    kwargs: dict[str, object] = dict(spec.kwargs)
    kwargs.update(varying)
    _ = parser.add_argument(*options, dest=spec.dest, help=help, **kwargs)
