"""Tests for skills/herdr/scripts/herdr_agy_bridge.py (managed agy bridge installer).

Every case passes an explicit `--hooks` path under tmp_path; no test touches the
real ~/.gemini configuration.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import cast

import herdr_agy_bridge
import herdr_cli
import pytest

from tests.herdr.stub import SCRIPTS_DIR

SCRIPT = SCRIPTS_DIR / "herdr_agy_bridge.py"


def run(*args: str, env_home: str | None = None) -> subprocess.CompletedProcess[str]:
    home = env_home if env_home is not None else "/nonexistent-home"
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
        env={"HOME": home, "PATH": os.environ.get("PATH", "")},
    )


def hooks_file(tmp_path: Path) -> Path:
    return tmp_path / "config" / "hooks.json"


def install(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return run("--install", "--hooks", str(hooks_file(tmp_path)))


def read_hooks(tmp_path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(hooks_file(tmp_path).read_text()))


def herdr_group(tmp_path: Path) -> dict[str, object]:
    group = read_hooks(tmp_path)["herdr"]
    assert isinstance(group, dict)
    return group


def managed_count(group: dict[str, object], event: str) -> int:
    entries = group.get(event)
    assert isinstance(entries, list)
    count = 0
    for entry in entries:
        assert isinstance(entry, dict)
        hooks = entry.get("hooks")
        if isinstance(hooks, list):
            count += sum(
                1
                for hook in hooks
                if isinstance(hook, dict) and "herdr-agy-bridge.sh" in str(hook.get("command", ""))
            )
        elif "herdr-agy-bridge.sh" in str(entry.get("command", "")):
            count += 1
    return count


# ── unit: pure helpers ──────────────────────────────────────────────────────────


def test_prune_managed_removes_only_marked_hooks() -> None:
    entries: list[object] = [
        {"type": "command", "command": "bash '/x/herdr-agy-bridge.sh' stop"},
        {"type": "command", "command": "./mine.sh"},
    ]
    kept, removed = herdr_agy_bridge.prune_managed(entries)
    assert removed == 1
    assert kept == [{"type": "command", "command": "./mine.sh"}]


def test_prune_managed_drops_empty_matcher_group() -> None:
    entries: list[object] = [
        {
            "matcher": "ask_permission",
            "hooks": [{"type": "command", "command": "bash '/x/herdr-agy-bridge.sh' permission"}],
        },
        {"matcher": "run_command", "hooks": [{"type": "command", "command": "./gate.sh"}]},
    ]
    kept, removed = herdr_agy_bridge.prune_managed(entries)
    assert removed == 1
    assert kept == [entries[1]]


# ── integration: install ────────────────────────────────────────────────────────


def herdr_entries(group: dict[str, object], event: str) -> list[object]:
    entries = group.get(event)
    assert isinstance(entries, list)
    return entries


def test_install_writes_stop_and_permission_hooks(tmp_path: Path) -> None:
    done = install(tmp_path)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    group = herdr_group(tmp_path)
    (stop,) = herdr_entries(group, "Stop")
    assert isinstance(stop, dict)
    assert stop["type"] == "command"
    assert stop["timeout"] == 10
    assert str(stop["command"]).startswith("bash '")
    assert str(stop["command"]).endswith("herdr-agy-bridge.sh' stop")
    (permission_group,) = herdr_entries(group, "PreToolUse")
    assert isinstance(permission_group, dict)
    assert permission_group["matcher"] == "ask_permission"
    hooks = permission_group["hooks"]
    assert isinstance(hooks, list)
    (permission_hook,) = hooks
    assert isinstance(permission_hook, dict)
    assert "permission" in str(permission_hook["command"])
    assert "herdr-agy-bridge: installed managed hooks" in done.stdout


def test_install_deploys_executable_bridge_script(tmp_path: Path) -> None:
    done = install(tmp_path)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    script = herdr_agy_bridge.bridge_script_path(hooks_file(tmp_path))
    assert script.exists()
    assert os.access(script, os.X_OK)
    content = script.read_text()
    assert "HERDR_INTEGRATION_ID=herdr_agy_bridge" in content
    assert "fullyIdle" in content
    assert "\\033]0;" in content  # OSC 0 title escape


def test_reinstall_updates_without_duplicates(tmp_path: Path) -> None:
    first = install(tmp_path)
    assert first.returncode == herdr_cli.EXIT_OK, first.stderr
    second = install(tmp_path)
    assert second.returncode == herdr_cli.EXIT_OK, second.stderr
    assert "updated managed hooks" in second.stdout
    group = herdr_group(tmp_path)
    assert managed_count(group, "Stop") == 1
    assert managed_count(group, "PreToolUse") == 1


def test_install_preserves_unrelated_hooks(tmp_path: Path) -> None:
    hooks_path = hooks_file(tmp_path)
    _ = hooks_path.parent.mkdir(parents=True)
    seed = {
        "herdr": {
            "PreInvocation": [
                {
                    "type": "command",
                    "command": "bash '.../herdr-agent-state.sh' session",
                    "timeout": 10,
                }
            ]
        },
        "safety-gate": {
            "PreToolUse": [
                {
                    "matcher": "run_command",
                    "hooks": [{"type": "command", "command": "./scripts/safety-check.sh"}],
                }
            ]
        },
    }
    _ = hooks_path.write_text(json.dumps(seed))
    done = install(tmp_path)
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    data = read_hooks(tmp_path)
    assert isinstance(data["safety-gate"], dict)
    group = cast(dict[str, object], data["herdr"])
    assert len(herdr_entries(group, "PreInvocation")) == 1
    assert managed_count(group, "Stop") == 1


def test_install_and_uninstall_preserve_same_group_siblings(tmp_path: Path) -> None:
    """A foreign hook sharing the managed Stop list or ask_permission matcher group must survive."""
    hooks_path = hooks_file(tmp_path)
    _ = hooks_path.parent.mkdir(parents=True)
    foreign_stop = {"type": "command", "command": "./notify.sh", "timeout": 5}
    foreign_permission = {"type": "command", "command": "./gate.sh", "timeout": 5}
    seed = {
        "herdr": {
            "Stop": [foreign_stop],
            "PreToolUse": [{"matcher": "ask_permission", "hooks": [foreign_permission]}],
        }
    }
    _ = hooks_path.write_text(json.dumps(seed))
    assert install(tmp_path).returncode == herdr_cli.EXIT_OK
    group = herdr_group(tmp_path)
    stop_entries = group["Stop"]
    assert isinstance(stop_entries, list)
    assert foreign_stop in stop_entries
    assert managed_count(group, "Stop") == 1
    assert managed_count(group, "PreToolUse") == 1
    matchers = group["PreToolUse"]
    assert isinstance(matchers, list)
    permission_groups = [
        m for m in matchers if isinstance(m, dict) and m.get("matcher") == "ask_permission"
    ]
    assert len(permission_groups) == 1
    hooks = permission_groups[0]["hooks"]
    assert isinstance(hooks, list)
    assert foreign_permission in hooks

    done = run("--uninstall", "--hooks", str(hooks_path))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    group = herdr_group(tmp_path)
    assert group["Stop"] == [foreign_stop]
    assert managed_count(group, "PreToolUse") == 0
    matchers = group["PreToolUse"]
    assert isinstance(matchers, list)
    assert any(
        isinstance(m, dict)
        and m.get("matcher") == "ask_permission"
        and m.get("hooks") == [foreign_permission]
        for m in matchers
    )


# ── integration: status ─────────────────────────────────────────────────────────


def test_status_installed_exits_zero(tmp_path: Path) -> None:
    assert install(tmp_path).returncode == herdr_cli.EXIT_OK
    done = run("--status", "--hooks", str(hooks_file(tmp_path)))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "installed and active" in done.stdout


def test_status_json_reports_installed(tmp_path: Path) -> None:
    assert install(tmp_path).returncode == herdr_cli.EXIT_OK
    done = run("--status", "--json", "--hooks", str(hooks_file(tmp_path)))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    report = json.loads(done.stdout)
    assert report["installed"] is True
    assert report["problems"] == []


def test_status_missing_file_is_not_installed(tmp_path: Path) -> None:
    done = run("--status", "--hooks", str(hooks_file(tmp_path)))
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "hooks file missing" in done.stderr


def test_status_corrupt_json_is_misconfigured(tmp_path: Path) -> None:
    hooks_path = hooks_file(tmp_path)
    _ = hooks_path.parent.mkdir(parents=True)
    _ = hooks_path.write_text("not json {{{")
    done = run("--status", "--hooks", str(hooks_path))
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "not valid JSON" in done.stderr


def test_status_missing_script_is_misconfigured(tmp_path: Path) -> None:
    assert install(tmp_path).returncode == herdr_cli.EXIT_OK
    _ = herdr_agy_bridge.bridge_script_path(hooks_file(tmp_path)).unlink()
    done = run("--status", "--hooks", str(hooks_file(tmp_path)))
    assert done.returncode == herdr_cli.EXIT_HERDR
    assert "bridge script missing" in done.stderr


# ── integration: uninstall ──────────────────────────────────────────────────────


def test_uninstall_removes_only_managed_entries(tmp_path: Path) -> None:
    hooks_path = hooks_file(tmp_path)
    _ = hooks_path.parent.mkdir(parents=True)
    unrelated = {"type": "command", "command": "./keep-me.sh", "timeout": 5}
    seed = {
        "herdr": {"PreInvocation": [unrelated]},
        "safety-gate": {"PreToolUse": [{"matcher": "run_command", "hooks": [unrelated]}]},
    }
    _ = hooks_path.write_text(json.dumps(seed))
    assert install(tmp_path).returncode == herdr_cli.EXIT_OK
    done = run("--uninstall", "--hooks", str(hooks_path))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    data = read_hooks(tmp_path)
    group = cast(dict[str, object], data["herdr"])
    assert "Stop" not in group
    assert "PreToolUse" not in group
    assert group["PreInvocation"] == [unrelated]
    assert data["safety-gate"] == seed["safety-gate"]
    assert not herdr_agy_bridge.bridge_script_path(hooks_path).exists()
    assert "removed 2 managed hook entries" in done.stdout


def test_uninstall_is_noop_when_absent(tmp_path: Path) -> None:
    done = run("--uninstall", "--hooks", str(hooks_file(tmp_path)))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert "nothing installed" in done.stdout


def test_uninstall_keeps_foreign_script(tmp_path: Path) -> None:
    assert install(tmp_path).returncode == herdr_cli.EXIT_OK
    script = herdr_agy_bridge.bridge_script_path(hooks_file(tmp_path))
    _ = script.write_text("#!/bin/sh\n# someone else's script\n")
    done = run("--uninstall", "--hooks", str(hooks_file(tmp_path)))
    assert done.returncode == herdr_cli.EXIT_OK, done.stderr
    assert script.exists()
    assert "not the managed script" in done.stderr


# ── integration: deployed bridge script behavior ────────────────────────────────


def run_bridge(
    tmp_path: Path, mode: str, payload: str, *, tty_target: Path | None = None
) -> subprocess.CompletedProcess[str]:
    script = herdr_agy_bridge.bridge_script_path(hooks_file(tmp_path))
    env = {**os.environ}
    if tty_target is not None:
        env["HERDR_AGY_BRIDGE_TTY"] = str(tty_target)
    return subprocess.run(
        ["/bin/sh", str(script), mode],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def bridge_title(tmp_path: Path, mode: str, payload: str) -> str:
    tty = tmp_path / "tty-capture"
    done = run_bridge(tmp_path, mode, payload, tty_target=tty)
    assert done.returncode == 0, done.stderr
    return tty.read_text()


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ('{"fullyIdle": true}', "agy: idle"),
        ('{"fullyIdle": false}', "agy: working (subagents)"),
        ('{"fullyIdle":true}', "agy: idle"),
        ('{"fullyIdle":false}', "agy: working (subagents)"),
        ("{}", "agy: idle"),
        ("", "agy: idle"),
    ],
)
def test_bridge_stop_publishes_lifecycle_title(tmp_path: Path, payload: str, expected: str) -> None:
    """Swapping the idle/working titles must fail these tests: Herdr reads the OSC 0 text."""
    assert install(tmp_path).returncode == herdr_cli.EXIT_OK
    assert bridge_title(tmp_path, "stop", payload) == f"\033]0;{expected}\007"


def test_bridge_permission_publishes_blocked_title(tmp_path: Path) -> None:
    assert install(tmp_path).returncode == herdr_cli.EXIT_OK
    title = bridge_title(tmp_path, "permission", '{"tool": "ask_permission"}')
    assert title == "\033]0;agy: blocked (permission)\007"


def test_bridge_title_capture_path_is_configurable(tmp_path: Path) -> None:
    """Without the override the script must still exit 0 with no tty available."""
    assert install(tmp_path).returncode == herdr_cli.EXIT_OK
    done = run_bridge(tmp_path, "stop", '{"fullyIdle": true}')
    assert done.returncode == 0
    assert done.stderr == ""
    assert json.loads(done.stdout) == {}


# ── usage ───────────────────────────────────────────────────────────────────────


def test_requires_an_action(tmp_path: Path) -> None:
    done = run("--hooks", str(hooks_file(tmp_path)))
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "one of the arguments" in done.stderr or "--install" in done.stderr


def test_json_requires_status(tmp_path: Path) -> None:
    done = run("--install", "--json", "--hooks", str(hooks_file(tmp_path)))
    assert done.returncode == herdr_cli.EXIT_USAGE
    assert "--json is only meaningful with --status" in done.stderr


# ── metadata: PEP 723 conformance ────────────────────────────────────────────────


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
    assert "usage: herdr-agy-bridge" in done.stdout
