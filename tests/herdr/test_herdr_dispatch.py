"""Tests for skills/herdr/scripts/herdr_dispatch.py (herdr-dispatch helper).

Integration cases route through the shared stub `herdr`.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import herdr_cli
import herdr_dispatch
import herdr_prompt
import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness

SCRIPT = SCRIPTS_DIR / "herdr_dispatch.py"


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPT)


def payload_file(tmp_path: Path, text: str = "TICKET BODY") -> Path:
    path = tmp_path / "ticket.md"
    _ = path.write_text(text, encoding="utf-8")
    return path


def test_dispatch_requires_file(stub: StubHarness) -> None:
    done = stub.run("callee")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "--file" in done.stderr
    assert stub.prompts() == []


def test_derive_ticket_id_prefers_hash_prefixed_stem() -> None:
    assert (
        herdr_dispatch.derive_ticket_id("tickets/#182-herdr-msg-enhance.md")
        == "#182-herdr-msg-enhance"
    )
    assert herdr_dispatch.derive_ticket_id("#182-herdr-msg-enhance.md") == "#182-herdr-msg-enhance"


def test_derive_ticket_id_numbers_a_leading_digit_stem() -> None:
    assert (
        herdr_dispatch.derive_ticket_id("tickets/182-herdr-msg-enhance.md")
        == "#182-herdr-msg-enhance"
    )
    assert herdr_dispatch.derive_ticket_id("182-foo.md") == "#182-foo"
    assert herdr_dispatch.derive_ticket_id("182_foo.md") == "#182_foo"
    assert herdr_dispatch.derive_ticket_id("42.md") == "#42"


def test_derive_ticket_id_keeps_a_non_numeric_stem_verbatim() -> None:
    assert herdr_dispatch.derive_ticket_id("PROJ-182-oauth-refresh.md") == "PROJ-182-oauth-refresh"


def test_derive_ticket_id_returns_none_for_stdin() -> None:
    assert herdr_dispatch.derive_ticket_id("-") is None


def test_dispatch_persists_derived_ids_and_renders_hierarchy(
    stub: StubHarness, tmp_path: Path
) -> None:
    import herdr_lease

    ticket = tmp_path / "182-herdr-msg-enhance.md"
    _ = ticket.write_text("TICKET BODY", encoding="utf-8")
    done = stub.run("reviewer", "--file", str(ticket), "--no-wait", env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    lease = herdr_lease.get_lease("reviewer", base_dir=tmp_path)
    assert lease is not None
    assert lease["ticket_id"] == "#182-herdr-msg-enhance"
    assert lease["task_id"] == "#182-herdr-msg-enhance"
    (call,) = stub.prompts()
    text = call[4]
    assert "  Ticket-ID: #182-herdr-msg-enhance" in text
    assert "  Task-ID: #182-herdr-msg-enhance" in text


def test_dispatch_explicit_ids_override_derivation(stub: StubHarness, tmp_path: Path) -> None:
    import herdr_lease

    ticket = payload_file(tmp_path, "TICKET BODY")
    done = stub.run(
        "reviewer",
        "--file",
        str(ticket),
        "--no-wait",
        "--ticket-id",
        "#182-herdr-msg-enhance",
        "--task-id",
        "#182-herdr-msg-enhance#full-stack",
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    lease = herdr_lease.get_lease("reviewer", base_dir=tmp_path)
    assert lease is not None
    assert lease["ticket_id"] == "#182-herdr-msg-enhance"
    assert lease["task_id"] == "#182-herdr-msg-enhance#full-stack"
    (call,) = stub.prompts()
    assert "  Ticket-ID: #182-herdr-msg-enhance" in call[4]
    assert "  Task-ID: #182-herdr-msg-enhance#full-stack" in call[4]


def test_dispatch_injects_caller_context_and_reply_contract(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "do this")), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[1:4] == ["agent", "prompt", "reviewer"]
    text = call[4]
    lines = text.splitlines()
    assert re.match(r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z\]$", lines[0])
    assert lines[1:13] == [
        "Routing:",
        "  Sender: reviewer@w9:p1 - tab w9:t1 - kind pi",
        "  Group: [reviewer@w9:p1]",
        "  Receiver(You): reviewer@w9:p1 - tab w9:t1 - kind pi",
        "Hierarchy:",
        "  Task-Group: w9:t1",
        "  Ticket-ID: ticket",
        "  Task-ID: ticket",
        "Runtime:",
        "  Cwd: /tmp/harness",
        "Protocol:",
        f"  {herdr_prompt.SKILL_NOTICE}",
    ]
    assert "Group: [reviewer@w9:p1]" in text
    assert "Receiver(You): reviewer@w9:p1 - tab w9:t1 - kind pi" in text
    assert "Herdr: see skill ~/.agents/skills/herdr/SKILL.md" in text
    assert "\n\ndo this\n\n" in text
    assert (
        'uv run ~/.agents/skills/herdr/scripts/herdr_reply.py reviewer "<STATUS> <artifacts> <issues>"'
        in text
    )


def test_dispatch_refuses_agent_kind(stub: StubHarness, tmp_path: Path) -> None:
    state = {
        **DEFAULT_STATE,
        "agents": [{"pane_id": "w9:p2", "name": "t7-impl", "agent": "qodercli"}],
    }
    done = stub.run("qodercli", "--file", str(payload_file(tmp_path)), state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "is an agent kind" in done.stderr
    assert "live agent names: t7-impl" in done.stderr
    assert stub.prompts() == []


def test_dispatch_refuses_qoderclicn_agent_kind(stub: StubHarness, tmp_path: Path) -> None:
    state = {
        **DEFAULT_STATE,
        "agents": [{"pane_id": "w9:p2", "name": "t7-impl", "agent": "qoderclicn"}],
    }
    done = stub.run("qoderclicn", "--file", str(payload_file(tmp_path)), state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "is an agent kind" in done.stderr
    assert "live agent names: t7-impl" in done.stderr
    assert stub.prompts() == []


def test_dispatch_reports_delivery_revision(stub: StubHarness, tmp_path: Path) -> None:
    state = {
        **DEFAULT_STATE,
        "agent_get_rev_seq": {"reviewer": ["r99"]},
        "agent_get": {"reviewer": {"pane_id": "w9:p1"}},
    }
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "prompted reviewer" in done.stdout
    assert "revision=r99" in done.stdout


def test_dispatch_constant_revision_accepted_without_retry(
    stub: StubHarness, tmp_path: Path
) -> None:
    state = {
        **DEFAULT_STATE,
        "agent_get_rev_seq": {"reviewer": ["r1", "r1", "r1"]},
    }
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "prompt dropped" not in done.stderr
    assert len(stub.prompts()) == 1


def test_dispatch_refuses_when_target_has_active_lease(stub: StubHarness, tmp_path: Path) -> None:
    import herdr_lease

    _ = herdr_lease.acquire_lease("reviewer", "old_ticket.md", "orch-1", base_dir=tmp_path)
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert (
        "target reviewer has an active ticket lease (old_ticket.md) issued by orch-1. Await reply or pass --force"
        in done.stderr
    )
    assert stub.prompts() == []


def test_dispatch_force_bypasses_active_lease(stub: StubHarness, tmp_path: Path) -> None:
    import herdr_lease

    _ = herdr_lease.acquire_lease("reviewer", "old_ticket.md", "orch-1", base_dir=tmp_path)
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        "--force",
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert len(stub.prompts()) == 1
    lease = herdr_lease.get_lease("reviewer", base_dir=tmp_path)
    assert lease is not None
    assert lease["ticket"] == str(payload_file(tmp_path))


def test_dispatch_acquires_lease_on_successful_dispatch(stub: StubHarness, tmp_path: Path) -> None:
    import herdr_lease

    ticket = payload_file(tmp_path, "ticket content")
    done = stub.run(
        "reviewer",
        "--file",
        str(ticket),
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    lease = herdr_lease.get_lease("reviewer", base_dir=tmp_path)
    assert lease is not None
    assert lease["ticket"] == str(ticket)
    assert lease["caller"] == "reviewer"


def test_dispatch_accepts_revision_zero_without_retry(stub: StubHarness, tmp_path: Path) -> None:
    """Inherits the herdr-prompt fix: revision-0 (agy) exit 0 is accepted, never re-sent."""
    state = {
        **DEFAULT_STATE,
        "agent_get_rev_seq": {"reviewer": ["0", "0"]},
    }
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "prompt dropped" not in done.stderr
    assert len(stub.prompts()) == 1


def test_dispatch_dry_run_prints_argv(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "dry")), "--dry-run")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    from typing import cast

    parsed = cast(object, json.loads(done.stdout))
    assert isinstance(parsed, list)
    assert parsed[3] == "reviewer"
    assert "Sender: reviewer@w9:p1 - tab w9:t1 - kind pi" in str(parsed[4])
    assert "Receiver(You): reviewer@w9:p1 - tab w9:t1 - kind pi" in str(parsed[4])


def test_dispatch_rolls_back_lease_on_blocked_outcome(stub: StubHarness, tmp_path: Path) -> None:
    import herdr_lease

    error = {"code": "agent_blocked", "message": "agent reviewer is blocked"}
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        env={"PWD": str(tmp_path)},
        state={**DEFAULT_STATE, "prompt_error": error},
    )
    assert done.returncode == herdr_cli.EXIT_BLOCKED
    assert herdr_lease.get_lease("reviewer", base_dir=tmp_path) is None


def test_dispatch_rolls_back_lease_on_herdr_failure(stub: StubHarness, tmp_path: Path) -> None:
    import herdr_lease

    error = {"code": "agent_crashed", "message": "agent target crashed"}
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        env={"PWD": str(tmp_path)},
        state={**DEFAULT_STATE, "prompt_error": error},
    )
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert herdr_lease.get_lease("reviewer", base_dir=tmp_path) is None


def test_dispatch_retains_lease_on_wait_timeout(stub: StubHarness, tmp_path: Path) -> None:
    import herdr_lease

    error = {"code": "timeout", "message": "wait timed out"}
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        "--wait",
        env={"PWD": str(tmp_path)},
        state={**DEFAULT_STATE, "prompt_error": error},
    )
    assert done.returncode == 4
    lease = herdr_lease.get_lease("reviewer", base_dir=tmp_path)
    assert lease is not None
    assert lease["target"] == "reviewer"


def test_dispatch_records_pane_id_and_canonical_name(stub: StubHarness, tmp_path: Path) -> None:
    import herdr_lease

    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    lease = herdr_lease.get_lease("reviewer", base_dir=tmp_path)
    assert lease is not None
    assert lease["target"] == "reviewer"
    assert lease.get("pane_id") == "w9:p1"
    assert herdr_lease.get_lease("w9:p1", base_dir=tmp_path) == lease


def test_pep723_metadata_precedes_docstring() -> None:
    header = SCRIPT.read_text().split('"""', 1)[0]
    assert header.startswith("#!/usr/bin/env python3\n")
    assert "# /// script" in header
    assert 'requires-python = ">=3.14"' in header
    assert "dependencies = []" in header
    assert header.rstrip().endswith("# ///")


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv is required for the PEP 723 runner")
def test_uv_run_help_executes_without_path_configuration(tmp_path: Path) -> None:
    done = subprocess.run(
        ["uv", "run", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
        env={"HOME": os.environ.get("HOME", ""), "PATH": os.environ.get("PATH", "")},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "usage: herdr-dispatch" in done.stdout


def test_dispatch_draft_prints_skeleton_with_prefilled_routing(stub: StubHarness) -> None:
    done = stub.run("callee", "--draft")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    assert "- Sender: reviewer@w9:p1 - tab w9:t1 - kind pi" in done.stdout
    assert "- Receiver: callee" in done.stdout
    assert re.search(r"^- Drafted: \[\d{4}-\d{2}-\d{2}T", done.stdout, re.MULTILINE)
    assert "## Task" in done.stdout
    assert "## Context" in done.stdout
    assert "## Acceptance criteria" in done.stdout
    assert "herdr-draft: unfilled" in done.stdout


def test_dispatch_draft_writes_skeleton_to_file(stub: StubHarness, tmp_path: Path) -> None:
    path = tmp_path / "draft.md"
    done = stub.run("callee", "--draft", "--file", str(path))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    assert "## Task" not in done.stdout
    skeleton = path.read_text(encoding="utf-8")
    assert "- Sender: reviewer@w9:p1 - tab w9:t1 - kind pi" in skeleton
    assert "- Receiver: callee" in skeleton


def test_dispatch_accepts_free_form_ticket_with_braces(stub: StubHarness, tmp_path: Path) -> None:
    """`{{...}}` is a diagnostic, never a rejection reason on its own."""
    ticket = payload_file(tmp_path, "Ship it to {{branch}} on {{host}}.")
    done = stub.run("callee", "--file", str(ticket), "--dry-run")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr


def test_dispatch_refuses_live_draft_marker(stub: StubHarness, tmp_path: Path) -> None:
    ticket = payload_file(
        tmp_path,
        "<!-- herdr-draft: unfilled — fill Task/Context/Acceptance, then delete this line. -->\n\n"
        "## Task\n\nShip {{branch}}.\n\n## Context\n\nSome context.\n\n"
        "## Acceptance criteria\n\nTests pass.\n",
    )
    done = stub.run("callee", "--file", str(ticket), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "still carries the draft marker" in done.stderr
    assert "{{branch}}" in done.stderr
    assert stub.prompts() == []


def test_dispatch_refuses_untouched_skeleton(stub: StubHarness, tmp_path: Path) -> None:
    ticket = payload_file(
        tmp_path,
        "## Routing\n\n- Sender: reviewer@w9:p1\n\n## Task\n\n## Context\n\n## Acceptance criteria\n",
    )
    done = stub.run("callee", "--file", str(ticket), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "empty Task/Context/Acceptance sections" in done.stderr
    assert stub.prompts() == []


def test_dispatch_accepts_filled_skeleton_dry_run(stub: StubHarness, tmp_path: Path) -> None:
    ticket = payload_file(
        tmp_path,
        "## Task\n\nShip the fix.\n\n## Context\n\n\n## Acceptance criteria\n",
    )
    done = stub.run("callee", "--file", str(ticket), "--dry-run")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
