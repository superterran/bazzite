# 24 Games for Windows 95

Steam shortcut: **24 Games for Windows 95**, app ID **3616716904**.
Launcher: `bin/launch-24-games.sh`.
Data: `/var/mnt/fast/shared-games/24-games-windows95/`.

Original Expert Software collection, sourced from https://archive.org/details/24GamesForWindows95 . The ISO's SHA-1 was checked against that item's published metadata. Extracted CD files are under `cd/`; the installed collection's launcher is `cd/WIN/PROGRAM/GAMES.EXE`. The original front-cover image supplies Steam portrait artwork.

These are 16-bit Windows 3.1 applications. Proton 11.0's winevdm launches them successfully in an isolated prefix under `compatdata/`. No Windows OS installation or virtual desktop is used. Steam runs the shell launcher as a native shortcut, which invokes Proton; do not additionally force a compatibility tool on this shortcut. Game Mode/Gamescope handles fullscreen presentation.

Verified in an isolated Xvfb session: the picker and Black Box Chess launch. The user subsequently confirmed fullscreen presentation in Game Mode and working controller input. Bulldozer later froze and its dedicated Wine session was stopped; stability across all 24 games is not established.

## Shared desktop / Ally setup

`bin/launch-24-games.sh` is also deployed as `shared-games/24-games-windows95/play.sh`. It resolves the local shared folder, launches directly through Proton 11.0, and keeps Wine runtime files **local** at `~/.local/share/24-games-windows95/compatdata`. The desktop's existing prefix was moved there, preserving its state. Never synchronize a live Proton prefix; the previous shared prefix path is now excluded in shared-games/.stignore. Original CD files, settings written into the program folder, artwork and portable setup bundle share through Syncthing.

Run `python3 ~/repos/bazzite/bin/setup-24-games.py --controller ally` on the Ally while Steam and its intended controller are available, with Steam CEF debugging enabled. Or run `bash ~/repos/bazzite/common.d/24-games.sh`, included in common setup. Pass `--game-dir` if the local share is elsewhere. The self-contained shared copy can be run as `python3 ~/shared-games/24-games-windows95/setup/bin/setup-24-games.py --controller ally` without updating the repo first. Requires installed Proton 11.0.

The installer preserves an existing matching Steam shortcut ID, updates its launch target for Game Mode, clears old launch options, applies the native Steam Input layout and matching artwork, and backs up previous shortcut metadata/controller configuration under `~/.local/state/24-games-setup/<timestamp>/`. It stops if duplicate matching entries exist. Steam must be running; a desktop-only launcher remains untouched. Each device retains its own Steam shortcut ID and local prefix. If the old entry forces a compatibility tool in Steam Properties, turn that off: the new shell launcher invokes Proton itself. That old-entry compatibility setting still needs inspection on the offline Ally.

| Control | DualSense | Ally |
| --- | --- | --- |
| Arrow keys | D-pad and left stick | D-pad and left stick |
| Enter | Cross | A |
| Space | Square | X |
| Escape | Circle / Options | B / Menu |
| F2 (Bulldozer restart) | Triangle | Y |
| Tab | Create | View |
| Pointer | Touchpad / right stick | Right stick (touchscreen also available) |
| Left click | R2 / R1 / right-stick press / touchpad press | RT / RB / right-stick press |
| Right click | L2 / L1 | LT / LB |

No PS/Guide hold required. The menu-only bridge remains separate; games use Steam Input. Saved VDF references are under `config/steam/24-games/`; the Ally variant is a prepared template, not a capture from its offline hardware. The installer configures the actual connected controller through Steam's native API.

Corrected Windows 95-inspired wide capsule (`capsule.png`) and hero (`hero.png`) depict only games verified in this collection: Black Box Chess, Bulldozer, Reversi Plus, Pegopolis and Cryptograms. Removed the invented card-solitaire, Tetris and colored-line panels at user request, preserving the overall style. Applied to desktop Steam and exported through existing title-based `rom-artwork/steam` sync. Original portrait is retained; old generated versions are saved as `capsule-v1.png` / `hero-v1.png`. Images are illustrative, not exact gameplay screenshots.

**Ally deployment remains pending:** it was offline on 2026-10-23 (mDNS unresolved; known LAN addresses unavailable; Syncthing disconnected). Its existing game copy, shortcut and controller behavior could not be inspected or tested. Files and setup instructions are staged in the shared folder for delivery when it reconnects; no automatic execution is claimed.
