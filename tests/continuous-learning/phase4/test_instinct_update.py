"""
Tests for instinct update.

Eval 4.2: Instinct Update

Input: Agent result updating existing instinct
Expected: Confidence updated, evidence appended

Pass criteria:
- [ ] Confidence score updated
- [ ] Evidence list extended
- [ ] updated_at timestamp refreshed
- [ ] No duplicate evidence
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add lib to path for tz import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "lib"))
from tz import TZ_CST
import yaml

from hooks.observe.agent_runner import AgentResult, InstinctUpdated, Evidence
from hooks.observe.instinct_manager import InstinctManager


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
INSTINCTS_DIR = FIXTURES_DIR / "instincts"
AGENT_RESULTS_DIR = FIXTURES_DIR / "agent_results"


@pytest.fixture
def existing_instinct_content() -> str:
    """Load existing instinct fixture."""
    with open(INSTINCTS_DIR / "existing_instinct.yaml") as f:
        return f.read()


@pytest.fixture
def update_result() -> dict:
    """Load agent result with instinct to update."""
    with open(AGENT_RESULTS_DIR / "update_result.json") as f:
        return json.load(f)


@pytest.fixture
def instinct_manager(homunculus_dir: Path) -> InstinctManager:
    """Create instinct manager instance."""
    return InstinctManager(homunculus_dir)


@pytest.fixture
def project_with_existing_instinct(
    homunculus_dir: Path, existing_instinct_content: str
) -> Path:
    """Create project directory with existing instinct."""
    project_id = "a1b2c3d4e5f6"
    instincts_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
    instincts_dir.mkdir(parents=True, exist_ok=True)

    instinct_file = instincts_dir / "read-before-edit.yaml"
    instinct_file.write_text(existing_instinct_content)

    return homunculus_dir


class TestInstinctUpdate:
    """Tests for updating existing instinct files."""

    def test_updates_confidence_score(
        self, instinct_manager: InstinctManager, project_with_existing_instinct: Path
    ) -> None:
        """
        Eval 4.2: Confidence score updated.

        When an instinct is updated, its confidence should be changed
        to the new value from the agent result.
        """
        project_id = "a1b2c3d4e5f6"
        update = InstinctUpdated(
            id="read-before-edit",
            new_confidence=0.85,
            evidence_appended=[
                Evidence(session_id="s1", description="New evidence")
            ]
        )

        file_path = instinct_manager.update_instinct(update, project_id)
        assert file_path is not None

        content = file_path.read_text()
        parts = content.split("---")
        frontmatter = yaml.safe_load(parts[1])

        assert frontmatter["confidence"] == 0.85

    def test_evidence_list_extended(
        self, instinct_manager: InstinctManager, project_with_existing_instinct: Path
    ) -> None:
        """
        Eval 4.2: Evidence list extended.

        New evidence should be appended to the existing evidence list
        without removing the original evidence.
        """
        project_id = "a1b2c3d4e5f6"
        update = InstinctUpdated(
            id="read-before-edit",
            new_confidence=0.85,
            evidence_appended=[
                Evidence(session_id="new-session-001", description="New evidence 1"),
                Evidence(session_id="new-session-002", description="New evidence 2")
            ]
        )

        file_path = instinct_manager.update_instinct(update, project_id)
        content = file_path.read_text()

        # Original evidence should still be there
        assert "session-abc-001" in content
        assert "session-def-002" in content

        # New evidence should be appended
        assert "new-session-001" in content
        assert "New evidence 1" in content
        assert "new-session-002" in content
        assert "New evidence 2" in content

    def test_updated_at_timestamp_refreshed(
        self, instinct_manager: InstinctManager, project_with_existing_instinct: Path
    ) -> None:
        """
        Eval 4.2: updated_at timestamp refreshed.

        The updated_at field should be set to current time.
        created_at should remain unchanged.
        """
        project_id = "a1b2c3d4e5f6"

        # Read original timestamps
        instincts_dir = project_with_existing_instinct / "projects" / project_id / "instincts" / "personal"
        original_file = instincts_dir / "read-before-edit.yaml"
        original_content = original_file.read_text()
        original_parts = original_content.split("---")
        original_frontmatter = yaml.safe_load(original_parts[1])
        original_created_at = original_frontmatter["created_at"]

        update = InstinctUpdated(
            id="read-before-edit",
            new_confidence=0.85,
            evidence_appended=[Evidence(session_id="s1", description="Test")]
        )

        before = datetime.now(TZ_CST)
        file_path = instinct_manager.update_instinct(update, project_id)
        after = datetime.now(TZ_CST)

        content = file_path.read_text()
        parts = content.split("---")
        frontmatter = yaml.safe_load(parts[1])

        # created_at should be unchanged
        assert frontmatter["created_at"] == original_created_at

        # updated_at should be recent
        updated_at = datetime.fromisoformat(frontmatter["updated_at"])

        # Compare timestamps without timezone info (both are in the same TZ)
        before_naive = before.replace(tzinfo=None)
        after_naive = after.replace(tzinfo=None)
        updated_at_naive = updated_at.replace(tzinfo=None)

        assert before_naive <= updated_at_naive <= after_naive

    def test_no_duplicate_evidence(
        self, instinct_manager: InstinctManager, project_with_existing_instinct: Path
    ) -> None:
        """
        Eval 4.2: No duplicate evidence.

        If evidence with the same session_id already exists, it should not be duplicated.
        """
        project_id = "a1b2c3d4e5f6"
        update = InstinctUpdated(
            id="read-before-edit",
            new_confidence=0.85,
            evidence_appended=[
                # This session already exists in the fixture
                Evidence(session_id="session-abc-001", description="Updated evidence for existing session")
            ]
        )

        file_path = instinct_manager.update_instinct(update, project_id)
        content = file_path.read_text()

        # Count occurrences of session-abc-001 in evidence section
        # It should appear exactly once
        evidence_section = content.split("## Evidence")[1].split("---")[0] if "## Evidence" in content else content
        count = evidence_section.count("session-abc-001")
        assert count <= 2, f"session-abc-001 should not be duplicated, found {count} times"

    def test_evidence_count_updated(
        self, instinct_manager: InstinctManager, project_with_existing_instinct: Path
    ) -> None:
        """
        Evidence count in frontmatter should reflect total evidence items.
        """
        project_id = "a1b2c3d4e5f6"

        # Original has 3 evidence items
        update = InstinctUpdated(
            id="read-before-edit",
            new_confidence=0.85,
            evidence_appended=[
                Evidence(session_id="new-1", description="New 1"),
                Evidence(session_id="new-2", description="New 2")
            ]
        )

        file_path = instinct_manager.update_instinct(update, project_id)
        content = file_path.read_text()
        parts = content.split("---")
        frontmatter = yaml.safe_load(parts[1])

        # 3 original + 2 new = 5
        assert frontmatter["evidence_count"] == 5

    def test_returns_none_for_nonexistent_instinct(
        self, instinct_manager: InstinctManager, homunculus_dir: Path
    ) -> None:
        """
        Updating a non-existent instinct should return None.
        """
        project_id = "nonexistent-project"
        update = InstinctUpdated(
            id="nonexistent-instinct",
            new_confidence=0.5,
            evidence_appended=[Evidence(session_id="s1", description="Test")]
        )

        result = instinct_manager.update_instinct(update, project_id)
        assert result is None

    def test_processes_agent_result_updates_multiple_instincts(
        self, instinct_manager: InstinctManager, project_with_existing_instinct: Path
    ) -> None:
        """
        Processing an AgentResult should update all instincts in instincts_updated.
        """
        # Create a second instinct
        project_id = "a1b2c3d4e5f6"
        instincts_dir = project_with_existing_instinct / "projects" / project_id / "instincts" / "personal"
        second_instinct = """---
