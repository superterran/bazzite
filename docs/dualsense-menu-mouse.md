# DualSense mouse in Game Mode

The user service `dualsense-menu-mouse.service` makes the touchpad work without holding PS:

- Slide one finger: move the pointer.
- Tap one finger: left-click.
- Tap two fingers: right-click.
- Physically press the left/right half: left/right mouse button; hold and move to drag.

It runs only while Steam's menu/configuration app has focus, pauses for games, and leaves PS-held chords to Steam. It does not grab the gamepad or alter its HID reports. A real mouse remains usable.

On this machine, the evdev touchpad device existed but emitted no touch events during physical testing. The gamepad channel worked. Reading the same controller's raw HID reports supplied actual touch contacts, confirmed by the user after the bridge switched to that path. The program supports Bluetooth (0x31, 78-byte) and USB (0x01, 64-byte) input formats, matching Linux `drivers/hid/hid-playstation.c`'s `dualsense_input_report`. Existing Steam udev rules already grant raw HID access; no new broad raw-device permissions were added.

Output uses XTest on Steam's Xwayland display. Both button 1 and button 3 were received by Steam as trusted mouse events in a controlled test. The earlier uinput attempt did not produce clicks in that test and was removed. Gesture and report-decoding regression tests are in `tests/test_dualsense_menu_mouse.py`.

Install: `desktop.d/dualsense-menu-mouse.sh`.
Logs: `journalctl --user -u dualsense-menu-mouse`.
Disable: `systemctl --user disable --now dualsense-menu-mouse.service`.
The scoped udev rule only grants the active local seat access to the DualSense touchpad event node for the fallback path.
