"""Release-failure diagnostics: the watch must name the failing job › step and a log tail.

Regression for issue #283. The failure path used to call the exiting `fail` helper inside the
poll loop, so the diagnostics written below it could never run: a failed release printed one
bare conclusion line and exited (release run 39621268988). These cases drive the real scripts
against a scripted fake `gh` and a fake semantic-release, so the assertion is on the exact
output an operator sees — no network, no gh auth, no real waits.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GH_RELEASE = REPO_ROOT / "skills/gh-router/subskills/gh-release/scripts"
DISPATCH = GH_RELEASE / "dispatch.sh"
RELEASE_WATCH = GH_RELEASE / "release-watch.sh"

LOG_LINES = 500
JOBS_JSON = json.dumps(
    {
        "jobs": [
            {
                "name": "release",
                "conclusion": "failure",
                "steps": [
                    {"name": "checkout", "conclusion": "success"},
                    {"name": "dependency audit", "conclusion": "failure"},
                    {"name": "semantic-release", "conclusion": "skipped"},
                ],
            },
            {
                "name": "verify",
                "conclusion": "success",
                "steps": [{"name": "pytest", "conclusion": "success"}],
            },
        ]
    }
)

FAKE_GH = '''#!/usr/bin/env python3
"""Fake `gh` for release-watch fixtures: answers the exact argv the scripts issue."""
import json
import os
import sys

args = sys.argv[1:]
scenario = os.environ["FAKE_GH_SCENARIO"]
state_path = os.environ["FAKE_GH_STATE"]
jobs_json = os.environ["FAKE_GH_JOBS"]
log_count = int(os.environ.get("FAKE_GH_LOG_LINES", "500"))


def load_state():
    try:
        with open(state_path, encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def save_state(state):
    with open(state_path, "w", encoding="utf-8") as handle:
        json.dump(state, handle)


def log_body():
    for index in range(1, log_count + 1):
        print("LOG-%03d" % index)


if args[:2] == ["auth", "token"]:
    print("fake-token")
    sys.exit(0)

if args[:2] == ["run", "list"]:
    state = load_state()
    state["listed"] = state.get("listed", 0) + 1
    save_state(state)
    print("100" if state["listed"] == 1 else "101")
    sys.exit(0)

if args[:2] == ["run", "view"]:
    if "--log-failed" in args or "--log" in args:
        log_body()
        sys.exit(0)
    if "--json" in args:
        payload = args[args.index("--json") + 1]
        if payload == "status,conclusion":
            print("completed success" if scenario == "success" else "completed failure")
        elif "conclusion" in payload:
            print("success" if scenario == "success" else "failure")
        sys.exit(0)
    sys.exit(0)

if args and args[0] == "api":
    path = args[1]
    if path.endswith("/dispatches"):
        sys.exit(0)
    if "/jobs" in path:
        print(jobs_json)
        sys.exit(0)
    if "actions/workflows/release.yml/runs" in path:
        print("101")
        sys.exit(0)
    if "actions/runs/101" in path:
        jq = args[args.index("--jq") + 1] if "--jq" in args else ""
        if jq == ".status":
            print("completed")
        elif jq == ".conclusion":
            print("failure")
        elif jq == ".html_url":
            print("https://github.com/acme/widgets/actions/runs/101")
        sys.exit(0)

sys.exit(0)
'''

FAKE_NPX = """#!/usr/bin/env bash
echo "The next release version is 1.2.3"
echo "## 1.2.3"
echo "### Features"
echo "* add thing"
exit 0
"""


def _run(command: list[str], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    assert result.returncode == 0, f"{command} failed:\n{result.stdout}{result.stderr}"


def _release_repo(tmp_path: Path) -> Path:
    """Temp repo on `main` whose push remote parses to the acme/widgets slug."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _run(["git", "init", "-q", "-b", "main"], repo)
    _run(["git", "config", "user.email", "test@example.com"], repo)
    _run(["git", "config", "user.name", "Test"], repo)
    _run(["git", "remote", "add", "origin", "git@github.com:acme/widgets.git"], repo)
    _ = (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    _run(["git", "add", "README.md"], repo)
    _run(["git", "commit", "-qm", "chore: fixture"], repo)
    return repo


def _fake_env(tmp_path: Path, scenario: str) -> dict[str, str]:
    mock_bin = tmp_path / "bin"
    mock_bin.mkdir()
    for name, body in (("gh", FAKE_GH), ("npx", FAKE_NPX)):
        path = mock_bin / name
        _ = path.write_text(body, encoding="utf-8")
        _ = path.chmod(0o755)
    return {
        **os.environ,
        "PATH": f"{mock_bin}:{os.environ.get('PATH', '')}",
        "FAKE_GH_SCENARIO": scenario,
        "FAKE_GH_STATE": str(tmp_path / "gh-state.json"),
        "FAKE_GH_JOBS": JOBS_JSON,
        "FAKE_GH_LOG_LINES": str(LOG_LINES),
    }


def _run_script(script: Path, repo: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script)],
        cwd=repo,
        env=env,
        input="a\n",
        capture_output=True,
        text=True,
        check=False,
    )


