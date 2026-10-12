"""Tests for skills/herdr/scripts/herdr_envelope.py (the envelope render/parse module).

Rendering is asserted line-for-line against the exact Format the dispatcher delivers; parsing is
asserted by round-trip (render → parse → fields match) and by refusal on non-envelope text.
"""

import re

import herdr_envelope
import pytest

TIMESTAMP_RE = r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\]$"


def sender(**overrides: object) -> herdr_envelope.CallerContext:
    fields: dict[str, object] = {
        "pane_id": "w1:p1",
        "label": "orchestrator",
        "agent": "orchestrator",
    }
    _ = fields.update(overrides)
    return herdr_envelope.CallerContext(**fields)  # type: ignore[arg-type]


# ── _scalar: YAML-quoting invariants ───────────────────────────────────────────────────────────


def test_scalar_passes_safe_values_through() -> None:
    assert herdr_envelope._scalar("w1:p1") == "w1:p1"
    assert herdr_envelope._scalar("/path/to/session.jsonl") == "/path/to/session.jsonl"
    assert herdr_envelope._scalar("") == ""


def test_scalar_quotes_values_a_yaml_reader_would_mangle() -> None:
    assert herdr_envelope._scalar("review pane X") == '"review pane X"'
    assert herdr_envelope._scalar("a#b") == '"a#b"'
    assert herdr_envelope._scalar("it's") == '"it\'s"'
    assert herdr_envelope._scalar('say "hi"') == '"say \\"hi\\""'
    assert herdr_envelope._scalar("back\\slash x") == '"back\\\\slash x"'


# ── _single_line: collapse and truncate ───────────────────────────────────────────────────────


def test_single_line_collapses_whitespace_and_truncates() -> None:
    assert herdr_envelope._single_line("review\npane\tX") == "review pane X"
    assert herdr_envelope._single_line("a" * 80) == "a" * 64
    assert herdr_envelope._single_line("a" * 80, 10) == "a" * 10


# ── refs ───────────────────────────────────────────────────────────────────────────────────────


def test_sender_ref_joins_position_fields_with_dash_separator() -> None:
    context = sender(label="lane", agent="t7-impl", tab_id="w1:t1", kind="qodercli")
    assert (
        herdr_envelope.sender_ref(context)
        == "t7-impl@w1:p1 - label lane - tab w1:t1 - kind qodercli"
    )


def test_sender_ref_omits_a_label_equal_to_the_agent_name() -> None:
    assert herdr_envelope.sender_ref(sender()) == "orchestrator@w1:p1"


def test_sender_ref_without_an_agent_names_the_pane_only() -> None:
    context = herdr_envelope.CallerContext(pane_id="w9:p2", label="scratch pad")
    assert herdr_envelope.sender_ref(context) == 'w9:p2 - label "scratch pad"'


def test_receiver_ref_renders_a_resolved_context_as_a_position_ref() -> None:
    receiver = sender(pane_id="w1:p3", label="impl-1", agent="impl-1", kind="agy", tab_id="w1:t1")
    assert herdr_envelope.receiver_ref(receiver) == "impl-1@w1:p3 - tab w1:t1 - kind agy"


def test_receiver_ref_renders_an_unresolved_target_as_a_bare_scalar() -> None:
    assert herdr_envelope.receiver_ref("impl-1") == "impl-1"
    assert herdr_envelope.receiver_ref("some target") == '"some target"'


# ── render_envelope: sections ──────────────────────────────────────────────────────────────────


def test_render_envelope_default_is_routing_and_protocol_only() -> None:
    rendered = herdr_envelope.render_envelope(sender(kind="pi"), receiver="impl-1")
    assert rendered == "\n".join(
        [
            "Routing:",
            "  Sender: orchestrator@w1:p1 - kind pi",
            "  Receiver(You): impl-1",
            "Protocol:",
            f"  {herdr_envelope.SKILL_NOTICE}",
        ]
    )
    assert "Hierarchy:" not in rendered
    assert "Runtime:" not in rendered


def test_render_envelope_group_uses_the_bracket_form() -> None:
    rendered = herdr_envelope.render_envelope(
        sender(), group_members=["orchestrator@w1:p1", "impl-1@w1:p3"]
    )
    assert "  Group: [orchestrator@w1:p1, impl-1@w1:p3]" in rendered.splitlines()


