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
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import herdr_bootstrap
import herdr_cli
import herdr_lease
import herdr_prompt
import herdr_reply
import pytest
import yaml

from tests.git_env import GIT_LOCATION_VARS
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


def test_reply_refuses_a_payload_without_a_leading_status_line(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 D1.1: the body must start at its status line; anything else is refused.

    A first non-empty line that is not a status line used to be recorded anyway, as a row
    with `status: null` and `shape: n/a` that looks like a real reply. The precondition is
    enforced before any record exists, so the store stays untouched and nothing is delivered.
    """
    body = "## Summary\nthis body never starts at a status line\n"
    before = herdr_lease.list_replies(base_dir=tmp_path)

    done = stub.run("orchestrator", body)

    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "status line" in done.stderr
    assert "COMPLETED" in done.stderr and "BLOCKED" in done.stderr and "REJECTED" in done.stderr
    assert stub.prompts() == []
    # The store's record count is unchanged: this is not merely a non-zero exit.
    assert herdr_lease.list_replies(base_dir=tmp_path) == before == []


def test_a_refused_reply_keeps_the_lease_so_the_corrected_reply_advances(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 D1.1 combined pin: a refused first reply must not consume the lease.

    A status-less payload used to be RECORDED with `status: null`, `shape: n/a`; the send
    then released the sender's lease, so the corrected reply recorded its payload but had no
    lease to resolve `task_id` from and could never advance the task (the advance is guarded
    on `task_id` resolved from the lease). This exercises BOTH sends in one flow: a single
    well-formed reply passes today and proves nothing, so do not simplify this back to one
    send.
    """
    task_id = "#246#d11-advance"
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "246.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#246",
        task_id=task_id,
    )
    before = herdr_lease.list_replies(base_dir=tmp_path)

    malformed = "## Summary\nmalformed first reply that never starts at a status line\n"
    refused = stub.run("orchestrator", malformed, env={"PWD": str(tmp_path)})

    assert refused.returncode == herdr_cli.EXIT_USAGE
    assert "status line" in refused.stderr
    assert herdr_lease.list_replies(base_dir=tmp_path) == before
    assert herdr_lease.get_lease("reviewer", base_dir=tmp_path) is not None, (
        "the refusal must not consume the sender's lease"
    )

    corrected = "COMPLETED deadbeef\n\n## Evidence\n- 1078 passed\n"
    done = stub.run("orchestrator", corrected, env={"PWD": str(tmp_path)})
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    records = herdr_lease.list_replies(base_dir=tmp_path)
    assert len(records) == 1
    assert records[0]["task_id"] == task_id, "the corrected reply carries the lease's task linkage"
    assert records[0]["shape"] == "complete"

    task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert task is not None
    assert task["status"] == "completed"
    assert herdr_lease.get_lease("reviewer", base_dir=tmp_path) is None


def test_a_correction_for_a_lease_expired_ticket_binds_the_rendered_task(
    stub_factory: Callable[[Path], StubHarness], tmp_path: Path
) -> None:
    """#246 E1.2 positive: a correction after the lease is gone binds THE CORRECT task.

    Old role (D1.2 pin 1): the second reply re-bound through the sender's sole open task — the
    inference E1.2 deletes. New role: the dispatcher renders `--ticket <derived id>`; the first
    reply consumes the lease; the follow-up correction for the same ticket resends with that
    rendered `--ticket` value and must advance THAT task. No inference is involved, so no other
    open task can move. A dropped `--ticket` leaves the correction unlinked (see the key pin).
    """
    dispatch = stub_factory(SCRIPTS_DIR / "herdr_dispatch.py")
    reply = stub_factory(SCRIPTS_DIR / "herdr_reply.py")
    ticket = tmp_path / "246-e12-correction.md"
    _ = ticket.write_text("TICKET BODY", encoding="utf-8")

    dispatched = dispatch.run(
        "reviewer", "--file", str(ticket), "--no-wait", env={"PWD": str(tmp_path)}
    )
    assert dispatched.returncode == herdr_cli.EXIT_OK, dispatched.stderr
    (prompt,) = dispatch.prompts()
    rendered = re.search(r"--ticket (\S+)", prompt[4])
    assert rendered, prompt[4]
    rendered_ticket = rendered.group(1)
    task_id = rendered_ticket  # the dispatcher mirrors the task id onto the derived ticket id

    first = reply.run(
        "orchestrator", "BLOCKED waiting on human input\n", env={"PWD": str(tmp_path)}
    )
    assert first.returncode == herdr_cli.EXIT_OK, first.stderr
    assert herdr_lease.get_lease("reviewer", base_dir=tmp_path) is None, (
        "the first reply consumed the lease; only the rendered --ticket can bind the next"
    )
    first_task = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert first_task is not None and first_task["status"] == "blocked"

    corrected = reply.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 1 passed\n",
        "--ticket",
        rendered_ticket,
        env={"PWD": str(tmp_path)},
    )
    assert corrected.returncode == herdr_cli.EXIT_OK, corrected.stderr

    record = herdr_lease.list_replies(base_dir=tmp_path)[-1]
    assert record["task_id"] == rendered_ticket, "the rendered --ticket names the correct task"
    advanced = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert advanced is not None and advanced["status"] == "completed"
    assert [event for event in advanced["trajectory"] if event["event"] == "completed"], (
        "the correction must advance the correct task"
    )


