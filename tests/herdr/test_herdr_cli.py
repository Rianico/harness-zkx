"""Tests for skills/herdr/scripts/herdr_cli.py — the adapter the three helpers share."""

import io
import json
import os
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

import herdr_cli
import herdr_prompt
import herdr_reply
import pytest
import yaml

from tests.herdr.stub import SCRIPTS_DIR, StubHarness


def test_error_code_reads_envelope() -> None:
    stderr = '{"error":{"code":"agent_blocked","message":"blocked"},"id":"cli:agent:prompt"}'
    assert herdr_cli.error_code(stderr) == "agent_blocked"


@pytest.mark.parametrize("stderr", ["", "not json", "[]", '{"error":null}', '{"ok":1}'])
def test_error_code_tolerates_other_shapes(stderr: str) -> None:
    assert herdr_cli.error_code(stderr) is None


def test_error_code_accepts_plain_string_error() -> None:
    assert herdr_cli.error_code('{"error":"split failed"}') == "split failed"


def test_decode_response_reports_non_json() -> None:
    with pytest.raises(herdr_cli.HerdrError, match="non-JSON"):
        _ = herdr_cli.decode_response("not json")


def test_decode_response_reports_non_object() -> None:
    with pytest.raises(herdr_cli.HerdrError, match="non-object"):
        _ = herdr_cli.decode_response("[1, 2]")


def test_payload_field_reads_nested_values() -> None:
    raw = json.dumps({"result": {"pane": {"pane_id": "w9:p1"}}})
    assert herdr_cli.payload_field(raw, "result", "pane", "pane_id") == "w9:p1"


def test_payload_field_reports_the_missing_path() -> None:
    with pytest.raises(herdr_cli.HerdrError, match=r"result\.pane\.pane_id"):
        _ = herdr_cli.payload_field(json.dumps({"result": {}}), "result", "pane", "pane_id")


def test_text_field_rejects_an_empty_string() -> None:
    raw = json.dumps({"result": {"pane": {"pane_id": ""}}})
    with pytest.raises(herdr_cli.HerdrError, match="non-empty string"):
        _ = herdr_cli.text_field(raw, "result", "pane", "pane_id")


@pytest.mark.parametrize(
    ("value", "expected"),
    [("x", "x"), ("", None), (None, None), (7, None)],
)
def test_entry_optional_text_tolerates_absence(value: object, expected: str | None) -> None:
    assert herdr_cli.entry_optional_text({"label": value}, "label") == expected


def test_entry_optional_text_missing_key_is_none() -> None:
    assert herdr_cli.entry_optional_text({}, "label") is None


def test_entry_text_requires_a_non_empty_string() -> None:
    assert herdr_cli.entry_text({"pane_id": "w9:p1"}, "pane_id", where="pane") == "w9:p1"
    with pytest.raises(herdr_cli.HerdrError, match="has no usable 'pane_id'"):
        _ = herdr_cli.entry_text({"pane_id": ""}, "pane_id", where="pane")


def test_entries_reads_a_list_of_objects() -> None:
    raw = json.dumps({"result": {"panes": [{"pane_id": "w9:p1"}, {"pane_id": "w9:p2"}]}})
    found = herdr_cli.entries(raw, "result", "panes")
    assert [entry["pane_id"] for entry in found] == ["w9:p1", "w9:p2"]


def test_entries_rejects_a_non_list() -> None:
    with pytest.raises(herdr_cli.HerdrError, match="is not a list"):
        _ = herdr_cli.entries(json.dumps({"result": {"panes": {}}}), "result", "panes")


def test_entries_rejects_a_non_object_entry() -> None:
    with pytest.raises(herdr_cli.HerdrError, match="non-object entry"):
        _ = herdr_cli.entries(json.dumps({"result": {"panes": [1]}}), "result", "panes")


def test_guard_maps_usage_errors_to_exit_usage(capsys: pytest.CaptureFixture[str]) -> None:
    def boom() -> int:
        raise herdr_cli.UsageError("bad flag")

    assert herdr_cli.guard("herdr-x", boom) == herdr_cli.EXIT_USAGE
    assert "herdr-x: bad flag" in capsys.readouterr().err


def test_guard_maps_herdr_errors_to_exit_herdr(capsys: pytest.CaptureFixture[str]) -> None:
    def boom() -> int:
        raise herdr_cli.HerdrError("herdr said no")

    assert herdr_cli.guard("herdr-x", boom) == herdr_cli.EXIT_HERDR
    assert "herdr-x: herdr said no" in capsys.readouterr().err


def test_guard_passes_through_a_successful_action() -> None:
    assert herdr_cli.guard("herdr-x", lambda: int(herdr_cli.EXIT_OK)) == herdr_cli.EXIT_OK


# ── unit: scoped agent naming ──────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("role", "task_group", "expected"),
    [
        ("tm", "msg", "msg-tm"),
        ("msg-tm", "msg", "msg-tm"),
        ("tm", None, "tm"),
        ("tm", "", "tm"),
        ("msg", "msg", "msg"),
    ],
)
def test_scoped_agent_name_prefixes_and_passes_through(
    role: str, task_group: str | None, expected: str
) -> None:
    assert herdr_cli.scoped_agent_name(role, task_group) == expected


def test_scoped_agent_name_is_idempotent() -> None:
    once = herdr_cli.scoped_agent_name("tm", "msg")
    assert herdr_cli.scoped_agent_name(once, "msg") == once == "msg-tm"


def test_validate_agent_name_accepts_a_scoped_name() -> None:
    herdr_cli.validate_agent_name("msg-impl-1")


@pytest.mark.parametrize("name", ["Message", "msg impl", "a" * 33])
def test_validate_agent_name_rejects_violations(name: str) -> None:
    with pytest.raises(herdr_cli.UsageError, match="not a valid agent name"):
        herdr_cli.validate_agent_name(name)


# ── pin: the shared payload reader, exercised through BOTH entry points ────────────
#
# `herdr_cli.read_payload_stream` and `herdr_cli.decode_payload` are the shared
# acquisition-and-validation seam. `herdr_prompt.read_payload` and
# `herdr_reply.read_payload` keep their own fallback (MESSAGE, the both-given refusal) and
# their own wording. This pin calls both entry points with the same input and asserts they
# agree, so a future edit that re-forks one caller's path (drops the NUL check, drops the
# UTF-8 decode, or swaps in the other caller's wording) fails here.

PayloadReader = Callable[[str | None, str | None], str]


