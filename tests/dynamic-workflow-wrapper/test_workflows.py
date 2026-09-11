"""Tests for dynamic workflow scripts under skills/dynamic-workflow-wrapper/workflows/."""

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "dynamic-workflow-wrapper"
WORKFLOWS_DIR = SKILL_DIR / "workflows"


def test_converge_goal_structure_and_syntax():
    """converge-goal.js must export meta and be syntactically valid in an async execution context."""
    script_path = WORKFLOWS_DIR / "converge-goal.js"
    assert script_path.exists(), f"Missing workflow script: {script_path}"
    content = script_path.read_text(encoding="utf-8")

    # Verify meta export
    assert "export const meta = {" in content
    assert 'name: "converge-goal"' in content
    assert "phases:" in content
    assert "Plan & Prepare" in content
    assert "Iterate & Gate" in content
    assert "Finalize" in content

    # Verify required primitives are utilized
    assert "gate(" in content, "Workflow must use gate() helper for convergence loop"
    assert "agent(" in content, "Workflow must invoke agent() subagents"
    assert 'agentType: "developer"' in content
    assert 'agentType: "gate-runner"' in content
    assert 'agentType: "code-reviewer"' in content
    assert "phase(" in content

    # Verify absence of forbidden VM globals/modules
    assert "import " not in re.sub(r"/\*[\s\S]*?\*/|//.*", "", content), "VM scripts must not contain imports"
    assert "require(" not in content, "VM scripts must not use require()"

    # Verify syntax when wrapped in an async function (matching Pi VM execution model)
    node_checker = """
    const fs = require('node:fs');
    const full = fs.readFileSync(process.argv[1], 'utf8');
    const body = full.replace(/export const meta = \\{[\\s\\S]*?\\};\\n/, '');
    new Function('(async () => {' + body + '})');
    """
    proc = subprocess.run(
        ["node", "-e", node_checker, str(script_path)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"converge-goal.js syntax check failed:\n{proc.stderr}"