def test_a_second_reply_with_an_ambiguous_ticket_is_recorded_unlinked_and_warns(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 D1.2 pin 2 (negative): an ambiguous ticket is never guessed at.

    The sender holds two open tasks for two tickets; the lease binds the first reply to the
    second ticket's task and is then released. The second reply could belong to either task or
    to a third ticket, so it must be recorded unlinked — never attributed to the first
    record's task — and exactly one warning line must say so. A blind "reuse the most recent
    record's task" passes pin 1 but fails here.
    """
    first_task = "#246#d12-amb-1"
    second_task = "#247#d12-amb-2"
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "246.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#246",
        task_id=first_task,
    )
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "247.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#247",
        task_id=second_task,
    )

    bound = stub.run("orchestrator", "BLOCKED waiting on human input\n", env={"PWD": str(tmp_path)})
    assert bound.returncode == herdr_cli.EXIT_OK, bound.stderr
    assert herdr_lease.list_replies(base_dir=tmp_path)[-1]["task_id"] == second_task

    ambiguous = stub.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 2 passed\n",
        env={"PWD": str(tmp_path)},
    )
    assert ambiguous.returncode == herdr_cli.EXIT_OK, ambiguous.stderr

    record = herdr_lease.list_replies(base_dir=tmp_path)[-1]
    assert record["task_id"] is None, "an ambiguous ticket is never attributed to a task"
    assert record["task_id"] != second_task, "not the first record's task either"
    assert "task linkage" in ambiguous.stderr, "one warning line says the linkage was not guessed"
    assert len([line for line in ambiguous.stderr.splitlines() if "task linkage" in line]) == 1
    first_state = herdr_lease.get_task(first_task, base_dir=tmp_path)
    second_state = herdr_lease.get_task(second_task, base_dir=tmp_path)
    assert first_state is not None and first_state["status"] == "dispatched"
    assert second_state is not None and second_state["status"] == "blocked"


def test_explicit_ticket_flag_binds_a_reply_the_lease_cannot(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 D1.2 primary mechanism: `--ticket` names the task when inference cannot.

    With two open tasks and no lease the ticket is ambiguous, so the reply binds to the named
    task only because the flag names it, and the other task is left untouched.
    """
    named = "#246#d12-flag"
    other = "#247#d12-flag"
    _ = herdr_lease.acquire_lease(
        "reviewer", "246.md", "orchestrator", base_dir=tmp_path, ticket_id="#246", task_id=named
    )
    _ = herdr_lease.acquire_lease(
        "reviewer", "247.md", "orchestrator", base_dir=tmp_path, ticket_id="#247", task_id=other
    )
    assert herdr_lease.release_lease("reviewer", base_dir=tmp_path) is True

    done = stub.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 3 passed\n",
        "--ticket",
        named,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    assert herdr_lease.list_replies(base_dir=tmp_path)[-1]["task_id"] == named
    named_state = herdr_lease.get_task(named, base_dir=tmp_path)
    other_state = herdr_lease.get_task(other, base_dir=tmp_path)
    assert named_state is not None and named_state["status"] == "completed"
    assert other_state is not None and other_state["status"] == "dispatched"


def test_explicit_ticket_flag_naming_a_foreign_task_is_unlinked_and_warns(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 D1.2 negative / D1.5 F2: an explicit name that is not the sender's open task never binds.

    The flag names another sender's task while this sender holds its own live lease; the
    reply is recorded unlinked with one warning, and neither task is advanced. The warning is
    the REFUSED severity — the flag named something the sender does not hold open — not the
    quiet "nothing to link" and not the "unreadable" wording.
    """
    foreign = "#999#d12-foreign"
    mine = "#246#d12-mine"
    _ = herdr_lease.acquire_lease(
        "someone-else",
        "999.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#999",
        task_id=foreign,
    )
    _ = herdr_lease.acquire_lease(
        "reviewer", "246.md", "orchestrator", base_dir=tmp_path, ticket_id="#246", task_id=mine
    )

    done = stub.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 4 passed\n",
        "--ticket",
        foreign,
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    assert herdr_lease.list_replies(base_dir=tmp_path)[-1]["task_id"] is None
    warnings = [line for line in done.stderr.splitlines() if "task linkage" in line]
    assert len(warnings) == 1, done.stderr
    assert herdr_reply.UNLINKED_REFUSED_MARKER in warnings[0], warnings[0]
    assert herdr_reply.UNLINKED_NOTHING_MARKER not in warnings[0], warnings[0]
    assert herdr_reply.UNLINKED_UNREADABLE_MARKER not in warnings[0], warnings[0]
    foreign_state = herdr_lease.get_task(foreign, base_dir=tmp_path)
    mine_state = herdr_lease.get_task(mine, base_dir=tmp_path)
    assert foreign_state is not None and foreign_state["status"] == "dispatched"
    assert mine_state is not None and mine_state["status"] == "dispatched"


def test_a_reply_using_the_rendered_contract_binds_with_no_lease(
    stub_factory: Callable[[Path], StubHarness], tmp_path: Path
) -> None:
    """#246 E1.1 pin 2: the RENDERED contract binds with no lease.

    This pin is what replaced the sole-open-task inference (deleted in E1.2) — do NOT
    "simplify" it back to a lease-only path. The dispatch renders the reply contract; the
    callee's first reply consumes the lease; the callee then resends using the exact `--ticket`
    value the rendered contract carried. Nothing else can bind the second reply, and it must
    advance THAT task. A dropped `--ticket` (mutant a) and a foreign id (mutant b, e.g. the
    sender's name) both fail here.
    """
    dispatch = stub_factory(SCRIPTS_DIR / "herdr_dispatch.py")
    reply = stub_factory(SCRIPTS_DIR / "herdr_reply.py")
    ticket = tmp_path / "182-herdr-msg-enhance.md"
    _ = ticket.write_text("TICKET BODY", encoding="utf-8")

    dispatched = dispatch.run(
        "reviewer", "--file", str(ticket), "--no-wait", env={"PWD": str(tmp_path)}
    )
    assert dispatched.returncode == herdr_cli.EXIT_OK, dispatched.stderr
    (prompt,) = dispatch.prompts()
    rendered = re.search(r"--ticket (\S+)", prompt[4])
    assert rendered, prompt[4]
    rendered_ticket = rendered.group(1)

    first = reply.run(
        "orchestrator", "BLOCKED waiting on human input\n", env={"PWD": str(tmp_path)}
    )
    assert first.returncode == herdr_cli.EXIT_OK, first.stderr
    assert herdr_lease.get_lease("reviewer", base_dir=tmp_path) is None, (
        "the first reply consumed the lease; only the rendered --ticket can bind the next"
    )

    second = reply.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 1 passed\n",
        "--ticket",
        rendered_ticket,
        env={"PWD": str(tmp_path)},
    )
    assert second.returncode == herdr_cli.EXIT_OK, second.stderr
    record = herdr_lease.list_replies(base_dir=tmp_path)[-1]
    assert record["task_id"] == rendered_ticket, "the rendered --ticket names the task to advance"
    task = herdr_lease.get_task(rendered_ticket, base_dir=tmp_path)
    assert task is not None and task["status"] == "completed"


def test_in_reply_to_record_rebinds_a_followup_without_restating_the_ticket(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 D1.2: `--in-reply-to <record-id>` resolves the named record's task linkage.

    Two open tasks make the ticket ambiguous, so only the explicit record reference can bind
    the follow-up; it re-binds to the very task the named record rode.
    """
    first_task = "#246#d12-alias-1"
    second_task = "#247#d12-alias-2"
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "246.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#246",
        task_id=first_task,
    )
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "247.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#247",
        task_id=second_task,
    )

    first = stub.run("orchestrator", "BLOCKED waiting on human input\n", env={"PWD": str(tmp_path)})
    assert first.returncode == herdr_cli.EXIT_OK, first.stderr
    record = herdr_lease.list_replies(base_dir=tmp_path)[-1]
    assert record["task_id"] == second_task

    done = stub.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 5 passed\n",
        "--in-reply-to",
        str(record["id"]),
        env={"PWD": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    assert herdr_lease.list_replies(base_dir=tmp_path)[-1]["task_id"] == second_task
    second_state = herdr_lease.get_task(second_task, base_dir=tmp_path)
    first_state = herdr_lease.get_task(first_task, base_dir=tmp_path)
    assert second_state is not None and second_state["status"] == "completed"
    assert first_state is not None and first_state["status"] == "dispatched"


def test_a_reply_whose_open_task_cannot_be_named_is_still_unlinked_and_never_guessed(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 E1.2 (rewritten D1.3 pin 1): a damaged task id changes nothing, and nothing is guessed.

    Old role: the sender's sole open task record had lost its string `task_id`, and the
    now-deleted sole-open-task branch answered a loud "holds open work" warning. With that
    branch gone there is no inference left to warn about: the single open task falls into the
    same count-based refusal as any other flagless reply, is recorded unlinked, and mutates
    nothing. The damaged id can never be bound while the reply names no ticket.

    Mutant killed: restore the `len(open_tasks) == 1` binding and the record carries the task id
    again (or the warning changes shape); the reply must stay unlinked.
    """
    task_id = "#246#d13-nameless"
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "246.md",
        "orchestrator",
        base_dir=tmp_path,
        ticket_id="#246",
        task_id=task_id,
    )
    assert herdr_lease.release_lease("reviewer", base_dir=tmp_path) is True
    tasks_file = herdr_lease.resolve_tasks_file(base_dir=tmp_path)
    tasks = yaml.safe_load(tasks_file.read_text(encoding="utf-8"))
    del tasks["tasks"][task_id]["task_id"]
    _ = tasks_file.write_text(yaml.safe_dump(tasks, sort_keys=False), encoding="utf-8")

    done = stub.run("orchestrator", "COMPLETED deadbeef\n\n## Evidence\n- 1 passed\n")
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    record = herdr_lease.list_replies(base_dir=tmp_path)[-1]
    assert record["task_id"] is None, "an unnameable task is never attributed by guesswork"
    warnings = [line for line in done.stderr.splitlines() if "task linkage" in line]
    assert len(warnings) == 1, done.stderr
    assert herdr_reply.UNLINKED_REFUSED_MARKER in warnings[0], warnings[0]
    assert "no open task" not in warnings[0], warnings[0]


def test_unlinked_warnings_distinguish_open_work_from_nothing_to_link(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 D1.3 pin 2 (severity): 'several open tasks' must not warn like 'no open task'.

    The sender resolves the same way in both runs (the stub's current pane), so only the
    open-work state differs. A sender holding several open tasks has work this step refuses to
    guess at, so its line must differ from — and be the louder of — a sender holding none.

    Mutant killed: make the ambiguous path emit the "holds no open task" text and this pin fails
    on the two lines being identical, on the loud marker, and on the quiet marker.
    """
    several = tmp_path / "several"
    none = tmp_path / "none"
    several.mkdir()
    none.mkdir()
    _ = herdr_lease.acquire_lease(
        "reviewer", "246.md", "orchestrator", base_dir=several, ticket_id="#246", task_id="#246#a"
    )
    _ = herdr_lease.acquire_lease(
        "reviewer", "247.md", "orchestrator", base_dir=several, ticket_id="#247", task_id="#247#b"
    )
    assert herdr_lease.release_lease("reviewer", base_dir=several) is True

    body = "COMPLETED deadbeef\n\n## Evidence\n- 2 passed\n"
    loud = stub.run("orchestrator", body, env={"HERDR_LANE_DIR": str(several)})
    quiet = stub.run("orchestrator", body, env={"HERDR_LANE_DIR": str(none)})
    assert loud.returncode == herdr_cli.EXIT_OK, loud.stderr
    assert quiet.returncode == herdr_cli.EXIT_OK, quiet.stderr

    loud_lines = [line for line in loud.stderr.splitlines() if "task linkage" in line]
    quiet_lines = [line for line in quiet.stderr.splitlines() if "task linkage" in line]
    assert len(loud_lines) == 1, loud.stderr
    assert len(quiet_lines) == 1, quiet.stderr
    assert loud_lines[0] != quiet_lines[0], "the two severities must not warn identically"
    assert herdr_reply.UNLINKED_REFUSED_MARKER in loud_lines[0], loud_lines[0]
    assert herdr_reply.UNLINKED_NOTHING_MARKER in quiet_lines[0], quiet_lines[0]
    assert herdr_reply.UNLINKED_NOTHING_MARKER not in loud_lines[0], loud_lines[0]
    assert herdr_reply.UNLINKED_REFUSED_MARKER not in quiet_lines[0], quiet_lines[0]
    assert loud_lines[0].endswith(herdr_reply.RECORDED_CLAUSE), loud_lines[0]
    assert quiet_lines[0].endswith(herdr_reply.RECORDED_CLAUSE), quiet_lines[0]
    assert "ambiguous" in loud_lines[0], loud_lines[0]
    assert "ambiguous" not in quiet_lines[0], quiet_lines[0]
    assert "no open task" in quiet_lines[0], quiet_lines[0]
    assert "no open task" not in loud_lines[0], loud_lines[0]
    assert herdr_lease.list_replies(base_dir=several)[-1]["task_id"] is None
    assert herdr_lease.list_replies(base_dir=none)[-1]["task_id"] is None


def test_resolve_task_linkage_never_returns_a_silent_answer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#246 D1.3 invariant: every unlinked answer carries a reason, so no silent path returns.

    These two branches fire when the lane anchor cannot be resolved, or when any `list_tasks`
    raise — a store this process cannot read — and never because store damage is swallowed:
    `_load_state` turns a damaged store into empty state, which produces the PLAIN "holds no
    open task" line instead. So the invariant is pinned at the resolver: both branches answer
    `(None, <reason>)`, never the reasonless `(None, None)` they used to.
    """
    task_id, warning = herdr_reply.resolve_task_linkage(
        sender=None, lease=None, explicit_ticket=None, in_reply_to_record=None, env={}
    )
    assert task_id is None
    assert warning is not None and "no sender resolved" in warning

    def _no_open_tasks(sender: str, env: Mapping[str, str]) -> None:
        """Stand in for a store this process cannot read: `_sender_open_tasks` returns None."""
        _ = sender, env

    monkeypatch.setattr(herdr_reply, "_sender_open_tasks", _no_open_tasks)
    task_id, warning = herdr_reply.resolve_task_linkage(
        sender="reviewer", lease=None, explicit_ticket=None, in_reply_to_record=None, env={}
    )
    assert task_id is None
    assert warning is not None and "could not be read" in warning


def test_unlinked_lines_never_claim_a_record_at_the_resolver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#246 D1.5 F1: the two store-dependent branches never claim a record in the resolver's text.

    The same branch records when the store resolves and records nothing when it does not, so the
    resolver cannot vouch for a record: the claim is appended by the caller only after a store
    answered. Both lines therefore carry the third severity marker and no record clause.

    Mutant killed: put "; recording the reply unlinked" back into `_unlinked` and both lines
    claim a record the resolver never saw written.
    """
    task_id, warning = herdr_reply.resolve_task_linkage(
        sender=None, lease=None, explicit_ticket=None, in_reply_to_record=None, env={}
    )
    assert task_id is None and warning is not None
    assert "no sender resolved" in warning, warning
    assert herdr_reply.UNLINKED_UNREADABLE_MARKER in warning, warning
    assert herdr_reply.RECORDED_CLAUSE not in warning, warning
    assert herdr_reply.NOT_RECORDED_CLAUSE not in warning, warning

    def _no_open_tasks(sender: str, env: Mapping[str, str]) -> None:
        """Stand in for a store this process cannot read: `_sender_open_tasks` returns None."""
        _ = sender, env

    monkeypatch.setattr(herdr_reply, "_sender_open_tasks", _no_open_tasks)
    task_id, warning = herdr_reply.resolve_task_linkage(
        sender="reviewer", lease=None, explicit_ticket=None, in_reply_to_record=None, env={}
    )
    assert task_id is None and warning is not None
    assert "could not be read" in warning, warning
    assert herdr_reply.UNLINKED_UNREADABLE_MARKER in warning, warning
    assert herdr_reply.RECORDED_CLAUSE not in warning, warning
    assert herdr_reply.NOT_RECORDED_CLAUSE not in warning, warning


def test_the_flag_path_markers_are_pinned_at_the_resolver(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """#246 D1.5 F2: every `_linkage_from_ticket`/`_linkage_from_record` outcome names its marker.

    The five refusal sites in those two functions and the "no sender resolved"/"could not be
    resolved" sites carried no marker assertion, so mutating `UNLINKED_REFUSED_MARKER` to
    `UNLINKED_NOTHING_MARKER` at all five left every pin green. The flag paths are exercised
    here at the resolver, where the end-to-end unreachable no-sender branch can still be named.
    """
    store = tmp_path / "store"
    store.mkdir()
    env = {"HERDR_LANE_DIR": str(store)}

    # No sender resolved: the flag paths answer with the unreadable severity, never a refusal.
    _, ticket_warning = herdr_reply._linkage_from_ticket("#246#any", sender=None, env=env)
    assert ticket_warning is not None
    assert herdr_reply.UNLINKED_UNREADABLE_MARKER in ticket_warning, ticket_warning
    _, record_warning = herdr_reply._linkage_from_record("some-record", sender=None, env=env)
    assert record_warning is not None
    assert herdr_reply.UNLINKED_UNREADABLE_MARKER in record_warning, record_warning

    # A `--ticket` name that matches no open task of the sender: refused.
    _, warning = herdr_reply._linkage_from_ticket("#246#no-such-task", sender="reviewer", env=env)
    assert warning is not None
    assert herdr_reply.UNLINKED_REFUSED_MARKER in warning, warning
    assert herdr_reply.UNLINKED_NOTHING_MARKER not in warning, warning

    # An `--in-reply-to` id the store does not hold: refused.
    _, warning = herdr_reply._linkage_from_record("no-such-record", sender="reviewer", env=env)
    assert warning is not None
    assert herdr_reply.UNLINKED_REFUSED_MARKER in warning, warning

    # An `--in-reply-to` record that carries no task linkage: refused.
    def _reply_no_linkage(
        record_id: str, *, env: Mapping[str, str] | None = None
    ) -> dict[str, Any]:
        _ = record_id, env
        return {"sender": "reviewer", "task_id": None}

    def _no_task(task_id: str, *, env: Mapping[str, str] | None = None) -> None:
        _ = task_id, env

    monkeypatch.setattr(herdr_reply, "get_reply", _reply_no_linkage)
    monkeypatch.setattr(herdr_reply, "get_task", _no_task)
    _, warning = herdr_reply._linkage_from_record("rec-a", sender="reviewer", env=env)
    assert warning is not None
    assert herdr_reply.UNLINKED_REFUSED_MARKER in warning, warning

    # An `--in-reply-to` record whose task is no longer open: refused.
    def _reply_closed(record_id: str, *, env: Mapping[str, str] | None = None) -> dict[str, Any]:
        _ = record_id, env
        return {"sender": "reviewer", "task_id": "#246#closed"}

    def _closed_task(task_id: str, *, env: Mapping[str, str] | None = None) -> dict[str, Any]:
        _ = task_id, env
        return {"assignee": "reviewer", "status": "completed"}

    monkeypatch.setattr(herdr_reply, "get_reply", _reply_closed)
    monkeypatch.setattr(herdr_reply, "get_task", _closed_task)
    _, warning = herdr_reply._linkage_from_record("rec-b", sender="reviewer", env=env)
    assert warning is not None
    assert herdr_reply.UNLINKED_REFUSED_MARKER in warning, warning

    # A store the flag path cannot read: the unreadable severity.
    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("store boom")

    monkeypatch.setattr(herdr_reply, "get_reply", _boom)
    _, warning = herdr_reply._linkage_from_record("rec-c", sender="reviewer", env=env)
    assert warning is not None
    assert herdr_reply.UNLINKED_UNREADABLE_MARKER in warning, warning

    monkeypatch.undo()
    monkeypatch.setattr(herdr_reply, "list_tasks", _boom)
    _, warning = herdr_reply._linkage_from_ticket("#246#any", sender="reviewer", env=env)
    assert warning is not None
    assert herdr_reply.UNLINKED_UNREADABLE_MARKER in warning, warning


def test_a_missing_lane_anchor_warns_once_and_never_claims_a_record(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 D1.5 F1/F2: with no lane anchor the warning names the real outcome, and no record.

    `resolve_base_dir` raises `LaneAnchorError` before the store is read or written, so the
    run records nothing and the delivered prompt carries the `NOT RECORDED` pointer. The
    warning used to end with "; recording the reply unlinked" anyway — one run, two
    contradictory statements about what happened. The record claim is caller-side now.

    Mutant killed: append the recording clause inside `_unlinked` again and this pin fails on
    the warning claiming a record the pointer delivered in the same run says was not written.
    """
    nongit = tmp_path / "nongit"
    nongit.mkdir()
    done = stub.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 1 passed\n",
        env={"HERDR_LANE_DIR": None},
        cwd=nongit,
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    warnings = [line for line in done.stderr.splitlines() if "task linkage" in line]
    assert len(warnings) == 1, done.stderr
    assert "could not be read" in warnings[0], warnings[0]
    assert herdr_reply.UNLINKED_UNREADABLE_MARKER in warnings[0], warnings[0]
    assert herdr_reply.RECORDED_CLAUSE not in warnings[0], warnings[0]
    assert warnings[0].endswith(herdr_reply.NOT_RECORDED_CLAUSE), warnings[0]
    assert len([line for line in done.stderr.splitlines() if "could not be read" in line]) == 1

    (call,) = stub.prompts()
    assert "Payload: NOT RECORDED" in call[4], call[4]
    assert not (nongit / ".lane").exists(), "no store was written: the anchor never resolved"


def test_a_flagless_reply_with_one_open_task_is_unlinked_and_mutates_nothing(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 E1.2 KEY pin: a sole open task is NO LONGER a ticket signal.

    INCIDENT (do not "restore" this convenience later): a guard that guesses mutated the wrong
    row. An addendum reply about `#246` arrived flagless while the sender held exactly one open
    task, `#247#probe-unrelated`; the sole-open-task inference bound the addendum to that row and
    flipped it `dispatched -> completed`. The ticket signal is no longer missing — the rendered
    dispatch contract carries `--ticket` (E1.1) — so a reply that names no ticket is recorded
    UNLINKED and mutates no task. A guard that is told does not guess.

    Mutant killed: restore the `len(open_tasks) == 1` binding and the record carries the task id
    again and the task advances to `completed`.
    """
    task_id = "#246#e12-sole"
    _ = herdr_lease.acquire_lease(
        "reviewer", "246.md", "orchestrator", base_dir=tmp_path, ticket_id="#246", task_id=task_id
    )
    assert herdr_lease.release_lease("reviewer", base_dir=tmp_path) is True, (
        "no lease: nothing may bind this reply"
    )
    before = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert before is not None and before["status"] == "dispatched"

    done = stub.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 1 passed\n",
        env={"HERDR_LANE_DIR": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    record = herdr_lease.list_replies(base_dir=tmp_path)[-1]
    assert record["task_id"] is None, "a flagless reply is recorded unlinked, never guessed"
    warnings = [line for line in done.stderr.splitlines() if "task linkage" in line]
    assert len(warnings) == 1, done.stderr
    assert herdr_reply.UNLINKED_REFUSED_MARKER in warnings[0], warnings[0]
    after = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert after is not None and after["status"] == "dispatched", "no task may move"
    assert not [event for event in after["trajectory"] if event["event"] == "completed"], (
        "the flagless reply must not append a completed event to any task"
    )


def test_a_reply_about_another_ticket_never_flips_the_unrelated_open_task(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 E1.2 incident reconstruction: the flagless addendum no longer flips the wrong row.

    Old role (D1.4 pin 2 / PROBE1): the sender held exactly one open task while its payload was
    about another ticket, and the sole-open-task inference bound the foreign reply to that row.
    New role: reconstruct the live incident — the sender held exactly one open task,
    `#247#probe-unrelated` (`dispatched`), when an addendum about ticket `#246` arrived with no
    ticket flag. The inference flipped `#247#probe-unrelated` `dispatched -> completed`. Now the
    flagless reply is recorded UNLINKED with its reason and NO task changes status.

    Mutant killed: restore the inference and this reply re-binds to `#247#probe-unrelated`, whose
    status flips, failing both assertions below.
    """
    task_id = "#247#probe-unrelated"
    _ = herdr_lease.acquire_lease(
        "reviewer", "247.md", "orchestrator", base_dir=tmp_path, ticket_id="#247", task_id=task_id
    )
    assert herdr_lease.release_lease("reviewer", base_dir=tmp_path) is True
    open_before = [
        task["task_id"]
        for task in herdr_lease.list_tasks(base_dir=tmp_path)
        if task.get("assignee") == "reviewer" and task.get("status") != "completed"
    ]
    assert open_before == [task_id], "the sender must hold exactly one open task"

    done = stub.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- addendum for #246\n",
        env={"HERDR_LANE_DIR": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    record = herdr_lease.list_replies(base_dir=tmp_path)[-1]
    assert record["task_id"] is None, "the flagless reply is unlinked, not bound to the wrong row"
    warnings = [line for line in done.stderr.splitlines() if "task linkage" in line]
    assert len(warnings) == 1, done.stderr
    assert herdr_reply.UNLINKED_REFUSED_MARKER in warnings[0], warnings[0]
    after = herdr_lease.get_task(task_id, base_dir=tmp_path)
    assert after is not None and after["status"] == "dispatched", (
        "#247#probe-unrelated must not have been flipped"
    )
    assert not [event for event in after["trajectory"] if event["event"] == "completed"], (
        "no completed event may be appended to the unrelated task"
    )


def test_explicit_linkage_bindings_stay_silent(stub: StubHarness, tmp_path: Path) -> None:
    """#246 (rewritten D1.4 pin 3): a flag is the caller's instruction, so it never warns.

    Old role: proved the explicit paths stayed quiet while the sole-open-task inference used to
    warn. New role: the same negative with the inference gone — a flagless reply is the loud
    case now, so a quiet stderr here can only come from the explicit binding winning first. The
    `--in-reply-to` run names a stored record whose task is still open (a BLOCKED first reply
    leaves the round running).

    Mutant killed: make the explicit paths warn and both runs report a linkage line.

    F7: the negative is scoped to linkage lines rather than a bare empty stderr, because other
    legitimate writers exist on that stream (`--verbose`'s recovery diagnostic, the lease-trouble
    line); a future benign line must not force the honest silence assertion to be deleted.
    """
    flag_task = "#246#d14-explicit-flag"
    _ = herdr_lease.acquire_lease(
        "reviewer", "246.md", "orchestrator", base_dir=tmp_path, ticket_id="#246", task_id=flag_task
    )
    assert herdr_lease.release_lease("reviewer", base_dir=tmp_path) is True

    flagged = stub.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 1 passed\n",
        "--ticket",
        flag_task,
        env={"HERDR_LANE_DIR": str(tmp_path)},
    )
    assert flagged.returncode == herdr_cli.EXIT_OK, flagged.stderr
    assert herdr_lease.list_replies(base_dir=tmp_path)[-1]["task_id"] == flag_task
    assert [line for line in flagged.stderr.splitlines() if "task linkage" in line] == [], (
        flagged.stderr
    )

    record_store = tmp_path / "reply-to"
    record_store.mkdir()
    record_task = "#246#d14-explicit-record"
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "246.md",
        "orchestrator",
        base_dir=record_store,
        ticket_id="#246",
        task_id=record_task,
    )
    assert herdr_lease.release_lease("reviewer", base_dir=record_store) is True
    first = stub.run(
        "orchestrator",
        "BLOCKED waiting on the explicit reference\n",
        "--ticket",
        record_task,
        env={"HERDR_LANE_DIR": str(record_store)},
    )
    assert first.returncode == herdr_cli.EXIT_OK, first.stderr
    record_id = herdr_lease.list_replies(base_dir=record_store)[-1]["id"]

    rebound = stub.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 1 passed\n",
        "--in-reply-to",
        str(record_id),
        env={"HERDR_LANE_DIR": str(record_store)},
    )
    assert rebound.returncode == herdr_cli.EXIT_OK, rebound.stderr
    assert herdr_lease.list_replies(base_dir=record_store)[-1]["task_id"] == record_task
    assert [line for line in rebound.stderr.splitlines() if "task linkage" in line] == [], (
        rebound.stderr
    )


def test_the_open_and_terminal_status_partition_covers_every_canonical_status() -> None:
    """#246 D1.4 F2: the partition is explicit, so no canonical status defaults to open.

    `_is_open_task` decides which tasks count as the sender's open work for the linkage. While it
    hardcoded the singleton {"completed"}, any status added later would silently count as open.
    The partition is now enumerated and pinned total and disjoint against the store's
    `CANONICAL_STATUSES`, so a new status forces a decision instead of defaulting.
    """
    open_statuses = herdr_reply.OPEN_TASK_STATUSES
    terminal_statuses = herdr_reply.TERMINAL_TASK_STATUSES
    assert open_statuses | terminal_statuses == frozenset(herdr_lease.CANONICAL_STATUSES)
    assert open_statuses.isdisjoint(terminal_statuses)
    assert terminal_statuses == frozenset({"completed"})
    for status in herdr_lease.CANONICAL_STATUSES:
        assert herdr_reply._is_open_task({"status": status}) is (status in open_statuses), status
    assert [status for status in herdr_lease.CANONICAL_STATUSES if status not in open_statuses] == [
        "completed"
    ]


def test_a_corrupt_store_reads_as_unreadable_not_as_a_missing_open_task(
    stub: StubHarness, tmp_path: Path
) -> None:
    """#246 D1.4 F3: a corrupt store must not be reported as "the sender holds no open task".

    `herdr_lease._load_state` swallows corruption and returns empty state, so the unreadable
    branch never fired and a damaged store produced the quiet "holds no open task" line — the
    wrong claim, since the store may hold open work nobody could read. The file below is
    unparseable, so the reply is still recorded unlinked (fail-closed) but says so accurately.
    """
    task_id = "#246#d14-corrupt"
    _ = herdr_lease.acquire_lease(
        "reviewer", "246.md", "orchestrator", base_dir=tmp_path, ticket_id="#246", task_id=task_id
    )
    tasks_file = herdr_lease.resolve_tasks_file(base_dir=tmp_path)
    _ = tasks_file.write_text("{ corrupt: [unterminated\n", encoding="utf-8")

    done = stub.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 1 passed\n",
        env={"HERDR_LANE_DIR": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr

    assert herdr_lease.list_replies(base_dir=tmp_path)[-1]["task_id"] is None
    warnings = [line for line in done.stderr.splitlines() if "task linkage" in line]
    assert len(warnings) == 1, done.stderr
    assert "could not be read" in warnings[0], warnings[0]
    assert "no open task" not in warnings[0], warnings[0]
    assert herdr_reply.UNLINKED_UNREADABLE_MARKER in warnings[0], warnings[0]
    assert warnings[0].endswith(herdr_reply.RECORDED_CLAUSE), warnings[0]


@pytest.mark.parametrize(
    "tasks_yaml",
    [
        "tasks:\n  - task_id: '#246#d15r-broken'\n    assignee: reviewer\n    status: dispatched\n",
        "tasks:\n  t1: not-a-mapping\n",
    ],
)
def test_a_broken_inner_store_shape_reads_as_unreadable_not_as_no_open_task(
    stub: StubHarness, tmp_path: Path, tasks_yaml: str
) -> None:
    """#246 D1.5 F5: a store whose top level parses but whose rows do not reads as unreadable.

    `state_is_readable` used to check only the top level, so `tasks:` written as a sequence (or
    a task value that is not a mapping) parsed as a dict and read as readable-as-empty while
    `_load_state` silently dropped every row. The reply then claimed the sender held no open
    task while the file named one. The probe now requires the shape `_load_state` consumes, so
    the warning says the store could not be read instead — one level deeper than D1.4/F3.
    """
    task_id = "#246#d15r-broken"
    _ = herdr_lease.acquire_lease(
        "reviewer", "246.md", "orchestrator", base_dir=tmp_path, ticket_id="#246", task_id=task_id
    )
    tasks_file = herdr_lease.resolve_tasks_file(base_dir=tmp_path)
    _ = tasks_file.write_text("active_leases: {}\n" + tasks_yaml, encoding="utf-8")

    done = stub.run(
        "orchestrator",
        "COMPLETED deadbeef\n\n## Evidence\n- 1 passed\n",
        env={"HERDR_LANE_DIR": str(tmp_path)},
    )
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert herdr_lease.list_replies(base_dir=tmp_path)[-1]["task_id"] is None
    warnings = [line for line in done.stderr.splitlines() if "task linkage" in line]
    assert len(warnings) == 1, done.stderr
    assert herdr_reply.UNLINKED_UNREADABLE_MARKER in warnings[0], warnings[0]
    assert "holds no open task" not in warnings[0], warnings[0]


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
        f'uv run "{herdr_reply.REPLY_HELPER}" lens-orchestrator --file <reply> --auto-start pi'
    ) in done.stderr
    assert "~/.agents" not in done.stderr
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
    # A recovery command is executable and lane-local: it resolves this module's own helper, never
    # the `~/.agents` symlink, which can point into another worktree whose code is older.
    assert herdr_reply.REPLY_HELPER.is_absolute()
    assert herdr_reply.REPLY_HELPER.name == "herdr_reply.py"
    assert herdr_reply.REPLY_HELPER == SCRIPT

    recovery = {
        "pane_id": "wM:p1N",
        "kind": "pi",
        "resume_cmd": "pi --session sess.jsonl",
        "cwd": "/repo",
    }
    rendered = herdr_reply.format_reply_recovery_diagnostic(
        "lens-orchestrator", recovery, "<reply>"
    )
    assert rendered == (
        "herdr-reply: target agent 'lens-orchestrator' in pane wM:p1N has exited.\n"
        "Suggested recovery:\n"
        f'  1. Auto-revive & deliver: uv run "{herdr_reply.REPLY_HELPER}" '
        "lens-orchestrator --file <reply> --auto-start pi\n"
        "  2. Or resume manually in pane wM:p1N: pi --session sess.jsonl"
    )
    assert "~/.agents" not in rendered
    # Line 2 is omitted when no resume command is known.
    without_resume = herdr_reply.format_reply_recovery_diagnostic(
        "callee", {"pane_id": "w1:p1", "kind": "claude"}, "reply.md"
    )
    assert without_resume == (
        "herdr-reply: target agent 'callee' in pane w1:p1 has exited.\n"
        "Suggested recovery:\n"
        f'  1. Auto-revive & deliver: uv run "{herdr_reply.REPLY_HELPER}" '
        "callee --file reply.md --auto-start claude"
    )
    assert "~/.agents" not in without_resume


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


@pytest.mark.parametrize(
    "bold_line",
    ["**Status:** COMPLETED. Commit `abc1234`.", "**Status:**"],
)
def test_lane_reply_shape_records_the_evidence_section(tmp_path: Path, bold_line: str) -> None:
    """F5: the lane's own reply shape records `evidence: evidence`, not `status`.

    A bold `**Status:**` line sits between the status line and the canonical `## Evidence`
    section, whose body is a fenced block. The bold status line matches evidence vocabulary
    (stem `status`) and carries an inline tail, so it is recorded as class 2 before the
    class-1 `## Evidence` heading is ever seen; the fence under that heading must not discard
    the pending canonical heading, or document order alone would hand the label to `status`.

    Driven through the store the way the helper does — `build_reply_entry`, then
    `persist_reply` — and re-read with `get_reply`, so the pinned label is the one the reader
    returns, not just what `evidence_section` reports in isolation.
    """
    payload = f"COMPLETED abc1234\n\n{bold_line}\n\n## Evidence\n\n```\n660 passed\n```\n"
    assert herdr_reply.payload_shape(payload) == ("complete", "Evidence")

    mapped, sha, _line = herdr_reply.parse_status_line(payload)
    shape, heading = herdr_reply.payload_shape(payload)
    entry = herdr_reply.build_reply_entry(
        payload,
        sender="reviewer",
        caller="orchestrator",
        ticket_id="#231",
        task_id="#231#lane-reply",
        in_reply_to="#231#lane-reply",
        mapped=mapped,
        sha=sha,
        shape=shape,
        evidence=heading,
    )
    env = {"HERDR_LANE_DIR": str(tmp_path)}
    stored, reason = herdr_reply.persist_reply(entry, payload, env=env)
    assert reason is None
    assert stored is not None
    assert stored["shape"] == "complete"
    assert stored["evidence"] == "evidence"

    resolved = herdr_lease.get_reply(str(stored["id"]), base_dir=tmp_path)
    assert resolved is not None
    assert resolved["evidence"] == "evidence"


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


# ── #238: settle the revived caller before delivering the reply ─────────────────────


def _shell_pane_state() -> dict[str, object]:
    """A bare shell pane carrying the label the reply target resolves by."""
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


def test_auto_start_settles_the_revived_caller_and_zero_is_exact(
    stub: StubHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pin 2 (#238, revive path): the caller settles after its spawn, before delivery.

    Mutant killed (order): move `settle_fresh_pane(options.settle)` after the delivery — the
    `fake_sleep` probe then sees the prompt already logged and its assertion fails (#237).
    Mutant killed (exactness): drop the `seconds <= 0` guard in `settle_fresh_pane` — the
    `--settle 0` run records a `0.0` sleep and the `slept == []` assertion fails.
    """
    slept: list[float] = []

    def fake_sleep(seconds: float) -> None:
        assert stub.prompts() == [], "the revive must settle before the reply is delivered"
        slept.append(seconds)

    monkeypatch.setattr(herdr_bootstrap, "_sleep", fake_sleep)
    state = _shell_pane_state()

    done = stub.run("lens-orchestrator", "COMPLETED", "--auto-start", "pi", state=state)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert len(stub.starts()) == 1
    assert slept == [herdr_bootstrap.DEFAULT_SETTLE_SECONDS]

    slept.clear()
    zero = stub.run(
        "lens-orchestrator", "COMPLETED", "--auto-start", "pi", "--settle", "0", state=state
    )
    assert zero.returncode == herdr_cli.EXIT_OK, zero.stderr
    assert slept == [], "--settle 0 must not sleep at all on the revive path"


def test_revive_refuses_a_negative_settle(
    stub: StubHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F3 (#238): a negative `--settle` is refused on the revive path; no spawn, no sleep.

    RED on base: `--settle -3` exits 0, spawns the caller, and never sleeps.
    Mutant killed: drop the `settle < 0` refusal — the run spawns and exits 0.
    """
    slept: list[float] = []
    monkeypatch.setattr(herdr_bootstrap, "_sleep", slept.append)

    done = stub.run(
        "lens-orchestrator",
        "COMPLETED",
        "--auto-start",
        "pi",
        "--settle",
        "-3",
        state=_shell_pane_state(),
    )

    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert "must not be negative" in done.stderr
    assert stub.starts() == []
    assert slept == []


def test_auto_start_dry_run_shows_the_planned_settle_and_never_sleeps(
    stub: StubHarness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A revive dry run plans the settle in its JSON and sleeps not at all."""
    slept: list[float] = []
    monkeypatch.setattr(herdr_bootstrap, "_sleep", slept.append)

    done = stub.run(
        "lens-orchestrator",
        "COMPLETED",
        "--auto-start",
        "pi",
        "--dry-run",
        state=_shell_pane_state(),
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    plan = json.loads(done.stdout)
    assert plan["settle"] == herdr_bootstrap.DEFAULT_SETTLE_SECONDS
    assert plan["agent_start"][1:3] == ["agent", "start"]
    assert plan["agent_prompt"][1:3] == ["agent", "prompt"]
    assert slept == []
    assert stub.starts() == []
    assert stub.prompts() == []


# ── an outbound payload may not cite a SHA that resolves to nothing (#245 D2) ─────────

# The measured pair from the defect: `8d9fa742` is a real abbreviated commit in this lane,
# `8d9a742` is its one-hex-digit drift — seven characters, and no git object at all.
RESOLVING_ABBREV = "8d9fa742"
DRIFTED_ABBREV = "8d9a742"


def reply_payload(evidence_line: str = "- 660 passed") -> str:
    """A COMPLETED payload that cites evidence, so the shape check never decides these cases."""
    return f"COMPLETED\n\n## Evidence\n\n```\n{evidence_line}\n```\n"


def sha_guard_repo(root: Path, name: str = "sha-guard-repo") -> tuple[Path, str]:
    """A scratch git repository with one commit; returns (repo, abbreviated commit SHA).

    The scratch repo is the lane anchor the guard resolves against, so the pins exercise the
    real `git rev-parse --verify <token>^{commit}` probe instead of a stub of it. `name` seats a
    second, unrelated repository under the same root for the cwd-versus-anchor pins, and the
    commit message carries `name`, so the two repos have different commit SHAs: an empty commit
    with one message gives both repos the same SHA, which would make "a token that resolves only
    in the other repository" untestable.
    """
    repo = root / name
    repo.mkdir()

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
        )

    assert git("init", "-q", "-b", "main").returncode == 0
    committed = git(
        "-c",
        "user.name=herdr",
        "-c",
        "user.email=herdr@example.invalid",
        "commit",
        "-q",
        "--allow-empty",
        "-m",
        f"one for {name}",
    )
    assert committed.returncode == 0, committed.stderr
    short = git("rev-parse", "--short=8", "HEAD")
    assert short.returncode == 0, short.stderr
    return repo, short.stdout.strip()


def test_the_sha_guard_reads_only_a_whole_backticked_hex_code_span() -> None:
    """The chosen rule, pinned by shape: a backticked code span of 7-40 lowercase hex.

    A bare hex word is prose — the measurement found 37 distinct non-resolving bare tokens in
    today's tree (mutant labels, review ids, UUID fragments inside cited paths), so reading those
    as instructions would refuse innocent payloads. `?`-prefixed, uppercase, too short, and
    too long spans are not SHA-shaped at all.
    """
    assert herdr_reply.backticked_sha_tokens("COMPLETED deadbeef") == []
    assert herdr_reply.backticked_sha_tokens("COMPLETED `deadbeef`") == ["deadbeef"]
    assert herdr_reply.backticked_sha_tokens("`deadbeef` then `deadbeef`") == ["deadbeef"]
    assert herdr_reply.backticked_sha_tokens("`8d9a74`") == []
    assert herdr_reply.backticked_sha_tokens("`DEADBEEF`") == []
    assert herdr_reply.backticked_sha_tokens("`?8d9a742`") == []
    assert herdr_reply.backticked_sha_tokens("`" + "a" * 41 + "`") == []
    assert herdr_reply.backticked_sha_tokens("`" + "a" * 40 + "`") == ["a" * 40]


def test_the_drifted_abbreviation_names_no_commit_and_the_real_one_does() -> None:
    """Pins 1 and 2 at the rule: the guard's verdict on the measured pair, in this lane."""
    assert herdr_reply.unresolvable_sha_tokens(f"`{RESOLVING_ABBREV}`", cwd=REPO_ROOT) == []
    assert herdr_reply.unresolvable_sha_tokens(f"`{DRIFTED_ABBREV}`", cwd=REPO_ROOT) == [
        DRIFTED_ABBREV
    ]
    assert herdr_reply.unresolvable_sha_tokens("COMPLETED 8d9a742", cwd=REPO_ROOT) == []
    assert herdr_reply.unresolvable_sha_tokens("COMPLETED", cwd=REPO_ROOT) == []


def test_an_unresolvable_sha_is_refused_before_any_record_or_lease_change(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Pin 1: a payload naming the drifted token is refused, naming token and payload path.

    Refused before the store is touched, so a refused payload consumes nothing: no reply record,
    no prompt, and the sender's lease is still held for the corrected reply.
    """
    repo, _short = sha_guard_repo(tmp_path)
    _ = herdr_lease.acquire_lease(
        "reviewer",
        "238-R4-bridge-neutral-pin.md",
        "orchestrator",
        base_dir=repo,
        ticket_id="#238-R4",
        task_id="#238-R4#pin",
    )
    body = reply_payload(f"- base `{DRIFTED_ABBREV}`")
    path = tmp_path / "reply.md"
    _ = path.write_text(body, encoding="utf-8")

    done = stub.run(
        "orchestrator", "--file", str(path), env={"HERDR_LANE_DIR": str(repo)}, cwd=repo
    )

    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert DRIFTED_ABBREV in done.stderr
    assert str(path) in done.stderr
    assert stub.prompts() == []
    assert herdr_lease.list_replies(base_dir=repo) == []
    assert herdr_lease.get_lease("reviewer", base_dir=repo) is not None

    message_origin = stub.run("orchestrator", body, env={"HERDR_LANE_DIR": str(repo)}, cwd=repo)
    assert message_origin.returncode == herdr_cli.EXIT_USAGE
    assert "<message>" in message_origin.stderr


def test_a_payload_naming_a_resolving_abbreviated_sha_is_delivered(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Pin 2: a real abbreviated commit passes and the body is delivered verbatim."""
    repo, short = sha_guard_repo(tmp_path)
    body = reply_payload(f"- base `{short}`")
    path = tmp_path / "reply.md"
    _ = path.write_text(body, encoding="utf-8")

    done = stub.run(
        "orchestrator", "--file", str(path), env={"HERDR_LANE_DIR": str(repo)}, cwd=repo
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[4].endswith(body)


def test_a_payload_with_no_sha_shaped_token_passes_even_in_a_repository(
    stub: StubHarness, tmp_path: Path
) -> None:
    """Pin 2, second half: nothing to verify, and a bare hex word is not an instruction."""
    repo, _short = sha_guard_repo(tmp_path)
    bodies = (reply_payload(), reply_payload("- the mutant died; bare deadbeef in prose"))
    for body in bodies:
        done = stub.run("orchestrator", body, env={"HERDR_LANE_DIR": str(repo)}, cwd=repo)
        assert done.returncode == herdr_cli.EXIT_OK, (body, done.stderr)


def test_a_dry_run_reports_an_unresolvable_sha_instead_of_accepting_it_silently(
    stub: StubHarness, tmp_path: Path
) -> None:
    """A draft that names an unresolvable SHA is reported by the same guard, not skipped.

    `--dry-run` submits nothing, but it is not a bypass: the refusal happens before the plan is
    printed, and a resolving token still prints the planned argv.
    """
    repo, short = sha_guard_repo(tmp_path)
    refused = stub.run(
        "orchestrator",
        reply_payload(f"- base `{DRIFTED_ABBREV}`"),
        "--dry-run",
        env={"HERDR_LANE_DIR": str(repo)},
        cwd=repo,
    )
    assert refused.returncode == herdr_cli.EXIT_USAGE, refused.stdout
    assert DRIFTED_ABBREV in refused.stderr
    assert refused.stdout == ""
    assert stub.prompts() == []

    planned = stub.run(
        "orchestrator",
        reply_payload(f"- base `{short}`"),
        "--dry-run",
        env={"HERDR_LANE_DIR": str(repo)},
        cwd=repo,
    )
    assert planned.returncode == herdr_cli.EXIT_OK, planned.stderr
    assert json.loads(planned.stdout)[1:3] == ["agent", "prompt"]


@pytest.mark.parametrize("waived_token", [DRIFTED_ABBREV, "bb8e69bf1bef"])
def test_the_documented_waiver_admits_an_intentional_nonresolving_token(
    stub: StubHarness, tmp_path: Path, waived_token: str
) -> None:
    """The escape hatch, on the two measured false-positive classes.

    The drifted commit abbreviation is one; the other is the payload shape the scan found in
    today's tree — a backticked mutant or review-record id, which no shape rule can tell apart
    from a commit abbreviation. Both are delivered once the token is named, and the waiver is
    reported on stderr rather than silently.
    """
    repo, _short = sha_guard_repo(tmp_path)
    body = reply_payload(f"- the wrapper's drifted `{waived_token}`, quoted deliberately")
    path = tmp_path / "reply.md"
    _ = path.write_text(body, encoding="utf-8")

    done = stub.run(
        "orchestrator",
        "--file",
        str(path),
        herdr_reply.ALLOW_UNRESOLVABLE_SHA,
        waived_token,
        env={"HERDR_LANE_DIR": str(repo)},
        cwd=repo,
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "waived" in done.stderr
    assert waived_token in done.stderr
    (call,) = stub.prompts()
    assert call[4].endswith(body)


def test_the_sha_guard_says_so_when_git_cannot_answer(stub: StubHarness, tmp_path: Path) -> None:
    """Unverifiable is never unresolvable: outside a work tree the guard skips loudly."""
    nongit = tmp_path / "nongit"
    nongit.mkdir()

    done = stub.run(
        "orchestrator",
        reply_payload(f"- base `{DRIFTED_ABBREV}`"),
        env={"HERDR_LANE_DIR": str(nongit), "PWD": str(nongit)},
        cwd=nongit,
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "SHA guard skipped" in done.stderr
    assert DRIFTED_ABBREV in done.stderr
    assert len(stub.prompts()) == 1


def test_the_sha_guard_resolves_against_the_lane_anchor_not_the_working_directory(
    stub: StubHarness, tmp_path: Path
) -> None:
    """F2: the guard answers about the lane anchor, so the ambient cwd cannot change the verdict.

    `lane_git_dir` is the store anchor (#229), never `Path.cwd()`: run from a directory where git
    answers differently and the drifted token is still refused, while the anchor's own commit
    still resolves. Resolving against the cwd instead would skip the check here — the cwd is
    outside every repository, so `git_can_resolve_commits` answers False and the mutant delivers
    the dead token with a skip line.
    """
    repo, short = sha_guard_repo(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    assert herdr_reply.git_can_resolve_commits(repo) is True
    assert herdr_reply.git_can_resolve_commits(elsewhere) is False

    drifted = stub.run(
        "orchestrator",
        reply_payload(f"- base `{DRIFTED_ABBREV}`"),
        env={"HERDR_LANE_DIR": str(repo)},
        cwd=elsewhere,
    )
    assert drifted.returncode == herdr_cli.EXIT_USAGE, (drifted.stdout, drifted.stderr)
    assert DRIFTED_ABBREV in drifted.stderr
    assert "SHA guard skipped" not in drifted.stderr
    assert stub.prompts() == []

    delivered = stub.run(
        "orchestrator",
        reply_payload(f"- base `{short}`"),
        env={"HERDR_LANE_DIR": str(repo)},
        cwd=elsewhere,
    )
    assert delivered.returncode == herdr_cli.EXIT_OK, delivered.stderr
    assert len(stub.prompts()) == 1


def test_the_sha_guard_still_refuses_when_git_location_is_not_redirected(
    stub: StubHarness, tmp_path: Path
) -> None:
    """F3, the other direction: with no location override the refusal still fires."""
    repo, _short = sha_guard_repo(tmp_path)

    done = stub.run(
        "orchestrator",
        reply_payload(f"- base `{DRIFTED_ABBREV}`"),
        env={"HERDR_LANE_DIR": str(repo)},
        cwd=repo,
    )

    assert done.returncode == herdr_cli.EXIT_USAGE, (done.stdout, done.stderr)
    assert DRIFTED_ABBREV in done.stderr
    assert "SHA guard skipped" not in done.stderr
    assert stub.prompts() == []


# ── #245 D2-rework-2: which git overrides actually move the object store ───────────────

# The four names whose presence relocates the objects `git rev-parse` reads, so the guard's verdict
# would be about another repository. A literal, never read from the module under test: a name
# dropped from the tuple must fail a pin, not vanish from the parametrisation.
OBJECT_STORE_REDIRECT_VARS: tuple[str, ...] = (
    "GIT_DIR",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
)
# git's location overrides that leave the probe's verdict unchanged: they move the index or the
# work tree, which decide `git status`, never which commit a SHA names.
VERDICT_NEUTRAL_REDIRECT_VARS: tuple[str, ...] = ("GIT_INDEX_FILE", "GIT_WORK_TREE")


def redirect_value(var: str, other: Path) -> str:
    """The path `var` gets set to so git reads `other` instead of the lane repository."""
    return {
        "GIT_DIR": str(other / ".git"),
        "GIT_COMMON_DIR": str(other / ".git"),
        "GIT_OBJECT_DIRECTORY": str(other / ".git" / "objects"),
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(other / ".git" / "objects"),
        "GIT_INDEX_FILE": str(other / ".git" / "index"),
        "GIT_WORK_TREE": str(other),
    }[var]


@pytest.mark.parametrize("redirect_var", OBJECT_STORE_REDIRECT_VARS)
def test_the_sha_guard_skips_loudly_when_the_object_store_is_relocated(
    stub: StubHarness, tmp_path: Path, redirect_var: str
) -> None:
    """#245 D2-rework-2 (a) and (b): the object-store overrides skip loudly, in both directions.

    (a) `GIT_OBJECT_DIRECTORY` and `GIT_ALTERNATE_OBJECT_DIRECTORIES` were the unguarded pair: an
    override plus a token that resolves only in the foreign store used to be delivered with no
    skip line at all — the exact silent false pass the guard exists to prevent — and the lane's
    own commit could be refused (exit 2) because the probe asked the foreign store about it. (b)
    With the override in the tuple every direction delivers: the foreign-only token is not trusted
    silently, a dead token is not refused on the strength of a location the guard cannot trust,
    the lane's own token is not refused either, and the skip line names every token left
    unchecked. The assertions the F3 pin made on the falsified name list live here, retargeted at
    the measured set.
    """
    repo, short = sha_guard_repo(tmp_path)
    other, other_short = sha_guard_repo(tmp_path, name="other-repo")
    redirect = {"HERDR_LANE_DIR": str(repo), redirect_var: redirect_value(redirect_var, other)}

    unchecked = stub.run(
        "orchestrator",
        reply_payload(f"- lane `{short}`, foreign `{other_short}`"),
        env=redirect,
        cwd=repo,
    )
    assert unchecked.returncode == herdr_cli.EXIT_OK, unchecked.stderr
    assert "SHA guard skipped" in unchecked.stderr
    assert redirect_var in unchecked.stderr
    assert short in unchecked.stderr, "the skip line must name every unchecked token"
    assert other_short in unchecked.stderr, "the skip line must name every unchecked token"
    assert len(stub.prompts()) == 1

    dead = stub.run(
        "orchestrator", reply_payload(f"- base `{DRIFTED_ABBREV}`"), env=redirect, cwd=repo
    )
    assert dead.returncode == herdr_cli.EXIT_OK, dead.stderr
    assert "SHA guard skipped" in dead.stderr
    assert DRIFTED_ABBREV in dead.stderr

    own = stub.run("orchestrator", reply_payload(f"- base `{short}`"), env=redirect, cwd=repo)
    assert own.returncode == herdr_cli.EXIT_OK, own.stderr
    assert len(stub.prompts()) == 3


@pytest.mark.parametrize("redirect_var", VERDICT_NEUTRAL_REDIRECT_VARS)
def test_a_verdict_neutral_override_still_refuses_a_dead_token(
    stub: StubHarness, tmp_path: Path, redirect_var: str
) -> None:
    """#245 D2-rework-2 (c): the index and work-tree overrides must not skip.

    Measured: with only `GIT_INDEX_FILE` or `GIT_WORK_TREE` set, the probe's verdict is identical
    to a clean environment — the lane's commit still resolves, a foreign or dead token still does
    not. Skipping there would turn a correct refusal into a warning-bearing delivery, so the
    guard answers the question it can answer and no skip line appears.
    """
    repo, short = sha_guard_repo(tmp_path)
    other, other_short = sha_guard_repo(tmp_path, name="other-repo")
    redirect = {"HERDR_LANE_DIR": str(repo), redirect_var: redirect_value(redirect_var, other)}

    dead = stub.run(
        "orchestrator", reply_payload(f"- base `{DRIFTED_ABBREV}`"), env=redirect, cwd=repo
    )
    assert dead.returncode == herdr_cli.EXIT_USAGE, (dead.stdout, dead.stderr)
    assert DRIFTED_ABBREV in dead.stderr
    assert "SHA guard skipped" not in dead.stderr

    foreign = stub.run(
        "orchestrator", reply_payload(f"- base `{other_short}`"), env=redirect, cwd=repo
    )
    assert foreign.returncode == herdr_cli.EXIT_USAGE, (foreign.stdout, foreign.stderr)
    assert "SHA guard skipped" not in foreign.stderr
    assert stub.prompts() == []

    own = stub.run("orchestrator", reply_payload(f"- base `{short}`"), env=redirect, cwd=repo)
    assert own.returncode == herdr_cli.EXIT_OK, own.stderr
    assert len(stub.prompts()) == 1


def test_the_object_store_set_is_measured_not_asserted(tmp_path: Path) -> None:
    """The tuple's membership, re-derived by probing git itself, not by trusting the tuple.

    Raw `git rev-parse --verify` from the lane directory: an object-store override flips the
    verdict for a token (the lane's own commit stops resolving, or a foreign-only one starts),
    while a verdict-neutral override leaves both answers exactly as clean. This is the
    measurement the tuple follows, so a name moved in or out of it without re-measuring fails.
    """
    lane, lane_short = sha_guard_repo(tmp_path, name="lane")
    other, other_short = sha_guard_repo(tmp_path, name="other-repo")

    def resolves(sha: str, extra: dict[str, str]) -> bool:
        done = subprocess.run(
            ["git", "rev-parse", "--verify", f"{sha}^{{commit}}"],
            cwd=lane,
            capture_output=True,
            text=True,
            check=False,
            env={"PATH": os.environ["PATH"], **extra},
        )
        return done.returncode == 0

    clean = (resolves(lane_short, {}), resolves(other_short, {}))

    def flips(var: str) -> bool:
        pinned = {var: redirect_value(var, other)}
        return (resolves(lane_short, pinned), resolves(other_short, pinned)) != clean

    assert clean == (True, False), "the scratch lane must resolve its own commit and not another's"
    assert [var for var in OBJECT_STORE_REDIRECT_VARS if flips(var)] == list(
        OBJECT_STORE_REDIRECT_VARS
    )
    assert [var for var in VERDICT_NEUTRAL_REDIRECT_VARS if flips(var)] == []


def test_the_guard_skip_set_agrees_with_the_canonical_git_location_list() -> None:
    """Single-sourcing: the tuple plus the neutral pair are git's whole location family.

    A prod module cannot import tests, so the guard's set stays a literal here and
    `tests/git_env.GIT_LOCATION_VARS` — the list the shell scrub and the session scrub both
    derive from — stays canonical there; this pin holds the two together. Union and disjointness
    make the agreement exhaustive in both directions, so a name added to either list, or moved
    between the two classes, fails until the measurement above is redone. The pair is read from
    prod, and each set is compared to the literal above, so a name dropped from prod fails too.
    """
    assert set(herdr_reply.GIT_LOCATION_REDIRECT_VARS) == set(OBJECT_STORE_REDIRECT_VARS)
    assert set(herdr_reply.GIT_VERDICT_NEUTRAL_LOCATION_VARS) == set(VERDICT_NEUTRAL_REDIRECT_VARS)
    assert set(OBJECT_STORE_REDIRECT_VARS) & set(VERDICT_NEUTRAL_REDIRECT_VARS) == set()
    assert set(OBJECT_STORE_REDIRECT_VARS) | set(VERDICT_NEUTRAL_REDIRECT_VARS) == set(
        GIT_LOCATION_VARS
    )
