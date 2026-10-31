# Mac mini SSH and KVM access

Verified 2026-10-31. Run `ssh mac-mini` for the Mini's `superterran` account.
The managed routes pin the Mini's existing ED25519 host key, choose one explicit
local identity without an SSH agent, disable password prompting, and send
keepalives every 15 seconds. Administration keys support shell commands and
SFTP; the existing messaging keys retain their forced commands and restrictions.

## Verified routes

| Origin | Default Mini route | Validation |
| --- | --- | --- |
| desktop | Tailscale 100.90.54.59 | Three fresh SSH logins and SFTP upload/download checksum comparison |
| Closet host | Tailscale 100.90.54.59 | Same |
| Closet codex-rc | Tailscale 100.90.54.59 | Same |
| Closet claude-rc | Tailscale 100.90.54.59 | Same |
| Closet OpenClaw container | Tailscale 100.90.54.59 | Same |
| macbook-air | LAN mac-mini.local | Same; Air has no Tailscale installation/route |
| ally | Pending | Offline during repair; no client key deployed or test claimed |

`ssh mac-mini-lan` explicitly selects LAN/mDNS. `ssh mac-mini-tailnet` explicitly
selects Tailscale. The tailnet DNS name and 100.90.54.59 also select that private
route with the correct user/key. The Air needs Tailscale installation/enrollment
before its direct off-LAN route can work. No public SSH listener or router port
forward was added.

Source restrictions match the actual transport: desktop LAN 10.0.0.226 and
Tailscale 100.119.114.55; Closet LAN 10.0.0.75 and Tailscale 100.101.167.38;
Air LAN 10.0.0.188. LAN routes use IPv4 because these key allowlists contain IPv4
addresses. A future DHCP address change for the Air requires updating its key's
source list, or replacing that dependency with an enrolled tailnet address.

## Configuration and identities

`bin/fleet-ssh-client.py` manages `~/.ssh/fleet-access/*.conf` and
`~/.ssh/fleet-known-hosts`. A single Include is inserted before existing Host
stanzas, preserving top-level integrations such as OrbStack. Original config
and managed file revisions are backed up with `.before-fleet-TIMESTAMP` names.
No private keys are stored in the repository or copied between machines.

| Origin | Mini identity |
| --- | --- |
| desktop, Air, claude-rc, OpenClaw | Each origin's own ~/.ssh/mac_mini_admin_ed25519 |
| Closet host | Existing ~/.ssh/id_ed25519 |
| codex-rc | Existing ~/.ssh/mac_mini_ed25519 |

Examples from an origin where its private key already exists:

```bash
python3 bin/fleet-ssh-client.py mac-mini --identity '~/.ssh/mac_mini_admin_ed25519'
# Air, until enrolled in Tailscale:
python3 bin/fleet-ssh-client.py mac-mini --identity '~/.ssh/mac_mini_admin_ed25519' --transport lan
```

`bin/fleet-ssh-authorize.py` runs as the Mini user and reads a JSON array from
stdin, each item containing a public `key` and a nonempty `sources` list. It
backs up and atomically replaces authorized_keys, validates ED25519 keys and
source addresses, and refuses to broaden existing forced-command service keys.
Existing administration source lists are extended without changing other options.

The Claude messaging MCP uses `mac-mini-imessage` with its original restricted
identity and LAN source. Its original server command is retained. The alias
comes from `config/mac-mini-imessage-ssh.conf`; only that MCP's host argument was
changed in the container's persistent `.claude.json`. An initialize handshake
returned the expected Mac mini iMessage server. No messages were read or sent.
The OpenClaw service key and forced RPC command remain unchanged.

The Claude container has no Python interpreter. Apply the client helper through
Closet's existing Python to its persistent home at
`/mnt/storage/apps/claude-rc/home` as uid/gid568. IdentityFile entries retain
`~` so paths resolve correctly inside the container. Other containers' files
also live in their existing persistent homes; no recreation was needed.

## JetKVM recovery

`ssh kvm-mini` and compatibility alias `ssh jetkvm` now select
100.102.2.16 with a pinned host key on desktop, Closet host and codex-rc.
All three passed fresh authenticated SSH checks. The private web endpoint
http://kvm-mini.tail3758dd.ts.net responded HTTP200. These are transport checks;
no keyboard input, reboot, browser-session takeover or FileVault unlock was
performed during this repair.

Desktop and codex-rc retain their separate existing `jetkvm_ed25519` identities.
Closet host has its own `kvm_mini_admin_ed25519`. JetKVM's Dropbear rejects the
OpenSSH `from=` key option, so the new Closet key instead invokes the persistent
`/userdata/fleet-ssh-closet.sh` gate, sourced from
`config/kvm-mini-closet-ssh.sh`. It checks the actual SSH_CONNECTION source
against Closet's LAN/tailnet addresses before executing a command or shell;
agent/X11/port forwarding are disabled for that recovery key. Existing keys
remain untouched. The persistent authorized_keys lives under
`/userdata/dropbear/.ssh/` through the existing /root/.ssh symlink.

Mini FileVault remains enabled. A cold boot still requires local/KVM unlock
before the normal user session and user-owned Tailscale application return.
The existing Mini no-sleep policy and caffeinate LaunchAgent were verified;
no power or FileVault policy was changed.

## Rollback and pending validation

Restore the relevant per-origin `.ssh/config.before-fleet-*` backup, and the
Mini's `authorized_keys.before-fleet-*` backup if removing newly granted access.
The original working Closet/Codex keys were preserved. Restore the backed-up
Claude `.claude.json` together with its matching SSH alias if rolling back MCP
routing. KVM authorized_keys has its own `.before-fleet` backup; leave existing
keys in place when removing the new Closet recovery key.

Eight helper tests pass, including config precedence/idempotence, pinned routes,
real authorized_keys newlines, preservation of service restrictions, and the
JetKVM source gate. Live validation covered the six available origins. Reboot,
container recreation, off-LAN Air access and Ally access remain untested.