def test_render_envelope_renders_the_full_hierarchy_block() -> None:
    rendered = herdr_envelope.render_envelope(
        sender(),
        task_group="full-stack",
        tab_id="w1:t2",
        ticket_id="#182-herdr-msg-enhance",
        task_id="t7-impl",
        in_reply_to="#182-herdr-msg-enhance#full-stack",
    )
    assert rendered.splitlines()[1:7] == [
        "  Sender: orchestrator@w1:p1",
        "Hierarchy:",
        "  Task-Group: full-stack (w1:t2)",
        "  Ticket-ID: #182-herdr-msg-enhance",
        "  Task-ID: t7-impl",
        "  In-Reply-To: #182-herdr-msg-enhance#full-stack",
    ]


def test_render_envelope_runtime_block_appears_only_with_recovery() -> None:
    context = sender(
        cwd="/path/to/my project", resume_cmd="pi --session /tmp/session.jsonl", kind="pi"
    )
    assert "Runtime:" not in herdr_envelope.render_envelope(context)
    rendered = herdr_envelope.render_envelope(context, include_recovery=True)
    assert "Runtime:" in rendered.splitlines()
    lines = rendered.splitlines()
    assert lines[lines.index("Runtime:") + 1] == '  Cwd: "/path/to/my project"'
    assert lines[lines.index("Runtime:") + 2] == '  Resume: "pi --session /tmp/session.jsonl"'


# ── stamping and paging ────────────────────────────────────────────────────────────────────────


def test_utc_stamp_matches_the_envelope_timestamp_grammar() -> None:
    assert re.match(TIMESTAMP_RE, herdr_envelope.utc_stamp())


def test_paging_delimiter_is_the_pinned_triple_dash() -> None:
    assert herdr_envelope.PAGING_DELIMITER == "---"


