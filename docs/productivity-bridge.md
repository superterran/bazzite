# Independent GNOME productivity experiment

Configured 2026-10-31 without restarting or reconfiguring Sunshine or the main
GNOME session. The current direct Jump VNC fallback at5901 remains available.

## Connect

In Jump create an **RDP** connection, host `100.119.114.55`, separate port field
`3391`, username `desktop-remote`. Password is the first eight characters of the
existing GNOME RDP credential, as with the current VNC fallback. No password is
in this repository, shell arguments or logs. Enable matching the client display
resolution if offered. The endpoint has its own self-signed TLS certificate.
Tailscale must be connected.

This is a separate Linux account and desktop, so application preferences and
sign-ins do not automatically match the gaming account. It has no admin access
and its OS login password remains locked. Project sharing is not configured.

## Architecture

Jump RDP -> TLS1.2/1.3 xrdp on the tailnet address3391 -> loopback VNC adapter5903
-> anonymous-DH TLS1.2 GNOME headless VNC5902 -> headless GNOME Wayland compositor.

`desktop-remote` owns its own user bus, user manager, compositor and GNOME Remote
Desktop service. Only that account has lingering enabled by this setup. A
headless GNOME shell uses no physical seat/HDMI monitor. Each VNC connection
creates a virtual monitor; xrdp translates client geometry into SetDesktopSize.
The compositor survives disconnects. Idle blanking/automatic locking disabled
only for this remote account; external access still requires VNC authentication.

xrdp runs in a Debian container with host networking, all capabilities dropped,
no-new-privileges and fixed backend target. No xrdp packages layered onto the
immutable host and no gaming GPU passthrough. Container image built from Debian
stable repositories, xrdp0.10.1 package at initial setup; rebuild for updates.
System unit `productivity-xrdp.service` owns the container lifecycle.

GNOME headless VNC on this Fedora build enforces anonymous TLS even though the
assistance backend supports plain VNC. The small adapter negotiates that TLS
channel and forwards password challenge/response unchanged. It neither knows
nor stores a password. It accepts RFB3.3 (xrdp) and3.8. Both IPv4 and IPv6 loopback
listeners are required: xrdp selects ::1 even for its configured127.0.0.1 target.
External3391 uses a separate TLS certificate/key in `/var/lib/productivity-bridge`.

GNOME5902 binds all interfaces, but runtime and permanent firewall drops block
it in LAN, hotspot, Docker and tailnet zones. Adapter5903 binds only127.0.0.1/::1.
External3391 binds only100.119.114.55 and is allowed in the tailnet zone.
Headless credentials are stored by GNOME's protected credential backend; TPM is
unavailable so its built-in GKeyFile fallback is used in the remote account.
No user passwords or keys were copied between physical machines.

## Deployment

Run `bash desktop.d/productivity-bridge.sh` from the main user with its existing
GNOME credential available. It creates/configures only this experiment's
account, services, image/container, certificate and firewall rules. Service
sources for the independent account are in `config/productivity-bridge` and
installed into that account's user systemd directory. The adapter is installed
to `/usr/local/libexec`. Persistent environment.d settings supply its Wayland
display for account-local activated applications.

## Validation and limits

- Native VNC authentication and virtual resize acknowledgements passed at
  2360x1640 and3440x1440 through the loopback adapter.
- RDP negotiation/TLS1.3 passed from Closet over Tailscale.
- A real FreeRDP client in an isolated Xvfb test container authenticated through
  the complete bridge. xrdp logged client2360x1640, old1920x1080 and confirmed
  new2360x1640 GNOME layout. Test intentionally terminated after8seconds.
- Main Sunshine process180961 remained running; separate GNOME compositor346491
  has a different UID/user bus and no physical HDMI display. The main physical
  GNOME display layout was not changed by these tests.
- Actual Jump picture/input/automatic sizing/rotation remain pending user test.
  Simultaneous Moonlight gameplay, latency/load, app persistence and cold boot
  have not yet been validated. Do not call the experiment a production replacement.
- xrdp reports ISO-8859-1-only clipboard support through this VNC backend. Audio
  redirection is disabled. This is a productivity experiment, not a Moonlight
  gaming replacement. It uses a standalone headless shell rather than a GDM
  login; some session-manager/Polkit functions may be unavailable.

## Stop the experiment

Stop/disable the system `productivity-xrdp.service`. Under `desktop-remote`'s
user manager stop/disable `productivity-vnc-tls-adapter.service`,
`gnome-remote-desktop-headless.service` and `remote-productivity-shell.service`.
Disable lingering for `desktop-remote` if retiring the account. Preserve its
home/application data until reviewed. These actions do not require stopping
the main user's Sunshine/GNOME services or deleting the existing5901 fallback.


## Persistence follow-up

User confirmed Jump opens GNOME and fills the iPad screen. Server/system and
account services verified enabled, linger enabled; compositor remained alive
through several test disconnects. No cold-boot test performed. Headless backend
credential file is owned by desktop-remote with mode0600. Initial password is
seeded from the original RDP credential; subsequent setup preserves the saved
backend password exactly, even if the main RDP password changes. Before/after
credential comparison passed without logging its value. Jump's iPad Save
Credentials option must be enabled client-side; this session cannot control
the iPad UI. Saved documents survive reboot; open application processes do not.
