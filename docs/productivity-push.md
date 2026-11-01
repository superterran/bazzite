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

The TV fullscreen viewer/Steam shortcut is a separate pending step. This service
only makes the encrypted virtual desktop ready; it does not launch a viewer,
move windows, resize displays, restart Steam/Sunshine, or end running games.
Do not test lock/re-unlock while a user has unsaved encrypted desktop work.

Deployment: desktop.d/productivity-push.sh installs public source and enables
only the isolated approval service when the encrypted notification credential
already exists. It does not restart running services or replace existing Serve
mappings. Credential bootstrap must pass notification JSON to systemd-creds
through stdin, never a plaintext file or command argument.

Rollback: stop/disable productivity-push.service and remove only its Tailscale
Serve443 mapping if still pointing at18742. Leave the encrypted broker, RDP3392,
Steam, Sunshine, home data and existing recovery password untouched.
