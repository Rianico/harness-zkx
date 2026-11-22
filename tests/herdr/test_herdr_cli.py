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
