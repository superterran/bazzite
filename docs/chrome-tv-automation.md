# Chrome on the TV and through Moonlight

Steam entry: **Chrome - TV & Automation**, desktop app ID `3789767895`.
The matching Moonlight tile launches the same Steam entry, on the same Game Mode screen.

This is visible Chrome, with an ordinary persistent profile. Sign in directly using the TV or Moonlight. Playwright attaches to that browser's existing default context over CDP, so it uses those same login sessions. There is no second headless browser, exported cookie file, copied desktop profile or browser-extension dependency. Account authentication is still performed by the user; no accounts were signed in during installation.

- Launcher: `~/.local/bin/launch-chrome-tv.sh`, sourced from `bin/launch-chrome-tv.sh`.
- Profile: `~/.var/app/com.google.Chrome/config/chrome-tv-automation`, private to this machine.
- Automation endpoint: `http://127.0.0.1:9223`, verified bound to loopback only. Remote agents can run Playwright over SSH or use a local SSH tunnel; do not expose this port to the LAN or Internet.
- No forced Proton compatibility on this Steam entry: it launches the installed Chrome Flatpak.
- Input: right stick or DualSense touchpad pointer; RT/RB left click, LT/LB right click; right-stick/touchpad press left click; D-pad/left stick arrow keys; Cross Enter, Square Space, Circle Escape, Triangle Tab, Options F6 (cycle focus/address bar), Create Backspace. Steam + X opens Steam's keyboard.
- The separate menu mouse bridge pauses here; Steam Input handles the browser like a game.

Run `bash ~/repos/bazzite/desktop.d/chrome-tv.sh` to reapply the launcher, Steam entry, controller layout and Sunshine app tile. Reuses the shortcut ID and backs up prior configuration under `~/.local/state/chrome-tv-setup/<timestamp>/`. Does not restart Sunshine automatically, so it does not interrupt existing streams during setup. Local app ID and endpoint are recorded in `~/.config/chrome-tv.json`.

## Playwright

With Chrome open:

```bash
uv run --script ~/repos/bazzite/bin/chrome-tv-playwright.py status
uv run --script ~/repos/bazzite/bin/chrome-tv-playwright.py open https://example.com
```

The script declares its Playwright dependency, so no separate browser download is required. For custom authorized automation:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9223')
    context = browser.contexts[0]
    # Reuse an appropriate existing tab, or create one for the requested task.
    page = context.new_page()
    # Perform the requested actions. Do not close the browser/default context.
```

Stopping Playwright disconnects automation while Chrome remains open. Opening Chrome later reuses the on-disk profile. Only one Chrome instance may own that profile; attach to it rather than launching a concurrent headless process with the same directory. The default everyday desktop Chrome profile is unaffected.

References: [Playwright CDP attachment](https://playwright.dev/python/docs/api/class-browsertype#browser-type-connect-over-cdp), [Chrome's custom-profile requirement for remote debugging](https://developer.chrome.com/blog/remote-debugging-port).

## Sunshine startup fix

The active service is `app-dev.lizardbyte.app.Sunshine.service`, currently running native `/usr/bin/sunshine` despite its historical unit name. Its active config is `~/.config/sunshine/`; the old Flatpak config also receives the app tile for future migration. Native KMS/NVENC remains selected, with the RTX 4070 at `/dev/dri/renderD129`.

The service previously started without a Wayland display, before Game Mode was ready, and failed to initialize capture/encoders. `bin/launch-sunshine-session.sh` now waits for a Wayland session socket, sets DISPLAY and WAYLAND_DISPLAY, and starts the native binary. Installed through `desktop.d/sunshine-session.sh` and `config/systemd/user/app-dev.lizardbyte.app.Sunshine.service.d/session.conf`. Existing restart policy and pairings are retained.

Native KMS with `WAYLAND_DISPLAY=gamescope-0` initialized H.264, HEVC, AV1 and HDR encoding successfully in an isolated probe and after restarting the actual service. A wlr probe was rejected because this Gamescope session does not expose the required XDG_OUTPUT interface; no wlr configuration was applied. This supersedes older repo comments about a working Flatpak-only capture path.

## Validation and remaining checks

On 2026-10-23, Steam launched Chrome into Game Mode and Gamescope focused its app ID. Playwright connected to the visible browser, created a disposable test page, clicked its button, verified the result and removed the test tab. The browser stayed open after Playwright disconnected. CDP listener is loopback only. Sunshine now detects the NVIDIA encoders successfully.

TV/controller behavior, actual account login retention and a complete Moonlight client video/input session still require user confirmation. Encoder initialization is not proof of a complete remote stream. The Ally remains offline and this desktop browser setup was not deployed to it.
