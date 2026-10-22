#!/usr/bin/env python3
"""herdr-envelope — the envelope domain: render, delimit, parse.

Internal — import it, do not run it. Every inter-agent message carries the A2A Markdown
frontmatter envelope that `docs/adr/0020-a2a-markdown-frontmatter-envelope.md` adopts: a block
fenced by `---` on line 1 and closed by `---` before the payload, holding the canonical fields
`id` (the task), `context_id` (the sender's session), `status` (`state` plus `timestamp`) and
`metadata` (ticket, the sender/receiver addresses, the task group, the replied-to task, plus the
lane topology the routing used to carry). The Herdr skill notice follows the closing fence as
its own plain line, then the payload follows.

PyYAML emits and reads the block, so a generic Markdown frontmatter parser reads an envelope
without a bespoke regex: `parse_envelope` accepts exactly what the renderers write, and the
retired Style 2 `Routing:`/`Hierarchy:`/`Runtime:`/`Protocol:` form is refused — the cutover
ships no backward-compatibility shim. `status.state` is authoritative for the task lifecycle.

Identity producers (`build_identity`, `resolve_caller`, `resolve_receiver`,
`resolve_group_members`) stay in `herdr_prompt`: this module formats and parses the envelope
from a `CallerContext` it is handed, and never looks a pane up.
"""

from __future__ import annotations

import shlex
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import yaml

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
    session_path: str | None = None
    resume_cmd: str | None = None
    tab_id: str | None = None
    cwd: str | None = None


def _single_line(value: str, limit: int = 64) -> str:
    """Collapse a free-form pane label onto one header line; labels are operator input."""
    return " ".join(value.split())[:limit]


def _scalar(value: str) -> str:
    """Render a routing-ref value; quote only when a YAML reader would mangle it.

    This is the hand-written form used by `sender_ref`, whose composite position ref is prose an
    operator reads in a ticket draft — never a frontmatter field. Frontmatter values go through
    `yaml.safe_dump`, which owns its own quoting.
    """
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


def address_of(ref: str | CallerContext) -> str:
    """The strict `<agent>@<pane>` address a frontmatter field carries, never a composite ref.

    A resolved pane falls back to its bare pane id when no agent name registered; an unresolved
    dispatch target is its own address, because that token is what `herdr agent prompt` accepted.
    """
    if isinstance(ref, CallerContext):
        return caller_anchor(ref)
    return ref


# The canonical A2A `TaskState` names this harness renders; `status.state` is authoritative.
STATE_WORKING = "TASK_STATE_WORKING"
STATE_COMPLETED = "TASK_STATE_COMPLETED"
STATE_INPUT_REQUIRED = "TASK_STATE_INPUT_REQUIRED"
STATE_FAILED = "TASK_STATE_FAILED"

# A reply's first token reaches the envelope through `herdr_evidence.parse_status_line`, which
# maps COMPLETED/BLOCKED/REJECTED onto `completed`/`blocked`/`rework`. This table is the single
# place the two vocabularies meet: a completion is `TASK_STATE_COMPLETED`, work awaiting input
# is `TASK_STATE_INPUT_REQUIRED`, and a refusal is `TASK_STATE_FAILED`. An unmapped or absent
# status renders `TASK_STATE_WORKING`, which is also what a dispatch or a prompt renders, since
# the callee has not settled the task yet.
REPLY_STATE_BY_STATUS: Mapping[str, str] = {
    "completed": STATE_COMPLETED,
    "blocked": STATE_INPUT_REQUIRED,
    "rework": STATE_FAILED,
}


def reply_state(status: str | None) -> str:
    """The canonical state a parsed reply status renders as; nothing settled is still working."""
    return REPLY_STATE_BY_STATUS.get(status or "", STATE_WORKING)


