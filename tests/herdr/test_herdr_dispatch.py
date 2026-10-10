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

import herdr_bootstrap
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
    assert lines[1:11] == [
        "Routing:",
        "  Sender: reviewer@w9:p1 - tab w9:t1 - kind pi",
        "  Group: [reviewer@w9:p1]",
        "  Receiver(You): reviewer@w9:p1 - tab w9:t1 - kind pi",
        "Hierarchy:",
        "  Task-Group: w9:t1",
        "  Ticket-ID: ticket",
        "  Task-ID: ticket",
        "Protocol:",
        f"  {herdr_prompt.SKILL_NOTICE}",
    ]
    assert "Runtime:" not in text
    assert "Cwd:" not in text
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


def test_dispatch_releases_lease_whose_recorded_pane_is_gone(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Issue #210: a lease naming a closed pane must not block follow-up work without --force."""
    import herdr_lease

    _ = herdr_lease.acquire_lease(
        "reviewer", "round-1.md", "orch-1", pane_id="wZ:pQ", base_dir=tmp_path
    )
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "releasing the stale lease for reviewer" in done.stderr
    assert "(pane wZ:pQ no longer exists)" in done.stderr
    assert len(stub.prompts()) == 1
    lease = herdr_lease.get_lease("reviewer", base_dir=tmp_path)
    assert lease is not None and lease["ticket"] == str(payload_file(tmp_path))


def test_dispatch_refuses_lease_whose_recorded_pane_is_alive(
    stub: StubHarness, tmp_path: Path
) -> None:
    """A live pane keeps the conflict real, so --force stays the only override."""
    import herdr_lease

    _ = herdr_lease.acquire_lease(
        "reviewer", "round-1.md", "orch-1", pane_id="w9:p1", base_dir=tmp_path
    )
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "active ticket lease (round-1.md)" in done.stderr
    assert stub.prompts() == []


# ── #234: a label that outlived its agent is reported during a normal dispatch ─────


def test_dispatch_reports_a_label_whose_agent_has_exited(stub: StubHarness, tmp_path: Path) -> None:
    """A normal dispatch reports the orphaned label; no operator --verify/--sync pass is run.

    Pin -> mutant: build the staleness rows from the *agent* inventory (the #234 defect),
    so the exited pane is invisible and this advisory never prints.
    """
    state = {
        **DEFAULT_STATE,
        "panes": [
            {"pane_id": "w9:p1", "label": "reviewer", "agent": "pi", "agent_status": "working"},
            {"pane_id": "w9:p2", "label": "buildbot", "agent": None, "agent_status": "unknown"},
        ],
        "agents": [
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi", "agent_status": "working"}
        ],
    }
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        "--no-wait",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "w9:p2" in done.stderr
    assert "buildbot" in done.stderr
    # The operator ran no verification pass: the dispatch itself reported the staleness.
    assert "--verify" not in done.stderr
    # The remedy must name a command that acts on the orphan (#234 rework). `--sync` cannot:
    # it converges label/agent pairs from the agent inventory, where this orphan is absent.
    assert "herdr-label --clear --pane w9:p2" in done.stderr
    assert "--sync" not in done.stderr
    assert len(stub.prompts()) == 1


def test_dispatch_reports_an_orphan_whose_name_is_live_on_another_pane(
    stub: StubHarness, tmp_path: Path
) -> None:
    """The orphaned pane is reported end to end although its label names a live sibling.

    `reviewer` is live on `w9:p1`; `w9:p2` keeps the label `reviewer` with no live agent in
    it, so a normal dispatch must still report it.

    Pin -> mutant: build the name-match from every agent row (`label in live_names`), so the
    live name on another pane suppresses the advisory and stderr is empty here.
    """
    state = {
        **DEFAULT_STATE,
        "panes": [
            {"pane_id": "w9:p1", "label": "reviewer", "agent": "pi", "agent_status": "working"},
            {"pane_id": "w9:p2", "label": "reviewer", "agent": None, "agent_status": "unknown"},
        ],
        "agents": [
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi", "agent_status": "working"}
        ],
    }
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        "--no-wait",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "w9:p2" in done.stderr
    assert len(stub.prompts()) == 1


def test_dispatch_advisory_tells_the_operator_to_replace_the_name_placeholder(
    stub: StubHarness, tmp_path: Path
) -> None:
    """The re-label template cannot be copied verbatim into a literal `<name>` label.

    `herdr-label '<name>' --pane w9:p2` on an orphan exits 0 and writes the literal `<name>`,
    because `validate_agent_name` does not fire without a live agent, so the advisory must tell
    the operator to substitute.

    Pin -> mutant: print the bare copy-pasteable template (`herdr-label <name> --pane w9:p2`)
    with no substitution instruction, so stderr lacks the hint and this fails.
    """
    state = {
        **DEFAULT_STATE,
        "panes": [
            {"pane_id": "w9:p1", "label": "reviewer", "agent": "pi", "agent_status": "working"},
            {"pane_id": "w9:p2", "label": "buildbot", "agent": None, "agent_status": "unknown"},
        ],
        "agents": [
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi", "agent_status": "working"}
        ],
    }
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        "--no-wait",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "replace `<name>`" in done.stderr


def test_dispatch_reports_no_stale_label_when_every_label_has_its_agent(
    stub: StubHarness, tmp_path: Path
) -> None:
    """A live label matching its live agent is never reported stale (no false positives).

    Pin -> mutant: drop the `pane_id not in live_panes` filter, so the live `w9:p1` row is
    also reported and the advisory prints for a healthy lane.
    """
    state = {
        **DEFAULT_STATE,
        "panes": [
            {"pane_id": "w9:p1", "label": "reviewer", "agent": "pi", "agent_status": "working"},
            {"pane_id": "w9:p2", "label": "buildbot", "agent": "pi", "agent_status": "idle"},
        ],
        "agents": [
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi", "agent_status": "working"},
            {"pane_id": "w9:p2", "name": "buildbot", "agent": "pi", "agent_status": "idle"},
        ],
    }
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        "--no-wait",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "outlived" not in done.stderr


def test_report_stale_labels_is_silent_when_the_pane_inventory_is_unreadable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Positivist (#210): an unreadable pane inventory answers nothing, so nothing is reported.

    Pin -> mutant: remove the `try/except` around the inventory read, so a `pane list`
    failure propagates instead of leaving the advisory silent.
    """
    bin_dir = tmp_path / "fake-bin"
    bin_dir.mkdir()
    fake = bin_dir / "herdr"
    _ = fake.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "args = sys.argv[1:]\n"
        "if args[:2] == ['pane', 'list']:\n"
        "    sys.exit(1)\n"
        "if args[:2] == ['agent', 'list']:\n"
        "    print(json.dumps({'result': {'agents': [{'pane_id': 'w9:p1', 'name': 'reviewer'}]}}))\n"
        "    sys.exit(0)\n"
        "sys.exit(0)\n"
    )
    os.chmod(fake, 0o755)
    real_path = os.environ.get("PATH", "")
    herdr_dispatch.report_stale_labels(str(fake), {"PATH": f"{bin_dir}:{real_path}"})
    assert capsys.readouterr().err == ""


def test_dispatch_identity_comes_from_the_agent_inventory_not_the_label(
    stub: StubHarness,
) -> None:
    """Dispatch targeting resolves by identifier: a reused label does not move the identity.

    Pin -> mutant: match `target` against the pane *label* in `resolve_target_identity`, so
    ownership comes from decoration; the first assert then returns `(\"reviewer\", None)`.
    """
    state = {
        **DEFAULT_STATE,
        "panes": [
            {
                "pane_id": "w9:p1",
                "label": "reused-elsewhere",
                "agent": "pi",
                "agent_status": "working",
            },
            {"pane_id": "w9:p2", "label": "reviewer", "agent": None, "agent_status": "unknown"},
        ],
        "agents": [
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi", "agent_status": "working"}
        ],
    }
    stub.write_state(state)
    env = stub.base_env()
    herdr = str(stub.herdr)
    assert herdr_dispatch.resolve_target_identity(herdr, "reviewer", env) == ("reviewer", "w9:p1")
    assert herdr_dispatch.resolve_target_identity(herdr, "w9:p1", env) == ("reviewer", "w9:p1")


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


def test_dispatch_persists_caller_recovery_without_invented_keys(
    stub: StubHarness, tmp_path: Path
) -> None:
    import herdr_lease

    ticket = tmp_path / "182-herdr-msg-enhance.md"
    _ = ticket.write_text("TICKET BODY", encoding="utf-8")
    done = stub.run("reviewer", "--file", str(ticket), "--no-wait", env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    task = herdr_lease.get_task("#182-herdr-msg-enhance", base_dir=tmp_path)
    assert task is not None
    recovery = task["caller_recovery"]
    assert recovery["pane_id"] == "w9:p1"
    assert recovery["kind"] == "pi"
    assert recovery["cwd"] == "/tmp/harness"
    # The default stub caller has no session, so these keys must never appear.
    assert "session_path" not in recovery
    assert "resume_cmd" not in recovery


def test_dispatch_multi_hop_same_task_id_preserves_trajectory(
    stub: StubHarness, tmp_path: Path
) -> None:
    import herdr_lease

    task_id = "#182-herdr-msg-enhance#full-stack"
    ticket = payload_file(tmp_path, "TICKET BODY")
    first = stub.run(
        "reviewer",
        "--file",
        str(ticket),
        "--task-id",
        task_id,
        env={"PWD": str(tmp_path)},
    )
    assert first.returncode == herdr_cli.EXIT_OK, first.stderr

    second = stub.run(
        "callee2",
        "--file",
        str(ticket),
        "--task-id",
        task_id,
        env={"PWD": str(tmp_path), "HERDR_PANE_ID": "w9:p2"},
    )
    assert second.returncode == herdr_cli.EXIT_OK, second.stderr

    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    trajectory = task["trajectory"]
    assert [event["seq"] for event in trajectory] == [1, 2]
    assert [event["event"] for event in trajectory] == ["dispatched", "dispatched"]
    assert task["status"] == "dispatched"
    assert task["assignee"] == "callee2"
    assert task["caller_recovery"] == {"pane_id": "w9:p2", "cwd": "/tmp/scratch"}


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
    assert 'dependencies = ["pyyaml"]' in header
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


def test_dispatch_auto_start_bootstraps_missing_agent_with_trust_flags(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Issue #225: a ticket for a role with no live agent starts it via the
    bootstrap contract (kind trust flags + ROLE INVARIANT), then dispatches.

    The invariant reaches the agent as the absolute path of the lane-local snippet file,
    because herdr refuses a multi-line agent arg; read that file to prove delivery.
    """
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": str(tmp_path),
                "label": "callee",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    ticket = payload_file(tmp_path, "TICKET BODY")
    done = stub.run(
        "callee",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "pi",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (start,) = stub.starts()
    assert start[3] == "callee"
    assert "--kind" in start and start[start.index("--kind") + 1] == "pi"
    assert "--append-system-prompt" in start
    invariant = start[start.index("--append-system-prompt") + 1]
    assert invariant == str(tmp_path / ".lane" / "role-invariant.md")
    assert Path(invariant).is_absolute()
    assert Path(invariant).read_text() == herdr_bootstrap.render_invariant("callee")
    for arg in start[start.index("--") + 1 :]:
        assert "\n" not in arg
    split = start.index("--")
    assert "--append-system-prompt" not in start[:split]
    assert "--model" not in start[:split]
    assert "--append-system-prompt" in start[split + 1 :]
    assert start[-1] == "--approve"
    (prompt,) = stub.prompts()
    assert prompt[3] == "callee"


def test_dispatch_auto_start_skips_bootstrap_for_live_agent(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Issue #225: a live bootstrapped agent gets the ticket with no extra start."""
    ticket = payload_file(tmp_path, "TICKET BODY")
    done = stub.run(
        "reviewer",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "pi",
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.starts() == []
    (prompt,) = stub.prompts()
    assert prompt[3] == "reviewer"


def test_dispatch_auto_start_dry_run_shows_plan_without_mutating(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Issue #225: dry-run shows the would-bootstrap plan without starting."""
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": "/tmp",
                "label": "callee",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    ticket = payload_file(tmp_path, "TICKET BODY")
    done = stub.run(
        "callee",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "pi",
        "--dry-run",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.starts() == []
    assert stub.prompts() == []
    assert "callee" in done.stdout
    assert "pi" in done.stdout


def test_dispatch_auto_start_rejects_unknown_kind(stub: StubHarness, tmp_path: Path) -> None:
    """Issue #225: an unrecognized --auto-start kind fails before any mutation."""
    ticket = payload_file(tmp_path, "TICKET BODY")
    done = stub.run(
        "callee",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "notakind",
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not a recognized agent kind" in done.stderr
    assert stub.starts() == []
    assert stub.prompts() == []


def test_dispatch_auto_start_uses_claude_trust_flags(stub: StubHarness, tmp_path: Path) -> None:
    """Issue #225: the bootstrap contract owns trust flags (claude path)."""
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": str(tmp_path),
                "label": "callee",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    ticket = payload_file(tmp_path, "TICKET BODY")
    done = stub.run(
        "callee",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "claude",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (start,) = stub.starts()
    assert start[start.index("--kind") + 1] == "claude"
    split = start.index("--")
    assert "--append-system-prompt" not in start[:split]
    assert "--model" not in start[:split]
    assert "--append-system-prompt" in start[split + 1 :]
    assert start[-1] == "--dangerously-skip-permissions"
    assert "--append-system-prompt" in start


def test_dispatch_auto_start_without_flag_keeps_bare_shell_refusal(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Issue #225: without --auto-start a missing agent still refuses safely."""
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": "/tmp",
                "label": "callee",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    ticket = payload_file(tmp_path, "TICKET BODY")
    done = stub.run(
        "callee",
        "--file",
        str(ticket),
        "--no-wait",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "no live agent" in done.stderr
    assert stub.starts() == []
    assert stub.prompts() == []


def test_dispatch_auto_start_triggers_on_typed_signal_despite_reworded_prose(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """HIGH 1: the hook keys on BareShellRefusal, not herdr_cli prose.

    Rewords both bare-shell diagnostic messages; auto-start must still fire.
    Fails if is_bare_shell_failure is re-coupled to message text.
    """
    import herdr_cli

    orig_format = herdr_cli.format_shell_pane_diagnostic

    def reworded(**kwargs: object) -> str:
        return "REWORDED DIAGNOSTIC — no trigger phrases here"

    monkeypatch.setattr(herdr_cli, "format_shell_pane_diagnostic", reworded)
    probe = orig_format(target="x", pane_id="wM:p1N", label=None, foreground_proc="zsh")
    assert "no live agent" in probe or "has no live agent" in probe
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": str(tmp_path),
                "label": "callee",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    ticket = payload_file(tmp_path, "TICKET BODY")
    done = stub.run(
        "callee",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "pi",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (start,) = stub.starts()
    assert start[3] == "callee"
    assert "--append-system-prompt" in start
    (prompt,) = stub.prompts()
    assert prompt[3] == "callee"


def test_dispatch_auto_start_mixed_targets_bootstraps_none_and_reraises(
    stub: StubHarness, tmp_path: Path
) -> None:
    """HIGH 2: two-phase inspect — a non-shell second target orphans nothing.

    First candidate is a bare shell, second is a live agent: assert zero
    starts, zero renames, and the original UsageError still propagates.
    """
    state = {
        **DEFAULT_STATE,
        "agents": [
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi", "agent_status": "working"}
        ],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": "/tmp",
                "label": "callee",
            },
            {
                "pane_id": "w9:p1",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": "pi",
                "agent_status": "working",
                "cwd": "/tmp/harness",
            },
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    ticket = payload_file(tmp_path, "TICKET BODY")
    done = stub.run(
        "callee",
        "reviewer",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "pi",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "no live agent" in done.stderr
    assert stub.starts() == []
    assert [c for c in stub.calls() if c[1:3] == ["pane", "rename"]] == []
    assert stub.prompts() == []


def test_dispatch_auto_start_mid_bootstrap_failure_orphans_nothing_silent(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Round 2: two bare-shell targets, the SECOND fails mid-bootstrap.

    The first agent is already started; the raised error must NAME it (loud,
    never a silent orphan), and no ticket may be dispatched to anyone.
    """
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": str(tmp_path),
                "label": "callee-one",
            },
            {
                "pane_id": "wM:p2N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": str(tmp_path),
                "label": "callee-two",
            },
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            },
            "wM:p2N": {
                "shell_pid": 5678,
                "foreground_processes": [{"name": "zsh", "pid": 5678}],
            },
        },
        "agent_start_error_for": ["callee-two"],
    }
    ticket = payload_file(tmp_path, "TICKET BODY")
    done = stub.run(
        "callee-one",
        "callee-two",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "pi",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    # Exactly one start SUCCEEDED (the first); the refused second start is
    # still logged but registered nothing. The error names the orphan loudly.
    assert "start refused for callee-two" in done.stderr
    assert "callee-one" in done.stderr
    assert "hold no ticket" in done.stderr
    # Nothing was dispatched to anyone.
    assert stub.prompts() == []


def test_dispatch_auto_start_converges_pane_cwd_then_starts(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Issue #225: the lane worktree cwd rides through bootstrap, pane converges."""
    lane = tmp_path / "lane"
    lane.mkdir()
    state = {
        **DEFAULT_STATE,
        "agents": [],
        "panes": [
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": "/tmp",
                "label": "callee",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    ticket = payload_file(tmp_path, "TICKET BODY")
    done = stub.run(
        "callee",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "codex",
        "--role",
        "impl-1",
        "--cwd",
        str(lane),
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    runs = [call for call in stub.calls() if call[1:3] == ["pane", "run"]]
    assert len(runs) == 1
    assert runs[0][3:] == ["wM:p1N", f"cd {lane}"]
    (start,) = stub.starts()
    assert start[start.index("--kind") + 1] == "codex"
    assert (lane / "AGENTS.md").read_text().count("ROLE INVARIANT") == 1
    assert "impl-1" in (lane / "AGENTS.md").read_text()


def test_dispatch_auto_start_live_agent_makes_no_extra_herdr_calls(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Issue #225: the live path keeps its call count with --auto-start set."""
    import herdr_lease

    ticket = payload_file(tmp_path, "TICKET BODY")
    plain = stub.run("reviewer", "--file", str(ticket), "--no-wait", env={"PWD": str(tmp_path)})
    assert plain.returncode == herdr_cli.EXIT_OK, plain.stderr
    plain_calls = len(stub.calls())
    _ = herdr_lease.release_lease("reviewer", base_dir=tmp_path)
    auto = stub.run(
        "reviewer",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "pi",
        env={"PWD": str(tmp_path)},
    )
    assert auto.returncode == herdr_cli.EXIT_OK, auto.stderr
    assert stub.starts() == []
    assert len(stub.calls()) == 2 * plain_calls
