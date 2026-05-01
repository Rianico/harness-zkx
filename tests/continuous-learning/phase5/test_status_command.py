"""
Tests for status command.

Eval 5.1: status Command

Input: `/continuous-learning status`
Expected: Display all instincts with confidence

Pass criteria:
- [ ] Shows project-scoped instincts
- [ ] Shows global instincts
- [ ] Displays confidence scores
- [ ] Shows domain and trigger
"""

import sys
from pathlib import Path

import pytest
import yaml

from hooks.observe.instinct_manager import InstinctManager


SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent / "skills" / "continuous-learning" / "scripts"
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def status_script() -> Path:
    """Return path to status script."""
    return SCRIPTS_DIR / "status.py"


@pytest.fixture
def instinct_manager(homunculus_dir: Path) -> InstinctManager:
    """Create instinct manager instance."""
    return InstinctManager(homunculus_dir)


@pytest.fixture
def sample_project_instinct(homunculus_dir: Path) -> Path:
    """Create a sample project-scoped instinct."""
    project_id = "a1b2c3d4e5f6"
    instincts_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
    instincts_dir.mkdir(parents=True, exist_ok=True)

    instinct_content = """---
id: test-project-instinct
trigger: "when editing unfamiliar files"
confidence: 0.7
domain: "workflow"
scope: "project"
project_id: "a1b2c3d4e5f6"
created_at: "2026-04-30T10:00:00Z"
updated_at: "2026-04-30T10:05:00Z"
evidence_count: 3
---

# Test Project Instinct

## Action
Use Read tool before Edit.

## Evidence
- Session s1: Pattern observed
"""
    instinct_file = instincts_dir / "test-project-instinct.yaml"
    instinct_file.write_text(instinct_content)
    return instinct_file


@pytest.fixture
def sample_global_instinct(homunculus_dir: Path) -> Path:
    """Create a sample global instinct."""
    instincts_dir = homunculus_dir / "instincts" / "personal"
    instincts_dir.mkdir(parents=True, exist_ok=True)

    instinct_content = """---
id: test-global-instinct
trigger: "when running bash commands"
confidence: 0.9
domain: "debugging"
scope: "global"
project_id: "global"
created_at: "2026-04-30T09:00:00Z"
updated_at: "2026-04-30T09:30:00Z"
evidence_count: 15
---

# Test Global Instinct

## Action
Check exit codes before proceeding.

## Evidence
- Session g1: Global pattern observed
"""
    instinct_file = instincts_dir / "test-global-instinct.yaml"
    instinct_file.write_text(instinct_content)
    return instinct_file


class TestStatusCommandScript:
    """Tests for the status command script file existence."""

    def test_script_exists(self, status_script: Path) -> None:
        """
        The status.py script should exist in the scripts directory.
        """
        assert status_script.exists(), f"Script not found at {status_script}"


class TestStatusCommandFunctionality:
    """Tests for status command functionality via InstinctManager."""

    def test_shows_project_scoped_instincts(
        self, instinct_manager: InstinctManager, sample_project_instinct: Path
    ) -> None:
        """
        Eval 5.1: Shows project-scoped instincts.

        The status command should list instincts for the current project.
        """
        instincts = instinct_manager.list_instincts(project_id="a1b2c3d4e5f6")

        assert len(instincts) >= 1
        found_ids = [i["frontmatter"]["id"] for i in instincts]
        assert "test-project-instinct" in found_ids

    def test_shows_global_instincts(
        self, instinct_manager: InstinctManager, sample_global_instinct: Path
    ) -> None:
        """
        Eval 5.1: Shows global instincts.

        The status command should list global instincts.
        """
        instincts = instinct_manager.list_instincts()

        found_ids = [i["frontmatter"]["id"] for i in instincts]
        assert "test-global-instinct" in found_ids

    def test_displays_confidence_scores(
        self, instinct_manager: InstinctManager, sample_project_instinct: Path
    ) -> None:
        """
        Eval 5.1: Displays confidence scores.

        The status command should show confidence values for each instinct.
        """
        instincts = instinct_manager.list_instincts(project_id="a1b2c3d4e5f6")

        project_instinct = next(
            (i for i in instincts if i["frontmatter"]["id"] == "test-project-instinct"),
            None
        )
        assert project_instinct is not None
        assert project_instinct["frontmatter"]["confidence"] == 0.7

    def test_displays_domain_and_trigger(
        self, instinct_manager: InstinctManager, sample_project_instinct: Path
    ) -> None:
        """
        Eval 5.1: Shows domain and trigger.

        The status command should show the domain and trigger for each instinct.
        """
        instincts = instinct_manager.list_instincts(project_id="a1b2c3d4e5f6")

        project_instinct = next(
            (i for i in instincts if i["frontmatter"]["id"] == "test-project-instinct"),
            None
        )
        assert project_instinct is not None
        assert project_instinct["frontmatter"]["domain"] == "workflow"
        assert "editing unfamiliar files" in project_instinct["frontmatter"]["trigger"]

    def test_returns_empty_list_when_no_instincts(
        self, instinct_manager: InstinctManager
    ) -> None:
        """
        When no instincts exist, should return empty list.
        """
        instincts = instinct_manager.list_instincts()
        assert instincts == []


