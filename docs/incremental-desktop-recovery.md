# Encrypted baseline and desktop history

Restic stores client-side encrypted, deduplicated snapshots on Closet at
`/mnt/storage/backups/desktop-restic`. Its separate repository password is in
1Password / Closet / Desktop Secure Recovery / **Incremental backup repository
password**. This is NOT the age identity or LUKS passphrase. The tested original
age archive remains separate and is never deleted by Restic retention.

## Two backup scopes

- `baseline`: selective known-good system capture. Actual OSTree sysroot,
  boot/EFI files, GPT/UUID/subvolume inventory, writable system configuration,
  installed Flatpaks/Homebrew/tools, selected main-home application data/config,
  native encrypted-home image, agent/tool settings (including Codex/Claude), repo state and persistent container data.
  Baselines are protected from automatic desktop retention. Capture explicitly
  again after major intentional setup changes.
- `desktop`: nightly snapshot of the LUKS backing image plus current manifest,
  header and public recovery metadata. Seven daily, four weekly, three monthly
  points. Retention groups by host/tags and applies ONLY to host desktop/tag
  desktop. It does not remove baseline or verification snapshots.

Every restore point describes a complete logical file tree, but unchanged chunks
are stored once in the repository. The LUKS image has64GiB logical capacity and
about7GiB allocated now. Each run may still scan its logical size; deduplication
reduces stored/uploaded data, not necessarily all local reads. Encryption-sector
writes change affected ciphertext chunks; actual increment size depends on
workload and filesystem writes. Do not promise zero growth on an idle desktop.

The encrypted desktop remains a LUKS image within the already-encrypted Restic
repository. Thus raw-volume recovery and application settings are retained.
Individual old files require restoring/mounting a COPY of that image first.
A separate two-version fixture verifies history retrieval independently.

## Capture safety and exclusions

Capture reads stable Btrfs snapshots, not a changing raw disk. The encrypted ext4
home is frozen briefly before its backing var snapshot, with an independent
20second thaw timer. Baseline briefly pauses currently running Docker containers
for its var snapshot, with independent30second unpause timers; it never stops or
restarts them. Root/var/home snapshots are sequential, not an atomic multi-volume
transaction. No OS deployment transition may straddle root/boot capture; the
job refuses active rpm-ostree transactions and compares deployment status again.
Boot files are copied while the OS is stable. This is filesystem-consistent
capture, not a claim of application-level consistency for arbitrary live databases.

Exclude Downloads, Steam downloaded games/shaders/full Windows prefix components,
AI model downloads, root Docker images/build cache, rootless container images,
Claude downloadable VM bundles/cache/logs, repo dependency/cache folders and
unselected general home development/build trees. Exclusions do NOT delete live
files. Installed applications are retained deliberately to reduce reprovisioning.

Keep Steam config/userdata/art/controller state and app manifests. Preserve each
prefix's steamuser profile and registry as a small additional save/config safety
net (~2.4GiB profiles at capture preparation). This is not an exhaustive audit of
all game-specific save locations or proof of Steam Cloud upload. ROM save share
was observed synced to Closet, idle/no pending/no errors; sync is not itself an
independent backup. Shared ROM/data drives remain outside baseline scope.

Repo captures retain `.git` history and local tracked/untracked/ignored files,
except named dependency caches and approved model file types. This deliberately
keeps some remotely recoverable source to avoid losing unpushed history. Repo
inventory is a sizing aid, not the backup source. Broken historical gitfiles are
captured as files with their working trees, not silently omitted. Repos outside
~/repos require explicit selection. No credentials are copied to Git or logs.

## Commands and schedule

```
sudo python3 bin/backup-productivity-incremental.py             # desktop
sudo systemctl start productivity-baseline.service             # explicit baseline
sudo python3 bin/productivity-restic.py snapshots
sudo python3 bin/productivity-restic.py stats --mode raw-data
sudo python3 bin/productivity-restic.py check
python3 bin/verify-productivity-incremental.py
```

`productivity-incremental.timer`:04:15 plus up to5minutes jitter, while awake.
No wake or missed-job catch-up. Service fails on a nonzero Restic result,
including unreadable files/incomplete snapshots; it does not silently accept
partial capture. Retention executes only after successful backup. Journal and
root-only `/var/lib/productivity-recovery/{desktop,baseline}-latest.log` plus
latest-success JSON receipts distinguish failures from successful snapshots.
No push failure alert is configured. Monitor failed units and NAS capacity.
The200GiB figure is a planning allowance, NOT a quota or guaranteed retention size.

