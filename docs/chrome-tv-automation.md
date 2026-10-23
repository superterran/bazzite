# One Chrome browser for Steam, Moonlight and Playwright

The persistent browser runs on a private virtual desktop. Steam and Moonlight view that same desktop. There is one Chrome process, one profile, one set of website sessions and one 1Password extension lock state.

## Use it

- **Steam / TV:** launch **Chrome - TV & Automation**, app ID `3789767895`. This opens a fullscreen viewer. Closing or stopping this entry closes the viewer and its audio playback, while Chrome and automation continue in the background.
- **Moonlight / private view:** refresh hosts and choose **Chrome Browser**, then **Chrome - TV & Automation**. This host streams the private desktop independently of the TV. If discovery fails, add `desktop.local:48989` (current LAN address `10.0.0.226:48989`). A client may need to pair with the new host; this is separate from browser/account sign-in.
- **Automation:** use Codex MCP **playwright-tv**, or `uv run --script ~/repos/bazzite/bin/chrome-tv-playwright.py status`. The endpoint remains `http://127.0.0.1:9223` and attaches to this same Chrome instance.
- **1Password:** unlock once through either viewer; both show the same extension. Its idle auto-lock is disabled at the user's request. It locks when Chrome restarts, including after PC reboot. No password-based unattended unlock is configured.

The original desktop Moonlight host streams the TV/game display and offers Desktop and Steam only. The misleading duplicate Chrome tile was removed. Use the separate **Chrome Browser** host for private Chrome without affecting the TV; the Steam library still includes its fullscreen Chrome viewer.

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

### Moonlight Steam and Chrome separation

The main host’s Steam Big Picture tile runs `bin/focus-steam-tv.py`: it navigates to Game Mode home and explicitly selects Steam in Gamescope, even if the TV Chrome viewer was previously in front. It does not close Big Picture when the stream ends. The separate **Chrome Browser** host captures only the private browser display; choosing Steam on the main host does not move or restart that browser. The main host’s Chrome tile intentionally opens the Steam viewer on the TV.

### Remote clients over Tailscale

Tailscale is installed and enabled at boot. Enrollment requires the user's Tailscale account sign-in; it is currently pending, so internet access is not yet verified. Run `sudo tailscale up --hostname=bazzite-desktop --accept-routes=false --accept-dns=false` to obtain the current login URL. No router port forwards are needed for this design. UPnP is explicitly disabled on both streaming hosts, encrypted streams required, and management UIs restricted to the local PC.

`desktop.d/moonlight-remote.sh` installs a dedicated firewalld zone for tailscale0 allowing both streaming port families, excluding management ports. Tailscale also applies its own packet filtering and account access policy; the zone is not a substitute for tailnet policy review. Keep Chrome CDP9223 and VNC5905 localhost-only.

On phone, tablet, Mac and upstairs computer: install Moonlight and Tailscale, sign into the same personal tailnet, then manually add the desktop Tailscale IPv4 address twice: default port for Steam/TV and `:48989` for private Chrome. Pair each host if prompted. Verify custom-port support on each client. First test LAN playback/input on both hosts, then cellular on phone with Wi-Fi off, then Mac/upstairs computer. Check `tailscale status` and `tailscale ping CLIENT` for direct versus relay path if performance is poor. Client setup, account enrollment and internet streaming remain untested.

The private browser works without a physical monitor. The TV/Game Mode capture still depends on Gamescope maintaining a physical or emulated display; a monitor-unplugged test is required before claiming the entire workstation is fully headless. Remote access requires the PC awake; Bluetooth wake is not configured.

Post-network-change Playwright verification: attached existing CDP endpoint, created disposable local-content tab, clicked a button, verified DOM change and closed only that test tab. Shared browser remained running.

Enrollment completed via the existing Google browser session on 2026-10-23: desktop Tailscale IPv4 **100.119.114.55**. Both Sunshine serverinfo endpoints respond on that address: add **100.119.114.55** for Steam/TV and **100.119.114.55:48989** for private Chrome. Other clients still require Tailscale sign-in to the same personal account and Moonlight pairing. This local endpoint check does not verify cellular streaming.

### iPad stutter audit, 2026-10-23

Host-side review completed while user was away; no live iPad stream was available. Do not mark end-to-end smoothness fixed.

