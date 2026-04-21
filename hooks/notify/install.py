#!/usr/bin/env python3
import json
import shutil
import sys
from pathlib import Path


TARGET_HOOK_RELATIVE_PATH = Path('hooks/notify_user.py')
SOURCE_HOOK_NAME = 'notify_user.py'


def show_help() -> None:
    print(
        'Usage:\n'
        '  uv run install-hooks.py notify install <settings.json>\n'
        '  uv run install-hooks.py notify uninstall <settings.json>\n'
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


def build_hook_entry(target_hook: Path) -> dict:
    return {
        'matcher': '*',
        'hooks': [
            {
                'type': 'command',
                'command': f'uv run "{target_hook}"',
            }
        ],
    }


def ensure_notification_hook(data: dict, hook_entry: dict) -> bool:
    hooks = data.setdefault('hooks', {})
    notification_hooks = hooks.setdefault('Notification', [])

    for entry in notification_hooks:
        if entry == hook_entry:
            return False

    notification_hooks.append(hook_entry)
    return True


def remove_notification_hook(data: dict, hook_entry: dict) -> bool:
    hooks = data.get('hooks')
    if not isinstance(hooks, dict):
        return False

    notification_hooks = hooks.get('Notification')
    if not isinstance(notification_hooks, list):
        return False

    remaining_hooks = [entry for entry in notification_hooks if entry != hook_entry]
    if len(remaining_hooks) == len(notification_hooks):
        return False

    if remaining_hooks:
        hooks['Notification'] = remaining_hooks
    else:
        hooks.pop('Notification', None)
        if not hooks:
            data.pop('hooks', None)

    return True


def install_family(settings_path: Path) -> int:
    target_hook = install_hook_script(settings_path)
    hook_entry = build_hook_entry(target_hook)
    data = load_settings(settings_path)
    changed = ensure_notification_hook(data, hook_entry)
    save_settings(settings_path, data)

    print(f'Updated {settings_path}' if changed else f'No changes needed for {settings_path}')
    print(f'Installed hook script at {target_hook}')
    return 0


def uninstall_family(settings_path: Path) -> int:
    target_hook = target_hook_path(settings_path)
    hook_entry = build_hook_entry(target_hook)
    data = load_settings(settings_path)
    changed = remove_notification_hook(data, hook_entry)
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
