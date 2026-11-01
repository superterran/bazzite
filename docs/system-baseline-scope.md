# Known-good system baseline: measured scope

2026-11-01 read-only inventory. This is a proposal, not a completed or verified
whole-system backup. No reboot, snapshot, service stop, prune or new capture was
performed for this inventory. Existing encrypted-home backup remains separate.

## Goal and preferred capture

Preserve the installed Bazzite system and its actual layered deployment rather
than relying on package-list reconstruction. Retain the root OSTree repository,
deployments and metadata, writable var state, main home configuration, native
Homebrew installation, secure home image, boot partition, EFI files and disk/
filesystem identity metadata. Steam downloads can be downloaded again.

Capture root, var and home as distinct Btrfs subvolumes. Mount topology matters:
archiving the runtime composefs `/` is not a copy of the OSTree sysroot. Preserve
hardlinks, numeric ownership, ACLs, all required xattrs and SELinux labels. Boot
and EFI are separate ext4/FAT filesystems. Save GPT, partition/filesystem UUIDs,
Btrfs subvolume layout, fstab, boot entries and UEFI inventory privately with the
backup. Source contains no copied host credentials.

The straightforward baseline is an offline file-level capture from recovery
media, encrypted before transfer to Closet. The live system can be inventoried
and all tools prepared without reboot. An online variant would require a tested
consistent capture across root/var/home plus boot files, secure ext4 freeze and
application quiescing; do not call independent snapshots application-consistent
without that work. Do not copy a changing block device as a disk image.

## Measured sizes (allocated bytes; approximate, not compressed archive size)

| Item | GiB | Treatment |
|---|---:|---|
| Root OSTree subvolume | 20.6 | Preserve whole, actual layered deployments |
| Boot + EFI | 0.53 | Preserve plus disk/boot metadata |
| Var subvolume | 293.5 | Preserve conservatively; includes Docker below |
| Home after provisional exclusions | 352.9 | See exclusions and caveats below |
| Steam common game downloads | 521.1 | Exclude from baseline, redownload |
| Steam shader cache | 81.2 | Exclude, regenerate |
| Steam Proton compatdata | 49.5 | Keep: may hold saves and local modifications |
| Main ~/.config | 21.7 | Keep; Claude accounts for about20.7GiB |
| Root Docker storage | 261.5 | Not mostly system configuration; review separately |
| Main ~/models | 78.7 | Optional redownloadable models; not excluded yet |
| Main ~/.ollama | 19.7 | Optional redownloadable models; not excluded yet |
| Homebrew under linuxbrew home | 8.6 | Included in home total |

Measured subtotal ~667.4GiB BEFORE compression excludes these paths only:
`me/.cache`, `me/Downloads`, and Steam steamapps/{common,shadercache,downloading,temp}.
Downloads (~53GiB) are a provisional exclusion for sizing, NOT an approved loss
of personal files; retain by default until reviewed. With Downloads retained,
allow roughly720GiB before compression. No exact compression ratio or transfer
runtime has been established. Closet has about1.7TiB available, enough for one
conservative baseline with headroom; keep independent nightly backup capacity.
Docker system-df reported150images and1315build-cache entries; its categories
share layers, so never add its image/cache numbers as independent disk usage.

Do not drop Steam userdata/config, app manifests, artwork, non-Steam games,
controller mappings, workshop authoring files, saves or Proton prefixes merely
because they are under Steam. Inspect other configured game-library roots if
expanding scope. Do not prune Docker, caches or model files from the running
machine to shrink a backup; exclusions affect the backup only. Keep persistent
container volumes and unique writable state even if rebuilding disposable images.

## Restore implications and evidence boundary

A selective file backup is not a Clonezilla raw/used-block disk image; that form
cannot simply exclude game directories. Bare-metal restoration must recreate
GPT/filesystems/subvolumes, restore files and the exact OSTree state, then restore
or repair EFI/boot entries and reconcile UUID references. On another-sized drive,
review partition layout rather than blindly replaying the original GPT. Do not
run duplicate network identities simultaneously. Check the installed bootloader
and composefs/OSTree requirements against the preserved deployment before coding
a destructive installer. A successful archive check alone is not a boot test.

