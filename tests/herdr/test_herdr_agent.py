"""Tests for skills/herdr/scripts/herdr_agent.py (agent-state observation seam).

The unwrap is driven by a fake `run_herdr` at the seam's own boundary: the fake
answers with a `herdr agent get` JSON record and the tests assert what the
observation interprets from it, including the fail-loud raises consumers catch.
"""

import json
import subprocess
from collections.abc import Mapping

import herdr_agent
import pytest
from herdr_agent import AgentObservation
from herdr_cli import HerdrError

ENV = {"PATH": "/usr/bin"}


def agent_json(agent: Mapping[str, object]) -> str:
    return json.dumps({"id": "cli:agent:get", "result": {"agent": dict(agent), "type": "agent"}})


def install_fake_run(
    monkeypatch: pytest.MonkeyPatch,
    stdout: str,
    returncode: int = 0,
    stderr: str = "",
) -> list[list[str]]:
    """Replace `herdr_agent.run_herdr` with a canned answer; records each argv."""
    calls: list[list[str]] = []

    def fake_run(argv: list[str], env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
        calls.append(list(argv))
        return subprocess.CompletedProcess(
            args=list(argv), returncode=returncode, stdout=stdout, stderr=stderr
        )

    monkeypatch.setattr(herdr_agent, "run_herdr", fake_run)
    return calls


# ── unwrap ─────────────────────────────────────────────────────────────────────


def test_observe_unwraps_the_full_record(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = install_fake_run(
        monkeypatch,
        agent_json(
            {
                "agent_status": "idle",
                "revision": "r7",
                "agent_session": {"kind": "path", "value": "/tmp/s.jsonl"},
                "tokens": {"summary": "ready"},
                "interactive_ready": True,
                "pane_id": "w9:p1",
            }
        ),
    )
    obs = herdr_agent.observe_agent("herdr", "a", ENV)
    assert calls == [["herdr", "agent", "get", "a"]]
    assert obs == AgentObservation(
        target="a",
        status="idle",
        revision="r7",
        session="/tmp/s.jsonl",
        tokens={"summary": "ready"},
        interactive_ready=True,
        pane_id="w9:p1",
    )


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("r5", "r5"), (0, "0"), (7, "7"), (-3, None), ("", None), (None, None)],
)
def test_observe_normalizes_revision(
    monkeypatch: pytest.MonkeyPatch, raw: object, expected: str | None
) -> None:
    agent: dict[str, object] = {"agent_status": "done"}
    if raw is not None:
        agent["revision"] = raw
    _ = install_fake_run(monkeypatch, agent_json(agent))
    assert herdr_agent.observe_agent("herdr", "a", ENV).revision == expected


def test_observe_filters_non_string_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    _ = install_fake_run(
        monkeypatch,
        agent_json(
            {"agent_status": "idle", "tokens": {"summary": "⏳ 1", "count": 3, "flag": True}}
        ),
    )
    assert herdr_agent.observe_agent("herdr", "a", ENV).tokens == {"summary": "⏳ 1"}


def test_observe_reads_pane_id_as_text(monkeypatch: pytest.MonkeyPatch) -> None:
    _ = install_fake_run(monkeypatch, agent_json({"agent_status": "idle", "pane_id": 12}))
    assert herdr_agent.observe_agent("herdr", "a", ENV).pane_id == "12"


@pytest.mark.parametrize(("raw", "expected"), [(True, True), (False, False), ("yes", None)])
def test_observe_interactive_ready_is_boolean_or_none(
    monkeypatch: pytest.MonkeyPatch, raw: object, expected: bool | None
) -> None:
    _ = install_fake_run(
        monkeypatch, agent_json({"agent_status": "idle", "interactive_ready": raw})
    )
    assert herdr_agent.observe_agent("herdr", "a", ENV).interactive_ready == expected


def test_observe_missing_interactive_ready_reads_none(monkeypatch: pytest.MonkeyPatch) -> None:
    _ = install_fake_run(monkeypatch, agent_json({"agent_status": "idle"}))
    assert herdr_agent.observe_agent("herdr", "a", ENV).interactive_ready is None


# ── fail-loud ──────────────────────────────────────────────────────────────────


