#!/usr/bin/env python3
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def escape_applescript(value: str) -> str:
    return value.replace('\\', '\\\\').replace('"', '\\"')


def project_name_from_cwd(cwd: str) -> str:
    if not cwd:
        return 'unknown-project'
    return Path(cwd).name or 'unknown-project'


def notify_macos(message: str, project_name: str) -> None:
    safe_message = escape_applescript(message)
    safe_project_name = escape_applescript(project_name)
    subprocess.run(
        [
            'osascript',
            '-e',
            f'display notification "{safe_message}" with title "Claude Code" subtitle "{safe_project_name}" sound name "Heroine"',
        ],
        check=False,
    )


def notify_windows(title: str, message: str) -> None:
    script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] > $null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml('<toast><visual><binding template="ToastGeneric"><text>{title}</text><text>{message}</text></binding></visual></toast>')
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Code').Show($toast)
""".strip()
    subprocess.run(
        ['powershell', '-NoProfile', '-Command', script],
        check=False,
    )


def notify_linux(title: str, message: str) -> None:
    if shutil.which('notify-send') is None:
        return
    subprocess.run(['notify-send', title, message], check=False)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    title = payload.get('title') or 'Claude Code'
    message = payload.get('message') or 'Claude Code notification'
    notification_type = payload.get('notification_type') or payload.get('hook_event_name') or payload.get('event_name') or 'unknown'
    project_name = project_name_from_cwd(payload.get('cwd') or '')
    system = platform.system()

    if system == 'Darwin':
        notify_macos(message, project_name)
    elif system == 'Windows':
        notify_windows(title, f'[{project_name}] {message} ({notification_type})')
    else:
        notify_linux(title, f'[{project_name}] {message} ({notification_type})')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
