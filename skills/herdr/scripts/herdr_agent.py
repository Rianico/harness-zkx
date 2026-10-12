#!/usr/bin/env python3
"""herdr-agent — the agent-state observation seam: unwrap `herdr agent get`, interpret the state.

Internal — import it, do not run it. `herdr agent get` answers arrive as a
`result.agent` record, and both herdr-wait and herdr-prompt re-read that record with
the same steps and the same vocabulary: revision 0 means weak recognition, an `⏳`
or `subagent` token marker means background subagents still run, `interactive_ready`
flags a pending human input. The unwrap and the interpretation live here once.

`observe_agent` returns an `AgentObservation` and is fail-loud: a non-zero exit or a
record without `agent_status` raises `HerdrError`. Consumers keep their own fail-soft
policies by catching — herdr-prompt turns a raise into `(None, None)` or
`(False, None, None)`, herdr-wait lets it end the poll as a hard failure.

The interpretation functions accept any record carrying the interpreted fields
(an `AgentObservation` or herdr-wait's `Snapshot`); `has_active_subagents` also
takes a bare `Mapping[str, str] | None` of tokens.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import (
    HerdrError,
    decode_response,
    entry_optional_text,
    run_herdr,
)


@dataclass(frozen=True)
class AgentObservation:
    """One target's interpreted `herdr agent get` record."""

    target: str
    status: str
    revision: str | None = None
    session: str | None = None
    tokens: Mapping[str, str] | None = None
    interactive_ready: bool | None = None
    pane_id: str | None = None


class _StateLike(Protocol):
    """Anything carrying the interpreted fields; herdr-wait's `Snapshot` included."""

    @property
    def status(self) -> str: ...

    @property
    def revision(self) -> str | None: ...

    @property
    def tokens(self) -> Mapping[str, str] | None: ...


def observe_agent(herdr: str, target: str, env: Mapping[str, str]) -> AgentObservation:
    """Read `herdr agent get <target>` and unwrap it; a failed read is fail-loud."""
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
    revision_raw = agent.get("revision")
    revision: str | None = None
    if isinstance(revision_raw, str) and revision_raw:
        revision = revision_raw
    elif isinstance(revision_raw, int) and revision_raw >= 0:
        revision = str(revision_raw)
    session_raw = agent.get("agent_session")
    session: str | None = None
    if isinstance(session_raw, dict):
        session = entry_optional_text(session_raw, "value")
    tokens_raw = agent.get("tokens")
    tokens: dict[str, str] | None = None
    if isinstance(tokens_raw, dict):
        tokens = {str(k): str(v) for k, v in tokens_raw.items() if isinstance(v, str)}
    ready_raw = agent.get("interactive_ready")
    interactive_ready = ready_raw if isinstance(ready_raw, bool) else None
    pane_raw = agent.get("pane_id")
    pane_id = str(pane_raw) if pane_raw is not None else None
    return AgentObservation(
        target=target,
        status=status,
        revision=revision,
        session=session,
        tokens=tokens,
        interactive_ready=interactive_ready,
        pane_id=pane_id,
    )


def read_interactive_ready(herdr: str, target: str, env: Mapping[str, str]) -> bool | None:
    """Tri-state read of `interactive_ready`: False when explicit, True when explicit, else None.

    A failed read, a missing field, or a non-bool value all read None; never a gate,
    only evidence for refusal messaging after some other check has already refused.
    """
    try:
        obs = observe_agent(herdr, target, env)
    except HerdrError:
        return None
    return obs.interactive_ready


def is_recognized(state: _StateLike) -> bool:
    """Revision 0 means Herdr has not recognized an agent turn yet.

    Seen on agy panes: `agent get` reports idle/done with revision 0 and no
    session while the pane status bar still reads WORKING. Such a record never
    settles a barrier.
    """
    return state.revision != "0"


def has_active_subagents(tokens_or_obs: _StateLike | Mapping[str, str] | None) -> bool:
    """True when tokens indicate active subagents (e.g. ⏳ in summary or title-suffix)."""
    tokens: Mapping[str, str] | None
    if tokens_or_obs is None:
        tokens = None
    elif isinstance(tokens_or_obs, Mapping):
        tokens = tokens_or_obs
    else:
        tokens = tokens_or_obs.tokens
    if not tokens:
        return False
    summary = tokens.get("summary", "")
    title_suffix = tokens.get("title-suffix", "")
    return "⏳" in summary or "subagent" in summary.lower() or "⏳" in title_suffix


def is_agent_settled(state: _StateLike, wanted: Sequence[str]) -> bool:
    """Settled means: in a wanted state, recognized, and without active subagents."""
    if state.status not in wanted:
        return False
    if not is_recognized(state):
        return False
    if has_active_subagents(state):
        return False
    return True
