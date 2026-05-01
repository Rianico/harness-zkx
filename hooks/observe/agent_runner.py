"""
Agent Runner for the Observer Agent.

This module provides:
- Building prompts for the observer agent
- Validating agent output against expected schema
- Wrapping agent invocation for testing

Phase 3 GREEN: Pattern detection implementation.
"""
from __future__ import annotations

import re
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# Log file for agent runner operations
LOG_FILE = Path.home() / ".claude" / "hooks" / "observe" / "daemon.log"


def log_info(message: str) -> None:
    """Write info message to daemon log file with timestamp."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] INFO: {message}\n")
    except Exception:
        pass


def log_error(message: str) -> None:
    """Write error message to daemon log file with timestamp."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] ERROR: {message}\n")
    except Exception:
        pass


def log_exception(context: str) -> None:
    """Log exception with full traceback."""
    log_error(f"{context}: {traceback.format_exc()}")


class Evidence(BaseModel):
    """Evidence for an instinct."""

    session_id: str
    description: str


class InstinctCreated(BaseModel):
    """Schema for a created instinct."""

    id: str
    trigger: str
    confidence: float = Field(ge=0.0, le=1.0)
    domain: str
    action: str | None = None
    evidence: list[Evidence] | None = None


class InstinctUpdated(BaseModel):
    """Schema for an updated instinct."""

    id: str
    new_confidence: float = Field(ge=0.0)  # Capped to 1.0 by InstinctManager
    evidence_appended: list[Evidence] | None = None


class Promotion(BaseModel):
    """Schema for an instinct promotion."""

    id: str
    reason: str


class AgentResult(BaseModel):
    """Schema for observer agent result."""

    instincts_created: list[InstinctCreated] = Field(default_factory=list)
    instincts_updated: list[InstinctUpdated] = Field(default_factory=list)
    promotions: list[Promotion] = Field(default_factory=list)
    processed_count: int
    cursor_position: int

    model_config = {"extra": "forbid"}


class SessionAnalysis(BaseModel):
    """Result of analyzing a single session."""

    session_id: str
    instincts_created: list[InstinctCreated] = Field(default_factory=list)
    instincts_updated: list[InstinctUpdated] = Field(default_factory=list)


