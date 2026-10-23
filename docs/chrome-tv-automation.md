# One Chrome browser for Steam, Moonlight and Playwright

The persistent browser runs on a private virtual desktop. Steam and Moonlight view that same desktop. There is one Chrome process, one profile, one set of website sessions and one 1Password extension lock state.

## Use it

- **Steam / TV:** launch **Chrome - TV & Automation**, app ID `3789767895`. This opens a fullscreen viewer. Closing or stopping this entry closes the viewer and its audio playback, while Chrome and automation continue in the background.
- **Moonlight / private view:** refresh hosts and choose **Chrome Browser**, then **Chrome - TV & Automation**. This host streams the private desktop independently of the TV. If discovery fails, add `desktop.local:48989` (current LAN address `10.0.0.226:48989`). A client may need to pair with the new host; this is separate from browser/account sign-in.
- **Automation:** use Codex MCP **playwright-tv**, or `uv run --script ~/repos/bazzite/bin/chrome-tv-playwright.py status`. The endpoint remains `http://127.0.0.1:9223` and attaches to this same Chrome instance.
- **1Password:** unlock once through either viewer; both show the same extension. Its idle auto-lock is disabled at the user's request. It locks when Chrome restarts, including after PC reboot. No password-based unattended unlock is configured.

The original desktop Moonlight host still streams the TV/game display. Its Chrome tile opens the TV viewer and therefore changes what the TV shows. Use the separate **Chrome Browser** host for a private view without affecting the TV.

## Controls in the Steam viewer

| Control | Action |
| --- | --- |
| Right stick / DualSense touchpad | Pointer |
| R2 / L2 | Left / right mouse click |
| Touchpad press | Left click |
| R1 / L1 | Zoom in / out (Ctrl+= / Ctrl+-) |
| Right-stick press | Reset zoom (Ctrl+0) |
| D-pad / left stick | Arrow keys |
| Cross / Square / Circle / Triangle | Enter / Space / Escape / Tab |
| Options / Create | F6 (focus/address bar) / Backspace |

Steam + X opens Steam's keyboard. Moonlight's native mouse, keyboard and touch-as-mouse input goes to the private input seat. Private-host controller passthrough is disabled; use Moonlight's mouse/keyboard controls or controller mouse mode. The Steam viewer retains the controller-to-mouse layout above.

## Components

| Component | Location / purpose |
| --- | --- |
| Browser profile | `~/.var/app/com.google.Chrome/config/chrome-tv-automation` (unchanged) |
| Private Xorg display | `:20`, dummy driver, input seat `seat-browser`, authenticated local socket, no TCP X11 listener |
| Window manager | Openbox from Fedora RPMs extracted under `~/.local/opt/chrome-private` |
| Shared browser | `chrome-private-browser.service`, installed Chrome Flatpak on display :20 |
| Local viewer transport | Native Fedora x11vnc, localhost-only `127.0.0.1:5905` / `::1:5905` |
| Steam viewer | `bin/launch-chrome-tv.sh` launches `bin/chrome-private-viewer.py` using GTK-VNC |
| Private audio | Separate PulseAudio server on `%t/chrome-private/pulse/native`, sink `browser` |
| Private Moonlight host | `chrome-private-sunshine.service`, X11 capture, NVIDIA NVENC, port family 48989 |
| Native TV Moonlight host | Existing `app-dev.lizardbyte.app.Sunshine.service`, unchanged KMS capture with display-session wrapper |
| Moonlight config | `~/.config/sunshine-browser/`, private state/certificates, distinct host UUID |
| Artwork | `assets/chrome-tv-cover.png`, applied to Steam portrait and Moonlight app entries |

The private host requires encrypted streaming and advertises SDR encoding. Its port family is TCP48984,48989,49010 and UDP48998–49000, enabled through `chrome-browser` firewalld service on the default zone. The private web UI at localhost48990 permits only local administration. CDP and VNC remain loopback-only.

Sunshine's native XDG_SEAT support appends `(seat-browser)` to its virtual input device names. The scoped rule `config/udev/72-chrome-private-seat.rules` assigns only those devices to the private seat and gives the local user access. Private Xorg consumes them; Gamescope's seat0 input remains separate. This uses native libinput routing, not a custom mouse-event bridge.

Audio uses a separate server so remote sessions do not redirect the TV's default audio sink. Chrome's private Flatpak launch disables the default host PulseAudio socket and grants access to the private runtime socket. The Steam viewer forwards the private monitor to the TV only while the viewer is open; its child audio processes terminate with the viewer, including abrupt termination.