def _read_prompt(source: str | None, message: str | None) -> str:
    """Adapt herdr-prompt's one-argument reader to the two-argument shape the pin uses."""
    assert message is None, "herdr-prompt has no MESSAGE positional"
    return herdr_prompt.read_payload(source)


def _read_reply(source: str | None, message: str | None) -> str:
    return herdr_reply.read_payload(source, message)


PAYLOAD_READERS: list[object] = [
    pytest.param(_read_prompt, id="prompt"),
    pytest.param(_read_reply, id="reply"),
]


class _Tty:
    """A stand-in for an interactive stdin: `isatty()` is all `read_payload` asks of it."""

    def isatty(self) -> bool:
        return True


@pytest.mark.parametrize("read", PAYLOAD_READERS)
def test_payload_reader_rejects_a_nul_byte(read: PayloadReader, tmp_path: Path) -> None:
    path = tmp_path / "nul.bin"
    _ = path.write_bytes(b"a\x00b")
    with pytest.raises(herdr_cli.UsageError, match="NUL byte"):
        _ = read(str(path), None)


@pytest.mark.parametrize("read", PAYLOAD_READERS)
def test_payload_reader_rejects_invalid_utf8(read: PayloadReader, tmp_path: Path) -> None:
    path = tmp_path / "binary.bin"
    _ = path.write_bytes(b"\xff\xfebad")
    with pytest.raises(herdr_cli.UsageError, match="not valid UTF-8"):
        _ = read(str(path), None)


@pytest.mark.parametrize("read", PAYLOAD_READERS)
def test_payload_reader_names_the_nul_refusal_first(read: PayloadReader, tmp_path: Path) -> None:
    """Both entry points report the SAME blocker for a NUL-bearing, invalid-UTF-8 payload.

    Pins the NUL-before-decode order: the argv-safety refusal wins over the codec complaint.
    """
    path = tmp_path / "both.bin"
    _ = path.write_bytes(b"\x00\xff")
    with pytest.raises(herdr_cli.UsageError, match="NUL byte"):
        _ = read(str(path), None)


@pytest.mark.parametrize("read", PAYLOAD_READERS)
def test_payload_reader_reports_a_missing_file(read: PayloadReader, tmp_path: Path) -> None:
    with pytest.raises(herdr_cli.UsageError, match="cannot read payload"):
        _ = read(str(tmp_path / "nope.md"), None)


@pytest.mark.parametrize("read", PAYLOAD_READERS)
def test_payload_reader_returns_the_same_valid_payload(read: PayloadReader, tmp_path: Path) -> None:
    path = tmp_path / "ok.md"
    _ = path.write_text("shared payload \u00e9\n", encoding="utf-8")
    assert read(str(path), None) == "shared payload \u00e9\n"


@pytest.mark.parametrize("read", PAYLOAD_READERS)
def test_payload_reader_reads_stdin_and_dash(
    read: PayloadReader, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO("piped \u00e9\n".encode())))
    assert read(None, None) == "piped \u00e9\n"
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b"dashed\n")))
    assert read("-", None) == "dashed\n"


def test_payload_readers_agree_on_one_valid_payload(tmp_path: Path) -> None:
    path = tmp_path / "ok.md"
    _ = path.write_text("agreed \u00e9\n", encoding="utf-8")
    assert _read_prompt(str(path), None) == _read_reply(str(path), None)


# ── pin: the reply-only fallbacks stay local to herdr-reply ────────────────────────


def test_reply_message_and_file_together_are_refused(tmp_path: Path) -> None:
    with pytest.raises(herdr_cli.UsageError, match="not both"):
        _ = herdr_reply.read_payload(str(tmp_path / "x"), "msg")


def test_reply_message_alone_is_the_payload() -> None:
    assert herdr_reply.read_payload(None, "msg") == "msg"


