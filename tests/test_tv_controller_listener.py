import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

spec = importlib.util.spec_from_file_location('listener', Path(__file__).resolve().parents[1] / 'scripts/tv-control/orb-listener.py')
listener = importlib.util.module_from_spec(spec)
spec.loader.exec_module(listener)


class ListenerTests(unittest.IsolatedAsyncioTestCase):
    def test_only_actual_controllers(self):
        self.assertTrue(listener.supported_controller('DualSense Wireless Controller'))
        self.assertTrue(listener.supported_controller('8BitDo Ultimate Wireless Controller'))
        self.assertFalse(listener.supported_controller('DualSense Wireless Controller Touchpad'))
        self.assertFalse(listener.supported_controller('DualSense Wireless Controller Motion Sensors'))

    async def test_short_press_works_and_repeat_release_ignored(self):
        key = listener.ecodes
        async def events():
            for value in [1, 2, 0]:
                yield SimpleNamespace(type=key.EV_KEY, code=key.BTN_MODE, value=value)
        device = SimpleNamespace(path='test', name='DualSense Wireless Controller', async_read_loop=events, close=Mock())
        gate = Mock()
        await listener._watch(device, gate)
        gate.press.assert_called_once()
        device.close.assert_called_once()

    async def test_debounce_and_inflight(self):
        wait = asyncio.Event()
        async def switch():
            await wait.wait()
        with patch.object(listener, '_fire_tv_switch', side_effect=switch), patch.object(listener, 'time', SimpleNamespace(monotonic=lambda: 10)):
            gate = listener.SwitchGate()
            self.assertTrue(gate.press())
            self.assertFalse(gate.press())
        with patch.object(listener, 'time', SimpleNamespace(monotonic=lambda: 15)):
            self.assertFalse(gate.press())
        wait.set()
        await gate.task
        with patch.object(listener, '_fire_tv_switch', new_callable=AsyncMock), patch.object(listener, 'time', SimpleNamespace(monotonic=lambda: 16)):
            self.assertTrue(gate.press())
            await gate.task

    async def test_tv_selection_does_not_depend_on_pause_success(self):
        with patch.object(listener, '_run', new_callable=AsyncMock, side_effect=[-1, 0]) as run:
            await listener._fire_tv_switch()
            self.assertEqual(run.await_count, 2)
            self.assertIn('tv-switch hdmi2', [c.args[0] for c in run.await_args_list])

    async def test_command_timeout_cleans_up(self):
        self.assertEqual(await listener._run('test timeout', '/usr/bin/sleep', '5', timeout=.05), -1)


if __name__ == '__main__':
    unittest.main()
