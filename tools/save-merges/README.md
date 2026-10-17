# One-off save merges (2026-10-16)

Every distinct playthrough found on old devices/backups was moved into its own
in-game slot instead of letting sync pick a winner. Each script rebuilds from the
*current* shared save at run time, backs it up to
`/var/mnt/fast/rom-original-backups/save-merges-20261016/`, writes the canonical
cartridge save, then runs `rom-save-alias-sync.py` to fan it out.

| Game | Result | Format notes |
|---|---|---|
| Super Metroid | A 1:23 (Steam/main), B 0:28 (old iPhone RA), C 0:15 (Delta) | slot = 0x65C bytes at 0x10+i*0x65C; checksum = 16-bit word sum, complement at +8, mirrored at 0x1FF0/0x1FF8 |
| Super Mario World | A 36 exits, B 7 (Delta), C 6 (old iPhone widescreen) | 6×143-byte blocks (files + backups); sum(141 bytes)+u16 == 0x5A5A |
| Super Mario 64 | file A = union of all runs: 23 stars (Ghostship 19, Dropbox-2021 19, 2019 state 13, Ally SD .eep 10) | EEPROM SaveFile 0x38 (2 copies per file); Ghostship PC port stores it little-endian ("AD"), N64 big-endian ("DA") |

Sources are preserved: Delta mirror and legacy Dropbox saves in closet
`gaming/delta-backup`, iPhone RetroArch saves in `gaming/archive/iphone-retroarch-20261016`.
Scripts reference /tmp scratch inputs and are kept as a record, not for re-running as-is.