def test_reply_stdin_refusal_names_message_not_only_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The reply's wording must keep naming MESSAGE, never the prompt's `--file` sentence."""
    monkeypatch.setattr(sys, "stdin", _Tty())
    with pytest.raises(herdr_cli.UsageError, match="MESSAGE"):
        _ = herdr_reply.read_payload(None, None)


def test_prompt_stdin_refusal_names_only_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stdin", _Tty())
    with pytest.raises(herdr_cli.UsageError, match="no --file given"):
        _ = herdr_prompt.read_payload(None)


def test_prompt_empty_refusal_names_the_prompt(tmp_path: Path) -> None:
    path = tmp_path / "blank.md"
    _ = path.write_text("   \n", encoding="utf-8")
    with pytest.raises(herdr_cli.UsageError, match="empty prompt"):
        _ = herdr_prompt.read_payload(str(path))


def test_reply_empty_refusal_names_the_reply(tmp_path: Path) -> None:
    path = tmp_path / "blank.md"
    _ = path.write_text("   \n", encoding="utf-8")
    with pytest.raises(herdr_cli.UsageError, match="empty reply"):
        _ = herdr_reply.read_payload(str(path), None)


# ── lane anchor primitive (#266 T2a P2) ────────────────────────────────────────────


def test_lane_anchor_prefers_the_explicit_env_anchor(tmp_path: Path) -> None:
    lane = tmp_path / "lane"
    lane.mkdir()

    assert herdr_cli.resolve_lane_base_dir({herdr_cli.LANE_DIR_ENV: str(lane)}) == lane


def test_lane_anchor_resolves_the_repo_root_of_a_real_checkout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = {**os.environ}
    _ = env.pop(herdr_cli.LANE_DIR_ENV, None)
    repo = tmp_path / "repo"
    repo.mkdir()
    _ = subprocess.run(["git", "init", "-q", str(repo)], check=True, env=env)
    _ = monkeypatch.chdir(repo)

    assert herdr_cli.resolve_lane_base_dir(env) == repo.resolve()


def test_lane_anchor_refuses_when_no_anchor_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = {**os.environ, "GIT_CEILING_DIRECTORIES": str(tmp_path)}
    _ = env.pop(herdr_cli.LANE_DIR_ENV, None)
    plain = tmp_path / "plain"
    plain.mkdir()
    _ = monkeypatch.chdir(plain)

    with pytest.raises(herdr_cli.LaneAnchorError, match="no lane state anchor"):
        _ = herdr_cli.resolve_lane_base_dir(env)


def test_sanitize_branch_maps_a_slash_to_a_dash() -> None:
    assert herdr_cli.sanitize_branch("feat/184-worktree") == "feat-184-worktree"
    assert herdr_cli.sanitize_branch("///") == "worktree"


def test_worktree_module_reexports_the_anchor_primitive() -> None:
    import herdr_worktree

    assert herdr_worktree.resolve_lane_base_dir is herdr_cli.resolve_lane_base_dir
    assert herdr_worktree.LaneAnchorError is herdr_cli.LaneAnchorError
    assert herdr_worktree.LANE_DIR_ENV == herdr_cli.LANE_DIR_ENV
    assert herdr_worktree.sanitize_branch is herdr_cli.sanitize_branch


# ── the shared atomic store primitive (#266 T2b P4) ────────────────────────────────


def test_atomic_write_yaml_preserves_declaration_order(tmp_path: Path) -> None:
    path = tmp_path / "store.yaml"

    herdr_cli.atomic_write_yaml(path, {"b": 1, "a": {"z": 3, "y": 2}}, default_flow_style=False)

    assert path.read_text(encoding="utf-8") == "b: 1\na:\n  z: 3\n  y: 2\n"


def test_atomic_write_bytes_leaves_no_temporary_file(tmp_path: Path) -> None:
    path = tmp_path / "store.yaml"

    herdr_cli.atomic_write_bytes(path, b"x: 1\n")

    assert path.read_text(encoding="utf-8") == "x: 1\n"
    assert [entry.name for entry in tmp_path.iterdir()] == ["store.yaml"]


def test_atomic_write_bytes_cleans_up_when_the_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "store.yaml"

    def explode(*_args: object, **_kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(herdr_cli.os, "replace", explode)

    with pytest.raises(OSError, match="disk full"):
        herdr_cli.atomic_write_bytes(path, b"x: 1\n")
    assert list(tmp_path.iterdir()) == []


# ── merged inventory: snapshot + store, annotated (#266 T2c P6) ────────────────────


def inventory_env(tmp_path: Path, store: dict[str, object] | None) -> dict[str, str]:
    """A lane anchor with an optional `.lane/tasks.yaml` store."""
    if store is not None:
        lane = tmp_path / ".lane"
        lane.mkdir(parents=True, exist_ok=True)
        _ = (lane / "tasks.yaml").write_text(yaml.safe_dump(store), encoding="utf-8")
    return {**os.environ, herdr_cli.LANE_DIR_ENV: str(tmp_path)}


def stub_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    panes: Sequence[Mapping[str, object]],
    agents: Sequence[Mapping[str, object]],
) -> None:
    """Answer the two inventory reads; any other herdr call is a bug in this test."""

    def fake(argv: Sequence[str], _env: Mapping[str, str]) -> str:
        if argv[1:3] == ["pane", "list"]:
            return json.dumps({"result": {"panes": panes}})
        if argv[1:3] == ["agent", "list"]:
            return json.dumps({"result": {"agents": agents}})
        raise AssertionError(f"unexpected herdr call: {argv}")

    monkeypatch.setattr(herdr_cli, "run_herdr_checked", fake)


def test_merged_inventory_marks_an_absent_store_pane_stale_and_keeps_the_fact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lease = {
        "target": "ghost",
        "ticket": "#265",
        "pane_id": "w9:p9",
        "acquired_at": "2026-10-20T00:00:00Z",
    }
    env = inventory_env(tmp_path, {"active_leases": {"ghost": lease}})
    stub_snapshot(monkeypatch, [{"pane_id": "w9:p1"}], [])

    inventory = herdr_cli.merged_inventory("/bin/herdr", env)

    assert len(inventory.bindings) == 1
    binding = inventory.bindings[0]
    assert binding["liveness"] == "stale"
    assert binding["kind"] == "lease"
    assert binding["key"] == "ghost"
    assert binding["target"] == "ghost"
    assert binding["ticket"] == "#265"
    assert binding["evidence"] == {"pane_listed": False, "agent_listed": False}
    # stale is reported, never deleted
    stored = yaml.safe_load((tmp_path / ".lane" / "tasks.yaml").read_text(encoding="utf-8"))
    assert stored["active_leases"]["ghost"] == lease


def test_merged_inventory_marks_a_store_pane_the_daemon_lists_live(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = inventory_env(
        tmp_path,
        {"active_leases": {"impl": {"target": "impl", "pane_id": "w9:p1", "ticket": "#1"}}},
    )
    stub_snapshot(monkeypatch, [{"pane_id": "w9:p1"}], [{"pane_id": "w9:p1", "name": "impl"}])

    binding = herdr_cli.merged_inventory("/bin/herdr", env).bindings[0]

    assert binding["liveness"] == "live"
    assert binding["evidence"] == {"pane_listed": True, "agent_listed": True}


def test_merged_inventory_reports_an_unclaimed_agent_without_inventing_ownership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = inventory_env(tmp_path, None)
    stub_snapshot(monkeypatch, [{"pane_id": "w9:p2"}], [{"pane_id": "w9:p2", "name": "reviewer"}])

    inventory = herdr_cli.merged_inventory("/bin/herdr", env)

    assert inventory.bindings == []
    assert inventory.unclaimed == [
        {
            "pane_id": "w9:p2",
            "name": "reviewer",
            "liveness": "live",
            "ownership": "unclaimed",
        }
    ]


def test_merged_inventory_keeps_every_daemon_field_and_annotates_additively(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env = inventory_env(tmp_path, None)
    pane = {"pane_id": "w9:p1", "tab_id": "w9:t1", "label": "impl"}
    agent = {"pane_id": "w9:p1", "name": "impl", "status": "idle", "revision": 3}
    stub_snapshot(monkeypatch, [pane], [agent])

    inventory = herdr_cli.merged_inventory("/bin/herdr", env)

    assert inventory.panes[0] == {**pane, "liveness": "live"}
    assert inventory.agents[0] == {**agent, "liveness": "live"}
    assert inventory.raw_panes == json.dumps({"result": {"panes": [pane]}})
    assert inventory.raw_agents == json.dumps({"result": {"agents": [agent]}})


def test_read_store_facts_degrades_to_empty_dict_on_missing_pyyaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lane_dir = tmp_path / ".lane"
    lane_dir.mkdir()
    _ = (lane_dir / "tasks.yaml").write_text("tasks: []\n", encoding="utf-8")

    def raise_herdr_error() -> None:
        raise herdr_cli.HerdrError("store access needs pyyaml; run this script with `uv run`")

    monkeypatch.setattr(herdr_cli, "yaml_module", raise_herdr_error)
    facts = herdr_cli.read_store_facts({"HERDR_LANE_DIR": str(tmp_path)})
    assert facts == {}


def test_current_workspace_id_reads_env_first(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(_argv: Sequence[str], _env: Mapping[str, str]) -> str:
        raise AssertionError("env should avoid subprocess call")

    monkeypatch.setattr(herdr_cli, "run_herdr_checked", explode)
    assert herdr_cli.current_workspace_id("/bin/herdr", {"HERDR_WORKSPACE_ID": "w12"}) == "w12"


def test_current_workspace_id_falls_back_to_pane_current(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(argv: Sequence[str], _env: Mapping[str, str]) -> str:
        assert list(argv) == ["/bin/herdr", "pane", "current", "--current"]
        return json.dumps({"result": {"pane": {"workspace_id": "w15", "pane_id": "w15:p3"}}})

    monkeypatch.setattr(herdr_cli, "run_herdr_checked", fake_run)
    assert herdr_cli.current_workspace_id("/bin/herdr", {}) == "w15"


def test_current_workspace_id_derives_from_pane_id_split(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(argv: Sequence[str], _env: Mapping[str, str]) -> str:
        assert list(argv) == ["/bin/herdr", "pane", "current", "--current"]
        return json.dumps({"result": {"pane": {"pane_id": "w99:p1"}}})

    monkeypatch.setattr(herdr_cli, "run_herdr_checked", fake_run)
    assert herdr_cli.current_workspace_id("/bin/herdr", {}) == "w99"


# ── fail closed: the target is verified as an agent before any send (#369) ─────────
#
# `verify_target_not_bare_shell` asks the daemon what a target is running so prose is never
# injected into a shell. Two defects made that gate optional (#369): an unreadable daemon
# counted as "not a shell" (fail-open), and `--no-caller-context` skipped the check along
# with the envelope lookups. These pin both closed. The three outcomes are distinct:
# could not verify ⇒ `HerdrError` (exit 1, no send); verified shell ⇒ `BareShellRefusal`
# (exit 2, no send); verified agent ⇒ the send happens, with or without the UX flags.

PROMPT_SCRIPT = SCRIPTS_DIR / "herdr_prompt.py"
SHELL_TARGET = "w9:p2"  # DEFAULT_STATE: a pane with no live agent
AGENT_TARGET = "reviewer"  # DEFAULT_STATE: the live agent on w9:p1
INVENTORY_CALLS: tuple[list[str], ...] = (["pane", "list"], ["agent", "list"])


@pytest.fixture
def stub(stub_factory: Callable[[Path], StubHarness]) -> StubHarness:
    """The shared stub `herdr`, driven through `herdr-prompt` as in the prompt suite."""
    return stub_factory(PROMPT_SCRIPT)


def prompt_payload(tmp_path: Path, text: str = "hi") -> Path:
    path = tmp_path / "payload.md"
    _ = path.write_text(text, encoding="utf-8")
    return path


def inventory_failure(mode: str, argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    """One unverifiable daemon answer: dead process, garbage, silence, or a missing field."""
    if mode == "error":
        return subprocess.CompletedProcess(list(argv), 1, "", '{"error":"daemon unreachable"}')
    if mode == "garbage":
        return subprocess.CompletedProcess(list(argv), 0, "not json at all", "")
    if mode == "empty":
        return subprocess.CompletedProcess(list(argv), 0, "", "")
    return subprocess.CompletedProcess(list(argv), 0, json.dumps({"result": {}}), "")


@pytest.fixture
def failing_daemon(monkeypatch: pytest.MonkeyPatch, stub: StubHarness) -> Callable[[str], None]:
    """Fail only the inventory reads; any other argv still reaches the stub and is logged."""

    def install(mode: str) -> None:
        real = herdr_cli.run_herdr

        def fake(argv: Sequence[str], env: Mapping[str, str]) -> subprocess.CompletedProcess[str]:
            if list(argv)[1:3] in INVENTORY_CALLS:
                return inventory_failure(mode, argv)
            return real(argv, env)

        monkeypatch.setattr(herdr_cli, "run_herdr", fake)

    return install


DAEMON_FAILURES = [
    pytest.param("error", id="exit-1"),
    pytest.param("garbage", id="non-json"),
    pytest.param("empty", id="empty-output"),
    pytest.param("missing-field", id="missing-field"),
]
FLAG_VARIANTS = [
    pytest.param((), id="envelope"),
    pytest.param(("--no-caller-context",), id="no-caller-context"),
]


@pytest.mark.parametrize("mode", DAEMON_FAILURES)
@pytest.mark.parametrize("flags", FLAG_VARIANTS)
def test_an_unverifiable_target_refuses_the_send(
    stub: StubHarness,
    tmp_path: Path,
    failing_daemon: Callable[[str], None],
    mode: str,
    flags: tuple[str, ...],
) -> None:
    """A daemon that cannot answer is not evidence of an agent: refuse, send nothing."""
    failing_daemon(mode)

    done = stub.run(AGENT_TARGET, "--file", str(prompt_payload(tmp_path)), *flags)

    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "could not verify" in done.stderr
    assert AGENT_TARGET in done.stderr
    assert "herdr agent list" in done.stderr  # the remedy, not just the symptom
    assert stub.prompts() == []


@pytest.mark.parametrize("mode", DAEMON_FAILURES)
def test_a_dry_run_still_verifies_and_refuses_an_unverifiable_target(
    stub: StubHarness,
    tmp_path: Path,
    failing_daemon: Callable[[str], None],
    mode: str,
) -> None:
    """`--dry-run` sends nothing, but it must not skip the check either."""
    failing_daemon(mode)

    done = stub.run(
        AGENT_TARGET,
        "--file",
        str(prompt_payload(tmp_path)),
        "--dry-run",
        "--no-caller-context",
    )

    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "could not verify" in done.stderr
    assert stub.prompts() == []


@pytest.mark.parametrize("flags", FLAG_VARIANTS)
def test_a_bare_shell_target_is_refused(
    stub: StubHarness, tmp_path: Path, flags: tuple[str, ...]
) -> None:
    done = stub.run(SHELL_TARGET, "--file", str(prompt_payload(tmp_path)), *flags)

    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "no live agent" in done.stderr
    assert "Refusing injection" in done.stderr
    assert "could not verify" not in done.stderr
    assert stub.prompts() == []


def test_a_dry_run_reports_a_bare_shell_target_instead_of_sending(
    stub: StubHarness, tmp_path: Path
) -> None:
    """A dry run cannot inject, so the shell verdict is a note, not a refusal (#369 C)."""
    done = stub.run(
        SHELL_TARGET,
        "--file",
        str(prompt_payload(tmp_path)),
        "--dry-run",
        "--no-caller-context",
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert f"note: target {SHELL_TARGET!r} is a bare shell" in done.stderr
    assert f"refused with exit {herdr_cli.EXIT_USAGE}" in done.stderr
    assert stub.prompts() == []


@pytest.mark.parametrize("flags", FLAG_VARIANTS)
def test_a_verified_agent_target_proceeds(
    stub: StubHarness, tmp_path: Path, flags: tuple[str, ...]
) -> None:
    done = stub.run(AGENT_TARGET, "--file", str(prompt_payload(tmp_path)), "--no-wait", *flags)

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    (call,) = stub.prompts()
    assert call[3] == AGENT_TARGET


def test_a_verified_agent_target_still_dry_runs_without_sending(
    stub: StubHarness, tmp_path: Path
) -> None:
    done = stub.run(
        AGENT_TARGET,
        "--file",
        str(prompt_payload(tmp_path)),
        "--dry-run",
        "--no-caller-context",
    )

    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert stub.prompts() == []


def test_verify_raises_herdr_error_when_the_inventory_is_unreadable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def explode(_argv: Sequence[str], _env: Mapping[str, str]) -> str:
        raise herdr_cli.HerdrError("herdr pane list failed: exit status 1")

    monkeypatch.setattr(herdr_cli, "run_herdr_checked", explode)

    with pytest.raises(herdr_cli.HerdrError, match="could not verify target 'w9:p1'"):
        herdr_cli.verify_target_not_bare_shell("/bin/herdr", "w9:p1", {})


def test_verify_raises_the_bare_shell_refusal_for_a_shell_pane(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub_snapshot(
        monkeypatch,
        [{"pane_id": "w9:p2", "agent": None, "agent_status": "unknown"}],
        [],
    )

    def failing_run(
        argv: Sequence[str], _env: Mapping[str, str]
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(list(argv), 1, "", "")

    monkeypatch.setattr(herdr_cli, "run_herdr", failing_run)

    with pytest.raises(herdr_cli.BareShellRefusal, match="no live agent"):
        herdr_cli.verify_target_not_bare_shell("/bin/herdr", "w9:p2", {})


def test_verify_accepts_a_live_agent_target(monkeypatch: pytest.MonkeyPatch) -> None:
    stub_snapshot(
        monkeypatch,
        [{"pane_id": "w9:p1", "agent": "pi", "agent_status": "idle"}],
        [{"pane_id": "w9:p1", "name": "reviewer"}],
    )

    herdr_cli.verify_target_not_bare_shell("/bin/herdr", "reviewer", {})


# ── typed response wrappers (#370) ─────────────────────────────────────────────────
#
# Every wrapper owns one verb: the argv it sends, the response path it reads, and the shape
# it admits. The payloads below carry every field herdr 0.9.5 declares, so a parser that
# drops a field or accepts the wrong type fails here instead of in a caller.


def stub_response(monkeypatch: pytest.MonkeyPatch, payload: str) -> list[list[str]]:
    """Answer every herdr call with `payload` and return the argv log."""
    calls: list[list[str]] = []

    def fake(argv: Sequence[str], _env: Mapping[str, str]) -> str:
        calls.append(list(argv))
        return payload

    monkeypatch.setattr(herdr_cli, "run_herdr_checked", fake)
    return calls


def live_pane(pane_id: str = "w9:p1") -> dict[str, object]:
    """One `PaneInfo`: every required field plus the optional fields v0.9.5 sends."""
    return {
        "pane_id": pane_id,
        "terminal_id": f"term-{pane_id}",
        "workspace_id": "w9",
        "tab_id": "w9:t1",
        "focused": True,
        "agent_status": "idle",
        "revision": 11,
        "agent": "pi",
        "agent_session": {
            "source": "native",
            "agent": "pi",
            "kind": "id",
            "value": "session-1",
        },
        "cwd": "/tmp/work",
        "display_agent": "pi",
        "foreground_cwd": "/tmp/work",
        "label": "impl",
        "restore_error": None,
        "scroll": {
            "offset_from_bottom": 0,
            "max_offset_from_bottom": 240,
            "viewport_rows": 30,
        },
        "state_labels": {"ticket": "#370"},
        "terminal_title": "pi",
        "terminal_title_stripped": "pi",
        "title": "impl",
        "tokens": {"ticket": "#370"},
    }


def live_tab() -> dict[str, object]:
    """One `TabInfo`: every required field."""
    return {
        "tab_id": "w9:t2",
        "workspace_id": "w9",
        "number": 2,
        "label": "impl",
        "focused": True,
        "pane_count": 1,
        "agent_status": "idle",
    }


def live_agent() -> dict[str, object]:
    """One `AgentInfo`: every required field plus the optional fields v0.9.5 sends."""
    return {
        "terminal_id": "term-w9:p1",
        "agent_status": "idle",
        "workspace_id": "w9",
        "tab_id": "w9:t1",
        "pane_id": "w9:p1",
        "focused": True,
        "revision": 7,
        "agent": "pi",
        "agent_session": {
            "source": "native",
            "agent": "pi",
            "kind": "id",
            "value": "session-1",
        },
        "completion_seq": 3,
        "cwd": "/tmp/work",
        "display_agent": "pi",
        "foreground_cwd": "/tmp/work",
        "interactive_ready": True,
        "launch_pending": False,
        "name": "impl",
        "screen_detection_skipped": False,
        "state_change_seq": 2,
        "state_labels": {"ticket": "#370"},
        "terminal_title": "pi",
        "terminal_title_stripped": "pi",
        "title": "impl",
        "tokens": {"ticket": "#370"},
    }


def live_workspace() -> dict[str, object]:
    """One `WorkspaceInfo`: every required field plus the optional fields v0.9.5 sends."""
    return {
        "workspace_id": "w9",
        "number": 1,
        "label": "main",
        "focused": True,
        "pane_count": 2,
        "tab_count": 1,
        "active_tab_id": "w9:t1",
        "agent_status": "idle",
        "tokens": {"ticket": "#370"},
        "worktree": {
            "repo_key": "harness",
            "repo_name": "harness",
            "repo_root": "/tmp/harness",
            "checkout_path": "/tmp/harness",
            "is_linked_worktree": False,
        },
    }


def live_workspace_listing() -> dict[str, object]:
    """One `workspace list` entry: only the fields herdr 0.9.5 requires."""
    return {
        "workspace_id": "w9",
        "number": 1,
        "label": "main",
        "focused": True,
        "pane_count": 2,
        "tab_count": 1,
        "active_tab_id": "w9:t1",
        "agent_status": "idle",
    }


def live_layout() -> dict[str, object]:
    """One `PaneLayoutSnapshot`: every required field of the layout and its panes."""
    return {
        "workspace_id": "w9",
        "tab_id": "w9:t1",
        "zoomed": False,
        "area": {"x": 0, "y": 0, "width": 160, "height": 48},
        "focused_pane_id": "w9:p1",
        "panes": [
            {
                "pane_id": "w9:p1",
                "focused": True,
                "rect": {"x": 0, "y": 0, "width": 80, "height": 24},
            }
        ],
        "splits": [],
    }


def live_read() -> dict[str, object]:
    """One `PaneReadResult`: every required field."""
    return {
        "pane_id": "w9:p1",
        "workspace_id": "w9",
        "tab_id": "w9:t1",
        "source": "recent",
        "format": "text",
        "text": "READY\n",
        "revision": 12,
        "truncated": False,
    }


def live_match() -> dict[str, object]:
    """One `output_matched` result: the read and the matched line."""
    return {
        "pane_id": "w9:p1",
        "revision": 12,
        "matched_line": "READY",
        "read": live_read(),
    }


def test_create_tab_reads_tab_and_root_pane_from_one_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps(
        {"result": {"type": "tab_created", "tab": live_tab(), "root_pane": live_pane("w9:p2")}}
    )
    calls = stub_response(monkeypatch, payload)

    created = herdr_cli.create_tab(
        "/bin/herdr",
        {},
        workspace_id="w9",
        label="impl",
        cwd="/tmp/work",
        env_vars=["A=1"],
        focus=False,
    )

    assert calls == [
        [
            "/bin/herdr",
            "tab",
            "create",
            "--workspace",
            "w9",
            "--cwd",
            "/tmp/work",
            "--label",
            "impl",
            "--env",
            "A=1",
            "--no-focus",
        ]
    ]
    assert created.tab.tab_id == "w9:t2"
    assert created.tab.number == 2
    assert created.root_pane.pane_id == "w9:p2"
    assert created.root_pane.agent_session is not None
    assert created.root_pane.agent_session.value == "session-1"
    assert created.root_pane.scroll is not None
    assert created.root_pane.scroll.viewport_rows == 30


def test_create_tab_names_a_missing_root_pane(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"result": {"type": "tab_created", "tab": live_tab()}})
    calls = stub_response(monkeypatch, payload)

    with pytest.raises(herdr_cli.HerdrError, match="root_pane"):
        _ = herdr_cli.create_tab("/bin/herdr", {})
    assert len(calls) == 1


def test_split_pane_reads_result_pane_and_sends_the_expected_tokens(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps({"result": {"type": "pane_info", "pane": live_pane("w9:p3")}})
    calls = stub_response(monkeypatch, payload)

    pane = herdr_cli.split_pane(
        "/bin/herdr",
        {},
        pane_id="w9:p1",
        direction="right",
        cwd="/tmp/work",
        env_vars=["A=1"],
        focus=True,
    )

    assert calls == [
        [
            "/bin/herdr",
            "pane",
            "split",
            "--pane",
            "w9:p1",
            "--direction",
            "right",
            "--cwd",
            "/tmp/work",
            "--env",
            "A=1",
            "--focus",
        ]
    ]
    assert pane.pane_id == "w9:p3"
    assert pane.state_labels == {"ticket": "#370"}


def test_split_pane_sends_ratio_between_direction_and_cwd(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps({"result": {"type": "pane_info", "pane": live_pane("w9:p3")}})
    calls = stub_response(monkeypatch, payload)

    _ = herdr_cli.split_pane(
        "/bin/herdr",
        {},
        pane_id="w9:p1",
        direction="right",
        ratio=0.3,
        cwd="/tmp/work",
    )

    assert calls == [
        [
            "/bin/herdr",
            "pane",
            "split",
            "--pane",
            "w9:p1",
            "--direction",
            "right",
            "--ratio",
            "0.3",
            "--cwd",
            "/tmp/work",
        ]
    ]


def test_split_pane_omits_ratio_when_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"result": {"type": "pane_info", "pane": live_pane("w9:p3")}})
    calls = stub_response(monkeypatch, payload)

    _ = herdr_cli.split_pane("/bin/herdr", {}, pane_id="w9:p1", direction="down")

    assert calls == [["/bin/herdr", "pane", "split", "--pane", "w9:p1", "--direction", "down"]]
    assert "--ratio" not in calls[0]


def test_split_pane_formats_ratio_like_the_lane_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps({"result": {"type": "pane_info", "pane": live_pane("w9:p3")}})
    calls = stub_response(monkeypatch, payload)

    _ = herdr_cli.split_pane("/bin/herdr", {}, pane_id="w9:p1", ratio=0.1234567)

    assert calls == [["/bin/herdr", "pane", "split", "--pane", "w9:p1", "--ratio", "0.123457"]]


@pytest.mark.parametrize("ratio", [float("nan"), float("inf")])
def test_split_pane_refuses_a_non_finite_ratio_before_any_call(
    monkeypatch: pytest.MonkeyPatch,
    ratio: float,
) -> None:
    payload = json.dumps({"result": {"type": "pane_info", "pane": live_pane("w9:p3")}})
    calls = stub_response(monkeypatch, payload)

    with pytest.raises(herdr_cli.UsageError, match=f"ratio {ratio} is not finite"):
        _ = herdr_cli.split_pane("/bin/herdr", {}, ratio=ratio)

    assert calls == []


@pytest.mark.parametrize(
    ("field", "value"),
    [("focused", "yes"), ("revision", "3"), ("pane_id", None), ("state_labels", ["#370"])],
)
def test_pane_info_rejects_a_wrong_typed_required_field(
    monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    pane = live_pane()
    pane[field] = value
    payload = json.dumps({"result": {"type": "pane_info", "pane": pane}})
    _ = stub_response(monkeypatch, payload)

    with pytest.raises(herdr_cli.HerdrError, match=f"no usable '{field}'"):
        _ = herdr_cli.split_pane("/bin/herdr", {})


def test_pane_info_names_a_missing_nested_agent_session_field() -> None:
    pane = live_pane()
    pane["agent_session"] = {"source": "native", "agent": "pi", "value": "session-1"}

    with pytest.raises(herdr_cli.HerdrError, match=r"agent_session has no usable 'kind'"):
        _ = herdr_cli._pane_info(pane, where="pane")


def test_get_pane_layout_parses_panes_and_rectangles(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"result": {"type": "pane_layout", "layout": live_layout()}})
    calls = stub_response(monkeypatch, payload)

    layout = herdr_cli.get_pane_layout("/bin/herdr", {}, "w9:p1")

    assert calls == [["/bin/herdr", "pane", "layout", "--pane", "w9:p1"]]
    assert layout.workspace_id == "w9"
    assert layout.focused_pane_id == "w9:p1"
    assert layout.panes == (
        herdr_cli.PaneLayoutPane(
            pane_id="w9:p1",
            focused=True,
            rect=herdr_cli.PaneRect(x=0, y=0, width=80, height=24),
        ),
    )


def test_get_pane_layout_names_a_wrong_typed_rect_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = live_layout()
    layout["panes"] = [{"pane_id": "w9:p1", "focused": True, "rect": {"x": 0, "y": 0}}]
    payload = json.dumps({"result": {"type": "pane_layout", "layout": layout}})
    _ = stub_response(monkeypatch, payload)

    with pytest.raises(herdr_cli.HerdrError, match=r"no usable 'width'"):
        _ = herdr_cli.get_pane_layout("/bin/herdr", {}, "w9:p1")


def test_get_agent_reads_result_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"result": {"type": "agent_info", "agent": live_agent()}})
    calls = stub_response(monkeypatch, payload)

    agent = herdr_cli.get_agent("/bin/herdr", {}, "impl")

    assert calls == [["/bin/herdr", "agent", "get", "impl"]]
    assert agent.name == "impl"
    assert agent.completion_seq == 3
    assert agent.state_change_seq == 2


def test_get_agent_names_a_missing_required_field(monkeypatch: pytest.MonkeyPatch) -> None:
    broken = live_agent()
    del broken["revision"]
    payload = json.dumps({"result": {"type": "agent_info", "agent": broken}})
    _ = stub_response(monkeypatch, payload)

    with pytest.raises(herdr_cli.HerdrError, match=r"result\.agent has no usable 'revision'"):
        _ = herdr_cli.get_agent("/bin/herdr", {}, "impl")


def test_get_agent_reads_an_absent_state_labels_key_as_an_empty_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = live_agent()
    del agent["state_labels"]
    del agent["tokens"]
    _ = stub_response(monkeypatch, json.dumps({"result": {"type": "agent_info", "agent": agent}}))

    found = herdr_cli.get_agent("/bin/herdr", {}, "impl")

    assert found.state_labels == {}
    assert found.tokens == {}


def test_get_agent_reads_a_null_state_labels_key_as_an_empty_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = live_agent()
    agent["state_labels"] = None
    agent["tokens"] = None
    _ = stub_response(monkeypatch, json.dumps({"result": {"type": "agent_info", "agent": agent}}))

    found = herdr_cli.get_agent("/bin/herdr", {}, "impl")

    assert found.state_labels == {}
    assert found.tokens == {}


def test_get_agent_names_a_non_object_state_labels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = live_agent()
    agent["state_labels"] = ["#370"]
    _ = stub_response(monkeypatch, json.dumps({"result": {"type": "agent_info", "agent": agent}}))

    with pytest.raises(herdr_cli.HerdrError, match=r"no usable 'state_labels'"):
        _ = herdr_cli.get_agent("/bin/herdr", {}, "impl")


def test_get_agent_names_a_non_string_token_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = live_agent()
    agent["tokens"] = {"ticket": 7}
    _ = stub_response(monkeypatch, json.dumps({"result": {"type": "agent_info", "agent": agent}}))

    with pytest.raises(herdr_cli.HerdrError, match=r"no usable 'tokens'"):
        _ = herdr_cli.get_agent("/bin/herdr", {}, "impl")


def test_list_agents_reads_every_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    second = live_agent()
    second["pane_id"] = "w9:p2"
    payload = json.dumps({"result": {"type": "agent_list", "agents": [live_agent(), second]}})
    calls = stub_response(monkeypatch, payload)

    agents = herdr_cli.list_agents("/bin/herdr", {})

    assert calls == [["/bin/herdr", "agent", "list"]]
    assert [agent.pane_id for agent in agents] == ["w9:p1", "w9:p2"]


def test_list_agents_names_the_offending_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    broken = live_agent()
    broken["terminal_id"] = None
    payload = json.dumps({"result": {"type": "agent_list", "agents": [live_agent(), broken]}})
    _ = stub_response(monkeypatch, payload)

    with pytest.raises(herdr_cli.HerdrError, match=r"agents\[1\] has no usable 'terminal_id'"):
        _ = herdr_cli.list_agents("/bin/herdr", {})


def test_list_workspaces_reads_every_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    second = live_workspace_listing()
    second["workspace_id"] = "w1P"
    second["number"] = 2
    payload = json.dumps(
        {"result": {"type": "workspace_list", "workspaces": [live_workspace_listing(), second]}}
    )
    calls = stub_response(monkeypatch, payload)

    workspaces = herdr_cli.list_workspaces("/bin/herdr", {})

    assert calls == [["/bin/herdr", "workspace", "list"]]
    assert [workspace.workspace_id for workspace in workspaces] == ["w9", "w1P"]
    assert workspaces[0].active_tab_id == "w9:t1"
    assert workspaces[0].pane_count == 2
    assert workspaces[0].tokens == {}
    assert workspaces[0].worktree is None


def test_list_workspaces_names_the_offending_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    broken = live_workspace_listing()
    del broken["active_tab_id"]
    payload = json.dumps(
        {"result": {"type": "workspace_list", "workspaces": [live_workspace_listing(), broken]}}
    )
    _ = stub_response(monkeypatch, payload)

    with pytest.raises(
        herdr_cli.HerdrError, match=r"workspaces\[1\] has no usable 'active_tab_id'"
    ):
        _ = herdr_cli.list_workspaces("/bin/herdr", {})


def test_prompt_agent_sends_wait_flags_only_when_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps({"result": {"type": "agent_prompted", "agent": live_agent()}})
    calls = stub_response(monkeypatch, payload)

    agent = herdr_cli.prompt_agent(
        "/bin/herdr",
        {},
        "impl",
        "status?",
        wait=True,
        until=("idle", "blocked"),
        timeout_ms=120000,
    )

    assert calls == [
        [
            "/bin/herdr",
            "agent",
            "prompt",
            "impl",
            "status?",
            "--wait",
            "--until",
            "idle",
            "--until",
            "blocked",
            "--timeout",
            "120000",
        ]
    ]
    assert agent.pane_id == "w9:p1"


def test_prompt_agent_omits_wait_flags_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"result": {"type": "agent_prompted", "agent": live_agent()}})
    calls = stub_response(monkeypatch, payload)

    _ = herdr_cli.prompt_agent("/bin/herdr", {}, "impl", "hi")

    assert calls == [["/bin/herdr", "agent", "prompt", "impl", "hi"]]


