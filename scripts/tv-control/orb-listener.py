#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["evdev>=1.7"]
# ///
"""PS/Home button → pause Apple TV and select PC HDMI, without grabbing input."""
from __future__ import annotations
import asyncio
import os
from pathlib import Path
import signal
import time

from evdev import InputDevice, ecodes, list_devices

DEBOUNCE_SEC = 2.0
SCRIPT_DIR = Path(__file__).parent
ATV_SCRIPT = SCRIPT_DIR / "atv.py"
TV_SWITCH = SCRIPT_DIR / "tv-switch.sh"
TARGET_INPUT = os.environ.get("TV_PC_INPUT", "hdmi2").lower()


def supported_controller(name: str) -> bool:
    return name in {"DualSense Wireless Controller", "DualShock 4 Wireless Controller"} or (
        "8bitdo" in name.lower() and "ultimate" in name.lower()
        and not any(part in name.lower() for part in ("motion", "touchpad", "keyboard"))
    )


async def _run(label: str, *cmd: str, timeout: float = 8.0) -> int:
    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        if proc and proc.returncode is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await proc.wait()
        print(f"{label}: timeout after {timeout}s", flush=True)
        return -1
    except OSError as exc:
        print(f"{label}: could not start ({exc})", flush=True)
        return -1
    if proc.returncode != 0:
        print(f"{label}: failed ({proc.returncode}) {err.decode().strip()}", flush=True)
    else:
        msg = (out.decode().strip() or "ok").splitlines()[-1]
        print(f"{label}: {msg}", flush=True)
    return proc.returncode


async def _fire_tv_switch() -> None:
    # Start the input change immediately even if Apple TV is asleep/unreachable.
    await asyncio.gather(
        _run("atv pause", str(ATV_SCRIPT), "pause", timeout=6.0),
        _run(f"tv-switch {TARGET_INPUT}", str(TV_SWITCH), TARGET_INPUT, timeout=10.0),
    )


class SwitchGate:
    def __init__(self):
        self.last_fire = float('-inf')
        self.task = None

    def press(self) -> bool:
        now = time.monotonic()
        if now - self.last_fire < DEBOUNCE_SEC or self.task and not self.task.done():
            return False
        self.last_fire = now
        self.task = asyncio.create_task(_fire_tv_switch())
        return True


async def _watch(dev: InputDevice, gate: SwitchGate) -> None:
    print(f"Watching {dev.path} ({dev.name}) for PS/Home button press", flush=True)
    try:
        async for event in dev.async_read_loop():
            # No grab: Steam receives the same guide button, including its chords.
            if event.type == ecodes.EV_KEY and event.code == ecodes.BTN_MODE and event.value == 1:
                if gate.press():
                    print(f"{dev.name}: PS/Home → selecting {TARGET_INPUT}", flush=True)
    except OSError as exc:
        print(f"{dev.name}: disconnected ({exc})", flush=True)
    finally:
        dev.close()


async def main() -> None:
    if TARGET_INPUT not in {"hdmi1", "hdmi2", "hdmi3", "hdmi4"}:
        raise ValueError("TV_PC_INPUT must be hdmi1, hdmi2, hdmi3 or hdmi4")
    gate = SwitchGate()
    watchers = {}
    waiting = False
    while True:
        for path, task in list(watchers.items()):
            if task.done():
                task.result()
                del watchers[path]
        for path in list_devices():
            if path in watchers:
                continue
            try:
                dev = InputDevice(path)
            except OSError:
                continue
            if not supported_controller(dev.name) or ecodes.BTN_MODE not in dev.capabilities().get(ecodes.EV_KEY, []):
                dev.close()
                continue
            watchers[path] = asyncio.create_task(_watch(dev, gate))
        if not watchers and not waiting:
            print("No supported controller connected; waiting for DualSense or 8BitDo", flush=True)
        waiting = not watchers
        await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())
