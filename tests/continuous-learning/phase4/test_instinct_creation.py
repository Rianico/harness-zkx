"""
Tests for instinct creation.

Eval 4.1: Instinct Creation

Input: Agent result with new instinct
Expected: YAML file created in correct location

Pass criteria:
- [ ] File created at `instincts/personal/<id>.yaml`
- [ ] YAML frontmatter valid
- [ ] Content matches agent result
- [ ] Timestamps set correctly
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from hooks.observe.agent_runner import AgentResult, InstinctCreated, Evidence
from hooks.observe.instinct_manager import InstinctManager


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
AGENT_RESULTS_DIR = FIXTURES_DIR / "agent_results"


@pytest.fixture
def creation_result() -> dict:
    """Load agent result with instinct to create."""
    with open(AGENT_RESULTS_DIR / "creation_result.json") as f:
        return json.load(f)


@pytest.fixture
def instinct_manager(homunculus_dir: Path) -> InstinctManager:
    """Create instinct manager instance."""
    return InstinctManager(homunculus_dir)


@pytest.fixture
def project_instincts_dir(homunculus_dir: Path) -> Path:
    """Create project instincts directory."""
    project_id = "a1b2c3d4e5f6"
    instincts_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
    instincts_dir.mkdir(parents=True, exist_ok=True)
    return instincts_dir


class TestInstinctCreation:
    """Tests for creating instinct YAML files from agent results."""

    def test_creates_yaml_file_at_correct_location(
        self, instinct_manager: InstinctManager, project_instincts_dir: Path
    ) -> None:
        """
        Eval 4.1: File created at `instincts/personal/<id>.yaml`.

        When an agent result contains a new instinct, the manager should
        create a YAML file in the project's instincts directory.
        """
        instinct = InstinctCreated(
            id="read-before-write",
            trigger="when writing new files",
            confidence=0.5,
            domain="workflow",
            action="Read existing files first",
            evidence=[Evidence(session_id="s1", description="Test")]
        )
        project_id = "a1b2c3d4e5f6"

        file_path = instinct_manager.create_instinct(instinct, project_id)

        assert file_path is not None
        assert file_path.exists()
        assert file_path.name == "read-before-write.yaml"
        assert "projects" in str(file_path)
        assert project_id in str(file_path)

    def test_yaml_frontmatter_valid(
        self, instinct_manager: InstinctManager, project_instincts_dir: Path
    ) -> None:
        """
        Eval 4.1: YAML frontmatter valid.

        The created file should have valid YAML frontmatter with all
        required fields from the instinct schema.
        """
        instinct = InstinctCreated(
            id="test-instinct",
            trigger="test trigger",
            confidence=0.7,
            domain="workflow",
            action="Test action",
            evidence=[Evidence(session_id="s1", description="Test")]
        )
        project_id = "a1b2c3d4e5f6"

        file_path = instinct_manager.create_instinct(instinct, project_id)
        content = file_path.read_text()

        # Parse frontmatter (between --- markers)
        parts = content.split("---")
        assert len(parts) >= 3, "File should have YAML frontmatter"

        frontmatter = yaml.safe_load(parts[1])
        assert frontmatter["id"] == "test-instinct"
        assert frontmatter["trigger"] == "test trigger"
        assert frontmatter["confidence"] == 0.7
        assert frontmatter["domain"] == "workflow"
        assert frontmatter["scope"] == "project"
        assert frontmatter["project_id"] == project_id

    def test_content_matches_agent_result(
        self, instinct_manager: InstinctManager, project_instincts_dir: Path
    ) -> None:
        """
        Eval 4.1: Content matches agent result.

        The instinct content (action and evidence) should be preserved
        from the agent result in the YAML file body.
        """
        instinct = InstinctCreated(
            id="read-before-write",
            trigger="when writing new files",
            confidence=0.5,
            domain="workflow",
            action="Read existing files in the same directory to understand patterns",
            evidence=[
                Evidence(session_id="session-001", description="First evidence"),
                Evidence(session_id="session-002", description="Second evidence")
            ]
        )
        project_id = "a1b2c3d4e5f6"

        file_path = instinct_manager.create_instinct(instinct, project_id)
        content = file_path.read_text()

        # Check action is in content
        assert "Read existing files in the same directory" in content

        # Check evidence is recorded
        assert "session-001" in content
        assert "First evidence" in content
        assert "session-002" in content
        assert "Second evidence" in content

    def test_timestamps_set_correctly(
        self, instinct_manager: InstinctManager, project_instincts_dir: Path
    ) -> None:
        """
        Eval 4.1: Timestamps set correctly.

        Both created_at and updated_at should be set to current time
        when creating a new instinct.
        """
        instinct = InstinctCreated(
            id="timestamp-test",
            trigger="test trigger",
            confidence=0.5,
            domain="workflow",
            action="Test action",
            evidence=[Evidence(session_id="s1", description="Test")]
        )
        project_id = "a1b2c3d4e5f6"

        before = datetime.now(timezone.utc)
        file_path = instinct_manager.create_instinct(instinct, project_id)
        after = datetime.now(timezone.utc)

        content = file_path.read_text()
        parts = content.split("---")
        frontmatter = yaml.safe_load(parts[1])

        created_at = datetime.fromisoformat(frontmatter["created_at"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(frontmatter["updated_at"].replace("Z", "+00:00"))

        assert before <= created_at <= after
        assert before <= updated_at <= after
        assert created_at == updated_at

    def test_evidence_count_in_frontmatter(
        self, instinct_manager: InstinctManager, project_instincts_dir: Path
    ) -> None:
        """
        Evidence count should match number of evidence items.
        """
        instinct = InstinctCreated(
            id="evidence-count-test",
            trigger="test trigger",
            confidence=0.5,
            domain="workflow",
            action="Test action",
            evidence=[
                Evidence(session_id="s1", description="First"),
                Evidence(session_id="s2", description="Second"),
                Evidence(session_id="s3", description="Third")
            ]
        )
        project_id = "a1b2c3d4e5f6"

        file_path = instinct_manager.create_instinct(instinct, project_id)
        content = file_path.read_text()
        parts = content.split("---")
        frontmatter = yaml.safe_load(parts[1])

        assert frontmatter["evidence_count"] == 3

    def test_processes_agent_result_creates_multiple_instincts(
        self, instinct_manager: InstinctManager, project_instincts_dir: Path
    ) -> None:
        """
        Processing an AgentResult should create all instincts in instincts_created.
        """
        result = AgentResult(
            instincts_created=[
                InstinctCreated(
                    id="first-instinct",
                    trigger="trigger 1",
                    confidence=0.5,
                    domain="workflow",
                    action="Action 1",
                    evidence=[Evidence(session_id="s1", description="Test")]
                ),
                InstinctCreated(
                    id="second-instinct",
                    trigger="trigger 2",
                    confidence=0.6,
                    domain="debugging",
                    action="Action 2",
                    evidence=[Evidence(session_id="s2", description="Test")]
                )
            ],
            instincts_updated=[],
            promotions=[],
            processed_count=10,
            cursor_position=10
        )
        project_id = "a1b2c3d4e5f6"

        created_paths = instinct_manager.process_result(result, project_id)

        assert len(created_paths) == 2
        assert all(p.exists() for p in created_paths)

    def test_does_not_overwrite_existing_instinct(
        self, instinct_manager: InstinctManager, project_instincts_dir: Path
    ) -> None:
        """
        Creating an instinct that already exists should not overwrite.
        Instead, it should be added to instincts_updated.
        """
        # Create initial instinct
        instinct = InstinctCreated(
            id="existing-instinct",
            trigger="test trigger",
            confidence=0.5,
            domain="workflow",
            action="Original action",
            evidence=[Evidence(session_id="s1", description="Original")]
        )
        project_id = "a1b2c3d4e5f6"
        file_path = instinct_manager.create_instinct(instinct, project_id)
        original_content = file_path.read_text()

        # Try to create the same instinct again
        new_instinct = InstinctCreated(
            id="existing-instinct",
            trigger="new trigger",
            confidence=0.7,
            domain="workflow",
            action="New action",
            evidence=[Evidence(session_id="s2", description="New")]
        )

        result = instinct_manager.create_instinct(new_instinct, project_id)

        # Should return None (not created) and file should be unchanged
        assert result is None
        assert file_path.read_text() == original_content


class TestInstinctCreationGlobalScope:
    """Tests for creating instincts at global scope."""

    def test_creates_global_instinct_in_personal_dir(
        self, instinct_manager: InstinctManager, homunculus_dir: Path
    ) -> None:
        """
        Creating an instinct with global scope should use the global directory.
        """
        instinct = InstinctCreated(
            id="global-instinct",
            trigger="test trigger",
            confidence=0.5,
            domain="workflow",
            action="Global action",
            evidence=[Evidence(session_id="s1", description="Test")]
        )

        file_path = instinct_manager.create_instinct(instinct, scope="global")

        assert file_path is not None
        assert file_path.exists()
        assert "instincts" in str(file_path)
        assert "personal" in str(file_path)
        assert "projects" not in str(file_path)
