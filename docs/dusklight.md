# Dusklight

Official Dusklight v2.0.3 Linux x86_64 (bundled Randomizer v1.0.6) lives in the existing Syncthing shared-games folder under `dusklight/`. Desktop path: `/var/mnt/fast/shared-games/dusklight`. This folder is shared directly with Ally; Closet is not a member of shared-games.

`play.sh` uses `--user-dir` pointing at `dusklight/user-data`, so saves and randomizer data travel with the game. Exit the game and allow sync to finish before playing on the other machine. The original Twilight Princess disc dump is still needed for first-run asset import.

Install or repair the Steam shortcut against a running local Steam CEF session:

```bash
python3 bin/setup-dusklight.py --game-dir /path/to/shared-games/dusklight
```

A portable copy of the setup script and its helper modules is included in `dusklight/setup/` for the Ally. It creates a native Linux shortcut and preserves unrelated Steam entries. Steam CEF debugging must already be enabled, as for the existing fleet setup tools.

2026-10-31: Desktop Steam entry 2323161660 verified by live Steam app overview (`Dusklight`). Launcher `--help` passes. AppImage SHA256 matches official release: `87ec251963c984ad2b3ac075281431d2221db2297dc19f2ab5daad92e969fc06`. Ally last seen five hours earlier; pinned tailnet SSH timed out. Folder queued for sync, but Ally transfer, shortcut registration and physical play remain unverified.
