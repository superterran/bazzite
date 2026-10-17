import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest


class SessionTests(unittest.TestCase):
    def test_stop_requests_clean_unload_before_launcher_returns(self):
        module_dir = Path(__file__).parents[1] / 'bin'
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            fake = root / 'core.py'
            fake.write_text(
                "import socket, pathlib\n"
                f"root=pathlib.Path({folder!r})\n"
                "s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)\n"
                f"s.bind(('127.0.0.1',{port}))\n"
                "(root/'ready').touch()\n"
                "while s.recvfrom(100)[0]!=b'QUIT':pass\n"
                "(root/'saved').write_text('unloaded')\n")
            expression = (f'import sys;sys.path.insert(0,{str(module_dir)!r});'
                          'from retroarch_session import run_session;'
                          f'raise SystemExit(run_session([sys.executable,{str(fake)!r}],{port}))')
            wrapper = subprocess.Popen([sys.executable, '-c', expression])
            try:
                deadline = time.monotonic() + 5
                while not (root / 'ready').exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue((root / 'ready').exists())
                wrapper.send_signal(signal.SIGTERM)
                self.assertEqual(wrapper.wait(timeout=5), 0)
                self.assertEqual((root / 'saved').read_text(), 'unloaded')
            finally:
                if wrapper.poll() is None:
                    wrapper.kill()
                    wrapper.wait()

    def test_normal_exit_preserves_result(self):
        module_dir = Path(__file__).parents[1] / 'bin'
        expression = (f'import sys;sys.path.insert(0,{str(module_dir)!r});'
                      'from retroarch_session import run_session;'
                      'raise SystemExit(run_session([sys.executable,"-c","raise SystemExit(7)"],55356))')
        result = subprocess.run([sys.executable, '-c', expression], timeout=5)
        self.assertEqual(result.returncode, 7)

    def test_occupied_control_port_never_launches_another_game(self):
        import importlib.util
        module_path = Path(__file__).parents[1] / 'bin/retroarch_session.py'
        spec = importlib.util.spec_from_file_location('session', module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('0.0.0.0', 0))
            with self.assertRaises(OSError):
                module.run_session(['definitely-not-an-executable'], sock.getsockname()[1])