Repository password is host-encrypted by systemd for unattended use. Unlike the
original age-public-key-only job, unattended Restic needs its repository key.
Root on the live host can decrypt that credential; possession of the encrypted
NAS repository alone cannot. The LUKS home still needs its separate full password.
No plaintext repository-key file is created; wrapper uses an anonymous memfd.

## Recovery on another Linux host

Install Restic plus cryptsetup/e2fsprogs and obtain authorized access to Closet.
Use the repository password from1Password in Restic's interactive password prompt;
never put secrets in argv, URLs, shell history or support logs. The host credential
file is machine-bound; do not assume copying it recovers the key on another host.
List snapshots and restore a selected ID to a NEW empty staging directory:

```
restic -r sftp:closet:/mnt/storage/backups/desktop-restic snapshots
restic -r sftp:closet:/mnt/storage/backups/desktop-restic restore SNAPSHOT_ID \
  --target /mnt/restore-staging --sparse --verify
```

Captured paths are under `/var/lib/productivity-recovery/restic-capture/`:
`root/` is the OSTree sysroot; `var/` and `home/` are separately selected source
subvolumes; `boot-files/` contains boot plus nested EFI files; `metadata/` includes
disk/UUID/boot/package inventories and manifests. Do not restore these paths over
the live capture directory or live home. Copy the saved LUKS image into a separate
recovery location, unlock it interactively with the full volume password, replay
its journal ON THE COPY if required, and run a clean check before mounting read-only.
See secure-desktop-recovery.md for the tested copy-only journal procedure.

Desktop history deliberately does not contain the whole baseline. Keep access to
the baseline snapshot as well as the selected newer desktop snapshot when rebuilding.
Raw snapshot paths are not directly the staging layout expected by the older
age-archive `install-restored-secure-desktop.py`; normalize them carefully before
using that tool. No automated destructive bare-metal installer is supplied.
Bare-metal recovery needs GPT/filesystem/subvolume recreation, correct numeric
ownership/ACL/xattrs, OSTree/composefs-aware boot restoration, UUID references and
UEFI entries. Current composefs config is enabled=yes; different integrity modes
may require fs-verity re-enablement/OSTree deployment rather than simple file copy.
Do not claim a fresh-machine boot test based solely on a successful file restore.

Retain1Password Emergency Kit/account recovery separately. No off-site copy is
configured. Replicate the entire repository with appropriate tools, including
its keys/config/index/data/snapshots, if adding off-site recovery later.

## Initial validation and cache refinements — 2026-11-01

Independent repository access using the1Password key, separate LUKS image restore,
copy-only journal replay/clean fsck, five saved-home hashes, and recovery of both
versions of an overwritten test fixture passed. Root-only evidence:
`/var/lib/productivity-recovery/incremental-restore-test.json`.
The first desktop snapshot added7690365546packed bytes (~7.2GiB).

The finalizer waits for the first baseline and applies
`config/productivity-backup-excludes.json` to that explicit snapshot ID only.
This filters additional Flatpak caches/Whisper models and disposable Docker model/
monitoring cache volumes discovered during capture, without recopying everything.
It replaces that intermediate snapshot with its filtered counterpart; the protected
original age archive is untouched. Scoped nightly prune reclaims unreferenced data.
Future captures apply those exclusions directly. No live files are removed.

Installed rootless container image/writable distro layers are excluded; mounted
persistent volumes and host-side app settings are retained. The sole observed
rootless container was Envision, with most layer bulk in installed /usr software;
its container image and internal package/config customizations may need rebuilding.
This is not a full container-engine clone. Docker persistent volumes, container
inspection metadata and unique root Docker upper-layer files are separately kept.

Finalizer then checks five saved configuration files against hashes from the
immutable source snapshots, runs Restic repository metadata checks, executes the
actual nightly service including retention/prune, and records measured second-run
storage additions in completed-backup-validation.json. Check this report before
claiming the full baseline and follow-up finished. Fresh-machine boot remains
unexercised regardless of successful file recovery.
