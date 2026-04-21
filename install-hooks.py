#!/usr/bin/env python3
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load_module(module_name: str, relative_path: str):
    file_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load module from {file_path}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NOTIFY_INSTALL = load_module('notify_install', 'hooks/notify/install.py')
ENSURE_TODO_INSTALL = load_module('ensure_todo_install', 'hooks/ensure_todo/install.py')


def show_help() -> None:
    print(
        'Usage:\n'
        '  uv run install-hooks.py <sub_module> install <settings.json>\n'
        '  uv run install-hooks.py <sub_module> uninstall <settings.json>\n'
        '  uv run install-hooks.py --help\n\n'
        'Sub-modules:\n'
        '  notify       Install or uninstall the notification hook family\n'
        '  ensure_todo  Install or uninstall the stop/post-tool-use todo hook family\n'
        '  all          Install or uninstall all hook families\n'
    )


FAMILY_HANDLERS = {
    'notify': (NOTIFY_INSTALL.install_family, NOTIFY_INSTALL.uninstall_family),
    'ensure_todo': (ENSURE_TODO_INSTALL.install_family, ENSURE_TODO_INSTALL.uninstall_family),
}


def run_command(sub_module: str, command: str, settings_path: Path) -> int:
    if sub_module == 'all':
        handlers = FAMILY_HANDLERS.values()
    else:
        family = FAMILY_HANDLERS.get(sub_module)
        if family is None:
            show_help()
            return 1
        handlers = [family]

    exit_code = 0
    for install_handler, uninstall_handler in handlers:
        code = install_handler(settings_path) if command == 'install' else uninstall_handler(settings_path)
        if code != 0:
            exit_code = code
    return exit_code


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] in {'--help', '-h'}:
        show_help()
        return 0

    if len(argv) != 4 or argv[1] not in {*FAMILY_HANDLERS.keys(), 'all'} or argv[2] not in {'install', 'uninstall'}:
        show_help()
        return 1

    sub_module = argv[1]
    command = argv[2]
    settings_path = Path(argv[3]).expanduser().resolve()
    return run_command(sub_module, command, settings_path)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
