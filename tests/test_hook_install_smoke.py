import json
import tempfile
import unittest
from pathlib import Path

from hooks.ensure_todo.install import install_family as install_ensure_todo
from hooks.ensure_todo.install import uninstall_family as uninstall_ensure_todo
from hooks.notify.install import install_family as install_notify
from hooks.notify.install import uninstall_family as uninstall_notify


class HookInstallSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_path = Path(self.temp_dir.name)
        self.settings_path = self.base_path / '.claude' / 'settings.json'
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def read_settings(self) -> dict:
        return json.loads(self.settings_path.read_text())

    def test_notify_install_and_uninstall_use_family_directory(self) -> None:
        self.assertEqual(install_notify(self.settings_path), 0)

        target_script = self.base_path / '.claude' / 'hooks' / 'notify' / 'notify_user.py'
        self.assertTrue(target_script.exists())

        data = self.read_settings()
        command = data['hooks']['Notification'][0]['hooks'][0]['command']
        self.assertEqual(command, f'uv run "{target_script.resolve()}"')

        self.assertEqual(uninstall_notify(self.settings_path), 0)
        self.assertFalse(target_script.exists())
        self.assertEqual(self.read_settings(), {})

    def test_notify_install_removes_legacy_entry_and_script(self) -> None:
        legacy_script = self.base_path / '.claude' / 'hooks' / 'notify_user.py'
        legacy_script.parent.mkdir(parents=True, exist_ok=True)
        legacy_script.write_text('# legacy notify script\n')
        self.settings_path.write_text(
            json.dumps(
                {
                    'hooks': {
                        'Notification': [
                            {
                                'matcher': '*',
                                'hooks': [
                                    {
                                        'type': 'command',
                                        'command': f'uv run "{legacy_script.resolve()}"',
                                    }
                                ],
                            }
                        ]
                    }
                }
            )
        )

        self.assertEqual(install_notify(self.settings_path), 0)

        target_script = self.base_path / '.claude' / 'hooks' / 'notify' / 'notify_user.py'
        data = self.read_settings()
        notification_hooks = data['hooks']['Notification']
        self.assertEqual(len(notification_hooks), 1)
        command = notification_hooks[0]['hooks'][0]['command']
        self.assertEqual(command, f'uv run "{target_script.resolve()}"')
        self.assertFalse(legacy_script.exists())

    def test_ensure_todo_install_and_uninstall_use_family_directory(self) -> None:
        self.assertEqual(install_ensure_todo(self.settings_path), 0)

        stop_script = self.base_path / '.claude' / 'hooks' / 'ensure_todo' / 'ensure_todo_stop.py'
        post_tool_use_script = self.base_path / '.claude' / 'hooks' / 'ensure_todo' / 'ensure_todo_post_tool_use.py'
        self.assertTrue(stop_script.exists())
        self.assertTrue(post_tool_use_script.exists())

        data = self.read_settings()
        stop_command = data['hooks']['Stop'][0]['hooks'][0]['command']
        post_tool_use_command = data['hooks']['PostToolUse'][0]['hooks'][0]['command']
        self.assertEqual(stop_command, f'uv run "{stop_script.resolve()}"')
        self.assertEqual(post_tool_use_command, f'uv run "{post_tool_use_script.resolve()}"')

        self.assertEqual(uninstall_ensure_todo(self.settings_path), 0)
        self.assertFalse(stop_script.exists())
        self.assertFalse(post_tool_use_script.exists())
        self.assertEqual(self.read_settings(), {})

    def test_ensure_todo_install_removes_legacy_entries_and_scripts(self) -> None:
        legacy_stop_script = self.base_path / '.claude' / 'hooks' / 'ensure_todo_stop.py'
        legacy_post_tool_use_script = self.base_path / '.claude' / 'hooks' / 'ensure_todo_post_tool_use.py'
        legacy_stop_script.parent.mkdir(parents=True, exist_ok=True)
        legacy_stop_script.write_text('# legacy stop script\n')
        legacy_post_tool_use_script.write_text('# legacy post tool use script\n')
        self.settings_path.write_text(
            json.dumps(
                {
                    'hooks': {
                        'Stop': [
                            {
                                'matcher': '*',
                                'hooks': [
                                    {
                                        'type': 'command',
                                        'command': f'uv run "{legacy_stop_script.resolve()}"',
                                    }
                                ],
                            }
                        ],
                        'PostToolUse': [
                            {
                                'matcher': 'Edit|Write|MultiEdit',
                                'hooks': [
                                    {
                                        'type': 'command',
                                        'command': f'uv run "{legacy_post_tool_use_script.resolve()}"',
                                    }
                                ],
                            }
                        ],
                    }
                }
            )
        )

        self.assertEqual(install_ensure_todo(self.settings_path), 0)

        stop_script = self.base_path / '.claude' / 'hooks' / 'ensure_todo' / 'ensure_todo_stop.py'
        post_tool_use_script = self.base_path / '.claude' / 'hooks' / 'ensure_todo' / 'ensure_todo_post_tool_use.py'
        data = self.read_settings()

        stop_hooks = data['hooks']['Stop']
        post_tool_use_hooks = data['hooks']['PostToolUse']
        self.assertEqual(len(stop_hooks), 1)
        self.assertEqual(len(post_tool_use_hooks), 1)
        self.assertEqual(stop_hooks[0]['hooks'][0]['command'], f'uv run "{stop_script.resolve()}"')
        self.assertEqual(post_tool_use_hooks[0]['hooks'][0]['command'], f'uv run "{post_tool_use_script.resolve()}"')
        self.assertFalse(legacy_stop_script.exists())
        self.assertFalse(legacy_post_tool_use_script.exists())

    def test_legacy_only_uninstall_does_not_delete_current_notify_script(self) -> None:
        current_script = self.base_path / '.claude' / 'hooks' / 'notify' / 'notify_user.py'
        legacy_script = self.base_path / '.claude' / 'hooks' / 'notify_user.py'
        current_script.parent.mkdir(parents=True, exist_ok=True)
        legacy_script.parent.mkdir(parents=True, exist_ok=True)
        current_script.write_text('# current notify script\n')
        legacy_script.write_text('# legacy notify script\n')
        self.settings_path.write_text(
            json.dumps(
                {
                    'hooks': {
                        'Notification': [
                            {
                                'matcher': '*',
                                'hooks': [
                                    {
                                        'type': 'command',
                                        'command': f'uv run "{legacy_script.resolve()}"',
                                    }
                                ],
                            }
                        ]
                    }
                }
            )
        )

        self.assertEqual(uninstall_notify(self.settings_path), 0)

        self.assertTrue(current_script.exists())
        self.assertFalse(legacy_script.exists())
        self.assertEqual(self.read_settings(), {})

    def test_legacy_only_uninstall_does_not_delete_current_ensure_todo_scripts(self) -> None:
        current_stop_script = self.base_path / '.claude' / 'hooks' / 'ensure_todo' / 'ensure_todo_stop.py'
        current_post_tool_use_script = self.base_path / '.claude' / 'hooks' / 'ensure_todo' / 'ensure_todo_post_tool_use.py'
        legacy_stop_script = self.base_path / '.claude' / 'hooks' / 'ensure_todo_stop.py'
        legacy_post_tool_use_script = self.base_path / '.claude' / 'hooks' / 'ensure_todo_post_tool_use.py'
        current_stop_script.parent.mkdir(parents=True, exist_ok=True)
        legacy_stop_script.parent.mkdir(parents=True, exist_ok=True)
        current_stop_script.write_text('# current stop script\n')
        current_post_tool_use_script.write_text('# current post tool use script\n')
        legacy_stop_script.write_text('# legacy stop script\n')
        legacy_post_tool_use_script.write_text('# legacy post tool use script\n')
        self.settings_path.write_text(
            json.dumps(
                {
                    'hooks': {
                        'Stop': [
                            {
                                'matcher': '*',
                                'hooks': [
                                    {
                                        'type': 'command',
                                        'command': f'uv run "{legacy_stop_script.resolve()}"',
                                    }
                                ],
                            }
                        ],
                        'PostToolUse': [
                            {
                                'matcher': 'Edit|Write|MultiEdit',
                                'hooks': [
                                    {
                                        'type': 'command',
                                        'command': f'uv run "{legacy_post_tool_use_script.resolve()}"',
                                    }
                                ],
                            }
                        ],
                    }
                }
            )
        )

        self.assertEqual(uninstall_ensure_todo(self.settings_path), 0)

        self.assertTrue(current_stop_script.exists())
        self.assertTrue(current_post_tool_use_script.exists())
        self.assertFalse(legacy_stop_script.exists())
        self.assertFalse(legacy_post_tool_use_script.exists())
        self.assertEqual(self.read_settings(), {})


if __name__ == '__main__':
    unittest.main()
