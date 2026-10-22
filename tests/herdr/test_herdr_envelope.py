"""Tests for skills/herdr/scripts/herdr_envelope.py (the A2A frontmatter envelope module).

Rendering is asserted line-for-line against the exact Format the dispatcher delivers; parsing is
asserted by round-trip (render → `yaml.safe_load`/`parse_envelope` → fields match) and by refusal
of every non-envelope text, the retired Style 2 blocks included. The contract is the ADR: a block
fenced by `---` on line 1, the four top-level keys, the canonical `status.state` names, the bare
ISO-8601 timestamp, then the Herdr skill notice on its own line and the payload. Emitter internals
(whose library, which quoting style) are deliberately not asserted — a generic Markdown
frontmatter reader must get the same values back, which is what these tests check.
"""

import re
from typing import Any, cast

import herdr_envelope
import herdr_evidence
import pytest
import yaml

# The bare ISO-8601 UTC grammar of `status.status.timestamp`: milliseconds, `Z`, no brackets.
TIMESTAMP_RE = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"

STAMP = "2026-01-02T03:04:05.678Z"

# The `id` a render with no task emits: `unlinked-` plus `STAMP` without its `-`/`:` separators.
# Hard-coded rather than derived so a renderer that rewrites the stamp differently stays caught.
UNLINKED_ID = "unlinked-20260102T030405678Z"

# Captured before the fixture below replaces the module attribute, so the grammar test still
# checks the real clock and not its own patch.
REAL_UTC_STAMP = herdr_envelope.utc_stamp


@pytest.fixture(autouse=True)
def frozen_stamp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the clock so line-for-line shape assertions are deterministic."""
    monkeypatch.setattr(herdr_envelope, "utc_stamp", lambda: STAMP)


def sender(**overrides: object) -> herdr_envelope.CallerContext:
    fields: dict[str, object] = {
        "pane_id": "w1:p1",
        "label": "orchestrator",
        "agent": "orchestrator",
    }
    _ = fields.update(overrides)
    return herdr_envelope.CallerContext(**fields)  # type: ignore[arg-type]


def frontmatter(block: str) -> dict[str, Any]:
    """The fenced block's content as a generic Markdown/YAML reader sees it."""
    lines = block.splitlines()
    assert lines[0] == "---" and lines[-1] == "---", (
        f"block is not fenced: {lines[:1] + lines[-1:]}"
    )
    parsed = yaml.safe_load("\n".join(lines[1:-1]))
    assert isinstance(parsed, dict)
    return cast("dict[str, Any]", parsed)


# ── _scalar: the hand-written routing ref form (never a frontmatter field) ──────────────────────


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


# ── refs and addresses ─────────────────────────────────────────────────────────────────────────


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


def test_address_of_a_resolved_pane_is_the_strict_agent_at_pane_form() -> None:
    receiver = sender(pane_id="w1:p3", label="impl-1", agent="impl-1", kind="agy", tab_id="w1:t1")
    assert herdr_envelope.address_of(receiver) == "impl-1@w1:p3"
    assert herdr_envelope.address_of("impl-1") == "impl-1"


# ── render_envelope: exact frontmatter shape ───────────────────────────────────────────────────


def test_render_envelope_is_a_fenced_block_of_the_four_top_level_keys() -> None:
    rendered = herdr_envelope.render_envelope(sender(kind="pi"), receiver="impl-1")
    assert rendered.splitlines() == [
        "---",
        f"id: {UNLINKED_ID}",
        "context_id: ''",
        "status:",
        "  state: TASK_STATE_WORKING",
        f"  timestamp: '{STAMP}'",
        "metadata:",
        "  sender: orchestrator@w1:p1",
        "  receiver: impl-1",
        "---",
    ]
    assert set(frontmatter(rendered)) == {"id", "context_id", "status", "metadata"}


