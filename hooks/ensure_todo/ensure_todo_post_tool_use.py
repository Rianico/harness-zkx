#!/usr/bin/env python3
import json
import os
import shlex
import subprocess
import sys


EDIT_TOOL_NAMES = {'Edit', 'Write', 'MultiEdit'}
TIMEOUT_SECONDS = 120


def edited_paths_from_payload(payload: dict) -> list[str]:
    tool_name = payload.get('tool_name') or payload.get('tool')
    if tool_name not in EDIT_TOOL_NAMES:
        return []

    tool_input = payload.get('tool_input') or {}
    paths: list[str] = []

    file_path = tool_input.get('file_path')
    if isinstance(file_path, str) and file_path:
        paths.append(file_path)

    edits = tool_input.get('edits') or []
    if isinstance(edits, list):
        for edit in edits:
            if not isinstance(edit, dict):
                continue
            edit_path = edit.get('file_path')
            if isinstance(edit_path, str) and edit_path:
                paths.append(edit_path)

    return paths


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    paths = edited_paths_from_payload(payload)
    if not paths:
        return 0

    test_command = os.environ.get('CLAUDE_ENSURE_TODO_TEST_COMMAND')
    if not test_command:
        print('[ensure_todo] CLAUDE_ENSURE_TODO_TEST_COMMAND is not set; skipping tests.', file=sys.stderr)
        return 0

    try:
        completed = subprocess.run(shlex.split(test_command), check=False, timeout=TIMEOUT_SECONDS)
    except ValueError:
        print('[ensure_todo] CLAUDE_ENSURE_TODO_TEST_COMMAND is invalid.', file=sys.stderr)
        return 0
    except FileNotFoundError:
        print('[ensure_todo] Test command executable was not found.', file=sys.stderr)
        return 0
    except subprocess.TimeoutExpired:
        print(f'[ensure_todo] Test command timed out after {TIMEOUT_SECONDS}s.', file=sys.stderr)
        return 0

    if completed.returncode == 0:
        print(f'[ensure_todo] Tests passed after editing {len(paths)} file(s).', file=sys.stderr)
    else:
        print(f'[ensure_todo] Test command failed with exit code {completed.returncode}.', file=sys.stderr)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