def test_render_prelude_stamps_envelopes_and_ends_with_the_page_break(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stamp = "[2026-01-02T03:04:05.678Z]"
    monkeypatch.setattr(herdr_envelope, "utc_stamp", lambda: stamp)
    assert (
        herdr_envelope.render_prelude("Routing:\nProtocol:")
        == "[2026-01-02T03:04:05.678Z]\nRouting:\nProtocol:\n---\n\n"
    )


# ── render_reply_contract ──────────────────────────────────────────────────────────────────────


def test_reply_contract_names_the_helper_and_the_status_shape() -> None:
    contract = herdr_envelope.render_reply_contract(sender(agent="reviewer"))
    assert (
        f'  uv run "{herdr_envelope.REPLY_HELPER}" reviewer "<STATUS> <artifacts> <issues>"'
        in contract
    )
    assert "--ticket" not in contract


def test_reply_contract_binds_a_ticket_shell_quoted_in_the_equals_form() -> None:
    contract = herdr_envelope.render_reply_contract(sender(agent="reviewer"), "#182-herdr-msg")
    assert "\"<STATUS> <artifacts> <issues>\" --ticket='#182-herdr-msg'" in contract
    assert "--ticket '#182-herdr-msg'" not in contract
    assert "--ticket #182-herdr-msg" not in contract


def test_reply_contract_quotes_a_ticket_with_shell_metacharacters_inert() -> None:
    contract = herdr_envelope.render_reply_contract(sender(agent="reviewer"), "pwn;touch PWNED.md")
    assert "--ticket='pwn;touch PWNED.md'" in contract


def test_reply_contract_without_an_agent_name_is_unaddressable() -> None:
    contract = herdr_envelope.render_reply_contract(herdr_envelope.CallerContext(pane_id="w9:p2"))
    assert "cannot be addressed" in contract
    assert "uv run" not in contract


def test_reply_contract_documents_the_sha_guard_waiver_with_a_quoted_example() -> None:
    for contract in (
        herdr_envelope.render_reply_contract(sender(agent="reviewer"), "#228-waiver-doc"),
        herdr_envelope.render_reply_contract(sender(agent="reviewer")),
    ):
        assert "--allow-unresolvable-sha" in contract
        assert "'0c81f04c'" in contract
        assert "<TOKEN>" not in contract


# ── wrap_with_envelope: exact layout ───────────────────────────────────────────────────────────


def test_wrap_with_envelope_layout_is_stamp_envelope_delimiter_body_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stamp = "[2026-01-02T03:04:05.678Z]"
    monkeypatch.setattr(herdr_envelope, "utc_stamp", lambda: stamp)
    context = sender(agent="reviewer", label="reviewer", kind="pi", tab_id="w9:t1")
    envelope = herdr_envelope.render_envelope(
        context, receiver="reviewer", group_members=["reviewer@w9:p1"], tab_id="w9:t1"
    )
    contract = herdr_envelope.render_reply_contract(context)
    wrapped = herdr_envelope.wrap_with_envelope(
        "hi",
        context,
        group_members=["reviewer@w9:p1"],
        receiver="reviewer",
        tab_id="w9:t1",
    )
    assert wrapped == f"{stamp}\n{envelope}\n---\n\nhi\n\n{contract}"
    assert "\n---\n\nhi\n\n" in wrapped
    assert wrapped.endswith(contract)


# ── parse_envelope / split_envelope_and_body ───────────────────────────────────────────────────


def test_parse_envelope_round_trips_a_wrapped_payload() -> None:
    context = sender(
        label="review pane X",
        agent="reviewer",
        kind="pi",
        tab_id="w9:t1",
        cwd="/path/to/my project",
        resume_cmd="pi --session /tmp/session.jsonl",
    )
    receiver = herdr_envelope.CallerContext(pane_id="w1:p3", agent="impl-1", kind="agy")
    wrapped = herdr_envelope.wrap_with_envelope(
        "body text",
        context,
        group_members=["reviewer@w9:p1", "impl-1@w1:p3"],
        receiver=receiver,
        include_recovery=True,
        ticket_id="#182-herdr-msg-enhance",
        task_id="t7-impl",
        task_group="full-stack",
        tab_id="w9:t1",
    )
    envelope, body = herdr_envelope.split_envelope_and_body(wrapped)
    assert envelope is not None
    assert envelope.sender == herdr_envelope.sender_ref(context)
    assert envelope.group == ("reviewer@w9:p1", "impl-1@w1:p3")
    assert envelope.receiver == herdr_envelope.receiver_ref(receiver)
    assert envelope.task_group == "full-stack (w9:t1)"
    assert envelope.ticket_id == "#182-herdr-msg-enhance"
    assert envelope.task_id == "t7-impl"
    assert envelope.cwd == "/path/to/my project"
    assert envelope.resume == "pi --session /tmp/session.jsonl"
    assert envelope.protocol == herdr_envelope.SKILL_NOTICE
    assert body is not None
    assert body.startswith("body text\n\n")


def test_parse_envelope_reads_a_bare_envelope_without_a_stamp_or_delimiter() -> None:
    context = sender(agent="reviewer", label="reviewer", kind="pi")
    envelope = herdr_envelope.parse_envelope(herdr_envelope.render_envelope(context))
    assert envelope is not None
    assert envelope.sender == "reviewer@w1:p1 - kind pi"
    assert envelope.group == ()
    assert envelope.ticket_id == ""


def test_parse_envelope_unquotes_only_when_the_renderer_quoted() -> None:
    context = sender(cwd="/plain/path", resume_cmd="a#b")
    envelope = herdr_envelope.parse_envelope(
        herdr_envelope.render_envelope(context, include_recovery=True)
    )
    assert envelope is not None
    assert envelope.cwd == "/plain/path"
    assert envelope.resume == "a#b"


def test_split_envelope_and_body_refuses_non_envelope_text() -> None:
    assert herdr_envelope.parse_envelope("just a payload\nwith lines") is None
    assert herdr_envelope.split_envelope_and_body("just a payload") == (None, None)
    assert herdr_envelope.split_envelope_and_body("not an envelope\n---\n\nbody") == (None, None)


def test_parse_envelope_refuses_an_unknown_section_header() -> None:
    assert herdr_envelope.parse_envelope("Routing:\n  Sender: a@p\nBogus:\n") is None
