# GNOME productivity access over RDP

Configured 2026-10-31 alongside the existing Moonlight host. GNOME Remote
Desktop uses screen-share-mode extend: a connecting client supplies a virtual
monitor's initial resolution and can resize it using RDP Display Update. This
creates workspace beyond the physical TV rather than stretching the TV image.

## Connect

- Home LAN: 10.0.0.226:3389
- Tailscale: 100.119.114.55:3389
- RDP username: me
- Password: generated and stored in GNOME's login keyring. View it through
  Settings > System > Remote Desktop > Desktop Sharing. It is a separate RDP
  credential, not the operating-system login password.
- Certificate: ~/.local/share/gnome-remote-desktop/tls.crt. SHA256 fingerprint
  F2:89:D7:62:28:8B:EE:A6:63:3A:6E:A4:80:91:E8:A3:51:BF:E3:61:8A:18:C2:3B:8C:AC:DF:E5:DC:E5:19:69.

This is access to the existing, unlocked GNOME session, not a separate headless
login. If Game Mode is active, first select Desktop in Moonlight. Locking or
logging out of GNOME ends this kind of RDP connection. Keyring credentials must
be available to the daemon; unattended cold-boot/keyring behavior is untested.
No lock, login, or power policy was weakened by this configuration.

Use a client option that matches the remote display to the client size, with
native/Retina rendering as desired. Do not substitute image stretching for a
new remote resolution. Test iPad landscape/portrait, window resizing, keyboard
shortcuts, pointer input, clipboard and ultrawide3440x1440 before calling the
productivity setup end-to-end verified. This extended screen may initially have
no existing application windows; application placement and primary-display
behavior should also be checked with the actual client.

## Source and validation

Run `bash desktop.d/gnome-rdp.sh` as the desktop user with existing sudo access.
The helper creates a private TLS key/certificate if absent, stores a generated
password directly in the GNOME keyring through grdctl, sets extend mode and
input control, fixes port3389 without negotiation, and enables the user service.
Repeat setup was verified to preserve credentials and certificate. No password
is passed in argv, printed, or saved in a plaintext file.

This grdctl build fails when both username/password are supplied through two
piped interactive reads; the helper passes only the public username as an
argument and sends the password through stdin. Never work around it by putting
the password in a command argument.

TCP3389 is allowed from the home IPv4 LAN and existing Tailscale zone; explicit
non-LAN IPv4 and physical IPv6 drops prevent a broad workstation-zone exception
from exposing this service. No router changes were made. Existing direct-AP
and unrelated firewall rules are preserved.

Verified: daemon active, port3389 listening, CUDA initialization successful,
RDP negotiation and TLS1.3 certificate fingerprint matched from Closet over
both LAN and Tailscale. Client authentication, rendered virtual monitor, live
resizing and perceived latency still await an actual client test.

To disable: `grdctl rdp disable` and stop the user gnome-remote-desktop.service.
To mirror instead of extending: set the RDP screen-share-mode to mirror-primary.
The source certificate setup-info.json contains public metadata only.

## Client and host compatibility findings

Jump Desktop has iPad and Mac clients and handles RDP, VNC and its own Fluid
protocol. US App Store prices checked2026-10-31: iPad$14.99, Mac$34.99, separate
purchases. Its Mac host, Jump Desktop Connect, supports Fluid virtual displays.
One virtual display is included in current plans; multiple virtual displays
require Enterprise. Linux Connect is alpha; its virtual displays require a
session it starts when no one is signed in. No Jump software has been installed
or purchased during this setup. The user has not yet chosen Fluid on Mini
versus requiring RDP on both hosts.

Third-party Mac RDP servers exist, including experimental NativeMacRDP, but
none has been installed or validated on the Mini. Existing Mini SSH, Apple
Screen Sharing, FileVault and KVM routes remain intact.

Jump cannot consume Sunshine/Moonlight's protocol. Fluid includes gaming and
controller features on supported versions, but the Linux host is alpha;
Gamescope/Bazzite compatibility, latency and controller behavior are untested.
Moonlight remains the verified gaming route.

GL.iNet documents a Comet VNC server through kvmd-vnc. Jump/iPad codec/auth
compatibility is unverified, and the actual kvm-pro is offline during this
check. JetKVM's native VNC request remains open; its running controller has no
reachable5900/5901 listener. No KVM configuration or input was changed. A
supported VNC bridge for JetKVM was not established.

References:

- [GNOME configuration](https://github.com/GNOME/gnome-remote-desktop/blob/main/docs/configuration.md)
- [Jump iPad client](https://apps.apple.com/us/app/jump-desktop-rdp-vnc-fluid/id364876095)
- [Jump Mac client](https://apps.apple.com/us/app/jump-desktop-rdp-vnc-fluid/id524141863)
- [Jump virtual displays](https://docs.jumpdesktop.com/viewer/virtual-displays/)
- [Jump Linux alpha](https://jumpdesktop.com/remote-desktop-linux.html)
- [Jump game controllers](https://docs.jumpdesktop.com/viewer/session/game-controllers/)
- [GL.iNet Comet VNC discussion](https://forum.gl-inet.com/t/enable-vnc-server-on-comet-kvm/59347)
- [JetKVM VNC request](https://github.com/jetkvm/kvm/issues/117)


## Jump compatibility and VNC alternative — 2026-10-31

Jump RDP failed first at NTLM negotiation. An isolated WinPR experiment passed
that stage, but actual Jump attempts then failed GNOME's mandatory graphics
pipeline capability check. RDP through Jump is not working.

GNOME's packaged VNC backend is now enabled in `extend` mode on port5901.
Connect in Jump using VNC to100.119.114.55:5901, username blank, with the first
eight characters of the existing GNOME RDP password. The credential remains in
GNOME keyring and is never printed or passed in arguments. Classic VNC has an
eight-byte password limit. Transport encryption is supplied by Tailscale;
firewall rules drop5901 on physical LAN, hotspot and Docker zones and allow the
tailnet zone. The pre-existing loopback-only5900 listener is preserved.

Deploy with `bash desktop.d/gnome-vnc.sh`. Setup uses `/usr/bin/gsettings`:
Linuxbrew's gsettings writes a separate backend and did not configure the
native daemon. Fixed the RDP setup to use the native command as well.

Verified VNC password challenge/authentication, ServerInit and an actual raw
framebuffer pixel response over the desktop's tailnet address. Native setting
reads `extend`. Client-side picture, input and resize remain pending user
validation; a preliminary protocol resize probe did not establish resizing.
Requires an unlocked GNOME session, as with the RDP assistance service.

The user confirmed the Mini's Jump Fluid connection and scaled resolution work;
Mini VNC had already been user-confirmed. No changes to the Mini for this test.
