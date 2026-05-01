# /// script
# dependencies = []
# ///
"""
Observation capture functionality for the hook.

Captures tool events and writes them to project-scoped files.
"""
from __future__ import annotations

import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Support both standalone script execution and module import
# When run standalone, add script directory to path for local imports
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import config
    import detect_project
    import secrets
except ImportError:
    from hooks.observe import config, detect_project, secrets

# Track observation count for daemon signaling
_observation_count = 0


def _get_or_create_tool_use_id(event: dict) -> str:
    """Get existing tool_use_id or generate a new one."""
    if "tool_use_id" in event and event["tool_use_id"]:
        return event["tool_use_id"]
    return f"toolu_{uuid.uuid4().hex[:12]}"


def _truncate_string(s: str, max_length: int = 5000) -> str:
    """Truncate a string to max_length characters."""
    if len(s) <= max_length:
        return s
    return s[:max_length]


def _truncate_dict(data: dict, max_length: int = 5000) -> dict:
    """
    Truncate a dict so its JSON representation is <= max_length.

    This truncates string values to ensure the total JSON output
    doesn't exceed max_length characters.
    """
    # First, try without truncation
    json_str = json.dumps(data)
    if len(json_str) <= max_length:
        return data

    # Need to truncate - create a result that fits within max_length
    result = {}
    items = list(data.items())

    for key, value in items:
        if isinstance(value, str):
            # Binary search for the right truncation length
            low, high = 0, len(value)
            best_value = value[:0]  # Start with empty string

            while low <= high:
                mid = (low + high) // 2
                test_result = dict(result)  # Copy current result
                test_result[key] = value[:mid] if mid < len(value) else value
                test_json = json.dumps(test_result)

                if len(test_json) <= max_length:
                    best_value = test_result[key]
                    low = mid + 1
                else:
                    high = mid - 1

            result[key] = best_value
        elif isinstance(value, dict):
            # For nested dicts, truncate the JSON representation
            nested_json = json.dumps(value)
            if len(nested_json) <= max_length - len(json.dumps(result)):
                result[key] = value
            else:
                # Truncate the nested JSON string
                overhead = len(json.dumps(result)) + len(json.dumps(key)) + 3
                available = max_length - overhead
                if available > 0:
                    result[key] = nested_json[:available]
                else:
                    result[key] = ""
        else:
            test_result = dict(result)
            test_result[key] = value
            if len(json.dumps(test_result)) <= max_length:
                result[key] = value

    # Final check - if still over, truncate the string values more
    while len(json.dumps(result)) > max_length:
        # Find the longest string value and truncate it
        longest_key = None
        longest_len = 0
        for k, v in result.items():
            if isinstance(v, str) and len(v) > longest_len:
                longest_key = k
                longest_len = len(v)

        if longest_key is None or longest_len <= 0:
            break

        result[longest_key] = result[longest_key][:-1]

    return result


def _create_observation(
    event_type: str,
    tool_event: dict,
) -> dict:
    """
    Create an observation record from a tool event.

    Args:
        event_type: 'tool_start' or 'tool_complete'.
        tool_event: The event payload from the hook.

    Returns:
        An observation dictionary.
    """
    # Get the working directory from the event
    cwd = tool_event.get("cwd")

    # Get project context - use event-provided project_id if available
    # (useful for testing), otherwise compute from cwd
    project_id = tool_event.get("project_id")
    if project_id is None:
        project_id = detect_project.get_project_id(cwd)
    project_name = detect_project.get_project_name(cwd)

    # Get or create tool_use_id
    tool_use_id = _get_or_create_tool_use_id(tool_event)

    # Scrub secrets from input
    tool_input = tool_event.get("tool_input", {})
    if isinstance(tool_input, dict):
        scrubbed_input = secrets.scrub_dict(tool_input)
        truncated_input = _truncate_dict(scrubbed_input)
    else:
        # Handle non-dict input (e.g., string) by wrapping in a dict
        scrubbed_str = secrets.scrub_secrets(str(tool_input))
        truncated_input = {"content": _truncate_string(scrubbed_str)}

    # Create observation
    observation = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "event": event_type,
        "tool": tool_event.get("tool_name", "Unknown"),
        "input": truncated_input,
        "session": tool_event.get("session_id", ""),
        "project_id": project_id,
        "project_name": project_name,
        "tool_use_id": tool_use_id,
    }

    # Add output for tool_complete events
    if event_type == "tool_complete":
        output = tool_event.get("tool_result", "")
        if output:
            # Scrub and truncate output
            scrubbed_output = secrets.scrub_secrets(str(output))
            observation["output"] = _truncate_string(scrubbed_output)
        else:
            observation["output"] = ""

    return observation


def _write_observation(observation: dict) -> None:
    """
    Write an observation to the appropriate file.

    Args:
        observation: The observation to write.
    """
    project_id = observation["project_id"]

    # Get the observations file path
    observations_file = detect_project.get_observations_file(project_id)

    # Ensure directory exists
    observations_file.parent.mkdir(parents=True, exist_ok=True)

    # Register/update project in registry (not for global)
    if project_id != "global":
        detect_project.register_project(
            project_id,
            observation["project_name"],
            observation.get("cwd", str(Path.cwd())),
        )

    # Append observation as JSON line
    with open(observations_file, "a") as f:
        f.write(json.dumps(observation) + "\n")


def signal_daemon() -> None:
    """
    Signal the observer daemon to process observations.

    This sends SIGUSR1 to the daemon PID if running.
    """
    import os
    import signal

    homunculus_dir = config.get_homunculus_dir()
    pid_file = homunculus_dir / ".observer.pid"

    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGUSR1)
        except (ValueError, OSError):
            pass


def handle_pre_tool_use(event: dict) -> None:
    """
    Handle a PreToolUse event.

    Args:
        event: The event payload containing:
            - tool_name: Name of the tool being called
            - tool_input: Input parameters for the tool
            - cwd: Current working directory
            - session_id: Session identifier
            - tool_use_id: (optional) Tool use identifier
    """
    global _observation_count

    # Create observation
    observation = _create_observation("tool_start", event)

    # Write observation
    _write_observation(observation)

    # Increment count and check if we should signal daemon
    _observation_count += 1
    signal_interval = config.get_signal_interval()
    if _observation_count % signal_interval == 0:
        signal_daemon()


def handle_post_tool_use(event: dict) -> None:
    """
    Handle a PostToolUse event.

    Args:
        event: The event payload containing:
            - tool_name: Name of the tool that was called
            - tool_input: Input parameters for the tool
            - tool_result: Output from the tool
            - cwd: Current working directory
            - session_id: Session identifier
            - tool_use_id: (optional) Tool use identifier
    """
    global _observation_count

    # Create observation
    observation = _create_observation("tool_complete", event)

    # Write observation
    _write_observation(observation)

    # Increment count and check if we should signal daemon
    _observation_count += 1
    signal_interval = config.get_signal_interval()
    if _observation_count % signal_interval == 0:
        signal_daemon()


def reset_observation_count() -> None:
    """Reset the observation counter. Used for testing."""
    global _observation_count
    _observation_count = 0


def main() -> int:
    """
    Main entry point for the hook script.

    Usage: observe.py pre|post

    Reads JSON from stdin and writes observation to observations.jsonl.
    """
    import sys

    if len(sys.argv) < 2 or sys.argv[1] not in ("pre", "post"):
        print("Usage: observe.py pre|post", file=sys.stderr)
        return 1

    phase = sys.argv[1]

    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if phase == "pre":
        handle_pre_tool_use(event)
    else:
        handle_post_tool_use(event)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
