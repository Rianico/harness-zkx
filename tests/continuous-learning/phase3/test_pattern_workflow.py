"""
Tests for repeated workflow pattern detection.

Eval 3.2: Pattern Detection - Repeated Workflow

Input: Session with repeated tool sequence
Expected: Instinct created with confidence 0.7+

Pass criteria:
- [ ] Workflow sequence detected
- [ ] Minimum 3 repetitions required
- [ ] Confidence starts at 0.7
"""

import json
from pathlib import Path

import pytest

from hooks.observe.agent_runner import AgentRunner, AgentResult


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
SESSIONS_DIR = FIXTURES_DIR / "sessions"
EXPECTED_DIR = FIXTURES_DIR / "expected_outputs"


@pytest.fixture
def repeated_workflow_session() -> list[dict]:
    """Load repeated workflow session fixture."""
    with open(SESSIONS_DIR / "repeated_workflow.json") as f:
        return json.load(f)


@pytest.fixture
def expected_workflow_output() -> dict:
    """Load expected output for repeated workflow pattern."""
    with open(EXPECTED_DIR / "repeated_workflow.json") as f:
        return json.load(f)


@pytest.fixture
def agent_runner() -> AgentRunner:
    """Create agent runner instance."""
    return AgentRunner()


class TestRepeatedWorkflowPattern:
    """Tests for repeated workflow pattern detection."""

    def test_detects_read_edit_bash_sequence(
        self, agent_runner: AgentRunner, repeated_workflow_session: list[dict]
    ) -> None:
        """
        Eval 3.2: Detect Read-Edit-Bash sequence repeated multiple times.

        Pattern: Read -> Edit -> Bash repeated 3+ times.
        """
        result = agent_runner.analyze_session(
            session_id="workflow-1",
            events=repeated_workflow_session
        )

        assert result is not None
        assert len(result.instincts_created) >= 1

        instinct = result.instincts_created[0]
        # Should identify the workflow pattern
        assert instinct.trigger is not None

    def test_requires_minimum_three_repetitions(
        self, agent_runner: AgentRunner
    ) -> None:
        """
        Eval 3.2: Workflow pattern requires at least 3 repetitions.

        2 repetitions should NOT trigger instinct creation.
        """
        # Create session with only 2 repetitions
        two_reps_session = [
            # First repetition
            {"timestamp": "2026-04-30T11:00:00Z", "event": "tool_start", "tool": "Read", "session": "workflow-2"},
            {"timestamp": "2026-04-30T11:00:05Z", "event": "tool_complete", "tool": "Read", "session": "workflow-2"},
            {"timestamp": "2026-04-30T11:00:10Z", "event": "tool_start", "tool": "Edit", "session": "workflow-2"},
            {"timestamp": "2026-04-30T11:00:15Z", "event": "tool_complete", "tool": "Edit", "session": "workflow-2"},
            {"timestamp": "2026-04-30T11:00:20Z", "event": "tool_start", "tool": "Bash", "session": "workflow-2"},
            {"timestamp": "2026-04-30T11:00:25Z", "event": "tool_complete", "tool": "Bash", "session": "workflow-2"},
            # Second repetition
            {"timestamp": "2026-04-30T11:05:00Z", "event": "tool_start", "tool": "Read", "session": "workflow-2"},
            {"timestamp": "2026-04-30T11:05:05Z", "event": "tool_complete", "tool": "Read", "session": "workflow-2"},
            {"timestamp": "2026-04-30T11:05:10Z", "event": "tool_start", "tool": "Edit", "session": "workflow-2"},
            {"timestamp": "2026-04-30T11:05:15Z", "event": "tool_complete", "tool": "Edit", "session": "workflow-2"},
            {"timestamp": "2026-04-30T11:05:20Z", "event": "tool_start", "tool": "Bash", "session": "workflow-2"},
            {"timestamp": "2026-04-30T11:05:25Z", "event": "tool_complete", "tool": "Bash", "session": "workflow-2"},
        ]

        result = agent_runner.analyze_session(
            session_id="workflow-2",
            events=two_reps_session
        )

        # Should NOT create workflow instinct with only 2 repetitions
        workflow_instincts = [
            i for i in (result.instincts_created or [])
            if "workflow" in i.id.lower() or "sequence" in i.id.lower()
        ]
        assert len(workflow_instincts) == 0, \
            "Workflow instinct should not be created with only 2 repetitions"

    def test_confidence_starts_at_seven(
        self, agent_runner: AgentRunner, repeated_workflow_session: list[dict]
    ) -> None:
        """
        Eval 3.2: Workflow patterns should start with confidence 0.7.
        """
        result = agent_runner.analyze_session(
            session_id="workflow-1",
            events=repeated_workflow_session
        )

        assert result is not None
        instinct = result.instincts_created[0]
        assert instinct.confidence == 0.7, \
            f"Expected confidence 0.7, got {instinct.confidence}"

    def test_domain_is_workflow(
        self, agent_runner: AgentRunner, repeated_workflow_session: list[dict]
    ) -> None:
        """
        Eval 3.2: Repeated workflow patterns should be in 'workflow' domain.
        """
        result = agent_runner.analyze_session(
            session_id="workflow-1",
            events=repeated_workflow_session
        )

        assert result is not None
        instinct = result.instincts_created[0]
        assert instinct.domain == "workflow"

    def test_records_evidence(
        self, agent_runner: AgentRunner, repeated_workflow_session: list[dict]
    ) -> None:
        """
        Eval 3.2: Evidence should include repetition count.
        """
        result = agent_runner.analyze_session(
            session_id="workflow-1",
            events=repeated_workflow_session
        )

        assert result is not None
        instinct = result.instincts_created[0]
        assert instinct.evidence is not None
        assert len(instinct.evidence) >= 1
        # Evidence should mention the repetition count
        evidence_str = str(instinct.evidence)
        assert "4" in evidence_str or "four" in evidence_str.lower() or "repeated" in evidence_str.lower()


