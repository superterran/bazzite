import importlib.util
from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('nightly', Path(__file__).resolve().parents[1] / 'bin/nightly-maintenance.py')
nightly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nightly)


class NightlyTests(unittest.TestCase):
    def test_window_excludes_daytime_catchup(self):
        self.assertTrue(nightly.within_window(datetime(2026, 10, 24, 5, 0)))
        self.assertFalse(nightly.within_window(datetime(2026, 10, 24, 6, 0)))
        self.assertFalse(nightly.within_window(datetime(2026, 10, 24, 12, 0)))

    def test_only_unbooted_staged_deployment_needs_reboot(self):
        self.assertTrue(nightly.staged_update({'deployments': [{'booted': False, 'staged': True}]}))
        self.assertFalse(nightly.staged_update({'deployments': [{'booted': True}, {'booted': False, 'staged': False}]}))

    def cycle(self, reasons, pending=True, hour=5, fingerprints=('same', 'same')):
        with tempfile.TemporaryDirectory() as temp, patch.object(nightly, 'STATE', Path(temp)), \
                patch.object(nightly.decky, 'busy_reason', side_effect=reasons), \
                patch.object(nightly, 'fingerprint', side_effect=fingerprints), \
                patch.object(nightly, 'pending_reboot', return_value=pending), \
                patch.object(nightly.subprocess, 'run') as run, \
                patch.object(nightly, 'datetime') as clock, patch('sys.argv', ['nightly']):
            clock.now.return_value = datetime(2026, 10, 24, hour, 0)
            nightly.main()
            return [c.args[0] for c in run.call_args_list]

    def test_game_running_skips_updates_and_reboot(self):
        self.assertEqual(self.cycle(['Game running']), [])

    def test_game_started_during_updates_blocks_reboot(self):
        commands = self.cycle([None, None, 'Game started'])
        self.assertNotIn(['systemctl', 'reboot'], commands)
        self.assertIn(['systemctl', 'start', 'uupd.service'], commands)

    def test_no_update_means_no_reboot(self):
        self.assertNotIn(['systemctl', 'reboot'], self.cycle([None, None], pending=False))

    def test_pending_update_and_idle_allows_reboot(self):
        self.assertEqual(self.cycle([None, None, None])[-1], ['systemctl', 'reboot'])

    def test_daytime_run_does_nothing(self):
        self.assertEqual(self.cycle([None], hour=12), [])


if __name__ == '__main__':
    unittest.main()
