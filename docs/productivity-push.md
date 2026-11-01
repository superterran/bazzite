# Phone approval for encrypted GNOME

Request a notification without changing the TV:

```
python3 ~/repos/bazzite/bin/request-secure-desktop.py
```

The request goes to the user's Pushover email alias through existing Gmail SMTP.
No Pushover API application token is needed. Notification delivery was accepted
by SMTP and the user confirmed receipt on iPhone. HTTPS health check passed
locally and independently from Closet with certificate validation. Actual
iPhone AutoFill/unlock interaction still needs user confirmation.
The alias and SMTP credentials are stored in a host-encrypted systemd credential
at /etc/credstore.encrypted/productivity-push, decrypted only into service runtime.
No desktop encryption passphrase is saved by this service.

The notification links to https://desktop.tail3758dd.ts.net/#<random-request>.
Tailscale Serve provides a publicly trusted HTTPS certificate, but access is
restricted to the tailnet; Funnel is not used. Phone needs Tailscale connected.
On first use choose 1Password's Desktop Encrypted GNOME item manually; add this
website to that item's login URLs if desired. Keep biometric authentication for
AutoFill enabled on the phone. This is password AutoFill plus confirmation,
not a custom biometric-only key-release mechanism.

The link expires after five minutes. Opening it claims an approval but cannot
unlock the volume. An HttpOnly/Secure/SameSite cookie plus a per-request CSRF
value and matching Origin are required for submission. Three password attempts
are allowed. Successful unlock invalidates the request. Request creation is
limited to root and main gaming UID1000 through a kernel-credential checked Unix
socket, with a one-minute notification cooldown; creating another request
revokes the prior one. Requests disappear after service restart. No URLs,
passwords, request bodies or tokens are logged by the app. The fragment is
removed from browser history when the page opens, before submitting its token.
Passwords necessarily exist temporarily in Python process memory; core dumps
are disabled. No full password in URLs, notifications, command arguments or disk.

The root-owned service has no capabilities and a restricted filesystem. It
submits the password over the existing kernel-credential checked broker socket;
only that existing broker manages the volume and encrypted GNOME session.
It cannot lock sessions or switch display modes through any HTTP endpoint.
SMTP delivery carries an expiring link through Gmail/Pushover, not the volume key.

The TV fullscreen viewer/Steam shortcut is now installed as described below.
The approval service itself only makes the encrypted virtual desktop ready;
the Steam launcher owns the viewer. Neither service restarts Steam/Sunshine or
ends running games.
Do not test lock/re-unlock while a user has unsaved encrypted desktop work.

Deployment: desktop.d/productivity-push.sh installs public source and enables
only the isolated approval service when the encrypted notification credential
already exists. It does not restart running services or replace existing Serve
mappings. Credential bootstrap must pass notification JSON to systemd-creds
through stdin, never a plaintext file or command argument.

Rollback: stop/disable productivity-push.service and remove only its Tailscale
Serve443 mapping if still pointing at18742. Leave the encrypted broker, RDP3392,
Steam, Sunshine, home data and existing recovery password untouched.

Safari form correction: initial iPhone form submission returned Invalid origin.
The original no-referrer policy can cause Origin:null on form POST. Changed to
same-origin, retaining strict Origin/Host checks, CSRF/cookie validation and no
referrers to other sites. Added regression coverage; six tests pass. Refreshed
notification after restarting only the isolated approval service. iPhone retry
confirmation pending.

## TV shortcut

Steam now has **Secure Desktop**, appid3716438448, gameid15961981591790551040.
Launch it to request phone approval and show a waiting dialog. Use the latest
Pushover link and 1Password, then the native FreeRDP viewer opens fullscreen on
the Gamescope game display, with dynamic resolution and the same desktop-secure
GNOME session. This can displace a Jump connection because the backend has a
single active viewer; it does not create another desktop or close remote apps.
Controller layout uses the established desktop mouse/navigation bindings:
right stick/touchpad mouse, triggers for clicks, D-pad arrows, A Enter, B Escape,
X Tab, Y Space. Steam+X opens Steam's on-screen keyboard. Guide/Steam menu lets
you exit the shortcut and return to Steam. Actual controller feel needs user
validation; regular keyboard/mouse also work. Remote audio remains disabled.

A separate random viewer ticket is returned only over the main-user/root
peer-checked Unix socket, never in the notification URL. After valid phone
password and broker success, the service holds that password in memory for up
to30seconds, for one retrieval by the requesting local viewer. The viewer feeds
it to FreeRDP through anonymous stdin; no command argument/file/clipboard is
used. Expired handoffs are reaped every second. This deliberately authorizes the
main gaming UID to receive that approved session credential in memory. Someone
already controlling that account could inspect its viewer process; this does
not isolate a running desktop from a compromised host. No unattended volume
unlock key is saved. The existing full password remains the recovery route.

FreeRDP pins the gateway's SHA256 certificate via the public viewer-cert.sha256
file. Refresh the pin after deliberately renewing the gateway TLS certificate
using desktop.d/secure-desktop-tv.sh. That script installs FreeRDP if missing and
registers/updates only the Secure Desktop shortcut. Physical GNOME remains a
recovery option; its main account home still contains Steam/gaming state. It
was not erased or converted into an encrypted home.

Closing the viewer keeps encrypted GNOME running/unlocked. Use **Lock encrypted
desktop** inside GNOME to end apps and close the volume. Do not equate exiting
the Steam shortcut with locking encryption.

### End-to-end verification — 2026-11-01