## Services and deployment

`desktop.d/chrome-private.sh` installs the scoped input rule, firewall service, config and six enabled user units:

- `chrome-private-display.service`
- `chrome-private-wm.service`
- `chrome-private-audio.service`
- `chrome-private-browser.service`
- `chrome-private-vnc.service`
- `chrome-private-sunshine.service`

The display unit upholds dependent units after recovery. The browser restarts automatically when it exits. Its ExecStop sends CDP `Browser.close`: terminating only the Flatpak launcher can leave the browser alive in its separate scope, so explicit shutdown is necessary to avoid duplicate-window restart loops. The existing cached uv/Playwright environment supports this offline stop command.

System Xorg, libinput and GTK-VNC were already available. Openbox, its small missing libraries, x11vnc and the dummy driver are extracted from Fedora RPMs under the user's home, so no OS layering/reboot was needed. Dependency RPMs are cached under `~/.cache/chrome-private-rpms`. Homebrew PulseAudio was already available. A Homebrew x11vnc trial lacked X11 support; the deployment uses the native Fedora binary instead.

Reapply with `bash ~/repos/bazzite/desktop.d/chrome-private.sh`. `--stage` installs without starting services. The first move requires closing the previous direct-on-TV Chrome instance, because one profile cannot run concurrently on two display servers. The existing profile is reused; a local private backup was placed under `~/.local/state/chrome-private-migration/` during the move. Credentials and browser profiles are not committed to the repo.

`desktop.d/chrome-tv.sh` maintains the existing Steam shortcut ID, input layout, cover and Codex MCP registration. `bin/focus-chrome-tv.py` opens or focuses the viewer. If Steam keeps another game's priority above it, the helper updates Gamescope's app-priority control. It does not stop the other game or launch another browser.

## Automation and 1Password

```bash
uv run --script ~/repos/bazzite/bin/chrome-tv-playwright.py status
uv run --script ~/repos/bazzite/bin/chrome-tv-playwright.py open https://example.com
```

For custom requested automation, attach with `playwright.chromium.connect_over_cdp('http://127.0.0.1:9223')` and reuse `browser.contexts[0]`. Do not create a second persistent context using this profile. Do not close the browser/default context at the end of ordinary tasks. The script's `stop` command is reserved for intentional browser shutdown/service management.

Codex's additional user-level **playwright-tv** MCP server uses `~/.local/bin/playwright-tv-mcp.sh`. The existing **playwright** server remains available for isolated headless Chromium tasks. TV MCP output is private and automatic trace recording is off. MCP initialize, list-tools and live tab listing succeeded with 28 tools. New Codex sessions load the registered server.

The browser extension is signed in, but **1Password CLI access is separate and remains unauthenticated**. Native app integration is configured in the extension but disconnected; Chrome is Flatpak, which 1Password documents as incompatible with desktop native messaging on Linux. Browser overlay autofill worked in the user's live sign-in test. No vault passwords, Secret Keys, session tokens or unattended-unlock credentials were stored in launch scripts.

References: [Playwright CDP attachment](https://playwright.dev/python/docs/api/class-browsertype#browser-type-connect-over-cdp), [Chrome debugging custom-profile requirement](https://developer.chrome.com/blog/remote-debugging-port), [1Password Linux browser integration](https://support.1password.com/connect-1password-browser-app/), [Sunshine configuration](https://docs.lizardbyte.dev/projects/sunshine/latest/md_docs_2configuration.html).

## Validation on 2026-10-23

- Exactly one main Chrome process, display :20, original profile and CDP9223.
- Both Moonlight servers respond with distinct host UUIDs/names; private host advertises port48989 on LAN via Avahi. Encoders initialized and firewall rules are active.
- Synthetic private-seat mouse input moved only :20's pointer; both Gamescope pointers remained unchanged.
- A click sent to the fullscreen Steam viewer reached a disposable test button in the same tab read by Playwright.
- Silent Web Audio test created a Chrome stream only on the private PulseAudio server; the TV's default sink remained unchanged.
- Closing the viewer terminated its audio children and left the browser service/CDP running.
- Browser/display stop-start and recovery completed with one browser process; restart counters remained zero afterward. Shell syntax and Python compile checks passed.
- Test tabs and duplicate empty windows created during migration were removed; user pages were retained. No 1Password unlock was automated.

Full Moonlight client playback/input and controller usability still await the user's test. Initial 1Password unlock is needed after this migration. The Ally remains offline and this desktop backend was not deployed there.
