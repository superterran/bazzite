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