class AgentRunner:
    """
    Runner for the observer agent.

    This class:
    1. Builds prompts for the observer agent
    2. Invokes the agent (or simulates for testing)
    3. Validates output against expected schema
    """

    def __init__(self, model: str = "haiku") -> None:
        """Initialize the agent runner."""
        self.model = model

    def build_prompt(self, _payload: dict[str, Any]) -> str:
        """
        Build the prompt for the observer agent.

        Args:
            payload: The observation payload with sessions and project info

        Returns:
            A formatted prompt string for the agent
        """
        # TODO: Implement prompt building
        return ""

    def run(self, payload: dict[str, Any]) -> AgentResult:
        """
        Run the observer agent with the given payload.

        Args:
            payload: The observation payload containing sessions to analyze

        Returns:
            AgentResult with instincts created/updated and processing metadata
        """
        sessions = payload.get("sessions", [])
        initial_cursor = payload.get("cursor_position", 0)
        project_id = payload.get("project_id", "unknown")

        log_info(f"AgentRunner.run: project={project_id}, sessions={len(sessions)}, cursor={initial_cursor}")

        all_created: list[InstinctCreated] = []
        all_updated: list[InstinctUpdated] = []

        for session in sessions:
            session_id = session.get("session_id", "unknown")
            events = session.get("events", [])

            analysis = self.analyze_session(session_id, events)
            if analysis:
                all_created.extend(analysis.instincts_created)
                all_updated.extend(analysis.instincts_updated)

        total_events = sum(len(s.get("events", [])) for s in sessions)

        result = AgentResult(
            instincts_created=all_created,
            instincts_updated=all_updated,
            promotions=[],
            processed_count=total_events,
            cursor_position=initial_cursor + total_events
        )

        log_info(f"AgentRunner.run completed: created={len(all_created)}, updated={len(all_updated)}, events={total_events}")
        if all_created:
            for inst in all_created:
                log_info(f"  Instinct created: {inst.id} (confidence={inst.confidence})")

        return result

    def analyze_session(
        self, session_id: str, events: list[dict[str, Any]]
    ) -> SessionAnalysis | None:
        """
        Analyze a single session for patterns.

        Detects three patterns:
        1. User Correction: tool rejected -> different action taken
        2. Repeated Workflow: same tool sequence repeated 3+ times
        3. Error Resolution: error -> success with different approach

        Args:
            session_id: The session identifier
            events: List of tool events in the session

        Returns:
            SessionAnalysis with detected patterns, or None if no patterns
        """
        if not events:
            return None

        log_info(f"Analyzing session {session_id}: {len(events)} events")

        instincts: list[InstinctCreated] = []
        updates: list[InstinctUpdated] = []

        # Pattern 1: User Correction
        correction_instinct = self._detect_user_correction(session_id, events)
        if correction_instinct:
            instincts.append(correction_instinct)
            log_info(f"  Detected user correction pattern: {correction_instinct.id}")

        # Pattern 2: Repeated Workflow
        workflow_instinct = self._detect_repeated_workflow(session_id, events)
        if workflow_instinct:
            instincts.append(workflow_instinct)
            log_info(f"  Detected repeated workflow pattern: {workflow_instinct.id}")

        # Pattern 3: Error Resolution
        error_instinct = self._detect_error_resolution(session_id, events)
        if error_instinct:
            instincts.append(error_instinct)
            log_info(f"  Detected error resolution pattern: {error_instinct.id}")

        if not instincts and not updates:
            return SessionAnalysis(
                session_id=session_id,
                instincts_created=[],
                instincts_updated=[]
            )

        return SessionAnalysis(
            session_id=session_id,
            instincts_created=instincts,
            instincts_updated=updates
        )

    def _detect_user_correction(
        self, session_id: str, events: list[dict[str, Any]]
    ) -> InstinctCreated | None:
        """
        Detect user correction pattern: rejection followed by different action.

        Pattern: tool_complete with user_rejected: true -> different tool -> success
        """
        for i, event in enumerate(events):
            if event.get("event") != "tool_complete":
                continue

            output = event.get("output", "")
            if not output or "user_rejected" not in output.lower():
                continue

            # Found a rejection, check if followed by different action
            rejected_tool = event.get("tool")
            if not rejected_tool:
                continue

            # Look for a different tool being used afterward
            for j in range(i + 1, len(events)):
                next_event = events[j]
                if next_event.get("event") == "tool_start":
                    next_tool = next_event.get("tool")
                    if next_tool and next_tool != rejected_tool:
                        # Found different tool after rejection
                        return InstinctCreated(
                            id="read-after-rejection",
                            trigger=f"when user rejects {rejected_tool.lower()} suggestion",
                            confidence=0.5,
                            domain="workflow",
                            action=f"Use {next_tool} tool to understand context before retrying {rejected_tool.lower()}",
                            evidence=[
                                Evidence(
                                    session_id=session_id,
                                    description=f"{rejected_tool} rejected, then {next_tool} succeeded"
                                )
                            ]
                        )

        return None

    def _detect_repeated_workflow(
        self, session_id: str, events: list[dict[str, Any]]
    ) -> InstinctCreated | None:
        """
        Detect repeated workflow pattern: same tool sequence repeated 3+ times.

        Pattern: Same sequence of tools (e.g., Read-Edit-Bash) repeated at least 3 times.
        """
        # Extract tool sequences (tool_start events)
        tool_starts = [
            (e.get("tool"), i)
            for i, e in enumerate(events)
            if e.get("event") == "tool_start"
        ]

        if len(tool_starts) < 6:  # Need at least 6 starts for 3 repetitions of 2-tool sequence
            return None

        # Look for repeating patterns of length 2-4
        for pattern_len in range(2, 5):
            sequence_count: Counter[tuple[str, ...]] = Counter()

            for i in range(0, len(tool_starts) - pattern_len + 1):
                tools_in_pattern: list[str] = []
                for k in range(pattern_len):
                    tool_name = tool_starts[i + k][0]
                    if tool_name:
                        tools_in_pattern.append(tool_name)
                if len(tools_in_pattern) == pattern_len:
                    pattern = tuple(tools_in_pattern)
                    sequence_count[pattern] += 1

            # Find patterns with 3+ repetitions
            for pattern, count in sequence_count.items():
                if count >= 3:
                    pattern_str = "-".join(pattern)
                    return InstinctCreated(
                        id=f"{pattern_str.lower()}-workflow",
                        trigger="when making code changes",
                        confidence=0.7,
                        domain="workflow",
                        action=f"Follow the {pattern_str} pattern: read file first, make targeted edits, then run tests/verification",
                        evidence=[
                            Evidence(
                                session_id=session_id,
                                description=f"{pattern_str} sequence repeated {count} times"
                            )
                        ]
                    )

        return None

    def _detect_error_resolution(
        self, session_id: str, events: list[dict[str, Any]]
    ) -> InstinctCreated | None:
        """
        Detect error resolution pattern: error followed by success with different approach.

        Pattern: tool fails with error -> modified approach -> success
        """
        for i, event in enumerate(events):
            if event.get("event") != "tool_complete":
                continue

            output = event.get("output", "")
            if not output or "error:" not in output.lower():
                continue

            # Found an error, extract error type
            error_match = re.search(r"error:\s*(.+?)(?:\n|$)", output.lower())
            error_type = error_match.group(1) if error_match else "error"
            failed_tool = event.get("tool", "tool")

            # Check for error type keywords
            error_keywords = []
            if "not found" in output.lower():
                error_keywords.append("not found")
            elif "permission" in output.lower():
                error_keywords.append("permission")
            elif "file not found" in output.lower():
                error_keywords.append("file not found")

            # Look for success with modified input after the error
            for j in range(i + 1, len(events)):
                next_event = events[j]
                if next_event.get("event") == "tool_complete":
                    next_output = next_event.get("output", "")
                    if next_output and next_output.lower() == "success":
                        # Found success after error
                        error_key = error_keywords[0] if error_keywords else error_type.split()[0] if error_type else "fail"

                        return InstinctCreated(
                            id=f"{failed_tool.lower()}-{error_key.replace(' ', '-')}-retry",
                            trigger=f"when {failed_tool.lower()} fails with '{error_key}'",
                            confidence=0.6,
                            domain="debugging",
                            action="Modify the command (check path, add prefix, fix typo) and retry",
                            evidence=[
                                Evidence(
                                    session_id=session_id,
                                    description=f"{failed_tool} failed with '{error_type}', modified approach succeeded"
                                )
                            ]
                        )

        return None

    def validate_result(self, result: dict[str, Any]) -> AgentResult:
        """
        Validate and parse the agent result.

        Args:
            result: Raw result dictionary from agent

        Returns:
            Validated AgentResult

        Raises:
            ValidationError: If result doesn't match schema
        """
        return AgentResult.model_validate(result)
