import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'bin' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


client = module('fleet-ssh-client')
authorize = module('fleet-ssh-authorize')
KEY = client.HOSTS['mac-mini']['key'] + ' administration-test'


class FleetSSHTests(unittest.TestCase):
    def test_client_preserves_integrations_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, HOME=folder):
            home = Path(folder)
            ssh = home / '.ssh'
            ssh.mkdir()
            (ssh / 'test-key').touch()
            original = '# Integration\nInclude ~/.orbstack/ssh/config\n\nHost *\n  User wrong-user\n'
            (ssh / 'config').write_text(original)
            for _ in range(2):
                client.configure('mac-mini', '~/.ssh/test-key', 'tailnet')
            config = (ssh / 'config').read_text()
            self.assertLess(config.index('Include ~/.orbstack'), config.index('Include ~/.ssh/fleet-access'))
            self.assertEqual(config.count('Include ~/.ssh/fleet-access'), 1)
            self.assertIn('Host *\n  User wrong-user', config)
            self.assertEqual(len(list(ssh.glob('config.before-fleet-*'))), 1)
            effective = subprocess.check_output(
                ['ssh', '-G', '-F', str(ssh / 'config'), 'mac-mini'], text=True)
            for setting in ('hostname 100.90.54.59', 'user superterran',
                            'addressfamily inet', 'identityagent none',
                            'stricthostkeychecking true', 'forwardagent no'):
                self.assertIn(setting, effective)
            self.assertEqual((ssh / 'fleet-known-hosts').stat().st_mode & 0o777, 0o600)

    def test_missing_identity_does_not_modify_config(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, HOME=folder):
            with self.assertRaises(RuntimeError):
                client.configure('mac-mini', '~/.ssh/missing', 'tailnet')
            self.assertFalse((Path(folder) / '.ssh/config').exists())

    def test_lan_default_keeps_explicit_tailnet_alias_on_tailnet(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, HOME=folder):
            ssh = Path(folder) / '.ssh'
            ssh.mkdir()
            (ssh / 'test-key').touch()
            client.configure('mac-mini', '~/.ssh/test-key', 'lan')
            for host, address in [('mac-mini', 'mac-mini.local'),
                                  ('100.90.54.59', '100.90.54.59')]:
                effective = subprocess.check_output(
                    ['ssh', '-G', '-F', str(ssh / 'config'), host], text=True)
                self.assertIn('hostname ' + address, effective)

    def test_authorization_has_real_newlines_and_preserves_service_key(self):
        service = 'from="10.0.0.75",restrict,command="/service" ssh-ed25519 OTHER service-key\n'
        entry = {'key': KEY, 'sources': ['100.119.114.55']}
        result = authorize.merge(service, [entry])
        self.assertEqual(len(result.splitlines()), 2)
        self.assertTrue(result.startswith(service))
        self.assertNotIn('\\n', result)
        self.assertEqual(authorize.merge(result, [entry]), result)

    def test_existing_admin_key_extends_only_source_list(self):
        before = 'from="10.0.0.75",no-agent-forwarding ' + KEY + '\n'
        after = authorize.merge(before, [{'key': KEY, 'sources': ['100.101.167.38']}])
        self.assertEqual(after, before.replace('10.0.0.75', '10.0.0.75,100.101.167.38'))

    def test_forced_command_key_cannot_be_broadened(self):
        service = 'from="10.0.0.75",restrict,command="/service" ' + KEY + '\n'
        with self.assertRaises(ValueError):
            authorize.merge(service, [{'key': KEY, 'sources': ['100.101.167.38']}])

    def test_multiline_key_and_unbounded_sources_are_rejected(self):
        for entry in ({'key': KEY + '\n' + KEY, 'sources': ['10.0.0.1']},
                      {'key': KEY, 'sources': []},
                      {'key': KEY, 'sources': ['*']}):
            with self.assertRaises(ValueError):
                authorize.merge('', [entry])

    def test_kvm_recovery_gate_checks_actual_source_before_command(self):
        wrapper = ROOT / 'config/kvm-mini-closet-ssh.sh'
        for source, success in [('100.101.167.38', True), ('10.0.0.75', True),
                                ('100.119.114.55', False), ('', False)]:
            result = subprocess.run(['sh', str(wrapper)], capture_output=True, text=True,
                                    env={**os.environ,
                                         'SSH_CONNECTION': source + ' 50000 100.102.2.16 22',
                                         'SSH_ORIGINAL_COMMAND': 'echo permitted'})
            self.assertEqual(result.returncode == 0, success)
            self.assertEqual('permitted' in result.stdout, success)


if __name__ == '__main__':
    unittest.main()
