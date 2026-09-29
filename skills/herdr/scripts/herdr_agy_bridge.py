#!/usr/bin/env python3
# /// script
# requires-python = ">=3.14"
# dependencies = []
# ///
"""herdr-agy-bridge — managed installation of the Antigravity (agy) lifecycle bridge.

`agy` panes are weakly recognized by Herdr: the revision stays 0 and the status
bar reads stale WORKING after a settle, so barriers and prompt checks cannot
trust the state feed. Antigravity CLI ships real lifecycle hooks (global
`~/.gemini/config/hooks.json`, project `.agents/hooks.json`); this helper
installs the bridge into them so every agy pane writes trustworthy OSC 0 titles
that Herdr's screen detection reads:

    Stop        payload `fullyIdle` true or absent -> `agy: idle`
                `fullyIdle` false                  -> `agy: working (subagents)`
    PreToolUse  matcher `ask_permission` fires                -> `agy: blocked (permission)`

    uv run "$SKILL_DIR/scripts/herdr_agy_bridge.py" --install             # global
    uv run "$SKILL_DIR/scripts/herdr_agy_bridge.py" --install --project   # ./.agents/hooks.json
    uv run "$SKILL_DIR/scripts/herdr_agy_bridge.py" --status
    uv run "$SKILL_DIR/scripts/herdr_agy_bridge.py" --uninstall

Installs are idempotent: the managed entries (identified by the deployed
`herdr-agy-bridge.sh` command) are replaced, never duplicated, and unrelated
hooks in the same file are preserved. The bridge script is deployed next to the
hooks file under `hooks/` (e.g. `~/.gemini/config/hooks/herdr-agy-bridge.sh`).
`--hooks PATH` points at a different hooks.json; the script lands beside it in
`hooks/`. Uninstall removes only the managed entries and the deployed script.

Exit status: 0 done (or installed, for --status), 1 not-installed or
misconfigured (--status) / file failure, 2 usage or missing precondition.

Local addition to the absorbed upstream Herdr skill; not part of ``herdrdev/herdr``.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

# Intended flat sibling import: `uv run <script>.py` puts the script directory on sys.path.
from herdr_cli import EXIT_HERDR, EXIT_OK, HerdrError, UsageError, guard

BRIDGE_SCRIPT_NAME = "herdr-agy-bridge.sh"
BRIDGE_MARKER = "herdr-agy-bridge.sh"
SCRIPT_MARKER = "HERDR_INTEGRATION_ID=herdr_agy_bridge"
HERDR_GROUP = "herdr"
STOP_EVENT = "Stop"
PRE_TOOL_EVENT = "PreToolUse"
PERMISSION_MATCHER = "ask_permission"
HOOK_TIMEOUT_S = 10

BRIDGE_SCRIPT = """#!/bin/sh
# installed by herdr_agy_bridge.py
# managed by herdr; --install updates this file; edit custom hooks beside it instead.
# HERDR_INTEGRATION_ID=herdr_agy_bridge
# HERDR_INTEGRATION_VERSION=1

# AGY lifecycle bridge: map Antigravity hook events onto OSC 0 pane titles that
# Herdr's screen detection reads, because agy reports revision 0 forever.

set -eu

mode="${1:-}"

emit() {
  # HERDR_AGY_BRIDGE_TTY redirects the title escape for tests; hooks run against a tty.
  (printf '\\033]0;%s\\007' "$1" > "${HERDR_AGY_BRIDGE_TTY:-/dev/tty}") 2>/dev/null || true
}

payload=""
if [ ! -t 0 ]; then
  payload="$(cat 2>/dev/null || true)"
fi

case "$mode" in
  stop)
    if printf '%s' "$payload" | grep -Eq '"fullyIdle"[[:space:]]*:[[:space:]]*false'; then
      emit "agy: working (subagents)"
    else
      emit "agy: idle"
    fi
    ;;
  permission)
    emit "agy: blocked (permission)"
    ;;
esac

