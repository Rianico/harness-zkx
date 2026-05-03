"""
Tests for promote command.

Eval 5.4: promote Command

Input: `/continuous-learning promote <id>`
Expected: Instinct promoted to global

Pass criteria:
- [ ] Validates promotion criteria
- [ ] Moves/links to global directory
- [ ] Updates metadata
- [ ] Confirms to user
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest
import yaml

# Add lib to path for tz import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "lib"))
from tz import TZ_CST

from hooks.observe.agent_runner import Promotion
from hooks.observe.instinct_manager import InstinctManager


SCRIPTS_DIR = Path(__file__).parent.parent.parent.parent / "skills" / "continuous-learning" / "scripts"


@pytest.fixture
def promote_script() -> Path:
    """Return path to promote script."""
    return SCRIPTS_DIR / "promote.py"


@pytest.fixture
def instinct_manager(homunculus_dir: Path) -> InstinctManager:
    """Create instinct manager instance."""
    return InstinctManager(homunculus_dir)


@pytest.fixture
def eligible_instinct_in_two_projects(homunculus_dir: Path) -> dict[str, Path]:
    """Create an instinct that exists in 2 projects with high confidence."""
    paths = {}

    for project_id in ["proj-eligible-1", "proj-eligible-2"]:
        project_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
        project_dir.mkdir(parents=True, exist_ok=True)

        instinct_content = f"""---
id: promotable-instinct
trigger: "when running tests"
confidence: 0.85
domain: "testing"
scope: "project"
project_id: "{project_id}"
created_at: "2026-04-30T10:00:00Z"
updated_at: "2026-04-30T10:30:00Z"
evidence_count: 10
---

# Promotable Instinct

## Action
Run tests before committing.

## Evidence
- Session s1: Pattern observed in project {project_id}
- Session s2: Pattern reinforced
"""
        instinct_file = project_dir / "promotable-instinct.yaml"
        instinct_file.write_text(instinct_content)
        paths[project_id] = instinct_file

    return paths


@pytest.fixture
def single_project_instinct(homunculus_dir: Path) -> Path:
    """Create an instinct that only exists in one project."""
    project_id = "single-project"
    project_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
    project_dir.mkdir(parents=True, exist_ok=True)

    instinct_content = """---
id: single-instinct
trigger: "when working alone"
confidence: 0.9
domain: "workflow"
scope: "project"
project_id: "single-project"
created_at: "2026-04-30T11:00:00Z"
updated_at: "2026-04-30T11:30:00Z"
evidence_count: 15
---

# Single Project Instinct

## Action
Only exists in one project.

## Evidence
- Session s1: Pattern observed
"""
    instinct_file = project_dir / "single-instinct.yaml"
    instinct_file.write_text(instinct_content)
    return instinct_file


@pytest.fixture
def low_confidence_instincts(homunculus_dir: Path) -> dict[str, Path]:
    """Create instincts with low confidence in multiple projects."""
    paths = {}

    for project_id in ["low-conf-1", "low-conf-2"]:
        project_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
        project_dir.mkdir(parents=True, exist_ok=True)

        instinct_content = f"""---
id: low-confidence-instinct
trigger: "when unsure"
confidence: 0.5
domain: "uncertain"
scope: "project"
project_id: "{project_id}"
created_at: "2026-04-30T12:00:00Z"
updated_at: "2026-04-30T12:30:00Z"
evidence_count: 3
---

# Low Confidence Instinct

## Action
Not confident enough.

## Evidence
- Session s1: Weak pattern
"""
        instinct_file = project_dir / "low-confidence-instinct.yaml"
        instinct_file.write_text(instinct_content)
        paths[project_id] = instinct_file

    return paths


@pytest.fixture
def already_global_instinct(homunculus_dir: Path) -> Path:
    """Create an instinct that's already global."""
    global_dir = homunculus_dir / "instincts" / "personal"
    global_dir.mkdir(parents=True, exist_ok=True)

    instinct_content = """---
id: already-global
trigger: "when globally applicable"
confidence: 0.9
domain: "global"
scope: "global"
project_id: "global"
created_at: "2026-04-30T08:00:00Z"
updated_at: "2026-04-30T08:30:00Z"
evidence_count: 25
---

# Already Global Instinct

## Action
Already promoted.

## Evidence
- Session g1: Global pattern
"""
    instinct_file = global_dir / "already-global.yaml"
    instinct_file.write_text(instinct_content)
    return instinct_file