def test_rendered_envelope_never_opens_with_a_bracketed_stamp() -> None:
    rendered = herdr_envelope.render_envelope(
        sender(),
        receiver="impl-1",
        ticket_id="#182-a2a-envelope",
        task_id="#182-a2a-envelope#t1-cutover",
        task_group="refactor-herdr",
        tab_id="w1:t1",
        in_reply_to="#182-a2a-envelope#impl-1",
    )
    lines = rendered.splitlines()
    assert lines[0] == "---"
    assert not any(line.startswith("[20") for line in lines)
    status = frontmatter(rendered)["status"]
    assert isinstance(status, dict)
    assert set(status) == {"state", "timestamp"}


def test_render_envelope_carries_the_correlation_metadata_in_order() -> None:
    rendered = herdr_envelope.render_envelope(
        sender(session_id="sess-9"),
        receiver=sender(pane_id="w1:p3", agent="impl-1"),
        ticket_id="#182-a2a-envelope",
        task_id="#182-a2a-envelope#t1-cutover",
        task_group="refactor-herdr",
        tab_id="w1:t1",
        in_reply_to="#182-a2a-envelope#impl-1",
    )
    assert frontmatter(rendered) == {
        "id": "#182-a2a-envelope#t1-cutover",
        "context_id": "sess-9",
        "status": {"state": "TASK_STATE_WORKING", "timestamp": STAMP},
        "metadata": {
            "ticket_id": "#182-a2a-envelope",
            "sender": "orchestrator@w1:p1",
            "receiver": "impl-1@w1:p3",
            "task_group": "refactor-herdr@w1:t1",
            "in_reply_to": "#182-a2a-envelope#impl-1",
        },
    }
    # Dict equality cannot see order, so the name's real property is checked on the rendered
    # lines themselves: the metadata block emits `ticket_id` first and `in_reply_to` last, and
    # a mutant that shuffles either keeps this list assertion, not just the parse above.
    lines = rendered.splitlines()
    metadata_at = lines.index("metadata:")
    assert lines[metadata_at + 1 : -1] == [
        "  ticket_id: '#182-a2a-envelope'",
        "  sender: orchestrator@w1:p1",
        "  receiver: impl-1@w1:p3",
        "  task_group: refactor-herdr@w1:t1",
        "  in_reply_to: '#182-a2a-envelope#impl-1'",
    ]


def test_render_envelope_renders_the_group_topology_as_a_list() -> None:
    rendered = herdr_envelope.render_envelope(
        sender(), group_members=["orchestrator@w1:p1", "impl-1@w1:p3"]
    )
    assert frontmatter(rendered)["metadata"]["group"] == [
        "orchestrator@w1:p1",
        "impl-1@w1:p3",
    ]


def test_render_envelope_recovery_metadata_appears_only_when_requested() -> None:
    context = sender(
        cwd="/path/to/my project", resume_cmd="pi --session /tmp/session.jsonl", kind="pi"
    )
    trimmed = frontmatter(herdr_envelope.render_envelope(context))["metadata"]
    assert "cwd" not in trimmed and "resume" not in trimmed
    recovery = frontmatter(herdr_envelope.render_envelope(context, include_recovery=True))[
        "metadata"
    ]
    assert recovery["cwd"] == "/path/to/my project"
    assert recovery["resume"] == "pi --session /tmp/session.jsonl"


def test_render_envelope_state_defaults_to_working_and_takes_what_is_given() -> None:
    rendered = herdr_envelope.render_envelope(sender(), state=herdr_envelope.STATE_COMPLETED)
    assert frontmatter(rendered)["status"]["state"] == "TASK_STATE_COMPLETED"


# ── render_envelope: `Task.id` is required, so it is never rendered empty (#182 h1) ────────────


@pytest.mark.parametrize("task_id", [None, ""])
def test_an_unlinked_render_replaces_the_empty_id_with_a_generated_one(
    task_id: str | None,
) -> None:
    """A2A requires `Task.id`, so no falsy task id may reach the wire as `''`.

    Pin -> mutant: restore `task_id or ""` and `id` renders `''` again, which a generic A2A
    parser cannot tell from a malformed document.
    """
    rendered = herdr_envelope.render_envelope(sender(), task_id=task_id)
    ident = frontmatter(rendered)["id"]
    assert ident != ""
    assert ident == UNLINKED_ID