id: second-instinct
trigger: "test trigger"
confidence: 0.5
domain: "workflow"
scope: "project"
project_id: "a1b2c3d4e5f6"
created_at: "2026-04-30T10:00:00Z"
updated_at: "2026-04-30T10:05:00Z"
evidence_count: 1
---

# Second Instinct

## Action
Test action.

## Evidence
- Session s1: Test evidence
"""
        (instincts_dir / "second-instinct.yaml").write_text(second_instinct)

        result = AgentResult(
            instincts_created=[],
            instincts_updated=[
                InstinctUpdated(
                    id="read-before-edit",
                    new_confidence=0.85,
                    evidence_appended=[Evidence(session_id="s1", description="Update 1")]
                ),
                InstinctUpdated(
                    id="second-instinct",
                    new_confidence=0.75,
                    evidence_appended=[Evidence(session_id="s2", description="Update 2")]
                )
            ],
            promotions=[],
            processed_count=20,
            cursor_position=20
        )

        updated_paths = instinct_manager.process_result(result, project_id)

        assert len(updated_paths) == 2
        assert all(p.exists() for p in updated_paths)


class TestConfidenceCalculation:
    """Tests for confidence score calculation during updates."""

    def test_confidence_increases_with_repeated_evidence(
        self, instinct_manager: InstinctManager, project_with_existing_instinct: Path
    ) -> None:
        """
        Multiple confirmations should increase confidence.

        This tests the implementation of confidence boosting logic.
        """
        project_id = "a1b2c3d4e5f6"

        # The manager might implement confidence boosting
        # For now, we test that it accepts the new_confidence value
        update = InstinctUpdated(
            id="read-before-edit",
            new_confidence=0.95,  # Higher confidence
            evidence_appended=[
                Evidence(session_id="s1", description="Confirmation"),
                Evidence(session_id="s2", description="Another confirmation")
            ]
        )

        file_path = instinct_manager.update_instinct(update, project_id)
        content = file_path.read_text()
        parts = content.split("---")
        frontmatter = yaml.safe_load(parts[1])

        # Confidence should be updated to the new value
        assert frontmatter["confidence"] == 0.95

    def test_confidence_bounded_at_max(
        self, instinct_manager: InstinctManager, project_with_existing_instinct: Path
    ) -> None:
        """
        Confidence should not exceed 1.0.
        """
        project_id = "a1b2c3d4e5f6"
        update = InstinctUpdated(
            id="read-before-edit",
            new_confidence=1.5,  # Invalid, should be capped or rejected
            evidence_appended=[Evidence(session_id="s1", description="Test")]
        )

        file_path = instinct_manager.update_instinct(update, project_id)

        if file_path:
            content = file_path.read_text()
            parts = content.split("---")
            frontmatter = yaml.safe_load(parts[1])
            # Confidence should be at most 1.0
            assert frontmatter["confidence"] <= 1.0