class TestPromoteCommandScript:
    """Tests for the promote command script file existence."""

    def test_script_exists(self, promote_script: Path) -> None:
        """
        The promote.py script should exist in the scripts directory.
        """
        assert promote_script.exists(), f"Script not found at {promote_script}"


class TestPromoteCommandFunctionality:
    """Tests for promote command functionality via InstinctManager."""

    def test_validates_promotion_criteria(
        self, instinct_manager: InstinctManager, eligible_instinct_in_two_projects: dict[str, Path]
    ) -> None:
        """
        Eval 5.4: Validates promotion criteria.

        The promote command should check that the instinct meets criteria.
        """
        is_eligible, reason = instinct_manager.check_promotion_eligibility("promotable-instinct")

        assert is_eligible, f"Expected eligible: {reason}"
        assert "2 projects" in reason.lower() or "eligible" in reason.lower()

    def test_moves_to_global_directory(
        self, instinct_manager: InstinctManager, eligible_instinct_in_two_projects: dict[str, Path]
    ) -> None:
        """
        Eval 5.4: Moves/links to global directory.

        After promotion, the instinct should exist in global directory.
        """
        promotion = Promotion(
            id="promotable-instinct",
            reason="Seen in 2 projects with high confidence"
        )

        global_path = instinct_manager.promote_instinct(promotion)

        assert global_path is not None
        assert global_path.exists()
        assert "instincts" in str(global_path)
        assert "personal" in str(global_path)
        assert "projects" not in str(global_path)

    def test_updates_metadata(
        self, instinct_manager: InstinctManager, eligible_instinct_in_two_projects: dict[str, Path]
    ) -> None:
        """
        Eval 5.4: Updates metadata.

        Promoted instinct should have updated scope and project_id.
        """
        promotion = Promotion(
            id="promotable-instinct",
            reason="Seen in 2 projects with high confidence"
        )

        global_path = instinct_manager.promote_instinct(promotion)
        content = global_path.read_text()
        parts = content.split("---")
        frontmatter = yaml.safe_load(parts[1])

        assert frontmatter["scope"] == "global"
        assert frontmatter["project_id"] == "global"

    def test_confirms_to_user_via_return(
        self, instinct_manager: InstinctManager, eligible_instinct_in_two_projects: dict[str, Path]
    ) -> None:
        """
        Eval 5.4: Confirms to user.

        The promote command should return the path to confirm success.
        """
        promotion = Promotion(
            id="promotable-instinct",
            reason="Seen in 2 projects with high confidence"
        )

        global_path = instinct_manager.promote_instinct(promotion)

        # Return of a valid path confirms success
        assert global_path is not None
        assert global_path.exists()

    def test_rejects_single_project_instinct(
        self, instinct_manager: InstinctManager, single_project_instinct: Path
    ) -> None:
        """
        Should not promote instincts that only exist in one project.
        """
        is_eligible, reason = instinct_manager.check_promotion_eligibility("single-instinct")

        assert not is_eligible
        assert "1 project" in reason.lower() or "need at least 2" in reason.lower()

    def test_rejects_low_confidence_instinct(
        self, instinct_manager: InstinctManager, low_confidence_instincts: dict[str, Path]
    ) -> None:
        """
        Should not promote instincts with low average confidence.
        """
        is_eligible, reason = instinct_manager.check_promotion_eligibility("low-confidence-instinct")

        assert not is_eligible
        assert "confidence" in reason.lower() or "0.8" in reason

    def test_handles_already_global_instinct(
        self, instinct_manager: InstinctManager, already_global_instinct: Path
    ) -> None:
        """
        Should handle the case where instinct is already global.
        """
        # Try to promote an already global instinct
        # It's in global directory, so check_promotion_eligibility won't find project instances
        is_eligible, reason = instinct_manager.check_promotion_eligibility("already-global")

        # Should not be eligible (no project instances found)
        assert not is_eligible

    def test_removes_project_copies_after_promotion(
        self, instinct_manager: InstinctManager, eligible_instinct_in_two_projects: dict[str, Path]
    ) -> None:
        """
        After promotion, project-specific copies should be removed.
        """
        promotion = Promotion(
            id="promotable-instinct",
            reason="Seen in 2 projects with high confidence"
        )

        instinct_manager.promote_instinct(promotion)

        # Check project copies are removed
        for project_id, path in eligible_instinct_in_two_projects.items():
            assert not path.exists(), f"Project copy should be removed: {path}"