def test_the_generated_id_is_the_compact_stamp_with_no_separators() -> None:
    """Exact shape under the frozen clock: `unlinked-` plus the stamp stripped of `-`, `:` and `.`."""
    ident = frontmatter(herdr_envelope.render_envelope(sender()))["id"]
    assert ident == "unlinked-20260102T030405678Z"
    stamp_part = ident.removeprefix("unlinked-")
    assert not any(ch in stamp_part for ch in "-:.")
    assert re.fullmatch(r"\d{8}T\d{9}Z", stamp_part)


def test_the_generated_id_is_built_through_the_module_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The fallback reads `utc_stamp()`, so freezing that clock freezes the id and the stamp alike.

    Pin -> mutant: build the fallback from `datetime.now()` directly and the id stops following
    the patched clock, so this reads the real time where the fixture pinned the stamp — and every
    line-for-line golden below drifts with it.
    """
    monkeypatch.setattr(herdr_envelope, "utc_stamp", lambda: "2026-12-31T23:59:59.001Z")
    rendered = frontmatter(herdr_envelope.render_envelope(sender()))
    assert rendered["id"] == "unlinked-20261231T235959001Z"
    assert rendered["status"]["timestamp"] == "2026-12-31T23:59:59.001Z"


def test_the_generated_id_matches_the_compact_grammar_on_the_real_clock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The unfrozen shape is still `unlinked-<compact stamp>`: the grammar holds for any clock."""
    monkeypatch.setattr(herdr_envelope, "utc_stamp", REAL_UTC_STAMP)
    ident = frontmatter(herdr_envelope.render_envelope(sender()))["id"]
    assert re.fullmatch(r"unlinked-\d{8}T\d{9}Z", ident)


def test_the_generated_id_never_reaches_the_correlation_metadata() -> None:
    """`unlinked-…` rides the `id` slot alone: an unlinked reply carries neither correlation key.

    Pin -> mutant: pass the generated id as `in_reply_to` (or `ticket_id`) as well and the
    metadata block advertises a correlation that no task holds.
    """
    rendered = herdr_envelope.render_envelope(sender(), ticket_id=None, in_reply_to=None)
    metadata = frontmatter(rendered)["metadata"]
    assert "ticket_id" not in metadata
    assert "in_reply_to" not in metadata
    lines = rendered.splitlines()
    metadata_block = "\n".join(lines[lines.index("metadata:") + 1 : -1])
    assert UNLINKED_ID not in metadata_block


def test_context_id_still_renders_empty_when_the_harness_knows_no_session() -> None:
    """The `id` fix must not spill into `context_id`: a session never observed stays `''`.

    Pin -> mutant: invent a session id alongside the task id and this positive blank fails.
    """
    rendered = frontmatter(herdr_envelope.render_envelope(sender()))
    assert rendered["id"] != ""
    assert rendered["context_id"] == ""


def test_a_linked_render_keeps_its_task_id_and_leaves_no_generated_id_behind() -> None:
    """A task that IS known renders verbatim: the fallback must not perturb a linked envelope."""
    rendered = herdr_envelope.render_envelope(sender(), task_id="#182-a2a-hardening#h1")
    assert frontmatter(rendered)["id"] == "#182-a2a-hardening#h1"
    assert UNLINKED_ID not in rendered


# ── stamping, quoting, and paging ──────────────────────────────────────────────────────────────


def test_utc_stamp_is_a_bare_iso8601_string_without_brackets() -> None:
    stamp = REAL_UTC_STAMP()
    assert re.match(TIMESTAMP_RE, stamp)
    assert not stamp.startswith("[")


def test_paging_delimiter_is_the_pinned_triple_dash() -> None:
    assert herdr_envelope.PAGING_DELIMITER == "---"


