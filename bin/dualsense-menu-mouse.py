#!/usr/bin/python3
"""Use the DualSense touchpad as a real mouse while Steam's Game Mode UI has focus."""
import asyncio
import ctypes
import math
import os
from pathlib import Path
import time
from types import SimpleNamespace

from evdev import InputDevice, ecodes as E, list_devices

TOUCHPAD = 'DualSense Wireless Controller Touchpad'
GAMEPAD = 'DualSense Wireless Controller'
MOUSE_APPS = {int(value) for value in os.environ.get('DUALSENSE_MOUSE_APPS', '769,413080,413090,443510,588460').split(',')}


def parse_report(report):
    # Layout: Linux drivers/hid/hid-playstation.c, dualsense_input_report.
    # BT has a 2-byte header; USB has a 1-byte header. Read only, never write HID.
    if len(report) == 78 and report[0] == 0x31:
        base = 2
    elif len(report) == 64 and report[0] == 1:
        base = 1
    else:
        return None
    points = {}
    for slot in range(2):
        p = report[base + 32 + slot * 4:base + 36 + slot * 4]
        if not p[0] & 0x80:
            x, y = p[1] | ((p[2] & 15) << 8), (p[2] >> 4) | (p[3] << 4)
            if 0 <= x < 1920 and 0 <= y < 1080:
                points[slot] = (p[0] & 127, x, y)
    return points, bool(report[base + 9] & 2), bool(report[base + 9] & 1)


def find_raw():
    for path in Path('/sys/class/hidraw').glob('hidraw*'):
        try:
            info = (path / 'device/uevent').read_text()
            if 'HID_NAME=DualSense Wireless Controller\n' in info:
                return os.open('/dev/' + path.name, os.O_RDONLY | os.O_NONBLOCK)
        except OSError:
            continue
    return None


async def read_report(fd):
    loop = asyncio.get_running_loop()
    while True:
        try:
            report = os.read(fd, 128)
            if not report:
                raise OSError('Controller disconnected')
            return report
        except BlockingIOError:
            ready = loop.create_future()
            def readable():
                if not ready.done():
                    ready.set_result(None)
            loop.add_reader(fd, readable)
            try:
                await ready
            finally:
                loop.remove_reader(fd)


class MenuMouse:
    """Send trusted X11 mouse input to Steam's Xwayland display."""
    def __init__(self):
        self.x = ctypes.CDLL('libX11.so.6')
        self.test = ctypes.CDLL('libXtst.so.6')
        self.x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x.XOpenDisplay.restype = ctypes.c_void_p
        self.x.XFlush.argtypes = [ctypes.c_void_p]
        self.x.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.test.XTestFakeRelativeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
        self.test.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]
        self.display = self.x.XOpenDisplay(b':0')
        if not self.display:
            raise OSError('Steam Xwayland display is not available')
        self.dx = self.dy = 0

    def write(self, kind, code, value):
        if kind == E.EV_REL:
            if code == E.REL_X:
                self.dx += value
            elif code == E.REL_Y:
                self.dy += value
        elif kind == E.EV_KEY:
            self.test.XTestFakeButtonEvent(self.display, 3 if code == E.BTN_RIGHT else 1, value, 0)

    def syn(self):
        if self.dx or self.dy:
            self.test.XTestFakeRelativeMotionEvent(self.display, self.dx, self.dy, 0)
            self.dx = self.dy = 0
        self.x.XFlush(self.display)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.x.XCloseDisplay(self.display)


class Gesture:
    """Translate complete touch frames; keep physical click and tap gestures distinct."""
    def __init__(self, mouse):
        self.mouse = mouse
        self.slots = {}
        self.slot = 0
        self.active = False
        self.armed = False
        self.held = None
        self.reset()

    def reset(self):
        self.start = None
        self.origins = {}
        self.previous = None
        self.max_fingers = 0
        self.moved = False
        self.clicked = False
        self.frac_x = self.frac_y = 0.0

    def enable(self, active):
        if active == self.active:
            return
        self.release()
        self.active = active
        self.armed = False
        self.reset()

    def release(self):
        if self.held is not None:
            self.mouse.write(E.EV_KEY, self.held, 0)
            self.mouse.syn()
            self.held = None

    def event(self, event, now):
        if event.type == E.EV_ABS:
            if event.code == E.ABS_MT_SLOT:
                self.slot = event.value
            elif event.code == E.ABS_MT_TRACKING_ID:
                if event.value < 0:
                    self.slots.pop(self.slot, None)
                else:
                    self.slots[self.slot] = [None, None]
                    self.origins.pop(self.slot, None)
            elif event.code in (E.ABS_MT_POSITION_X, E.ABS_MT_POSITION_Y) and self.slot in self.slots:
                self.slots[self.slot][event.code == E.ABS_MT_POSITION_Y] = event.value
        elif event.type == E.EV_KEY and event.code == E.BTN_LEFT:
            if event.value == 0:
                self.release()
            elif event.value == 1 and self.active and self.armed:
                point = next((p for p in self.slots.values() if p[0] is not None), [0, 0])
                self.held = E.BTN_RIGHT if point[0] >= 960 else E.BTN_LEFT
                self.clicked = True
                self.mouse.write(E.EV_KEY, self.held, 1)
                self.mouse.syn()
        elif event.type == E.EV_SYN and event.code == E.SYN_REPORT:
            self.frame(now)
        elif event.type == E.EV_SYN and event.code == E.SYN_DROPPED:
            self.release()
            self.slots.clear()
            self.armed = False
            self.reset()

    def frame(self, now):
        points = {s: tuple(p) for s, p in self.slots.items() if None not in p}
        if not self.active:
            self.reset()
            return
        if not self.armed:
            if not self.slots:
                self.armed = True
            return
        if not points:
            if not self.slots and self.start is not None:
                if not self.clicked and not self.moved and now - self.start <= .28:
                    button = E.BTN_RIGHT if self.max_fingers >= 2 else E.BTN_LEFT
                    self.mouse.write(E.EV_KEY, button, 1)
                    self.mouse.syn()
                    self.mouse.write(E.EV_KEY, button, 0)
                    self.mouse.syn()
                self.reset()
            return
        if self.start is None:
            self.start = now
        self.max_fingers = max(self.max_fingers, len(points))
        for slot, point in points.items():
            origin = self.origins.setdefault(slot, point)
            if math.dist(origin, point) > 18:
                self.moved = True
        if len(points) == 1:
            slot, point = next(iter(points.items()))
            if self.previous is not None and self.previous[0] == slot:
                old = self.previous[1]
                dx, dy = point[0] - old[0], point[1] - old[1]
                if abs(dx) < 250 and abs(dy) < 250:
                    self.frac_x += dx * 1.25
                    self.frac_y += dy * 1.25
                    x, y = int(self.frac_x), int(self.frac_y)
                    self.frac_x -= x
                    self.frac_y -= y
                    if x or y:
                        self.mouse.write(E.EV_REL, E.REL_X, x)
                        self.mouse.write(E.EV_REL, E.REL_Y, y)
                        self.mouse.syn()
            self.previous = (slot, point)
        else:
            self.previous = None


