#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path


CHECKBOX_PATTERN = re.compile(r'^\s*[-*]\s+\[(?P<mark>[ xX])\]\s+(?P<task>.+?)\s*$')
DEFAULT_TODO_RELATIVE_PATHS = [
    Path('.claude/tasks/current.md'),
    Path('.claude/tasks/plan.md'),
    Path('TODO.md'),
    Path('CLAUDE.md'),
]
MAX_REASON_ITEMS = 3


def resolve_todo_path(cwd: str) -> Path | None:
    explicit_path = os.environ.get('CLAUDE_ENSURE_TODO_FILE')
    if explicit_path:
        candidate = Path(explicit_path).expanduser()
        return candidate.resolve() if candidate.exists() else None

    if not cwd:
        return None

    base_dir = Path(cwd)
    for relative_path in DEFAULT_TODO_RELATIVE_PATHS:
        candidate = base_dir / relative_path
        if candidate.exists():
            return candidate.resolve()
    return None


def open_tasks_from_text(content: str) -> list[str]:
    open_tasks: list[str] = []
    for line in content.splitlines():
        match = CHECKBOX_PATTERN.match(line)
        if not match:
            continue
        if match.group('mark') == ' ':
            open_tasks.append(match.group('task').strip())
    return open_tasks


def build_reason(todo_path: Path, open_tasks: list[str]) -> str:
    preview = '; '.join(open_tasks[:MAX_REASON_ITEMS])
    return f'Unfinished tasks remain in {todo_path}: {len(open_tasks)} open item(s). Next: {preview}'


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({'decision': 'approve'}))
        return 0

    cwd = payload.get('cwd') or ''
    todo_path = resolve_todo_path(cwd)
    if todo_path is None:
        print(json.dumps({'decision': 'approve'}))
        return 0

    try:
        content = todo_path.read_text()
    except (OSError, UnicodeDecodeError):
        print(json.dumps({'decision': 'approve'}))
        return 0

    open_tasks = open_tasks_from_text(content)
    if open_tasks:
        print(json.dumps({'decision': 'block', 'reason': build_reason(todo_path, open_tasks)}))
        return 0

    print(json.dumps({'decision': 'approve'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
