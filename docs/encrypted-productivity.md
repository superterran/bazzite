# Encrypted virtual GNOME desktop

User-confirmed working from Jump on2026-10-31, including client-sized display.

## Connection and lifecycle

RDP100.119.114.55 port3392, username desktop-secure. Full strong password is
saved in Closet vault, item **Desktop Encrypted GNOME**. Save credentials in
Jump if desired. The old eight-character credential does not authorize this
endpoint. No passphrase is recorded in repository, arguments or logs.

The 64GiB sparse LUKS2 image is /var/lib/productivity-volume/desktop-secure.luks,
with ext4 mounted at /var/home/desktop-secure only after authentication.
AES-XTS512bit key, Argon2id256MiB/approximately1second. Root-only LUKS header
backup is desktop-secure.header beside the image. No volume-unlock key file or
automatic unlock is configured. TLS identity keys are distinct from volume keys.

Correct RDP login -> xrdp gateway PAM -> authenticated local TLS broker -> full
LUKS passphrase verification -> mount -> background PAM session -> independent
user manager/GNOME/VNC -> RDP display. Reconnecting checks the full password even
when already unlocked. Wrong password differing only after character8 was
rejected. Internal VNC still uses its protocol's eight-character credential;
the external full-password gate is mandatory and its target is fixed.

Disconnect keeps apps and the unlocked home running. **Lock encrypted desktop**
in GNOME's applications closes the session, stops its user manager, unmounts and
closes LUKS. This user-owned action was tested. No lingering/boot-autostart for
this account; the broker and gateway start at boot while the home stays locked.
An authenticated background PAM session holds the user manager while unlocked.
An actual whole-host cold boot has not been tested for the encrypted endpoint.

This does not protect an unlocked desktop from host administrators. The original
unencrypted desktop-remote account3391 was retained as rollback, including its
original data. Existing customizations copied into the encrypted account; old
plaintext copies have not been erased. Do not claim all pre-existing data is
now encrypted. Moonlight/Gamescope and Mini Fluid were not reconfigured.

## Source and deployment

- bin/initialize-productivity-volume.py: one-time initialization/data copy, input
  supplied privately on stdin. Refuses overwrite and refuses migration again
  once /etc/productivity-secure.json exists. --resume is only for interrupted
  initial provisioning and verifies the saved passphrase before continuing.
- bin/productivity-secret-runtime.py and productivity-1password.cjs: authorized
  Closet1Password runtime lookup; secret exists only in memory/anonymous stdin.
  Node child stdin is a socket, so JSON changes to op use a real anonymous pipe.
- desktop.d/secure-productivity.sh: idempotent deployment after initialization.
- config/secure-productivity/: gateway image/PAM/config and lock launcher.
- config/systemd/productivity-{volume-broker,secure-xrdp,secure-session@}.service.

The gateway container has all capabilities dropped, no-new-privileges and SELinux
isolation retained. Its client certificate authenticates it to the root broker
on127.0.0.1:35921. Both sides validate TLS certificates with a private CA. No
volume key is in these TLS files. Native Unix socket accepts unlock only from
root and lock only from root/the desktop owner via SO_PEERCRED; unauthorized UID
and TLS client without a certificate were rejected in tests. These keys and
public metadata live under /var/lib/productivity-secure-bridge and
/etc/productivity-secure.json, not the repo. Certificate renewal is required
before expiration (gateway outer certificate365days, local leaves825days).

Backend VNC5914 is blocked by firewall in current external zones; adapter5915
binds only loopback. The broker waits for the adapter's real RFB greeting before
allowing xrdp to connect, eliminating a cold-session startup race. The older unencrypted3391 and5901 listeners were subsequently retired;
the original desktop-remote home remains on disk for rollback.

## Verification

End-to-end FreeRDP over TLS from closed LUKS state unlocked the home, started
GNOME and confirmed2360x1640 applied. Checks also passed for wrong full password
while open and closed, lock closure, file absence while locked, persistence after
remote unlock, and service restart retaining locked state. User then confirmed
**Encrypted GNOME opens and fits** and later **desktop-secure works** in Jump.
Native browser/Moonlight tests were not repeated as part of encryption testing.

User later reported slow rendering. GNOME was using NVIDIA GBM/EGL, not software
rendering, and the client requested4608x1944 with megabytes of queued RDP output.
Enabled missing bulk_compression=true and explicit tcp_nodelay=true in the
secure gateway's mounted config without restarting it, and disabled GNOME
animations only for desktop-secure. User reconnected and explicitly reported it
felt much faster, then chose to keep resolution/settings as-is. Original
productivity bridge template also includes compression for future deployment.
No H.264 hardware video encoding is provided by this legacy VNC-to-RDP path.
Audio remains disabled; clipboard is limited by xrdp's VNC backend.

## Default desktop and authentication

The encrypted desktop is the main productivity setup. Existing background and
app customizations are preserved. Native 1Password SSH agent is the default for
terminals and SSH; CLI app integration was enabled and an approved vault-list
request succeeded. The app is enabled to start in future unlocked sessions;
that fresh-session startup still needs verification. No private SSH keys were
copied. Legacy3391/3389/5901 listeners are retired, with old home data retained.
Moonlight now exposes only Steam Big Picture and preserves its Game Mode no-op
behavior. Jump remains the encrypted desktop client on3392.
