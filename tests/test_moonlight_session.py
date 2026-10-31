import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'moonlight_session', Path(__file__).parents[1] / 'bin/moonlight-session.py')
session = importlib.util.module_from_spec(spec)
spec.loader.exec_module(session)


class MoonlightSessionTests(unittest.TestCase):
    def test_game_mode_request_never_runs_a_command_when_already_in_game(self):
        with patch.object(session, 'current_mode', return_value='game'), \
                patch.object(session, 'run') as run:
            session.request('game')
        run.assert_not_called()

    def test_desktop_request_is_also_idempotent(self):
        with patch.object(session, 'current_mode', return_value='desktop'), \
                patch.object(session, 'run') as run:
            session.request('desktop')
        run.assert_not_called()

    def test_unknown_session_is_never_logged_out(self):
        with patch.object(session, 'current_mode', return_value='unknown'), \
                patch.object(session, 'run') as run:
            with self.assertRaises(RuntimeError):
                session.request('desktop')
        run.assert_not_called()

    def test_switch_uses_shared_steam_session_helper(self):
        with patch.object(session, 'current_mode', return_value='game'), \
                patch.object(session, 'run') as run:
            session.request('desktop')
        self.assertEqual(Path(run.call_args.args[0]).name, 'switch-bazzite-session.sh')
        self.assertEqual(run.call_args.args[1], 'desktop')

    def test_game_to_gnome_worker_stops_graphical_targets_before_relogin(self):
        root = Path(__file__).parents[1]
        if not Path('/usr/share/wayland-sessions/gnome.desktop').exists():
            self.skipTest('Requires the Bazzite GNOME session definition')
        with tempfile.TemporaryDirectory() as folder:
            mockbin = Path(folder)
            for name, body in {
                'sudo': 'exit 0',
                'pgrep': 'exit 1',
                'systemctl': 'printf "%s\\n" "$*" >> "$CALLS"; exit 0',
                'loginctl': 'echo unexpected-loginctl >&2; exit 99',
            }.items():
                p = mockbin / name
                p.write_text('#!/bin/sh\n' + body + '\n')
                p.chmod(0o755)
            calls = mockbin / 'calls'
            subprocess.run(['bash', str(root / 'bin/switch-bazzite-session.sh'),
                            'desktop', '--worker'], check=True, capture_output=True,
                           env={**os.environ, 'PATH': str(mockbin) + ':' + os.environ['PATH'],
                                'CALLS': str(calls)})
            self.assertIn('--user stop gamescope-session.target graphical-session.target '
                          'graphical-session-pre.target', calls.read_text())

    def test_steam_compatibility_command_reaches_helper_without_runtime_libraries(self):
        root = Path(__file__).parents[1]
        with tempfile.TemporaryDirectory() as folder:
            helper = Path(folder) / 'repos/bazzite/bin/switch-bazzite-session.sh'
            helper.parent.mkdir(parents=True)
            helper.write_text('#!/bin/sh\ntest -z "${LD_LIBRARY_PATH:-}" || exit 99\n'
                              'printf "%s\\n" "$*" > "$HOME/args"\n')
            helper.chmod(0o755)
            subprocess.run(['bash', str(root / 'bin/steamosctl-compat'),
                            'switch-to-desktop-mode', 'gnome.desktop'], check=True,
                           env={**os.environ, 'HOME': folder,
                                'LD_LIBRARY_PATH': '/unwanted-steam-runtime'})
            self.assertEqual((Path(folder) / 'args').read_text(), 'desktop\n')

    def test_display_is_passive_and_steam_never_launches_or_focuses_steam(self):
        data = json.loads((Path(__file__).parents[1] / 'config/sunshine/apps.json').read_text())
        self.assertEqual({a['name'] for a in data['apps']},
                         {'Desktop', 'Display Mode', 'Steam Big Picture'})
        for app in data['apps']:
            for field in ('detached', 'cmd'):
                self.assertFalse(app.get(field))
            if app['name'] == 'Display Mode':
                self.assertFalse(app.get('prep-cmd'))

    def test_deployment_preserves_custom_apps_and_environment(self):
        with tempfile.TemporaryDirectory() as home:
            target = Path(home) / '.config/sunshine/apps.json'
            target.parent.mkdir(parents=True)
            original = {'env': {'CUSTOM': 'keep'}, 'apps': [
                {'name': 'Desktop', 'prep-cmd': [{'do': 'old-switch-command'}]},
                {'name': 'Steam Big Picture', 'detached': ['old-focus-command']},
                {'name': 'Custom App', 'cmd': 'keep-command'}]}
            target.write_text(json.dumps(original))
            deploy = Path(__file__).parents[1] / 'bin/setup-moonlight-apps.py'
            for _ in range(2):
                subprocess.run(['python3', str(deploy)], env={**os.environ, 'HOME': home},
                               check=True, capture_output=True)
            result = json.loads(target.read_text())
            self.assertEqual(result['env'], original['env'])
            self.assertEqual(len(result['apps']), 4)
            self.assertEqual(result['apps'][-1], original['apps'][-1])
            self.assertNotIn('detached', result['apps'][1])
            self.assertEqual(len(list(target.parent.glob('apps.json.before-*'))), 1)


if __name__ == '__main__':
    unittest.main()