def _task_group_field(task_group: str | None, tab_id: str | None) -> str:
    """The `<group_slug>@<tab_id>` task group; a lone side of it is its own value, neither is absent."""
    if task_group and tab_id:
        return f"{task_group}@{tab_id}"
    return task_group or tab_id or ""


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
    state: str = STATE_WORKING,
) -> str:
    """Render the A2A frontmatter block: fenced top and bottom, an absent field renders no key.

    The four top-level keys are always present. `id` is never empty: it is either the linked task
    id or a generated `unlinked-<compact utc stamp>` id, because A2A requires `Task.id` and a
    generic parser cannot tell `''` from a malformed document. `context_id` renders `''` when the
    harness knows no session — an honest blank, no session is invented. `metadata` carries the A2A
    correlation fields plus the lane topology the retired routing blocks used to hold: the `group`
    member list always, `cwd`/`resume` only when `include_recovery` is set (the `--verbose` route),
    because recovery metadata is retrieved just-in-time from `.lane/tasks.yaml` on the default path.
    """
    metadata: dict[str, Any] = {}
    if ticket_id:
        metadata["ticket_id"] = ticket_id
    metadata["sender"] = address_of(sender)
    if receiver is not None:
        metadata["receiver"] = address_of(receiver)
    group_field = _task_group_field(task_group, tab_id)
    if group_field:
        metadata["task_group"] = group_field
    if in_reply_to:
        metadata["in_reply_to"] = in_reply_to
    if group_members:
        metadata["group"] = list(group_members)
    if include_recovery:
        if sender.cwd:
            metadata["cwd"] = sender.cwd
        if sender.resume_cmd:
            metadata["resume"] = sender.resume_cmd

    # One stamp for both uses, so an unlinked id and its own `status.timestamp` cannot disagree.
    stamp = utc_stamp()
    frontmatter: dict[str, Any] = {
        # The fallback rides the `id` slot ONLY: `metadata.in_reply_to` stays absent on an
        # unlinked reply, so a generated id never advertises a correlation the store denies.
        "id": task_id or _unlinked_id(stamp),
        "context_id": sender.session_id or "",
        "status": {"state": state, "timestamp": stamp},
        "metadata": metadata,
    }
    block = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
    return "\n".join([PAGING_DELIMITER, *block.rstrip().splitlines(), PAGING_DELIMITER])


def _unlinked_id(stamp: str) -> str:
    """A valid `Task.id` for a message that bound no task: `unlinked-` plus the compact stamp.

    Compact means the ISO-8601 extended separators (`-`, `:`, the fractional-second `.`) are
    dropped, so the id is one unquoted path-safe word. The stamp arrives through `utc_stamp()`,
    the module's single clock indirection, so the frozen-clock tests pin it exactly.
    """
    return f"unlinked-{stamp.translate(str.maketrans('', '', '-:.'))}"