# Antigravity parses stdout as a hook JSON object; {} accepts without steering.
printf '{}\\n'
exit 0
"""


class Options:
    """CLI options; `argparse` writes into this typed namespace."""

    install: bool = False
    uninstall: bool = False
    status: bool = False
    global_: bool = False
    project: bool = False
    hooks: str | None = None
    json: bool = False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="herdr-agy-bridge",
        description="Install, inspect, or remove the managed agy lifecycle bridge hooks.",
        epilog="exit status: 0 done or installed, 1 not-installed or misconfigured, 2 usage",
    )
    action = parser.add_mutually_exclusive_group(required=True)
    _ = action.add_argument("--install", action="store_true", help="install or update the bridge")
    _ = action.add_argument(
        "--uninstall", action="store_true", help="remove managed entries and script"
    )
    _ = action.add_argument(
        "--status", action="store_true", help="check whether the bridge is active"
    )
    scope = parser.add_mutually_exclusive_group()
    _ = scope.add_argument(
        "--global",
        dest="global_",
        action="store_true",
        help="target ~/.gemini/config/hooks.json (default)",
    )
    _ = scope.add_argument(
        "--project",
        action="store_true",
        help="target the repo's .agents/hooks.json",
    )
    _ = parser.add_argument(
        "--hooks",
        metavar="PATH",
        help="explicit hooks.json path; the bridge script deploys into hooks/ beside it",
    )
    _ = parser.add_argument("--json", action="store_true", help="machine-readable status report")
    return parser


def resolve_hooks_path(options: Options, env: Mapping[str, str]) -> Path:
    if options.hooks:
        return Path(options.hooks).expanduser()
    if options.project:
        return Path.cwd() / ".agents" / "hooks.json"
    home = Path(env.get("HOME") or Path.home())
    return home / ".gemini" / "config" / "hooks.json"


def bridge_script_path(hooks_path: Path) -> Path:
    return hooks_path.parent / "hooks" / BRIDGE_SCRIPT_NAME


def load_hooks(hooks_path: Path) -> dict[str, object]:
    if not hooks_path.exists():
        return {}
    try:
        raw = hooks_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise HerdrError(f"cannot read {hooks_path}: {exc}") from exc
    if not raw.strip():
        return {}
    try:
        decoded: object = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HerdrError(f"{hooks_path} is not valid JSON: {exc}") from exc
    if not isinstance(decoded, dict):
        raise HerdrError(f"{hooks_path} is not a JSON object")
    return {str(key): value for key, value in decoded.items()}


def write_hooks(hooks_path: Path, data: Mapping[str, object]) -> None:
    try:
        hooks_path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=hooks_path.parent, prefix=".herdr-hooks-")
        tmp = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                _ = handle.write(json.dumps(data, indent=2, sort_keys=True) + "\n")
            _ = tmp.replace(hooks_path)
        except OSError:
            _ = tmp.unlink(missing_ok=True)
            raise
    except OSError as exc:
        raise HerdrError(f"cannot write {hooks_path}: {exc}") from exc


def deploy_script(script_path: Path) -> bool:
    """Write the bridge script; returns True when the file changed."""
    if script_path.exists() and script_path.read_text(encoding="utf-8") == BRIDGE_SCRIPT:
        _ = script_path.chmod(
            script_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        )
        return False
    try:
        script_path.parent.mkdir(parents=True, exist_ok=True)
        _ = script_path.write_text(BRIDGE_SCRIPT, encoding="utf-8")
        _ = script_path.chmod(0o755)
    except OSError as exc:
        raise HerdrError(f"cannot deploy {script_path}: {exc}") from exc
    return True


def is_managed_hook(hook: object) -> bool:
    return isinstance(hook, dict) and BRIDGE_MARKER in str(hook.get("command", ""))


def prune_managed(entries: object) -> tuple[list[object], int]:
    """Drop managed hooks from Stop lists or PreToolUse matcher groups."""
    if not isinstance(entries, list):
        return [], 0
    kept: list[object] = []
    removed = 0
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("hooks"), list):
            hooks, entry_removed = prune_managed(entry["hooks"])
            if entry_removed == 0:
                kept.append(entry)
            elif hooks:
                kept.append({**entry, "hooks": hooks})
            removed += entry_removed
        elif is_managed_hook(entry):
            removed += 1
        else:
            kept.append(entry)
    return kept, removed


def install_bridge(hooks_path: Path) -> int:
    script_path = bridge_script_path(hooks_path)
    data = load_hooks(hooks_path)
    group_raw = data.get(HERDR_GROUP)
    group: dict[str, object] = dict(group_raw) if isinstance(group_raw, dict) else {}

    stop_kept, stop_removed = prune_managed(group.get(STOP_EVENT))
    pretool_kept, pretool_removed = prune_managed(group.get(PRE_TOOL_EVENT))
    stop_command = f"bash '{script_path}' stop"
    permission_command = f"bash '{script_path}' permission"
    group[STOP_EVENT] = [
        *stop_kept,
        {"type": "command", "command": stop_command, "timeout": HOOK_TIMEOUT_S},
    ]
    managed_permission = {
        "type": "command",
        "command": permission_command,
        "timeout": HOOK_TIMEOUT_S,
    }
    merged: list[object] = []
    merged_into_existing = False
    for entry in pretool_kept:
        if (
            isinstance(entry, dict)
            and entry.get("matcher") == PERMISSION_MATCHER
            and not merged_into_existing
        ):
            hooks = entry.get("hooks")
            hooks_list = list(hooks) if isinstance(hooks, list) else []
            merged.append({**entry, "hooks": [*hooks_list, managed_permission]})
            merged_into_existing = True
        else:
            merged.append(entry)
    if not merged_into_existing:
        merged.append({"matcher": PERMISSION_MATCHER, "hooks": [managed_permission]})
    group[PRE_TOOL_EVENT] = merged
    data[HERDR_GROUP] = group
    _ = write_hooks(hooks_path, data)
    deployed = deploy_script(script_path)

    verb = "updated" if stop_removed or pretool_removed else "installed"
    print(f"herdr-agy-bridge: {verb} managed hooks in {hooks_path}")
    print(
        f"herdr-agy-bridge:   Stop        -> agy: idle / agy: working (subagents)  [{stop_command}]"
    )
    print(
        f"herdr-agy-bridge:   PreToolUse (matcher {PERMISSION_MATCHER}) -> "
        f"agy: blocked (permission)  [{permission_command}]"
    )
    if deployed:
        print(f"herdr-agy-bridge: deployed bridge script {script_path}")
    else:
        print(f"herdr-agy-bridge: bridge script already current at {script_path}")
    return EXIT_OK


def uninstall_bridge(hooks_path: Path) -> int:
    script_path = bridge_script_path(hooks_path)
    removed = 0
    if hooks_path.exists():
        data = load_hooks(hooks_path)
        group_raw = data.get(HERDR_GROUP)
        if isinstance(group_raw, dict):
            group = dict(group_raw)
            for event in (STOP_EVENT, PRE_TOOL_EVENT):
                kept, event_removed = prune_managed(group.get(event))
                removed += event_removed
                if kept:
                    group[event] = kept
                else:
                    _ = group.pop(event, None)
            if group:
                data[HERDR_GROUP] = group
            else:
                _ = data.pop(HERDR_GROUP, None)
        if removed:
            _ = write_hooks(hooks_path, data)
    script_removed = False
    if script_path.exists():
        managed = False
        try:
            managed = SCRIPT_MARKER in script_path.read_text(encoding="utf-8")
        except OSError:
            managed = False
        if managed:
            try:
                _ = script_path.unlink()
                script_removed = True
            except OSError as exc:
                raise HerdrError(f"cannot remove {script_path}: {exc}") from exc
        else:
            print(
                f"herdr-agy-bridge: warning: {script_path} is not the managed script; left in place",
                file=sys.stderr,
            )
    if not hooks_path.exists() and not script_removed and removed == 0:
        print("herdr-agy-bridge: nothing installed; no action taken")
        return EXIT_OK
    print(f"herdr-agy-bridge: removed {removed} managed hook entries from {hooks_path}")
    if script_removed:
        print(f"herdr-agy-bridge: removed bridge script {script_path}")
    return EXIT_OK


def find_managed_entries(data: Mapping[str, object]) -> tuple[bool, bool]:
    """Return (has_stop, has_permission) for managed hooks anywhere in the file."""
    has_stop = False
    has_permission = False
    for group_raw in data.values():
        if not isinstance(group_raw, dict):
            continue
        stop_entries = group_raw.get(STOP_EVENT)
        if isinstance(stop_entries, list) and any(is_managed_hook(h) for h in stop_entries):
            has_stop = True
        pretool = group_raw.get(PRE_TOOL_EVENT)
        if isinstance(pretool, list):
            for matcher_group in pretool:
                if not isinstance(matcher_group, dict):
                    continue
                hooks = matcher_group.get("hooks")
                if isinstance(hooks, list) and any(is_managed_hook(h) for h in hooks):
                    has_permission = True
    return has_stop, has_permission


def status_bridge(hooks_path: Path, *, as_json: bool) -> int:
    script_path = bridge_script_path(hooks_path)
    problems: list[str] = []
    data: dict[str, object] = {}
    parsed = False
    if not hooks_path.exists():
        problems.append(f"hooks file missing: {hooks_path}")
    else:
        try:
            data = load_hooks(hooks_path)
            parsed = True
        except HerdrError as exc:
            problems.append(str(exc))
    if parsed:
        has_stop, has_permission = find_managed_entries(data)
        if not has_stop:
            problems.append(f"managed {STOP_EVENT} hook not present")
        if not has_permission:
            problems.append(f"managed {PRE_TOOL_EVENT} permission hook not present")
    if not script_path.exists():
        problems.append(f"bridge script missing: {script_path}")
    elif not os.access(script_path, os.X_OK):
        problems.append(f"bridge script not executable: {script_path}")
    installed = not problems
    if as_json:
        print(
            json.dumps(
                {
                    "installed": installed,
                    "hooks_path": str(hooks_path),
                    "script_path": str(script_path),
                    "problems": problems,
                },
                indent=2,
            )
        )
    else:
        if installed:
            print(f"herdr-agy-bridge: installed and active at {hooks_path}")
            print(f"herdr-agy-bridge:   bridge script {script_path}")
        else:
            print("herdr-agy-bridge: NOT INSTALLED OR MISCONFIGURED", file=sys.stderr)
            for problem in problems:
                print(f"herdr-agy-bridge: {problem}", file=sys.stderr)
    return EXIT_OK if installed else EXIT_HERDR


def run(options: Options, env: Mapping[str, str]) -> int:
    if options.json and not options.status:
        raise UsageError("--json is only meaningful with --status")
    hooks_path = resolve_hooks_path(options, env)
    if options.install:
        return install_bridge(hooks_path)
    if options.uninstall:
        return uninstall_bridge(hooks_path)
    return status_bridge(hooks_path, as_json=options.json)


def main(argv: Sequence[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    env_map = dict(os.environ if env is None else env)
    options = build_parser().parse_args(argv, namespace=Options())
    return guard("herdr-agy-bridge", lambda: run(options, env_map))


if __name__ == "__main__":
    raise SystemExit(main())
