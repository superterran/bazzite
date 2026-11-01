# Secure Desktop recovery

The Git repository recreates software/configuration. It is not a backup of your
personal encrypted home. The independent Closet archive protects that data.

## Current backup system

Encrypted deduplicated Restic history and the selective system baseline are documented in [incremental-desktop-recovery.md](incremental-desktop-recovery.md). Its repository password is a third field in the same1Password recovery record. The original tested age archive below remains a protected independent baseline. After the new restore test passes, productivity-incremental.timer replaces the nightly full-archive timer; the old archive tool remains available manually.

## What to keep

- Repository: https://github.com/superterran/bazzite (main). A Git bundle also
  travels inside each encrypted backup. Current package inventory and exact
  gateway OCI image are included, so the bridge is not dependent on future APT
  packages remaining identical.
- Closet: `/mnt/storage/backups/desktop-secure/desktop-secure-*.tar.zst.age` plus
  its receipt. The archive is encrypted before crossing SSH; no volume key or
  backup decryption key is stored with it. Keep a tested baseline and recent
  successful backups. Do not mistake `.partial` files for successful backups.
- 1Password, Closet vault, **Desktop Secure Recovery**: Backup decryption key
  (age), Encrypted home recovery password, and LUKS UUID. Existing **Desktop
  Encrypted GNOME** remains the normal login credential. Keep 1Password's
  Emergency Kit/account recovery available separately from this desktop.
- Printed recovery sheet: private 1Password item link and repository link only.
  Neither QR contains a password or grants access by itself. Losing 1Password
  access and its account recovery can still make the encrypted backup unusable.

## Existing machine still works

Use Steam's Secure Desktop shortcut and approve through Pushover/1Password, or
Jump RDP3392. TV uses local native RDP3393 with NVIDIA encoding,1080p scaled to4K
and HDMI sound. Exit viewer keeps apps/home open. Lock encrypted desktop ends
apps and locks the home. Do not reinstall merely because a viewer disconnects.

A fresh GNOME session loads the saved Bottom Overview extension. The native
1Password app/SSH agent, background, desktop preferences and customizations are
inside the encrypted home. Restoring the files may still require normal app
sign-in or macOS/1Password account recovery; no promise of bypassing app auth.

## Restore data to a separate location first

Use Linux with Python3, GNU tar, age, zstd, cryptsetup and Podman. Download the
repository over HTTPS or recover its saved Git bundle. Copy a completed archive
from Closet to local storage. It is safe to transport the encrypted archive.
Never paste either secret into a command argument, URL or a plaintext key file.

```
sudo python3 bin/restore-secure-desktop.py \
  --archive /path/to/desktop-secure-TIMESTAMP.tar.zst.age \
  --destination /mnt/secure-recovery
```

The tool prompts privately for the **age backup decryption key** from1Password.
It uses an anonymous memory descriptor, authenticates/decrypts the archive and
extracts only into the empty staging directory. It does not alter live accounts,
services or a production volume. A failed/incomplete extraction is not a
restorable staging copy. `recovery/manifest.json` records UUID, account UID/GID,
source commit, date and saved-file hashes. `recovery/luks.header` is the matching
header backup. Do not run luksFormat or the original initialization/migration
script on restored data.

Online snapshots can need ext4 journal recovery. On the disposable extracted copy only, first open it read-write and run `sudo e2fsck -p -E journal_only /dev/mapper/recovered-home`; close it, then reopen read-only and run `sudo e2fsck -fn /dev/mapper/recovered-home`. Stop if the final check reports errors. Never run repair against the live production mapper.

For manual read-only data recovery, use the recovered LUKS image and full
Encrypted home recovery password via cryptsetup's interactive prompt:

```
sudo cryptsetup open --readonly \
  /mnt/secure-recovery/var/lib/productivity-volume/desktop-secure.luks recovered-home
sudo mkdir -p /mnt/recovered-home
sudo mount -o ro,noload,nodev,nosuid,noexec /dev/mapper/recovered-home /mnt/recovered-home
# Copy needed files out. Do not start GNOME/1Password against this test copy.
sudo umount /mnt/recovered-home
sudo cryptsetup close recovered-home
```

## Fresh Bazzite installation on the desktop

Prefer the recorded Bazzite GNOME/NVIDIA image/package inventory, user `me`, and
matching physical hardware. Current setup uses GNOME50 and locked non-admin
account desktop-secure UID1002/GID1003. Different hardware requires review of GPU,
HDMI output, fan channels/cooling calibration, audio output and driver setup.
Do not blindly apply the motherboard/firmware configuration to another machine.

First stage/decrypt as above, then review a plan:

```
sudo python3 bin/install-restored-secure-desktop.py --staging /mnt/secure-recovery --plan
```

The installer validates volume size/UUID and saved UID/GID ownership. Applying
refuses to replace an existing secure desktop. On a genuinely fresh host:

```
sudo python3 bin/install-restored-secure-desktop.py --staging /mnt/secure-recovery --apply
```

This installs the existing encrypted image, locked account, gateway identity/
config, saved OCI image and public backup settings. It does not unlock the home,
overwrite the main user's home, enroll Tailscale, restore every old host service,
or enable an obsolete cooling daemon. **Never rerun
initialize-productivity-volume.py to restore an existing home.**

