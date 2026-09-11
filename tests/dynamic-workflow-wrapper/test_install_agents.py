"""Tests for dynamic-workflow-wrapper install-agents.mjs and canonical agent definitions."""

import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "dynamic-workflow-wrapper"
CANONICAL_AGENTS_DIR = SKILL_DIR / "references" / "agents"
LOCK_PATH = SKILL_DIR / "references" / "agents.lock.json"
INSTALL_SCRIPT = SKILL_DIR / "scripts" / "install-agents.mjs"


def test_install_agents_check_passes():
    """install-agents.mjs --check must exit 0, indicating all canonical agents are aligned."""
    result = subprocess.run(
        ["node", str(INSTALL_SCRIPT), "--check"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"install-agents --check failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"


def test_agents_lock_matches_canonical_hashes():
    """Every canonical agent file's sha256 hash must match agents.lock.json."""
    assert LOCK_PATH.exists(), f"Missing lockfile: {LOCK_PATH}"
    lock_data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    locked_agents = lock_data.get("agents", {})

    agent_files = list(CANONICAL_AGENTS_DIR.glob("*.md"))
    assert len(agent_files) >= 5, f"Expected at least 5 canonical agents, found {len(agent_files)}"

    for agent_file in agent_files:
        content = agent_file.read_bytes()
        computed_sha = hashlib.sha256(content).hexdigest()
        assert agent_file.name in locked_agents, f"{agent_file.name} missing from agents.lock.json"
        assert (
            locked_agents[agent_file.name] == computed_sha
        ), f"Hash mismatch for {agent_file.name} in agents.lock.json"


def test_canonical_agent_frontmatters():
    """All canonical agent files must have valid name, description, tools, and systemPromptMode."""
    expected_agents = ["developer.md", "gate-runner.md", "code-reviewer.md", "ticket-planner.md", "merger.md"]

    for name in expected_agents:
        agent_file = CANONICAL_AGENTS_DIR / name
        assert agent_file.exists(), f"Expected canonical agent {name} not found"
        text = agent_file.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f"{name} does not start with YAML frontmatter"
        parts = text.split("---\n")
        assert len(parts) >= 3, f"{name} frontmatter not properly closed"

        frontmatter = parts[1]
        assert f"name: {name.replace('.md', '')}" in frontmatter
        assert "description:" in frontmatter
        assert "systemPromptMode: replace" in frontmatter
        assert "tools:" in frontmatter


def test_target_agents_have_inlined_output_contract():
    """Target installed agents in .pi/agents must have expanded @include directives inlining the contract."""
    target_dir = REPO_ROOT / ".pi" / "agents"
    assert target_dir.exists(), f"Target directory {target_dir} does not exist"

    inlined_agents = ["developer.md", "gate-runner.md", "code-reviewer.md", "merger.md"]
    for name in inlined_agents:
        target_file = target_dir / name
        assert target_file.exists(), f"Expected installed target agent {name} not found"
        text = target_file.read_text(encoding="utf-8")
        assert "<!-- @include" not in text, f"{name} still contains unexpanded <!-- @include directive"
        assert "# Subagent Response Format" in text, f"{name} does not contain inlined Subagent Response Format"
        assert "## 1. Dual-Mode Representation" in text, f"{name} missing inlined Dual-Mode Representation"


def test_agents_lock_tracks_includes_and_compiled():
    """agents.lock.json must track included templates and compiled target hashes."""
    lock_data = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    assert "includes" in lock_data, "Missing 'includes' section in agents.lock.json"
    assert "compiled" in lock_data, "Missing 'compiled' section in agents.lock.json"
    assert "references/resp-format.md" in lock_data["includes"]

    resp_format_path = SKILL_DIR / "references" / "resp-format.md"
    assert resp_format_path.exists()
    computed_sha = hashlib.sha256(resp_format_path.read_bytes()).hexdigest()
    assert lock_data["includes"]["references/resp-format.md"] == computed_sha

