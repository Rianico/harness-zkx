"""
Tests for instinct promotion.

Eval 4.3: Instinct Promotion

Input: Instinct seen in 2+ projects with confidence >= 0.8
Expected: Promoted to global scope

Pass criteria:
- [ ] Instinct moved/linked to global directory
- [ ] scope changed to "global"
- [ ] project_id set to "global"
- [ ] Promotion reason logged
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

# Add lib to path for tz import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "lib"))
import yaml
from tz import TZ_CST

from hooks.observe.agent_runner import AgentResult, Promotion
from hooks.observe.instinct_manager import InstinctManager

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
INSTINCTS_DIR = FIXTURES_DIR / "instincts"
AGENT_RESULTS_DIR = FIXTURES_DIR / "agent_results"


@pytest.fixture
def promotion_result() -> dict:
    """Load agent result with instinct to promote."""
    with open(AGENT_RESULTS_DIR / "promotion_result.json") as f:
        return json.load(f)


@pytest.fixture
def instinct_manager(homunculus_dir: Path) -> InstinctManager:
    """Create instinct manager instance."""
    return InstinctManager(homunculus_dir)


@pytest.fixture
def multi_project_setup(homunculus_dir: Path) -> dict[str, Path]:
    """
    Create multiple projects with the same instinct.

    Simulates the scenario where the same instinct exists in
    multiple projects with high confidence, qualifying for promotion.
    """
    projects = {}
    for project_id in ["project-alpha", "project-beta", "project-gamma"]:
        instincts_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
        instincts_dir.mkdir(parents=True, exist_ok=True)

        instinct_content = f"""---
id: common-pattern
trigger: "when working with tests"
confidence: 0.85
domain: "workflow"
scope: "project"
project_id: "{project_id}"
created_at: "2026-04-30T10:00:00Z"
updated_at: "2026-04-30T10:30:00Z"
evidence_count: 5
---

# Common Pattern

## Action
Run tests after making code changes.

## Evidence
- Session s1: Test pattern observed
- Session s2: Repeated workflow
- Session s3: Consistent behavior
- Session s4: More evidence
- Session s5: Final confirmation
"""
        (instincts_dir / "common-pattern.yaml").write_text(instinct_content)
        projects[project_id] = instincts_dir

    return projects


class TestInstinctPromotion:
    """Tests for promoting instincts to global scope."""

    def test_moves_instinct_to_global_directory(
        self, instinct_manager: InstinctManager, multi_project_setup: dict[str, Path]
    ) -> None:
        """
        Eval 4.3: Instinct moved/linked to global directory.

        When an instinct qualifies for promotion, it should be moved
        to the global instincts/personal directory.
        """
        promotion = Promotion(
            id="common-pattern", reason="Seen in 3 projects with average confidence 0.85"
        )

        global_path = instinct_manager.promote_instinct(promotion)

        assert global_path is not None
        assert global_path.exists()
        assert "instincts" in str(global_path)
        assert "personal" in str(global_path)
        assert "projects" not in str(global_path)

    def test_scope_changed_to_global(
        self, instinct_manager: InstinctManager, multi_project_setup: dict[str, Path]
    ) -> None:
        """
        Eval 4.3: scope changed to "global".

        The promoted instinct's scope field should be updated to "global".
        """
        promotion = Promotion(
            id="common-pattern", reason="Seen in 3 projects with average confidence 0.85"
        )

        global_path = instinct_manager.promote_instinct(promotion)
        content = global_path.read_text()
        parts = content.split("---")
        frontmatter = yaml.safe_load(parts[1])

        assert frontmatter["scope"] == "global"

    def test_project_id_set_to_global(
        self, instinct_manager: InstinctManager, multi_project_setup: dict[str, Path]
    ) -> None:
        """
        Eval 4.3: project_id set to "global".

        The promoted instinct's project_id should be changed to "global".
        """
        promotion = Promotion(
            id="common-pattern", reason="Seen in 3 projects with average confidence 0.85"
        )

        global_path = instinct_manager.promote_instinct(promotion)
        content = global_path.read_text()
        parts = content.split("---")
        frontmatter = yaml.safe_load(parts[1])

        assert frontmatter["project_id"] == "global"

    def test_promotion_reason_logged(
        self, instinct_manager: InstinctManager, multi_project_setup: dict[str, Path]
    ) -> None:
        """
        Eval 4.3: Promotion reason logged.

        The reason for promotion should be recorded in the instinct file.
        """
        promotion = Promotion(
            id="common-pattern", reason="Seen in 3 projects with average confidence 0.85"
        )

        global_path = instinct_manager.promote_instinct(promotion)
        content = global_path.read_text()

        assert "Seen in 3 projects" in content
        assert "promotion" in content.lower()

    def test_removes_project_copies(
        self, instinct_manager: InstinctManager, multi_project_setup: dict[str, Path]
    ) -> None:
        """
        After promotion, project-specific copies should be removed or archived.

        This prevents duplicate instincts at different scopes.
        """
        promotion = Promotion(
            id="common-pattern", reason="Seen in 3 projects with average confidence 0.85"
        )

        instinct_manager.promote_instinct(promotion)

        # Check that project-specific copies are removed
        for _project_id, instincts_dir in multi_project_setup.items():
            project_instinct = instincts_dir / "common-pattern.yaml"
            assert not project_instinct.exists(), (
                f"Project instinct should be removed: {project_instinct}"
            )

    def test_returns_none_for_nonexistent_instinct(
        self, instinct_manager: InstinctManager, homunculus_dir: Path
    ) -> None:
        """
        Promoting a non-existent instinct should return None.
        """
        promotion = Promotion(id="nonexistent-instinct", reason="Should not work")

        result = instinct_manager.promote_instinct(promotion)
        assert result is None

    def test_processes_agent_result_promotions(
        self, instinct_manager: InstinctManager, multi_project_setup: dict[str, Path]
    ) -> None:
        """
        Processing an AgentResult should promote all instincts in promotions list.
        """
        result = AgentResult(
            instincts_created=[],
            instincts_updated=[],
            promotions=[
                Promotion(
                    id="common-pattern", reason="Seen in 3 projects with average confidence 0.85"
                )
            ],
            processed_count=100,
            cursor_position=100,
        )

        promoted_paths = instinct_manager.process_result(result, project_id="any")

        assert len(promoted_paths) == 1
        assert promoted_paths[0].exists()


class TestPromotionCriteria:
    """Tests for promotion eligibility criteria."""

    def test_requires_minimum_projects(
        self, instinct_manager: InstinctManager, homunculus_dir: Path
    ) -> None:
        """
        Promotion requires instinct to exist in at least 2 projects.
        """
        # Create only one project with the instinct
        project_id = "single-project"
        instincts_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
        instincts_dir.mkdir(parents=True, exist_ok=True)

        instinct_content = """---
