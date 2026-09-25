"""Tests for dynamic-workflow-wrapper install-agents.mjs and canonical agent definitions."""

import hashlib
import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "dynamic-workflow-wrapper"
CANONICAL_AGENTS_DIR = SKILL_DIR / "references" / "agents"
LOCK_PATH = SKILL_DIR / "references" / "agents.lock.json"
INSTALL_SCRIPT = SKILL_DIR / "scripts" / "install-agents.mjs"


def _install_agents_into(cwd: Path) -> Path:
    """Install the roles into `cwd` and return the target dir the installer populated.

    The installer resolves its target as `<git top-level>/.pi/agents`, and `.pi/` is gitignored:
    a fresh checkout (CI) has no installed roles, so the tests must produce the state they assert
    on instead of depending on developer-local installs.
    """
    probe = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=str(cwd), capture_output=True, text=True
    )
    assert probe.returncode != 0, (
        f"refusing to install into {cwd}: it sits inside the repository at {probe.stdout.strip()}"
    )

    result = subprocess.run(
        ["node", str(INSTALL_SCRIPT)], cwd=str(cwd), capture_output=True, text=True
    )
    assert result.returncode == 0, (
        f"install-agents failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )

    target_dir = cwd / ".pi" / "agents"
    assert target_dir.is_dir(), f"installer did not populate {target_dir}:\nstdout: {result.stdout}"
    return target_dir


def test_install_agents_check_passes(tmp_path):
    """install-agents.mjs --check must exit 0 once the installed roles match the lockfile."""
    _ = _install_agents_into(tmp_path)

    result = subprocess.run(
        ["node", str(INSTALL_SCRIPT), "--check"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"install-agents --check failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )


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
        assert locked_agents[agent_file.name] == computed_sha, (
            f"Hash mismatch for {agent_file.name} in agents.lock.json"
        )


def test_canonical_agent_frontmatters():
    """All canonical agent files must have valid name, description, tools, and systemPromptMode."""
    expected_agents = [
        "developer.md",
        "gate-runner.md",
        "code-reviewer.md",
        "ticket-planner.md",
        "merger.md",
    ]

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


def test_target_agents_have_inlined_output_contract(tmp_path):
    """Installed roles must carry @include directives expanded into inlined contracts."""
    target_dir = _install_agents_into(tmp_path)

    inlined_agents = ["developer.md", "gate-runner.md", "code-reviewer.md", "merger.md"]
    for name in inlined_agents:
        target_file = target_dir / name
        assert target_file.exists(), f"Expected installed target agent {name} not found"
        text = target_file.read_text(encoding="utf-8")
        assert "<!-- @include" not in text, (
            f"{name} still contains unexpanded <!-- @include directive"
        )
        assert "# Subagent Response Format" in text, (
            f"{name} does not contain inlined Subagent Response Format"
        )
        assert "## 1. Dual-Mode Representation" in text, (
            f"{name} missing inlined Dual-Mode Representation"
        )


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


def test_check_flags_drift_instead_of_overwriting(tmp_path):
    """A hand-edited installed role must read as drift, and --check must leave it untouched."""
    target_dir = _install_agents_into(tmp_path)
    target = target_dir / "developer.md"
    edited = target.read_text(encoding="utf-8") + "\nlocal edit\n"
    _ = target.write_text(edited, encoding="utf-8")

    result = subprocess.run(
        ["node", str(INSTALL_SCRIPT), "--check"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2, (
        f"expected drift to exit 2:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "drifted: developer.md" in result.stdout, result.stdout
    assert target.read_text(encoding="utf-8") == edited, "drifted role was overwritten by --check"


def test_canonical_agent_skills_resolve():
    """Every skill a role declares or points at must resolve to a real skill directory.

    The runtime binds only `tools`, `disallowedTools`, `model`, `isolation`, and the
    body prompt: the `skills:` frontmatter is parsed-but-ignored, so a role's body
    pointers are the ONLY load path. A pointer is opened at task time, so a stale
    name fails there: `resolving-merge-conflicts` shipped while the canonical
    directory is `resolve-merge-conflicts`.

    Because the pointer is the load path, every declared skill must also be pointed
    at in the body — a declared-but-unpointed name never loads.
    """
    # `.agents/skills` is gitignored (local harness only), so it is absent in CI. A
    # referenced skill must resolve to a tracked root (`skills/`) or, when the local
    # harness root is present, to `.agents/skills`. In CI a name that lives only in the
    # local harness cannot be asserted, so it is skipped; a name that resolves nowhere
    # in the current checkout is stale (e.g. the `resolving-merge-conflicts` typo).
    skill_roots = [REPO_ROOT / "skills"]
    local_root = REPO_ROOT / ".agents" / "skills"
    if local_root.is_dir():
        skill_roots.append(local_root)

    def resolves(name):
        return any((root / name).is_dir() for root in skill_roots)

    def check(name, what):
        if not resolves(name):
            # A name that is neither tracked nor present in the local harness root is
            # only stale when the local root exists to disprove it; without it (CI) it
            # is an unverifiable external harness skill, not a repo contract.
            if local_root.is_dir():
                raise AssertionError(f"{agent_file.name} {what} unknown skill {name!r}")

    # Both the user-scoped `~/.agents/skills/<name>/` form and the project-scoped
    # `.agents/skills/<name>/` form are valid load paths; match either.
    pointer_re = re.compile(r"(?:~/)?\.agents/skills/([A-Za-z0-9._-]+)/")

    for agent_file in sorted(CANONICAL_AGENTS_DIR.glob("*.md")):
        text = agent_file.read_text(encoding="utf-8")
        frontmatter = text.split("---\n")[1]
        body = text.split("---\n", 2)[2]

        pointed = set(pointer_re.findall(body))

        declared = re.search(r"^skills:\s*(.+)$", frontmatter, re.MULTILINE)
        if declared is not None:
            names = [part.strip() for part in declared.group(1).split(",") if part.strip()]
            for name in names:
                check(name, "declares")
                # The body pointer is the load path: a declared name with no pointer
                # never reaches the subagent, so the declaration is dead config.
                assert name in pointed, (
                    f"{agent_file.name} declares {name!r} but never points at it in the body; "
                    f"the `skills:` field is inert, so the body pointer is the only load path"
                )

        for name in sorted(pointed):
            check(name, "points at")