async def steam_menu_focused():
    try:
        proc = await asyncio.create_subprocess_exec(
            '/usr/bin/xprop', '-root', 'GAMESCOPE_FOCUSED_APP',
            env={**os.environ, 'DISPLAY': ':0'},
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=1)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return False
        return proc.returncode == 0 and int(out.decode().rsplit('=', 1)[1].strip()) in MOUSE_APPS
    except (OSError, ValueError, IndexError):
        return False


def find_devices():
    pad = gamepad = None
    for path in list_devices():
        try:
            dev = InputDevice(path)
        except OSError:
            continue
        if dev.name == TOUCHPAD and pad is None:
            pad = dev
        elif dev.name == GAMEPAD and gamepad is None:
            gamepad = dev
        else:
            dev.close()
    return pad, gamepad


async def watch(pad, gamepad):
    with MenuMouse() as mouse:
        gesture = Gesture(mouse)
        print(f'Connected {pad.path}; tap=left, two-finger tap=right; press left/right half to click', flush=True)
        async def focus():
            previous = None
            while True:
                # The existing PS-held chord is left to Steam, avoiding double movement.
                guide = gamepad is not None and E.BTN_MODE in gamepad.active_keys()
                active = not guide and await steam_menu_focused()
                gesture.enable(active)
                if active and not gesture.slots and E.BTN_TOUCH not in pad.active_keys():
                    gesture.armed = True
                if active != previous:
                    print('Menu mouse active' if active else 'Menu mouse paused (game, PS chord, or no menu)', flush=True)
                    previous = active
                await asyncio.sleep(.15)
        focus_task = asyncio.create_task(focus())
        try:
            async for event in pad.async_read_loop():
                if focus_task.done():
                    focus_task.result()
                gesture.event(event, time.monotonic())
        finally:
            focus_task.cancel()
            await asyncio.gather(focus_task, return_exceptions=True)
            gesture.release()


async def watch_raw(fd):
    with MenuMouse() as mouse:
        gesture = Gesture(mouse)
        focused = False
        async def focus():
            nonlocal focused
            while True:
                focused = await steam_menu_focused()
                if not focused:
                    gesture.enable(False)
                await asyncio.sleep(.15)
        task = asyncio.create_task(focus())
        ids = {}
        clicked = False
        last_active = None
        seen_touch = False
        print('Reading DualSense raw touch reports (read-only); menu-only mouse ready', flush=True)
        try:
            while True:
                if task.done():
                    task.result()
                decoded = parse_report(await read_report(fd))
                if decoded is None:
                    continue
                points, click, guide = decoded
                if points and not seen_touch:
                    print('Confirmed live touchpad contact in raw controller reports', flush=True)
                    seen_touch = True
                gesture.enable(focused and not guide)
                if gesture.active != last_active:
                    print('Menu mouse active' if gesture.active else 'Menu mouse paused', flush=True)
                    last_active = gesture.active
                for slot, (tracking_id, x, y) in points.items():
                    if ids.get(slot) != tracking_id:
                        gesture.origins.pop(slot, None)
                    gesture.slots[slot] = [x, y]
                for slot in set(gesture.slots) - set(points):
                    del gesture.slots[slot]
                ids = {slot: p[0] for slot, p in points.items()}
                if not points and not click:
                    gesture.armed = True
                if click != clicked:
                    gesture.event(SimpleNamespace(type=E.EV_KEY, code=E.BTN_LEFT, value=int(click)), time.monotonic())
                    clicked = click
                gesture.frame(time.monotonic())
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            gesture.release()


async def main():
    while True:
        raw = find_raw()
        if raw is not None:
            try:
                await watch_raw(raw)
            except OSError as exc:
                print(f'Raw controller disconnected: {exc}', flush=True)
            finally:
                os.close(raw)
            await asyncio.sleep(3)
            continue
        pad, gamepad = find_devices()
        if pad is None:
            if gamepad:
                gamepad.close()
            await asyncio.sleep(3)
            continue
        try:
            await watch(pad, gamepad)
        except OSError as exc:
            print(f'Device/access changed: {exc}; reconnecting', flush=True)
        finally:
            pad.close()
            if gamepad:
                gamepad.close()
        await asyncio.sleep(3)


if __name__ == '__main__':
    asyncio.run(main())
