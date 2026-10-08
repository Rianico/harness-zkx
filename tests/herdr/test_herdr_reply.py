"""Tests for skills/herdr/scripts/herdr_reply.py (herdr-reply helper).

Integration cases route through the shared stub `herdr`; payload assertions read back the
recorded argv, proving byte-for-byte delivery without caller context injection.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import herdr_cli
import herdr_prompt
import herdr_reply
import pytest

from tests.herdr.stub import DEFAULT_STATE, SCRIPTS_DIR, StubHarness

SCRIPT = SCRIPTS_DIR / "herdr_reply.py"

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
    "resume_cmd": "pi --resume sess.jsonl",
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
    done = stub.run("orchestrator", "COMPLETED deadbeef", env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["status"] == "completed"
    completed = [event for event in task["trajectory"] if event["event"] == "completed"]
    assert len(completed) == 1
    assert completed[-1]["sha"] == "deadbeef"
    assert completed[-1]["to_status"] == "completed"
    assert completed[-1]["note"] == "COMPLETED deadbeef"
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
    assert "Or resume manually in pane wM:p1N: pi --resume sess.jsonl" in done.stderr
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
        "resume_cmd": "pi --resume sess.jsonl",
        "cwd": "/repo",
    }
    assert herdr_reply.format_reply_recovery_diagnostic(
        "lens-orchestrator", recovery, "<reply>"
    ) == (
        "herdr-reply: target agent 'lens-orchestrator' in pane wM:p1N has exited.\n"
        "Suggested recovery:\n"
        "  1. Auto-revive & deliver: uv run ~/.agents/skills/herdr/scripts/herdr_reply.py "
        "lens-orchestrator --file <reply> --auto-start pi\n"
        "  2. Or resume manually in pane wM:p1N: pi --resume sess.jsonl"
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