def test_timestamp_survives_the_yaml_reader_as_text_not_a_date() -> None:
    rendered = herdr_envelope.render_envelope(sender())
    status = frontmatter(rendered)["status"]
    assert isinstance(status["timestamp"], str)
    assert re.match(TIMESTAMP_RE, status["timestamp"])


def test_a_quoting_sensitive_ticket_id_survives_render_and_safe_load() -> None:
    rendered = herdr_envelope.render_envelope(
        sender(), ticket_id="#182: a2a/envelope", task_id="#182#t1: cutover"
    )
    assert frontmatter(rendered)["metadata"]["ticket_id"] == "#182: a2a/envelope"
    envelope = herdr_envelope.parse_envelope(rendered)
    assert envelope is not None
    assert envelope.ticket_id == "#182: a2a/envelope"
    assert envelope.id == "#182#t1: cutover"


def test_render_prelude_joins_the_block_the_skill_notice_and_the_page_break() -> None:
    block = herdr_envelope.render_envelope(sender())
    prelude = herdr_envelope.render_prelude(block)
    assert prelude == f"{block}\n{herdr_envelope.SKILL_NOTICE}\n\n"
    assert prelude.startswith(f"{block}\n")
    lines = prelude.splitlines()
    assert lines[0] == "---"
    assert lines[len(block.splitlines())] == herdr_envelope.SKILL_NOTICE
    assert lines[len(block.splitlines())].startswith("Herdr:")
    assert lines[-1] == ""


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


def test_reply_contract_states_what_makes_a_payload_complete() -> None:
    """#299: the contract names the evidence shape in one line, before the reply is sent.

    A callee that closes a lane with a summary payload learns here — not from a later
    `shape=incomplete` record — whether its payload counts as complete.
    """
    contract = herdr_envelope.render_reply_contract(sender(agent="reviewer"))
    lines = [line for line in contract.splitlines() if "COMPLETED payload is complete" in line]
    assert len(lines) == 1, contract
    assert "evidence heading" in lines[0], lines[0]
    assert "inline evidence label" in lines[0], lines[0]


# ── wrap_with_envelope: exact layout ───────────────────────────────────────────────────────────


def test_wrap_with_envelope_layout_is_block_notice_payload_contract() -> None:
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
    assert wrapped == f"{envelope}\n{herdr_envelope.SKILL_NOTICE}\n\nhi\n\n{contract}"
    assert wrapped.splitlines()[0] == "---"
    assert f"\n---\n{herdr_envelope.SKILL_NOTICE}\n\nhi\n\n" in wrapped
    assert wrapped.endswith(contract)


# ── status mapping ─────────────────────────────────────────────────────────────────────────────


def test_reply_state_maps_each_settled_status_to_a_canonical_task_state() -> None:
    assert herdr_envelope.reply_state("completed") == "TASK_STATE_COMPLETED"
    assert herdr_envelope.reply_state("blocked") == "TASK_STATE_INPUT_REQUIRED"
    assert herdr_envelope.reply_state("rework") == "TASK_STATE_FAILED"


def test_reply_state_vocabulary_is_bound_to_the_payload_status_map() -> None:
    """The two status vocabularies move together or this fails loudly.

    `herdr_evidence.STATUS_MAP` produces the tokens `REPLY_STATE_BY_STATUS` consumes: every
    producible token must have a canonical state and the table must hold no token the parser
    cannot emit. A fourth payload status added without its reply state (or the reverse) would
    otherwise silently render `TASK_STATE_WORKING` through the `reply_state` fallback.
    """
    assert set(herdr_envelope.REPLY_STATE_BY_STATUS) == set(herdr_evidence.STATUS_MAP.values())


def test_reply_state_of_an_unsettled_or_unknown_status_is_working() -> None:
    assert herdr_envelope.reply_state(None) == "TASK_STATE_WORKING"
    assert herdr_envelope.reply_state("") == "TASK_STATE_WORKING"
    assert herdr_envelope.reply_state("in_progress") == "TASK_STATE_WORKING"