As `me`, install needed host packages through existing setup: GNOME Remote
Desktop/headless services, native1Password/CLI, cryptsetup, Podman, Homebrew
FreeRDP/age/zstd and GUI dependencies. Inspect common.d/1password.sh and package
inventory first; rpm-ostree layering may require reboot. Do not install the old
unencrypted desktop test endpoints or experimental Linux Fluid globally.

Restore selected main-user Steam userdata/controller/art/config and Sunshine
pairings from staging/home/me after backing up fresh files. Preserve user UID1000
and owner/modes. Staged SSH files contain private keys: restore only deliberately
with correct0600/0700 permissions. Host SSH keys are included in future backups;
reusing them is appropriate only for this same machine with the old instance
retired. Old network identities must not run simultaneously on two machines.

Join Tailscale normally and inspect its current IPv4/DNS name. Update the gateway
port address in `/var/lib/productivity-secure-bridge/xrdp.ini` and public
`/etc/productivity-secure.json` if it differs from100.119.114.55. Review firewall
zone membership:3392 tailnet-only, VNC5914 and native3393 blocked externally.
Run the encrypted gateway deployment script after inspecting its address:

```
bash desktop.d/secure-productivity.sh
```

Then perform one normal Jump login on3392 using the full1Password password.
This unlocks the restored home and starts its stored independent GNOME units.
Verify picture/input/custom background, native1Password and existing app data.
Refresh public certificate pins with desktop.d/secure-desktop-tv.sh while the
home is unlocked; native3393 credential/certificate live inside the volume.
If the volume password changes, native RDP credentials must be refreshed too.

## Restore phone approvals

The archive contains `recovery/notification.json.age`, separately encrypted to
the same backup identity. Decrypt it only through anonymous pipes/memory, then
feed it into `systemd-creds encrypt --name=notification -
/etc/credstore.encrypted/productivity-push` on the new host. Do not restore the old
host's TPM/credential-secret material over a new system. The credential needs
fresh host encryption. Existing helper source describes the JSON fields; never
log/print the decoded payload.

Inspect the approval HTTPS origin if the new Tailscale DNS name differs. Configure
Tailscale Serve HTTPS to127.0.0.1:18742 (not Funnel), install/enable
productivity-push.service with desktop.d/productivity-push.sh, and update the
saved1Password website/Jump endpoint as needed. Verify real iPhone notification,
AutoFill confirmation, one-use unlock and TV viewer; a listening service alone
is not evidence of working capture. No unlock/decryption key is needed on the
backup daemon: only the public age recipient is installed in recovery settings.

## Backups and restore checks

`sudo python3 bin/backup-secure-desktop.py` freezes the mounted encrypted ext4
home briefly, with an independent20second thaw timer, then takes read-only
Btrfs snapshots of var/home. It thaws before network transfer and streams sparse
tar → zstd → age → Closet. The archive is promoted from.partial only when every
local pipeline stage succeeds. The receipt includes encrypted-byte SHA256,
length, source commit and date. Main Steam config/userdata, Sunshine pairing,
selected shell/SSH/service/cooling/firewall config and independently wrapped
notification credential are included. This is not a full backup of every drive,
ROM/game install, arbitrary main-user repo or personal folder. Existing gaming
sync/backups are separate. The encrypted desktop home itself is captured whole.

`python3 bin/test-secure-desktop-restore.py` retrieves recovery keys privately
from authorized1Password on Closet, downloads/decrypts to a separate directory,
opens a different read-only LUKS mapping, runs e2fsck and verifies selected home
file hashes, the wrapped notification credential and Git bundle. It then closes
that mapping and removes the extracted private test data, leaving a report.
It never starts a second GNOME against the copied home or replaces production.
A completely fresh-machine graphical rebuild is not claimed until separately
exercised. Repeat a recovery test after encryption/key/header changes and major
setup changes. A second off-site copy is still needed for loss of both desktop
and Closet; no off-site upload has been configured by this task.

## Verified baseline — 2026-11-01

Archive `desktop-secure-20261101T175057Z.tar.zst.age`, 8676320350 encrypted bytes. SHA256: `47c35103b3a3efaa4035b124971ced8bbfa83cb6bd97316e82e69267d7c2e59a`. Independent decryption, LUKS unlock, ext4 check after journal replay on the copy, five saved-home hashes, nested notification credential and Git bundle verification passed at18:09UTC. A fresh-machine graphical rebuild remains untested.

The original full-archive timer was configured for04:15; verified Restic history supersedes it after the documented switch. The new nightly history runs at04:15 with up to5minutes jitter while the desktop is awake. Missed jobs do not wake it. Inspect `systemctl status productivity-backup.timer productivity-backup.service` and `/var/lib/productivity-recovery/latest.json`. Backups are retained until deliberately reviewed; monitor NAS free space and preserve this tested baseline. No off-site copy is configured.

NAS access bootstrap is also escrowed in the same recovery record: the existing
NAS SSH identity and pinned server key, alongside the three encryption secrets.
Use `bin/backup-recovery-access.py` with your independently signed-in owner
1Password CLI if the original desktop/SSH files are gone. See the incremental
runbook's bootstrap section; setup validation retrieved actual NAS snapshots
without the original local SSH identity or agent.
