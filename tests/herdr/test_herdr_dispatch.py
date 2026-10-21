"""Tests for skills/herdr/scripts/herdr_dispatch.py (herdr-dispatch helper).

Integration cases route through the shared stub `herdr`.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import herdr_bootstrap
import herdr_cli
import herdr_dispatch
import herdr_label
import herdr_lease
import herdr_prompt
import herdr_reply
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


DRIFTED_ABBREV = "8d9a742"


def filled_ticket(evidence_line: str = "- base `66053e2`") -> str:
    """A ticket with filled sections, so only the SHA guard can refuse it."""
    return (
        "## Task\n\nShip it.\n\n## Context\n\n" + evidence_line + "\n\n"
        "## Acceptance criteria\n\nTests pass.\n"
    )


def sha_repo(root: Path) -> tuple[Path, str]:
    """A scratch git repository with one commit; returns (repo, abbreviated commit SHA).

    The scratch repo is the lane anchor the dispatch SHA guard resolves against, so the
    pins exercise the real `git rev-parse --verify <token>^{commit}` probe instead of a
    stub of it. Mirrors the reply-path `sha_guard_repo` pin; kept local so the dispatch
    pins do not couple to the reply test module.
    """
    repo = root / "dispatch-sha-repo"
    repo.mkdir()

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
        )

    assert git("init", "-q", "-b", "main").returncode == 0
    assert (
        git(
            "-c",
            "user.name=herdr",
            "-c",
            "user.email=herdr@example.invalid",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "dispatch-sha-repo seed",
        ).returncode
        == 0
    )
    short = git("rev-parse", "--short", "HEAD").stdout.strip()
    assert len(short) >= 7
    return repo, short


def _no_settle(_seconds: float) -> None:
    """Stand in for the fresh-spawn settle in tests that assert delivery, not timing."""


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


def test_dispatch_persists_derived_ids_and_renders_envelope(
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
    envelope = herdr_prompt.parse_envelope(text)
    assert envelope is not None
    assert envelope.ticket_id == "#182-herdr-msg-enhance"
    assert envelope.id == "#182-herdr-msg-enhance"


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
    envelope = herdr_prompt.parse_envelope(call[4])
    assert envelope is not None
    assert envelope.ticket_id == "#182-herdr-msg-enhance"
    assert envelope.id == "#182-herdr-msg-enhance#full-stack"


def test_dispatch_injects_caller_context_and_reply_contract(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "do this")), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[1:4] == ["agent", "prompt", "reviewer"]
    text = call[4]
    lines = text.splitlines()
    assert lines[0] == "---"
    assert not re.match(r"^\[\d{4}-\d{2}-\d{2}T", text)
    envelope, body = herdr_prompt.split_envelope_and_body(text)
    assert envelope is not None
    assert envelope.sender == "reviewer@w9:p1"
    assert envelope.receiver == "reviewer@w9:p1"
    assert envelope.task_group == "w9:t1"
    assert envelope.ticket_id == "ticket"
    assert envelope.id == "ticket"
    assert envelope.state == "TASK_STATE_WORKING"
    assert envelope.group == ("reviewer@w9:p1",)
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$", envelope.timestamp)
    for legacy in ("Routing:", "Hierarchy:", "Protocol:", "Runtime:"):
        assert legacy not in text
    assert "cwd:" not in text
    assert "resume:" not in text
    assert "${herdr_skill}" in herdr_prompt.SKILL_NOTICE
    assert "~/.agents" not in herdr_prompt.SKILL_NOTICE
    assert f"\n---\n{herdr_prompt.SKILL_NOTICE}\n\ndo this\n\n" in text
    assert body is not None and body.startswith("do this")
    reply = re.search(r'  uv run "([^"]+)" reviewer "<STATUS> <artifacts> <issues>"', text)
    assert reply, text
    assert Path(reply.group(1)).is_file(), reply.group(1)
    # #241 P2-B (new pin): the helper must be THIS tree's sibling script, not merely an
    # existing path — `is_file()` passes for a foreign copy too.
    assert Path(reply.group(1)).resolve().parent == SCRIPTS_DIR, reply.group(1)
    assert "~/.agents" not in text


def test_dispatch_renders_the_reply_contract_with_the_ticket_bound(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 E1.1 pin 1: the envelope a callee receives binds the derived ticket id.

    Asserted on the RENDERED ENVELOPE (the text `herdr agent prompt` delivers), never on an
    intermediate option: the reply contract carries `--ticket <derived id>` — the explicit name
    the reply side binds. E1.2 (landed) deleted the sole-open-task inference this replaces.

    Old role: scraped the whitespace-delimited token after `--ticket` and compared it to the
    unquoted id, which asserted bytes of a command the pin never ran. E1.1-rework role:
    parsed the rendered line as a shell does (`shlex.split`) and asserted the id is
    `--ticket`'s argument (`[-2:] == ["--ticket", "<id>"]`). New role (herdr228-p3#P2):
    parses the rendered line as a shell does and asserts the id arrives as the single
    `--ticket=<id>` token, so a leading-dash id cannot be parsed as a flag.
    """
    ticket = tmp_path / "182-herdr-msg-enhance.md"
    _ = ticket.write_text("TICKET BODY", encoding="utf-8")
    done = stub.run("reviewer", "--file", str(ticket), "--no-wait", env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    envelope = call[4]
    # Parse the rendered line as a shell does: the id is what `--ticket=` carries once the
    # shell has resolved quoting, which is exactly what the callee's copy-paste delivers.
    line = _rendered_contract_line(envelope)
    assert shlex.split(line)[-1] == "--ticket=#182-herdr-msg-enhance", line


def _rendered_contract_line(envelope: str) -> str:
    """The reply-contract line out of a rendered envelope, verbatim and unstripped."""
    return next(line for line in envelope.splitlines() if line.strip().startswith("uv run "))


def _run_contract_line_in_a_shell(stub: StubHarness, contract_line: str, cwd: Path) -> list[str]:
    """Run the rendered contract line through a real shell and return the helper's argv.

    The `uv` on PATH is a shim that records its argv one element per line, so a value the
    shell split, swallowed as a comment, or expanded into a new command is observable as such.
    """
    shim = stub.bin_dir / "uv"
    _ = shim.write_text(
        '#!/bin/sh\n: > "${FAKE_UV_LOG}"\nfor a in "$@"; do printf \'%s\\n\' "$a" >> "${FAKE_UV_LOG}"; done\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    log = cwd / "fake-uv-argv.txt"
    env = {**stub.base_env(), "FAKE_UV_LOG": str(log)}
    done = subprocess.run(
        ["bash", "-c", contract_line], cwd=cwd, env=env, capture_output=True, text=True
    )
    assert done.returncode == 0, done.stderr
    return log.read_text(encoding="utf-8").splitlines()


def test_the_rendered_ticket_id_survives_a_real_shell(stub: StubHarness, tmp_path: Path) -> None:
    """#246 E1.1 rework F1.3 (a): a lane ticket stem reaches the helper as ONE argument.

    The contract is a command a callee copy-pastes, so the honest witness runs it through a real
    shell. Every ticket in this lane starts with a number, so the derived id begins with `#`:
    unquoted, that `#` starts a shell comment, the id is swallowed, and the real helper exits 2
    with `argument --ticket: expected one argument`. Red on the unquoted render.
    herdr228-p3#P2 role: the render is now `--ticket=<quoted>` (one shell word), so the pin
    asserts the helper receives that single `--ticket=<id>` element.
    """
    ticket = tmp_path / "246-render-ticket-in-contract.md"
    _ = ticket.write_text("TICKET BODY", encoding="utf-8")
    done = stub.run("reviewer", "--file", str(ticket), "--no-wait", env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    line = _rendered_contract_line(call[4])

    argv = _run_contract_line_in_a_shell(stub, line, tmp_path)
    assert argv[-1] == "--ticket=#246-render-ticket-in-contract", argv


def test_a_hostile_ticket_filename_reaches_the_shell_quoted(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 E1.1 rework F1.3 (b): a crafted filename is quoted, so the shell executes nothing.

    Unquoted, `pwn;touch PWNED.md` derived `pwn;touch PWNED`, the `;` split the id off the flag,
    and the shell ran `touch PWNED`. The render must keep the id one argument and leave the
    side-effect file uncreated. Red on the unquoted render.
    herdr228-p3#P2 role: the render is now `--ticket=<quoted>` (one shell word), so the pin
    asserts the helper receives that single `--ticket=<id>` element.
    """
    ticket = tmp_path / "pwn;touch PWNED.md"
    _ = ticket.write_text("TICKET BODY", encoding="utf-8")
    done = stub.run("reviewer", "--file", str(ticket), "--no-wait", env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    line = _rendered_contract_line(call[4])

    argv = _run_contract_line_in_a_shell(stub, line, tmp_path)
    assert argv[-1] == "--ticket=pwn;touch PWNED", argv
    assert not (tmp_path / "PWNED").exists(), "the shell executed text out of the ticket filename"
    assert not (tmp_path / "PWNED.md").exists(), (
        "the shell executed text out of the ticket filename"
    )


def test_a_leading_dash_ticket_id_survives_a_real_shell(stub: StubHarness, tmp_path: Path) -> None:
    """herdr228-p3#P2 pin: a ticket stem starting with a dash reaches the helper intact.

    `shlex.quote('-rf')` is `-rf`, so the space form renders `--ticket -rf` and argparse
    reads the value as option-like (`argument --ticket: expected one argument`, exit 2) —
    the reply is never sent, with no refusal naming the cause. The `=` form renders
    `--ticket=-rf`, which argparse binds as the value even with the leading dash.
    The honest witness runs the RENDERED line through a real `bash -c` with the fake `uv`
    shim on PATH and asserts the value arrives as ONE intact argv element. Red on the
    space-form render (argv ends `[..., '--ticket', '-rf']`, and the reply parser exits 2).
    """
    ticket = tmp_path / "-rf.md"
    _ = ticket.write_text("TICKET BODY", encoding="utf-8")
    done = stub.run("reviewer", "--file", str(ticket), "--no-wait", env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    line = _rendered_contract_line(call[4])
    assert "--ticket=" in line, line

    argv = _run_contract_line_in_a_shell(stub, line, tmp_path)
    assert argv[-1] == "--ticket=-rf", argv
    value = argv[-1].split("=", 1)[1]
    assert value == "-rf", argv
    bound = herdr_reply.build_parser().parse_args(["reviewer", "--file", "r.md", argv[-1]])
    assert bound.ticket == "-rf", argv


def test_dispatch_without_a_derivable_ticket_renders_the_unbound_contract(
    stub: StubHarness,
) -> None:
    """#246 E1.1 pin 3: no derivable ticket renders today's contract, without `--ticket`.

    `--file -` reads the ticket from stdin, and a stdin ticket has no filename to derive an id
    from, so the derivation returns None. The contract must still render (no crash) in its
    pre-change form; the reply then lands unlinked with D1.3's warning.
    """
    done = stub.run("reviewer", "--file", "-", "--no-wait", stdin="TICKET BODY\n")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    envelope = call[4]
    reply = re.search(r'  uv run "([^"]+)" reviewer "<STATUS> <artifacts> <issues>"', envelope)
    assert reply, envelope
    assert "--ticket" not in envelope


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
    assert task["status"] == herdr_lease.STATE_SUBMITTED
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
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path, "dry")), "--dry-run", "--json")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    from typing import cast

    parsed = cast(object, json.loads(done.stdout))
    assert isinstance(parsed, list)
    assert parsed[3] == "reviewer"
    envelope = herdr_prompt.parse_envelope(str(parsed[4]))
    assert envelope is not None
    assert envelope.sender == "reviewer@w9:p1"
    assert envelope.receiver == "reviewer@w9:p1"
    assert envelope.state == "TASK_STATE_WORKING"


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


def test_dispatch_draft_prints_skeleton_with_prefilled_addresses(stub: StubHarness) -> None:
    done = stub.run("callee", "--draft")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []
    assert "- Sender: reviewer@w9:p1 - tab w9:t1 - kind pi" in done.stdout
    assert "- Receiver: callee" in done.stdout
    assert re.search(
        r"^- Drafted: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$", done.stdout, re.MULTILINE
    )
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


def test_dispatch_refuses_a_ticket_naming_an_unresolvable_sha(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Pin 1 (#247, dispatch path): the drifted token is refused before any lease is taken.

    The dispatcher inlines the ticket file verbatim, so a drifted SHA copy would otherwise
    reach the callee with no mechanism to detect it. Refused before the store is touched:
    no prompt, and no lease for the callee that a corrected re-send would have to force
    past.

    Mutant killed: skip the guard on the dispatch path — this exits 0 and prompts.
    """
    repo, _short = sha_repo(tmp_path)
    ticket = payload_file(tmp_path, filled_ticket(f"- base `{DRIFTED_ABBREV}`"))
    done = stub.run("callee", "--file", str(ticket), "--no-wait", env={"HERDR_LANE_DIR": str(repo)})

    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert DRIFTED_ABBREV in done.stderr
    assert str(ticket) in done.stderr
    assert stub.prompts() == []
    assert herdr_lease.get_lease("callee", base_dir=repo) is None


def test_dispatch_delivers_a_ticket_naming_a_resolving_sha(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Pin 2 (#247, dispatch path): a real abbreviated commit passes the guard."""
    repo, short = sha_repo(tmp_path)
    ticket = payload_file(tmp_path, filled_ticket(f"- base `{short}`"))
    done = stub.run(
        "callee",
        "--file",
        str(ticket),
        "--dry-run",
        env={"HERDR_LANE_DIR": str(repo)},
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr


def test_dispatch_waiver_names_the_intentional_token_on_stderr(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Pin 3 (#247, dispatch path): a waived token dispatches, and the waiver is loud."""
    repo, _short = sha_repo(tmp_path)
    ticket = payload_file(tmp_path, filled_ticket(f"- base `{DRIFTED_ABBREV}`"))
    done = stub.run(
        "callee",
        "--file",
        str(ticket),
        "--dry-run",
        "--allow-unresolvable-sha",
        DRIFTED_ABBREV,
        env={"HERDR_LANE_DIR": str(repo)},
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert DRIFTED_ABBREV in done.stderr


def test_dispatch_refuses_untouched_skeleton(stub: StubHarness, tmp_path: Path) -> None:
    ticket = payload_file(
        tmp_path,
        "## Routing\n\n- Sender: reviewer@w9:p1\n\n## Task\n\n## Context\n\n## Acceptance criteria\n",
    )
    done = stub.run("callee", "--file", str(ticket), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "empty Task/Context/Acceptance sections" in done.stderr
    assert stub.prompts() == []


def test_dispatch_refuses_untouched_skeleton_with_cr_line_endings(
    stub: StubHarness, tmp_path: Path
) -> None:
    """The boundary search is newline-agnostic: a CR-separated unfilled skeleton is refused.

    The payload is validated as the raw delivered bytes, and `read_bytes().decode` keeps a
    lone `\r` as-is (unlike `read_text`, which translated it to `\n`). An LF-only boundary
    search then finds no section end, so the guard fails open and the unfilled ticket is
    dispatched (exit 0, a prompt, a lease).
    """
    ticket = tmp_path / "ticket.md"
    _ = ticket.write_bytes(
        b"## Routing\r\r- Sender: reviewer@w9:p1\r\r"
        b"## Task\r\r## Context\r\r## Acceptance criteria\r"
    )
    done = stub.run("callee", "--file", str(ticket), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "empty Task/Context/Acceptance sections" in done.stderr
    assert stub.prompts() == []
    assert not (tmp_path / ".lane" / "tasks.yaml").exists()


def test_dispatch_refuses_untouched_skeleton_with_mixed_crlf_sections(
    stub: StubHarness, tmp_path: Path
) -> None:
    """A `\n\r## ` boundary (LF then a lone CR before the heading) is still a section end."""
    ticket = tmp_path / "ticket.md"
    _ = ticket.write_bytes(
        b"## Routing\n\r- Sender: reviewer@w9:p1\n\r"
        b"## Task\n\r## Context\n\r## Acceptance criteria\n"
    )
    done = stub.run("callee", "--file", str(ticket), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "empty Task/Context/Acceptance sections" in done.stderr
    assert stub.prompts() == []
    assert not (tmp_path / ".lane" / "tasks.yaml").exists()


def test_dispatch_accepts_filled_skeleton_dry_run(stub: StubHarness, tmp_path: Path) -> None:
    ticket = payload_file(
        tmp_path,
        "## Task\n\nShip the fix.\n\n## Context\n\n\n## Acceptance criteria\n",
    )
    done = stub.run("callee", "--file", str(ticket), "--dry-run")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr


# ── #182 t2: active ID-anchored reconciliation at dispatch (ADR-0020) ──────────────


def reconcile_renames(stub: StubHarness) -> list[list[str]]:
    """Every rename this dispatch issued (or attempted), minus the herdr argv head."""
    return [call[1:] for call in stub.calls() if call[2] == "rename"]


LANE_TAB = {"tab_id": "w9:t1", "workspace_id": "w9", "label": "harness"}


def lane_state(**overrides: object) -> dict[str, object]:
    """DEFAULT_STATE (tab titled `harness`, orchestrator pane w9:p1 hosts the live, named
    `reviewer`) with the lane rows spelled out, so each drift below is one mutated row."""
    state: dict[str, object] = {
        **DEFAULT_STATE,
        "tabs": [LANE_TAB],
        "agents": [
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi", "agent_status": "working"}
        ],
        "panes": [
            {
                "pane_id": "w9:p1",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": "pi",
                "agent_status": "working",
                "cwd": "/tmp/harness",
            },
            {
                "pane_id": "w9:p3",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": "pi",
                "agent_status": "idle",
                "cwd": "/tmp/work",
                "label": "worker-1",
            },
        ],
    }
    return {**state, **overrides}


def dispatch_into_lane(
    stub: StubHarness, tmp_path: Path, state: dict[str, object], *extra: str
) -> subprocess.CompletedProcess[str]:
    return stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        "--no-wait",
        "--task-group",
        "harness",
        *extra,
        state=state,
        env={"PWD": str(tmp_path)},
    )


def test_dispatch_renames_a_generic_tab_title_on_its_physical_id(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Scenario 1: tab `w9:t1` titled `3` is set back to `<task_group>` by `tab_id`.

    Pin -> mutant: anchor the rename on the visible title instead of `tab_id`, so the argv
    row mismatches and this fails.
    """
    state = lane_state(tabs=[{"tab_id": "w9:t1", "workspace_id": "w9", "label": "3"}])
    done = dispatch_into_lane(stub, tmp_path, state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert reconcile_renames(stub) == [["tab", "rename", "w9:t1", "harness"]]
    assert len(stub.prompts()) == 1


def test_dispatch_renames_nothing_when_the_lane_is_already_correct(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Scenario 2: the no-op invariant — a correct lane earns zero renames.

    Pin -> mutant: rename unconditionally at dispatch, so this logs a tab rename anyway.
    """
    done = dispatch_into_lane(stub, tmp_path, lane_state())
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert reconcile_renames(stub) == []
    assert len(stub.prompts()) == 1


def test_dispatch_restores_a_dropped_agent_name_with_both_renames(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Scenario 3: ADR-0020 names BOTH commands; each is anchored on the worker's `pane_id`.

    Pin -> mutant: issue only `agent rename` (or only `pane rename`), so the pair comes back
    half-healed and this sees one argv where it asserts two.
    """
    state = lane_state(
        agents=[
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi", "agent_status": "working"},
            {"pane_id": "w9:p3", "agent": "pi", "agent_status": "idle"},
        ]
    )
    done = dispatch_into_lane(stub, tmp_path, state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert reconcile_renames(stub) == [
        ["agent", "rename", "w9:p3", "worker-1"],
        ["pane", "rename", "w9:p3", "worker-1"],
    ]


def test_dispatch_rename_failure_delivers_anything(stub: StubHarness, tmp_path: Path) -> None:
    """Scenario 4: a refused rename is one stderr line — the exit status and the delivery stand.

    Pin -> mutant: let `HerdrError` propagate out of the pass (or exit on it), so this
    dispatch turns EXIT_OK into EXIT_HERDR or never prompts.
    """
    state = lane_state(
        agents=[
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi", "agent_status": "working"},
            {"pane_id": "w9:p3", "agent": "pi", "agent_status": "idle"},
        ],
        pane_rename_error_for=["w9:p3"],
    )
    done = dispatch_into_lane(stub, tmp_path, state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert done.stderr.count("herdr-dispatch: rename skipped:") == 1
    assert len(stub.prompts()) == 1
    assert reconcile_renames(stub) == [
        ["agent", "rename", "w9:p3", "worker-1"],
        ["pane", "rename", "w9:p3", "worker-1"],
    ]


def test_dispatch_renames_a_dropped_orchestrator_to_the_composed_lane_name(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Scenario 5: the sending pane's agent lost its name -> re-registered `<task_group>-orch`.

    The orchestrator pane carries the agent-shaped label `old-reviewer`, so case 1's worker
    restoration WOULD claim it; pin -> mutant: let case 1 do so, and this sees a rename to
    `old-reviewer` instead of exactly one rename to `harness-orch`.
    """
    state = lane_state(
        agents=[
            {"pane_id": "w9:p1", "agent": "pi", "agent_status": "working"},
            {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi", "agent_status": "idle"},
        ],
        panes=[
            {
                "pane_id": "w9:p1",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": "pi",
                "agent_status": "working",
                "cwd": "/tmp/harness",
                "label": "old-reviewer",
            },
            {
                "pane_id": "w9:p3",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": "pi",
                "agent_status": "idle",
                "cwd": "/tmp/work",
                "label": "worker-1",
            },
        ],
    )
    done = stub.run(
        "worker-1",
        "--file",
        str(payload_file(tmp_path)),
        "--no-wait",
        "--task-group",
        "harness",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert reconcile_renames(stub) == [["agent", "rename", "w9:p1", "harness-orch"]]


def test_dispatch_second_run_over_a_corrected_lane_renames_nothing(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Scenario 6: idempotence — after the first pass heals the drift, the next pass is silent.

    Pin -> mutant: rename from the dispatch's OWN intent rather than from the inventory
    comparison, so the second run over the corrected fleet still issues renames.
    """
    drifted = lane_state(
        tabs=[{"tab_id": "w9:t1", "workspace_id": "w9", "label": "3"}],
        agents=[
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi", "agent_status": "working"},
            {"pane_id": "w9:p3", "agent": "pi", "agent_status": "idle"},
        ],
    )
    first = dispatch_into_lane(stub, tmp_path, drifted)
    assert first.returncode == herdr_cli.EXIT_OK, first.stderr
    assert reconcile_renames(stub) == [
        ["agent", "rename", "w9:p3", "worker-1"],
        ["pane", "rename", "w9:p3", "worker-1"],
        ["tab", "rename", "w9:t1", "harness"],
    ]
    # The fleet as the two healed rows leave it: worker holds its name, tab holds the slug.
    corrected = lane_state(
        agents=[
            {"pane_id": "w9:p1", "name": "reviewer", "agent": "pi", "agent_status": "working"},
            {"pane_id": "w9:p3", "name": "worker-1", "agent": "pi", "agent_status": "idle"},
        ]
    )
    before = len(stub.calls())
    second = dispatch_into_lane(stub, tmp_path, corrected, "--force")
    assert second.returncode == herdr_cli.EXIT_OK, second.stderr
    assert [call[1:] for call in stub.calls()[before:] if call[2] == "rename"] == []


def test_dispatch_dry_run_prints_the_reconciliation_and_renames_nothing(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Scenario 7: `--dry-run` prints the planned argv, issues no rename, mutates nothing."""
    state = lane_state(tabs=[{"tab_id": "w9:t1", "workspace_id": "w9", "label": "3"}])
    done = dispatch_into_lane(stub, tmp_path, state, "--dry-run")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (planned,) = json.loads(done.stdout.splitlines()[0])
    assert planned[1:] == ["tab", "rename", "w9:t1", "harness"]
    assert reconcile_renames(stub) == []
    assert stub.prompts() == []


def test_dispatch_advises_when_the_pane_inventory_gives_no_tab_anchor(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#182 t5 2.2: a `pane list` that answers no tab id costs the lease its anchor — say so.

    `lane_tab_ids` returns `{}` both when the inventory raises (its `except` swallows every
    failure) and when the rows simply carry no `tab_id`, so the lease then records no `tab_id`
    and a later reply loses the anchor its reconciliation case 2 needs — while the reply side
    DOES print a skip line for the same class of loss. One advisory makes the two sides
    symmetric, and it is advisory only: same exit status, same delivery, and a delivery summary
    whose shape is untouched apart from the fields a missing anchor legitimately changes (see
    `_summary_shape`).

    Pin -> mutants: return `{}` without printing, and no line matches; print onto stdout, and
    the summary-shape comparison fails; print on the healthy path too, and the first dispatch's
    stderr catches it; crash or skip the prompt, and those asserts fail.
    """
    healthy = dispatch_into_lane(stub, tmp_path, lane_state())
    assert healthy.returncode == herdr_cli.EXIT_OK, healthy.stderr
    assert "no tab" not in healthy.stderr, healthy.stderr
    prompts_before = len(stub.prompts())
    # The inventory answers, but neither row carries the physical tab anchor.
    anchorless = [
        {
            "pane_id": "w9:p1",
            "workspace_id": "w9",
            "agent": "pi",
            "agent_status": "working",
            "cwd": "/tmp/harness",
        },
        {
            "pane_id": "w9:p3",
            "workspace_id": "w9",
            "agent": "pi",
            "agent_status": "idle",
            "cwd": "/tmp/work",
            "label": "worker-1",
        },
    ]
    done = dispatch_into_lane(stub, tmp_path, lane_state(panes=anchorless), "--force")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    advisories = [line for line in done.stderr.splitlines() if "no tab" in line]
    assert len(advisories) == 1, done.stderr
    assert advisories[0].startswith("herdr-dispatch: "), advisories[0]
    assert "no tab" not in done.stdout, "the advisory is stderr-only"
    # The anchor the advisory names is missing from the delivered envelope too, and that IS the
    # loss: the slug survives, its `@<tab>` half does not. Asserted here so `_summary_shape`
    # filtering the line cannot hide it.
    assert "  task_group: harness@w9:t1\n" in healthy.stdout, healthy.stdout
    assert "  task_group: harness\n" in done.stdout, done.stdout
    assert _summary_shape(done.stdout) == _summary_shape(healthy.stdout), (
        f"stdout drifted: {done.stdout!r} vs {healthy.stdout!r}"
    )
    assert len(stub.prompts()) == prompts_before + 1, "the advisory never costs the delivery"
    lease = herdr_lease.get_lease("reviewer", base_dir=tmp_path)
    assert lease is not None
    assert "tab_id" not in lease, "the anchor is absent, exactly as the advisory says"


def _summary_shape(stdout: str) -> list[str]:
    """The delivery-summary lines a dispatch advisory may not disturb, across two runs.

    Three fields legitimately differ between one dispatch whose panes carry a tab id and one whose
    panes do not, and the first two are the anchor under test rather than noise: the envelope's
    `metadata.task_group` loses its `@<tab>` half (asserted directly, in the test below, never
    quietly filtered away), the delivered prompt therefore shrinks, and the status line echoes
    that size as `bytes=`; `revision=` is the stub's per-pane counter, which moves with each
    delivery. The wall-clock `timestamp:` line varies between any two runs. Everything else — the
    anchored target, both `---` delimiters, the ticket_id, the state, the source line and the body
    preview — is deterministic under the stub, so a line added to stdout, or the summary changing
    shape, still fails the comparison.
    """
    shape: list[str] = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if "timestamp:" in stripped or stripped.startswith("task_group:"):
            continue
        shape.append(re.sub(r"bytes=\d+  revision=\S+", "bytes=<n>  revision=<r>", line))
    return shape


def test_dispatch_delivers_when_the_reconciliation_planner_raises(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#182 t5 2.3: the planner is inside the guard, so a raise costs one line and no dispatch.

    The same structural hole as the reply seam: `reconciliation_argv` ran outside `reconcile_lane`'s
    `try`, and `herdr-dispatch` consumed its result unguarded before `resolve_targets`, so a
    planner exception aborted the dispatch it promised only to annotate.

    Pin -> mutant: move the planner call back outside the `try` and this exits 1 with a traceback
    and zero prompts.
    """

    def boom(*args: object, **kwargs: object) -> None:
        raise TypeError("planner boom")

    _ = monkeypatch.setattr(herdr_label, "reconciliation_argv", boom)
    done = dispatch_into_lane(stub, tmp_path, lane_state())
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "Traceback" not in done.stderr, done.stderr
    assert done.stderr.count("herdr-dispatch: reconciliation skipped:") == 1, done.stderr
    assert len(stub.prompts()) == 1


def test_dispatch_skips_an_ungrammatical_task_group_with_one_line(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Scenario 8: a violating slug is SKIPPED — one stderr line, and it never reaches herdr.

    Pin -> mutant: validate the slug but still forward it, or crash on it, so this either
    logs a tab rename or loses the delivery.
    """
    state = lane_state(tabs=[{"tab_id": "w9:t1", "workspace_id": "w9", "label": "3"}])
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        "--no-wait",
        "--task-group",
        "Bad Slug",
        state=state,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert reconcile_renames(stub) == []
    assert done.stderr.count("left the tab title and the orchestrator name alone") == 1
    assert len(stub.prompts()) == 1


# ── pin: the dispatch ticket payload goes through the shared reader ────────────────
#
# `herdr-dispatch` used to read its own ticket with `Path(...).read_text(encoding="utf-8")`.
# A NUL byte passed that read (NUL is valid UTF-8) and was only refused later, by the
# prompt reader's second read of the same file; invalid UTF-8 was not refused at all, it
# died as a bare `UnicodeDecodeError` traceback (exit 1), never a usage refusal. The read
# now goes through `herdr_cli.read_payload_stream` + `decode_payload`, so dispatch refuses
# both payloads in the same sentence `herdr-prompt` and `herdr-reply` use. The pin compares
# all three paths, so a dispatch-specific paraphrase fails here too, and so does dropping
# the refusal from the shared reader.


@pytest.mark.parametrize(
    "body",
    [b"TICKET BODY\x00tail\n", b"TICKET BODY \xff\xfe bad\n"],
    ids=["nul", "invalid-utf8"],
)
def test_dispatch_refuses_what_the_shared_payload_reader_refuses(
    stub: StubHarness, tmp_path: Path, body: bytes
) -> None:
    ticket = tmp_path / "ticket.md"
    _ = ticket.write_bytes(body)

    with pytest.raises(herdr_cli.UsageError) as prompt_raised:
        _ = herdr_prompt.read_payload(str(ticket))
    with pytest.raises(herdr_cli.UsageError) as reply_raised:
        _ = herdr_reply.read_payload(str(ticket), None)
    prompt_sentence = str(prompt_raised.value)
    reply_sentence = str(reply_raised.value)

    done = stub.run("callee", "--file", str(ticket), "--no-wait")

    assert prompt_sentence == reply_sentence, "prompt and reply must keep one shared sentence"
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "Traceback" not in done.stderr
    assert done.stderr.strip() == f"herdr-dispatch: {prompt_sentence}"
    assert stub.prompts() == []
    # The refusal now lands BEFORE `acquire_lease`, not after the lease via the prompt
    # reader's second read of the same file. Without this the pin passes on the old
    # ordering too: the NUL sentence and exit code are identical, only the lease differs.
    # Asserted on the RESOLVED store, never on `tmp_path / ".lane"`: dropping the stub's
    # `HERDR_LANE_DIR` anchor would otherwise let a lease land in this repository's own
    # store while the `tmp_path` copy stayed absent, and the pin would still pass.
    store = herdr_lease.resolve_tasks_file(env=stub.base_env())
    assert store == Path(stub.tmp_path).resolve() / herdr_lease.STATE_FILE_LANE
    assert not store.exists()


def test_dispatch_missing_file_refusal_names_the_seam_sentence(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Pin the unreadable-ticket sentence: it is now the shared seam's, a caller contract.

    `herdr-dispatch` used to raise its own `cannot read ticket file ...`; the shared payload
    seam (`herdr_cli.read_payload_stream`) now covers the missing file too, in the sentence
    `herdr-prompt` and `herdr-reply` also print. The sentence carries the path twice and the
    Python errno repr; that shape is pinned here, so a paraphrase or a seam tidy-up is a
    deliberate, visible change rather than silent drift.
    """
    missing = tmp_path / "nope.md"
    with pytest.raises(OSError) as missing_exc:
        _ = missing.read_bytes()
    detail = str(missing_exc.value)
    done = stub.run("callee", "--file", str(missing), "--no-wait")
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert done.stderr.strip() == (
        f"herdr-dispatch: cannot read payload from {str(missing)!r}: {detail}"
    )
    assert stub.prompts() == []
    assert not (tmp_path / ".lane" / "tasks.yaml").exists()


def test_dispatch_auto_start_bootstraps_missing_agent_with_trust_flags(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Issue #225: a ticket for a role with no live agent starts it via the
    bootstrap contract (kind trust flags + ROLE INVARIANT), then dispatches.

    The invariant reaches the agent as the absolute path of the lane-local snippet file,
    because herdr refuses a multi-line agent arg; read that file to prove delivery.

    The spawn's 5s settle is faked here (this test asserts delivery, not timing); pin 4
    (`test_dispatch_auto_start_settles_the_fresh_pane_once`) owns the settle assertion.
    """
    monkeypatch.setattr(herdr_bootstrap, "_sleep", _no_settle)
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
    assert invariant == str(tmp_path / ".lane" / "invariants" / "callee.md")
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


def test_dispatch_auto_start_contract_rides_for_a_scoped_implementer_label(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """BLOCKING-1: without `--task-group` the role falls back to the scoped agent name, so
    `herdr228-impl-1` must still receive the implementer cooperation contract."""
    monkeypatch.setattr(herdr_bootstrap, "_sleep", _no_settle)
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
                "label": "herdr228-impl-1",
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
        "herdr228-impl-1",
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
    invariant = start[start.index("--append-system-prompt") + 1]
    assert invariant == str(tmp_path / ".lane" / "invariants" / "herdr228-impl-1.md")
    text = Path(invariant).read_text()
    assert "single writer for your task" in text
    assert text == herdr_bootstrap.render_invariant("herdr228-impl-1")


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


def test_dispatch_auto_start_uses_claude_trust_flags(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Issue #225: the bootstrap contract owns trust flags (claude path)."""
    monkeypatch.setattr(herdr_bootstrap, "_sleep", _no_settle)
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
    # #240 (rewritten pin, was: the text flag): claude takes the snippet file through its
    # `-file` flag — the text flag would boot it with the path string as its system prompt.
    assert "--append-system-prompt-file" in start[split + 1 :]
    assert "--append-system-prompt" not in start[split + 1 :]
    assert start[-1] == "--dangerously-skip-permissions"
    assert "--append-system-prompt-file" in start


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
    monkeypatch.setattr(herdr_bootstrap, "_sleep", _no_settle)
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
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Round 2: two bare-shell targets, the SECOND fails mid-bootstrap.

    The first agent is already started; the raised error must NAME it (loud,
    never a silent orphan), and no ticket may be dispatched to anyone.
    """
    monkeypatch.setattr(herdr_bootstrap, "_sleep", _no_settle)
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
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Issue #225: the lane worktree cwd rides through bootstrap, pane converges."""
    monkeypatch.setattr(herdr_bootstrap, "_sleep", _no_settle)
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


# ── #238: a warm pane is never settled ──────────────────────────────────────────────


def test_warm_agent_dispatch_settles_nothing(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pin 3 (#238): a live idle agent is warm — an ordinary dispatch adds no settle delay.

    Mutant killed: call `settle_fresh_pane(DEFAULT_SETTLE_SECONDS)` on the warm dispatch path
    (`herdr_prompt.prompt_one`) — `herdr_bootstrap._sleep` then records a wait and this fails.
    """
    slept: list[float] = []
    monkeypatch.setattr(herdr_bootstrap, "_sleep", slept.append)
    monkeypatch.setattr(herdr_prompt, "_sleep", slept.append)
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
    assert stub.starts() == [], "a live agent is warm: nothing is spawned"
    (prompt,) = stub.prompts()
    assert prompt[3] == "reviewer"
    assert slept == [], "a warm dispatch must add no settle delay"


# ── #238: the dispatch auto-start flow settles a fresh pane, and --settle overrides ──


def _bare_shell_state(tmp_path: Path, label: str = "callee") -> dict[str, object]:
    """DEFAULT_STATE with no agents and one bare shell pane carrying `label`."""
    return {
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
                "label": label,
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }


def test_dispatch_auto_start_settles_the_fresh_pane_once(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pin 4 (#238, dispatch auto-start): the bootstrap the dispatch runs settles once, 5s.

    A pin, not a behaviour change: `run_bootstrap_contract` builds `herdr_bootstrap.Options(...)`
    with no `settle`, so the auto-started callee inherits `DEFAULT_SETTLE_SECONDS` today.
    Mutant killed: add `settle=0.0` to that `Options(...)` call — `slept == []` and this fails.
    """
    slept: list[float] = []
    monkeypatch.setattr(herdr_bootstrap, "_sleep", slept.append)
    ticket = payload_file(tmp_path, "TICKET BODY")

    done = stub.run(
        "callee",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "pi",
        state=_bare_shell_state(tmp_path),
        env={"PWD": str(tmp_path)},
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (start,) = stub.starts()
    assert start[3] == "callee"
    assert slept == [herdr_bootstrap.DEFAULT_SETTLE_SECONDS], (
        "the dispatch auto-start path must pay the 5s handshake exactly once"
    )


def test_dispatch_auto_start_settle_zero_is_exact(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`--settle 0` on herdr-dispatch spawns without sleeping; the default stays 5.

    RED on base: `herdr-dispatch` declares no `--settle`, so argparse refuses the flag (exit 2).
    Mutant killed: forward a hard-coded default instead of `options.settle` — the 0 run sleeps.
    """
    slept: list[float] = []
    monkeypatch.setattr(herdr_bootstrap, "_sleep", slept.append)
    ticket = payload_file(tmp_path, "TICKET BODY")

    done = stub.run(
        "callee",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "pi",
        "--settle",
        "0",
        state=_bare_shell_state(tmp_path),
        env={"PWD": str(tmp_path)},
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert len(stub.starts()) == 1
    assert slept == [], "--settle 0 must not sleep at all on the dispatch path"


def test_dispatch_parser_declares_settle_with_the_bootstrap_default() -> None:
    """`--settle` rides on herdr-dispatch like `--role`/`--cwd`/`--model`; default 5.

    RED on base: the parser has no `--settle`.
    """
    parser = herdr_dispatch.build_parser()
    assert (
        parser.parse_args(["callee", "--file", "t"]).settle
        == herdr_bootstrap.DEFAULT_SETTLE_SECONDS
    )
    assert parser.parse_args(["callee", "--file", "t", "--settle", "2.5"]).settle == 2.5


def test_dispatch_auto_start_dry_run_forwards_the_settle(stub: StubHarness, tmp_path: Path) -> None:
    """A dry-run auto-start plan carries the forwarded `--settle` value, never sleeps.

    RED on base: the parser has no `--settle`.
    """
    ticket = payload_file(tmp_path, "TICKET BODY")
    done = stub.run(
        "callee",
        "--file",
        str(ticket),
        "--no-wait",
        "--auto-start",
        "pi",
        "--settle",
        "2.5",
        "--dry-run",
        state=_bare_shell_state(tmp_path),
        env={"PWD": str(tmp_path)},
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    plan = json.loads(done.stdout.splitlines()[0])
    assert plan["settle"] == 2.5
    assert stub.starts() == []


# ── #252: the screen gate rides dispatch's delivery path too ────────────────────────

# Screens mirror `tests/herdr/test_herdr_prompt.py` (trust selector verbatim from
# `references/agents/qodercli.md`); kept local so the dispatch pins do not couple to
# the prompt module, mirroring the `sha_repo` convention.
DISPATCH_TRUST_SCREEN = (
    "◇ Qoder CLI CN\n"
    "\n"
    " Do you trust the files in this folder?\n"
    " /private/tmp/example-worktree\n"
    "  ❯ 1. Trust folder\n"
    "    2. Don't trust and exit\n"
)
DISPATCH_CLEAN_SCREEN = "◎ main · ◎ h2-writer 191s\n*   Type your message or @path/to/file\n"


def _dispatch_reads(stub: StubHarness) -> list[list[str]]:
    """Every `herdr agent read` the stub recorded: the gate's screen reads."""
    return [call for call in stub.calls() if call[1:3] == ["agent", "read"]]


def test_dispatch_refuses_a_modal_screen_before_injection(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Both entry points: dispatch routes through `prompt_agents` -> `wait_for_ready`.

    Mutant killed: remove the screen check — the prompt is injected into the selector and
    both `EXIT_USAGE` and `prompts() == []` fail.
    """
    state = {**DEFAULT_STATE, "agent_read_text": DISPATCH_TRUST_SCREEN}
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), "--no-wait", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "refusing to inject the prompt into the dialog" in done.stderr
    assert "Do you trust the files in this folder?" in done.stderr
    assert stub.prompts() == [], "bytes must not be injected into a modal"
    assert len(_dispatch_reads(stub)) == 1, "one confirm, no re-read"


def test_dispatch_clean_screen_delivers_with_one_read(stub: StubHarness, tmp_path: Path) -> None:
    """Mutant killed: make the screen check unconditional or screen-driven — a clean
    settled pane then never delivers and this fails.
    """
    state = {**DEFAULT_STATE, "agent_read_text": DISPATCH_CLEAN_SCREEN}
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), "--no-wait", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert len(stub.prompts()) == 1
    assert len(_dispatch_reads(stub)) == 1


def test_dispatch_never_reads_the_screen_while_waiting(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The waiting path stays screen-free under dispatch too (SKILL.md: no `agent read` poll).

    Mutant killed: move the screen read into the per-attempt loop — this run then records ~50
    reads. It does NOT kill a read inside `agent_readiness`'s READY branch: a target held
    `working` never takes that branch, so that mutant records zero reads here; dispatch's
    delivered case `test_dispatch_clean_screen_delivers_with_one_read` pins it. `_sleep` is
    patched on the shared `herdr_prompt` module, which the in-process dispatch body imports
    from `sys.modules`, so the 50 probes cost no real time.
    """
    monkeypatch.setattr(herdr_prompt, "_sleep", _no_settle)
    state = {**DEFAULT_STATE, "agent_get_seq": {"reviewer": ["working"]}}
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), "--no-wait", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE, done.stderr
    assert "did not settle for prompt delivery" in done.stderr
    assert stub.prompts() == []
    assert _dispatch_reads(stub) == []


def test_dispatch_skip_screen_check_delivers_to_a_modal_screen(
    stub: StubHarness, tmp_path: Path
) -> None:
    """The escape hatch on the dispatch entry point (`--skip-screen-check` is inherited).

    Mutants killed: make the flag a no-op in dispatch's parser (exit 2, no prompt); declare
    it on `herdr-prompt` only (argparse refuses the unknown flag here).
    """
    state = {**DEFAULT_STATE, "agent_read_text": DISPATCH_TRUST_SCREEN}
    done = stub.run(
        "reviewer",
        "--file",
        str(payload_file(tmp_path)),
        "--no-wait",
        "--skip-screen-check",
        state=state,
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert len(stub.prompts()) == 1
    assert "refusing to inject" not in done.stderr
    assert _dispatch_reads(stub) == []


def test_dispatch_delivers_past_a_quoted_dialog_in_the_callee_transcript(
    stub: StubHarness, tmp_path: Path
) -> None:
    """P2-1 through dispatch: prose that QUOTES the trust block is not a modal (#182 h2c).

    A callee summarising `references/agents/qodercli.md` prints the block, and the shipped
    patterns refused that dispatch. The screen's LAST line is the documented idle input row
    `Type your message or @path/to/file` — that row, below the quoted block, is the veto that
    makes this deliver. Mutant killed: drop the idle-input veto — the quote then refuses and
    this dispatch exits 2.
    """
    screen = (
        "◎ main · ◎ h2-reviewer 42s\n"
        "The reference documents the selector verbatim:\n"
        " Do you trust the files in this folder?\n"
        "  ❯ 1. Trust folder\n"
        "    2. Don't trust and exit\n"
        "*   Type your message or @path/to/file\n"
    )
    state = {**DEFAULT_STATE, "agent_read_text": screen}
    done = stub.run("reviewer", "--file", str(payload_file(tmp_path)), "--no-wait", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert len(stub.prompts()) == 1
    assert len(_dispatch_reads(stub)) == 1


def test_dispatch_group_roster_is_scoped_to_the_lane(stub: StubHarness, tmp_path: Path) -> None:
    """#270: the roster is the lane, not every agent sharing the workspace and tab."""
    state = {
        **DEFAULT_STATE,
        "agents": [
            {"pane_id": "w9:p1", "name": "harness-tm", "agent": "pi", "agent_status": "working"},
            {"pane_id": "w9:p2", "name": "harness-impl", "agent": "pi", "agent_status": "working"},
            {"pane_id": "w9:p3", "name": "style-tm", "agent": "pi", "agent_status": "working"},
        ],
        "panes": [
            {**DEFAULT_STATE["panes"][0], "cwd": "/tmp/harness"},
            {
                "pane_id": "w9:p2",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": "pi",
                "agent_status": "working",
                "cwd": "/tmp/harness",
                "label": "impl",
            },
            {
                "pane_id": "w9:p3",
                "tab_id": "w9:t1",
                "workspace_id": "w9",
                "agent": "pi",
                "agent_status": "working",
                "cwd": "/tmp/harness",
                "label": "style",
            },
        ],
    }

    done = stub.run(
        "w9:p2",
        "--file",
        str(payload_file(tmp_path, "do this")),
        "--no-wait",
        "--task-group",
        "harness",
        state=state,
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    envelope, _body = herdr_prompt.split_envelope_and_body(call[4])
    assert envelope is not None
    assert envelope.group == ("harness-tm@w9:p1", "harness-impl@w9:p2")
