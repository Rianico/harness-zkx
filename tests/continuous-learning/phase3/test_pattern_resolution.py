"""
Tests for error resolution pattern detection.

Eval 3.3: Pattern Detection - Error Resolution

Input: Session with error then success
Expected: Instinct created with confidence 0.6+

Pass criteria:
- [ ] Error pattern detected
- [ ] Resolution strategy captured
- [ ] Confidence starts at 0.6
"""

import json
from pathlib import Path

import pytest

from hooks.observe.agent_runner import AgentRunner

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
SESSIONS_DIR = FIXTURES_DIR / "sessions"
EXPECTED_DIR = FIXTURES_DIR / "expected_outputs"


@pytest.fixture
def error_resolution_session() -> list[dict]:
    """Load error resolution session fixture."""
    with open(SESSIONS_DIR / "error_resolution.json") as f:
        return json.load(f)


@pytest.fixture
def expected_resolution_output() -> dict:
    """Load expected output for error resolution pattern."""
    with open(EXPECTED_DIR / "error_resolution.json") as f:
        return json.load(f)


@pytest.fixture
def agent_runner() -> AgentRunner:
    """Create agent runner instance."""
    return AgentRunner()


class TestErrorResolutionPattern:
    """Tests for error resolution pattern detection."""

    def test_detects_error_followed_by_success(
        self, agent_runner: AgentRunner, error_resolution_session: list[dict]
    ) -> None:
        """
        Eval 3.3: Detect when a tool fails and a modified approach succeeds.

        Pattern: Bash fails with "command not found" -> modified command succeeds
        """
        result = agent_runner.analyze_session(
            session_id="resolution-1", events=error_resolution_session
        )

        assert result is not None
        assert len(result.instincts_created) >= 1

        instinct = result.instincts_created[0]
        assert instinct.trigger is not None
        # Trigger should mention the error type
        assert "not found" in instinct.trigger.lower() or "fail" in instinct.trigger.lower()

    def test_creates_instinct_with_correct_confidence(
        self, agent_runner: AgentRunner, error_resolution_session: list[dict]
    ) -> None:
        """
        Eval 3.3: Error resolution instincts should start with confidence 0.6.
        """
        result = agent_runner.analyze_session(
            session_id="resolution-1", events=error_resolution_session
        )

        assert result is not None
        instinct = result.instincts_created[0]
        assert instinct.confidence == 0.6, f"Expected confidence 0.6, got {instinct.confidence}"

    def test_domain_is_debugging(
        self, agent_runner: AgentRunner, error_resolution_session: list[dict]
    ) -> None:
        """
        Eval 3.3: Error resolution patterns should be in 'debugging' domain.
        """
        result = agent_runner.analyze_session(
            session_id="resolution-1", events=error_resolution_session
        )

        assert result is not None
        instinct = result.instincts_created[0]
        assert instinct.domain == "debugging"

    def test_captures_resolution_strategy(
        self, agent_runner: AgentRunner, error_resolution_session: list[dict]
    ) -> None:
        """
        Eval 3.3: The instinct should capture the resolution strategy.
        """
        result = agent_runner.analyze_session(
            session_id="resolution-1", events=error_resolution_session
        )

        assert result is not None
        instinct = result.instincts_created[0]
        assert instinct.action is not None
        # Action should mention what to do when the error occurs
        assert len(instinct.action) > 10, "Action description should be meaningful"

    def test_records_evidence(
        self, agent_runner: AgentRunner, error_resolution_session: list[dict]
    ) -> None:
        """
        Eval 3.3: Evidence should be recorded with the instinct.
        """
        result = agent_runner.analyze_session(
            session_id="resolution-1", events=error_resolution_session
        )

        assert result is not None
        instinct = result.instincts_created[0]
        assert instinct.evidence is not None
        assert len(instinct.evidence) >= 1
        assert any("resolution-1" in str(e) for e in instinct.evidence)


class TestDifferentErrorPatterns:
    """Tests for different types of error resolution patterns."""

    def test_detects_permission_error_resolution(self, agent_runner: AgentRunner) -> None:
        """
        Should detect permission error resolution pattern.
        """
        permission_session = [
            {
                "timestamp": "2026-04-30T13:00:00Z",
                "event": "tool_start",
                "tool": "Bash",
                "session": "perm-1",
            },
            {
                "timestamp": "2026-04-30T13:00:05Z",
                "event": "tool_complete",
                "tool": "Bash",
                "session": "perm-1",
                "output": "error: Permission denied",
            },
            {
                "timestamp": "2026-04-30T13:00:10Z",
                "event": "tool_start",
                "tool": "Bash",
                "session": "perm-1",
                "input": {"command": "sudo chmod +x script.sh"},
            },
            {
                "timestamp": "2026-04-30T13:00:15Z",
                "event": "tool_complete",
                "tool": "Bash",
                "session": "perm-1",
                "output": "success",
            },
        ]

        result = agent_runner.analyze_session(session_id="perm-1", events=permission_session)

        assert result is not None
        assert len(result.instincts_created) >= 1
        instinct = result.instincts_created[0]
        assert "permission" in instinct.trigger.lower()

    def test_detects_file_not_found_resolution(self, agent_runner: AgentRunner) -> None:
        """
        Should detect file not found resolution pattern.
        """
        file_not_found_session = [
            {
                "timestamp": "2026-04-30T14:00:00Z",
                "event": "tool_start",
                "tool": "Read",
                "session": "fnf-1",
            },
            {
                "timestamp": "2026-04-30T14:00:05Z",
                "event": "tool_complete",
                "tool": "Read",
                "session": "fnf-1",
                "output": "error: file not found",
            },
            {
                "timestamp": "2026-04-30T14:00:10Z",
                "event": "tool_start",
                "tool": "Bash",
                "session": "fnf-1",
                "input": {"command": "find . -name file.py"},
            },
            {
                "timestamp": "2026-04-30T14:00:15Z",
                "event": "tool_complete",
                "tool": "Bash",
                "session": "fnf-1",
                "output": "./src/file.py",
            },
            {
                "timestamp": "2026-04-30T14:00:20Z",
                "event": "tool_start",
                "tool": "Read",
                "session": "fnf-1",
            },
            {
                "timestamp": "2026-04-30T14:00:25Z",
                "event": "tool_complete",
                "tool": "Read",
                "session": "fnf-1",
                "output": "success",
            },
        ]

        result = agent_runner.analyze_session(session_id="fnf-1", events=file_not_found_session)

        assert result is not None
        assert len(result.instincts_created) >= 1

    def test_no_false_positives_on_normal_errors(self, agent_runner: AgentRunner) -> None:
        """
        Errors without resolution should not create instincts.
        """
        error_only_session = [
            {
                "timestamp": "2026-04-30T15:00:00Z",
                "event": "tool_start",
                "tool": "Bash",
                "session": "error-only",
            },
            {
                "timestamp": "2026-04-30T15:00:05Z",
                "event": "tool_complete",
                "tool": "Bash",
                "session": "error-only",
                "output": "error: command failed",
            },
            # No resolution follows
        ]

        result = agent_runner.analyze_session(session_id="error-only", events=error_only_session)

        # Should not create resolution instinct if there's no resolution
        if result.instincts_created:
            resolution_instincts = [
                i
                for i in result.instincts_created
                if "resolution" in i.id.lower() or "fail" in i.trigger.lower()
            ]
            assert len(resolution_instincts) == 0, (
                "Should not create resolution instinct without actual resolution"
            )