Root partition currently /dev/nvme0n1p3 (Btrfs root, var, home); p1 EFI600MiB;
p2 boot1GiB. Separate4TB NVMe and2TB SATA data drives are OUTSIDE this scope.

The next implementation should prepare a reversible capture tool and private
manifest, then schedule the offline capture only when authorized. A bootable
bare-metal recovery result remains unverified until actually exercised. Existing
secure-desktop recovery verification is documented separately in
[secure-desktop-recovery.md](secure-desktop-recovery.md).

Primary architecture reference:
https://ostreedev.github.io/ostree/deployment/

## User scope refinement

User excludes replaceable AI models and Docker images/build cache from the proposed baseline. This is a backup exclusion only, not authorization to delete live files. Preserve persistent container volumes, unique writable container data and configuration; inspect/export them separately rather than copying disposable image/cache storage. No revised total has been measured yet.

Encrypted desktop measured live:64GiB logical sparse LUKS image,7.2GiB physically allocated,4.4GiB used inside ext4. Current independent encrypted backup is8676320350bytes (~8.1GiB) and also includes selected main-system configuration and recovery artifacts.

Refined estimate: approximately370GiB before compression, retaining Downloads, Proton prefixes, container volumes and an allowance for unique Docker writable layers. This subtracts the three measured model directories and disposable root Docker storage from the conservative scope; it retains rootless Podman storage pending a safe split. Roughly360GiB is outside the7.2GiB secure-home image. This is sizing, not a captured archive or verified container-data export; Docker writable-layer export still needs implementation.

## Narrow system/settings scope and repository-local state

User requests that repo dependencies and remotely recoverable tracked source not
inflate the baseline. Preserve .env/ignored local config, untracked unique files,
uncommitted tracked edits, and local/unpushed Git history. Never assume ignored
means disposable, or that all commits have reached a remote. Record repo paths,
HEAD/refs, remote mappings privately and verify remote availability during actual
capture. Capture Git bundles (including local refs) and working-tree deltas;
linked worktrees need their shared Git metadata too. Git LFS objects/submodules
and deleted-but-uncommitted paths need explicit treatment in a capture tool.

Read-only inventory helper bin/inventory-repo-recovery.py creates a PRIVATE0600
report outside Git; it is not a backup or a complete restore manifest. Initial
scan found186repositories plus2invalid/broken Git entries. Whole repo directory
is ~44GiB. Local/untracked/ignored candidates after common dependency exclusions
were14.2GiB, of which10.3GiB were Adventurer GGUF/ggml model downloads. After
excluding these already-approved replaceable models, allow about4GiB of local
candidates plus5.7GiB Git metadata before further review/compression. Broken
usp-osf nested checkout (~780MiB) and historical visual-comfort linked worktree
(~38MiB) must be retained/reviewed separately, not silently dropped. Nothing was
modified or deleted in those projects. Vendor/build output still occurs among
candidates and could shrink further only after review. Repositories outside
~/repos and permission-inaccessible directories need separate coverage.

The narrow estimate is now roughly120–130GiB BEFORE compression: approximately
97GiB for saved OS/boot, installed Flatpaks/Homebrew/tools, app data and config,
secure home and selected local app state; add ~17GiB persistent Docker data and
unique writable-state allowance, and ~10GiB repo-local files/Git metadata plus
broken-checkout margin. This is a scope estimate, not a verified backup artifact.
Downloads, home build/checkouts and general developer data are outside this
narrow scope unless selected above. Installed app binaries are deliberately kept
to restore the working setup, rather than redownload/reprovision every app.

Save-policy caveat: ROM saves currently idle/no pending/no errors with Closet;
that does not establish coverage for every non-Steam or Steam Cloud game. Prefix
exclusion remains conditional on auditing local-only saves. No prefix or local
save has been removed. Current nightly encrypted-home backup is unchanged.

Implementation completed2026-11-01: see incremental-desktop-recovery.md for the
actual protected NAS baseline, verified extra local NVMe copy and nightly history.
The complete selected capture packed to53.2GiB, substantially below the planning
allowance. Initial NAS+legacy recovery material settled at about73GiB after cleanup;
latest measured repeat added5.6MiB. Fresh bare-metal boot remains untested.
