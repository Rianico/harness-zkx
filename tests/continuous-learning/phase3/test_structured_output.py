"""
Tests for agent structured output validation.

Eval 3.4: Structured Output

Input: Any valid observation payload
Expected: Valid JSON result matching schema

Pass criteria:
- [ ] Output is valid JSON
- [ ] Schema validation passes
- [ ] No extra fields
- [ ] Required fields present
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from hooks.observe.agent_runner import AgentRunner, AgentResult, InstinctCreated, InstinctUpdated, Promotion


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
SESSIONS_DIR = FIXTURES_DIR / "sessions"


@pytest.fixture
def agent_runner() -> AgentRunner:
    """Create agent runner instance."""
    return AgentRunner()


@pytest.fixture
def sample_payload() -> dict:
    """Create a sample observation payload."""
    with open(SESSIONS_DIR / "user_correction.json") as f:
        session = json.load(f)

    return {
        "sessions": [
            {
                "session_id": "test-session",
                "events": session
            }
        ],
        "project_id": "a1b2c3d4e5f6",
        "project_name": "test-project",
        "cursor_position": 0
    }


class TestInstinctCreatedSchema:
    """Tests for InstinctCreated schema validation."""

    def test_valid_instinct_created(self) -> None:
        """Valid InstinctCreated should pass validation."""
        instinct = InstinctCreated(
            id="test-instinct",
            trigger="when test condition",
            confidence=0.5,
            domain="workflow",
            action="do something",
            evidence=[{"session_id": "s1", "description": "test evidence"}]
        )

        assert instinct.id == "test-instinct"
        assert instinct.confidence == 0.5
        assert instinct.domain == "workflow"

    def test_confidence_bounds(self) -> None:
        """Confidence must be between 0 and 1."""
        # Valid bounds
        InstinctCreated(
            id="test",
            trigger="test",
            confidence=0.0,
            domain="workflow"
        )
        InstinctCreated(
            id="test",
            trigger="test",
            confidence=1.0,
            domain="workflow"
        )

        # Invalid bounds should raise
        with pytest.raises(ValidationError):
            InstinctCreated(
                id="test",
                trigger="test",
                confidence=1.5,
                domain="workflow"
            )
        with pytest.raises(ValidationError):
            InstinctCreated(
                id="test",
                trigger="test",
                confidence=-0.1,
                domain="workflow"
            )

    def test_required_fields(self) -> None:
        """Required fields must be present."""
        with pytest.raises(ValidationError):
            InstinctCreated()  # Missing all required fields

        with pytest.raises(ValidationError):
            InstinctCreated(id="test")  # Missing trigger, confidence, domain

    def test_optional_fields(self) -> None:
        """Optional fields should work."""
        instinct = InstinctCreated(
            id="test",
            trigger="test",
            confidence=0.5,
            domain="workflow"
        )
        assert instinct.action is None
        assert instinct.evidence is None


class TestInstinctUpdatedSchema:
    """Tests for InstinctUpdated schema validation."""

    def test_valid_instinct_updated(self) -> None:
        """Valid InstinctUpdated should pass validation."""
        update = InstinctUpdated(
            id="existing-instinct",
            new_confidence=0.8,
            evidence_appended=[{"session_id": "s1", "description": "test"}]
        )

        assert update.id == "existing-instinct"
        assert update.new_confidence == 0.8

    def test_required_fields(self) -> None:
        """Required fields must be present."""
        with pytest.raises(ValidationError):
            InstinctUpdated()  # Missing id, new_confidence


class TestPromotionSchema:
    """Tests for Promotion schema validation."""

    def test_valid_promotion(self) -> None:
        """Valid Promotion should pass validation."""
        promo = Promotion(
            id="instinct-to-promote",
            reason="Seen in 3 projects with high confidence"
        )

        assert promo.id == "instinct-to-promote"
        assert promo.reason is not None


class TestAgentResultSchema:
    """Tests for AgentResult schema validation."""

    def test_valid_agent_result(self) -> None:
        """Valid AgentResult should pass validation."""
        result = AgentResult(
            instincts_created=[],
            instincts_updated=[],
            promotions=[],
            processed_count=100,
            cursor_position=100
        )

        assert result.processed_count == 100
        assert result.cursor_position == 100

    def test_with_instincts(self) -> None:
        """AgentResult with instincts should validate."""
        result = AgentResult(
            instincts_created=[
                InstinctCreated(
                    id="test",
                    trigger="test trigger",
                    confidence=0.5,
                    domain="workflow"
                )
            ],
            instincts_updated=[
                InstinctUpdated(
                    id="existing",
                    new_confidence=0.8
                )
            ],
            promotions=[
                Promotion(
                    id="promoted",
                    reason="Test promotion"
                )
            ],
            processed_count=50,
            cursor_position=50
        )

        assert len(result.instincts_created) == 1
        assert len(result.instincts_updated) == 1
        assert len(result.promotions) == 1

    def test_required_fields(self) -> None:
        """Required fields must be present."""
        with pytest.raises(ValidationError):
            AgentResult()  # Missing processed_count, cursor_position

    def test_no_extra_fields_allowed(self) -> None:
        """Extra fields should be rejected."""
        with pytest.raises(ValidationError):
            AgentResult(
                instincts_created=[],
                instincts_updated=[],
                promotions=[],
                processed_count=10,
                cursor_position=10,
                extra_field="not allowed"  # type: ignore
            )


class TestAgentRunnerOutput:
    """Tests for agent runner output validation."""

    def test_run_returns_valid_agent_result(
        self, agent_runner: AgentRunner, sample_payload: dict
    ) -> None:
        """
        Eval 3.4: run() should return valid AgentResult.
        """
        result = agent_runner.run(sample_payload)

        assert isinstance(result, AgentResult)
        assert isinstance(result.processed_count, int)
        assert isinstance(result.cursor_position, int)

    def test_output_serializes_to_json(
        self, agent_runner: AgentRunner, sample_payload: dict
    ) -> None:
        """
        Eval 3.4: Output should serialize to valid JSON.
        """
        result = agent_runner.run(sample_payload)

        # Should be able to serialize to JSON
        json_str = result.model_dump_json()
        parsed = json.loads(json_str)

        assert isinstance(parsed, dict)
        assert "instincts_created" in parsed
        assert "processed_count" in parsed

    def test_processed_count_matches_events(
        self, agent_runner: AgentRunner, sample_payload: dict
    ) -> None:
        """
        processed_count should match total events processed.
        """
        result = agent_runner.run(sample_payload)

        total_events = sum(
            len(s["events"]) for s in sample_payload["sessions"]
        )
        assert result.processed_count == total_events

    def test_cursor_position_advanced(
        self, agent_runner: AgentRunner, sample_payload: dict
    ) -> None:
        """
        cursor_position should be advanced beyond starting position.
        """
        initial_cursor = sample_payload.get("cursor_position", 0)
        result = agent_runner.run(sample_payload)

        assert result.cursor_position > initial_cursor

    def test_empty_sessions_handled(
        self, agent_runner: AgentRunner
    ) -> None:
        """
        Empty sessions should return valid result with count 0.
        """
        payload = {
            "sessions": [],
            "project_id": "test",
            "project_name": "test",
            "cursor_position": 0
        }

        result = agent_runner.run(payload)

        assert result.processed_count == 0
        assert result.cursor_position == 0
        assert len(result.instincts_created) == 0


class TestSchemaCompleteness:
    """Tests for schema completeness per eval criteria."""

    def test_all_required_fields_present(
        self, agent_runner: AgentRunner, sample_payload: dict
    ) -> None:
        """
        Eval 3.4: All required fields must be present in output.
        """
        result = agent_runner.run(sample_payload)
        result_dict = result.model_dump()

        required_fields = [
            "instincts_created",
            "instincts_updated",
            "promotions",
            "processed_count",
            "cursor_position"
        ]

        for field in required_fields:
            assert field in result_dict, f"Missing required field: {field}"

    def test_no_extra_fields_in_output(
        self, agent_runner: AgentRunner, sample_payload: dict
    ) -> None:
        """
        Eval 3.4: No extra fields in output.
        """
        result = agent_runner.run(sample_payload)
        result_dict = result.model_dump()

        expected_fields = {
            "instincts_created",
            "instincts_updated",
            "promotions",
            "processed_count",
            "cursor_position"
        }

        extra_fields = set(result_dict.keys()) - expected_fields
        assert len(extra_fields) == 0, f"Unexpected extra fields: {extra_fields}"