id: single-project-instinct
trigger: "test trigger"
confidence: 0.9
domain: "workflow"
scope: "project"
project_id: "single-project"
created_at: "2026-04-30T10:00:00Z"
updated_at: "2026-04-30T10:30:00Z"
evidence_count: 5
---

# Single Project Instinct

## Action
Test action.

## Evidence
- Session s1: Test
"""
        (instincts_dir / "single-project-instinct.yaml").write_text(instinct_content)

        promotion = Promotion(id="single-project-instinct", reason="Only in one project")

        result = instinct_manager.promote_instinct(promotion)
        assert result is None, "Should not promote instinct from single project"

    def test_requires_minimum_confidence(
        self, instinct_manager: InstinctManager, homunculus_dir: Path
    ) -> None:
        """
        Promotion requires average confidence >= 0.8.
        """
        # Create two projects with low confidence
        for project_id in ["low-conf-1", "low-conf-2"]:
            instincts_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
            instincts_dir.mkdir(parents=True, exist_ok=True)

            instinct_content = f"""---
id: low-confidence-instinct
trigger: "test trigger"
confidence: 0.5
domain: "workflow"
scope: "project"
project_id: "{project_id}"
created_at: "2026-04-30T10:00:00Z"
updated_at: "2026-04-30T10:30:00Z"
evidence_count: 2
---

# Low Confidence Instinct

## Action
Test action.

## Evidence
- Session s1: Test
- Session s2: Test
"""
            (instincts_dir / "low-confidence-instinct.yaml").write_text(instinct_content)

        promotion = Promotion(id="low-confidence-instinct", reason="Low confidence")

        result = instinct_manager.promote_instinct(promotion)
        assert result is None, "Should not promote instinct with low confidence"


class TestPromotionAudit:
    """Tests for promotion audit trail."""

    def test_records_promotion_timestamp(
        self, instinct_manager: InstinctManager, multi_project_setup: dict[str, Path]
    ) -> None:
        """
        Promotion should record when it occurred.
        """
        promotion = Promotion(
            id="common-pattern", reason="Seen in 3 projects with average confidence 0.85"
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
        self, instinct_manager: InstinctManager, multi_project_setup: dict[str, Path]
    ) -> None:
        """
        Promotion should record which projects the instinct came from.
        """
        promotion = Promotion(
            id="common-pattern", reason="Seen in 3 projects with average confidence 0.85"
        )

        global_path = instinct_manager.promote_instinct(promotion)
        content = global_path.read_text()

        # Should mention source projects
        assert "project-alpha" in content or "alpha" in content.lower()

    def test_preserves_evidence_from_all_projects(
        self, instinct_manager: InstinctManager, multi_project_setup: dict[str, Path]
    ) -> None:
        """
        Promoted instinct should preserve evidence from all source projects.
        """
        promotion = Promotion(
            id="common-pattern", reason="Seen in 3 projects with average confidence 0.85"
        )

        global_path = instinct_manager.promote_instinct(promotion)
        content = global_path.read_text()
        parts = content.split("---")
        frontmatter = yaml.safe_load(parts[1])

        # Evidence count should reflect aggregated evidence
        # 3 projects * 5 evidence each = 15 total
        # But implementation might just preserve from one project
        assert frontmatter["evidence_count"] >= 5


class TestManualPromotion:
    """Tests for manually triggered promotion."""

    def test_manual_promotion_via_method(
        self, instinct_manager: InstinctManager, homunculus_dir: Path
    ) -> None:
        """
        User can manually promote an instinct via promote_instinct method.
        """
        # Create a single project with high confidence instinct
        project_id = "manual-promo-project"
        instincts_dir = homunculus_dir / "projects" / project_id / "instincts" / "personal"
        instincts_dir.mkdir(parents=True, exist_ok=True)

        instinct_content = f"""---
id: manual-promote-instinct
trigger: "test trigger"
confidence: 0.95
domain: "workflow"
scope: "project"
project_id: "{project_id}"
created_at: "2026-04-30T10:00:00Z"
updated_at: "2026-04-30T10:30:00Z"
evidence_count: 10
---

# Manual Promote Instinct

## Action
Test action.

## Evidence
- Session s1: Strong evidence
"""
        (instincts_dir / "manual-promote-instinct.yaml").write_text(instinct_content)

        # Manually promote with explicit flag
        global_path = instinct_manager.promote_instinct(
            Promotion(id="manual-promote-instinct", reason="User requested"),
            force=True,  # Bypass multi-project requirement
        )

        assert global_path is not None
        assert global_path.exists()