class TestDifferentWorkflowPatterns:
    """Tests for different types of workflow patterns."""

    def test_detects_different_sequence_pattern(
        self, agent_runner: AgentRunner
    ) -> None:
        """
        Should detect different workflow patterns, not just Read-Edit-Bash.
        """
        # Test a different pattern: Read-Write-Read (e.g., config editing)
        config_session = [
            # Repetition 1
            {"timestamp": "2026-04-30T12:00:00Z", "event": "tool_start", "tool": "Read", "session": "config-1"},
            {"timestamp": "2026-04-30T12:00:05Z", "event": "tool_complete", "tool": "Read", "session": "config-1"},
            {"timestamp": "2026-04-30T12:00:10Z", "event": "tool_start", "tool": "Write", "session": "config-1"},
            {"timestamp": "2026-04-30T12:00:15Z", "event": "tool_complete", "tool": "Write", "session": "config-1"},
            # Repetition 2
            {"timestamp": "2026-04-30T12:05:00Z", "event": "tool_start", "tool": "Read", "session": "config-1"},
            {"timestamp": "2026-04-30T12:05:05Z", "event": "tool_complete", "tool": "Read", "session": "config-1"},
            {"timestamp": "2026-04-30T12:05:10Z", "event": "tool_start", "tool": "Write", "session": "config-1"},
            {"timestamp": "2026-04-30T12:05:15Z", "event": "tool_complete", "tool": "Write", "session": "config-1"},
            # Repetition 3
            {"timestamp": "2026-04-30T12:10:00Z", "event": "tool_start", "tool": "Read", "session": "config-1"},
            {"timestamp": "2026-04-30T12:10:05Z", "event": "tool_complete", "tool": "Read", "session": "config-1"},
            {"timestamp": "2026-04-30T12:10:10Z", "event": "tool_start", "tool": "Write", "session": "config-1"},
            {"timestamp": "2026-04-30T12:10:15Z", "event": "tool_complete", "tool": "Write", "session": "config-1"},
        ]

        result = agent_runner.analyze_session(
            session_id="config-1",
            events=config_session
        )

        # Should detect the Read-Write workflow pattern
        assert result is not None
        assert len(result.instincts_created) >= 1