def test_each_settled_reply_status_survives_render_and_parse() -> None:
    """Every mapping in `REPLY_STATE_BY_STATUS` rides the full render → fence → parse route."""
    for status, expected in (
        ("completed", "TASK_STATE_COMPLETED"),
        ("blocked", "TASK_STATE_INPUT_REQUIRED"),
        ("rework", "TASK_STATE_FAILED"),
    ):
        delivered = (
            herdr_envelope.render_prelude(
                herdr_envelope.render_envelope(sender(), state=herdr_envelope.reply_state(status))
            )
            + f"{status.upper()} body"
        )
        assert delivered.splitlines()[0] == "---"
        envelope, body = herdr_envelope.split_envelope_and_body(delivered)
        assert envelope is not None
        assert envelope.state == expected
        assert body == f"{status.upper()} body"


# ── parse_envelope / split_envelope_and_body ───────────────────────────────────────────────────


def test_parse_envelope_round_trips_a_delivered_payload() -> None:
    context = sender(
        agent="reviewer",
        label="review pane X",
        kind="pi",
        session_id="sess-42",
        tab_id="w9:t1",
        cwd="/path/to/my project",
        resume_cmd="pi --session /tmp/session.jsonl",
    )
    receiver = herdr_envelope.CallerContext(pane_id="w1:p3", agent="impl-1", kind="agy")
    delivered = (
        herdr_envelope.render_prelude(
            herdr_envelope.render_envelope(
                context,
                group_members=["reviewer@w9:p1", "impl-1@w1:p3"],
                receiver=receiver,
                include_recovery=True,
                ticket_id="#182-herdr-msg-enhance",
                task_id="t7-impl",
                task_group="full-stack",
                tab_id="w9:t1",
                in_reply_to="#182-herdr-msg-enhance#full-stack",
            )
        )
        + "body text"
    )
    envelope, body = herdr_envelope.split_envelope_and_body(delivered)
    assert envelope is not None
    assert envelope.id == "t7-impl"
    assert envelope.context_id == "sess-42"
    assert envelope.state == "TASK_STATE_WORKING"
    assert envelope.timestamp == STAMP
    assert envelope.sender == "reviewer@w1:p1"
    assert envelope.group == ("reviewer@w9:p1", "impl-1@w1:p3")
    assert envelope.receiver == "impl-1@w1:p3"
    assert envelope.task_group == "full-stack@w9:t1"
    assert envelope.ticket_id == "#182-herdr-msg-enhance"
    assert envelope.in_reply_to == "#182-herdr-msg-enhance#full-stack"
    assert envelope.cwd == "/path/to/my project"
    assert envelope.resume == "pi --session /tmp/session.jsonl"
    assert body is not None
    assert body == "body text"


def test_parse_envelope_round_trips_the_reply_state() -> None:
    context = sender(agent="impl-1", session_id="sess-7")
    delivered = (
        herdr_envelope.render_prelude(
            herdr_envelope.render_envelope(
                context,
                receiver="orchestrator@w1:p1",
                state=herdr_envelope.reply_state("blocked"),
            )
        )
        + "BLOCKED need a decision"
    )
    envelope, _body = herdr_envelope.split_envelope_and_body(delivered)
    assert envelope is not None
    assert envelope.state == "TASK_STATE_INPUT_REQUIRED"


def test_parse_envelope_reads_a_bare_block_with_no_notice_or_payload() -> None:
    context = sender(agent="reviewer", label="reviewer", kind="pi", session_id="sess-1")
    envelope = herdr_envelope.parse_envelope(herdr_envelope.render_envelope(context))
    assert envelope is not None
    assert envelope.sender == "reviewer@w1:p1"
    assert envelope.context_id == "sess-1"
    assert envelope.group == ()
    assert envelope.ticket_id == ""


def test_split_envelope_and_body_refuses_non_envelope_text() -> None:
    assert herdr_envelope.parse_envelope("just a payload\nwith lines") is None
    assert herdr_envelope.split_envelope_and_body("just a payload") == (None, None)
    assert herdr_envelope.split_envelope_and_body("not an envelope\n---\n\nbody") == (None, None)