def _log_lines(output: str) -> list[str]:
    return [line for line in output.splitlines() if line.startswith("LOG-")]


def test_dispatch_failure_names_job_and_step_before_a_bounded_log_tail(tmp_path: Path) -> None:
    repo = _release_repo(tmp_path)
    result = _run_script(DISPATCH, repo, _fake_env(tmp_path, "failure"))
    combined = result.stdout + result.stderr

    assert result.returncode != 0, f"a failed release must exit non-zero:\n{combined}"
    step_lines = [line for line in combined.splitlines() if "›" in line]
    assert any("release" in line and "dependency audit" in line for line in step_lines), (
        f"failing job › step not named:\n{combined}"
    )
    assert "log tail (last 120 lines)" in combined, f"log tail not announced:\n{combined}"
    logs = _log_lines(combined)
    assert len(logs) == 120, f"log tail is not bounded to 120 lines ({len(logs)}):\n{combined}"
    assert logs[0] == "LOG-381" and logs[-1] == "LOG-500", f"wrong log tail:\n{combined}"
    assert "actions/runs/101" in combined, f"run URL hint missing:\n{combined}"


def test_dispatch_success_prints_only_the_success_line_and_tag_hint(tmp_path: Path) -> None:
    repo = _release_repo(tmp_path)
    result = _run_script(DISPATCH, repo, _fake_env(tmp_path, "success"))
    combined = result.stdout + result.stderr

    assert result.returncode == 0, f"a green release must exit 0:\n{combined}"
    assert "workflow completed: success" in combined, f"success line missing:\n{combined}"
    assert "release workflow succeeded — run 101" in combined, f"run line missing:\n{combined}"
    assert "tags:" in combined, f"tag hint missing:\n{combined}"
    assert "›" not in combined, f"a green run must not print failure diagnostics:\n{combined}"
    assert "log tail" not in combined, f"a green run must not print a log tail:\n{combined}"


def test_release_watch_failure_names_job_and_step_before_a_bounded_log_tail(
    tmp_path: Path,
) -> None:
    repo = _release_repo(tmp_path)
    result = _run_script(RELEASE_WATCH, repo, _fake_env(tmp_path, "failure"))
    combined = result.stdout + result.stderr

    assert result.returncode == 1, f"a failed release must exit 1:\n{combined}"
    assert "release failure — fetching logs" in combined, f"conclusion line missing:\n{combined}"
    assert "release › dependency audit" in combined, f"failing job › step not named:\n{combined}"
    logs = _log_lines(combined)
    assert len(logs) == 300, f"log tail is not bounded to 300 lines ({len(logs)}):\n{combined}"
    assert logs[0] == "LOG-201" and logs[-1] == "LOG-500", f"wrong log tail:\n{combined}"
