"""Shared stub-`herdr` harness for the herdr skill tests.

Import as ``tests.herdr.stub``: pytest's ``pythonpath = ["."]`` puts the project root on
``sys.path``, and ``tests.herdr`` resolves as a namespace package. A plain ``import stub``
would be implicitly relative and break if a test file is imported as a module.
"""

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

SCRIPTS_DIR = (Path(__file__).parent.parent.parent / "skills" / "herdr" / "scripts").resolve()

STUB_SOURCE = '''#!/usr/bin/env python3
"""Fake herdr for tests: append argv to STUB_HERDR_LOG, replay STUB_HERDR_STATE."""

import json
import os
import sys
from pathlib import Path

argv = sys.argv
with Path(os.environ["STUB_HERDR_LOG"]).open("a") as log:
    log.write(json.dumps(argv) + "\\n")
args = argv[1:]

state = json.loads(Path(os.environ["STUB_HERDR_STATE"]).read_text())

if args[:2] == ["pane", "current"]:
    print(json.dumps({"result": {"pane": {"pane_id": state["current"]}}}))
    raise SystemExit(0)

if args[:2] == ["pane", "layout"]:
    pane_id = args[args.index("--pane") + 1]
    print(json.dumps({"result": {"layout": {"panes": [{"pane_id": pane_id, "rect": state["rect"]}]}}}))
    raise SystemExit(0)

if args[:2] == ["pane", "split"]:
    if state.get("split_error"):
        print(json.dumps({"error": state["split_error"]}), file=sys.stderr)
        raise SystemExit(1)
    pane = state.get("split_pane", {"pane_id": "w9:pNEW", "tab_id": "w9:t1", "cwd": "/tmp"})
    print(json.dumps({"result": {"pane": pane}}))
    raise SystemExit(0)

if args[:2] == ["pane", "list"]:
    payload = {"id": "cli:pane:list", "result": {"panes": state["panes"], "type": "pane_list"}}
    print(json.dumps(payload))
    raise SystemExit(0)

if args[:2] == ["agent", "list"]:
    payload = {"id": "cli:agent:list", "result": {"agents": state.get("agents", []), "type": "agent_list"}}
    print(json.dumps(payload))
    raise SystemExit(0)

if args[:2] == ["workspace", "list"]:
    agents = state.get("workspaces", [])
    payload = {"id": "cli:workspace:list", "result": {"workspaces": agents, "type": "workspace_list"}}
    print(json.dumps(payload))
    raise SystemExit(0)

if args[:2] == ["pane", "rename"]:
    if state.get("pane_rename_error"):
        print(json.dumps({"error": state["pane_rename_error"], "id": "cli:pane:rename"}), file=sys.stderr)
        raise SystemExit(1)
    pane_id = args[2]
    label = None if "--clear" in args else " ".join(args[3:])
    payload = {"id": "cli:pane:rename", "result": {"pane": {"pane_id": pane_id, "label": label}}}
    print(json.dumps(payload))
    raise SystemExit(0)

if args[:2] == ["agent", "rename"]:
    if state.get("agent_rename_error"):
        print(json.dumps({"error": state["agent_rename_error"], "id": "cli:agent:rename"}), file=sys.stderr)
        raise SystemExit(1)
    target = args[2]
    name = None if "--clear" in args else args[3]
    payload = {"id": "cli:agent:rename", "result": {"agent": {"pane_id": target, "name": name}}}
    print(json.dumps(payload))
    raise SystemExit(0)

if args[:2] == ["agent", "prompt"]:
    if state.get("prompt_error"):
        print(json.dumps({"error": state["prompt_error"], "id": "cli:agent:prompt"}), file=sys.stderr)
        raise SystemExit(1)
    agent = {"agent": "pi", "agent_status": state.get("prompt_status", "idle")}
    print(json.dumps({"id": "cli:agent:prompt", "result": {"agent": agent, "type": "agent_prompted"}}))
    raise SystemExit(0)
if args[:2] == ["agent", "get"]:
    target = args[2] if len(args) > 2 else ""
    if state.get("agent_get_error"):
        print(json.dumps({"error": state["agent_get_error"], "id": "cli:agent:get"}), file=sys.stderr)
        raise SystemExit(1)
    seq = state.get("agent_get_seq", {}).get(target)
    static = state.get("agent_get", {}).get(target, {})
    if seq is not None:
        prior = -1
        try:
            with Path(os.environ["STUB_HERDR_LOG"]).open() as log:
                for line in log:
                    try:
                        logged = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if logged[1:4] == ["agent", "get", target]:
                        prior += 1
        except FileNotFoundError:
            prior = 0
        status = seq[min(max(prior, 0), len(seq) - 1)]
    else:
        status = static.get("agent_status", "working")
    agent = {
        "name": target,
        "agent": "pi",
        "agent_status": status,
        "revision": static.get("revision", "r1"),
    }
    if static.get("session"):
        agent["agent_session"] = {"kind": "path", "value": static["session"]}
    print(json.dumps({"id": "cli:agent:get", "result": {"agent": agent, "type": "agent"}}))
    raise SystemExit(0)

print(json.dumps({"error": "unexpected argv: " + " ".join(args)}), file=sys.stderr)
raise SystemExit(1)
'''

DEFAULT_STATE = {
    "current": "w9:p1",
    "rect": {"width": 100, "height": 40},
    "workspaces": [{"workspace_id": "w9", "label": "harness", "number": 1}],
    "agents": [{"pane_id": "w9:p1", "name": "reviewer", "agent": "pi", "agent_status": "working"}],
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
            "pane_id": "w9:p2",
            "tab_id": "w9:t1",
            "workspace_id": "w9",
            "agent": None,
            "agent_status": "unknown",
            "cwd": "/tmp/scratch",
            "label": "scratch pad",
        },
    ],
}


@dataclass(frozen=True)
class StubHarness:
    """A temp PATH containing a fake `herdr`, plus the run/log helpers around it."""

    script: Path
    tmp_path: Path
    bin_dir: Path
    log_path: Path
    state_path: Path

    @property
    def herdr(self) -> Path:
        return self.bin_dir / "herdr"

    def calls(self) -> list[list[str]]:
        if not self.log_path.exists():
            return []
        return [json.loads(line) for line in self.log_path.read_text().splitlines() if line]

    def splits(self) -> list[list[str]]:
        return [call for call in self.calls() if call[1:3] == ["pane", "split"]]

    def prompts(self) -> list[list[str]]:
        return [call for call in self.calls() if call[1:3] == ["agent", "prompt"]]

    def run(
        self,
        *args: str,
        state: Mapping[str, object] | None = None,
        env: Mapping[str, str | None] | None = None,
        stdin: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        _ = self.state_path.write_text(
            json.dumps(dict(state if state is not None else DEFAULT_STATE))
        )
        full_env: dict[str, str] = {
            "PATH": f"{self.bin_dir}:{os.environ.get('PATH', '')}",
            "HERDR_ENV": "1",
            "PWD": str(self.tmp_path),
            "STUB_HERDR_LOG": str(self.log_path),
            "STUB_HERDR_STATE": str(self.state_path),
        }
        for key, value in (env or {}).items():
            if value is None:
                _ = full_env.pop(key, None)
            else:
                full_env[key] = value
        argv = [sys.executable, str(self.script), *args]
        if stdin is None:
            return subprocess.run(
                argv,
                capture_output=True,
                text=True,
                env=full_env,
                check=False,
                stdin=subprocess.DEVNULL,
            )
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            env=full_env,
            check=False,
            input=stdin,
        )


def flag_value(call: list[str], flag: str) -> str:
    return call[call.index(flag) + 1]