def test_parse_envelope_refuses_the_retired_style_2_without_a_shim() -> None:
    assert herdr_envelope.parse_envelope("Routing:\n  Sender: a@p\n") is None
    assert herdr_envelope.split_envelope_and_body("Routing:\n  Sender: a@p\n---\n\nbody") == (
        None,
        None,
    )
    legacy = "Routing:\n  Sender: a@p\nHierarchy:\n  Group: [a@p]\n---\n\nbody"
    assert herdr_envelope.split_envelope_and_body(legacy) == (None, None)


def test_parse_envelope_refuses_a_block_with_an_unknown_key() -> None:
    assert herdr_envelope.parse_envelope("---\nid: t\nBogus: x\n---\n") is None
    assert (
        herdr_envelope.parse_envelope("---\nid: t\nstatus:\n  state: x\n  mood: y\n---\n") is None
    )
    assert (
        herdr_envelope.parse_envelope("---\nid: t\nstatus: {}\nmetadata:\n  hop: x\n---\n") is None
    )


def test_parse_envelope_refuses_malformed_yaml_and_a_non_mapping_block() -> None:
    assert herdr_envelope.parse_envelope("---\nid: [unclosed\n---\n") is None
    assert herdr_envelope.parse_envelope("---\n- just\n- a\n- list\n---\n") is None


# ── caller-facing delivery summary (#259, anchor addendum) ─────────────────────────────────────


def delivered_copy(receiver: str = "orchestrator") -> str:
    block = herdr_envelope.render_envelope(
        herdr_envelope.CallerContext(pane_id="w9:p1", agent="reviewer"), receiver=receiver
    )
    return f"{herdr_envelope.render_prelude(block)}body text"


def test_caller_anchor_names_agent_at_pane_and_falls_back_to_the_bare_pane() -> None:
    assert (
        herdr_envelope.caller_anchor(sender(agent="reviewer", pane_id="w9:p1")) == "reviewer@w9:p1"
    )
    assert herdr_envelope.caller_anchor(herdr_envelope.CallerContext(pane_id="w11:p1")) == "w11:p1"


def test_render_envelope_delivers_the_receiver_as_a_bare_address() -> None:
    rendered = herdr_envelope.render_envelope(sender(), receiver="impl-1")
    assert frontmatter(rendered)["metadata"]["receiver"] == "impl-1"
    assert "(You)" not in rendered


def test_envelope_metadata_lines_returns_the_block_without_fences_or_notice() -> None:
    lines = herdr_envelope.envelope_metadata_lines(delivered_copy())
    assert "---" not in lines
    assert not any(line.startswith("Herdr:") for line in lines)
    assert "  receiver: orchestrator" in lines
    assert "  sender: reviewer@w9:p1" in lines
    assert lines[0] == f"id: {UNLINKED_ID}"


def test_envelope_metadata_lines_refuses_text_without_a_fenced_block() -> None:
    assert herdr_envelope.envelope_metadata_lines("no envelope here") == []
    assert (
        herdr_envelope.envelope_metadata_lines(
            f"Routing:\n  Sender: a@p\n{herdr_envelope.SKILL_NOTICE}\n\nb"
        )
        == []
    )


def test_format_delivery_summary_leads_with_the_status_line_then_two_delimiters() -> None:
    rendered = herdr_envelope.format_delivery_summary(
        "[You: reviewer@w9:p1] prompted orchestrator", delivered_copy(), "body text", "File: t.md"
    )
    assert rendered.splitlines() == [
        "[You: reviewer@w9:p1] prompted orchestrator",
        "---",
        f"id: {UNLINKED_ID}",
        "context_id: ''",
        "status:",
        "  state: TASK_STATE_WORKING",
        f"  timestamp: '{STAMP}'",
        "metadata:",
        "  sender: reviewer@w9:p1",
        "  receiver: orchestrator",
        "---",
        "File: t.md",
        "body text",
    ]