- Main host: native Sunshine 2026.516.143833, KMS capture pinned to NVIDIA renderD129, NVENC, two-pass disabled. Existing FEC30 retained pending a controlled comparison; FEC adds bandwidth and is not a universal stutter fix. No automatic Gamescope session restart hooks are configured in current app entries. Historical bin/sunshine-stream-mode.sh exists but is not called.
- TV/Game Mode: 2560x1440 at119.95Hz. Private browser:1920x1080 exactly60Hz. A120Hz stream of the60Hz private desktop cannot create120 unique source frames. Do not change the user's TV refresh globally just to guess at a pacing issue.
- Ethernet:1Gbps full duplex, no kernel RX/TX errors/drops and no NIC CRC/missed/timeout counters. A20-packet idle gateway probe had0% loss,2.637/3.604/5.344ms min/avg/max. This does not test loaded jitter, Wi-Fi client loss or the extender backhaul. The Ethernet link rate does not prove an all-wired path to the router.
- Host at inspection:GPU45C, no recent kernel Xid found, approximately49GiB memory available, no active swap-in/out during two sampled one-second intervals. Both Sunshine services active with restart counters0. Current low load does not rule out game-time GPU saturation or thermal throttling.
- NVENC smoke test:600 synthetic1080p60 frames encoded in0.76seconds (13x realtime). Separate5-second private X11 capture+NVENC completed300frames at60fps. FFmpeg emitted startup duplicate timestamp warnings; this was a capacity smoke test, not a Sunshine pacing measurement or client latency measurement.
- Direct AP `desk-stream` /SSID **Bazzite** was already active but had no stations and used20MHz width. Updated to5GHz channel149,80MHz (verified actual width), explicit powersave disabled and autoconnect yes, preserving stored password. Setup script now modifies existing profile rather than deleting credentials, uses correct channel text and enables both streaming hosts in hotspot firewall. Main LAN internet route remainseno1. The driver survey returns zero counters, so channel occupancy was not measurable.
- Direct targets: **10.42.0.1** for Steam/TV, **10.42.0.1:48989** for private Chrome; both serverinfo endpoints verified locally. Use these direct addresses for the hotspot comparison, rather than routing that comparison through Tailscale.

Later iPad test baseline (client settings not applied remotely):1920x1080,60fps,15Mbps,SDR/HDR off, HEVC if supported; H.264 as a controlled codec comparison. Enable Moonlight on-screen statistics in its settings. Test an animated scene or scrolling page for at least2minutes on normal5GHz Wi-Fi, then Bazzite direct Wi-Fi at close range with exactly the same settings. Record incoming/renderedfps, network drops/jitter, decode time and frame queue if exposed by that client. Static browser pages may correctly deliver fewer frames. Do not treat static-content lowfps as dropped frames.

If network drops/jitter rise, lower bitrate first and compare the direct link. If incomingfps is stable but renderedfps is not, inspect client decoding/display pacing; match the requested60fps and client display where controllable. Raise only one setting at a time after a clean baseline. Test cellular/Tailscale separately and check direct versus relay path. Real end-to-end tests, iPad settings and user confirmation remain pending.

References: https://github.com/moonlight-stream/moonlight-docs/wiki/Frequently-Asked-Questions and https://github.com/moonlight-stream/moonlight-docs/wiki/Troubleshooting ; AP channel-width semantics: https://networkmanager.dev/docs/api/latest/settings-802-11-wireless.html .

### Upstairs Apple TV network investigation, 2026-10-23

AirPlay/Companion discovery found two actual Apple TVs (AppleTV14,1): Living Room10.0.0.237 and Office TV10.0.0.11. Office TV is the candidate upstairs client; room identity still needs user confirmation. HomePods/Roku advertisements excluded. No TV was awakened, paired, rebooted or reconfigured. No router settings were changed.

Measured evidence is saved in `docs/diagnostics/moonlight-network-2026-10-23.json`:

- Office TV from desktop,160small pings:0%loss,median6.14ms,p95 58.2ms,max82.4ms.22responses exceeded16.67ms,18exceeded33.33ms.160pings with1400bytepayload:0%loss,median7.56ms,p95 67.7ms,max88ms.
- Concurrent gateway1400byteprobe:0%loss,median3.69ms,p95 7.01ms,max22.8ms. A preceding120packet gateway test caught a48.8msmaximum.
- Controlled desktop-to-closet UDP:26042datagrams of1200bytes paced at25Mbps for10seconds. All received,0%loss. Temporary receiver bound only closetLAN10.0.0.75:52019 and exited immediately; no files installed or persistent server/firewall changes. Receiver arrival-jitter EWMA was0.288ms at end, not a worst-case jitter bound. Sender pacing uses Python/Linux scheduling, so this is a useful approximate stream-rate probe rather than calibrated network instrumentation.
- During that25Mbpsreference transfer:Office TVp95 70.6ms/max177ms, gatewayp95 8.45ms/max176ms, LivingRoomp95 5.02ms/max175ms; no pingloss. Shared single-sample spikes do not prove their cause is the router; host scheduling and shared paths remain possible.
- Independent closet-to-OfficeTV60packetprobe:0%loss,min3.502/avg14.943/max123.071ms,mdev24.911ms. Spikes therefore also appear from another host, but AppleTVidle Wi-Fi/pingprioritization may contribute.
- Desktop and closet Ethernet negotiate1Gbpsfull duplex. DesktopEEE is already disabled and NIC error/drop counters remainzero. Xfinity router responds at10.0.0.1. Physical mesh/pod/switch topology and OfficeTVWi-Fiband/RSSI are not available from these observations. Do not confuse a localEthernet1Gbpslink with a fully wired backhaul.

