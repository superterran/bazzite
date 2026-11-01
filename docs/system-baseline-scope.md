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
