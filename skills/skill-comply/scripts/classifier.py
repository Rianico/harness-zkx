"""Classify tool calls against compliance steps using LLM."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

from scripts.parser import ComplianceSpec, ObservationEvent

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# JSON schema for classifier output
CLASSIFIER_SCHEMA = {
    "type": "object",
    "additionalProperties": {
        "type": "array",
        "items": {"type": "integer"}
    }
}

def classify_events(
    spec: ComplianceSpec,
    trace: list[ObservationEvent],
    model: str = "haiku",
    timeout: int = 120,
) -> dict[str, list[int]]:
    """Classify which tool calls match which compliance steps.

    Returns {step_id: [event_indices]} via a single LLM call.
    """
    if not trace:
        return {}

    steps_desc = "\n".join(
        f"- {step.id}: {step.detector.description}"
        for step in spec.steps
    )

    tool_calls = "\n".join(
        f"[{i}] {event.tool}: input={event.input[:500]} output={event.output[:200]}"
        for i, event in enumerate(trace)
    )

    prompt_template = (PROMPTS_DIR / "classifier.md").read_text()
    prompt = (
        prompt_template
        .replace("{steps_description}", steps_desc)
        .replace("{tool_calls}", tool_calls)
    )

    result = subprocess.run(
        [
            "claude", "-p", prompt,
            "--model", model,
            "--output-format", "json",
            "--json-schema", json.dumps(CLASSIFIER_SCHEMA),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"classifier subprocess failed (rc={result.returncode}): "
            f"{result.stderr[:500]}"
        )

    return _parse_classification(result.stdout)

def _parse_classification(text: str) -> dict[str, list[int]]:
    """Parse LLM classification output into {step_id: [event_indices]}.

    Handles two formats:
    1. Direct JSON object (from text output)
    2. JSON array from --output-format json with structured_output in result
    """
    text = text.strip()

    try:
        parsed = json.loads(text)

        # Handle JSON array from --output-format json
        if isinstance(parsed, list):
            # Find the result object with structured_output
            for item in reversed(parsed):
                if isinstance(item, dict) and "structured_output" in item:
                    structured = item["structured_output"]
                    if isinstance(structured, dict):
                        return {
                            k: [int(i) for i in v]
                            for k, v in structured.items()
                            if isinstance(v, list)
                        }
            logger.warning("No structured_output found in JSON array")
            return {}

        # Handle direct dict output
        if isinstance(parsed, dict):
            return {
                k: [int(i) for i in v]
                for k, v in parsed.items()
                if isinstance(v, list)
            }

        logger.warning("Classifier returned unexpected JSON type: %s", type(parsed).__name__)
        return {}
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning("Failed to parse classification output: %s", e)
        logger.debug("Raw output was: %s", text[:500])
        return {}