def utc_stamp() -> str:
    """Timestamp an envelope as a bare ISO-8601 UTC string; both directions stamp, so a transcript reads in order."""
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


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

    The contract also states, in one line, what makes a COMPLETED payload complete: an
    evidence heading or an inline evidence label. The check runs in `herdr_reply`; naming
    the shape at authoring time is what a sender needs before the reply is recorded
    incomplete (#299).
    """
    if sender.agent:
        contract = f'  uv run "{REPLY_HELPER}" {sender.agent} "<STATUS> <artifacts> <issues>"'
        if ticket_id:
            contract += f" --ticket={shlex.quote(ticket_id)}"
        return (
            "On completion, reply to the sender in one message using the herdr helper script:\n"
            f"{contract}\n"
            "  A COMPLETED payload is complete only with evidence: an evidence heading"
            ' (such as "## Evidence") or an inline evidence label (such as "**Evidence:**").\n'
            "  If the reply quotes a review id such as '0c81f04c' that names no commit,"
            " the SHA guard refuses it: waive that token by name with"
            " --allow-unresolvable-sha '0c81f04c' (one flag per token, reported on stderr)."
        )
    note = (
        "(the sending pane has no agent name; reply cannot be addressed — "
        "report completion to the user instead)"
    )
    return f"On completion, reply to the sender in one message:\n  {note}"


# The frontmatter fence and the caller-facing page-break are the same token by design: Markdown
# reads `---` as the horizontal rule that closes the block, so one delimiter serves both roles.
PAGING_DELIMITER = "---"

# The delivered envelope is the frontmatter block, then the skill notice on its own line, then
# the payload. This one constant joins them and is the exact string the readers split on, so a
# renderer and a parser can never disagree about where the envelope ends.
NOTICE_SEPARATOR = f"\n{SKILL_NOTICE}\n\n"


def render_prelude(envelope: str) -> str:
    """Close the frontmatter block with the skill notice and the page break; the body follows."""
    return f"{envelope}{NOTICE_SEPARATOR}"


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
    state: str = STATE_WORKING,
) -> str:
    """Prepend the A2A envelope and skill notice and append the reply contract around the payload."""
    envelope = render_envelope(
        sender,
        receiver=receiver,
        group_members=group_members,
        include_recovery=include_recovery,
        ticket_id=ticket_id,
        task_id=task_id,
        task_group=task_group,
        tab_id=tab_id,
        state=state,
    )
    prelude = render_prelude(envelope)
    return f"{prelude}{payload}\n\n{render_reply_contract(sender, ticket_id)}"


# The canonical top-level key set, and the key sets nested inside it. A frontmatter block with a
# key outside its set is not an envelope this module rendered, so it is refused rather than
# half-read: a silently ignored key is how a producer and a consumer drift apart.
FRONTMATTER_KEYS = frozenset({"id", "context_id", "status", "metadata"})
STATUS_KEYS = frozenset({"state", "timestamp"})
METADATA_KEYS = frozenset(
    {
        "ticket_id",
        "sender",
        "receiver",
        "task_group",
        "in_reply_to",
        "group",
        "cwd",
        "resume",
    }
)


@dataclass(frozen=True)
class Envelope:
    """A parsed A2A envelope; a field is "" when the envelope carried no value for it.

    The field names are the frontmatter key names, so a reader can trace any value back to the
    block: `task_id` is the block's `id`, `state` and `timestamp` come from `status`, the rest
    from `metadata`.
    """

    id: str = ""
    context_id: str = ""
    state: str = ""
    timestamp: str = ""
    sender: str = ""
    receiver: str = ""
    ticket_id: str = ""
    task_group: str = ""
    in_reply_to: str = ""
    group: tuple[str, ...] = ()
    cwd: str = ""
    resume: str = ""


def _text(value: object) -> str:
    """A frontmatter scalar as text; a value the loader retyped (a bare `123`) is no envelope field."""
    return value if isinstance(value, str) else ""


def _names(value: object) -> tuple[str, ...]:
    """The `group` member list, dropped whole unless every entry is a string."""
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _frontmatter_block(payload: str) -> str | None:
    """The fenced frontmatter body of `payload`, or None when it opens or closes otherwise."""
    lines = payload.splitlines()
    if not lines or lines[0] != PAGING_DELIMITER:
        return None
    try:
        close = lines.index(PAGING_DELIMITER, 1)
    except ValueError:
        return None
    return "\n".join(lines[1:close])


def parse_envelope(payload: str) -> Envelope | None:
    """Parse an A2A envelope — the bare block or a whole delivered message; any other text is None.

    A dispatched prompt, a reply, and a bare `render_envelope` result all open with the `---`
    fence, so the same read serves each. The retired Style 2 header is refused here by shape: it
    never opens with a fence, so it needs no special case and no compatibility branch.
    """
    block = _frontmatter_block(payload)
    if block is None:
        return None
    try:
        raw: Any = yaml.safe_load(block)
    except yaml.YAMLError:
        return None
    if not isinstance(raw, dict) or not FRONTMATTER_KEYS.issuperset(raw):
        return None
    status = raw.get("status")
    if not isinstance(status, dict) or not STATUS_KEYS.issuperset(status):
        return None
    metadata = raw.get("metadata")
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict) or not METADATA_KEYS.issuperset(metadata):
        return None
    return Envelope(
        id=_text(raw.get("id")),
        context_id=_text(raw.get("context_id")),
        state=_text(status.get("state")),
        timestamp=_text(status.get("timestamp")),
        sender=_text(metadata.get("sender")),
        receiver=_text(metadata.get("receiver")),
        ticket_id=_text(metadata.get("ticket_id")),
        task_group=_text(metadata.get("task_group")),
        in_reply_to=_text(metadata.get("in_reply_to")),
        group=_names(metadata.get("group")),
        cwd=_text(metadata.get("cwd")),
        resume=_text(metadata.get("resume")),
    )


def split_envelope_and_body(text: str) -> tuple[Envelope | None, str | None]:
    """Split a wrapped payload at the skill-notice separator; non-envelope text yields (None, None)."""
    head, sep, body = text.partition(NOTICE_SEPARATOR)
    if not sep:
        return None, None
    envelope = parse_envelope(head)
    if envelope is None:
        return None, None
    return envelope, body


def caller_anchor(caller: CallerContext) -> str:
    """The `<agent>@<pane>` self-anchor, rendered as `[You: <anchor>]` on the caller's status line.

    The status line must say who is speaking, so the caller reads its own identity first and the
    addressee second. Falls back to the bare pane id when no agent name resolved.
    """
    if caller.agent:
        return f"{caller.agent}@{caller.pane_id}"
    return caller.pane_id


def envelope_metadata_lines(delivered: str) -> list[str]:
    """The delivered envelope's frontmatter key lines, fence and skill notice dropped.

    Caller-facing only: the callee still receives the full envelope. The `---` fences and the
    `Herdr:` notice line are cut because that notice is identical on every message and would
    otherwise repeat in the orchestrator's context, and the timestamp line stays — it is what
    makes a transcript readable in order. Text with no parseable frontmatter block
    (`--no-caller-context`, a body that is not an envelope) yields no lines, so a body containing
    a bare `---` is never mistaken for a header.
    """
    head, sep, _rest = delivered.partition(NOTICE_SEPARATOR)
    if not sep:
        return []
    return (_frontmatter_block(head) or "").splitlines()


def preview_body(body: str, limit: int = 3) -> list[str]:
    """A bounded preview of the payload: every non-empty line, or first/middle-marker/last.

    A body of `limit` or fewer non-empty lines prints in full; a longer one prints its first and
    last non-empty lines with a `... [skipped N lines]` marker for the lines in between, so the
    orchestrator sees the shape of what it dispatched without the whole ticket on stdout.
    """
    non_empty = [line for line in body.splitlines() if line.strip()]
    if len(non_empty) <= limit:
        return non_empty
    skipped = len(non_empty) - 2
    return [non_empty[0], f"... [skipped {skipped} lines]", non_empty[-1]]


def format_delivery_summary(status_line: str, delivered: str, body: str, source: str) -> str:
    """Render the caller-facing delivery summary: status, `---`, metadata, `---`, source, preview.

    `status_line` is the anchored first line (live prompt/reply status or the `dry-run:` plan
    line); `delivered` is the full wrapped payload (for the envelope metadata); `body` is the
    original payload (for the preview,
    so an appended reply contract or inserted pointer never leaks into it); `source` names where
    the payload came from. The two `---` delimiters separate status from metadata and metadata
    from preview — the same fence the callee's envelope opens with. This is what trims the
    orchestrator's context: the callee delivery is untouched, only this caller-side echo changes.
    """
    metadata = envelope_metadata_lines(delivered)
    return "\n".join(
        [
            status_line,
            PAGING_DELIMITER,
            *metadata,
            PAGING_DELIMITER,
            source,
            *preview_body(body),
        ]
    )
