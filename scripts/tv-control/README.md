# TV Control via 8BitDo Orb Button

Press the orb (Home) button on the 8BitDo Ultimate Wireless Controller to:

1. Pause whatever is playing on the Living Room Apple TV (best-effort — preserves position)
2. Switch the Living Room TCL Google TV to bazzite's HDMI input (HDMI 3 by default)

Also exposes individual scripts that Apple Shortcuts / `ssh` / cron can drive directly (TV power, Apple TV sleep/wake/pause, arbitrary HDMI input).

## Components

| File | Role |
|---|---|
| `tv.py` | Android TV Remote v2 — pair, power on/off, send keycodes (TIF input keys are stubbed by TCL — use `tv-switch.sh` to switch inputs) |
| `tv-switch.sh` | ADB + TIF passthrough intent — the only working path for HDMI input switching on this TCL |
| `atv.py` | pyatv Companion — pair, sleep, wake, pause, play-pause |
| `orb-listener.py` | evdev watcher on `BTN_MODE` → runs `atv.py pause` then `tv-switch.sh <input>` |
| `diag.py` | Inspection helper for AndroidTVRemote state |

Hardware identifiers:

| | |
|---|---|
| TCL Google TV (Living Room) | `10.0.0.7` |
| Apple TV (Living Room) | `10.0.0.237` / `3E:75:AA:71:AA:56` |
| 8BitDo dongle | USB `2dc8:3106` |
| 8BitDo evdev path | `/dev/input/by-id/usb-8BitDo_Ultimate_Wireless_Controller_912c5bd817e4-event-joystick` |

## First-time setup

```bash
# Pair Android TV (PIN appears on the TV)
./tv.py pair

# Pair Apple TV (PIN appears on the Apple TV)
./atv.py pair

# Enable ADB Network Debugging on the TCL:
#   Settings → System → About → Build (tap 7×) → Developer Options → USB/Network debugging

# Deploy unit + udev rule + enable listener
cd ~/repos/bazzite
just deploy-services
./desktop.d/tv-control.sh
```

`just setup` (which iterates `common.d/` + `desktop.d/`) will also pick up `desktop.d/tv-control.sh`.

## HDMI input map

Captured from `dumpsys tv_input` on 2026-05-31. Hardware IDs persist across TV reboots.

| Slug | TIF inputId tail |
|---|---|
| `hdmi1` | `HW1413744128` |
| `hdmi2` | `HW1413744384` |
| `hdmi3` | `HW1413744640` (bazzite PC) |
| `hdmi4` | `HW1413745664` |

Override the orb-listener's target via service env: `TV_PC_INPUT=hdmi2 systemctl --user restart tv-orb-listener.service`.

## Wake-from-sleep / wake-from-off

When bazzite is suspended (s2idle/S3) or powered off (S5), the userspace listener is gone — the wake has to be triggered at the hardware/kernel level by the USB controller seeing dongle activity.

### Linux side (handled by `desktop.d/tv-control.sh`)

A udev rule (`config/udev/rules.d/90-8bitdo-wake.rules`) sets:

- `power/wakeup = enabled` on the dongle's USB device — tells the kernel to register it as a wake source
- `power/control = on` — disables autosuspend so the dongle stays powered and the wake event isn't lost

Verify after setup:

```bash
for d in /sys/bus/usb/devices/*; do
    [ "$(cat $d/idVendor 2>/dev/null)" = "2dc8" ] || continue
    echo "$d: $(cat $d/power/wakeup) $(cat $d/power/control)"
done
```

Expected: `enabled on`.

### BIOS side (manual, board-specific)

Linux can only arm the wake source — the platform firmware decides whether USB power and wake events are honored in low-power states.

Look for these in BIOS (names vary by vendor):

| Setting | Set to | Why |
|---|---|---|
| ErP Ready / Deep Sleep | **Disabled** | Otherwise PSU cuts standby power to USB in S4/S5 |
| Power On by USB / USB Wake from S5 | **Enabled** | Allows USB activity to wake from cold off |
| USB Wake from S3 / Resume by USB | **Enabled** | Allows USB activity to wake from suspend |
| Wake-on-LAN (PCIe Wake) | **Enabled** | Separate concern — see `desktop.d/wol.sh` |

With those set, an orb press should wake from suspend and from S5 cold-off. From G3 (PSU switch off, or wall power lost), nothing wakes.

This composes with Phase 3 of `Context/projects/bazzite-console-mode-roadmap` (suspend-on-idle): the orb becomes the "console power button" — press it and the TV switches to the PC while bazzite wakes.

## Troubleshooting

```bash
journalctl --user -u tv-orb-listener.service -f    # live log
./tv-switch.sh hdmi3                               # bypass listener, test ADB+TIF path
./atv.py state                                     # confirm Apple TV reachable + paired
adb devices                                        # see if TV is attached
```

Common issues:

- **`atv pause: timeout`** — Apple TV asleep or off LAN. Best-effort; orb still switches input.
- **TIF intent runs but TV doesn't switch** — ADB Network Debugging got disabled on the TV (it auto-disables after factory reset / some updates). Re-enable.
- **Listener can't find 8BitDo** — controller asleep or dongle replugged. Listener retries every 3-5s. Press any button to wake the controller.
- **uv builds evdev wheel forever / fails** — script is pinned to Python `>=3.11,<3.14`; if uv is picking a newer Python, check the shebang's PEP-723 block.

## Updating the input map

If a TV factory reset rotates the HW IDs, recapture:

```bash
adb -s 10.0.0.7:5555 shell dumpsys tv_input | grep -A2 'TvPassThroughService'
```

Update the `INPUTS` array in `tv-switch.sh`.