Assessment: intermittent latency is a concrete candidate for choppy playback; sampled loss and25Mbpsreference delivery were good. These short probes cannot establish long-term reliability, AppleTVavailable throughput, video decode/pacing or sustained4Kcapacity. Idleping spikes are not proof of actual media packet jitter. The direct Bazzite hotspot only helps clients connected within its radio range; it is not automatically a better upstairs path.

Next controlled test when home:confirmOfficeTVidentity; launch Moonlight on it overLANusingdesktop10.0.0.226,1080p60/15Mbps/SDR baseline; match AppleTVoutput refresh to60Hz (or a compatible exact rate) for comparison, with originalsettings recorded. Enable available client statistics and compare active-stream ping/framestats. Check clientRSSI/band/APassociation and whetherdesktopEthernet actually terminates at an xFipod. If stillchoppy, temporarily wire AppleTV or test it near the primaryAP to isolate Wi-Fi/backhaul; compare normalnetwork withdirectAPonlyifrangeallows. Increase bitrate/resolution onlyafterbaselineisclean. TailscaleisforoutsideaccessandisnotrequiredforthehomeLANtest. No playbackimprovementclaimeduntiluserverifies.

### Bazzite DX session-switch repair, 2026-10-23

After a reboot the machine entered GNOME and the Logo Menu Return to Game Mode action failed. Journal showed `Execution of steamosctl failed: Command not found`. Native steamos-session-select delegates to os-session-select, which also calls missing steamosctl. This is the upstream Bazzite DX missing-steamos-manager issue https://github.com/ublue-os/bazzite-dx/issues/208 . It was separate from the Sunshine capture/focus configuration.

Fallback `bin/switch-bazzite-session.sh game|desktop [--prepare-only]` validates installed session files, uses AccountsService to select our own user's session, then requests normal GNOME logout (or terminates only local Gamescope seat when switching out). Requires existing passwordless sudo for narrow AccountsService calls. No GDM daemon restart or OS layering. `desktop.d/session-switch.sh` installs the helper, updates existing Desktop Mode launcher and provides a user-local Logo Menu copy changing only Game Mode command plus a desktop launcher override. Native extension is unchanged. User extension loads on the next GNOME login. Once native steamosctl returns, remove the local Logo Menu copy to use the upstream extension again; setup skips creating fallback when native command exists.

Actual GNOME logout and automatic login into gamescope-session-steam succeeded: gamescope-session-plus@steam.service active, Steam process uses-gamepadui, Gamescope focusedappid769. Private Chrome browser and private Sunshine stayedactive. The separate Desktop Mode launcher was updated but the reverse switch was not exercised after returning to Game Mode, to leave the requested session running. Original GNOME and default GDM configuration were not rewritten; only our account's savedsession changed.

### Removed duplicate Moonlight Chrome tile

2026-10-23: user correctly observed standalone Chrome launch changing the TV. Main-host logs showed a client stream while private-host logs showed no connections. Removed the legacy Chrome TV launcher from main Sunshine apps and from setup-chrome-tv.py deployment behavior. Main Moonlight host now exposes Desktop/Steam; separate Chrome Browser host at LAN10.0.0.226:48989 or Tailscale100.119.114.55:48989 exposes independent Chrome. Steam library Chrome viewer remains available. Refresh Moonlight app list and add the private host manually if absent.

### Private host empty app list correction

2026-10-23 user paired private host but saw noapps. NativeSunshine processparserrequires top-level`env`; templateomitteditand startup logged`No such node (env)`, leavingruntimeapplistemptydespitewebAPIreadingthefile. Added`env:{}`tolive/templateapps. Also fixedboot-timeuinputaccess:privateservicehadstartedbeforephysicalseatloginandloggedmouse/keyboardpermissiondenied;scopedpersistentuinputownershiptome(0600),without grantingrawphysicalinputaccess. RestartedprivateSunshine;app-parserandinput-permissionerrorsgone,encodersready. Pairingretained. Clientmustrefreshapplist;clientplaybackawaitstest.
