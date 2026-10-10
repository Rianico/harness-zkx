"""Tests for skills/herdr/scripts/herdr_reply.py (herdr-reply helper).

Integration cases route through the shared stub `herdr`; payload assertions read back the
recorded argv, proving byte-for-byte delivery without caller context injection.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import herdr_cli
import herdr_lease
import herdr_prompt
import herdr_reply
import pytest
import yaml

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness
from tests.herdr.test_herdr_reply_store import entry_for, failing_write, index_write_seam

SCRIPT = SCRIPTS_DIR / "herdr_reply.py"
REPO_ROOT = Path(__file__).resolve().parents[2]
LANE_COORDINATION = REPO_ROOT / "skills" / "herdr" / "references" / "lane-coordination.md"
RESP_FORMAT = REPO_ROOT / "skills" / "dynamic-workflow-wrapper" / "references" / "resp-format.md"
SKILL_MD = REPO_ROOT / "skills" / "herdr" / "SKILL.md"

METACHARS = """COMPLETED artifacts=[foo.py] issues=[]
Do NOT expand: $HOME `whoami` "$(date)" 'single' \\backslash
```bash
echo "code fence survived"
```"""


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    return stub_factory(SCRIPT)


def payload_file(tmp_path: Path, text: str = METACHARS) -> Path:
    path = tmp_path / "result.md"
    _ = path.write_text(text, encoding="utf-8")
    return path


def test_positional_message_is_delivered_verbatim(stub: StubHarness) -> None:
    done = stub.run("orchestrator", METACHARS)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[1:4] == ["agent", "prompt", "orchestrator"]
    assert call[4].endswith(METACHARS)
    envelope = call[4].splitlines()
    assert envelope[1] == "Routing:"
    assert envelope[2] == "  Sender: reviewer@w9:p1 - tab w9:t1 - kind pi"
    assert envelope[3] == "  Receiver(You): orchestrator"
    assert envelope[4] == "Hierarchy:"
    assert envelope[5] == "  Task-Group: w9:t1"
    assert envelope[6] == "Protocol:"
    assert envelope[7] == f"  {herdr_prompt.SKILL_NOTICE}"
    assert "Cwd:" not in call[4], "a reply stays short: no resumption fields"
    assert "reply to the sender" not in call[4]
    assert "replied to orchestrator" in done.stdout


def test_file_payload_is_delivered_verbatim(stub: StubHarness, tmp_path: Path) -> None:
    path = payload_file(tmp_path)
    done = stub.run("orchestrator", "--file", str(path))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[4].endswith(METACHARS)
    assert "Receiver(You): orchestrator" in call[4]


def test_stdin_payload_is_delivered_verbatim(stub: StubHarness) -> None:
    done = stub.run("orchestrator", stdin=METACHARS)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[4].endswith(METACHARS)
    assert "Receiver(You): orchestrator" in call[4]


def test_missing_target_is_rejected(stub: StubHarness) -> None:
    done = stub.run()
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "TARGET" in done.stderr
    assert stub.prompts() == []


def test_message_and_file_together_are_rejected(stub: StubHarness, tmp_path: Path) -> None:
    done = stub.run("orchestrator", "msg", "--file", str(payload_file(tmp_path)))
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not both" in done.stderr
    assert stub.prompts() == []


def test_empty_payload_is_rejected(stub: StubHarness) -> None:
    done = stub.run("orchestrator", "   \n")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "empty" in done.stderr
    assert stub.prompts() == []


def test_refuses_without_herdr_env(stub: StubHarness) -> None:
    done = stub.run("orchestrator", "done", env={"HERDR_ENV": None})
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "HERDR_ENV" in done.stderr
    assert stub.calls() == []


def test_refuses_target_that_is_an_agent_kind(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "agents": [{"pane_id": "w9:p1", "name": "orch-1", "agent": "pi"}],
    }
    done = stub.run("pi", "done", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "is an agent kind" in done.stderr
    assert "live agents of this kind: orch-1" in done.stderr
    assert stub.prompts() == []


def test_refuses_qoderclicn_target_that_is_an_agent_kind(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "agents": [{"pane_id": "w9:p2", "name": "orch-2", "agent": "qoderclicn"}],
    }
    done = stub.run("qoderclicn", "done", state=state)
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "is an agent kind" in done.stderr
    assert "live agents of this kind: orch-2" in done.stderr
    assert stub.prompts() == []


def test_delivery_reports_revision_increment(stub: StubHarness) -> None:
    state = {
        **DEFAULT_STATE,
        "agent_get": {"orchestrator": {"revision": "r42", "pane_id": "w9:p1"}},
    }
    done = stub.run("orchestrator", "COMPLETED", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "replied to orchestrator" in done.stdout
    assert "revision=r42" in done.stdout


def test_dry_run_prints_argv_without_submitting(stub: StubHarness) -> None:
    done = stub.run("orchestrator", "COMPLETED", "--dry-run")
    from typing import cast

    parsed = cast(object, json.loads(done.stdout))
    assert isinstance(parsed, list)
    assert parsed[1:4] == ["agent", "prompt", "orchestrator"]
    assert parsed[4].endswith("COMPLETED")


def test_wait_and_timeout_forwarded(stub: StubHarness) -> None:
    done = stub.run("orchestrator", "COMPLETED", "--wait", "--timeout", "15000")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[5:] == ["--wait", "--timeout", "15000"]


def test_auto_start_starts_agent_on_shell_pane_and_delivers_reply(stub: StubHarness) -> None:
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
                "label": "lens-orchestrator",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    done = stub.run("lens-orchestrator", "COMPLETED", "--auto-start", "pi", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.starts() == [
        [
            str(stub.herdr),
            "agent",
            "start",
            "lens-orchestrator",
            "--kind",
            "pi",
            "--pane",
            "wM:p1N",
        ]
    ]
    (call,) = stub.prompts()
    assert call[1:4] == ["agent", "prompt", "lens-orchestrator"]
    assert call[4].endswith("COMPLETED")
    assert "replied to lens-orchestrator (wM:p1N)" in done.stdout


def test_auto_start_on_pane_id_with_label(stub: StubHarness) -> None:
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
                "label": "lens-orchestrator",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    done = stub.run("wM:p1N", "COMPLETED", "--auto-start", "claude", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.starts() == [
        [
            str(stub.herdr),
            "agent",
            "start",
            "lens-orchestrator",
            "--kind",
            "claude",
            "--pane",
            "wM:p1N",
        ]
    ]
    (call,) = stub.prompts()
    assert call[1:4] == ["agent", "prompt", "lens-orchestrator"]
    assert call[4].endswith("COMPLETED")


def test_auto_start_when_target_already_has_live_agent_skips_start(stub: StubHarness) -> None:
    done = stub.run("reviewer", "COMPLETED", "--auto-start", "pi")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.starts() == []
    (call,) = stub.prompts()
    assert call[1:4] == ["agent", "prompt", "reviewer"]
    assert call[4].endswith("COMPLETED")


def test_auto_start_with_unrecognized_kind_fails(stub: StubHarness) -> None:
    done = stub.run("reviewer", "COMPLETED", "--auto-start", "notakind")
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "not a recognized agent kind" in done.stderr
    assert stub.starts() == []


def test_auto_start_dry_run_skips_submitting(stub: StubHarness) -> None:
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
                "label": "lens-orchestrator",
            }
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }
    done = stub.run(
        "lens-orchestrator", "COMPLETED", "--auto-start", "pi", "--dry-run", state=state
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.starts() == []
    assert stub.prompts() == []


def test_reply_releases_lease_for_current_agent(stub: StubHarness, tmp_path: Path) -> None:
    import herdr_lease

    _ = herdr_lease.acquire_lease("reviewer", "task.md", "orchestrator", base_dir=tmp_path)
    assert herdr_lease.get_lease("reviewer", base_dir=tmp_path) is not None

    done = stub.run("orchestrator", "COMPLETED", env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert herdr_lease.get_lease("reviewer", base_dir=tmp_path) is None


def test_reply_is_delivered_when_no_lease_store_resolves(stub: StubHarness, tmp_path: Path) -> None:
    """B1: delivery is not a function of store resolution (#229).

    A callee in a scratch directory no anchor covers still gets its completion through —
    exit 0 and one prompt — and every lease step it could not run says so on stderr
    (correlation, trajectory note, release) instead of aborting the reply or vanishing.
    """
    scratch = tmp_path / "no-repo"
    scratch.mkdir()

    done = stub.run(
        "orchestrator", "COMPLETED", env={"HERDR_LANE_DIR": None, "PWD": str(scratch)}, cwd=scratch
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert len(stub.prompts()) == 1
    assert "replied to orchestrator" in done.stdout
    for step in ("lease correlation", "trajectory note", "lease release"):
        assert f"{step} skipped" in done.stderr
    assert done.stderr.count("no lane state anchor") == 3


def test_reply_without_a_resolvable_store_drops_envelope_metadata_only(
    stub: StubHarness, tmp_path: Path
) -> None:
    """F2: a skipped correlation loses `Ticket-ID`/`In-Reply-To`, never the reply.

    Correlation is by pane/target (`agent prompt <target> <payload>`), so the caller still
    matches the reply to its outstanding request; only the envelope enrichment degrades.
    """
    scratch = tmp_path / "no-repo"
    scratch.mkdir()

    done = stub.run(
        "orchestrator", "COMPLETED", env={"HERDR_LANE_DIR": None, "PWD": str(scratch)}, cwd=scratch
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert "Ticket-ID:" not in call[4]
    assert "In-Reply-To:" not in call[4]
    assert "COMPLETED" in call[4]


def test_reply_does_not_release_lease_for_target_caller(stub: StubHarness, tmp_path: Path) -> None:
    import herdr_lease

    # Orchestrator is the target/caller receiving the reply, not the sender
    _ = herdr_lease.acquire_lease("orchestrator", "task.md", "prev", base_dir=tmp_path)
    assert herdr_lease.get_lease("orchestrator", base_dir=tmp_path) is not None

    done = stub.run("orchestrator", "COMPLETED", env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    # Calling herdr-reply must NOT release target's active lease
    assert herdr_lease.get_lease("orchestrator", base_dir=tmp_path) is not None


def test_reply_populates_correlation_from_sender_lease_and_releases(
    stub: StubHarness, tmp_path: Path
) -> None:
    import herdr_lease

    _ = herdr_lease.acquire_lease(
        "reviewer",
        "182-herdr-msg-enhance.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#182-herdr-msg-enhance",
        task_id="#182-herdr-msg-enhance#full-stack",
    )
    done = stub.run("orchestrator", "COMPLETED", env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    text = call[4]
    assert "  Ticket-ID: #182-herdr-msg-enhance" in text
    assert "  In-Reply-To: #182-herdr-msg-enhance#full-stack" in text
    assert herdr_lease.get_lease("reviewer", base_dir=tmp_path) is None


def test_reply_without_sender_lease_omits_correlation_and_still_sends(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run("orchestrator", "COMPLETED", env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert "Ticket-ID:" not in call[4]
    assert "In-Reply-To:" not in call[4]


def _shell_target_state() -> dict[str, object]:
    """Default live sender plus a bare-shell pane labelled `lens-orchestrator`."""
    return {
        **DEFAULT_STATE,
        "panes": [
            *DEFAULT_STATE["panes"],
            {
                "pane_id": "wM:p1N",
                "tab_id": "wM:t1",
                "workspace_id": "wM",
                "agent": None,
                "agent_status": "unknown",
                "cwd": "/tmp",
                "label": "lens-orchestrator",
            },
        ],
        "process_info": {
            "wM:p1N": {
                "shell_pid": 1234,
                "foreground_processes": [{"name": "zsh", "pid": 1234}],
            }
        },
    }


RECOVERY = {
    "pane_id": "wM:p1N",
    "kind": "pi",
    "resume_cmd": "pi --session sess.jsonl",
    "cwd": "/repo",
}


def test_reply_records_completion_event_with_sha(stub: StubHarness, tmp_path: Path) -> None:
    import herdr_lease

    task_id = "#183-tasks-yaml-and-preflight#full-stack"
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "183_tasks_yaml_and_preflight_impl.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#183-tasks-yaml-and-preflight",
        task_id=task_id,
    )
    # A bare `COMPLETED` carries no evidence and is recorded incomplete, so it no longer
    # advances the task (#231). Keep the same payload first line and add an evidence section,
    # so this case still pins the completed-event path with its sha.
    done = stub.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 660 passed",
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["status"] == "completed"
    completed = [event for event in task["trajectory"] if event["event"] == "completed"]
    assert len(completed) == 1
    assert completed[-1]["sha"] == "deadbeef"
    assert completed[-1]["to_status"] == "completed"
    # The trajectory note is metadata only (#231 F3): the mapped token and the validated sha,
    # never the raw status line. `deadbeef` is a hex token, so it is the recorded sha.
    assert completed[-1]["note"] == "completed deadbeef"
    assert herdr_lease.get_lease("reviewer", base_dir=tmp_path) is None


@pytest.mark.parametrize(
    ("body", "expected"),
    [("BLOCKED awaiting credentials", "blocked"), ("REJECTED diff too large", "rework")],
)
def test_reply_maps_blocked_and_rejected_statuses(
    stub: StubHarness, tmp_path: Path, body: str, expected: str
) -> None:
    import herdr_lease

    task_id = f"#183#{expected}"
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "183_tasks_yaml_and_preflight_impl.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#183",
        task_id=task_id,
    )
    done = stub.run("orchestrator", body, env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["status"] == expected
    assert task["trajectory"][-1]["event"] == expected
    assert herdr_lease.get_lease("reviewer", base_dir=tmp_path) is None


def test_reply_emits_recovery_diagnostic_for_exited_target(
    stub: StubHarness, tmp_path: Path
) -> None:
    import herdr_lease

    _ = herdr_lease.acquire_lease(
        "reviewer",
        "183_tasks_yaml_and_preflight_impl.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#183",
        task_id="#183#recovery",
        caller_recovery=RECOVERY,
    )
    done = stub.run(
        "lens-orchestrator",
        "COMPLETED",
        env={"PWD": str(tmp_path)},
        state=_shell_target_state(),
    )
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "target agent 'lens-orchestrator' in pane wM:p1N has exited." in done.stderr
    assert (
        "uv run ~/.agents/skills/herdr/scripts/herdr_reply.py lens-orchestrator "
        "--file <reply> --auto-start pi"
    ) in done.stderr
    assert "Or resume manually in pane wM:p1N: pi --session sess.jsonl" in done.stderr
    assert stub.prompts() == []


def test_reply_auto_start_revives_and_delivers_with_recovery(
    stub: StubHarness, tmp_path: Path
) -> None:
    import herdr_lease

    _ = herdr_lease.acquire_lease(
        "reviewer",
        "183_tasks_yaml_and_preflight_impl.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#183",
        task_id="#183#active",
        caller_recovery=RECOVERY,
    )
    done = stub.run(
        "lens-orchestrator",
        "COMPLETED",
        "--auto-start",
        "pi",
        env={"PWD": str(tmp_path)},
        state=_shell_target_state(),
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.starts() == [
        [
            str(stub.herdr),
            "agent",
            "start",
            "lens-orchestrator",
            "--kind",
            "pi",
            "--pane",
            "wM:p1N",
        ]
    ]
    (call,) = stub.prompts()
    assert call[1:4] == ["agent", "prompt", "lens-orchestrator"]
    assert call[4].endswith("COMPLETED")


def test_reply_without_recovery_keeps_existing_shell_diagnostic(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run(
        "lens-orchestrator",
        "COMPLETED",
        env={"PWD": str(tmp_path)},
        state=_shell_target_state(),
    )
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "no live agent" in done.stderr
    assert "has exited" not in done.stderr
    assert stub.prompts() == []


def test_format_reply_recovery_diagnostic_exact_shape() -> None:
    recovery = {
        "pane_id": "wM:p1N",
        "kind": "pi",
        "resume_cmd": "pi --session sess.jsonl",
        "cwd": "/repo",
    }
    assert herdr_reply.format_reply_recovery_diagnostic(
        "lens-orchestrator", recovery, "<reply>"
    ) == (
        "herdr-reply: target agent 'lens-orchestrator' in pane wM:p1N has exited.\n"
        "Suggested recovery:\n"
        "  1. Auto-revive & deliver: uv run ~/.agents/skills/herdr/scripts/herdr_reply.py "
        "lens-orchestrator --file <reply> --auto-start pi\n"
        "  2. Or resume manually in pane wM:p1N: pi --session sess.jsonl"
    )
    # Line 2 is omitted when no resume command is known.
    assert herdr_reply.format_reply_recovery_diagnostic(
        "callee", {"pane_id": "w1:p1", "kind": "claude"}, "reply.md"
    ) == (
        "herdr-reply: target agent 'callee' in pane w1:p1 has exited.\n"
        "Suggested recovery:\n"
        "  1. Auto-revive & deliver: uv run ~/.agents/skills/herdr/scripts/herdr_reply.py "
        "callee --file reply.md --auto-start claude"
    )


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("COMPLETED deadbeef", ("completed", "deadbeef")),
        ("BLOCKED: nope", ("blocked", None)),
        ("REJECTED why", ("rework", None)),
        ("hello there", (None, None)),
        ("\n\ncompleted abc", ("completed", "abc")),
        ("   ", (None, None)),
    ],
)
def test_parse_status_line_maps_first_nonempty_line(
    body: str, expected: tuple[str | None, str | None]
) -> None:
    mapped, sha, _ = herdr_reply.parse_status_line(body)
    assert (mapped, sha) == expected


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
    assert "usage: herdr-reply" in done.stdout


# ── payload shape (#231): a COMPLETED reply must cite evidence ───────────────────────
#
# `payload_shape` is a shape check, not a quality gate: it classifies whether a COMPLETED
# payload *cites* evidence, never whether that evidence is any good. Every row starts with
# the status line, because the check applies only when the first line maps to completed.
#
#   payload                                   shape        evidence heading
#   COMPLETED + "## Evidence" + body          complete     Evidence
#   COMPLETED + "**Evidence:** 660 passed"    complete     Evidence
#   COMPLETED + "Gates:" + a command line     complete     Gates
#   COMPLETED + "### Test output" + body      complete     Test output
#   COMPLETED + a fence with a non-blank line complete     ```
#   COMPLETED + "## Verification" + body      complete     Verification
#   COMPLETED                                 incomplete   None
#   COMPLETED abc1234                         incomplete   None
#   COMPLETED + "## Notes" + body             incomplete   None
#   COMPLETED + "## Evidence" then a heading  incomplete   None   (empty body)
#   COMPLETED + "## Next steps" + body        incomplete   None
#   BLOCKED waiting on CI                     n/a          None
#   REJECTED needs rework                     n/a          None
#   plain prose with no status line           n/a          None
#
# Second table, `test_realistic_evidence_headings_are_complete` — the widened floor (#231
# F4): a heading is evidence-shaped when a word matches the evidence vocabulary (an exact
# keyword or an evidence stem like `validat`/`result`/`diff`), or, for a heading form that
# vocabulary does not cover, when it has a body and its label is not in
# `NOT_EVIDENCE_HEADS`:
#
#   ## Evidence       complete   ## Validation output    complete
#   ## Verification   complete   ## Results             complete
#   ## Artifacts      complete   ## Benchmark results   complete
#   ## Tests          complete   ## Reproduced          complete
#   ## Gates          complete   ## Commands run        complete
#   ## Gate output    complete   ## CI / ## Diff        complete
#   ## Validation     complete   ## What I ran          complete
#   ## Status         complete   ## Outcome             complete
#   ## Acceptance     complete
#
# Third table, `test_shape_floor_stays_incomplete` — the floor is unchanged: a bare
# `COMPLETED`, a `COMPLETED <non-hex>`, a heading with no body, and a denied heading
# (`Notes`, `Next steps`, `Todo`, `Plan`, `Questions`, `Changelog`) are all `incomplete`.
#
# `evidence_section`'s precedence is the other half of F4/F5: a heading naming the canonical
# section (`Evidence`, `Verification`) outranks any other evidence-vocabulary heading, which
# outranks the deny-list floor, which outranks a fenced block. That is why the repo's own
# reply template records `Evidence` even though `## Artifacts` precedes it.


@pytest.mark.parametrize(
    ("payload", "shape", "heading"),
    [
        ("COMPLETED\n## Evidence\n- 660 passed", "complete", "Evidence"),
        ("COMPLETED\n**Evidence:** 660 passed", "complete", "Evidence"),
        ("COMPLETED\nGates:\n$ bash scripts/check.sh", "complete", "Gates"),
        ("COMPLETED\n### Test output\n66 passed", "complete", "Test output"),
        ("COMPLETED\n```\n660 passed\n```", "complete", "```"),
        ("COMPLETED\n## Verification\nall good", "complete", "Verification"),
        ("COMPLETED", "incomplete", None),
        ("COMPLETED abc1234", "incomplete", None),
        ("COMPLETED\n## Notes\nall good", "incomplete", None),
        ("COMPLETED\n## Evidence\n## Next steps\nlater", "incomplete", None),
        ("COMPLETED\n## Next steps\nlater", "incomplete", None),
        ("BLOCKED waiting on CI", "n/a", None),
        ("REJECTED needs rework", "n/a", None),
        ("plain prose with no status line", "n/a", None),
    ],
)
def test_payload_shape_table(payload: str, shape: str, heading: str | None) -> None:
    assert herdr_reply.payload_shape(payload) == (shape, heading)


def test_payload_shape_leaves_blocked_payloads_alone() -> None:
    # No evidence requirement for BLOCKED: even a keyword heading does not make it complete.
    assert herdr_reply.payload_shape("BLOCKED waiting on CI\n## Evidence\n- logs") == ("n/a", None)


def test_evidence_section_skips_an_empty_keyword_heading() -> None:
    # The first evidence-shaped section wins: an empty `## Evidence` is not one, so the next
    # keyword heading with a body is.
    assert herdr_reply.evidence_section("## Evidence\n## Verification\nall good") == "Verification"


REALISTIC_EVIDENCE_HEADINGS = (
    "Evidence",
    "Verification",
    "Artifacts",
    "Tests",
    "Gates",
    "Gate output",
    "Validation",
    "Validation output",
    "Results",
    "Benchmark results",
    "Reproduced",
    "Commands run",
    "CI",
    "Diff",
    "What I ran",
    "Status",
    "Outcome",
    "Acceptance",
)


@pytest.mark.parametrize("heading", REALISTIC_EVIDENCE_HEADINGS)
def test_realistic_evidence_headings_are_complete(heading: str) -> None:
    """F4: every realistic evidence heading with a body is `complete`, not a false negative."""
    payload = f"COMPLETED deadbeef\n\n## {heading}\n- 660 passed\n"
    assert herdr_reply.payload_shape(payload) == ("complete", heading)


@pytest.mark.parametrize(
    "payload",
    [
        "COMPLETED",
        "COMPLETED abc1234",
        "COMPLETED\n\n## Notes\nall good",
        "COMPLETED\n\n## Note\nall good",
        "COMPLETED\n\n## Next steps\nlater",
        "COMPLETED\n\n## Next\nlater",
        "COMPLETED\n\n## Todo\nlater",
        "COMPLETED\n\n## TBD\nlater",
        "COMPLETED\n\n## Plan\nlater",
        "COMPLETED\n\n## Questions\nlater",
        "COMPLETED\n\n## Changelog\nlater",
        # A heading with no body is never a section, however it is named.
        "COMPLETED\n\n## Status\n",
        "COMPLETED\n\n## Status\n\n## Notes\nlater",
    ],
)
def test_shape_floor_stays_incomplete(payload: str) -> None:
    """F4: the widened floor still refuses a payload that cites nothing."""
    assert herdr_reply.payload_shape(payload) == ("incomplete", None)


def test_the_floor_has_no_path_citation_fallback() -> None:
    """A cited path is not evidence: `## Notes` plus a path stays `incomplete` (#231 F4)."""
    payload = "COMPLETED deadbeef\n\n## Notes\n- see /home/u/.aws/credentials\n"
    assert herdr_reply.payload_shape(payload) == ("incomplete", None)


# ── the repo's own documented reply formats satisfy the floor (#231 F4/F5/F6) ────────


def fenced_blocks(text: str, info: str) -> list[str]:
    """The bodies of every fenced block opened with exactly `info` (e.g. `markdown`)."""
    blocks: list[str] = []
    body: list[str] | None = None
    for line in text.splitlines():
        if body is None:
            if line.strip() == f"```{info}":
                body = []
            continue
        if line.startswith("```"):
            blocks.append("\n".join(body))
            body = None
            continue
        body.append(line)
    if body is not None:
        blocks.append("\n".join(body))
    return blocks


def test_response_format_section_headings_pass_the_floor() -> None:
    """Every Mode A heading in the canonical response format is evidence-shaped.

    Read from the repo's own fixture, so the check tracks the documented format: a reply
    shaped by `resp-format.md` must never be recorded `incomplete` merely for its headings,
    and the format's `## Evidence` section is the one the record names.
    """
    block = next(
        block
        for block in fenced_blocks(RESP_FORMAT.read_text(encoding="utf-8"), "markdown")
        if "## Evidence" in block
    )
    assert [line for line in block.splitlines() if line.startswith("## ")] == [
        "## Summary",
        "## Artifacts",
        "## Evidence",
        "## Route",
        "## Issues",
        "## Suggestions (Optional)",
    ]
    headings = [line for line in block.splitlines() if line.startswith("## ")]
    assert herdr_reply.payload_shape(f"COMPLETED deadbeef\n{block}") == ("complete", "Evidence")
    for heading in headings:
        one = f"COMPLETED deadbeef\n\n{heading}\n- 660 passed"
        assert herdr_reply.payload_shape(one)[0] == "complete", heading


def test_canonical_template_records_the_evidence_section() -> None:
    """F5: the repo's own reply template records `evidence: evidence`, not `artifacts`."""
    block = next(
        block
        for block in fenced_blocks(LANE_COORDINATION.read_text(encoding="utf-8"), "markdown")
        if block.startswith("COMPLETED")
    )
    assert "## Artifacts" in block and "## Evidence" in block
    assert block.index("## Artifacts") < block.index("## Evidence")
    assert herdr_reply.evidence_section(block) == "Evidence"
    assert herdr_reply.payload_shape(block) == ("complete", "Evidence")
    assert herdr_reply.evidence_label("Evidence") == "evidence"


def test_skill_reply_examples_show_an_evidence_section() -> None:
    """The two `herdr-reply` examples in SKILL.md must show an evidence section (F6).

    The paragraph right below those examples already requires an evidence section for a
    `COMPLETED` reply, so the examples must carry one too. This is a live pin: the doc
    rewrite landed, so a bare `COMPLETED` payload here now fails the gate.
    """
    payloads = [
        match.group(1)
        for line in SKILL_MD.read_text(encoding="utf-8").splitlines()
        if "herdr_reply.py" in line
        for match in [re.search(r'orchestrator "([^"]*)"', line)]
        if match is not None
    ]
    assert len(payloads) == 2, payloads
    for payload in payloads:
        assert herdr_reply.payload_shape(payload)[0] == "complete", payload


# ── persist first, then poke (#231) ──────────────────────────────────────────────────


def test_reply_persists_a_record_a_later_reader_resolves(
    stub: StubHarness, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A valid reply lands in the store and is re-derivable through the reader."""
    body = (
        "COMPLETED abc1234\n\n"
        "## Evidence\n"
        "- 660 passed\n"
        "- see scripts/check.sh and tests/herdr/test_herdr_reply.py for details\n"
    )
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()

    done = stub.run("orchestrator", body)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    (call,) = stub.prompts()
    assert call[4].endswith(body)
    assert "Payload: COMPLETE" in call[4]
    assert f"sha256={digest}" in call[4]

    # `herdr-lease replies` is the reader the orchestrator uses to re-derive evidence.
    code = herdr_lease.main(["replies", "--json"], env={"HERDR_LANE_DIR": str(tmp_path)})
    assert code == 0
    captured = capsys.readouterr()
    records = json.loads(captured.out)
    assert len(records) == 1
    record = records[0]
    assert record["shape"] == "complete"
    # The ledger stores the label, not the heading text, and counts the cited artifacts
    # instead of copying paths (#231 F3).
    assert record["evidence"] == "evidence"
    assert record["status"] == "completed"
    assert record["sha"] == "abc1234"
    assert "status_line" not in record
    assert record["digest"] == digest
    assert record["payload"] == f".lane/replies/{record['id']}.md"
    assert record["artifacts"] == 2

    # ...and the same record resolves through `get_reply`.
    resolved = herdr_lease.get_reply(record["id"], env={"HERDR_LANE_DIR": str(tmp_path)})
    assert resolved == record

    # The payload file holds exactly the body bytes.
    payload_path = tmp_path / record["payload"]
    assert payload_path.read_bytes() == body.encode("utf-8")

    # The human reader names the record, both sides of the correlation, and the store path.
    assert herdr_lease.main(["replies", record["id"]], env={"HERDR_LANE_DIR": str(tmp_path)}) == 0
    captured = capsys.readouterr()
    assert record["id"] in captured.out
    assert "reviewer -> orchestrator" in captured.out
    assert record["payload"] in captured.out


def test_reply_reader_exits_two_on_an_unknown_record_id(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = herdr_lease.main(["replies", "no-such-record"], env={"HERDR_LANE_DIR": str(tmp_path)})
    assert code == herdr_cli.EXIT_USAGE
    captured = capsys.readouterr()
    assert "no reply record 'no-such-record'" in captured.err


def test_reply_keeps_a_canary_out_of_the_ledger(stub: StubHarness, tmp_path: Path) -> None:
    """Prompt text is never provenance: the body stays a file, the ledger stays metadata."""
    canary = f"SECRET-CANARY-{secrets.token_hex(6)}"
    body = f"COMPLETED deadbeef\n\n## Evidence\n- scanned {canary} clean\n"

    done = stub.run("orchestrator", body)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    index_files = sorted((tmp_path / ".lane").rglob("*.yaml"))
    assert index_files, "the store must hold an index for the recorded reply"
    for path in index_files:
        assert canary not in path.read_text(encoding="utf-8"), path

    bodies = list((tmp_path / ".lane" / "replies").glob("*.md"))
    assert len(bodies) == 1
    assert canary in bodies[0].read_text(encoding="utf-8")


def test_reply_delivers_body_only_when_the_store_write_fails(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Requirement 5: a deterministic unresolvable store — `HERDR_LANE_DIR` names a FILE,
    so `.lane/replies` cannot be created under it. Delivery still succeeds body-only."""
    blocker = tmp_path / "not-a-directory"
    _ = blocker.write_text("a file, so nothing can be created underneath it", encoding="utf-8")
    body = "COMPLETED deadbeef\n\n## Evidence\n- 660 passed"

    done = stub.run("orchestrator", body, env={"HERDR_LANE_DIR": str(blocker)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[1:4] == ["agent", "prompt", "orchestrator"]
    assert call[4].endswith(body)
    assert "Payload: NOT RECORDED" in call[4]
    assert "reply record skipped" in done.stderr


def test_reply_delivers_body_only_when_no_anchor_resolves(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Requirement 5, second setup: no `HERDR_LANE_DIR` and no git dir under the cwd."""
    scratch = tmp_path / "no-repo"
    scratch.mkdir()
    body = "COMPLETED\n\n## Evidence\n- ran the gate"

    done = stub.run(
        "orchestrator", body, env={"HERDR_LANE_DIR": None, "PWD": str(scratch)}, cwd=scratch
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[4].endswith(body)
    assert "Payload: NOT RECORDED" in call[4]


# ── prompt text is never provenance (#231) ───────────────────────────────────────────


def test_incomplete_completed_reply_does_not_advance_the_leased_task(
    stub: StubHarness, tmp_path: Path
) -> None:
    task_id = "#231#incomplete"
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "231.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#231",
        task_id=task_id,
    )

    done = stub.run("orchestrator", "COMPLETED deadbeef", env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["status"] == "dispatched"
    assert [event for event in task["trajectory"] if event["event"] == "completed"] == []

    # The verdict rides on the ledger record, not on a fabricated canonical status.
    assert herdr_lease.list_replies(base_dir=tmp_path)[-1]["shape"] == "incomplete"
    # The lease still releases: bookkeeping is unchanged, only the state advance is gated.
    assert herdr_lease.get_lease("reviewer", base_dir=tmp_path) is None


def test_complete_completed_reply_records_the_completed_event(
    stub: StubHarness, tmp_path: Path
) -> None:
    task_id = "#231#complete"
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "231.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#231",
        task_id=task_id,
    )
    body = "COMPLETED deadbeef\n\n## Evidence\n- 660 passed"

    done = stub.run("orchestrator", body, env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["status"] == "completed"
    completed = [event for event in task["trajectory"] if event["event"] == "completed"]
    assert len(completed) == 1
    assert completed[-1]["sha"] == "deadbeef"


def test_record_sender_status_is_silent_without_a_store_record(
    stub: StubHarness, tmp_path: Path
) -> None:
    task_id = "#231#norecord"
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "231.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#231",
        task_id=task_id,
    )
    env = stub.base_env()

    def still_dispatched() -> None:
        task = herdr_lease.get_task(task_id, base_dir=tmp_path)
        assert task is not None
        assert task["status"] == "dispatched"
        assert task["trajectory"][-1]["event"] == "dispatched"

    # No record id: an unpersisted reply advances nothing.
    herdr_reply.record_sender_status(str(stub.herdr), env, "completed", "deadbeef", record_id=None)
    still_dispatched()

    # A record id the store does not hold is equally silent.
    herdr_reply.record_sender_status(
        str(stub.herdr),
        env,
        "completed",
        "deadbeef",
        record_id="no-such-record",
        shape="complete",
    )
    still_dispatched()

    # A persisted record whose shape is incomplete carries the verdict: no state advance.
    entry = herdr_reply.build_reply_entry(
        "COMPLETED deadbeef",
        sender="reviewer",
        caller="orchestrator",
        ticket_id="#231",
        task_id=task_id,
        in_reply_to=task_id,
        mapped="completed",
        sha="deadbeef",
        shape="incomplete",
        evidence=None,
    )
    stored = herdr_lease.record_reply(entry, "COMPLETED deadbeef", base_dir=tmp_path)
    herdr_reply.record_sender_status(
        str(stub.herdr),
        env,
        "completed",
        "deadbeef",
        record_id=str(stored["id"]),
        shape="incomplete",
    )
    still_dispatched()


# ── the store under concurrency and failure (#231 F1/F2/F-C1/F-C2) ───────────────────

CANARY_LINE1 = "SECRETCANARYLINE1"
CANARY_HEADING = "SECRETCANARYHEADING"
CANARY_PATH = "/home/u/.aws/credentials"
CANARIES = (CANARY_LINE1, CANARY_HEADING, CANARY_PATH)
CANARY_PAYLOAD = (
    f"COMPLETED {CANARY_LINE1}\n\n"
    f"## Evidence {CANARY_HEADING}\n"
    f"- scanned {CANARY_PATH} and tests/herdr/test_herdr_reply.py clean\n"
)


def test_no_payload_text_reaches_the_ledger(
    stub: StubHarness, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """F3: a canary on line 1, in the evidence heading, or in a path token stays in the body.

    The body file holds the payload verbatim; no index file under the store, and none of the
    reader's three modes, may reprint any of the three canaries.
    """
    done = stub.run("orchestrator", CANARY_PAYLOAD)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    (call,) = stub.prompts()
    pointer = call[4][: len(call[4]) - len(CANARY_PAYLOAD)]
    for canary in CANARIES:
        assert canary not in pointer, "the delivered pointer must stay metadata only"

    bodies = list((tmp_path / ".lane" / "replies").glob("*.md"))
    assert len(bodies) == 1
    body_text = bodies[0].read_text(encoding="utf-8")
    for canary in CANARIES:
        assert canary in body_text

    index_files = sorted((tmp_path / ".lane").rglob("*.yaml"))
    assert index_files, "the store must hold an index for the recorded reply"
    for path in index_files:
        stored = path.read_text(encoding="utf-8")
        for canary in CANARIES:
            assert canary not in stored, path

    record_id = bodies[0].stem
    for argv in (
        ["replies"],
        ["replies", "--json"],
        ["replies", "--yaml"],
        ["replies", record_id],
    ):
        assert herdr_lease.main(argv, env={"HERDR_LANE_DIR": str(tmp_path)}) == 0
        captured = capsys.readouterr()
        for canary in CANARIES:
            assert canary not in captured.out + captured.err, argv


def test_lease_event_note_keeps_a_canary_out_of_the_store(
    stub: StubHarness, tmp_path: Path
) -> None:
    """F3 on the lease path: the appended trajectory event carries metadata only.

    A canary in the first token of payload line 1 is the second token after `COMPLETED`, so
    it rides `parse_status_line`'s sha slot. The event is still appended (the behaviour), but
    its `note` and `sha` stay bounded: the mapped status token and a hex sha only. The canary
    lives in `.lane/replies/<id>.md` and nowhere under `.lane/*.yaml`.
    """
    canary = f"SECRET-CANARY-{secrets.token_hex(6)}"
    task_id = "#231#lease-canary"
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "231.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#231",
        task_id=task_id,
    )
    body = f"COMPLETED {canary}\n\n## Evidence\n- scanned {canary} clean\n"

    done = stub.run("orchestrator", body)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    bodies = list((tmp_path / ".lane" / "replies").glob("*.md"))
    assert len(bodies) == 1
    assert canary in bodies[0].read_text(encoding="utf-8")

    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["status"] == "completed"
    event = task["trajectory"][-1]
    assert event["event"] == "completed"
    assert event["note"] == "completed"
    assert "sha" not in event

    assert canary not in (tmp_path / ".lane" / "tasks.yaml").read_text(encoding="utf-8")
    for path in sorted((tmp_path / ".lane").rglob("*.yaml")):
        assert canary not in path.read_text(encoding="utf-8"), path


def test_parallel_reply_helpers_deliver_resolvable_pointers(
    stub: StubHarness, tmp_path: Path
) -> None:
    """F1: 16 concurrent `herdr-reply` runs in one lane leave 16 resolvable pointers."""
    env = stub.base_env()
    stub.write_state(DEFAULT_STATE)
    released = threading.Barrier(16)

    def deliver(index: int) -> int:
        body = f"COMPLETED deadbeef\n\n## Evidence\n- shard {index}\n"
        _ = released.wait()
        return herdr_reply.main(["orchestrator", body], env=env)

    with ThreadPoolExecutor(max_workers=16) as pool:
        codes = list(pool.map(deliver, range(16)))

    assert codes == [herdr_cli.EXIT_OK] * 16
    delivered = [
        match.group(1)
        for call in stub.prompts()
        if (match := re.search(r"record=(\S+)", call[4])) is not None
    ]
    assert len(delivered) == 16
    rows = herdr_lease.list_replies(limit=100, base_dir=tmp_path)
    assert len(rows) == 16
    for record_id in delivered:
        assert herdr_lease.get_reply(record_id, base_dir=tmp_path) is not None, (
            f"delivered pointer names an unresolvable record: {record_id}"
        )
    # No writer may quarantine another writer's index file: publication is create-only and
    # complete-before-visible, so a concurrent reader never sees a half-written record.
    assert list((tmp_path / ".lane" / "replies").glob("*.corrupt-*")) == []


def test_failed_record_leaves_no_orphan_and_delivers_not_recorded(
    stub: StubHarness, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F1/F-C3: a failed index write unlinks the body and degrades the pointer honestly."""
    monkeypatch.setattr(
        herdr_lease, index_write_seam(), failing_write(OSError("no space left on device"))
    )

    done = stub.run("orchestrator", CANARY_PAYLOAD)

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[1:4] == ["agent", "prompt", "orchestrator"]
    assert call[4].endswith(CANARY_PAYLOAD)
    assert "Payload: NOT RECORDED" in call[4]
    assert "reply record skipped" in done.stderr
    assert list((tmp_path / ".lane" / "replies").glob("*.md")) == []
    assert herdr_lease.list_replies(base_dir=tmp_path) == []


def test_a_record_that_does_not_resolve_is_discarded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The pointer never names a record the reader cannot produce: it is dropped instead.

    Driven at `persist_reply`, the helper's own module: the in-process script run executes the
    file as `__main__`, so only a *module* attribute patched here is the global the stored
    path resolves through. F1's re-resolution rule is what this pins.
    """
    base = tmp_path
    body = "COMPLETED deadbeef\n\n## Evidence\n- 660 passed\n"
    entry = entry_for(body, record_id="row-1")

    def unresolved(*args: Any, **kwargs: Any) -> None:
        return None

    monkeypatch.setattr(herdr_reply, "get_reply", unresolved)

    stored, reason = herdr_reply.persist_reply(entry, body, env={"HERDR_LANE_DIR": str(base)})

    assert stored is None
    assert reason
    assert list((base / ".lane" / "replies").glob("*.md")) == []
    assert list((base / ".lane" / "replies").glob("*.yaml")) == []
    pointer = herdr_reply.pointer_block(
        shape="complete", evidence="evidence", stored=None, reason=reason
    )
    assert pointer is not None and "Payload: NOT RECORDED" in pointer


def test_unreadable_ledger_degrades_the_reply_and_preserves_the_file(
    stub: StubHarness, tmp_path: Path
) -> None:
    """F2: an unparsable ledger is preserved byte-for-byte; the reply says NOT RECORDED."""
    base = tmp_path
    prior_body = "COMPLETED deadbeef\n\n## Evidence\n- prior\n"
    _ = (base / ".lane" / "replies").mkdir(parents=True)
    _ = (base / ".lane" / "replies" / "prior.md").write_text(prior_body, encoding="utf-8")
    prior_row = {
        **entry_for(prior_body, record_id="prior"),
        "payload": ".lane/replies/prior.md",
        "evidence": "Evidence",
        "status_line": "COMPLETED deadbeef",
        "artifacts": ["tests/herdr/test_herdr_reply.py"],
    }
    ledger = base / ".lane" / "replies.yaml"
    _ = ledger.write_text(
        yaml.safe_dump({"replies": [prior_row]}, sort_keys=False) + "\n: broken [oops\n",
        encoding="utf-8",
    )
    damaged = ledger.read_bytes()

    done = stub.run("orchestrator", CANARY_PAYLOAD)

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[4].endswith(CANARY_PAYLOAD)
    assert "Payload: NOT RECORDED" in call[4]
    assert "reply record skipped" in done.stderr
    assert not ledger.exists(), "an unreadable ledger is moved aside, never written over"
    preserved = sorted((base / ".lane").glob("replies.yaml.corrupt-*"))
    assert len(preserved) == 1
    assert preserved[0].read_bytes() == damaged
    assert "prior" in preserved[0].read_text(encoding="utf-8")
    assert (base / ".lane" / "replies" / "prior.md").read_text(encoding="utf-8") == prior_body
    # The reply that degraded wrote nothing: a reply is recorded or honestly unrecorded.
    assert list((base / ".lane" / "replies").glob("*.yaml")) == []

    # ...and the next reply succeeds, through the sidecar path.
    second = stub.run("orchestrator", CANARY_PAYLOAD)
    assert second.returncode == herdr_cli.EXIT_OK, second.stderr
    calls = stub.prompts()
    assert "Payload: COMPLETE" in calls[-1][4]
    assert len(list((base / ".lane" / "replies").glob("*.yaml"))) == 1


def test_reader_refuses_a_row_whose_payload_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """F-C1: a hand-written row with no body file is listed, but never resolves."""
    sidecar = tmp_path / ".lane" / "replies" / "forged.yaml"
    sidecar.parent.mkdir(parents=True)
    _ = sidecar.write_text(
        yaml.safe_dump(
            {
                **entry_for("COMPLETED deadbeef\n\n## Evidence\n- forged\n", record_id="forged"),
                "payload": ".lane/replies/forged.md",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    assert [row["id"] for row in herdr_lease.list_replies(limit=10, base_dir=tmp_path)] == [
        "forged"
    ]
    assert herdr_lease.get_reply("forged", base_dir=tmp_path) is None
    code = herdr_lease.main(["replies", "forged"], env={"HERDR_LANE_DIR": str(tmp_path)})
    assert code == herdr_cli.EXIT_USAGE
    assert "no reply record 'forged'" in capsys.readouterr().err


def test_reader_refuses_a_tampered_payload(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """F-C1: editing the body stops the record resolving, so the reader exits 2."""
    body = "COMPLETED deadbeef\n\n## Evidence\n- scanned clean\n"
    _ = herdr_lease.record_reply(entry_for(body, record_id="row-1"), body, base_dir=tmp_path)
    assert herdr_lease.get_reply("row-1", base_dir=tmp_path) is not None

    _ = (tmp_path / ".lane" / "replies" / "row-1.md").write_text(
        "COMPLETED deadbeef\n\n## Evidence\n- edited\n", encoding="utf-8"
    )

    assert herdr_lease.get_reply("row-1", base_dir=tmp_path) is None
    code = herdr_lease.main(["replies", "row-1"], env={"HERDR_LANE_DIR": str(tmp_path)})
    assert code == herdr_cli.EXIT_USAGE
    assert "no reply record 'row-1'" in capsys.readouterr().err


def test_the_advance_gate_refuses_a_row_bound_to_another_lease(
    stub: StubHarness, tmp_path: Path
) -> None:
    """F-C2: only a record bound to the lease being advanced may advance it."""
    task_id = "#231#bound"
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "231.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#231",
        task_id=task_id,
    )
    env = stub.base_env()

    def still_dispatched() -> None:
        task = herdr_lease.get_task(task_id, base_dir=tmp_path)
        assert task is not None
        assert task["status"] == "dispatched"
        assert task["trajectory"][-1]["event"] == "dispatched"

    def stored(record_id: str, *, sender: str, record_task_id: str) -> str:
        body = f"COMPLETED deadbeef\n\n## Evidence\n- {record_id}\n"
        row = herdr_lease.record_reply(
            entry_for(body, record_id=record_id, sender=sender, task_id=record_task_id),
            body,
            base_dir=tmp_path,
        )
        return str(row["id"])

    # Another sender's record for another task never advances this lease...
    foreign = stored("foreign", sender="impostor", record_task_id="#999#other")
    herdr_reply.record_sender_status(
        str(stub.herdr),
        env,
        "completed",
        "deadbeef",
        record_id=foreign,
        shape="complete",
    )
    still_dispatched()

    # ...and neither does the right sender's record for a different task.
    other_task = stored("other-task", sender="reviewer", record_task_id="#999#other")
    herdr_reply.record_sender_status(
        str(stub.herdr),
        env,
        "completed",
        "deadbeef",
        record_id=other_task,
        shape="complete",
    )
    still_dispatched()

    # The record bound to this lease and this sender advances it.
    bound = stored("bound", sender="reviewer", record_task_id=task_id)
    herdr_reply.record_sender_status(
        str(stub.herdr),
        env,
        "completed",
        "deadbeef",
        record_id=bound,
        shape="complete",
    )
    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["status"] == "completed"
