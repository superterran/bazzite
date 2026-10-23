# Chrome on the TV and through Moonlight

Steam entry: **Chrome - TV & Automation**, desktop app ID `3789767895`.
The matching Moonlight tile launches the same Steam entry, on the same Game Mode screen.

This is visible Chrome, with an ordinary persistent profile. Sign in directly using the TV or Moonlight. Playwright attaches to that browser's existing default context over CDP, so it uses those same login sessions. There is no second headless browser, exported cookie file, copied desktop profile or browser-extension dependency. Account authentication is still performed by the user; no accounts were signed in during installation.

- Launcher: `~/.local/bin/launch-chrome-tv.sh`, sourced from `bin/launch-chrome-tv.sh`.
- Profile: `~/.var/app/com.google.Chrome/config/chrome-tv-automation`, private to this machine.
- Automation endpoint: `http://127.0.0.1:9223`, verified bound to loopback only. Remote agents can run Playwright over SSH or use a local SSH tunnel; do not expose this port to the LAN or Internet.
- No forced Proton compatibility on this Steam entry: it launches the installed Chrome Flatpak.
- Input: right stick or DualSense touchpad pointer; R2 left click, L2 right click; touchpad press left click; R1 zoom in (Ctrl+=), L1 zoom out (Ctrl+-), right-stick press reset zoom (Ctrl+0); D-pad/left stick arrow keys; Cross Enter, Square Space, Circle Escape, Triangle Tab, Options F6 (cycle focus/address bar), Create Backspace. Steam + X opens Steam's keyboard.
- The separate menu mouse bridge pauses here; Steam Input handles the browser like a game.

Run `bash ~/repos/bazzite/desktop.d/chrome-tv.sh` to reapply the launcher, Steam entry, controller layout and Sunshine app tile. Reuses the shortcut ID and backs up prior configuration under `~/.local/state/chrome-tv-setup/<timestamp>/`. Does not restart Sunshine automatically, so it does not interrupt existing streams during setup. Local app ID and endpoint are recorded in `~/.config/chrome-tv.json`.

## Playwright

Codex now has an additional user-level MCP server named **playwright-tv**. Its wrapper `~/.local/bin/playwright-tv-mcp.sh` attaches to this same CDP endpoint and fails with a clear instruction if Chrome is closed. Select this server for tasks involving the TV browser's signed-in accounts. The existing `playwright` server remains available for separate headless Chromium tasks. The TV wrapper does not enable automatic trace recording. Reapply registration through `desktop.d/chrome-tv.sh`; new Codex sessions load the configured server. It was tested independently using the MCP initialize/list-tools/browser-tabs protocol: 28 tools were exposed and live tab listing succeeded.

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

### Browser sign-in test

Subsequent live test on 2026-10-23 opened Reddit and Gmail in new tabs. Reddit presented a human-verification challenge, left for the user. Gmail was already signed in. The user requested following an Airbnb review email through Playwright; the 1Password extension supplied the saved matching login through its page overlay, and SMS verification completed with user participation. The review form was completed and Airbnb confirmed submission. This demonstrates browser-assisted authentication; no passwords were read or exported.

1Password's browser extension and CLI are separate integrations. `op` is installed (2.39.0), but `op whoami` reported no active CLI session, and the native 1Password app was not running at the time of the audit. Browser-extension sign-in alone does not establish unattended CLI vault access. For CLI access, open and unlock native 1Password, enable system authentication in Security and “Integrate with 1Password CLI” in Developer, then authenticate an `op` command. See [1Password's integration instructions](https://www.1password.dev/cli/app-integration). Do not write session tokens or vault credentials into MCP configuration. The existing browser overlay already works for interactive login assistance.

### Browser extension lock preference

At the user's request on 2026-10-23, turned off “Automatically lock 1Password” in this TV Chrome profile, replacing its eight-hour idle timeout. Reloaded extension settings and verified persistence; preset now displays Convenient. The extension reports no active desktop-app integration (General's integration toggle is enabled but shows a connection problem). Therefore it still locks when Chrome exits, including PC reboot. This is not unattended unlocking across restart. No account password or Secret Key was stored in a launcher. Other autofill confirmation and phishing-prevention settings were unchanged.

### Moonlight launcher focus — 2026-10-23

The Chrome tile now invokes bin/focus-chrome-tv.py. It launches the existing Steam shortcut only if its CDP endpoint is absent, then uses SteamUIStore.SetRunningApp and NavigateToRunningApp to select the already-running browser. Tested with Chrome running behind another game: Gamescope focus changed to Chrome app3789767895 without restarting Chrome or terminating the game. This is still display mirroring. Sunshine logs showed the client resuming a Desktop session; end that existing session and launch the Chrome tile to run its launcher. A private browser view independent of the TV would require a separate virtual desktop/capture session, which has not been configured.