def test_prompt_agent_refuses_until_without_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = stub_response(monkeypatch, "{}")

    with pytest.raises(herdr_cli.UsageError, match="require wait"):
        _ = herdr_cli.prompt_agent("/bin/herdr", {}, "impl", "hi", until=("idle",))
    assert calls == []


def test_prompt_agent_names_a_missing_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    _ = stub_response(monkeypatch, json.dumps({"result": {"type": "agent_prompted"}}))

    with pytest.raises(herdr_cli.HerdrError, match=r"result\.agent"):
        _ = herdr_cli.prompt_agent("/bin/herdr", {}, "impl", "hi")


def test_rename_pane_sends_the_label_and_returns_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = stub_response(monkeypatch, json.dumps({"result": {"type": "ok"}}))

    assert herdr_cli.rename_pane("/bin/herdr", {}, "w9:p1", "impl") is None
    assert calls == [["/bin/herdr", "pane", "rename", "w9:p1", "impl"]]


def test_rename_agent_sends_the_name_and_returns_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = stub_response(monkeypatch, json.dumps({"result": {"type": "ok"}}))

    assert herdr_cli.rename_agent("/bin/herdr", {}, "w9:p1", "impl") is None
    assert calls == [["/bin/herdr", "agent", "rename", "w9:p1", "impl"]]


