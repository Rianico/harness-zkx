"""
Tests for user correction pattern detection.

Eval 3.1: Pattern Detection - User Correction

Input: Session with user correction pattern
Expected: Instinct created with confidence 0.5+

Pass criteria:
- [ ] Correction pattern detected
- [ ] Instinct created with appropriate trigger
- [ ] Confidence in range [0.3, 0.9]
- [ ] Evidence recorded
"""

import json
from pathlib import Path

import pytest

from hooks.observe.agent_runner import AgentRunner, AgentResult


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
SESSIONS_DIR = FIXTURES_DIR / "sessions"
EXPECTED_DIR = FIXTURES_DIR / "expected_outputs"


@pytest.fixture
def user_correction_session() -> list[dict]:
    """Load user correction session fixture."""
    with open(SESSIONS_DIR / "user_correction.json") as f:
        return json.load(f)


@pytest.fixture
def expected_user_correction_output() -> dict:
    """Load expected output for user correction pattern."""
    with open(EXPECTED_DIR / "user_correction.json") as f:
        return json.load(f)


@pytest.fixture
def agent_runner() -> AgentRunner:
    """Create agent runner instance."""
    return AgentRunner()


class TestUserCorrectionPattern:
    """Tests for user correction pattern detection."""

    def test_detects_rejection_followed_by_different_action(
        self, agent_runner: AgentRunner, user_correction_session: list[dict]
    ) -> None:
        """
        Eval 3.1: Detect when user rejects a suggestion and takes a different action.

        Pattern: Edit rejected -> Read -> Edit succeeds
        This indicates the user wanted to read context first.
        """
        result = agent_runner.analyze_session(
            session_id="correction-1",
            events=user_correction_session
        )

        assert result is not None
        assert len(result.instincts_created) >= 1

        instinct = result.instincts_created[0]
        assert instinct.trigger is not None
        assert "reject" in instinct.trigger.lower() or "rejection" in instinct.trigger.lower()

    def test_creates_instinct_with_correct_confidence(
        self, agent_runner: AgentRunner, user_correction_session: list[dict]
    ) -> None:
        """
        Eval 3.1: Instinct should have confidence in range [0.3, 0.9].

        User corrections start at confidence 0.5.
        """
        result = agent_runner.analyze_session(
            session_id="correction-1",
            events=user_correction_session
        )

        assert result is not None
        instinct = result.instincts_created[0]
        assert 0.3 <= instinct.confidence <= 0.9, \
            f"Confidence {instinct.confidence} not in valid range [0.3, 0.9]"

    def test_records_evidence(
        self, agent_runner: AgentRunner, user_correction_session: list[dict]
    ) -> None:
        """
        Eval 3.1: Evidence should be recorded with the instinct.
        """
        result = agent_runner.analyze_session(
            session_id="correction-1",
            events=user_correction_session
        )

        assert result is not None
        instinct = result.instincts_created[0]
        assert instinct.evidence is not None
        assert len(instinct.evidence) >= 1
        assert any("correction-1" in str(e) for e in instinct.evidence)

    def test_domain_is_workflow(
        self, agent_runner: AgentRunner, user_correction_session: list[dict]
    ) -> None:
        """
        Eval 3.1: User correction patterns should be in 'workflow' domain.
        """
        result = agent_runner.analyze_session(
            session_id="correction-1",
            events=user_correction_session
        )

        assert result is not None
        instinct = result.instincts_created[0]
        assert instinct.domain == "workflow"

    def test_no_false_positives_on_normal_edit(
        self, agent_runner: AgentRunner
    ) -> None:
        """
        Normal edit sequence without rejection should not create correction instinct.
        """
        normal_session = [
            {"timestamp": "2026-04-30T10:00:00Z", "event": "tool_start", "tool": "Edit", "session": "normal-1"},
            {"timestamp": "2026-04-30T10:00:05Z", "event": "tool_complete", "tool": "Edit", "session": "normal-1", "output": "success"},
        ]

        result = agent_runner.analyze_session(
            session_id="normal-1",
            events=normal_session
        )

        # Should not create a correction instinct for normal successful edits
        correction_instincts = [
            i for i in (result.instincts_created or [])
            if "reject" in i.trigger.lower()
        ]
        assert len(correction_instincts) == 0


class TestAgentRunnerIntegration:
    """Integration tests for agent runner with user correction pattern."""

    def test_full_payload_processing(
        self, agent_runner: AgentRunner, user_correction_session: list[dict]
    ) -> None:
        """
        Full payload should be processed and return valid AgentResult.
        """
        payload = {
            "sessions": [
                {
                    "session_id": "correction-1",
                    "events": user_correction_session
                }
            ],
            "project_id": "test-project",
            "project_name": "Test Project"
        }

        result = agent_runner.run(payload)

        assert isinstance(result, AgentResult)
        assert result.processed_count == len(user_correction_session)
        assert result.cursor_position == len(user_correction_session)

    def test_result_matches_expected_schema(
        self, agent_runner: AgentRunner, user_correction_session: list[dict],
        expected_user_correction_output: dict
    ) -> None:
        """
        Result should match the expected output schema.
        """
        payload = {
            "sessions": [
                {
                    "session_id": "correction-1",
                    "events": user_correction_session
                }
            ],
            "project_id": "test-project",
            "project_name": "Test Project"
        }

        result = agent_runner.run(payload)

        # Validate schema
        assert hasattr(result, 'instincts_created')
        assert hasattr(result, 'instincts_updated')
        assert hasattr(result, 'promotions')
        assert hasattr(result, 'processed_count')
        assert hasattr(result, 'cursor_position')
