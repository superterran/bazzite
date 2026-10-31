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
                session.request('game')
        run.assert_not_called()

    def test_switch_request_uses_independent_unit(self):
        with patch.object(session, 'current_mode', return_value='desktop'), \
                patch.object(session, 'local_session', return_value='2'), \
                patch.object(session, 'run') as run:
            session.request('game')
        self.assertEqual(run.call_args.args[:3], ('systemd-run', '--user', '--collect'))
        self.assertIn('--worker', run.call_args.args)

    def test_failed_logout_recovers_sunshine(self):
        def fake_run(*args, **kwargs):
            if args[0].endswith('switch-bazzite-session.sh') and len(args) == 2:
                raise subprocess.CalledProcessError(1, args)
        with patch.object(session, 'current_mode', return_value='game'), \
                patch.object(session, 'local_session', return_value='2'), \
                patch.object(session.time, 'sleep'), \
                patch.object(session, 'run', side_effect=fake_run) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                session.switch('desktop')
        self.assertEqual(run.call_args.args, ('systemctl', '--user', 'start', session.SUNSHINE))

    def test_successful_switch_waits_for_replacement_session(self):
        with patch.object(session, 'current_mode', side_effect=['game', 'game', 'desktop']), \
                patch.object(session, 'local_session', side_effect=['2', '2', '3']), \
                patch.object(session.time, 'sleep'), \
                patch.object(session, 'run') as run:
            session.switch('desktop')
        calls = [c.args for c in run.call_args_list]
        self.assertIn(('systemctl', '--user', 'stop', session.SUNSHINE), calls)
        self.assertEqual(calls[-1], ('systemctl', '--user', 'start', session.SUNSHINE))

    def test_deployment_preserves_custom_apps_and_environment(self):
        with tempfile.TemporaryDirectory() as home:
            target = Path(home) / '.config/sunshine/apps.json'
            target.parent.mkdir(parents=True)
            original = {'env': {'CUSTOM': 'keep'}, 'apps': [
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
