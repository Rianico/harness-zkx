#!/usr/bin/env python3
"""herdr-envelope — the envelope domain: render, delimit, parse.

Internal — import it, do not run it. The Style 2 nested envelope that a dispatched prompt or
reply carries is formatted here: the `Routing:` (Sender, Group, `Receiver(You)`), `Hierarchy:`
(Task-Group, Ticket-ID, Task-ID, In-Reply-To), `Runtime:` (Cwd/Resume recovery metadata), and
`Protocol:` (the Herdr skill notice) sections, the `---` paging delimiter around the payload,
and the closing completion-reply contract. `parse_envelope` and `split_envelope_and_body`
read the exact format the renderers write, so the envelope can be consumed as well as
produced.

Identity producers (`build_identity`, `resolve_caller`, `resolve_receiver`,
`resolve_group_members`) stay in `herdr_prompt`: this module formats and parses the envelope
from a `CallerContext` it is handed, and never looks a pane up.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import reply_helper


@dataclass(frozen=True)
class CallerContext:
    """The envelope sender: pane id, visible label, addressable agent name, kind, session, tab, cwd."""

    pane_id: str
    label: str | None = None
    agent: str | None = None
    kind: str | None = None
    session_id: str | None = None
    resume_cmd: str | None = None
    tab_id: str | None = None
    cwd: str | None = None


def _single_line(value: str, limit: int = 64) -> str:
    """Collapse a free-form pane label onto one header line; labels are operator input."""
    return " ".join(value.split())[:limit]


def _scalar(value: str) -> str:
    """Render a header value; quote only when a YAML reader would mangle it."""
    if not value:
        return ""
    if (
        '"' in value
        or "'" in value
        or "#" in value
        or '": "' in value
        or any(ch.isspace() for ch in value)
    ):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def sender_ref(sender: CallerContext) -> str:
    """Render the targetable `<agent>@<pane>` ref plus position fields; a pane label is never a name."""
    label = _single_line(sender.label) if sender.label else ""
    parts = [f"{sender.agent}@{sender.pane_id}" if sender.agent else sender.pane_id]
    if label and label != sender.agent:
        parts.append(f"label {_scalar(label)}")
    if sender.tab_id:
        parts.append(f"tab {_scalar(sender.tab_id)}")
    if sender.kind:
        parts.append(f"kind {_scalar(sender.kind)}")
    return " - ".join(parts)


def receiver_ref(receiver: str | CallerContext) -> str:
    """Render the addressee as a position ref when it resolved, else as the bare target token."""
    if isinstance(receiver, CallerContext):
        return sender_ref(receiver)
    return _scalar(receiver)


def render_envelope(
    sender: CallerContext,
    *,
    receiver: str | CallerContext | None = None,
    group_members: Sequence[str] = (),
    include_recovery: bool = False,
    ticket_id: str | None = None,
    task_id: str | None = None,
    task_group: str | None = None,
    tab_id: str | None = None,
    in_reply_to: str | None = None,
) -> str:
    """Render the Style 2 envelope; the receiver closes the Routing block, and an absent field renders no line."""
    routing = ["Routing:", f"  Sender: {sender_ref(sender)}"]
    if group_members:
        routing.append(f"  Group: [{', '.join(group_members)}]")
    if receiver:
        routing.append(f"  Receiver(You): {receiver_ref(receiver)}")

    hierarchy: list[str] = []
    if task_group and tab_id:
        hierarchy.append(f"  Task-Group: {task_group} ({tab_id})")
    elif task_group:
        hierarchy.append(f"  Task-Group: {task_group}")
    elif tab_id:
        hierarchy.append(f"  Task-Group: {tab_id}")
    if ticket_id:
        hierarchy.append(f"  Ticket-ID: {ticket_id}")
    if task_id:
        hierarchy.append(f"  Task-ID: {task_id}")
    if in_reply_to:
        hierarchy.append(f"  In-Reply-To: {in_reply_to}")

    runtime: list[str] = []
    if include_recovery:
        if sender.cwd:
            runtime.append(f"  Cwd: {_scalar(sender.cwd)}")
        if sender.resume_cmd:
            runtime.append(f"  Resume: {_scalar(sender.resume_cmd)}")

    lines = [*routing]
    if hierarchy:
        lines.append("Hierarchy:")
        lines.extend(hierarchy)
    if runtime:
        lines.append("Runtime:")
        lines.extend(runtime)
    lines.append("Protocol:")
    lines.append(f"  {SKILL_NOTICE}")
    return "\n".join(lines)


def utc_stamp() -> str:
    """Timestamp an envelope; both directions stamp, so a transcript reads in order."""
    return f"[{datetime.now(UTC).isoformat(timespec='milliseconds').replace('+00:00', 'Z')}]"


SKILL_NOTICE = (
    "Herdr: follow the herdr skill — run its helper scripts from ${herdr_skill}/scripts/ for all "
    "coordination, never the bare herdr CLI"
)

# The reply contract is an executable command, so it names this lane's own `herdr_reply.py` as an
# absolute path resolved from this tree: the receiving agent runs it from any cwd, and a
# placeholder would render a command that cannot run. The derivation is single-sourced in
# `herdr_cli.reply_helper()` — the `~/.agents/skills/herdr` symlink is deliberately not used,
# since it can resolve into another worktree whose `herdr_*` code may be older.
REPLY_HELPER = reply_helper()


def render_reply_contract(sender: CallerContext, ticket_id: str | None = None) -> str:
    """Render the completion-reply contract; without an agent name no target is addressable.

    A known ticket id is bound with `--ticket`, so the callee's reply names its task and the
    reply side binds explicitly. This replaced the sender's sole-open-task inference, which
    #246 E1.2 deleted. The dispatcher reuses the same `derive_ticket_id` it stores on the
    lease, so the rendered id and the task it names cannot drift. Without a derived id
    (`--file -`, stdin) the contract renders without `--ticket` and the reply lands unlinked
    with D1.3's warning.

    The id is rendered shell-quoted in `=` form (`--ticket=` + `shlex.quote`), because
    this line is a command the callee copy-pastes: a lane ticket stem starts with a digit,
    so the derived id starts with `#`, which a shell reads as the start of a comment and
    would swallow the id — the helper then exits 2 with `argument --ticket: expected one
    argument`. The `=` form additionally keeps a leading-dash id (`-rf.md` derives `-rf`;
    `shlex.quote('-rf')` is `-rf`) from being parsed as a flag — the space form renders
    `--ticket -rf`, which argparse refuses with the same exit-2 `expected one argument`
    and the reply is never sent. A loud refusal of leading-dash ids at render time was
    rejected because it would make such tickets undispatchable; the `=` form delivers
    them, and argparse binds `--ticket=<value>` as the value even with a leading dash.
    Quoting also keeps a filename's shell metacharacters inert (`pwn;touch PWNED.md` used
    to run `touch PWNED`). Quoting is preferred over validating the id against a safe
    grammar because a grammar would refuse the arbitrary ticket names the dispatcher
    deliberately derives verbatim. This is the same treatment `herdr_bootstrap` gives a
    rendered path (`shlex.quote(target)`), and the reason agent names are refused for
    whitespace.

    The contract also carries the SHA guard's waiver route in prose: a callee quoting a
    review id (an eight-hex record such as '0c81f04c', which names no commit) meets the
    broad #247 trigger, so without guidance the reply is refused with no sanctioned next
    step. The guidance names `--allow-unresolvable-sha` with a single-quoted example, so
    the example survives copy-paste as one shell word — prose advice, never a shell
    template, so nothing pasted from it widens the waiver.
    """
    if sender.agent:
        contract = f'  uv run "{REPLY_HELPER}" {sender.agent} "<STATUS> <artifacts> <issues>"'
        if ticket_id:
            contract += f" --ticket={shlex.quote(ticket_id)}"
        return (
            "On completion, reply to the sender in one message using the herdr helper script:\n"
            f"{contract}\n"
            "  If the reply quotes a review id such as '0c81f04c' that names no commit,"
            " the SHA guard refuses it: waive that token by name with"
            " --allow-unresolvable-sha '0c81f04c' (one flag per token, reported on stderr)."
        )
    note = (
        "(the sending pane has no agent name; reply cannot be addressed — "
        "report completion to the user instead)"
    )
    return f"On completion, reply to the sender in one message:\n  {note}"


# The body page-breaks after the envelope; renderers and the parser share this one delimiter.
PAGING_DELIMITER = "---"


def render_prelude(envelope: str) -> str:
    """Stamp the envelope and page-break after it; the delivered body follows the delimiter."""
    return f"{utc_stamp()}\n{envelope}\n{PAGING_DELIMITER}\n\n"


def wrap_with_envelope(
    payload: str,
    sender: CallerContext,
    *,
    group_members: Sequence[str] = (),
    receiver: str | CallerContext | None = None,
    include_recovery: bool = False,
    ticket_id: str | None = None,
    task_id: str | None = None,
    task_group: str | None = None,
    tab_id: str | None = None,
) -> str:
    """Prepend the timestamped envelope and append the reply contract around the payload."""
    envelope = render_envelope(
        sender,
        receiver=receiver,
        group_members=group_members,
        include_recovery=include_recovery,
        ticket_id=ticket_id,
        task_id=task_id,
        task_group=task_group,
        tab_id=tab_id,
    )
    prelude = render_prelude(envelope)
    return f"{prelude}{payload}\n\n{render_reply_contract(sender, ticket_id)}"


_TIMESTAMP = re.compile(r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\]$")

_SECTION_HEADERS = frozenset({"Routing:", "Hierarchy:", "Runtime:", "Protocol:"})

_FIELD_NAMES: dict[str, str] = {
    "Sender": "sender",
    "Receiver(You)": "receiver",
    "Task-Group": "task_group",
    "Ticket-ID": "ticket_id",
    "Task-ID": "task_id",
    "In-Reply-To": "in_reply_to",
    "Cwd": "cwd",
    "Resume": "resume",
}


def _unquote(value: str) -> str:
    """Inverse of `_scalar`; a rendered header never starts a bare value with a double quote."""
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return value


@dataclass(frozen=True)
class Envelope:
    """A parsed envelope header; a field is "" when the envelope rendered no line for it."""

    sender: str = ""
    group: tuple[str, ...] = ()
    receiver: str = ""
    task_group: str = ""
    ticket_id: str = ""
    task_id: str = ""
    in_reply_to: str = ""
    cwd: str = ""
    resume: str = ""
    protocol: str = ""


def _group_members(value: str) -> tuple[str, ...]:
    """Parse the bracket form `[a, b]` the renderer emits for Group."""
    if not (value.startswith("[") and value.endswith("]")):
        return ()
    inner = value[1:-1].strip()
    if not inner:
        return ()
    return tuple(_unquote(item.strip()) for item in inner.split(","))


def parse_envelope(payload: str) -> Envelope | None:
    """Parse an envelope header — bare, timestamped, or ahead of the paging delimiter; else None."""
    head = payload.partition(f"\n{PAGING_DELIMITER}\n\n")[0]
    lines = head.splitlines()
    if lines and _TIMESTAMP.match(lines[0]):
        lines = lines[1:]
    if not lines or lines[0] != "Routing:":
        return None
    fields: dict[str, str] = {}
    group: tuple[str, ...] = ()
    protocol: list[str] = []
    in_protocol = False
    for line in lines[1:]:
        if not line.startswith("  "):
            if line not in _SECTION_HEADERS:
                return None
            in_protocol = line == "Protocol:"
            continue
        if in_protocol:
            protocol.append(line[2:])
            continue
        key, sep, value = line[2:].partition(": ")
        if not sep:
            return None
        if key == "Group":
            group = _group_members(value)
            continue
        name = _FIELD_NAMES.get(key)
        if name is not None:
            fields[name] = _unquote(value)
    return Envelope(
        sender=fields.get("sender", ""),
        group=group,
        receiver=fields.get("receiver", ""),
        task_group=fields.get("task_group", ""),
        ticket_id=fields.get("ticket_id", ""),
        task_id=fields.get("task_id", ""),
        in_reply_to=fields.get("in_reply_to", ""),
        cwd=fields.get("cwd", ""),
        resume=fields.get("resume", ""),
        protocol="\n".join(protocol),
    )


def split_envelope_and_body(text: str) -> tuple[Envelope | None, str | None]:
    """Split a wrapped payload at the paging delimiter; non-envelope text yields (None, None)."""
    head, sep, body = text.partition(f"\n{PAGING_DELIMITER}\n\n")
    if not sep:
        return None, None
    envelope = parse_envelope(head)
    if envelope is None:
        return None, None
    return envelope, body