class TestStatusCommandFilters:
    """Tests for status command filtering options."""

    def test_filter_by_project(
        self,
        instinct_manager: InstinctManager,
        sample_project_instinct: Path,
        sample_global_instinct: Path
    ) -> None:
        """
        Status command should support filtering by project.
        """
        # Filter by project should only show project instincts
        project_instincts = instinct_manager.list_instincts(
            project_id="a1b2c3d4e5f6",
            scope="project"
        )

        found_ids = [i["frontmatter"]["id"] for i in project_instincts]
        assert "test-project-instinct" in found_ids
        # Global should not appear when filtering by project scope
        assert "test-global-instinct" not in found_ids

    def test_filter_by_scope_global(
        self,
        instinct_manager: InstinctManager,
        sample_project_instinct: Path,
        sample_global_instinct: Path
    ) -> None:
        """
        Status command should support filtering by scope=global.
        """
        global_instincts = instinct_manager.list_instincts(scope="global")

        found_ids = [i["frontmatter"]["id"] for i in global_instincts]
        assert "test-global-instinct" in found_ids
        assert "test-project-instinct" not in found_ids

    def test_filter_by_scope_project(
        self,
        instinct_manager: InstinctManager,
        sample_project_instinct: Path,
        sample_global_instinct: Path
    ) -> None:
        """
        Status command should support filtering by scope=project.
        """
        project_instincts = instinct_manager.list_instincts(scope="project")

        found_ids = [i["frontmatter"]["id"] for i in project_instincts]
        assert "test-project-instinct" in found_ids
        assert "test-global-instinct" not in found_ids


class TestStatusCommandOutput:
    """Tests for status command output formatting."""

    def test_includes_all_required_fields(
        self, instinct_manager: InstinctManager, sample_project_instinct: Path
    ) -> None:
        """
        Status output should include all required fields.
        """
        instincts = instinct_manager.list_instincts(project_id="a1b2c3d4e5f6")

        assert len(instincts) >= 1
        instinct = instincts[0]
        fm = instinct["frontmatter"]

        # Required fields for status display
        assert "id" in fm
        assert "trigger" in fm
        assert "confidence" in fm
        assert "domain" in fm
        assert "scope" in fm

    def test_includes_body_content(
        self, instinct_manager: InstinctManager, sample_project_instinct: Path
    ) -> None:
        """
        Status output should include body content (action).
        """
        instincts = instinct_manager.list_instincts(project_id="a1b2c3d4e5f6")

        instinct = instincts[0]
        assert "body" in instinct
        assert "Read tool before Edit" in instinct["body"]


class TestStatusScriptExecution:
    """Tests for status script execution.

    These tests verify the script wrapper works correctly.
    The scripts are currently stubs, so these tests should FAIL.
    """

    def test_script_returns_zero_exit_code(
        self, status_script: Path, sample_project_instinct: Path, temp_home: Path
    ) -> None:
        """
        Script should return exit code 0 on success.

        Currently FAILS because script is a stub.
        """
        import subprocess

        env = {"HOME": str(temp_home)}

        result = subprocess.run(
            [sys.executable, str(status_script), "--project", "a1b2c3d4e5f6"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_script_outputs_instinct_data(
        self, status_script: Path, sample_project_instinct: Path, temp_home: Path
    ) -> None:
        """
        Script should output instinct data.

        Currently FAILS because script is a stub.
        """
        import subprocess

        env = {"HOME": str(temp_home)}

        result = subprocess.run(
            [sys.executable, str(status_script), "--project", "a1b2c3d4e5f6"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        # Should output the instinct ID
        assert "test-project-instinct" in result.stdout, f"Expected instinct in output: {result.stdout}"

    def test_script_json_output(
        self, status_script: Path, sample_project_instinct: Path, temp_home: Path
    ) -> None:
        """
        Script should produce valid JSON with --json flag.

        Currently FAILS because script is a stub.
        """
        import json
        import subprocess

        env = {"HOME": str(temp_home)}

        result = subprocess.run(
            [sys.executable, str(status_script), "--project", "a1b2c3d4e5f6", "--json"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        # Should produce valid JSON
        output = json.loads(result.stdout)
        assert isinstance(output, dict)
        assert "instincts" in output
