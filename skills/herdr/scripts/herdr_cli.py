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

The typed response layer (`PaneInfo`, `TabInfo`, `AgentInfo`, `WorkspaceInfo`, and the verb
wrappers that return them) admits daemon JSON through one validating parser per shape, so a
caller reads attributes instead of re-deriving field names and types from string maps.
"""

from __future__ import annotations

import argparse
import errno
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
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


LANE_DIR_ENV = "HERDR_LANE_DIR"
BRANCH_UNSAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


class LaneAnchorError(UsageError):
    """No lane state anchor could be resolved (exit status 2).

    A lane's state must resolve to one path for the two agents answering each other
    inside it. Refusing loudly, naming the missing anchors, beats guessing a directory
    that nothing else reads (#229); `PWD` is not an anchor for the same reason.
    """


def git_common_dir(env: Mapping[str, str]) -> Path:
    """Absolute path to the git directory every worktree of this repository shares.

    `--path-format=absolute` answers inside a bare repository too, where `--show-toplevel`
    fails with "this operation must be run in a work tree" and the plain flag returns `.`,
    which used to collapse a bare repo's root onto the git directory itself (#207).
    """
    done = run_herdr(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], env)
    if done.returncode == 0 and done.stdout.strip():
        return Path(os.path.realpath(done.stdout.strip()))
    raw = run_herdr_checked(["git", "rev-parse", "--git-common-dir"], env).strip()
    common = Path(raw)
    if not common.is_absolute():
        top = run_herdr_checked(["git", "rev-parse", "--show-toplevel"], env).strip()
        common = Path(top).resolve() / common
    return Path(os.path.realpath(common))


def git_repo_root(env: Mapping[str, str]) -> Path:
    """Absolute path to the main worktree root, even when called from a linked worktree."""
    common = git_common_dir(env)
    return common.parent if common.name == ".git" else common


def resolve_lane_base_dir(env: Mapping[str, str]) -> Path:
    """The directory one lane's shared state lives in: `HERDR_LANE_DIR`, else the repo root.

    The explicit anchor wins, so a pane provisioned by `herdr-pane` seats its callee's
    store deliberately instead of letting the callee derive its own. Without it, the
    repository root that the git common directory sits in is the one path every worktree
    and every nested subdirectory of this repository agrees on. That root is what
    `git_repo_root` derives, and it is the repository root only when the common directory
    is named `.git`. For a bare repository, a submodule (common directory under the
    superproject's `.git/modules/…`), or `git init --separate-git-dir`, the common
    directory itself is the base. It can live inside a git directory, and it is still one
    path per repository.

    `PWD` and the process cwd are deliberately not anchors: a dispatcher and the callee
    it dispatched to ran in different working directories, resolved different stores
    through them, and left a lease nobody could release (#229). With no anchor this
    raises `LaneAnchorError` instead of guessing.

    The result is resolved, so a caller and its callee usually agree on one spelling: an
    anchor written as a symlink or as `/tmp/...` would otherwise name the same directory as
    its `realpath` under a second string. Resolution alone is not identity — a case-insensitive
    volume keeps `MyLaneRepo` and `mylanerepo` as one file and two strings — so the lease
    comparison decides identity physically, with `os.path.samefile` (#229).
    """
    env_dir = env.get(LANE_DIR_ENV)
    if env_dir:
        return Path(env_dir).resolve()
    try:
        return git_repo_root(env).resolve()
    except HerdrError as exc:
        raise LaneAnchorError(
            "no lane state anchor: HERDR_LANE_DIR is unset and no git common dir "
            f"resolves for this working directory ({exc})"
        ) from exc


def sanitize_branch(branch: str) -> str:
    """Reduce a branch name to a filesystem-safe suffix (feat/184 -> feat-184)."""
    sanitized = BRANCH_UNSAFE_RE.sub("-", branch).strip("-.")
    return sanitized or "worktree"


def yaml_module() -> Any:
    """Import pyyaml on demand; helpers that never touch a store stay dependency-free.

    Only `claim`/`retire` (worktrees) and lease writes need the YAML database, and several
    helpers run under an inline script environment without pyyaml. Importing it at module
    scope would break importing this adapter from those helpers.
    """
    try:
        import yaml  # noqa: PLC0415 - optional dependency of the store, not of every helper
    except ModuleNotFoundError as exc:
        raise HerdrError("store access needs pyyaml; run this script with `uv run`") from exc
    return yaml


def atomic_write_bytes(path: Path, content: bytes) -> None:
    """Replace `path` with `content` atomically, so a reader never sees half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.tmp-")
    try:
        with open(fd, "wb") as handle:
            _ = handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def atomic_write_yaml(
    path: Path,
    data: Mapping[str, Any],
    *,
    default_flow_style: bool | None = None,
) -> None:
    """Serialise `data` in declaration order (`sort_keys=False`) and write it atomically.

    Key order is load-bearing for both stores: `.lane/tasks.yaml` is read by humans and by
    other agents mid-run, and reordering it on every write makes diffs unreadable. Callers
    that need block style pass `default_flow_style=False`; the default keeps pyyaml's own.
    """
    text = yaml_module().safe_dump(
        dict(data),
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=default_flow_style,
    )
    atomic_write_bytes(path, text.encode("utf-8"))


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


def failure_detail(done: subprocess.CompletedProcess[str]) -> str:
    """One-line diagnostic from a failed process, preferring stderr over stdout."""
    return (done.stderr or done.stdout).strip() or f"exit status {done.returncode}"


def run_herdr_checked(argv: Sequence[str], env: Mapping[str, str]) -> str:
    """Run herdr, raising with its own error output when it fails; return stdout."""
    done = run_herdr(argv, env)
    if done.returncode != 0:
        raise HerdrError(f"{shlex.join(argv)} failed: {failure_detail(done)}")
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


# ── typed response wrappers ────────────────────────────────────────────────────────
#
# Callers used to re-derive every daemon field from raw string maps, so a renamed or retyped
# field failed deep inside a caller. Each wrapper owns the verb, the request flags, the response
# path, and one validating parser per shape. A parse failure names the field, the response
# location, and an excerpt of what arrived instead.


@dataclass(frozen=True)
class AgentSession:
    """`AgentSessionInfo`: the session reference a pane or agent reports for resume."""

    source: str
    agent: str
    kind: str
    value: str


@dataclass(frozen=True)
class PaneScrollInfo:
    """`PaneScrollInfo`: the pane's scrollback position, in rows."""

    offset_from_bottom: int
    max_offset_from_bottom: int
    viewport_rows: int


@dataclass(frozen=True)
class PaneRect:
    """`PaneLayoutRect`: one pane's rectangle in cells."""

    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class PaneInfo:
    """`PaneInfo`: one pane's identity, focus, agent, and terminal state."""

    pane_id: str
    terminal_id: str
    workspace_id: str
    tab_id: str
    focused: bool
    agent_status: str
    revision: int
    agent: str | None
    agent_session: AgentSession | None
    cwd: str | None
    display_agent: str | None
    foreground_cwd: str | None
    label: str | None
    restore_error: str | None
    scroll: PaneScrollInfo | None
    state_labels: Mapping[str, str]
    terminal_title: str | None
    terminal_title_stripped: str | None
    title: str | None
    tokens: Mapping[str, str]


@dataclass(frozen=True)
class PaneLayoutPane:
    """`PaneLayoutPane`: one pane in a tab layout."""

    pane_id: str
    focused: bool
    rect: PaneRect


@dataclass(frozen=True)
class PaneLayout:
    """`PaneLayoutSnapshot`: the panes of one tab and their rectangles."""

    workspace_id: str
    tab_id: str
    focused_pane_id: str
    panes: tuple[PaneLayoutPane, ...]


@dataclass(frozen=True)
class TabInfo:
    """`TabInfo`: one tab's identity, focus, pane count, and agent status."""

    tab_id: str
    workspace_id: str
    number: int
    label: str
    focused: bool
    pane_count: int
    agent_status: str


@dataclass(frozen=True)
class CreatedTab:
    """The tab and root pane one `tab create` response reports."""

    tab: TabInfo
    root_pane: PaneInfo


@dataclass(frozen=True)
class AgentInfo:
    """`AgentInfo`: the agent in one pane, and its session state."""

    terminal_id: str
    agent_status: str
    workspace_id: str
    tab_id: str
    pane_id: str
    focused: bool
    revision: int
    agent: str | None
    agent_session: AgentSession | None
    completion_seq: int | None
    cwd: str | None
    display_agent: str | None
    foreground_cwd: str | None
    interactive_ready: bool | None
    launch_pending: bool | None
    name: str | None
    screen_detection_skipped: bool | None
    state_change_seq: int | None
    state_labels: Mapping[str, str]
    terminal_title: str | None
    terminal_title_stripped: str | None
    title: str | None
    tokens: Mapping[str, str]


@dataclass(frozen=True)
class WorkspaceWorktreeInfo:
    """`WorkspaceWorktreeInfo`: the worktree a workspace is bound to."""

    repo_key: str
    repo_name: str
    repo_root: str
    checkout_path: str
    is_linked_worktree: bool


@dataclass(frozen=True)
class WorkspaceInfo:
    """`WorkspaceInfo`: one workspace's identity, counts, and active tab."""

    workspace_id: str
    number: int
    label: str
    focused: bool
    pane_count: int
    tab_count: int
    active_tab_id: str
    agent_status: str
    tokens: Mapping[str, str]
    worktree: WorkspaceWorktreeInfo | None


@dataclass(frozen=True)
class PaneRead:
    """`PaneReadResult`: the snapshot text a read or match returned."""

    pane_id: str
    workspace_id: str
    tab_id: str
    source: str
    format: str
    text: str
    revision: int
    truncated: bool


@dataclass(frozen=True)
class PaneOutputMatch:
    """`output_matched`: the read whose text matched, plus the matched line when reported."""

    pane_id: str
    revision: int
    matched_line: str | None
    read: PaneRead


class NestedParser[T](Protocol):
    """A parser for one nested response object, called with its own `where` context."""

    def __call__(self, entry: Mapping[str, object], *, where: str) -> T: ...


def _excerpt(entry: Mapping[str, object]) -> str:
    """One line of the offending entry, truncated, so an error names what arrived."""
    return repr(dict(entry))[:120]


def _field_error(entry: Mapping[str, object], key: str, *, where: str, want: str) -> HerdrError:
    return HerdrError(f"{where} has no usable {key!r} ({want}): {_excerpt(entry)}")


def _required_text(entry: Mapping[str, object], key: str, *, where: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise _field_error(entry, key, where=where, want="a non-empty string")
    return value


def _required_text_allow_empty(entry: Mapping[str, object], key: str, *, where: str) -> str:
    """Read a required string that may be empty; an empty pane snapshot is a legal success."""
    value = entry.get(key)
    if not isinstance(value, str):
        raise _field_error(entry, key, where=where, want="a string")
    return value


def _required_int(entry: Mapping[str, object], key: str, *, where: str) -> int:
    value = entry.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise _field_error(entry, key, where=where, want="an integer")
    return value


def _required_bool(entry: Mapping[str, object], key: str, *, where: str) -> bool:
    value = entry.get(key)
    if not isinstance(value, bool):
        raise _field_error(entry, key, where=where, want="a boolean")
    return value


def _optional_int(entry: Mapping[str, object], key: str, *, where: str) -> int | None:
    value = entry.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise _field_error(entry, key, where=where, want="an integer or null")
    return value


def _optional_bool(entry: Mapping[str, object], key: str, *, where: str) -> bool | None:
    value = entry.get(key)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise _field_error(entry, key, where=where, want="a boolean or null")
    return value


def _string_map(entry: Mapping[str, object], key: str, *, where: str) -> Mapping[str, str]:
    """Read a string map; herdr 0.9.5 marks `state_labels`/`tokens` optional, so absence is `{}`."""
    value = entry.get(key)
    if value is None:
        return MappingProxyType({})
    if not isinstance(value, Mapping):
        raise _field_error(entry, key, where=where, want="an object of strings")
    found: dict[str, str] = {}
    for item_key, item_value in value.items():
        if not isinstance(item_key, str) or not isinstance(item_value, str):
            raise _field_error(entry, key, where=where, want="an object of strings")
        found[item_key] = item_value
    return MappingProxyType(found)


def _optional_nested[T](
    entry: Mapping[str, object],
    key: str,
    *,
    where: str,
    parse: NestedParser[T],
) -> T | None:
    """Parse an optional nested object; absence is `None`, a wrong type is refused."""
    value = entry.get(key)
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise _field_error(entry, key, where=where, want="an object")
    return parse(value, where=f"{where}.{key}")


def _nested_list[T](value: object, *, where: str, parse: NestedParser[T]) -> tuple[T, ...]:
    """Parse a required array of objects; a non-object entry names its index."""
    if not isinstance(value, list):
        raise HerdrError(f"{where} is not a list: {value!r}"[:200])
    found: list[T] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise HerdrError(f"{where}[{index}] is not an object: {item!r}")
        found.append(parse(item, where=f"{where}[{index}]"))
    return tuple(found)


def _response_object(raw: str, *path: str) -> Mapping[str, object]:
    """Read a required response object, or explain which path was missing."""
    value = payload_field(raw, *path)
    if not isinstance(value, Mapping):
        raise HerdrError(f"herdr response {'.'.join(path)} is not an object: {raw.strip()[:200]}")
    return value


def _agent_session(entry: Mapping[str, object], *, where: str) -> AgentSession:
    return AgentSession(
        source=_required_text(entry, "source", where=where),
        agent=_required_text(entry, "agent", where=where),
        kind=_required_text(entry, "kind", where=where),
        value=_required_text(entry, "value", where=where),
    )


def _pane_scroll(entry: Mapping[str, object], *, where: str) -> PaneScrollInfo:
    return PaneScrollInfo(
        offset_from_bottom=_required_int(entry, "offset_from_bottom", where=where),
        max_offset_from_bottom=_required_int(entry, "max_offset_from_bottom", where=where),
        viewport_rows=_required_int(entry, "viewport_rows", where=where),
    )


def _pane_rect(entry: Mapping[str, object], *, where: str) -> PaneRect:
    return PaneRect(
        x=_required_int(entry, "x", where=where),
        y=_required_int(entry, "y", where=where),
        width=_required_int(entry, "width", where=where),
        height=_required_int(entry, "height", where=where),
    )


def _pane_info(entry: Mapping[str, object], *, where: str) -> PaneInfo:
    """Admit one `PaneInfo`; every required field is checked, optionals degrade."""
    return PaneInfo(
        pane_id=_required_text(entry, "pane_id", where=where),
        terminal_id=_required_text(entry, "terminal_id", where=where),
        workspace_id=_required_text(entry, "workspace_id", where=where),
        tab_id=_required_text(entry, "tab_id", where=where),
        focused=_required_bool(entry, "focused", where=where),
        agent_status=_required_text(entry, "agent_status", where=where),
        revision=_required_int(entry, "revision", where=where),
        agent=entry_optional_text(entry, "agent"),
        agent_session=_optional_nested(entry, "agent_session", where=where, parse=_agent_session),
        cwd=entry_optional_text(entry, "cwd"),
        display_agent=entry_optional_text(entry, "display_agent"),
        foreground_cwd=entry_optional_text(entry, "foreground_cwd"),
        label=entry_optional_text(entry, "label"),
        restore_error=entry_optional_text(entry, "restore_error"),
        scroll=_optional_nested(entry, "scroll", where=where, parse=_pane_scroll),
        state_labels=_string_map(entry, "state_labels", where=where),
        terminal_title=entry_optional_text(entry, "terminal_title"),
        terminal_title_stripped=entry_optional_text(entry, "terminal_title_stripped"),
        title=entry_optional_text(entry, "title"),
        tokens=_string_map(entry, "tokens", where=where),
    )


def _required_nested[T](
    entry: Mapping[str, object],
    key: str,
    *,
    where: str,
    parse: NestedParser[T],
) -> T:
    """Parse a required nested object; a missing or non-object value is refused."""
    value = entry.get(key)
    if not isinstance(value, Mapping):
        raise _field_error(entry, key, where=where, want="an object")
    return parse(value, where=f"{where}.{key}")


def _pane_layout_pane(entry: Mapping[str, object], *, where: str) -> PaneLayoutPane:
    return PaneLayoutPane(
        pane_id=_required_text(entry, "pane_id", where=where),
        focused=_required_bool(entry, "focused", where=where),
        rect=_required_nested(entry, "rect", where=where, parse=_pane_rect),
    )


def _pane_layout(entry: Mapping[str, object], *, where: str) -> PaneLayout:
    return PaneLayout(
        workspace_id=_required_text(entry, "workspace_id", where=where),
        tab_id=_required_text(entry, "tab_id", where=where),
        focused_pane_id=_required_text(entry, "focused_pane_id", where=where),
        panes=_nested_list(entry.get("panes"), where=f"{where}.panes", parse=_pane_layout_pane),
    )


def _tab_info(entry: Mapping[str, object], *, where: str) -> TabInfo:
    return TabInfo(
        tab_id=_required_text(entry, "tab_id", where=where),
        workspace_id=_required_text(entry, "workspace_id", where=where),
        number=_required_int(entry, "number", where=where),
        label=_required_text(entry, "label", where=where),
        focused=_required_bool(entry, "focused", where=where),
        pane_count=_required_int(entry, "pane_count", where=where),
        agent_status=_required_text(entry, "agent_status", where=where),
    )


def _agent_info(entry: Mapping[str, object], *, where: str) -> AgentInfo:
    return AgentInfo(
        terminal_id=_required_text(entry, "terminal_id", where=where),
        agent_status=_required_text(entry, "agent_status", where=where),
        workspace_id=_required_text(entry, "workspace_id", where=where),
        tab_id=_required_text(entry, "tab_id", where=where),
        pane_id=_required_text(entry, "pane_id", where=where),
        focused=_required_bool(entry, "focused", where=where),
        revision=_required_int(entry, "revision", where=where),
        agent=entry_optional_text(entry, "agent"),
        agent_session=_optional_nested(entry, "agent_session", where=where, parse=_agent_session),
        completion_seq=_optional_int(entry, "completion_seq", where=where),
        cwd=entry_optional_text(entry, "cwd"),
        display_agent=entry_optional_text(entry, "display_agent"),
        foreground_cwd=entry_optional_text(entry, "foreground_cwd"),
        interactive_ready=_optional_bool(entry, "interactive_ready", where=where),
        launch_pending=_optional_bool(entry, "launch_pending", where=where),
        name=entry_optional_text(entry, "name"),
        screen_detection_skipped=_optional_bool(entry, "screen_detection_skipped", where=where),
        state_change_seq=_optional_int(entry, "state_change_seq", where=where),
        state_labels=_string_map(entry, "state_labels", where=where),
        terminal_title=entry_optional_text(entry, "terminal_title"),
        terminal_title_stripped=entry_optional_text(entry, "terminal_title_stripped"),
        title=entry_optional_text(entry, "title"),
        tokens=_string_map(entry, "tokens", where=where),
    )


def _workspace_worktree(entry: Mapping[str, object], *, where: str) -> WorkspaceWorktreeInfo:
    return WorkspaceWorktreeInfo(
        repo_key=_required_text(entry, "repo_key", where=where),
        repo_name=_required_text(entry, "repo_name", where=where),
        repo_root=_required_text(entry, "repo_root", where=where),
        checkout_path=_required_text(entry, "checkout_path", where=where),
        is_linked_worktree=_required_bool(entry, "is_linked_worktree", where=where),
    )


def _workspace_info(entry: Mapping[str, object], *, where: str) -> WorkspaceInfo:
    return WorkspaceInfo(
        workspace_id=_required_text(entry, "workspace_id", where=where),
        number=_required_int(entry, "number", where=where),
        label=_required_text(entry, "label", where=where),
        focused=_required_bool(entry, "focused", where=where),
        pane_count=_required_int(entry, "pane_count", where=where),
        tab_count=_required_int(entry, "tab_count", where=where),
        active_tab_id=_required_text(entry, "active_tab_id", where=where),
        agent_status=_required_text(entry, "agent_status", where=where),
        tokens=_string_map(entry, "tokens", where=where),
        worktree=_optional_nested(entry, "worktree", where=where, parse=_workspace_worktree),
    )


def _pane_read(entry: Mapping[str, object], *, where: str) -> PaneRead:
    return PaneRead(
        pane_id=_required_text(entry, "pane_id", where=where),
        workspace_id=_required_text(entry, "workspace_id", where=where),
        tab_id=_required_text(entry, "tab_id", where=where),
        source=_required_text(entry, "source", where=where),
        format=_required_text(entry, "format", where=where),
        text=_required_text_allow_empty(entry, "text", where=where),
        revision=_required_int(entry, "revision", where=where),
        truncated=_required_bool(entry, "truncated", where=where),
    )


def _focus_flags(focus: bool | None) -> list[str]:
    """`--focus` or `--no-focus` only when the caller chose; herdr keeps its own default."""
    if focus is None:
        return []
    return ["--focus"] if focus else ["--no-focus"]


def create_tab(
    herdr: str,
    env: Mapping[str, str],
    *,
    workspace_id: str | None = None,
    label: str | None = None,
    cwd: str | None = None,
    env_vars: Sequence[str] = (),
    focus: bool | None = None,
) -> CreatedTab:
    """`herdr tab create`: one call; read `.result.tab` and `.result.root_pane`.

    The creation response carries both objects, so the root pane is never re-listed with
    `pane list`. A response missing either path raises `HerdrError` naming it; the caller
    decides whether that is recoverable.
    """
    argv = [herdr, "tab", "create"]
    if workspace_id is not None:
        argv += ["--workspace", workspace_id]
    if cwd is not None:
        argv += ["--cwd", cwd]
    if label is not None:
        argv += ["--label", label]
    for item in env_vars:
        argv += ["--env", item]
    argv += _focus_flags(focus)
    raw = run_herdr_checked(argv, env)
    return CreatedTab(
        tab=_tab_info(_response_object(raw, "result", "tab"), where="tab create result.tab"),
        root_pane=_pane_info(
            _response_object(raw, "result", "root_pane"),
            where="tab create result.root_pane",
        ),
    )


def split_pane(
    herdr: str,
    env: Mapping[str, str],
    *,
    pane_id: str | None = None,
    direction: str | None = None,
    ratio: float | None = None,
    cwd: str | None = None,
    env_vars: Sequence[str] = (),
    focus: bool | None = None,
) -> PaneInfo:
    """`herdr pane split`: read the new pane from `.result.pane`.

    The target pane rides as `--pane` when the caller names one; an omitted `pane_id` leaves
    the target to herdr (the calling pane when it can resolve one, else the focused pane).
    `--ratio` rides only when set, formatted like the `%g` its callers already print, and a
    non-finite ratio is refused before any call.
    """
    if ratio is not None and not math.isfinite(ratio):
        raise UsageError(f"pane split: --ratio {ratio} is not finite")
    argv = [herdr, "pane", "split"]
    if pane_id is not None:
        argv += ["--pane", pane_id]
    if direction is not None:
        argv += ["--direction", direction]
    if ratio is not None:
        argv += ["--ratio", f"{ratio:g}"]
    if cwd is not None:
        argv += ["--cwd", cwd]
    for item in env_vars:
        argv += ["--env", item]
    argv += _focus_flags(focus)
    raw = run_herdr_checked(argv, env)
    return _pane_info(_response_object(raw, "result", "pane"), where="pane split result.pane")


def get_pane_layout(herdr: str, env: Mapping[str, str], pane_id: str) -> PaneLayout:
    """`herdr pane layout --pane`: read `.result.layout`, the panes and their rectangles."""
    raw = run_herdr_checked([herdr, "pane", "layout", "--pane", pane_id], env)
    return _pane_layout(
        _response_object(raw, "result", "layout"), where="pane layout result.layout"
    )


# Every C0 code point and DEL. `pane run` appends Enter, so one of these can end the typed
# line and let the remainder run as a second command of its own.
COMMAND_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def run_in_pane_safe(herdr: str, env: Mapping[str, str], pane_id: str, command: str) -> None:
    """`herdr pane run`: typed shell text, refused unless it is one clean command line.

    herdr appends Enter, so `command` is shell text executed by the pane's shell, not quoted
    input. Rejection, not quoting, is the guard: a newline, carriage return, NUL, or any other
    C0/DEL control character could end the line and run a second command, so it raises
    `UsageError` (exit status 2) before any argv is built or herdr is called. An empty or
    whitespace-only command is refused for the same reason. The whole command rides one argv
    element, so spaces and shell metacharacters reach the shell intact.
    """
    if not command.strip():
        raise UsageError("pane command is empty; refusing to send a bare Enter")
    found = COMMAND_CONTROL_CHARS.search(command)
    if found is not None:
        raise UsageError(
            f"pane command contains a control character (U+{ord(found.group()):04X}); "
            "herdr appends Enter, so it would run a second command"
        )
    _ = run_herdr_checked([herdr, "pane", "run", pane_id, command], env)


def get_agent(herdr: str, env: Mapping[str, str], target: str) -> AgentInfo:
    """`herdr agent get <target>`: read `.result.agent`."""
    raw = run_herdr_checked([herdr, "agent", "get", target], env)
    return _agent_info(_response_object(raw, "result", "agent"), where="agent get result.agent")


def list_agents(herdr: str, env: Mapping[str, str]) -> tuple[AgentInfo, ...]:
    """`herdr agent list`: read every `.result.agents` entry; an index names a bad one."""
    raw = run_herdr_checked([herdr, "agent", "list"], env)
    return tuple(
        _agent_info(item, where=f"agent list result.agents[{index}]")
        for index, item in enumerate(entries(raw, "result", "agents"))
    )


def list_workspaces(herdr: str, env: Mapping[str, str]) -> tuple[WorkspaceInfo, ...]:
    """`herdr workspace list`: read every `.result.workspaces` entry; an index names a bad one."""
    raw = run_herdr_checked([herdr, "workspace", "list"], env)
    return tuple(
        _workspace_info(item, where=f"workspace list result.workspaces[{index}]")
        for index, item in enumerate(entries(raw, "result", "workspaces"))
    )


def prompt_agent(
    herdr: str,
    env: Mapping[str, str],
    target: str,
    payload: str,
    *,
    wait: bool = False,
    until: Sequence[str] = (),
    timeout_ms: int | None = None,
) -> AgentInfo:
    """`herdr agent prompt <target> <payload>`: read `.result.agent`.

    `--wait`, each `--until`, and `--timeout` are sent only when set. The CLI rejects
    `--until`/`--timeout` without `--wait`, so that combination is a `UsageError` here,
    before any call.
    """
    if not wait and (until or timeout_ms is not None):
        raise UsageError("agent prompt: --until and --timeout require wait=True")
    argv = [herdr, "agent", "prompt", target, payload]
    if wait:
        argv.append("--wait")
    for status in until:
        argv += ["--until", status]
    if timeout_ms is not None:
        argv += ["--timeout", str(timeout_ms)]
    raw = run_herdr_checked(argv, env)
    return _agent_info(_response_object(raw, "result", "agent"), where="agent prompt result.agent")


def rename_pane(herdr: str, env: Mapping[str, str], pane_id: str, label: str) -> None:
    """`herdr pane rename <pane_id> <label>`: nothing is parsed.

    The schema pins no typed success result for this verb, so success is a zero exit and
    there is no return value to invent.
    """
    _ = run_herdr_checked([herdr, "pane", "rename", pane_id, label], env)


def rename_agent(herdr: str, env: Mapping[str, str], pane_id: str, name: str) -> None:
    """`herdr agent rename <pane_id> <name>`: nothing is parsed.

    The CLI target is the agent's pane id in v0.9.5, and the schema pins no typed success
    result, so success is a zero exit and there is no return value to invent.
    """
    _ = run_herdr_checked([herdr, "agent", "rename", pane_id, name], env)


def wait_pane_output(
    herdr: str,
    env: Mapping[str, str],
    pane_id: str,
    pattern: str,
    *,
    regex: bool = False,
    source: str | None = None,
    lines: int | None = None,
    timeout_ms: int | None = None,
    raw_output: bool = False,
) -> PaneOutputMatch:
    """`herdr pane wait-output <pane_id>`: read `.result` as `output_matched`.

    `pattern` is a literal substring with `--match`, or a Rust regex with `regex=True`.
    The snapshot flags and timeout are sent only when set. `.result.read` carries the matched
    snapshot text; `.result.matched_line` is optional.
    """
    argv = [herdr, "pane", "wait-output", pane_id, "--regex" if regex else "--match", pattern]
    if source is not None:
        argv += ["--source", source]
    if lines is not None:
        argv += ["--lines", str(lines)]
    if timeout_ms is not None:
        argv += ["--timeout", str(timeout_ms)]
    if raw_output:
        argv.append("--raw")
    raw = run_herdr_checked(argv, env)
    result = _response_object(raw, "result")
    return PaneOutputMatch(
        pane_id=_required_text(result, "pane_id", where="pane wait-output result"),
        revision=_required_int(result, "revision", where="pane wait-output result"),
        matched_line=entry_optional_text(result, "matched_line"),
        read=_pane_read(
            _response_object(raw, "result", "read"),
            where="pane wait-output result.read",
        ),
    )


def current_pane_id(herdr: str, env: Mapping[str, str]) -> str:
    """Resolve the calling pane through `herdr pane current --current`."""
    raw = run_herdr_checked([herdr, "pane", "current", "--current"], env)
    return text_field(raw, "result", "pane", "pane_id")


def current_workspace_id(herdr: str, env: Mapping[str, str]) -> str:
    """Resolve the calling workspace: env first, then `herdr pane current --current`."""
    env_ws = env.get("HERDR_WORKSPACE_ID")
    if env_ws:
        return env_ws
    raw = run_herdr_checked([herdr, "pane", "current", "--current"], env)
    try:
        return text_field(raw, "result", "pane", "workspace_id")
    except HerdrError:
        return text_field(raw, "result", "pane", "pane_id").split(":", 1)[0]


def fetch_inventory(
    herdr: str, env: Mapping[str, str]
) -> tuple[list[Mapping[str, object]], list[Mapping[str, object]]]:
    """Read the pane and agent inventories once, so every identity comes from one snapshot.

    Authority, when the two sources disagree (#266 T2a, TM decision):

    - The daemon snapshot (`pane list` / `agent list`) is authoritative for **live identity
      and liveness** — which panes and agents exist right now, their names, kinds, and
      revision counters.
    - `.lane/tasks.yaml` is authoritative for **leases, task state, and worktree bindings** —
      the durable facts a lane records about who owns what.

    The merge annotates the store's durable facts with the daemon's liveness; it never
    silently overrides one source with the other. A store entry whose pane the daemon does
    not list is stale, not deleted; a daemon agent with no store entry is unclaimed, not
    unowned.
    """
    panes = entries(run_herdr_checked([herdr, "pane", "list"], env), "result", "panes")
    agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
    return panes, agents


LIVENESS_LIVE = "live"
LIVENESS_STALE = "stale"
UNCLAIMED_OWNERSHIP = "unclaimed"
STORE_RELATIVE_PATH = Path(".lane") / "tasks.yaml"
STORE_SECTIONS = (("lease", "active_leases"), ("task", "tasks"))


@dataclass(frozen=True)
class Inventory:
    """One daemon snapshot, with the store's durable facts annotated by daemon liveness.

    The rule this encodes (#266 T2c, operator decision): the daemon owns live identity and
    liveness; `.lane/tasks.yaml` owns leases, task state, and worktree bindings. The merge
    only annotates, so a store record the daemon does not list is `stale` — reported, never
    deleted — and a daemon agent no store record claims is `unclaimed` — never given an
    owner, ticket, or task it did not have.

    `panes` and `agents` carry every daemon field plus `liveness`; `raw_panes`/`raw_agents`
    are the untouched payloads for callers that still parse text. `bindings` are the store
    records that name a pane, with `kind`, `key`, `liveness`, and the daemon `evidence`
    beside their original fields.
    """

    raw_panes: str
    raw_agents: str
    panes: Sequence[Mapping[str, object]]
    agents: Sequence[Mapping[str, object]]
    bindings: Sequence[Mapping[str, object]]
    unclaimed: Sequence[Mapping[str, object]]


def read_store_facts(env: Mapping[str, str]) -> Mapping[str, Any]:
    """Read the durable `.lane/tasks.yaml` mapping; an absent or unreadable store is `{}`.

    Read-only by design: the annotation must never rewrite the store, and a lane-less
    invocation (no `HERDR_LANE_DIR`, no git anchor) still gets a usable inventory.
    """
    try:
        base = resolve_lane_base_dir(env)
    except LaneAnchorError:
        return {}
    try:
        raw = (base / STORE_RELATIVE_PATH).read_text(encoding="utf-8")
    except OSError:
        return {}
    if not raw.strip():
        return {}
    try:
        yaml = yaml_module()
    except HerdrError:
        return {}
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, Mapping) else {}


def merged_panes(herdr: str, env: Mapping[str, str]) -> list[Mapping[str, object]]:
    """The pane inventory with `liveness: live` added to every record."""
    raw = run_herdr_checked([herdr, "pane", "list"], env)
    return [{**pane, "liveness": LIVENESS_LIVE} for pane in entries(raw, "result", "panes")]


def merged_agents(herdr: str, env: Mapping[str, str]) -> list[Mapping[str, object]]:
    """The agent inventory with `liveness: live` added to every record."""
    raw = run_herdr_checked([herdr, "agent", "list"], env)
    return [{**agent, "liveness": LIVENESS_LIVE} for agent in entries(raw, "result", "agents")]


def merged_inventory(herdr: str, env: Mapping[str, str]) -> Inventory:
    """Read one daemon snapshot and annotate the store's facts with daemon liveness."""
    raw_panes = run_herdr_checked([herdr, "pane", "list"], env)
    raw_agents = run_herdr_checked([herdr, "agent", "list"], env)
    panes = [{**pane, "liveness": LIVENESS_LIVE} for pane in entries(raw_panes, "result", "panes")]
    agents = [
        {**agent, "liveness": LIVENESS_LIVE} for agent in entries(raw_agents, "result", "agents")
    ]
    listed_panes = {str(pane["pane_id"]) for pane in panes if pane.get("pane_id")}
    listed_agents = {str(agent["pane_id"]) for agent in agents if agent.get("pane_id")}

    facts = read_store_facts(env)
    bindings: list[Mapping[str, object]] = []
    claimed: set[str] = set()
    for kind, section in STORE_SECTIONS:
        records = facts.get(section)
        if not isinstance(records, Mapping):
            continue
        for key, record in records.items():
            if not isinstance(record, Mapping):
                continue
            raw_pane_id = record.get("pane_id")
            pane_id = str(raw_pane_id) if raw_pane_id is not None else None
            evidence = {
                "pane_listed": pane_id in listed_panes,
                "agent_listed": pane_id in listed_agents,
            }
            live = evidence["pane_listed"] or evidence["agent_listed"]
            bindings.append(
                {
                    **record,
                    "kind": kind,
                    "key": str(key),
                    "liveness": LIVENESS_LIVE if live else LIVENESS_STALE,
                    "evidence": evidence,
                }
            )
            if pane_id is not None:
                claimed.add(pane_id)

    unclaimed = [
        {
            "pane_id": agent["pane_id"],
            "name": agent.get("name"),
            "liveness": LIVENESS_LIVE,
            "ownership": UNCLAIMED_OWNERSHIP,
        }
        for agent in agents
        if agent.get("pane_id") and str(agent["pane_id"]) not in claimed
    ]
    return Inventory(
        raw_panes=raw_panes,
        raw_agents=raw_agents,
        panes=panes,
        agents=agents,
        bindings=bindings,
        unclaimed=unclaimed,
    )


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


def read_target_inventory(
    herdr: str, env: Mapping[str, str]
) -> tuple[list[Mapping[str, object]], list[Mapping[str, object]]]:
    """Read the pane and agent inventories a target check needs, or raise `HerdrError`.

    One read with no degradation, because the two callers answer an unreadable daemon
    differently: `verify_target_not_bare_shell` must refuse, and `inspect_target_shell_pane`
    still stands down so the diagnostic callers keep their existing behaviour.
    """
    panes = entries(run_herdr_checked([herdr, "pane", "list"], env), "result", "panes")
    agents = entries(run_herdr_checked([herdr, "agent", "list"], env), "result", "agents")
    return panes, agents


def match_shell_pane(
    herdr: str,
    target: str,
    panes: Sequence[Mapping[str, object]],
    agents: Sequence[Mapping[str, object]],
    env: Mapping[str, str],
) -> ShellPaneInfo | None:
    """The pane `target` names, when no live agent occupies it; `None` for an agent target."""

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


def inspect_target_shell_pane(
    herdr: str, target: str, env: Mapping[str, str]
) -> ShellPaneInfo | None:
    """Diagnose a non-agent target; an unreadable inventory stands down to `None`."""
    try:
        panes, agents = read_target_inventory(herdr, env)
    except HerdrError:
        return None
    return match_shell_pane(herdr, target, panes, agents, env)


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


UNVERIFIED_TARGET_REMEDY = (
    "check daemon health with `herdr agent list` and `herdr pane list`, "
    "confirm the target is a listed agent, then retry"
)


def verify_target_not_bare_shell(herdr: str, target: str, env: Mapping[str, str]) -> None:
    """Refuse the send unless the daemon confirms the target is not a bare shell.

    Fail closed (#369): an inventory the daemon cannot answer — a non-zero exit, a timeout,
    unreadable or empty output, a missing field — is not evidence that the target is an
    agent, so it raises `HerdrError` (exit status 1) naming the target and the remedy.
    That stays distinct from a verified shell, which raises `BareShellRefusal` (exit status
    2) with the shell diagnostic: `herdr_dispatch` keys its auto-start remedy on that type,
    and an unreachable daemon must never trigger an agent start. A target the inventory
    does not mention at all is a send-time question, not this one, so it proceeds.
    """
    try:
        panes, agents = read_target_inventory(herdr, env)
    except HerdrError as exc:
        raise HerdrError(
            f"could not verify target {target!r} is a live agent pane, so refusing to send: "
            f"{exc}; {UNVERIFIED_TARGET_REMEDY}"
        ) from exc
    info = match_shell_pane(herdr, target, panes, agents, env)
    if info is not None:
        raise BareShellRefusal(
            format_shell_pane_diagnostic(
                target=target,
                pane_id=info.pane_id,
                label=info.label,
                foreground_proc=info.foreground_proc,
                is_label_match=info.is_label_match,
                suggested_name=info.suggested_name,
                suggested_kind=info.suggested_kind,
            )
        )


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


def entrypoint[OptionsT](
    prog: str,
    build_parser: Callable[[], argparse.ArgumentParser],
    action: Callable[[OptionsT, Mapping[str, str]], int],
    *,
    namespace: OptionsT | None = None,
    argv: Sequence[str] | None = None,
    env: Mapping[str, str] | None = None,
    before_parse: Callable[[argparse.ArgumentParser, list[str]], None] | None = None,
    timeout: tuple[type[BaseException], int] | None = None,
) -> int:
    """Parse this helper's argv and run its action under the shared error taxonomy.

    Every helper repeated the same five steps: default the environment mapping, build its
    parser, parse into its own options dataclass, run the action through `guard`, and map a
    delivery timeout onto its own exit status. Spelling that once keeps `prog: message`,
    the exit statuses, and the timeout print identical across helpers.

    `before_parse` is the caller's own pre-parse refusal (only `herdr-reply` has one), and
    `timeout` pairs the caller's exception type with its exit status. Neither changes the
    error taxonomy: `guard` still maps `UsageError`/`HerdrError`, and the timeout exception
    is re-raised untouched when it is not the declared type.
    """
    env_map = dict(os.environ if env is None else env)
    parser = build_parser()
    raw = list(sys.argv[1:] if argv is None else argv)
    if before_parse is not None:
        before_parse(parser, raw)
    options = cast(
        OptionsT, parser.parse_args(raw, namespace=cast("argparse.Namespace | None", namespace))
    )
    if timeout is None:
        return guard(prog, lambda: action(options, env_map))
    timeout_type, timeout_code = timeout
    try:
        return guard(prog, lambda: action(options, env_map))
    except BaseException as exc:  # noqa: BLE001 - re-raised unless it is the declared timeout
        if not isinstance(exc, timeout_type):
            raise
        print(f"{prog}: {exc}", file=sys.stderr)
        return timeout_code


class ArgumentSink(Protocol):
    """The `add_argument` surface an `ArgumentParser` and a mutually exclusive group share."""

    def add_argument(self, *args: str, **kwargs: Any) -> object: ...


@dataclass(frozen=True)
class SharedArgument:
    """One argument declaration that several helper parsers repeat.

    `dest` is fixed here and handed to `add_argument` explicitly, so a caller reusing a
    family can never pick a different namespace attribute by accident. `kwargs` is the rest
    of the canonical declaration, and it is frozen on construction, so neither the table nor
    a caller can edit a family in place. `varying` names the keys a caller may override,
    because the measured declarations differ there (for example `--role` defaults to `""` in
    bootstrap and `"assistant"` in transcript); `help` is always the caller's, since every
    script has its own sentence.
    """

    options: tuple[str, ...]
    dest: str
    kwargs: Mapping[str, object]
    varying: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        """Freeze `kwargs`: a frozen dataclass blocks rebinding, not an in-place edit."""
        object.__setattr__(self, "kwargs", MappingProxyType(dict(self.kwargs)))


# Keyed by family, and itself read-only. Every entry preserves the dest, action, type,
# metavar, nargs, required, and default that the declaring parsers already had at commit
# 630eab12; the pin in tests/herdr/test_herdr_shared_arguments.py freezes that per script and
# flag, subparsers included.
SHARED_ARGUMENTS: Mapping[str, SharedArgument] = MappingProxyType(
    {
        "json": SharedArgument(("--json",), "json", {"action": "store_true"}),
        "dry_run": SharedArgument(("--dry-run",), "dry_run", {"action": "store_true"}),
        "verbose": SharedArgument(("--verbose",), "verbose", {"action": "store_true"}),
        "wait": SharedArgument(("--wait",), "wait", {"action": "store_true"}),
        "no_wait": SharedArgument(("--no-wait",), "no_wait", {"action": "store_true"}),
        "no_caller_context": SharedArgument(
            ("--no-caller-context",), "no_caller_context", {"action": "store_true"}
        ),
        "skip_screen_check": SharedArgument(
            ("--skip-screen-check",), "skip_screen_check", {"action": "store_true"}
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
        "limit": SharedArgument(
            ("--limit",), "limit", {"type": int, "metavar": "N", "default": 20}
        ),
    }
)


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
