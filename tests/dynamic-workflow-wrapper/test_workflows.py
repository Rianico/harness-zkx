"""Tests for dynamic workflow scripts under skills/dynamic-workflow-wrapper/workflows/."""

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "dynamic-workflow-wrapper"
WORKFLOWS_DIR = SKILL_DIR / "workflows"

# The runtime body already executes inside an async function; wrap it the same way to check syntax.
NODE_SYNTAX_CHECKER = """
const fs = require('node:fs');
const full = fs.readFileSync(process.argv[1], 'utf8');
const body = full.replace(/export const meta = \\{[\\s\\S]*?\\};\\n/, '');
new Function('(async () => {' + body + '})');
"""

CANONICAL_ROLES = ["developer", "gate-runner", "code-reviewer", "ticket-planner", "merger"]


def workflow_scripts() -> list[Path]:
    """Every workflow script the skill ships; the glob keeps new scripts under the same checks."""
    return sorted(WORKFLOWS_DIR.glob("*.js"))


def read_workflow(name: str) -> str:
    script_path = WORKFLOWS_DIR / name
    assert script_path.exists(), f"Missing workflow script: {script_path}"
    return script_path.read_text(encoding="utf-8")


def strip_comments(content: str) -> str:
    return re.sub(r"/\*[\s\S]*?\*/|//.*", "", content)


def test_workflow_scripts_exist():
    """The skill must ship at least one workflow script."""
    scripts = workflow_scripts()
    assert scripts, f"No workflow scripts found in {WORKFLOWS_DIR}"


def test_workflow_scripts_are_syntactically_valid():
    """Every workflow must parse in the runtime's async-body execution model."""
    for script_path in workflow_scripts():
        proc = subprocess.run(
            ["node", "-e", NODE_SYNTAX_CHECKER, str(script_path)],
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, f"{script_path.name} syntax check failed:\n{proc.stderr}"


def test_workflow_scripts_avoid_vm_forbidden_globals():
    """The workflow VM provides no modules and no ambient nondeterminism."""
    for script_path in workflow_scripts():
        stripped = strip_comments(script_path.read_text(encoding="utf-8"))
        assert "import " not in stripped, f"{script_path.name} must not contain imports"
        assert "require(" not in stripped, f"{script_path.name} must not use require()"
        assert "Date.now(" not in stripped, f"{script_path.name} must not use Date.now()"
        assert "Math.random(" not in stripped, f"{script_path.name} must not use Math.random()"


def test_converge_tasks_declares_meta_and_phases():
    """converge-tasks.js must declare its meta and enter every phase it declares."""
    content = read_workflow("converge-tasks.js")

    assert "export const meta = {" in content
    assert re.search(r"name: ['\"]converge-tasks['\"]", content), "meta.name must be converge-tasks"
    assert "description:" in content

    for phase_title in ("Plan & Prepare", "Integrate & Gate", "Finalize"):
        assert phase_title in content, f"phase {phase_title!r} is not declared"
        assert f"phase('{phase_title}')" in content or f'phase("{phase_title}")' in content

    for primitive in ("agent(", "gate(", "log("):
        assert primitive in content, f"converge-tasks.js must use {primitive}()"


def test_converge_tasks_uses_the_canonical_roster():
    """Every node must be bound to a canonical role, so the roster stays load-bearing."""
    content = read_workflow("converge-tasks.js")
    for role in CANONICAL_ROLES:
        assert f"agentType: '{role}'" in content or f'agentType: "{role}"' in content, (
            f"role {role} is never dispatched"
        )


def test_converge_tasks_takes_a_task_list_with_bounded_budgets():
    """One task and many share the same code path; both budgets are explicit and bounded."""
    content = read_workflow("converge-tasks.js")

    assert "rawArgs.tasks" in content, "the task list is the interface"
    assert "dependsOn" in content, "batch ordering is declarative"
    assert "resolveOrder" in content, "dependency order must be resolved deterministically"
    assert "maxRounds" in content
    assert "maxMergeAttempts" in content
    assert "Math.min(" in content, "budgets must be clamped"


def test_converge_tasks_keeps_the_isolation_guards():
    """The two isolation phases are the falsifiable guards each round must run."""
    content = read_workflow("converge-tasks.js")
    assert "worktree-branch" in content
    assert "root-untouched" in content
    assert "status --porcelain --untracked-files=no" in content


def test_converge_tasks_derives_reverification_from_merge_exit_codes():
    """Merge authority: the merger reports exit codes; only the workflow decides re-verification."""
    content = read_workflow("converge-tasks.js")

    assert "merge_copy.py" in content
    assert "exitCode" in content
    assert "nonZero" in content, "a non-zero merge attempt must invalidate the round"
    assert "exactly ONE merge" in content, "the merger must not retry a merge inside one call"
    assert "reReview" not in content, "re-verification must never be a subagent self-report"


def test_converge_tasks_never_pushes_or_opens_a_pull_request():
    """Delivery is the operator's step: nothing external may be emitted unattended."""
    content = read_workflow("converge-tasks.js")

    for forbidden in ("git push", "gh pr create", "gh pr merge"):
        assert forbidden not in content, f"converge-tasks.js must not run {forbidden!r}"

    assert "nextActions" in content, "the operator step must be reported as nextActions"


DOCS_WITH_WORKFLOW_POINTERS = (
    SKILL_DIR / "SKILL.md",
    SKILL_DIR / "references" / "workflow-guidelines.md",
)

WORKFLOW_PATH_PATTERN = re.compile(r"workflows/([A-Za-z0-9._-]+\.js)")


def test_retired_workflow_scripts_stay_retired():
    """converge-goal was generalized into converge-tasks; the old entry surface stays closed."""
    assert not (WORKFLOWS_DIR / "converge-goal.js").exists(), (
        "converge-goal.js was retired into converge-tasks.js — re-adding it recreates the duplicate loop"
    )


def test_documented_workflow_paths_exist():
    """A documented workflow path that does not resolve is drift, not a TODO."""
    shipped = {script.name for script in workflow_scripts()}

    for doc in DOCS_WITH_WORKFLOW_POINTERS:
        referenced = set(WORKFLOW_PATH_PATTERN.findall(doc.read_text(encoding="utf-8")))
        assert referenced, f"{doc.name} must point at the workflow it routes to"
        for name in sorted(referenced):
            assert (WORKFLOWS_DIR / name).exists(), f"{doc.name} points at missing workflows/{name}"

    assert shipped <= set(WORKFLOW_PATH_PATTERN.findall((SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"))), (
        "every shipped workflow must be reachable from the routing table in SKILL.md"
    )


def test_no_dangling_ship_tasks_pointers():
    """The removed ship-tasks workflow must not survive as a pointer to nothing."""
    for doc in DOCS_WITH_WORKFLOW_POINTERS:
        content = doc.read_text(encoding="utf-8")
        assert "ship-tasks" not in content, f"{doc.name} still references the retired ship-tasks workflow"
