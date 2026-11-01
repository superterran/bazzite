# Hardware Monitor

Native GTK3, read-only sensor viewer installed as a non-Steam application.

Run `desktop.d/hardware-monitor.sh` while Steam is running to install or repair
the shortcut. The installer follows the existing `steam_client.py` CEF API and
preserves the shortcut ID on subsequent runs. Prior shortcut metadata is saved
under `~/.local/state/hardware-monitor/`. The generated app ID and game ID are
recorded in `~/.config/hardware-monitor.json`.

Launch **Hardware Monitor** in Steam's non-Steam library, or use the desktop
application of that name. Escape or Close exits. It does not require sudo,
create a network listener, control fans, write sensor registers, or install a
background service. The launcher clears Steam's preload/input-module settings
following the existing native 1Password viewer convention, and assigns the
window's `STEAM_GAME` property when launched by Steam.

Temperatures come from named sysfs hwmon sensors. The radiator/pump labels use
the verified 2026-10-25 mapping: NCT6799 fan2 and fan7 are the two
radiator fans; fan6 is the AIO pump. See docs/noctua-cooling.md. Confirm cabling before
relying on those labels following hardware changes. DIMM and NVMe numbering
denotes sensor enumeration, not a guaranteed physical slot. Unmapped AUX inputs
are omitted; unavailable values are shown explicitly.

NVIDIA temperature, fan percentage, and power come from `nvidia-smi`. The fan
percentage is driver telemetry, not a physical tachometer measurement. This
RTX 4070 has historically reported zero while the user observed spinning fans;
the UI states that limitation and does not label zero as a failure.

The gauge colors are visual guides, not a substitute for each component's
specified limits. This app deliberately does not display hardcoded benchmark
passes, memory timings, case-cover state, or overclock status as live facts.

For a headless readback: `python3 bin/hardware-monitor.py --snapshot`.

Source files: `bin/hardware-monitor.py`, `bin/launch-hardware-monitor.sh`,
`bin/setup-hardware-monitor.py`, `desktop.d/hardware-monitor.sh`, and
`config/hardware-monitor.desktop.in`.

## Kraken telemetry (2026-10-26)
Hardware Monitor reads CoolerControl /status on loopback using a dedicated read-only API token, avoiding concurrent USB polling. Adds coolant temperature, USB pumpRPM, commanded fan duty, CPU power/load. FanRPM0 is labeled feedback unavailable; no invented per-fan values. Readings older than10seconds are rejected. Token at ~/.config/hardware-monitor/coolercontrol-token mode600, excluded from repo. First-use CoolerControl admin password changed from vendor default to random; stored locally ~/.config/hardware-monitor/coolercontrol-admin mode600, never in repository or chat. Desktop GUI may require signing in again. Existing Steam shortcut retained and relaunched; fresh process verified; snapshot returned coolant32.4,pump2908,fan70%,RPM0. Visual TV confirmation pending.
