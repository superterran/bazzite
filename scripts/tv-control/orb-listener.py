#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["evdev>=1.7"]
# ///
"""
Watch the 8BitDo Ultimate Wireless Controller for orb-button (BTN_MODE) presses
and switch the TV to the PC's HDMI input on each press. Reconnects if the device
disappears (controller sleep, dongle unplug, etc).

Sequence per press:
  1. atv.py pause       (best-effort — preserve Apple TV playback position)
  2. tv-switch.sh hdmi2 (the actual TV input switch via ADB/TIF)

Debounces: ignores a press if one fired in the last DEBOUNCE_SEC.
"""
from __future__ import annotations
import asyncio
import os
import time
from pathlib import Path

from evdev import InputDevice, ecodes, list_devices

DEVICE_BY_ID = Path("/dev/input/by-id/usb-8BitDo_Ultimate_Wireless_Controller_912c5bd817e4-event-joystick")
DEVICE_NAME_HINT = "8BitDo Ultimate"
BTN_ORB = ecodes.BTN_MODE  # 316
DEBOUNCE_SEC = 1.5

SCRIPT_DIR = Path(__file__).parent
ATV_SCRIPT = SCRIPT_DIR / "atv.py"
TV_SWITCH = SCRIPT_DIR / "tv-switch.sh"
TARGET_INPUT = os.environ.get("TV_PC_INPUT", "hdmi2").lower()


def _find_device() -> InputDevice | None:
    if DEVICE_BY_ID.exists():
        try:
            return InputDevice(str(DEVICE_BY_ID))
        except OSError:
            pass
    for path in list_devices():
        try:
            dev = InputDevice(path)
        except OSError:
            continue
        if DEVICE_NAME_HINT.lower() in dev.name.lower():
            return dev
    return None


async def _run(label: str, *cmd: str, timeout: float = 8.0) -> int:
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        print(f"{label}: timeout after {timeout}s", flush=True)
        return -1
    if proc.returncode != 0:
        print(f"{label}: failed ({proc.returncode}) {err.decode().strip()}", flush=True)
    else:
        msg = (out.decode().strip() or "ok").splitlines()[-1]
        print(f"{label}: {msg}", flush=True)
    return proc.returncode


async def _fire_tv_switch() -> None:
    # Apple TV pause is best-effort; don't block the input switch on it.
    await _run("atv pause", str(ATV_SCRIPT), "pause", timeout=6.0)
    await _run(f"tv-switch {TARGET_INPUT}", str(TV_SWITCH), TARGET_INPUT, timeout=8.0)


async def _watch(dev: InputDevice) -> None:
    print(f"Watching {dev.path} ({dev.name}) for BTN_MODE", flush=True)
    last_fire = 0.0
    async for event in dev.async_read_loop():
        if event.type != ecodes.EV_KEY or event.code != BTN_ORB or event.value != 1:
            continue
        now = time.monotonic()
        if now - last_fire < DEBOUNCE_SEC:
            continue
        last_fire = now
        print("orb pressed → switching TV", flush=True)
        asyncio.create_task(_fire_tv_switch())


async def main() -> None:
    while True:
        dev = _find_device()
        if dev is None:
            print("8BitDo not present — waiting 5s", flush=True)
            await asyncio.sleep(5)
            continue
        try:
            await _watch(dev)
        except OSError as e:
            print(f"device disconnected ({e}) — retrying in 3s", flush=True)
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(main())
