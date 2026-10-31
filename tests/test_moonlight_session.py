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

    def test_stale_hooks_never_change_any_session(self):
        for mode in ('game', 'desktop', 'unknown'):
            with patch.object(session, 'current_mode', return_value=mode), \
                    patch.object(session, 'run') as run:
                session.request('desktop')
                session.switch('game')
            run.assert_not_called()

    def test_shipped_entries_have_no_commands_or_redundant_desktop(self):
        data = json.loads((Path(__file__).parents[1] / 'config/sunshine/apps.json').read_text())
        self.assertEqual({a['name'] for a in data['apps']},
                         {'Display Mode', 'Steam Big Picture'})
        for app in data['apps']:
            for field in ('prep-cmd', 'detached', 'cmd'):
                self.assertFalse(app.get(field))

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
            self.assertEqual(len(result['apps']), 3)
            self.assertEqual(result['apps'][-1], original['apps'][-1])
            self.assertNotIn('detached', result['apps'][1])
            self.assertEqual(len(list(target.parent.glob('apps.json.before-*'))), 1)


if __name__ == '__main__':
    unittest.main()