class TestPromoteCommandOptions:
    """Tests for promote command options."""

    def test_force_flag_bypasses_criteria(
        self, instinct_manager: InstinctManager, single_project_instinct: Path
    ) -> None:
        """
        --force flag should allow bypassing promotion criteria.
        """
        promotion = Promotion(
            id="single-instinct",
            reason="Force promoted"
        )

        global_path = instinct_manager.promote_instinct(promotion, force=True)

        assert global_path is not None
        assert global_path.exists()

    def test_records_promotion_reason(
        self, instinct_manager: InstinctManager, eligible_instinct_in_two_projects: dict[str, Path]
    ) -> None:
        """
        --reason should be recorded in the promoted instinct.
        """
        promotion = Promotion(
            id="promotable-instinct",
            reason="User requested promotion"
        )

        global_path = instinct_manager.promote_instinct(promotion)
        content = global_path.read_text()

        assert "User requested promotion" in content


class TestPromoteNonExistentInstinct:
    """Tests for promoting non-existent instincts."""

    def test_error_for_nonexistent_instinct(
        self, instinct_manager: InstinctManager
    ) -> None:
        """
        Should return None for non-existent instinct.
        """
        is_eligible, reason = instinct_manager.check_promotion_eligibility("nonexistent-instinct")

        assert not is_eligible
        assert "0 project" in reason.lower() or "not found" in reason.lower() or "need at least" in reason.lower()

    def test_promotion_returns_none_for_nonexistent(
        self, instinct_manager: InstinctManager
    ) -> None:
        """
        Promoting non-existent instinct should return None.
        """
        promotion = Promotion(
            id="nonexistent-instinct",
            reason="Should not work"
        )

        result = instinct_manager.promote_instinct(promotion)
        assert result is None


class TestPromoteCommandAudit:
    """Tests for promotion audit trail."""

    def test_records_promotion_timestamp(
        self, instinct_manager: InstinctManager, eligible_instinct_in_two_projects: dict[str, Path]
    ) -> None:
        """
        Promotion should record when it occurred.
        """
        promotion = Promotion(
            id="promotable-instinct",
            reason="Seen in 2 projects"
        )

        before = datetime.now(TZ_CST)
        global_path = instinct_manager.promote_instinct(promotion)
        after = datetime.now(TZ_CST)

        content = global_path.read_text()
        parts = content.split("---")
        frontmatter = yaml.safe_load(parts[1])

        promoted_at = datetime.fromisoformat(
            frontmatter.get("promoted_at", "2026-01-01T00:00:00+08:00")
        )

        # Compare timestamps without timezone info (both are in the same TZ)
        before_naive = before.replace(tzinfo=None)
        after_naive = after.replace(tzinfo=None)
        promoted_at_naive = promoted_at.replace(tzinfo=None)

        assert before_naive <= promoted_at_naive <= after_naive

    def test_records_source_projects(
        self, instinct_manager: InstinctManager, eligible_instinct_in_two_projects: dict[str, Path]
    ) -> None:
        """
        Promotion should record which projects the instinct came from.
        """
        promotion = Promotion(
            id="promotable-instinct",
            reason="Seen in 2 projects"
        )

        global_path = instinct_manager.promote_instinct(promotion)
        content = global_path.read_text()

        # Should mention source projects
        assert "proj-eligible" in content or "source_projects" in content.lower()


class TestPromoteScriptExecution:
    """Tests for promote script execution.

    These tests verify the script wrapper works correctly.
    The scripts are currently stubs, so these tests should FAIL.
    """

    def test_script_returns_zero_exit_code(
        self, promote_script: Path, eligible_instinct_in_two_projects: dict[str, Path], temp_home: Path
    ) -> None:
        """
        Script should return exit code 0 on success.

        Currently FAILS because script is a stub.
        """
        import subprocess

        env = {"HOME": str(temp_home)}

        result = subprocess.run(
            [sys.executable, str(promote_script), "promotable-instinct", "--force"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        assert result.returncode == 0, f"Script failed: {result.stderr}"

    def test_script_outputs_promotion_result(
        self, promote_script: Path, eligible_instinct_in_two_projects: dict[str, Path], temp_home: Path
    ) -> None:
        """
        Script should output the promotion result.

        Currently FAILS because script is a stub.
        """
        import subprocess

        env = {"HOME": str(temp_home)}

        result = subprocess.run(
            [sys.executable, str(promote_script), "promotable-instinct", "--force"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30
        )

        # Should mention promotion or success
        output = result.stdout.lower()
        assert "promoted" in output or "success" in output or "global" in output, \
            f"Expected promotion result in output: {result.stdout}"
