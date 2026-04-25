#!/usr/bin/env python3
import json
import shutil
import sys
from pathlib import Path


TARGET_HOOK_RELATIVE_PATHS = {
    'Stop': Path('hooks/ensure_todo/ensure_todo_stop.py'),
    'PostToolUse': Path('hooks/ensure_todo/ensure_todo_post_tool_use.py'),
}
LEGACY_TARGET_HOOK_RELATIVE_PATHS = {
    'Stop': (Path('hooks/ensure_todo_stop.py'),),
    'PostToolUse': (Path('hooks/ensure_todo_post_tool_use.py'),),
}
SOURCE_HOOK_NAMES = {
    'Stop': 'ensure_todo_stop.py',
    'PostToolUse': 'ensure_todo_post_tool_use.py',
}
MATCHERS = {
    'Stop': '*',
    'PostToolUse': 'Edit|Write|MultiEdit',
}


def load_settings(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_settings(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + '\n')


def target_hook_path(settings_path: Path, event_name: str) -> Path:
    return (settings_path.parent / TARGET_HOOK_RELATIVE_PATHS[event_name]).resolve()


def legacy_target_hook_paths(settings_path: Path, event_name: str) -> tuple[Path, ...]:
    return tuple((settings_path.parent / relative_path).resolve() for relative_path in LEGACY_TARGET_HOOK_RELATIVE_PATHS[event_name])


def install_hook_script(settings_path: Path, event_name: str) -> Path:
    target_hook = target_hook_path(settings_path, event_name)
    target_hook.parent.mkdir(parents=True, exist_ok=True)
    source_hook = Path(__file__).resolve().with_name(SOURCE_HOOK_NAMES[event_name])
    shutil.copy2(source_hook, target_hook)
    return target_hook


def build_hook_entry(target_hook: Path, event_name: str) -> dict:
    return {
        'matcher': MATCHERS[event_name],
        'hooks': [
            {
                'type': 'command',
                'command': f'uv run "{target_hook}"',
            }
        ],
    }


def ensure_hook(data: dict, event_name: str, hook_entry: dict) -> bool:
    hooks = data.setdefault('hooks', {})
    event_hooks = hooks.setdefault(event_name, [])

    for entry in event_hooks:
        if entry == hook_entry:
            return False

    event_hooks.append(hook_entry)
    return True


def remove_hook(data: dict, event_name: str, hook_entry: dict) -> bool:
    hooks = data.get('hooks')
    if not isinstance(hooks, dict):
        return False

    event_hooks = hooks.get(event_name)
    if not isinstance(event_hooks, list):
        return False

    remaining_hooks = [entry for entry in event_hooks if entry != hook_entry]
    if len(remaining_hooks) == len(event_hooks):
        return False

    if remaining_hooks:
        hooks[event_name] = remaining_hooks
    else:
        hooks.pop(event_name, None)
        if not hooks:
            data.pop('hooks', None)

    return True


def install_family(settings_path: Path) -> int:
    data = load_settings(settings_path)
    changes = []

    for event_name in TARGET_HOOK_RELATIVE_PATHS:
        target_hook = install_hook_script(settings_path, event_name)
        hook_entry = build_hook_entry(target_hook, event_name)
        changed = ensure_hook(data, event_name, hook_entry)
        removed_legacy_paths = []
        for legacy_path in legacy_target_hook_paths(settings_path, event_name):
            legacy_changed = remove_hook(data, event_name, build_hook_entry(legacy_path, event_name))
            changed = changed or legacy_changed
            if legacy_changed and legacy_path.exists():
                legacy_path.unlink()
                removed_legacy_paths.append(legacy_path)
        changes.append((event_name, changed, target_hook, removed_legacy_paths))

    save_settings(settings_path, data)
    print(f'Updated {settings_path}')
    for event_name, changed, target_hook, removed_legacy_paths in changes:
        status = 'Installed' if changed else 'Already installed'
        print(f'{status} {event_name} hook at {target_hook}')
        for legacy_path in removed_legacy_paths:
            print(f'Removed legacy hook script at {legacy_path}')
    return 0


def uninstall_family(settings_path: Path) -> int:
    data = load_settings(settings_path)
    changes = []

    for event_name in TARGET_HOOK_RELATIVE_PATHS:
        target_hook = target_hook_path(settings_path, event_name)
        hook_entry = build_hook_entry(target_hook, event_name)
        current_changed = remove_hook(data, event_name, hook_entry)
        changed = current_changed
        removed_script = False
        if current_changed and target_hook.exists():
            target_hook.unlink()
            removed_script = True
        removed_legacy_paths = []
        for legacy_path in legacy_target_hook_paths(settings_path, event_name):
            legacy_changed = remove_hook(data, event_name, build_hook_entry(legacy_path, event_name))
            changed = changed or legacy_changed
            if legacy_changed and legacy_path.exists():
                legacy_path.unlink()
                removed_legacy_paths.append(legacy_path)
        changes.append((event_name, changed, target_hook, removed_script, removed_legacy_paths))

    save_settings(settings_path, data)
    print(f'Updated {settings_path}')
    for event_name, changed, target_hook, removed_script, removed_legacy_paths in changes:
        status = 'Removed' if changed else 'No changes needed for'
        print(f'{status} {event_name} hook entry at {target_hook}')
        if removed_script:
            print(f'Removed hook script at {target_hook}')
        for legacy_path in removed_legacy_paths:
            print(f'Removed legacy hook script at {legacy_path}')
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] in {'--help', '-h'}:
        print(
            'Usage:\n'
            '  uv run install-hooks.py ensure_todo install <settings.json>\n'
            '  uv run install-hooks.py ensure_todo uninstall <settings.json>\n'
            '  uv run install-hooks.py --help\n'
        )
        return 0

    return 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