def test_wait_pane_output_reads_the_output_matched_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps({"result": {"type": "output_matched", **live_match()}})
    calls = stub_response(monkeypatch, payload)

    match = herdr_cli.wait_pane_output("/bin/herdr", {}, "w9:p1", "READY", timeout_ms=5000)

    assert calls == [
        ["/bin/herdr", "pane", "wait-output", "w9:p1", "--match", "READY", "--timeout", "5000"]
    ]
    assert match.matched_line == "READY"
    assert match.read.text == "READY\n"
    assert match.read.truncated is False


def test_wait_pane_output_uses_regex_and_snapshot_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps({"result": {"type": "output_matched", **live_match()}})
    calls = stub_response(monkeypatch, payload)

    _ = herdr_cli.wait_pane_output(
        "/bin/herdr",
        {},
        "w9:p1",
        "READY|DONE",
        regex=True,
        source="visible",
        lines=40,
        raw_output=True,
    )

    assert calls == [
        [
            "/bin/herdr",
            "pane",
            "wait-output",
            "w9:p1",
            "--regex",
            "READY|DONE",
            "--source",
            "visible",
            "--lines",
            "40",
            "--raw",
        ]
    ]


def test_wait_pane_output_names_a_missing_read(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps({"result": {"type": "output_matched", "pane_id": "w9:p1", "revision": 12}})
    _ = stub_response(monkeypatch, payload)

    with pytest.raises(herdr_cli.HerdrError, match=r"result\.read"):
        _ = herdr_cli.wait_pane_output("/bin/herdr", {}, "w9:p1", "READY")


def test_wait_pane_output_admits_an_empty_snapshot_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    match = live_match()
    match["read"] = {**live_read(), "text": ""}
    _ = stub_response(monkeypatch, json.dumps({"result": {"type": "output_matched", **match}}))

    found = herdr_cli.wait_pane_output("/bin/herdr", {}, "w9:p1", "READY")

    assert found.read.text == ""


def test_wait_pane_output_names_a_missing_snapshot_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read = live_read()
    del read["text"]
    payload = json.dumps({"result": {"type": "output_matched", **live_match(), "read": read}})
    _ = stub_response(monkeypatch, payload)

    with pytest.raises(herdr_cli.HerdrError, match=r"result\.read has no usable 'text'"):
        _ = herdr_cli.wait_pane_output("/bin/herdr", {}, "w9:p1", "READY")


def test_run_in_pane_safe_sends_the_command_as_one_argv_element(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = stub_response(monkeypatch, json.dumps({"result": {"type": "ok"}}))

    herdr_cli.run_in_pane_safe("/bin/herdr", {}, "w9:p1", "printf 'a b' && echo $HOME | cat")

    assert calls == [["/bin/herdr", "pane", "run", "w9:p1", "printf 'a b' && echo $HOME | cat"]]


@pytest.mark.parametrize(
    "command",
    [
        pytest.param("echo one\necho two", id="newline"),
        pytest.param("echo one\recho two", id="carriage-return"),
        pytest.param("echo one\x00two", id="nul"),
        pytest.param("echo one\x1becho two", id="escape"),
    ],
)
def test_run_in_pane_safe_refuses_control_characters_before_any_call(
    monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    calls = stub_response(monkeypatch, json.dumps({"result": {"type": "ok"}}))

    with pytest.raises(herdr_cli.UsageError, match="control character"):
        herdr_cli.run_in_pane_safe("/bin/herdr", {}, "w9:p1", command)
    assert calls == []


@pytest.mark.parametrize("command", ["", "   ", "\t\n"])
def test_run_in_pane_safe_refuses_an_empty_command(
    monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    calls = stub_response(monkeypatch, json.dumps({"result": {"type": "ok"}}))

    with pytest.raises(herdr_cli.UsageError, match="empty"):
        herdr_cli.run_in_pane_safe("/bin/herdr", {}, "w9:p1", command)
    assert calls == []


def test_workspace_info_parses_the_required_fields() -> None:
    info = herdr_cli._workspace_info(live_workspace(), where="workspace")

    assert info.active_tab_id == "w9:t1"
    assert info.tab_count == 1
    assert info.worktree is not None
    assert info.worktree.repo_name == "harness"


def test_workspace_info_names_a_missing_required_field() -> None:
    workspace = live_workspace()
    del workspace["active_tab_id"]

    with pytest.raises(herdr_cli.HerdrError, match=r"no usable 'active_tab_id'"):
        _ = herdr_cli._workspace_info(workspace, where="workspace")
