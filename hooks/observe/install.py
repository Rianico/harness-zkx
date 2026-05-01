#!/usr/bin/env python3
"""Installer for the observe hook family.

The observe hook captures PreToolUse and PostToolUse events for the
continuous learning system, writing observations to project-scoped files.
"""
import json
import shutil
import sys
from pathlib import Path

# Import shared tool checker
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tool_checker import run_tool_check


TARGET_HOOK_RELATIVE_PATH = Path('hooks/observe/observe.py')
SOURCE_HOOK_NAME = 'observe.py'

# Hook event types to register for
HOOK_EVENTS = ('PreToolUse', 'PostToolUse')


def show_help() -> None:
    print(
        'Usage:\n'
        '  uv run install-hooks.py observe install <settings.json>\n'
        '  uv run install-hooks.py observe uninstall <settings.json>\n'
        '  uv run install-hooks.py --help\n\n'
        'This module is installed through the root install-hooks.py entrypoint.\n'
    )


def load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_settings(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + '\n')


def target_hook_path(settings_path: Path) -> Path:
    return (settings_path.parent / TARGET_HOOK_RELATIVE_PATH).resolve()


def install_hook_script(settings_path: Path) -> Path:
    target_hook = target_hook_path(settings_path)
    target_hook.parent.mkdir(parents=True, exist_ok=True)
    source_hook = Path(__file__).resolve().with_name(SOURCE_HOOK_NAME)
    shutil.copy2(source_hook, target_hook)
    return target_hook


def build_hook_entry(target_hook: Path, event_type: str) -> dict:
    """Build a hook entry for the given event type.

    Args:
        target_hook: Path to the hook script
        event_type: 'PreToolUse' or 'PostToolUse'

    Returns:
        Hook entry dict for settings.json
    """
    # Determine the argument based on event type
    arg = 'pre' if event_type == 'PreToolUse' else 'post'
    return {
        'matcher': '*',
        'hooks': [
            {
                'type': 'command',
                'command': f'uv run "{target_hook}" {arg}',
            }
        ],
    }


def ensure_observe_hook(data: dict, hook_entry: dict, event_type: str) -> bool:
    """Ensure the observe hook is registered for the given event type.

    Args:
        data: Settings dict
        hook_entry: Hook entry to ensure
        event_type: 'PreToolUse' or 'PostToolUse'

    Returns:
        True if changes were made, False otherwise
    """
    hooks = data.setdefault('hooks', {})
    event_hooks = hooks.setdefault(event_type, [])

    for entry in event_hooks:
        if entry == hook_entry:
            return False

    event_hooks.append(hook_entry)
    return True


def remove_observe_hook(data: dict, hook_entry: dict, event_type: str) -> bool:
    """Remove the observe hook for the given event type.

    Args:
        data: Settings dict
        hook_entry: Hook entry to remove
        event_type: 'PreToolUse' or 'PostToolUse'

    Returns:
        True if changes were made, False otherwise
    """
    hooks = data.get('hooks')
    if not isinstance(hooks, dict):
        return False

    event_hooks = hooks.get(event_type)
    if not isinstance(event_hooks, list):
        return False

    remaining_hooks = [entry for entry in event_hooks if entry != hook_entry]
    if len(remaining_hooks) == len(event_hooks):
        return False

    if remaining_hooks:
        hooks[event_type] = remaining_hooks
    else:
        hooks.pop(event_type, None)
        if not hooks:
            data.pop('hooks', None)

    return True


def install_family(settings_path: Path) -> int:
    """Install the observe hook family.

    Registers the observe.py script for both PreToolUse and PostToolUse events.
    """
    # Check required tools
    required = ['uv']
    if not run_tool_check('observe', required):
        return 1

    target_hook = install_hook_script(settings_path)
    data = load_settings(settings_path)
    changed = False

    for event_type in HOOK_EVENTS:
        hook_entry = build_hook_entry(target_hook, event_type)
        if ensure_observe_hook(data, hook_entry, event_type):
            changed = True

    save_settings(settings_path, data)

    print(f'Updated {settings_path}' if changed else f'No changes needed for {settings_path}')
    print(f'Installed hook script at {target_hook}')
    print(f'Registered for events: {", ".join(HOOK_EVENTS)}')
    return 0


def uninstall_family(settings_path: Path) -> int:
    """Uninstall the observe hook family.

    Removes observe.py registrations from PreToolUse and PostToolUse events
    and deletes the copied script.
    """
    target_hook = target_hook_path(settings_path)
    data = load_settings(settings_path)
    changed = False

    for event_type in HOOK_EVENTS:
        hook_entry = build_hook_entry(target_hook, event_type)
        if remove_observe_hook(data, hook_entry, event_type):
            changed = True

    save_settings(settings_path, data)

    removed_script = False
    if changed and target_hook.exists():
        target_hook.unlink()
        removed_script = True

    print(f'Updated {settings_path}' if changed else f'No changes needed for {settings_path}')
    print(f'Removed hook script at {target_hook}' if removed_script else f'No hook script found at {target_hook}')
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] in {'--help', '-h'}:
        show_help()
        return 0

    show_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