def test_observe_fails_loud_on_nonzero_exit(monkeypatch: pytest.MonkeyPatch) -> None:
    _ = install_fake_run(monkeypatch, "", returncode=1, stderr="agent a not found")
    with pytest.raises(HerdrError, match="herdr agent get a failed: agent a not found"):
        _ = herdr_agent.observe_agent("herdr", "a", ENV)


def test_observe_fails_loud_without_agent_status(monkeypatch: pytest.MonkeyPatch) -> None:
    _ = install_fake_run(monkeypatch, agent_json({"revision": "r1"}))
    with pytest.raises(HerdrError, match="returned no agent_status"):
        _ = herdr_agent.observe_agent("herdr", "a", ENV)


def test_observe_fails_loud_without_result(monkeypatch: pytest.MonkeyPatch) -> None:
    _ = install_fake_run(monkeypatch, '{"ok": true}')
    with pytest.raises(HerdrError, match="returned no result"):
        _ = herdr_agent.observe_agent("herdr", "a", ENV)


def test_observe_fails_loud_without_agent_record(monkeypatch: pytest.MonkeyPatch) -> None:
    _ = install_fake_run(monkeypatch, '{"result": {"type": "agent"}}')
    with pytest.raises(HerdrError, match="returned no agent record"):
        _ = herdr_agent.observe_agent("herdr", "a", ENV)


# ── read_interactive_ready (tri-state, never a gate) ───────────────────────────


@pytest.mark.parametrize(
    ("agent", "expected"),
    [({"interactive_ready": False}, False), ({"interactive_ready": True}, True), ({}, None)],
)
def test_read_interactive_ready_tri_state(
    monkeypatch: pytest.MonkeyPatch, agent: dict[str, object], expected: bool | None
) -> None:
    _ = install_fake_run(monkeypatch, agent_json({"agent_status": "working", **agent}))
    assert herdr_agent.read_interactive_ready("herdr", "a", ENV) == expected


def test_read_interactive_ready_swallows_a_failed_read(monkeypatch: pytest.MonkeyPatch) -> None:
    _ = install_fake_run(monkeypatch, "", returncode=1, stderr="nope")
    assert herdr_agent.read_interactive_ready("herdr", "a", ENV) is None


# ── state vocabulary ───────────────────────────────────────────────────────────


def obs(
    status: str = "idle", revision: str | None = "r1", tokens: Mapping[str, str] | None = None
) -> AgentObservation:
    return AgentObservation(target="a", status=status, revision=revision, tokens=tokens)


def test_is_recognized() -> None:
    assert herdr_agent.is_recognized(obs(revision="r1"))
    assert herdr_agent.is_recognized(obs(revision=None))
    assert not herdr_agent.is_recognized(obs(revision="0"))


def test_has_active_subagents_accepts_mapping_none_and_observation() -> None:
    assert herdr_agent.has_active_subagents({"summary": "⏳ 1 subagent (developer)"})
    assert herdr_agent.has_active_subagents({"title-suffix": "⏳developer"})
    assert herdr_agent.has_active_subagents({"summary": "2 subagents running"})
    assert herdr_agent.has_active_subagents(obs(tokens={"summary": "⏳ 1 subagent"}))
    assert not herdr_agent.has_active_subagents(None)
    assert not herdr_agent.has_active_subagents({})
    assert not herdr_agent.has_active_subagents({"summary": "ready"})
    assert not herdr_agent.has_active_subagents(obs(tokens=None))


@pytest.mark.parametrize(
    ("status", "revision", "tokens", "wanted", "expected"),
    [
        ("idle", "r1", None, ("idle", "done"), True),
        ("done", "r1", None, ("idle", "done"), True),
        ("blocked", "r1", None, ("idle", "done", "blocked"), True),
        ("blocked", "r1", None, ("idle", "done"), False),
        ("working", "r1", None, ("idle", "done"), False),
        ("idle", "0", None, ("idle", "done"), False),
        ("idle", "r1", {"summary": "⏳ 1 subagent"}, ("idle", "done"), False),
        ("idle", "r1", {"title-suffix": "⏳dev"}, ("idle", "done"), False),
    ],
)
def test_is_agent_settled_matrix(
    status: str,
    revision: str | None,
    tokens: Mapping[str, str] | None,
    wanted: tuple[str, ...],
    expected: bool,
) -> None:
    assert herdr_agent.is_agent_settled(obs(status, revision, tokens), wanted) == expected