User approved the Pushover request and explicitly confirmed TV shows the
encrypted desktop. Native FreeRDP window is fullscreen3840x2160 on Gamescope's
game display; xrdp logged successful resize to3840x2160. Encrypted GNOME/home
stayed the existing session. Eight approval tests cover expiry, origin/CSRF,
three attempts, link claim and one-use viewer credential handoff. Controller
layout was saved through Steam; physical controller interactions and exit flow
still need user validation. No password in process command arguments.

## Accelerated TV path — 2026-11-01

The initial TV viewer used xrdp/VNC and felt slow. Native GNOME RDP is now
enabled inside the same encrypted account on3393, using a separate TLS identity
and the existing full encryption password stored by GRD inside the encrypted
home. Its RDP credential cache required one GRD-only restart; GNOME/apps/home
were preserved. Native RDP listens only while that user session is unlocked.
Firewall drop rules restrict3393 in external zones; the TV uses127.0.0.1. The
existing Tailscale3392 gateway remains available for Jump and phone-based cold
unlock. GNOME's CUDA initialized, client negotiated AVC420 and NVIDIA reported
an active encoder session. User explicitly reported noticeably/significantly
smoother TV behavior. No claim that Jump3392 became hardware encoded.

The TV launcher defaults to native NLA/GFX/H.264 with a pinned native certificate.
SECURE_DESKTOP_BRIDGE=1 selects the old compatible bridge and its original pin.
Phone approval remains mandatory for either viewer. Native RDP config and
credentials persist inside the encrypted home; after boot the existing broker
starts GRD only after successful full-key unlock. Provision/refresh native RDP
with BAZZITE_CONFIGURE_NATIVE_RDP=1 desktop.d/secure-native-rdp.sh while unlocked;
it briefly disconnects remote viewers but does not stop the compositor/apps.
Changing the volume/recovery password requires updating native credentials too.
Native password is never exposed through argv/logs by setup.

Animations were re-enabled after acceleration. The current4K virtual monitor
was temporarily scaled2x using Mutter's display API. TV launch defaults now
request1920x1080 and smart-size fullscreen on the4K TV, giving roughly2x apparent
UI size with one-quarter as many remote pixels. Dynamic client resizing is
disabled for this TV preset; Jump retains its adaptive bridge. RDP sound playback
is requested through the viewer's PulseAudio backend, targeting the main HDMI
default output; encrypted desktop apps initially use their virtual audio sink.
User confirmed the new size and sound both work. Mutter reported1920x1080
at1x inside the session, while the fullscreen TV window remained3840x2160;
RDP audio was connected and unmuted on the main HDMI sink. GNOME animations
are enabled. This is a TV preset, not a global font-size change.

Linux Fluid investigation: vendor10.16.83RPM was signature-verified against
pinned vendor keyB9B6833B44081D9973D2E9749DAE447061724867, extracted rather than
installed globally. An isolated user-local trial was attempted inside the
encrypted account. Vendor bundle only contains Qt xcb/offscreen GUI plugins,
not Wayland; explicit xcb UI started when given existing Xwayland display/auth.
Trial was stopped, is not enabled at boot, has no account link, and no Fluid
connection/encoding was verified. No global Jump service/PAM/login changes.
Personal cloud account enrollment and attachment to this background GNOME
session remain unresolved. Cloudless Fluid is documented as Teams Enterprise,
so it is not assumed available on the user's existing purchase. Staged public
trial files remain inside the encrypted home, not in an active startup path.

Final state: native GPU-encoded TV viewer is user-confirmed significantly
smoother, and its1080p scaled size plus HDMI sound are user-confirmed working.
The same GNOME compositor PID13717 persisted throughout capture/audio changes.
Linux Fluid trial is stopped with no auto-start/account link; network Jump3392
still uses compatibility VNC-to-RDP and has not received the hardware encoding
improvement. A supported native-RDP client could use GNOME's accelerated path
if a separately scoped network endpoint is deliberately exposed; current3393
remains local-only by firewall. Do not claim the Jump network path is fixed.

Audio/animation follow-up: user reports smooth video/minimize animation, but
Activities looks different and lip sync seems off (direction unclear). User
considers Activities difference minor; no Shell overrides/extensions applied.
GNOME remote-access handles can inhibit some animations independently of
enable-animations=true. Live FreeRDP Pulse properties showed tlength44100bytes
at44100Hz stereo16bit (~250ms) and8192frame node latency (~186ms). Saved
/sound:sys:pulse,latency:50 plus PULSE_LATENCY_MSEC=50 for the next viewer launch.
Current connection was not interrupted. New buffering and lip sync are not yet
verified by the user; do not claim synchronization is fixed.

## Bottom-edge Activities and session closure

Bottom Overview19 (bottom-overview@fthx), reviewed GNOME50-compatible archive
version_tag77092, installed only inside the encrypted account. Saved enabled
extension UUID while preserving other extensions. Current GNOME did not support
loading/reloading this newly installed extension over its extension D-Bus API;
it will load on the next fresh compositor session. Setup source pins SHA256 and
checks metadata/archive paths. Behavior through the remote pointer still needs
user validation: upstream uses a pressure barrier rather than a simple dwell,
and suppresses activation over fullscreen applications.

User explicitly authorized ending the encrypted session after returning to Steam.
Root broker lock accepted; verified mapping desktop-secure-home absent and home
unmounted, while Game Mode stayed active. Apps closed as part of ending that
session. Do not unlock again solely to test the extension without a new request.
